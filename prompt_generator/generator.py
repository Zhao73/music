"""Assembles all analysis results into comprehensive reproduction prompts."""

from dataclasses import dataclass
from prompt_generator.templates import (
    SUNO_STYLE_TEMPLATE, SUNO_LYRICS_TEMPLATE,
    GENERIC_TEMPLATE, UDIO_TEMPLATE, LYRIA_PROMPT_TEMPLATE,
)
from config import LANGUAGE_OPTIONS


@dataclass
class PromptResult:
    # Suno Custom Mode — two separate fields
    suno_style: str             # → paste into Suno "スタイル / Style" box
    suno_lyrics: str            # → paste into Suno "歌詞 / Lyrics" box
    suno_lyrics_translated: str # → translated lyrics for Suno
    # Lyria prompt
    lyria_prompt: str           # → for Google Lyria generation
    # Other formats
    udio_prompt: str
    generic_prompt: str
    translated_prompt: str


def _guess_genre(instruments: list[str], bpm: float, energy: str, feel: str, mood: str = "") -> str:
    inst_lower = " ".join(instruments).lower()
    mood_lower = mood.lower()

    if "electronic" in inst_lower or "synthesizer" in inst_lower:
        if bpm > 128:
            return "Electronic / EDM"
        if bpm > 100:
            return "Synth Pop / Electronic Pop"
        return "Electronic / Ambient"
    if "guitar (electric)" in inst_lower and "drums" in inst_lower:
        if "high" in energy:
            return "Rock"
        return "Pop Rock"
    if "acoustic guitar" in inst_lower:
        if "sad" in mood_lower or "melancholic" in mood_lower:
            return "Folk / Acoustic Ballad"
        return "Folk / Acoustic"
    if "piano" in inst_lower or "keys" in inst_lower:
        if "slow" in feel or "ballad" in feel:
            return "Piano Ballad"
        return "Pop"
    if "strings" in inst_lower:
        return "Orchestral / Cinematic"
    if bpm > 140:
        return "Dance / Uptempo"
    if bpm < 76:
        return "Ballad / Slow"
    return "Pop"


def _build_structured_lyrics(
    lyrics_text: str,
    sections: list,
    lyrics_segments: list = None,
    chord_per_section: dict = None,
    dynamic_events: list = None,
) -> str:
    """Build lyrics with section markers and musical annotations.

    Uses overlap-based matching instead of midpoint for better accuracy.
    """
    if not sections or not lyrics_text:
        return lyrics_text or ""

    result = []
    for section in sections:
        # Build annotated section header
        header = f"[{section.label}]"

        # Add chord annotation if available
        if chord_per_section:
            for label_key, prog in chord_per_section.items():
                if label_key.lower().replace(" ", "") in section.label.lower().replace(" ", "") or \
                   section.label.lower().replace(" ", "") in label_key.lower().replace(" ", ""):
                    header = f"[{section.label}] (chords: {prog})"
                    break

        result.append(header)

        if lyrics_segments:
            section_lyrics = []
            for seg in lyrics_segments:
                # Overlap-based matching: segment belongs to section if >50% overlap
                seg_start = seg["start"]
                seg_end = seg["end"]
                seg_dur = seg_end - seg_start
                if seg_dur <= 0:
                    continue

                overlap_start = max(seg_start, section.start_time)
                overlap_end = min(seg_end, section.end_time)
                overlap = max(0, overlap_end - overlap_start)

                if overlap > seg_dur * 0.5:
                    section_lyrics.append(seg["text"])

            if section_lyrics:
                for line in section_lyrics:
                    if line.strip():
                        result.append(line.strip())
            else:
                result.append("(instrumental)")
        result.append("")

    # Fallback: if no segments matched, distribute plain text
    text_in_result = [l for l in result if l.strip() and not l.startswith("[") and l != "(instrumental)"]
    if not text_in_result and lyrics_text.strip():
        lines = [l.strip() for l in lyrics_text.strip().split("\n") if l.strip()]
        if lines and sections:
            result = []
            n_sections = len(sections)
            lines_per = max(1, len(lines) // n_sections)
            for i, section in enumerate(sections):
                result.append(f"[{section.label}]")
                start_idx = i * lines_per
                end_idx = start_idx + lines_per if i < n_sections - 1 else len(lines)
                for line in lines[start_idx:end_idx]:
                    result.append(line)
                result.append("")
            return "\n".join(result)

    return "\n".join(result)


def _build_structure_detail(sections: list) -> str:
    if not sections:
        return "Unknown structure"
    from utils.audio_io import format_time
    lines = [" → ".join(s.label for s in sections), ""]
    for s in sections:
        dur = s.end_time - s.start_time
        lines.append(f"  {s.label}: {format_time(s.start_time)} - {format_time(s.end_time)} ({dur:.1f}s)")
    return "\n".join(lines)


def _format_chord_per_section(chord_per_section: dict) -> str:
    if not chord_per_section:
        return "  (not available)"
    lines = []
    for label, prog in chord_per_section.items():
        lines.append(f"  {label}: {prog}")
    return "\n".join(lines)


def _format_dynamic_events(dynamic_events: list) -> str:
    if not dynamic_events:
        return "No significant dynamic changes"
    from utils.audio_io import format_time
    parts = []
    for e in dynamic_events[:10]:
        parts.append(f"{format_time(e.time)}: {e.marking}")
    return " → ".join(parts)


def _describe_drum_hits(pattern: str, name: str) -> str:
    """Describe where drum hits land in musical terms."""
    if not pattern:
        return f"{name} on standard beats"
    hits = [i + 1 for i, c in enumerate(pattern.replace("|", "")) if c in "Xx"]
    if not hits:
        return f"no {name}"
    beat_positions = []
    for h in hits[:8]:
        beat = (h - 1) // 4 + 1
        sub = (h - 1) % 4 + 1
        if sub == 1:
            beat_positions.append(f"beat {beat}")
        else:
            beat_positions.append(f"beat {beat}.{sub}")
    return f"{name} on {', '.join(beat_positions)}"


def generate_prompt(
    lyrics_text: str,
    translated_text: str,
    bpm: float,
    key: str,
    time_signature: str,
    feel: str,
    energy: str,
    instruments: list[str],
    vocal_range: str,
    melody_description: str,
    melody_contour: str,
    melody_notation: str,
    sections: list,
    source_lang: str,
    target_lang: str = None,
    # Emotion
    mood: str = "",
    mood_tags: list[str] = None,
    emotional_arc: str = "",
    energy_curve: str = "",
    # Vocal style
    vocal_style_tags: list[str] = None,
    vibrato_desc: str = "",
    register_desc: str = "",
    tone_desc: str = "",
    articulation_desc: str = "",
    # Dynamics
    dynamics_marking: str = "",
    dynamic_range: str = "",
    volume_map: str = "",
    dynamic_events: list = None,
    rhythm_description: str = "",
    lyrics_segments: list = None,
    # Chords
    chord_progression: str = "",
    chord_per_section: dict = None,
    chord_description: str = "",
    # Drums
    drum_pattern: str = "",
    drum_groove: str = "",
    drum_description: str = "",
    drum_notation: str = "",
    kick_pattern: str = "",
    snare_pattern: str = "",
    hihat_pattern: str = "",
) -> PromptResult:
    """Generate comprehensive reproduction prompts with all analysis data."""
    genre = _guess_genre(instruments, bpm, energy, feel, mood)
    instruments_str = ", ".join(instruments)
    lang_name = LANGUAGE_OPTIONS.get(source_lang, source_lang)
    vocal_tags_str = ", ".join(vocal_style_tags) if vocal_style_tags else "natural"
    mood_tags_str = ", ".join(mood_tags) if mood_tags else mood
    dynamic_events_str = _format_dynamic_events(dynamic_events) if dynamic_events else "gradual"
    structured_lyrics = _build_structured_lyrics(
        lyrics_text, sections, lyrics_segments,
        chord_per_section=chord_per_section,
        dynamic_events=dynamic_events,
    )
    structure_detail = _build_structure_detail(sections)
    chord_section_str = _format_chord_per_section(chord_per_section or {})

    kick_desc = _describe_drum_hits(kick_pattern, "kick")
    snare_desc = _describe_drum_hits(snare_pattern, "snare")

    # Common template kwargs
    common = dict(
        genre=genre,
        bpm=f"{bpm:.0f}",
        key=key,
        time_signature=time_signature,
        mood=mood,
        mood_tags=mood_tags_str,
        emotional_arc=emotional_arc or "consistent throughout",
        energy_curve=energy_curve or "steady",
        feel=feel,
        energy=energy,
        rhythm_description=rhythm_description or feel,
        instruments=instruments_str,
        vocal_range=vocal_range,
        vocal_style_tags=vocal_tags_str,
        vibrato=vibrato_desc or "natural vibrato",
        register=register_desc or "mixed register",
        tone=tone_desc or "natural tone",
        articulation=articulation_desc or "legato",
        dynamics_marking=dynamics_marking or "mf",
        dynamic_range=dynamic_range or "moderate",
        volume_map=volume_map or "",
        melody_description=melody_description,
        melody_contour=melody_contour or "",
        melody_notation=melody_notation or "",
        structure_detail=structure_detail,
        chord_progression=chord_progression or "not detected",
        chord_per_section=chord_section_str,
        drum_groove=drum_groove or "standard",
        drum_notation=drum_notation or "",
        kick_pattern=kick_pattern or "X...|....|X.X.|....",
        snare_pattern=snare_pattern or "....|X...|....|X...",
        hihat_pattern=hihat_pattern or "X.X.|X.X.|X.X.|X.X.",
        kick_description=kick_desc,
        snare_description=snare_desc,
    )

    # ==========================================================
    # SUNO — Split into Style + Lyrics (matches Suno Custom UI)
    # ==========================================================
    suno_style = SUNO_STYLE_TEMPLATE.format(
        **common,
        language=lang_name,
    )

    suno_lyrics = SUNO_LYRICS_TEMPLATE.format(
        structured_lyrics=structured_lyrics,
    )

    # Translated Suno lyrics
    suno_lyrics_translated = ""
    if translated_text and target_lang:
        target_lang_name = LANGUAGE_OPTIONS.get(target_lang, target_lang)
        translated_structured = _build_structured_lyrics(translated_text, sections)
        suno_lyrics_translated = SUNO_LYRICS_TEMPLATE.format(
            structured_lyrics=translated_structured,
        )

    # --- Lyria prompt ---
    lyria_prompt = LYRIA_PROMPT_TEMPLATE.format(
        **common,
        language=lang_name,
        structured_lyrics=structured_lyrics,
    )

    # --- Udio prompt ---
    udio = UDIO_TEMPLATE.format(
        **common,
        language=lang_name,
        structured_lyrics=structured_lyrics,
    )

    # --- Generic (full detail) prompt ---
    generic = GENERIC_TEMPLATE.format(
        **common,
        language=lang_name,
        structured_lyrics=structured_lyrics,
        notes=(
            f"Genre: {genre}. "
            f"Reproduce faithfully: exact BPM ({bpm:.0f}), key ({key}), "
            f"chord progression ({chord_progression or 'auto'}), "
            f"drum pattern ({drum_groove or 'standard'}), "
            f"vocal style ({vocal_tags_str}), dynamics ({dynamics_marking or 'mf'})."
        ),
    )

    # --- Translated full prompt ---
    translated_prompt = ""
    if translated_text and target_lang:
        target_lang_name = LANGUAGE_OPTIONS.get(target_lang, target_lang)
        translated_structured = _build_structured_lyrics(translated_text, sections)
        translated_prompt = GENERIC_TEMPLATE.format(
            **common,
            language=target_lang_name,
            structured_lyrics=translated_structured,
            notes=(
                f"Genre: {genre}. "
                f"This is a {target_lang_name} cover of the original {lang_name} song. "
                f"KEEP EXACTLY THE SAME: BPM ({bpm:.0f}), key ({key}), "
                f"chord progression ({chord_progression or 'auto'}), "
                f"drum pattern ({drum_groove or 'standard'}), "
                f"melody, vocal style ({vocal_tags_str}), dynamics ({dynamics_marking or 'mf'}), "
                f"and emotional arc. ONLY change the lyrics language to {target_lang_name}."
            ),
        )

    return PromptResult(
        suno_style=suno_style,
        suno_lyrics=suno_lyrics,
        suno_lyrics_translated=suno_lyrics_translated,
        lyria_prompt=lyria_prompt,
        udio_prompt=udio,
        generic_prompt=generic,
        translated_prompt=translated_prompt,
    )
