"""Enhanced melody extraction with note-by-note timing, duration, and intervals."""

from dataclasses import dataclass, field
import numpy as np
import librosa


@dataclass
class NoteEvent:
    """A single note with precise timing."""
    note_name: str      # e.g., "C4", "A#3"
    midi_number: int    # MIDI note number
    start_time: float   # seconds
    end_time: float     # seconds
    duration: float     # seconds
    frequency_hz: float # average Hz during this note
    duration_type: str  # "short", "medium", "long", "sustained"
    velocity_est: float # estimated relative loudness 0-1


@dataclass
class MelodyResult:
    pitch_hz: np.ndarray        # Raw f0 contour in Hz
    note_sequence: list[str]    # Quantized note names
    note_events: list[NoteEvent]  # Full note-by-note with timing
    vocal_range_low: str
    vocal_range_high: str
    avg_pitch_hz: float
    intervals: list[str]        # Interval sequence (e.g., "+M3", "-P5")
    contour_per_section: str    # Contour description per section
    melody_notation: str        # Simplified notation string
    description: str


def _classify_duration(dur: float, beat_duration: float) -> str:
    """Classify note duration relative to the beat."""
    ratio = dur / beat_duration if beat_duration > 0 else 1.0
    if ratio < 0.3:
        return "short (staccato)"
    elif ratio < 0.8:
        return "medium"
    elif ratio < 1.5:
        return "long (one beat)"
    elif ratio < 3.0:
        return "sustained (2 beats)"
    else:
        return "very sustained (held note)"


def _interval_name(semitones: int) -> str:
    """Convert semitone distance to interval name."""
    direction = "+" if semitones >= 0 else "-"
    s = abs(semitones)
    names = {
        0: "unison", 1: "m2", 2: "M2", 3: "m3", 4: "M3",
        5: "P4", 6: "tritone", 7: "P5", 8: "m6", 9: "M6",
        10: "m7", 11: "M7", 12: "octave",
    }
    if s in names:
        return f"{direction}{names[s]}"
    elif s > 12:
        return f"{direction}{s} semitones (>{names.get(s % 12, str(s % 12) + 'st')}+octave)"
    return f"{direction}{s}st"


def extract_melody(y: np.ndarray, sr: int, bpm: float = 120.0) -> MelodyResult:
    """Extract detailed melody with note-by-note timing and intervals.

    Args:
        y: Audio waveform.
        sr: Sample rate.
        bpm: Detected BPM (for duration classification).
    """
    # PYIN pitch tracking
    f0, voiced_flag, voiced_probs = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C7"),
        sr=sr,
    )

    hop_length = 512  # librosa default
    times = librosa.frames_to_time(np.arange(len(f0)), sr=sr, hop_length=hop_length)

    # RMS energy per frame for velocity estimation
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    if len(rms) < len(f0):
        rms = np.pad(rms, (0, len(f0) - len(rms)))
    elif len(rms) > len(f0):
        rms = rms[:len(f0)]
    rms_max = rms.max() if rms.max() > 0 else 1.0

    voiced_f0 = f0[~np.isnan(f0)]

    if len(voiced_f0) == 0:
        return MelodyResult(
            pitch_hz=f0, note_sequence=[], note_events=[],
            vocal_range_low="N/A", vocal_range_high="N/A",
            avg_pitch_hz=0.0, intervals=[], contour_per_section="",
            melody_notation="", description="No pitched content detected",
        )

    # Convert to MIDI
    midi_all = np.where(np.isnan(f0), 0, librosa.hz_to_midi(np.where(np.isnan(f0), 440, f0)))

    # --- Build note events by grouping consecutive frames with same MIDI note ---
    beat_duration = 60.0 / bpm if bpm > 0 else 0.5
    note_events = []
    current_midi = 0
    current_start = 0
    current_hz_sum = 0.0
    current_rms_sum = 0.0
    current_count = 0

    for i in range(len(f0)):
        if np.isnan(f0[i]):
            # Silence / unvoiced -> close current note
            if current_count > 0:
                avg_hz = current_hz_sum / current_count
                avg_rms = current_rms_sum / current_count
                dur = times[i] - times[current_start]
                note_events.append(NoteEvent(
                    note_name=librosa.midi_to_note(current_midi),
                    midi_number=current_midi,
                    start_time=float(times[current_start]),
                    end_time=float(times[i]),
                    duration=float(dur),
                    frequency_hz=float(avg_hz),
                    duration_type=_classify_duration(dur, beat_duration),
                    velocity_est=float(min(1.0, avg_rms / rms_max)),
                ))
                current_count = 0
        else:
            rounded_midi = int(round(midi_all[i]))
            if current_count == 0:
                # Start new note
                current_midi = rounded_midi
                current_start = i
                current_hz_sum = f0[i]
                current_rms_sum = rms[i]
                current_count = 1
            elif rounded_midi == current_midi:
                # Continue same note
                current_hz_sum += f0[i]
                current_rms_sum += rms[i]
                current_count += 1
            else:
                # Different note -> close previous, start new
                avg_hz = current_hz_sum / current_count
                avg_rms = current_rms_sum / current_count
                dur = times[i] - times[current_start]
                note_events.append(NoteEvent(
                    note_name=librosa.midi_to_note(current_midi),
                    midi_number=current_midi,
                    start_time=float(times[current_start]),
                    end_time=float(times[i]),
                    duration=float(dur),
                    frequency_hz=float(avg_hz),
                    duration_type=_classify_duration(dur, beat_duration),
                    velocity_est=float(min(1.0, avg_rms / rms_max)),
                ))
                current_midi = rounded_midi
                current_start = i
                current_hz_sum = f0[i]
                current_rms_sum = rms[i]
                current_count = 1

    # Close last note
    if current_count > 0:
        avg_hz = current_hz_sum / current_count
        avg_rms = current_rms_sum / current_count
        dur = times[-1] - times[current_start]
        note_events.append(NoteEvent(
            note_name=librosa.midi_to_note(current_midi),
            midi_number=current_midi,
            start_time=float(times[current_start]),
            end_time=float(times[-1]),
            duration=float(dur),
            frequency_hz=float(avg_hz),
            duration_type=_classify_duration(dur, beat_duration),
            velocity_est=float(min(1.0, avg_rms / rms_max)),
        ))

    # Filter out very short artifacts (< 50ms)
    note_events = [n for n in note_events if n.duration >= 0.05]

    # Note names sequence
    note_names = [n.note_name for n in note_events]

    # Vocal range
    midi_notes = librosa.hz_to_midi(voiced_f0)
    low_note = librosa.midi_to_note(int(round(midi_notes.min())))
    high_note = librosa.midi_to_note(int(round(midi_notes.max())))

    # --- Intervals between consecutive notes ---
    intervals = []
    for i in range(1, len(note_events)):
        semitone_diff = note_events[i].midi_number - note_events[i - 1].midi_number
        intervals.append(_interval_name(semitone_diff))

    # --- Contour per quarter of the song ---
    total_dur = len(y) / sr
    quarters = ["", "", "", ""]
    quarter_names = ["Opening (0-25%)", "Development (25-50%)", "Climax (50-75%)", "Resolution (75-100%)"]
    for q in range(4):
        q_start = q * total_dur / 4
        q_end = (q + 1) * total_dur / 4
        q_notes = [n for n in note_events if n.start_time >= q_start and n.start_time < q_end]
        if len(q_notes) >= 2:
            first_avg = np.mean([n.midi_number for n in q_notes[:len(q_notes) // 3 + 1]])
            last_avg = np.mean([n.midi_number for n in q_notes[-len(q_notes) // 3 - 1:]])
            avg_vel = np.mean([n.velocity_est for n in q_notes])
            if last_avg > first_avg + 2:
                direction = "ascending"
            elif last_avg < first_avg - 2:
                direction = "descending"
            else:
                direction = "stable"
            intensity = "loud" if avg_vel > 0.6 else "soft" if avg_vel < 0.3 else "moderate"
            quarters[q] = f"{quarter_names[q]}: {direction}, {intensity} dynamics"
        elif len(q_notes) == 1:
            quarters[q] = f"{quarter_names[q]}: sparse/held notes"
        else:
            quarters[q] = f"{quarter_names[q]}: instrumental/silent"

    contour_per_section = "\n".join(quarters)

    # --- Simplified notation string (first 30 notes) ---
    notation_parts = []
    for n in note_events[:50]:
        dur_symbol = ""
        if "short" in n.duration_type:
            dur_symbol = "."
        elif "sustained" in n.duration_type or "very" in n.duration_type:
            dur_symbol = "---"
        elif "long" in n.duration_type:
            dur_symbol = "-"
        vel_symbol = ""
        if n.velocity_est > 0.7:
            vel_symbol = "!"
        elif n.velocity_est < 0.25:
            vel_symbol = "~"
        notation_parts.append(f"{n.note_name}{dur_symbol}{vel_symbol}")

    melody_notation = " ".join(notation_parts)
    if len(note_events) > 50:
        melody_notation += f" ... ({len(note_events)} notes total)"

    # Top notes
    unique_notes, counts = np.unique(
        [librosa.midi_to_note(int(round(m))) for m in midi_notes],
        return_counts=True,
    )
    top_notes = unique_notes[np.argsort(-counts)[:5]]

    # Duration statistics
    durations = [n.duration for n in note_events]
    short_count = sum(1 for n in note_events if "short" in n.duration_type)
    long_count = sum(1 for n in note_events if "sustained" in n.duration_type or "long" in n.duration_type)
    total_notes = len(note_events)

    if total_notes > 0:
        short_pct = short_count / total_notes * 100
        long_pct = long_count / total_notes * 100
    else:
        short_pct = long_pct = 0

    # Interval statistics
    step_intervals = sum(1 for iv in intervals if "m2" in iv or "M2" in iv or "unison" in iv)
    leap_intervals = len(intervals) - step_intervals
    step_pct = step_intervals / len(intervals) * 100 if intervals else 0

    # Overall description
    description = (
        f"Vocal range: {low_note} to {high_note} "
        f"({int(round(midi_notes.max() - midi_notes.min()))} semitones). "
        f"Total notes detected: {total_notes}. "
        f"Most frequent notes: {', '.join(top_notes)}.\n"
        f"Note durations: {short_pct:.0f}% short/staccato, {long_pct:.0f}% long/sustained. "
        f"Average note duration: {np.mean(durations):.2f}s.\n"
        f"Melodic movement: {step_pct:.0f}% stepwise, {100-step_pct:.0f}% leaps. "
        f"{'Smooth, flowing melody.' if step_pct > 65 else 'Jumpy melody with many leaps.' if step_pct < 40 else 'Mixed stepwise and leaping motion.'}"
    )

    return MelodyResult(
        pitch_hz=f0,
        note_sequence=note_names,
        note_events=note_events,
        vocal_range_low=low_note,
        vocal_range_high=high_note,
        avg_pitch_hz=float(np.mean(voiced_f0)),
        intervals=intervals,
        contour_per_section=contour_per_section,
        melody_notation=melody_notation,
        description=description,
    )
