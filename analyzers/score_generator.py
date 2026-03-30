"""Generate visual music scores (PDF/MusicXML/MIDI) from analysis results using music21."""

from dataclasses import dataclass, field
import os
import tempfile

try:
    import music21
    from music21 import (
        stream, note, chord as m21chord, meter, key as m21key,
        tempo, clef, instrument, duration, pitch, layout,
        percussion, expressions, dynamics as m21dynamics,
    )
    MUSIC21_AVAILABLE = True
except ImportError:
    MUSIC21_AVAILABLE = False


@dataclass
class ScoreResult:
    """Result of score generation."""
    pdf_path: str = ""
    musicxml_path: str = ""
    midi_path: str = ""
    success: bool = False
    error: str = ""
    summary: str = ""


def is_available() -> bool:
    """Check if music21 is installed."""
    return MUSIC21_AVAILABLE


def _parse_key_signature(key_str: str):
    """Parse key string like 'C major' or 'A minor' into music21 Key."""
    if not MUSIC21_AVAILABLE or not key_str:
        return None
    try:
        parts = key_str.strip().split()
        if len(parts) >= 2:
            root = parts[0]
            mode = parts[1].lower()
            return m21key.Key(root, mode)
        return m21key.Key(parts[0])
    except Exception:
        return m21key.Key("C", "major")


def _duration_type_to_music21(dur_type: str, duration_sec: float, beat_dur: float):
    """Convert duration type string to music21 duration type."""
    ratio = duration_sec / beat_dur if beat_dur > 0 else 1.0

    if ratio < 0.3:
        return "eighth"
    elif ratio < 0.6:
        return "eighth"
    elif ratio < 1.2:
        return "quarter"
    elif ratio < 2.0:
        return "half"
    elif ratio < 3.5:
        return "half"
    else:
        return "whole"


def _build_melody_part(note_events, key_sig, time_sig_str, bpm):
    """Build the melody/vocal part from note events."""
    part = stream.Part()
    part.partName = "Vocal Melody"
    part.partAbbreviation = "Vox"
    inst = instrument.Instrument()
    inst.instrumentName = "Voice"
    part.insert(0, inst)

    # Add clef, key, time signature, tempo
    part.insert(0, clef.TrebleClef())
    if key_sig:
        part.insert(0, key_sig)

    try:
        nums = time_sig_str.split("/")
        ts = meter.TimeSignature(time_sig_str)
    except Exception:
        ts = meter.TimeSignature("4/4")
    part.insert(0, ts)

    mm = tempo.MetronomeMark(number=bpm)
    part.insert(0, mm)

    if not note_events:
        # Add a whole rest if no notes
        r = note.Rest()
        r.duration = duration.Duration("whole")
        part.append(r)
        return part

    beat_dur = 60.0 / bpm if bpm > 0 else 0.5

    # Convert note events to music21 notes
    prev_end = 0.0
    for ne in note_events:
        # Add rest if gap
        gap = ne.start_time - prev_end
        if gap > 0.1:
            r = note.Rest()
            r_type = _duration_type_to_music21("", gap, beat_dur)
            r.duration = duration.Duration(r_type)
            part.append(r)

        # Create note
        try:
            n = note.Note(ne.note_name)
        except Exception:
            n = note.Note("C4")

        n_type = _duration_type_to_music21(ne.duration_type, ne.duration, beat_dur)
        n.duration = duration.Duration(n_type)

        # Add velocity
        n.volume.velocity = int(ne.velocity_est * 127)

        part.append(n)
        prev_end = ne.end_time

    return part


def _build_chord_part(chord_events, key_sig, time_sig_str, bpm, total_duration):
    """Build chord accompaniment part from chord events."""
    part = stream.Part()
    part.partName = "Chords"
    part.partAbbreviation = "Chd"
    inst = instrument.Piano()
    part.insert(0, inst)
    part.insert(0, clef.TrebleClef())
    if key_sig:
        part.insert(0, key_sig)
    try:
        ts = meter.TimeSignature(time_sig_str)
    except Exception:
        ts = meter.TimeSignature("4/4")
    part.insert(0, ts)

    if not chord_events:
        r = note.Rest()
        r.duration = duration.Duration("whole")
        part.append(r)
        return part

    beat_dur = 60.0 / bpm if bpm > 0 else 0.5

    # Map chord qualities to pitch offsets from root
    quality_map = {
        "":      [0, 4, 7],
        "m":     [0, 3, 7],
        "7":     [0, 4, 7, 10],
        "m7":    [0, 3, 7, 10],
        "maj7":  [0, 4, 7, 11],
        "dim":   [0, 3, 6],
        "aug":   [0, 4, 8],
        "sus4":  [0, 5, 7],
        "sus2":  [0, 2, 7],
    }

    prev_end = 0.0
    for ce in chord_events:
        # Add rest for gaps
        gap = ce.start_time - prev_end
        if gap > 0.1:
            r = note.Rest()
            r_type = _duration_type_to_music21("", gap, beat_dur)
            r.duration = duration.Duration(r_type)
            part.append(r)

        # Build chord
        chord_dur = ce.end_time - ce.start_time
        c_type = _duration_type_to_music21("", chord_dur, beat_dur)

        try:
            root_name = ce.root_note
            quality = ce.quality if ce.quality else ""
            offsets = quality_map.get(quality, [0, 4, 7])

            root_p = pitch.Pitch(root_name + "3")  # Chord in octave 3
            pitches = []
            for off in offsets:
                p = pitch.Pitch(root_p.midi + off)
                pitches.append(p.nameWithOctave)

            c = m21chord.Chord(pitches)
            c.duration = duration.Duration(c_type)
            part.append(c)
        except Exception:
            r = note.Rest()
            r.duration = duration.Duration(c_type)
            part.append(r)

        prev_end = ce.end_time

    return part


def _build_drum_part(drum_result, time_sig_str, bpm):
    """Build a simplified drum part from drum analysis."""
    part = stream.Part()
    part.partName = "Drums"
    part.partAbbreviation = "Dr"

    perc = instrument.UnpitchedPercussion()
    part.insert(0, perc)
    part.insert(0, clef.PercussionClef())

    try:
        ts = meter.TimeSignature(time_sig_str)
    except Exception:
        ts = meter.TimeSignature("4/4")
    part.insert(0, ts)

    if not drum_result or not drum_result.main_pattern:
        r = note.Rest()
        r.duration = duration.Duration("whole")
        part.append(r)
        return part

    # Parse the pattern string: K=kick(36), S=snare(38), H=hihat(42), .=rest
    # Each character = one 16th note
    pattern = drum_result.main_pattern
    midi_map = {"K": 36, "S": 38, "H": 42, "C": 49, "T": 45}

    beat_dur = 60.0 / bpm if bpm > 0 else 0.5
    sixteenth_dur = beat_dur / 4

    # Repeat pattern to fill ~4 bars
    bar_length = 16  # 16th notes per bar in 4/4
    total_chars = bar_length * 4
    full_pattern = (pattern * ((total_chars // max(len(pattern), 1)) + 1))[:total_chars]

    for ch in full_pattern:
        if ch in midi_map:
            n = note.Unpitched()
            n.displayName = ch
            n.storedInstrument = instrument.UnpitchedPercussion()
            # Map to standard GM percussion
            if ch == "K":
                n.displayName = "Bass Drum"
            elif ch == "S":
                n.displayName = "Snare"
            elif ch == "H":
                n.displayName = "Hi-Hat"
            n.duration = duration.Duration("16th")
            part.append(n)
        else:
            r = note.Rest()
            r.duration = duration.Duration("16th")
            part.append(r)

    return part


def _add_lyrics_to_part(part, lyrics_segments, note_events):
    """Add lyrics to the melody part, aligned to notes."""
    if not lyrics_segments or not note_events:
        return

    # Build a list of words with timestamps
    words = []
    for seg in lyrics_segments:
        text = seg.get("text", "").strip()
        start = seg.get("start", 0)
        if text:
            for word in text.split():
                words.append((start, word))
                start += 0.3  # Approximate word spacing

    # Assign words to notes by nearest time
    word_idx = 0
    notes_in_part = [n for n in part.recurse().notes if isinstance(n, note.Note)]

    for i, n_obj in enumerate(notes_in_part):
        if word_idx >= len(words):
            break
        # Find offset of this note
        n_offset = n_obj.offset
        # Simple assignment: one word per note, in order
        _, word = words[word_idx]
        n_obj.lyric = word
        word_idx += 1


def generate_score(
    note_events=None,
    chord_events=None,
    drum_result=None,
    key_str: str = "C major",
    time_signature: str = "4/4",
    bpm: float = 120.0,
    total_duration: float = 180.0,
    lyrics_segments=None,
    title: str = "MusicLens Analysis",
) -> ScoreResult:
    """Generate visual score from analysis results.

    Returns ScoreResult with paths to PDF, MusicXML, and MIDI files.
    """
    result = ScoreResult()

    if not MUSIC21_AVAILABLE:
        result.error = "music21 is not installed. Run: pip install music21"
        return result

    try:
        # Create the score
        s = stream.Score()
        s.metadata = music21.metadata.Metadata()
        s.metadata.title = title
        s.metadata.composer = "MusicLens Auto-Transcription"

        key_sig = _parse_key_signature(key_str)

        # --- Melody Part ---
        melody_part = _build_melody_part(note_events or [], key_sig, time_signature, bpm)
        if lyrics_segments and note_events:
            _add_lyrics_to_part(melody_part, lyrics_segments, note_events)
        s.insert(0, melody_part)

        # --- Chord Part ---
        if chord_events:
            chord_part = _build_chord_part(chord_events, key_sig, time_signature, bpm, total_duration)
            s.insert(0, chord_part)

        # --- Drum Part ---
        if drum_result and drum_result.main_pattern:
            drum_part = _build_drum_part(drum_result, time_signature, bpm)
            s.insert(0, drum_part)

        # --- Export ---
        tmp_dir = tempfile.mkdtemp(prefix="musiclens_score_")

        # MusicXML (always works)
        xml_path = os.path.join(tmp_dir, "score.musicxml")
        s.write("musicxml", fp=xml_path)
        result.musicxml_path = xml_path

        # MIDI
        midi_path = os.path.join(tmp_dir, "score.mid")
        s.write("midi", fp=midi_path)
        result.midi_path = midi_path

        # PDF (requires MuseScore or Lilypond installed)
        try:
            pdf_path = os.path.join(tmp_dir, "score.pdf")
            s.write("lily.pdf", fp=pdf_path)
            result.pdf_path = pdf_path
        except Exception:
            # Fallback: try musicxml.png via music21's built-in
            try:
                png_path = os.path.join(tmp_dir, "score.png")
                s.write("musicxml.png", fp=png_path)
                result.pdf_path = png_path  # Use PNG as fallback
            except Exception:
                result.pdf_path = ""  # PDF generation not available

        result.success = True

        # Summary
        n_notes = len(note_events) if note_events else 0
        n_chords = len(chord_events) if chord_events else 0
        has_drums = bool(drum_result and drum_result.main_pattern)
        parts_list = ["Melody"]
        if chord_events:
            parts_list.append("Chords")
        if has_drums:
            parts_list.append("Drums")

        result.summary = (
            f"Score generated: {' + '.join(parts_list)}\n"
            f"Key: {key_str}, Time: {time_signature}, BPM: {bpm:.0f}\n"
            f"Notes: {n_notes}, Chords: {n_chords}, Drums: {'Yes' if has_drums else 'No'}\n"
            f"Formats: MusicXML{' + MIDI' if result.midi_path else ''}"
            f"{' + PDF' if result.pdf_path else ' (PDF needs MuseScore/Lilypond)'}"
        )

    except Exception as e:
        result.error = f"Score generation failed: {e}"

    return result
