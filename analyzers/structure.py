"""Song structure detection using self-similarity and clustering."""

from dataclasses import dataclass, field
import numpy as np
import librosa


@dataclass
class Section:
    label: str  # e.g., "Intro", "Verse", "Chorus", "Bridge", "Outro"
    start_time: float
    end_time: float


@dataclass
class StructureResult:
    sections: list[Section] = field(default_factory=list)
    summary: str = ""
    description: str = ""


def detect_structure(
    y: np.ndarray, sr: int, lyrics_segments: list[dict] = None
) -> StructureResult:
    """Detect song structure (intro, verse, chorus, bridge, outro).

    Uses chroma-based self-similarity matrix and agglomerative clustering.
    Lyrics repetition is used as an additional signal if available.
    """
    duration = len(y) / sr

    # Compute features for segmentation
    # Use chroma + MFCCs for a richer representation
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

    # Stack features
    features = np.vstack([chroma, mfcc])

    # Compute self-similarity matrix
    rec = librosa.segment.recurrence_matrix(
        features, mode="affinity", sym=True
    )

    # Find segment boundaries using structural features
    n_segments = min(10, features.shape[1] // 50) or 6
    bound_frames = librosa.segment.agglomerative(features, k=n_segments)

    # Convert frames to times
    bound_times = librosa.frames_to_time(bound_frames, sr=sr)

    # Add start and end
    bound_times = np.unique(np.concatenate([[0.0], bound_times, [duration]]))
    bound_times = np.sort(bound_times)

    # Filter out very short segments (< 3 seconds)
    filtered = [bound_times[0]]
    for t in bound_times[1:]:
        if t - filtered[-1] >= 3.0:
            filtered.append(t)
    if filtered[-1] < duration - 1.0:
        filtered.append(duration)
    bound_times = np.array(filtered)

    # Limit to reasonable number of sections (max ~12)
    if len(bound_times) > 13:
        # Re-cluster with fewer segments
        n_segments = min(10, len(bound_times) - 1)
        bound_frames = librosa.segment.agglomerative(features, k=n_segments)
        bound_times = librosa.frames_to_time(bound_frames, sr=sr)
        bound_times = np.unique(np.concatenate([[0.0], bound_times, [duration]]))
        bound_times = np.sort(bound_times)

    # Compute energy per segment for labeling
    segment_energies = []
    segment_chromas = []
    for i in range(len(bound_times) - 1):
        start_sample = int(bound_times[i] * sr)
        end_sample = int(bound_times[i + 1] * sr)
        seg_audio = y[start_sample:end_sample]
        energy = float(np.mean(np.abs(seg_audio)))
        segment_energies.append(energy)

        # Chroma profile for similarity
        if len(seg_audio) > sr // 2:
            seg_chroma = np.mean(
                librosa.feature.chroma_cqt(y=seg_audio, sr=sr), axis=1
            )
        else:
            seg_chroma = np.zeros(12)
        segment_chromas.append(seg_chroma)

    # Find repeated sections (potential chorus) by chroma similarity
    n_segs = len(segment_energies)
    similarity = np.zeros((n_segs, n_segs))
    for i in range(n_segs):
        for j in range(n_segs):
            if np.linalg.norm(segment_chromas[i]) > 0 and np.linalg.norm(segment_chromas[j]) > 0:
                similarity[i][j] = np.dot(segment_chromas[i], segment_chromas[j]) / (
                    np.linalg.norm(segment_chromas[i]) * np.linalg.norm(segment_chromas[j])
                )

    # Label sections using heuristics
    labels = [""] * n_segs
    median_energy = np.median(segment_energies) if segment_energies else 0

    # Check lyrics repetition if available
    lyrics_by_segment = {}
    if lyrics_segments:
        for i in range(n_segs):
            seg_text = ""
            for ls in lyrics_segments:
                if ls["start"] >= bound_times[i] and ls["end"] <= bound_times[i + 1]:
                    seg_text += ls["text"] + " "
            lyrics_by_segment[i] = seg_text.strip()

    # Find most repeated segments (chorus candidates)
    repeat_counts = np.zeros(n_segs)
    for i in range(n_segs):
        for j in range(n_segs):
            if i != j and similarity[i][j] > 0.92:
                repeat_counts[i] += 1

    # Label assignment
    for i in range(n_segs):
        seg_duration = bound_times[i + 1] - bound_times[i]

        if i == 0 and (seg_duration < 15 or segment_energies[i] < median_energy * 0.7):
            labels[i] = "Intro"
        elif i == n_segs - 1 and (seg_duration < 15 or segment_energies[i] < median_energy * 0.7):
            labels[i] = "Outro"
        elif repeat_counts[i] >= 2 and segment_energies[i] >= median_energy:
            labels[i] = "Chorus"
        elif repeat_counts[i] >= 1 and segment_energies[i] >= median_energy * 1.1:
            labels[i] = "Chorus"
        else:
            labels[i] = ""

    # Fill remaining as Verse or Bridge
    verse_count = 0
    for i in range(n_segs):
        if labels[i] == "":
            # If it's between two choruses and unique, it might be a bridge
            has_chorus_before = any(labels[j] == "Chorus" for j in range(i))
            has_chorus_after = any(labels[j] == "Chorus" for j in range(i + 1, n_segs))
            if has_chorus_before and has_chorus_after and repeat_counts[i] == 0:
                # Check if it's the only non-labeled section between choruses
                labels[i] = "Bridge"
            else:
                verse_count += 1
                labels[i] = f"Verse"

    # Number the verses and choruses
    verse_num = 0
    chorus_num = 0
    for i in range(n_segs):
        if labels[i] == "Verse":
            verse_num += 1
            labels[i] = f"Verse {verse_num}"
        elif labels[i] == "Chorus":
            chorus_num += 1
            if chorus_num > 1:
                labels[i] = "Chorus"
            else:
                labels[i] = "Chorus"

    # Build sections
    sections = []
    for i in range(n_segs):
        sections.append(Section(
            label=labels[i],
            start_time=float(bound_times[i]),
            end_time=float(bound_times[i + 1]),
        ))

    summary = " - ".join(s.label for s in sections)
    description = f"Song structure: {summary} ({n_segs} sections detected)"

    return StructureResult(
        sections=sections,
        summary=summary,
        description=description,
    )
