"""Detailed dynamics and volume analysis.

Produces a per-section volume map, loudness contour, and dynamic markings
that map directly to musical notation concepts.
"""

from dataclasses import dataclass, field
import numpy as np
import librosa


@dataclass
class DynamicMark:
    """A musical dynamic marking at a specific time."""
    time: float
    marking: str        # "pp", "p", "mp", "mf", "f", "ff", "sfz"
    db_level: float


@dataclass
class VolumeSegment:
    """Volume info for a song section."""
    start_time: float
    end_time: float
    avg_db: float
    peak_db: float
    marking: str
    trend: str          # "steady", "crescendo", "decrescendo", "swell"


@dataclass
class DynamicsResult:
    # Overall
    overall_loudness_db: float
    dynamic_range_db: float
    loudness_units: str     # LUFS-like description

    # Per-section
    volume_map: list[VolumeSegment] = field(default_factory=list)

    # Dynamic markings timeline
    markings: list[DynamicMark] = field(default_factory=list)

    # Detailed description
    description: str = ""
    volume_map_text: str = ""


def _db_to_marking(db: float) -> str:
    """Convert dB to musical dynamic marking."""
    if db < -45:
        return "pp (pianissimo)"
    elif db < -35:
        return "p (piano)"
    elif db < -25:
        return "mp (mezzo-piano)"
    elif db < -18:
        return "mf (mezzo-forte)"
    elif db < -10:
        return "f (forte)"
    else:
        return "ff (fortissimo)"


def _db_to_short(db: float) -> str:
    if db < -45:
        return "pp"
    elif db < -35:
        return "p"
    elif db < -25:
        return "mp"
    elif db < -18:
        return "mf"
    elif db < -10:
        return "f"
    else:
        return "ff"


def analyze_dynamics(y: np.ndarray, sr: int, sections: list = None) -> DynamicsResult:
    """Comprehensive dynamics analysis.

    Args:
        y: Audio waveform.
        sr: Sample rate.
        sections: Optional list of Section objects for per-section analysis.
    """
    hop_length = 512
    duration = len(y) / sr

    # --- Loudness analysis ---
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    rms_db = librosa.amplitude_to_db(rms + 1e-10)
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)

    overall_loudness = float(np.mean(rms_db))
    dynamic_range = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 5))

    if overall_loudness > -15:
        loudness_desc = "Loud overall (heavily compressed/mastered)"
    elif overall_loudness > -25:
        loudness_desc = "Moderate loudness (typical pop/rock)"
    else:
        loudness_desc = "Quiet overall (acoustic/ambient style)"

    # --- Per-section volume map ---
    volume_map = []
    if sections:
        segment_boundaries = [(s.start_time, s.end_time, s.label) for s in sections]
    else:
        # Auto-segment every 15 seconds
        seg_dur = 15.0
        segment_boundaries = [
            (i * seg_dur, min((i + 1) * seg_dur, duration), f"Segment {i+1}")
            for i in range(max(1, int(duration / seg_dur)))
        ]

    for start, end, label in segment_boundaries:
        f_start = int(start * sr / hop_length)
        f_end = min(int(end * sr / hop_length), len(rms_db))
        if f_start >= f_end:
            continue

        seg_db = rms_db[f_start:f_end]
        avg_db = float(np.mean(seg_db))
        peak_db = float(np.max(seg_db))

        # Trend detection
        if len(seg_db) >= 4:
            first_half = np.mean(seg_db[:len(seg_db) // 2])
            second_half = np.mean(seg_db[len(seg_db) // 2:])
            diff = second_half - first_half
            if diff > 4:
                trend = "crescendo"
            elif diff < -4:
                trend = "decrescendo"
            elif abs(diff) < 2:
                trend = "steady"
            else:
                # Check for swell (up then down)
                q1 = np.mean(seg_db[:len(seg_db) // 4])
                q2 = np.mean(seg_db[len(seg_db) // 4:len(seg_db) // 2])
                q3 = np.mean(seg_db[len(seg_db) // 2:3 * len(seg_db) // 4])
                q4 = np.mean(seg_db[3 * len(seg_db) // 4:])
                if q2 > q1 and q3 > q4:
                    trend = "swell (crescendo then decrescendo)"
                else:
                    trend = "fluctuating"
        else:
            trend = "steady"

        volume_map.append(VolumeSegment(
            start_time=start,
            end_time=end,
            avg_db=avg_db,
            peak_db=peak_db,
            marking=_db_to_marking(avg_db),
            trend=trend,
        ))

    # --- Dynamic markings timeline ---
    markings = []
    # Sample every 5 seconds
    step = max(1, int(5.0 * sr / hop_length))
    prev_marking = ""
    for i in range(0, len(rms_db), step):
        window_end = min(i + step, len(rms_db))
        avg = float(np.mean(rms_db[i:window_end]))
        mark = _db_to_short(avg)
        if mark != prev_marking:
            markings.append(DynamicMark(
                time=float(times[i]),
                marking=mark,
                db_level=avg,
            ))
            prev_marking = mark

    # --- Build text outputs ---
    volume_map_lines = ["=== Volume Map (per section) ==="]
    for vs in volume_map:
        from utils.audio_io import format_time
        t1 = format_time(vs.start_time)
        t2 = format_time(vs.end_time)
        bar = "=" * max(1, int((vs.avg_db + 60) / 2))
        volume_map_lines.append(
            f"  [{t1}-{t2}] {vs.marking:<25} {vs.trend:<15} |{bar}|"
        )

    volume_map_text = "\n".join(volume_map_lines)

    marking_timeline = "Dynamic markings: "
    for m in markings:
        from utils.audio_io import format_time
        marking_timeline += f"[{format_time(m.time)}]{m.marking} → "
    if markings:
        marking_timeline = marking_timeline.rstrip(" → ")

    description = (
        f"=== Dynamics Analysis ===\n"
        f"Overall loudness: {overall_loudness:.1f} dB ({loudness_desc})\n"
        f"Dynamic range: {dynamic_range:.1f} dB\n"
        f"Overall dynamic marking: {_db_to_marking(overall_loudness)}\n\n"
        f"{marking_timeline}\n\n"
        f"{volume_map_text}"
    )

    return DynamicsResult(
        overall_loudness_db=overall_loudness,
        dynamic_range_db=dynamic_range,
        loudness_units=loudness_desc,
        volume_map=volume_map,
        markings=markings,
        description=description,
        volume_map_text=volume_map_text,
    )
