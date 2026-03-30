"""Rhythm, tempo, and beat analysis using librosa."""

from dataclasses import dataclass
import numpy as np
import librosa


@dataclass
class RhythmResult:
    bpm: float
    time_signature: str
    beat_times: np.ndarray
    feel: str
    energy_level: str
    description: str


def extract_rhythm(y: np.ndarray, sr: int) -> RhythmResult:
    """Extract rhythm and tempo information from audio."""
    # Tempo and beat tracking
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0])
    else:
        tempo = float(tempo)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # Onset strength for energy analysis
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    avg_onset = float(np.mean(onset_env))

    # Energy level classification
    if avg_onset > 8:
        energy_level = "high energy"
    elif avg_onset > 4:
        energy_level = "medium energy"
    else:
        energy_level = "low energy / calm"

    # Time signature estimation (simplified heuristic)
    # Check beat interval regularity for 3/4 vs 4/4
    time_signature = "4/4"
    if len(beat_times) > 4:
        intervals = np.diff(beat_times)
        if len(intervals) > 2:
            # Look for groupings of 3 by checking accent patterns
            accent_pattern = onset_env[beat_frames] if len(beat_frames) > 0 else []
            if len(accent_pattern) > 6:
                # Check if every 3rd beat is stronger (suggests 3/4)
                groups_of_3 = accent_pattern[::3]
                groups_of_4 = accent_pattern[::4]
                var_3 = np.var(groups_of_3) if len(groups_of_3) > 1 else float("inf")
                var_4 = np.var(groups_of_4) if len(groups_of_4) > 1 else float("inf")
                if var_3 < var_4 * 0.7:
                    time_signature = "3/4"

    # Feel classification
    if tempo > 140:
        feel = "fast / upbeat"
    elif tempo > 108:
        feel = "moderate / groovy"
    elif tempo > 76:
        feel = "mid-tempo / steady"
    else:
        feel = "slow / ballad"

    description = (
        f"BPM: {tempo:.0f}, Time signature: {time_signature}, "
        f"Feel: {feel}, Energy: {energy_level}"
    )

    return RhythmResult(
        bpm=tempo,
        time_signature=time_signature,
        beat_times=beat_times,
        feel=feel,
        energy_level=energy_level,
        description=description,
    )
