"""Chord progression detection.

Detects chords per beat/bar using chroma features and chord templates.
Outputs chord symbols (Am, F, C, G7, etc.) with timing.
"""

from dataclasses import dataclass, field
import numpy as np
import librosa


# Chord templates: 12 major, 12 minor, 12 dominant 7th, 12 minor 7th
# Each is a 12-dimensional binary vector (pitch class set)
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Intervals for each chord quality (in semitones from root)
CHORD_TYPES = {
    "":      [0, 4, 7],          # Major triad
    "m":     [0, 3, 7],          # Minor triad
    "7":     [0, 4, 7, 10],      # Dominant 7th
    "m7":    [0, 3, 7, 10],      # Minor 7th
    "maj7":  [0, 4, 7, 11],      # Major 7th
    "dim":   [0, 3, 6],          # Diminished
    "aug":   [0, 4, 8],          # Augmented
    "sus4":  [0, 5, 7],          # Suspended 4th
    "sus2":  [0, 2, 7],          # Suspended 2nd
}


@dataclass
class ChordEvent:
    """A chord at a specific time."""
    chord: str          # e.g., "Am", "F", "C", "G7"
    start_time: float
    end_time: float
    confidence: float
    root_note: str      # e.g., "A", "F", "C", "G"
    quality: str        # e.g., "m", "7", "maj7", ""


@dataclass
class ChordResult:
    chords: list[ChordEvent] = field(default_factory=list)
    chord_progression: str = ""     # e.g., "Am - F - C - G"
    progression_per_section: dict = field(default_factory=dict)  # section_label -> progression
    unique_chords: list[str] = field(default_factory=list)
    key_chords: str = ""            # Most used chords
    description: str = ""


def _build_chord_templates():
    """Build all chord templates as 12-dim vectors."""
    templates = {}
    for root_idx, root_name in enumerate(NOTE_NAMES):
        for quality, intervals in CHORD_TYPES.items():
            chord_name = f"{root_name}{quality}"
            template = np.zeros(12)
            for interval in intervals:
                template[(root_idx + interval) % 12] = 1.0
            # Normalize
            template = template / np.linalg.norm(template)
            templates[chord_name] = {
                "vector": template,
                "root": root_name,
                "root_idx": root_idx,
                "quality": quality,
            }
    return templates


CHORD_TEMPLATES = _build_chord_templates()


def detect_chords(
    y: np.ndarray,
    sr: int,
    beat_times: np.ndarray = None,
    sections: list = None,
) -> ChordResult:
    """Detect chord progression from audio.

    Args:
        y: Audio waveform (ideally the 'other' stem without vocals/drums).
        sr: Sample rate.
        beat_times: Beat positions from rhythm analyzer (for beat-sync).
        sections: Song sections for per-section chord analysis.
    """
    hop_length = 512

    # Compute chromagram (CQT-based for better frequency resolution)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    times = librosa.frames_to_time(np.arange(chroma.shape[1]), sr=sr, hop_length=hop_length)

    # Beat-synchronize chroma if beat times are available
    if beat_times is not None and len(beat_times) > 2:
        # Use beats as analysis windows
        beat_frames = librosa.time_to_frames(beat_times, sr=sr, hop_length=hop_length)
        beat_frames = beat_frames[beat_frames < chroma.shape[1]]
        if len(beat_frames) > 2:
            chroma_sync = librosa.util.sync(chroma, beat_frames, aggregate=np.median)
            sync_times = beat_times[:chroma_sync.shape[1]]
        else:
            chroma_sync = chroma
            sync_times = times
    else:
        # Use fixed windows (~0.5s each)
        window = max(1, int(0.5 * sr / hop_length))
        n_windows = chroma.shape[1] // window
        if n_windows > 0:
            chroma_sync = np.array([
                np.median(chroma[:, i * window:(i + 1) * window], axis=1)
                for i in range(n_windows)
            ]).T
            sync_times = np.array([times[i * window] for i in range(n_windows)])
        else:
            chroma_sync = chroma
            sync_times = times

    # Match each time window to the best chord template
    chord_events = []
    for i in range(chroma_sync.shape[1]):
        chroma_vec = chroma_sync[:, i]

        if np.linalg.norm(chroma_vec) < 0.01:
            # Silence
            continue

        chroma_norm = chroma_vec / (np.linalg.norm(chroma_vec) + 1e-10)

        # Find best matching chord
        best_score = -1
        best_chord = "N"
        best_root = ""
        best_quality = ""

        for chord_name, info in CHORD_TEMPLATES.items():
            score = float(np.dot(chroma_norm, info["vector"]))
            if score > best_score:
                best_score = score
                best_chord = chord_name
                best_root = info["root"]
                best_quality = info["quality"]

        start_t = float(sync_times[i]) if i < len(sync_times) else 0
        end_t = float(sync_times[i + 1]) if i + 1 < len(sync_times) else start_t + 0.5

        chord_events.append(ChordEvent(
            chord=best_chord,
            start_time=start_t,
            end_time=end_t,
            confidence=best_score,
            root_note=best_root,
            quality=best_quality,
        ))

    # Merge consecutive same chords
    merged = []
    for ce in chord_events:
        if merged and merged[-1].chord == ce.chord:
            merged[-1].end_time = ce.end_time
            merged[-1].confidence = max(merged[-1].confidence, ce.confidence)
        else:
            merged.append(ChordEvent(
                chord=ce.chord,
                start_time=ce.start_time,
                end_time=ce.end_time,
                confidence=ce.confidence,
                root_note=ce.root_note,
                quality=ce.quality,
            ))

    # Filter out very short chords (likely noise) — less than 0.3s
    merged = [c for c in merged if c.end_time - c.start_time >= 0.3]

    # Build chord progression string
    chord_names = [c.chord for c in merged]
    # Deduplicate consecutive for readability
    progression_parts = []
    for c in chord_names:
        if not progression_parts or progression_parts[-1] != c:
            progression_parts.append(c)
    chord_progression = " → ".join(progression_parts)

    # Find unique chords
    unique_chords = list(dict.fromkeys(chord_names))

    # Most common chords
    from collections import Counter
    chord_counts = Counter(chord_names)
    top_chords = [c for c, _ in chord_counts.most_common(6)]
    key_chords = ", ".join(top_chords)

    # Per-section chord progressions
    progression_per_section = {}
    if sections:
        for section in sections:
            section_chords = [
                c.chord for c in merged
                if c.start_time >= section.start_time and c.end_time <= section.end_time
            ]
            if section_chords:
                # Deduplicate consecutive
                deduped = []
                for c in section_chords:
                    if not deduped or deduped[-1] != c:
                        deduped.append(c)
                progression_per_section[section.label] = " → ".join(deduped)
            else:
                progression_per_section[section.label] = "(no chords detected)"

    # Build description
    from utils.audio_io import format_time
    desc_lines = [
        f"=== Chord Progression Analysis ===",
        f"Unique chords used: {', '.join(unique_chords)}",
        f"Most common chords: {key_chords}",
        f"Full progression: {chord_progression}",
        f"",
        f"--- Chords per Section ---",
    ]
    for label, prog in progression_per_section.items():
        desc_lines.append(f"  {label}: {prog}")

    desc_lines.append("")
    desc_lines.append("--- Detailed Chord Timeline ---")
    for c in merged[:60]:
        desc_lines.append(
            f"  [{format_time(c.start_time)}-{format_time(c.end_time)}] "
            f"{c.chord:<8} (confidence: {c.confidence:.2f})"
        )
    if len(merged) > 60:
        desc_lines.append(f"  ... and {len(merged) - 60} more chord changes")

    return ChordResult(
        chords=merged,
        chord_progression=chord_progression,
        progression_per_section=progression_per_section,
        unique_chords=unique_chords,
        key_chords=key_chords,
        description="\n".join(desc_lines),
    )
