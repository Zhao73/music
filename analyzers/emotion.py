"""Emotion and mood analysis from audio features.

Detects: overall mood, emotional arc, energy curve, tension/release patterns.
"""

from dataclasses import dataclass, field
import numpy as np
import librosa


@dataclass
class EmotionSegment:
    """Emotion for a time segment."""
    start_time: float
    end_time: float
    valence: float      # -1 (sad) to +1 (happy)
    arousal: float      # 0 (calm) to 1 (energetic)
    mood_label: str     # e.g., "happy", "sad", "energetic", "melancholic"
    tension: float      # 0 (relaxed) to 1 (tense)


@dataclass
class EmotionResult:
    # Overall mood
    overall_mood: str
    overall_valence: float      # -1 to +1
    overall_arousal: float      # 0 to 1
    mood_tags: list[str] = field(default_factory=list)

    # Emotional arc
    segments: list[EmotionSegment] = field(default_factory=list)
    emotional_arc: str = ""     # e.g., "builds from melancholic to triumphant"

    # Energy curve
    energy_curve_description: str = ""

    # Tension/release
    tension_description: str = ""

    full_description: str = ""


def _mood_from_va(valence: float, arousal: float) -> str:
    """Map valence-arousal to a mood label."""
    if valence > 0.3 and arousal > 0.5:
        return "happy / energetic"
    elif valence > 0.3 and arousal <= 0.5:
        return "peaceful / content"
    elif valence > 0 and arousal > 0.7:
        return "excited / uplifting"
    elif valence <= -0.3 and arousal > 0.5:
        return "angry / intense"
    elif valence <= -0.3 and arousal <= 0.5:
        return "sad / melancholic"
    elif valence <= 0 and arousal <= 0.3:
        return "somber / reflective"
    elif valence <= 0 and arousal > 0.5:
        return "tense / anxious"
    elif arousal > 0.7:
        return "powerful / dramatic"
    elif arousal < 0.3:
        return "calm / ambient"
    else:
        return "neutral / moderate"


def analyze_emotion(y: np.ndarray, sr: int) -> EmotionResult:
    """Analyze emotional content and mood arc of audio.

    Uses spectral features, dynamics, and harmonic content to estimate
    valence (happy/sad) and arousal (energetic/calm) over time.
    """
    hop_length = 512
    duration = len(y) / sr

    # --- Compute features for emotion estimation ---
    # RMS energy -> arousal
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    rms_norm = rms / (rms.max() + 1e-10)

    # Spectral centroid -> brightness -> valence tendency
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
    centroid_norm = centroid / (sr / 2)

    # Chroma for harmonic analysis (major=happy, minor=sad heuristic)
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)

    # Spectral contrast -> tension
    contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=hop_length)
    contrast_mean = np.mean(contrast, axis=0)
    contrast_norm = (contrast_mean - contrast_mean.min()) / (contrast_mean.max() - contrast_mean.min() + 1e-10)

    # Zero crossing rate -> noisiness / energy
    zcr = librosa.feature.zero_crossing_rate(y, hop_length=hop_length)[0]

    # Tempo variability -> arousal
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)

    # --- Segment analysis (every ~10 seconds) ---
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    segment_duration = 10.0  # seconds
    n_segments = max(1, int(duration / segment_duration))

    segments = []
    valences = []
    arousals = []

    for i in range(n_segments):
        t_start = i * segment_duration
        t_end = min((i + 1) * segment_duration, duration)

        # Frame range for this segment
        f_start = int(t_start * sr / hop_length)
        f_end = min(int(t_end * sr / hop_length), len(rms))

        if f_start >= f_end:
            continue

        # Arousal: based on RMS energy + onset strength + ZCR
        seg_rms = float(np.mean(rms_norm[f_start:f_end]))
        seg_onset = float(np.mean(onset_env[f_start:min(f_end, len(onset_env))])) if f_start < len(onset_env) else 0
        seg_zcr = float(np.mean(zcr[f_start:min(f_end, len(zcr))])) if f_start < len(zcr) else 0
        onset_norm = seg_onset / (np.max(onset_env) + 1e-10)
        arousal = min(1.0, (seg_rms * 0.4 + onset_norm * 0.4 + min(1.0, seg_zcr * 10) * 0.2))

        # Valence: based on spectral brightness + major/minor chroma tendency
        seg_brightness = float(np.mean(centroid_norm[f_start:f_end]))

        # Major vs minor: compare major triad energy vs minor triad energy
        seg_chroma = np.mean(chroma[:, f_start:f_end], axis=1)
        if seg_chroma.sum() > 0:
            seg_chroma = seg_chroma / seg_chroma.sum()
        # Check major triad intervals (0, 4, 7 semitones) vs minor (0, 3, 7)
        max_root = np.argmax(seg_chroma)
        major_strength = seg_chroma[max_root] + seg_chroma[(max_root + 4) % 12] + seg_chroma[(max_root + 7) % 12]
        minor_strength = seg_chroma[max_root] + seg_chroma[(max_root + 3) % 12] + seg_chroma[(max_root + 7) % 12]
        harmony_valence = (major_strength - minor_strength) / (major_strength + minor_strength + 1e-10)

        valence = float(np.clip(seg_brightness * 0.4 + harmony_valence * 0.6, -1.0, 1.0))

        # Tension: based on spectral contrast + dissonance
        seg_contrast = float(np.mean(contrast_norm[f_start:min(f_end, len(contrast_norm))])) if f_start < len(contrast_norm) else 0.5
        tension = min(1.0, seg_contrast * 0.5 + arousal * 0.3 + max(0, -valence) * 0.2)

        mood = _mood_from_va(valence, arousal)

        segments.append(EmotionSegment(
            start_time=t_start,
            end_time=t_end,
            valence=valence,
            arousal=arousal,
            mood_label=mood,
            tension=tension,
        ))
        valences.append(valence)
        arousals.append(arousal)

    # --- Overall mood ---
    if valences:
        overall_v = float(np.mean(valences))
        overall_a = float(np.mean(arousals))
    else:
        overall_v = 0.0
        overall_a = 0.5

    overall_mood = _mood_from_va(overall_v, overall_a)

    # --- Mood tags ---
    mood_tags = [overall_mood]
    if overall_a > 0.6:
        mood_tags.append("high-energy")
    if overall_a < 0.3:
        mood_tags.append("chill")
    if overall_v > 0.3:
        mood_tags.append("positive")
    if overall_v < -0.3:
        mood_tags.append("dark")

    # Check for emotional contrast
    if valences and (max(valences) - min(valences)) > 0.5:
        mood_tags.append("emotionally-dynamic")

    # --- Emotional arc ---
    if len(segments) >= 4:
        first_q = np.mean(valences[:len(valences) // 4])
        mid = np.mean(valences[len(valences) // 4:3 * len(valences) // 4])
        last_q = np.mean(valences[3 * len(valences) // 4:])

        first_a = np.mean(arousals[:len(arousals) // 4])
        mid_a = np.mean(arousals[len(arousals) // 4:3 * len(arousals) // 4])
        last_a = np.mean(arousals[3 * len(arousals) // 4:])

        arc_parts = []
        if first_q < mid and mid < last_q:
            arc_parts.append("progressively brighter/more positive")
        elif first_q > mid and mid > last_q:
            arc_parts.append("progressively darker/more somber")
        elif mid > first_q and mid > last_q:
            arc_parts.append("peaks emotionally in the middle then resolves")
        elif mid < first_q and mid < last_q:
            arc_parts.append("dips emotionally then recovers")
        else:
            arc_parts.append("varied emotional progression")

        if mid_a > first_a + 0.15 and mid_a > last_a + 0.15:
            arc_parts.append("energy builds to climax in the middle")
        elif last_a > first_a + 0.2:
            arc_parts.append("energy builds throughout")
        elif first_a > last_a + 0.2:
            arc_parts.append("energy gradually decreases")

        emotional_arc = "Emotional arc: " + "; ".join(arc_parts) + "."
    else:
        emotional_arc = f"Emotional arc: consistent {overall_mood} throughout."

    # --- Energy curve ---
    if arousals:
        peak_idx = int(np.argmax(arousals))
        peak_time = segments[peak_idx].start_time if peak_idx < len(segments) else 0
        energy_desc = (
            f"Energy curve: starts at {arousals[0]:.0%}, "
            f"peaks at {max(arousals):.0%} (around {peak_time:.0f}s), "
            f"ends at {arousals[-1]:.0%}."
        )
    else:
        energy_desc = "Energy curve: not enough data."

    # --- Tension description ---
    tensions = [s.tension for s in segments]
    if tensions:
        avg_tension = np.mean(tensions)
        max_tension_idx = int(np.argmax(tensions))
        tension_desc = (
            f"Average tension: {avg_tension:.0%}. "
            f"Peak tension at ~{segments[max_tension_idx].start_time:.0f}s "
            f"({segments[max_tension_idx].mood_label})."
        )
    else:
        tension_desc = ""

    # --- Full description ---
    full_desc = (
        f"=== Emotion & Mood Analysis ===\n"
        f"Overall mood: {overall_mood}\n"
        f"Valence: {overall_v:+.2f} ({'positive' if overall_v > 0 else 'negative'}), "
        f"Arousal: {overall_a:.2f} ({'energetic' if overall_a > 0.5 else 'calm'})\n"
        f"Mood tags: [{', '.join(mood_tags)}]\n"
        f"{emotional_arc}\n"
        f"{energy_desc}\n"
        f"{tension_desc}\n\n"
        f"--- Emotional Timeline ---\n"
    )
    for seg in segments:
        t = f"{seg.start_time:.0f}-{seg.end_time:.0f}s"
        full_desc += f"  [{t}] {seg.mood_label} (V:{seg.valence:+.2f} A:{seg.arousal:.2f} T:{seg.tension:.2f})\n"

    return EmotionResult(
        overall_mood=overall_mood,
        overall_valence=overall_v,
        overall_arousal=overall_a,
        mood_tags=mood_tags,
        segments=segments,
        emotional_arc=emotional_arc,
        energy_curve_description=energy_desc,
        tension_description=tension_desc,
        full_description=full_desc,
    )
