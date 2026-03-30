"""Melody and pitch extraction using librosa PYIN."""

from dataclasses import dataclass
import numpy as np
import librosa


@dataclass
class MelodyResult:
    pitch_hz: np.ndarray  # Raw f0 contour in Hz
    note_sequence: list[str]  # Quantized note names
    vocal_range_low: str
    vocal_range_high: str
    avg_pitch_hz: float
    description: str


def extract_melody(y: np.ndarray, sr: int) -> MelodyResult:
    """Extract melody/pitch information from audio.

    Uses PYIN for fundamental frequency estimation.
    """
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
    )

    # Filter out unvoiced frames (NaN)
    voiced_f0 = f0[~np.isnan(f0)]

    if len(voiced_f0) == 0:
        return MelodyResult(
            pitch_hz=f0,
            note_sequence=[],
            vocal_range_low="N/A",
            vocal_range_high="N/A",
            avg_pitch_hz=0.0,
            description="No pitched content detected",
        )

    # Convert to MIDI note numbers, then to note names
    midi_notes = librosa.hz_to_midi(voiced_f0)
    note_names = [librosa.midi_to_note(int(round(m))) for m in midi_notes]

    # Vocal range
    low_note = librosa.midi_to_note(int(round(midi_notes.min())))
    high_note = librosa.midi_to_note(int(round(midi_notes.max())))

    # Get the most common notes (simplified melody summary)
    unique_notes, counts = np.unique(
        [librosa.midi_to_note(int(round(m))) for m in midi_notes],
        return_counts=True,
    )
    top_notes = unique_notes[np.argsort(-counts)[:5]]

    avg_pitch = float(np.mean(voiced_f0))

    # Simple contour description
    first_quarter = np.mean(voiced_f0[: len(voiced_f0) // 4])
    last_quarter = np.mean(voiced_f0[-len(voiced_f0) // 4 :])
    if last_quarter > first_quarter * 1.05:
        contour = "overall ascending melody"
    elif last_quarter < first_quarter * 0.95:
        contour = "overall descending melody"
    else:
        contour = "relatively stable pitch range"

    description = (
        f"Vocal range: {low_note} to {high_note}. "
        f"Most frequent notes: {', '.join(top_notes)}. "
        f"Melody shows {contour}."
    )

    return MelodyResult(
        pitch_hz=f0,
        note_sequence=note_names,
        vocal_range_low=low_note,
        vocal_range_high=high_note,
        avg_pitch_hz=avg_pitch,
        description=description,
    )
