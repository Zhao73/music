"""Audio file loading and format conversion utilities."""

import os
import tempfile
import numpy as np
import librosa
from pydub import AudioSegment

from config import SAMPLE_RATE, SUPPORTED_FORMATS


def load_audio(file_path: str, sr: int = SAMPLE_RATE) -> tuple[np.ndarray, int]:
    """Load an audio file and return (waveform, sample_rate).

    Supports mp3, wav, flac, ogg, m4a, wma, aac.
    All formats are converted to mono WAV internally.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {ext}. Supported: {SUPPORTED_FORMATS}")

    if ext == ".wav":
        y, sr_out = librosa.load(file_path, sr=sr, mono=True)
    else:
        # Convert to WAV via pydub first
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_channels(1).set_frame_rate(sr)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            audio.export(tmp_path, format="wav")

        try:
            y, sr_out = librosa.load(tmp_path, sr=sr, mono=True)
        finally:
            os.unlink(tmp_path)

    return y, sr_out


def get_duration(y: np.ndarray, sr: int) -> float:
    """Return duration in seconds."""
    return len(y) / sr


def format_time(seconds: float) -> str:
    """Format seconds as MM:SS."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"
