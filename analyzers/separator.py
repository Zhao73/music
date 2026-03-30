"""Audio source separation using Demucs (Meta).

Separates audio into: vocals, drums, bass, other (guitar/piano/synth).
This dramatically improves lyrics recognition and melody extraction accuracy.
"""

import os
import tempfile
from dataclasses import dataclass
import numpy as np
import torch
import torchaudio


@dataclass
class SeparationResult:
    """Separated audio stems."""
    vocals: np.ndarray          # Isolated vocal track
    drums: np.ndarray           # Isolated drum track
    bass: np.ndarray            # Isolated bass track
    other: np.ndarray           # Everything else (guitar, piano, synth, strings)
    original: np.ndarray        # Original mix
    sr: int                     # Sample rate
    success: bool = True
    error: str = ""


def separate_tracks(audio_path: str, sr: int = 22050) -> SeparationResult:
    """Separate audio into vocals, drums, bass, and other using Demucs.

    Uses the 'htdemucs' model (hybrid transformer, best quality).
    Falls back to simpler methods if Demucs is unavailable.

    Args:
        audio_path: Path to audio file.
        sr: Target sample rate for output.

    Returns:
        SeparationResult with separated numpy arrays.
    """
    try:
        from demucs.pretrained import get_model
        from demucs.apply import apply_model
    except ImportError:
        return _fallback_separation(audio_path, sr)

    try:
        # Load audio
        waveform, orig_sr = torchaudio.load(audio_path)

        # Demucs expects specific sample rate (44100 for htdemucs)
        model = get_model("htdemucs")
        model_sr = model.samplerate  # typically 44100

        # Resample if needed
        if orig_sr != model_sr:
            resampler = torchaudio.transforms.Resample(orig_sr, model_sr)
            waveform = resampler(waveform)

        # Ensure stereo (Demucs expects 2 channels)
        if waveform.shape[0] == 1:
            waveform = waveform.repeat(2, 1)
        elif waveform.shape[0] > 2:
            waveform = waveform[:2]

        # Add batch dimension: (batch, channels, time)
        waveform = waveform.unsqueeze(0)

        # Apply model
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device)
        waveform = waveform.to(device)

        with torch.no_grad():
            sources = apply_model(model, waveform, device=device)

        # sources shape: (batch, num_sources, channels, time)
        # htdemucs sources order: drums, bass, other, vocals
        sources = sources[0].cpu().numpy()  # Remove batch dim

        # Map source names (htdemucs order)
        source_names = model.sources  # ['drums', 'bass', 'other', 'vocals']
        stems = {}
        for i, name in enumerate(source_names):
            # Convert stereo to mono and resample to target sr
            stem_mono = np.mean(sources[i], axis=0)  # Average channels to mono

            # Resample from model_sr to target sr
            if model_sr != sr:
                import librosa
                stem_mono = librosa.resample(stem_mono, orig_sr=model_sr, target_sr=sr)

            stems[name] = stem_mono

        # Also load original as mono at target sr
        import librosa
        original, _ = librosa.load(audio_path, sr=sr, mono=True)

        return SeparationResult(
            vocals=stems.get("vocals", original),
            drums=stems.get("drums", np.zeros_like(original)),
            bass=stems.get("bass", np.zeros_like(original)),
            other=stems.get("other", np.zeros_like(original)),
            original=original,
            sr=sr,
            success=True,
        )

    except Exception as e:
        return _fallback_separation(audio_path, sr, error=str(e))


def _fallback_separation(audio_path: str, sr: int, error: str = "") -> SeparationResult:
    """Fallback: use librosa HPSS (harmonic-percussive separation).

    Not as good as Demucs but works without extra model download.
    """
    import librosa

    y, sr_out = librosa.load(audio_path, sr=sr, mono=True)

    # Harmonic-percussive separation
    y_harmonic, y_percussive = librosa.effects.hpss(y)

    # Rough approximation:
    # - vocals ≈ harmonic (mid-high frequencies)
    # - drums ≈ percussive
    # - bass ≈ harmonic low frequencies
    # - other ≈ harmonic (remaining)

    # Simple frequency band split for bass
    S = librosa.stft(y_harmonic)
    freqs = librosa.fft_frequencies(sr=sr)

    bass_mask = freqs < 250
    other_mask = freqs >= 250

    S_bass = S.copy()
    S_bass[~bass_mask] = 0
    y_bass = librosa.istft(S_bass, length=len(y))

    S_other = S.copy()
    S_other[~other_mask] = 0
    y_other = librosa.istft(S_other, length=len(y))

    err_msg = "Demucs not available, using HPSS fallback (lower quality separation)"
    if error:
        err_msg += f". Demucs error: {error}"

    return SeparationResult(
        vocals=y_harmonic,      # Best approximation without Demucs
        drums=y_percussive,
        bass=y_bass,
        other=y_other,
        original=y,
        sr=sr_out,
        success=False,
        error=err_msg,
    )


def save_stem(stem: np.ndarray, sr: int, path: str):
    """Save a separated stem to a WAV file."""
    import soundfile as sf
    sf.write(path, stem, sr)
