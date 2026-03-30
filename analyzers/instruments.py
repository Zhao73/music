"""Instrument detection using spectral analysis heuristics."""

from dataclasses import dataclass, field
import numpy as np
import librosa


@dataclass
class InstrumentResult:
    detected: list[str] = field(default_factory=list)
    description: str = ""


def detect_instruments(y: np.ndarray, sr: int) -> InstrumentResult:
    """Detect instruments using spectral feature heuristics.

    Uses harmonic-percussive separation and frequency band analysis.
    """
    instruments = []

    # Harmonic-percussive source separation
    y_harmonic, y_percussive = librosa.effects.hpss(y)

    harmonic_energy = float(np.mean(np.abs(y_harmonic)))
    percussive_energy = float(np.mean(np.abs(y_percussive)))
    total_energy = harmonic_energy + percussive_energy + 1e-10

    # Spectral features on full mix
    spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    spectral_bandwidth = float(np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr)))
    spectral_rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))

    # Frequency band energy analysis
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)

    def band_energy(low, high):
        mask = (freqs >= low) & (freqs < high)
        if mask.any():
            return float(np.mean(S[mask, :]))
        return 0.0

    sub_bass = band_energy(20, 80)
    bass = band_energy(80, 300)
    low_mid = band_energy(300, 1000)
    mid = band_energy(1000, 4000)
    high_mid = band_energy(4000, 8000)
    high = band_energy(8000, 16000)

    total_band = sub_bass + bass + low_mid + mid + high_mid + high + 1e-10

    # Percussion detection
    if percussive_energy / total_energy > 0.25:
        instruments.append("Drums / Percussion")

    # Bass detection
    if (sub_bass + bass) / total_band > 0.35:
        instruments.append("Bass")

    # Vocal detection (dominant mid-range harmonic content)
    if harmonic_energy / total_energy > 0.4 and mid / total_band > 0.15:
        instruments.append("Vocals")

    # Guitar/Piano detection (harmonic content in low-mid to mid range)
    if harmonic_energy / total_energy > 0.5 and low_mid / total_band > 0.15:
        # Distinguish roughly by spectral centroid
        if spectral_centroid > 2000:
            instruments.append("Guitar (Electric)")
        elif spectral_centroid > 800:
            instruments.append("Piano / Keys")
        else:
            instruments.append("Acoustic Guitar")

    # Synth detection (wide bandwidth, high spectral rolloff)
    if spectral_bandwidth > 2500 and spectral_rolloff > 6000:
        instruments.append("Synthesizer / Electronic")

    # Strings (smooth harmonic, narrow bandwidth)
    if harmonic_energy / total_energy > 0.6 and spectral_bandwidth < 1500:
        instruments.append("Strings")

    # If nothing detected, provide generic
    if not instruments:
        instruments.append("Mixed instrumentation")

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for inst in instruments:
        if inst not in seen:
            seen.add(inst)
            unique.append(inst)

    description = f"Detected instruments: {', '.join(unique)}"

    return InstrumentResult(detected=unique, description=description)
