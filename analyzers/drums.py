"""Drum pattern and rhythm pattern analysis.

Analyzes the percussive track to detect specific drum patterns,
groove types, and rhythmic feel.
"""

from dataclasses import dataclass, field
import numpy as np
import librosa


@dataclass
class DrumHit:
    """A single detected drum hit."""
    time: float
    type: str           # "kick", "snare", "hihat", "cymbal", "tom"
    velocity: float     # 0-1 relative loudness


@dataclass
class DrumPattern:
    """A repeating drum pattern (typically 1-2 bars)."""
    pattern_str: str    # e.g., "K...S...K.K.S..." (K=kick, S=snare, H=hihat)
    duration: float     # Pattern duration in seconds
    beats: int          # Number of beats in pattern
    subdivision: int    # Subdivisions per beat (8th=2, 16th=4)


@dataclass
class DrumResult:
    hits: list[DrumHit] = field(default_factory=list)
    patterns: list[DrumPattern] = field(default_factory=list)
    main_pattern: str = ""          # The most common repeating pattern
    groove_type: str = ""           # "straight", "shuffle", "swing", "syncopated"
    kick_pattern: str = ""          # Kick-only pattern
    snare_pattern: str = ""         # Snare-only pattern
    hihat_pattern: str = ""         # Hi-hat pattern
    fills_count: int = 0            # Number of detected drum fills
    description: str = ""
    pattern_notation: str = ""      # Full pattern in grid notation


def _classify_drum_hit(S_frame: np.ndarray, freqs: np.ndarray) -> str:
    """Classify a percussive onset by frequency content."""
    # Energy in different frequency bands
    low = np.sum(S_frame[(freqs >= 30) & (freqs < 150)])
    low_mid = np.sum(S_frame[(freqs >= 150) & (freqs < 400)])
    mid = np.sum(S_frame[(freqs >= 400) & (freqs < 2000)])
    high_mid = np.sum(S_frame[(freqs >= 2000) & (freqs < 6000)])
    high = np.sum(S_frame[(freqs >= 6000) & (freqs < 16000)])

    total = low + low_mid + mid + high_mid + high + 1e-10

    low_ratio = low / total
    mid_ratio = mid / total
    high_ratio = (high_mid + high) / total

    # Classification heuristics
    if low_ratio > 0.45:
        return "kick"
    elif mid_ratio > 0.35 and low_mid / total > 0.15:
        return "snare"
    elif high_ratio > 0.5:
        return "hihat"
    elif high_ratio > 0.35 and high_mid / total > 0.2:
        return "cymbal"
    elif low_mid / total > 0.3:
        return "tom"
    elif low_ratio > 0.3:
        return "kick"
    else:
        return "hihat"


def analyze_drums(
    y_drums: np.ndarray,
    sr: int,
    bpm: float = 120.0,
    beat_times: np.ndarray = None,
) -> DrumResult:
    """Analyze drum patterns from a percussive/drum track.

    Args:
        y_drums: Drum-isolated audio (from separator or HPSS).
        sr: Sample rate.
        bpm: Detected BPM.
        beat_times: Beat positions from rhythm analyzer.
    """
    hop_length = 512

    if np.max(np.abs(y_drums)) < 0.001:
        return DrumResult(
            description="No significant drum/percussion content detected.",
        )

    # --- Detect onsets ---
    onset_frames = librosa.onset.onset_detect(
        y=y_drums, sr=sr, hop_length=hop_length,
        backtrack=True, units="frames",
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr, hop_length=hop_length)

    # --- Classify each onset ---
    S = np.abs(librosa.stft(y_drums, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr)
    rms = librosa.feature.rms(y=y_drums, hop_length=hop_length)[0]
    rms_max = rms.max() if rms.max() > 0 else 1.0

    hits = []
    for frame in onset_frames:
        if frame < S.shape[1]:
            hit_type = _classify_drum_hit(S[:, frame], freqs)
            velocity = float(min(1.0, rms[min(frame, len(rms) - 1)] / rms_max))
            hits.append(DrumHit(
                time=float(librosa.frames_to_time(frame, sr=sr, hop_length=hop_length)),
                type=hit_type,
                velocity=velocity,
            ))

    if not hits:
        return DrumResult(description="No drum hits detected.")

    # --- Build pattern grid ---
    beat_duration = 60.0 / bpm if bpm > 0 else 0.5
    subdivision = 4  # 16th notes (4 subdivisions per beat)
    grid_resolution = beat_duration / subdivision  # Duration of one grid cell

    # Analyze pattern over first few bars to find the repeating pattern
    # Try 1-bar (4 beats) and 2-bar (8 beats) patterns
    bar_duration = beat_duration * 4  # Assuming 4/4 time

    # Build grid for the entire song
    total_duration = len(y_drums) / sr
    total_cells = int(total_duration / grid_resolution) + 1

    # Create separate grids for each drum type
    type_map = {"kick": "K", "snare": "S", "hihat": "H", "cymbal": "C", "tom": "T"}
    grids = {t: np.zeros(total_cells) for t in type_map}

    for hit in hits:
        cell = int(hit.time / grid_resolution)
        if cell < total_cells:
            t = hit.type
            if t in grids:
                grids[t][cell] = max(grids[t][cell], hit.velocity)

    # --- Find repeating pattern ---
    # Try 1-bar pattern (16 cells for 16th notes in 4/4)
    cells_per_bar = int(bar_duration / grid_resolution)
    if cells_per_bar < 4:
        cells_per_bar = 16

    patterns_found = []

    # Extract patterns from each bar and find the most common
    n_bars = total_cells // cells_per_bar
    bar_patterns = []

    for bar in range(min(n_bars, 30)):  # Analyze up to 30 bars
        start = bar * cells_per_bar
        end = start + cells_per_bar
        if end > total_cells:
            break

        pattern_str = ""
        for cell in range(start, end):
            cell_char = "."
            # Priority: kick > snare > hihat > cymbal > tom
            if grids["kick"][cell] > 0.2:
                cell_char = "K"
            elif grids["snare"][cell] > 0.2:
                cell_char = "S"
            elif grids["hihat"][cell] > 0.15:
                cell_char = "H"
            elif grids["cymbal"][cell] > 0.15:
                cell_char = "C"
            elif grids["tom"][cell] > 0.2:
                cell_char = "T"
            pattern_str += cell_char

        bar_patterns.append(pattern_str)

    # Find most common pattern
    from collections import Counter
    if bar_patterns:
        pattern_counts = Counter(bar_patterns)
        main_pattern_str = pattern_counts.most_common(1)[0][0]
    else:
        main_pattern_str = "." * cells_per_bar

    # --- Individual instrument patterns ---
    def _make_instrument_pattern(grid, symbol, threshold=0.15):
        """Create a pattern string for one instrument."""
        pattern = ""
        for cell in range(cells_per_bar):
            # Average across all bars
            values = [grid[bar * cells_per_bar + cell]
                      for bar in range(min(n_bars, 20))
                      if bar * cells_per_bar + cell < total_cells]
            avg = np.mean(values) if values else 0
            pattern += symbol if avg > threshold else "."
        return pattern

    kick_pattern = _make_instrument_pattern(grids["kick"], "K", 0.2)
    snare_pattern = _make_instrument_pattern(grids["snare"], "S", 0.2)
    hihat_pattern = _make_instrument_pattern(grids["hihat"], "H", 0.1)

    # --- Groove type detection ---
    # Check if hi-hat pattern suggests shuffle/swing
    hihat_cells = [i for i, c in enumerate(hihat_pattern) if c == "H"]
    if len(hihat_cells) > 2:
        intervals = np.diff(hihat_cells)
        if len(intervals) > 1:
            interval_var = np.var(intervals)
            if interval_var < 0.5:
                if all(i % 2 == 0 for i in hihat_cells):
                    groove_type = "straight 8th notes"
                elif all(i % 1 == 0 for i in hihat_cells):
                    groove_type = "straight 16th notes"
                else:
                    groove_type = "straight"
            else:
                # Uneven spacing suggests shuffle/swing
                groove_type = "shuffle / swing"
        else:
            groove_type = "minimal percussion"
    else:
        groove_type = "sparse percussion"

    # Check for syncopation (kicks/snares on off-beats)
    kick_cells = [i for i, c in enumerate(kick_pattern) if c == "K"]
    snare_cells = [i for i, c in enumerate(snare_pattern) if c == "S"]
    offbeat_kicks = sum(1 for k in kick_cells if k % subdivision != 0)
    if kick_cells and offbeat_kicks / len(kick_cells) > 0.4:
        groove_type += ", syncopated kick"

    # --- Detect fills (bars that differ from main pattern) ---
    fills_count = 0
    for bp in bar_patterns:
        if bp != main_pattern_str:
            # Count how different it is
            diffs = sum(1 for a, b in zip(bp, main_pattern_str) if a != b)
            if diffs > cells_per_bar * 0.4:
                fills_count += 1

    # --- Build drum pattern ---
    patterns = [DrumPattern(
        pattern_str=main_pattern_str,
        duration=float(bar_duration),
        beats=4,
        subdivision=subdivision,
    )]

    # --- Format pattern notation ---
    def _format_grid_pattern(pattern_str, beats=4, sub=4):
        """Format pattern as readable grid."""
        lines = []
        cells = beats * sub
        pattern = pattern_str[:cells] if len(pattern_str) >= cells else pattern_str.ljust(cells, ".")

        # Beat markers
        beat_line = ""
        for b in range(beats):
            beat_line += f"|{b+1}" + " " * (sub - 2) + " "
        lines.append(f"Beat:   {beat_line}|")

        # Each instrument layer
        for symbol, name in [("K", "Kick "), ("S", "Snare"), ("H", "HiHat"), ("C", "Crash"), ("T", "Tom  ")]:
            row = ""
            has_content = False
            for i, c in enumerate(pattern):
                if i % sub == 0 and i > 0:
                    row += "|"
                if c == symbol:
                    row += "X"
                    has_content = True
                else:
                    row += "."
            if has_content:
                lines.append(f"{name}:  |{row}|")

        # Combined pattern
        combined = ""
        for i, c in enumerate(pattern):
            if i % sub == 0 and i > 0:
                combined += "|"
            combined += c if c != "." else "."
        lines.append(f"All:    |{combined}|")

        return "\n".join(lines)

    pattern_notation = _format_grid_pattern(main_pattern_str, beats=4, sub=subdivision)

    # --- Description ---
    desc_lines = [
        "=== Drum Pattern Analysis ===",
        f"Groove type: {groove_type}",
        f"Pattern subdivision: {subdivision} per beat (16th notes)",
        f"Drum fills detected: {fills_count}",
        f"Total drum hits: {len(hits)}",
        f"",
        f"--- Main Drum Pattern (1 bar = {cells_per_bar} cells) ---",
        pattern_notation,
        f"",
        f"--- Individual Patterns ---",
        f"Kick:   |{kick_pattern}|",
        f"Snare:  |{snare_pattern}|",
        f"Hi-hat: |{hihat_pattern}|",
        f"",
        f"Pattern legend: K=Kick, S=Snare, H=HiHat, C=Cymbal, T=Tom, .=rest",
        f"Each cell = 1/16th note at {bpm:.0f} BPM",
    ]

    # Per-section pattern variation
    if n_bars > 4:
        desc_lines.append("")
        desc_lines.append("--- Pattern Variation ---")
        unique_patterns = len(set(bar_patterns))
        desc_lines.append(f"Unique patterns across song: {unique_patterns} variations")
        desc_lines.append(f"Main pattern appears in {pattern_counts.most_common(1)[0][1]}/{len(bar_patterns)} bars")

    return DrumResult(
        hits=hits,
        patterns=patterns,
        main_pattern=main_pattern_str,
        groove_type=groove_type,
        kick_pattern=kick_pattern,
        snare_pattern=snare_pattern,
        hihat_pattern=hihat_pattern,
        fills_count=fills_count,
        description="\n".join(desc_lines),
        pattern_notation=pattern_notation,
    )
