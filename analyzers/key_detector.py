"""Musical key detection using chroma features and Krumhansl-Kessler profiles."""

from dataclasses import dataclass
import numpy as np
import librosa


# Krumhansl-Kessler key profiles
MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass
class KeyResult:
    key: str  # e.g., "C major"
    root_note: str  # e.g., "C"
    mode: str  # "major" or "minor"
    confidence: float
    description: str


def detect_key(y: np.ndarray, sr: int) -> KeyResult:
    """Detect the musical key of an audio signal.

    Uses chroma features correlated against Krumhansl-Kessler key profiles.
    """
    # Compute chromagram
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)

    # Average chroma across time to get pitch class profile
    pitch_profile = np.mean(chroma, axis=1)

    # Correlate with all 24 key profiles (12 major + 12 minor)
    best_corr = -1.0
    best_key = "C"
    best_mode = "major"

    for i in range(12):
        # Rotate profile to match each root note
        major_shifted = np.roll(MAJOR_PROFILE, i)
        minor_shifted = np.roll(MINOR_PROFILE, i)

        corr_major = float(np.corrcoef(pitch_profile, major_shifted)[0, 1])
        corr_minor = float(np.corrcoef(pitch_profile, minor_shifted)[0, 1])

        if corr_major > best_corr:
            best_corr = corr_major
            best_key = NOTE_NAMES[i]
            best_mode = "major"

        if corr_minor > best_corr:
            best_corr = corr_minor
            best_key = NOTE_NAMES[i]
            best_mode = "minor"

    key_name = f"{best_key} {best_mode}"
    description = f"Detected key: {key_name} (confidence: {best_corr:.2f})"

    return KeyResult(
        key=key_name,
        root_note=best_key,
        mode=best_mode,
        confidence=best_corr,
        description=description,
    )
