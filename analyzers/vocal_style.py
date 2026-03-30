"""Vocal style and singing technique analysis.

Detects: vibrato, dynamics (crescendo/decrescendo), breathiness,
vocal register, singing style, articulation patterns.
"""

from dataclasses import dataclass, field
import numpy as np
import librosa


@dataclass
class DynamicEvent:
    """A dynamic change in the song."""
    start_time: float
    end_time: float
    type: str           # "crescendo", "decrescendo", "accent", "subito_forte", "subito_piano"
    from_level: str     # "pp", "p", "mp", "mf", "f", "ff"
    to_level: str


@dataclass
class VocalStyleResult:
    # Vibrato
    vibrato_rate_hz: float          # Average vibrato rate (typically 5-7 Hz)
    vibrato_extent_cents: float     # Average vibrato width in cents
    vibrato_presence: float         # 0-1, how much of the vocal has vibrato
    vibrato_description: str

    # Dynamics
    dynamic_range_db: float         # Difference between loudest and softest
    avg_loudness_db: float
    dynamic_events: list[DynamicEvent] = field(default_factory=list)
    dynamics_description: str = ""

    # Vocal register
    chest_voice_pct: float = 0.0    # % of time in chest voice
    head_voice_pct: float = 0.0     # % of time in head voice / falsetto
    register_description: str = ""

    # Breathiness / Tone quality
    breathiness: float = 0.0        # 0-1
    brightness: float = 0.0         # 0-1
    nasality: float = 0.0           # 0-1
    tone_description: str = ""

    # Articulation
    legato_pct: float = 0.0         # % smooth connected notes
    staccato_pct: float = 0.0       # % short detached notes
    articulation_description: str = ""

    # Singing style summary
    style_tags: list[str] = field(default_factory=list)
    full_description: str = ""


def _dynamic_level(db: float) -> str:
    """Map dB to musical dynamic marking."""
    if db < -40:
        return "pp"
    elif db < -30:
        return "p"
    elif db < -22:
        return "mp"
    elif db < -15:
        return "mf"
    elif db < -8:
        return "f"
    else:
        return "ff"


def analyze_vocal_style(y: np.ndarray, sr: int, f0: np.ndarray = None) -> VocalStyleResult:
    """Comprehensive vocal style analysis.

    Args:
        y: Audio waveform.
        sr: Sample rate.
        f0: Pre-computed f0 contour (optional, will compute if None).
    """
    hop_length = 512

    # --- Get f0 if not provided ---
    if f0 is None:
        f0, _, _ = librosa.pyin(
            y, fmin=librosa.note_to_hz("C2"),
            fmax=librosa.note_to_hz("C7"), sr=sr,
        )

    # --- 1. VIBRATO ANALYSIS ---
    # Vibrato = periodic pitch fluctuation, typically 5-7 Hz, 20-200 cents
    voiced_mask = ~np.isnan(f0)
    vibrato_rate = 0.0
    vibrato_extent = 0.0
    vibrato_presence = 0.0

    if np.sum(voiced_mask) > 50:
        # Convert f0 to cents (relative to local mean)
        f0_voiced = f0.copy()
        f0_voiced[~voiced_mask] = 0

        # Analyze pitch fluctuation in short windows
        window_size = 50  # ~1 second at default hop
        vibrato_scores = []

        for start in range(0, len(f0) - window_size, window_size // 2):
            segment = f0[start:start + window_size]
            seg_voiced = segment[~np.isnan(segment)]

            if len(seg_voiced) < 20:
                continue

            # Detrend
            detrended = seg_voiced - np.polyval(np.polyfit(range(len(seg_voiced)), seg_voiced, 1), range(len(seg_voiced)))

            # FFT to find vibrato rate
            fft = np.abs(np.fft.rfft(detrended))
            freqs = np.fft.rfftfreq(len(detrended), d=hop_length / sr)

            # Look for peaks in vibrato range (4-8 Hz)
            vibrato_mask = (freqs >= 4) & (freqs <= 8)
            if vibrato_mask.any() and fft[vibrato_mask].max() > 0:
                peak_idx = np.argmax(fft[vibrato_mask])
                vibrato_freq = freqs[vibrato_mask][peak_idx]
                vibrato_power = fft[vibrato_mask].max()
                total_power = fft[1:].sum() + 1e-10

                if vibrato_power / total_power > 0.15:
                    vibrato_scores.append({
                        "rate": vibrato_freq,
                        "extent": float(np.std(detrended)),
                        "strength": vibrato_power / total_power,
                    })

        if vibrato_scores:
            vibrato_rate = float(np.mean([v["rate"] for v in vibrato_scores]))
            # Convert extent from Hz to cents approximately
            mean_f0 = np.mean(f0[voiced_mask])
            vibrato_extent_hz = float(np.mean([v["extent"] for v in vibrato_scores]))
            vibrato_extent = 1200 * np.log2((mean_f0 + vibrato_extent_hz) / mean_f0) if mean_f0 > 0 else 0
            vibrato_presence = len(vibrato_scores) / max(1, len(range(0, len(f0) - window_size, window_size // 2)))

    if vibrato_presence > 0.5:
        vibrato_desc = f"Strong vibrato ({vibrato_rate:.1f} Hz, ~{vibrato_extent:.0f} cents), present in {vibrato_presence*100:.0f}% of vocal"
    elif vibrato_presence > 0.2:
        vibrato_desc = f"Moderate vibrato ({vibrato_rate:.1f} Hz), present in {vibrato_presence*100:.0f}% of vocal"
    elif vibrato_presence > 0.05:
        vibrato_desc = f"Subtle vibrato, mostly on sustained notes"
    else:
        vibrato_desc = "Straight tone, minimal vibrato"

    # --- 2. DYNAMICS ANALYSIS ---
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    rms_db = librosa.amplitude_to_db(rms + 1e-10)
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)

    dynamic_range = float(rms_db.max() - rms_db.min())
    avg_loudness = float(np.mean(rms_db))

    # Detect dynamic events (significant volume changes)
    dynamic_events = []
    # Smooth RMS for trend detection
    kernel_size = min(21, len(rms_db) // 2 * 2 + 1)
    if kernel_size >= 3:
        smoothed = np.convolve(rms_db, np.ones(kernel_size) / kernel_size, mode="same")

        # Find significant changes (> 6dB over 2 seconds)
        change_window = int(2.0 * sr / hop_length)
        for i in range(change_window, len(smoothed) - change_window, change_window // 2):
            before = np.mean(smoothed[max(0, i - change_window):i])
            after = np.mean(smoothed[i:min(len(smoothed), i + change_window)])
            diff = after - before

            if abs(diff) > 6:
                event_type = "crescendo" if diff > 0 else "decrescendo"
                if abs(diff) > 15:
                    event_type = "subito_forte" if diff > 0 else "subito_piano"
                dynamic_events.append(DynamicEvent(
                    start_time=float(times[max(0, i - change_window)]),
                    end_time=float(times[min(len(times) - 1, i + change_window)]),
                    type=event_type,
                    from_level=_dynamic_level(before),
                    to_level=_dynamic_level(after),
                ))

    if dynamic_range > 30:
        dynamics_desc = f"Very wide dynamic range ({dynamic_range:.0f} dB). Dramatic contrasts between soft and loud sections."
    elif dynamic_range > 20:
        dynamics_desc = f"Wide dynamic range ({dynamic_range:.0f} dB). Clear dynamic variation."
    elif dynamic_range > 10:
        dynamics_desc = f"Moderate dynamic range ({dynamic_range:.0f} dB). Relatively consistent volume."
    else:
        dynamics_desc = f"Narrow dynamic range ({dynamic_range:.0f} dB). Very consistent/compressed dynamics."

    if dynamic_events:
        crescendos = sum(1 for e in dynamic_events if "crescendo" in e.type or "forte" in e.type)
        decrescendos = sum(1 for e in dynamic_events if "decrescendo" in e.type or "piano" in e.type)
        dynamics_desc += f" {crescendos} crescendos, {decrescendos} decrescendos detected."

    # --- 3. VOCAL REGISTER ---
    chest_voice_pct = 0.0
    head_voice_pct = 0.0
    if np.sum(voiced_mask) > 0:
        voiced_f0_values = f0[voiced_mask]
        midi_values = librosa.hz_to_midi(voiced_f0_values)
        # Rough register boundary: E4 (MIDI 64) for male, A4 (MIDI 69) for female
        # Use a middle ground
        register_boundary = 66  # F#4
        chest_voice_pct = float(np.sum(midi_values < register_boundary) / len(midi_values) * 100)
        head_voice_pct = float(np.sum(midi_values >= register_boundary) / len(midi_values) * 100)

    if head_voice_pct > 70:
        register_desc = f"Predominantly head voice/falsetto ({head_voice_pct:.0f}%). Light, airy upper register."
    elif head_voice_pct > 40:
        register_desc = f"Mixed voice: {chest_voice_pct:.0f}% chest, {head_voice_pct:.0f}% head voice. Versatile register usage."
    else:
        register_desc = f"Predominantly chest voice ({chest_voice_pct:.0f}%). Full, powerful lower register."

    # --- 4. TONE QUALITY (Breathiness, Brightness, Nasality) ---
    S = np.abs(librosa.stft(y, hop_length=hop_length))
    freqs = librosa.fft_frequencies(sr=sr)

    # Breathiness: high HNR (Harmonic-to-Noise ratio) = clear; low = breathy
    spectral_flatness = librosa.feature.spectral_flatness(S=S)
    breathiness = float(np.mean(spectral_flatness))
    breathiness = min(1.0, breathiness * 5)  # Scale to 0-1

    # Brightness: spectral centroid relative to range
    centroid = librosa.feature.spectral_centroid(S=S, sr=sr)
    brightness = float(np.mean(centroid)) / (sr / 2)
    brightness = min(1.0, brightness * 4)

    # Nasality approximation: energy ratio around 1000-3000 Hz vs total
    nasal_mask = (freqs >= 800) & (freqs <= 3000)
    total_mask = freqs > 0
    if nasal_mask.any() and total_mask.any():
        nasal_energy = float(np.mean(S[nasal_mask, :]))
        total_energy = float(np.mean(S[total_mask, :]))
        nasality = nasal_energy / (total_energy + 1e-10)
        nasality = min(1.0, max(0.0, (nasality - 0.3) * 2))
    else:
        nasality = 0.0

    tone_parts = []
    if breathiness > 0.5:
        tone_parts.append("breathy/airy tone")
    elif breathiness < 0.2:
        tone_parts.append("clear/clean tone")
    else:
        tone_parts.append("balanced tone")

    if brightness > 0.5:
        tone_parts.append("bright timbre")
    elif brightness < 0.2:
        tone_parts.append("warm/dark timbre")
    else:
        tone_parts.append("neutral brightness")

    if nasality > 0.5:
        tone_parts.append("nasal quality")

    tone_desc = "Vocal tone: " + ", ".join(tone_parts) + "."

    # --- 5. ARTICULATION (legato vs staccato) ---
    onsets = librosa.onset.onset_detect(y=y, sr=sr, hop_length=hop_length, units="time")
    if len(onsets) > 1:
        onset_intervals = np.diff(onsets)
        # Short intervals between notes = staccato tendency
        short_threshold = 0.15  # seconds
        staccato_count = np.sum(onset_intervals < short_threshold)
        total_intervals = len(onset_intervals)
        staccato_pct = float(staccato_count / total_intervals * 100)
        legato_pct = 100 - staccato_pct
    else:
        legato_pct = 100.0
        staccato_pct = 0.0

    if legato_pct > 70:
        artic_desc = f"Predominantly legato ({legato_pct:.0f}%). Smooth, connected phrasing."
    elif staccato_pct > 50:
        artic_desc = f"Predominantly staccato/detached ({staccato_pct:.0f}%). Rhythmic, punchy delivery."
    else:
        artic_desc = f"Mixed articulation: {legato_pct:.0f}% legato, {staccato_pct:.0f}% staccato."

    # --- 6. STYLE TAGS ---
    style_tags = []
    if vibrato_presence > 0.4:
        style_tags.append("vibrato-rich")
    if vibrato_presence < 0.1:
        style_tags.append("straight-tone")
    if breathiness > 0.5:
        style_tags.append("breathy")
    if brightness > 0.5:
        style_tags.append("bright")
    if brightness < 0.2:
        style_tags.append("warm")
    if dynamic_range > 25:
        style_tags.append("dynamic")
    if dynamic_range < 12:
        style_tags.append("consistent-volume")
    if head_voice_pct > 60:
        style_tags.append("falsetto/head-voice")
    if chest_voice_pct > 80:
        style_tags.append("chest-voice-dominant")
    if legato_pct > 75:
        style_tags.append("legato")
    if staccato_pct > 40:
        style_tags.append("rhythmic-articulation")

    full_desc = (
        f"=== Vocal Style Analysis ===\n"
        f"Vibrato: {vibrato_desc}\n"
        f"Dynamics: {dynamics_desc}\n"
        f"Register: {register_desc}\n"
        f"Tone: {tone_desc}\n"
        f"Articulation: {artic_desc}\n"
        f"Style tags: [{', '.join(style_tags)}]"
    )

    return VocalStyleResult(
        vibrato_rate_hz=vibrato_rate,
        vibrato_extent_cents=float(vibrato_extent),
        vibrato_presence=vibrato_presence,
        vibrato_description=vibrato_desc,
        dynamic_range_db=dynamic_range,
        avg_loudness_db=avg_loudness,
        dynamic_events=dynamic_events,
        dynamics_description=dynamics_desc,
        chest_voice_pct=chest_voice_pct,
        head_voice_pct=head_voice_pct,
        register_description=register_desc,
        breathiness=breathiness,
        brightness=brightness,
        nasality=nasality,
        tone_description=tone_desc,
        legato_pct=legato_pct,
        staccato_pct=staccato_pct,
        articulation_description=artic_desc,
        style_tags=style_tags,
        full_description=full_desc,
    )
