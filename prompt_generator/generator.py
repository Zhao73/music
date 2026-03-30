"""Assembles all analysis results into comprehensive AI music generation prompts."""

from dataclasses import dataclass
from prompt_generator.templates import SUNO_TEMPLATE, GENERIC_TEMPLATE, UDIO_TEMPLATE
from config import LANGUAGE_OPTIONS


@dataclass
class PromptResult:
    suno_prompt: str
    udio_prompt: str
    generic_prompt: str
    translated_prompt: str


def _guess_genre(instruments: list[str], bpm: float, energy: str, feel: str, mood: str = "") -> str:
    """Heuristic genre guess based on analysis results."""
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


def _build_structured_lyrics(lyrics_text: str, sections: list, lyrics_segments: list = None) -> str:
    """Combine lyrics with section labels and timestamps."""
    if not sections or not lyrics_text:
        return lyrics_text or ""

    result = []
    for section in sections:
        result.append(f"[{section.label}] ({section.start_time:.1f}s - {section.end_time:.1f}s)")

        if lyrics_segments:
            # Match lyrics segments to this section by time
            section_lyrics = []
            for seg in lyrics_segments:
                seg_mid = (seg["start"] + seg["end"]) / 2
                if section.start_time <= seg_mid <= section.end_time:
                    section_lyrics.append(seg["text"])
            if section_lyrics:
                for line in section_lyrics:
                    if line.strip():
                        result.append(line.strip())
            else:
                result.append("(instrumental)")
        result.append("")

    # If time-aligned lyrics didn't work well, fall back to even distribution
    text_in_result = [l for l in result if l.strip() and not l.startswith("[") and l != "(instrumental)"]
    if not text_in_result and lyrics_text.strip():
        lines = lyrics_text.strip().split("\n")
        lines = [l.strip() for l in lines if l.strip()]
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
    """Build detailed structure description."""
    if not sections:
        return "Unknown structure"

    from utils.audio_io import format_time
    lines = [" → ".join(s.label for s in sections), ""]
    for s in sections:
        dur = s.end_time - s.start_time
        lines.append(f"  {s.label}: {format_time(s.start_time)} - {format_time(s.end_time)} ({dur:.1f}s)")
    return "\n".join(lines)


def _format_dynamic_events(dynamic_events: list) -> str:
    """Format dynamic events list."""
    if not dynamic_events:
        return "No significant dynamic changes"
    from utils.audio_io import format_time
    parts = []
    for e in dynamic_events[:10]:
        parts.append(f"{format_time(e.start_time)}: {e.type} ({e.from_level} → {e.to_level})")
    return "; ".join(parts)


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
    # New detailed parameters
    mood: str = "",
    mood_tags: list[str] = None,
    emotional_arc: str = "",
    energy_curve: str = "",
    vocal_style_tags: list[str] = None,
    vibrato_desc: str = "",
    register_desc: str = "",
    tone_desc: str = "",
    articulation_desc: str = "",
    dynamics_marking: str = "",
    dynamic_range: str = "",
    volume_map: str = "",
    dynamic_events: list = None,
    rhythm_description: str = "",
    lyrics_segments: list = None,
) -> PromptResult:
    """Generate comprehensive AI music prompts with all analysis details."""
    genre = _guess_genre(instruments, bpm, energy, feel, mood)
    instruments_str = ", ".join(instruments)
    lang_name = LANGUAGE_OPTIONS.get(source_lang, source_lang)
    vocal_tags_str = ", ".join(vocal_style_tags) if vocal_style_tags else "natural"
    mood_tags_str = ", ".join(mood_tags) if mood_tags else mood
    dynamic_events_str = _format_dynamic_events(dynamic_events) if dynamic_events else "gradual natural dynamics"
    structured_lyrics = _build_structured_lyrics(lyrics_text, sections, lyrics_segments)
    structure_detail = _build_structure_detail(sections)

    # --- Suno prompt ---
    suno = SUNO_TEMPLATE.format(
        genre=genre,
        bpm=f"{bpm:.0f}",
        key=key,
        time_signature=time_signature,
        mood=mood,
        feel=feel,
        energy=energy,
        instruments=instruments_str,
        vocal_range=vocal_range,
        language=lang_name,
        vocal_style_tags=vocal_tags_str,
        dynamics_marking=dynamics_marking or "mf",
        structured_lyrics=structured_lyrics,
    )

    # --- Udio prompt ---
    udio = UDIO_TEMPLATE.format(
        genre=genre,
        key=key,
        bpm=f"{bpm:.0f}",
        time_signature=time_signature,
        feel=feel,
        energy=energy,
        mood=mood,
        instruments=instruments_str,
        vocal_range=vocal_range,
        vocal_style_tags=vocal_tags_str,
        vibrato=vibrato_desc or "natural vibrato",
        tone=tone_desc or "balanced tone",
        articulation=articulation_desc or "natural articulation",
        dynamics_marking=dynamics_marking or "mf",
        dynamic_range=dynamic_range or "moderate",
        melody_description=melody_description,
        emotional_arc=emotional_arc,
        language=lang_name,
        structured_lyrics=structured_lyrics,
    )

    # --- Generic (full detail) prompt ---
    generic = GENERIC_TEMPLATE.format(
        bpm=f"{bpm:.0f}",
        key=key,
        time_signature=time_signature,
        genre=genre,
        mood=mood,
        mood_tags=mood_tags_str,
        emotional_arc=emotional_arc or "consistent throughout",
        energy_curve=energy_curve or "steady",
        feel=feel,
        energy=energy,
        rhythm_description=rhythm_description or feel,
        vocal_range=vocal_range,
        melody_description=melody_description,
        melody_contour=melody_contour or "",
        melody_notation=melody_notation or "",
        vocal_style_tags=vocal_tags_str,
        vibrato=vibrato_desc or "natural",
        register=register_desc or "",
        tone=tone_desc or "",
        articulation=articulation_desc or "",
        dynamics_marking=dynamics_marking or "mf",
        dynamic_range=dynamic_range or "moderate",
        volume_map=volume_map or "",
        dynamic_events=dynamic_events_str,
        instruments=instruments_str,
        structure_detail=structure_detail,
        language=lang_name,
        structured_lyrics=structured_lyrics,
        notes=f"Genre: {genre}. Reproduce faithfully with exact BPM, key, structure, and vocal style.",
    )

    # --- Translated version ---
    translated_prompt = ""
    if translated_text and target_lang:
        target_lang_name = LANGUAGE_OPTIONS.get(target_lang, target_lang)
        translated_structured = _build_structured_lyrics(translated_text, sections)
        translated_prompt = GENERIC_TEMPLATE.format(
            bpm=f"{bpm:.0f}",
            key=key,
            time_signature=time_signature,
            genre=genre,
            mood=mood,
            mood_tags=mood_tags_str,
            emotional_arc=emotional_arc or "consistent throughout",
            energy_curve=energy_curve or "steady",
            feel=feel,
            energy=energy,
            rhythm_description=rhythm_description or feel,
            vocal_range=vocal_range,
            melody_description=melody_description,
            melody_contour=melody_contour or "",
            melody_notation=melody_notation or "",
            vocal_style_tags=vocal_tags_str,
            vibrato=vibrato_desc or "natural",
            register=register_desc or "",
            tone=tone_desc or "",
            articulation=articulation_desc or "",
            dynamics_marking=dynamics_marking or "mf",
            dynamic_range=dynamic_range or "moderate",
            volume_map=volume_map or "",
            dynamic_events=dynamic_events_str,
            instruments=instruments_str,
            structure_detail=structure_detail,
            language=target_lang_name,
            structured_lyrics=translated_structured,
            notes=(
                f"Genre: {genre}. "
                f"This is a {target_lang_name} cover of the original {lang_name} song. "
                f"KEEP THE EXACT SAME: melody, BPM ({bpm:.0f}), key ({key}), "
                f"vocal style ({vocal_tags_str}), dynamics ({dynamics_marking}), "
                f"and emotional arc. Only the lyrics language changes."
            ),
        )

    return PromptResult(
        suno_prompt=suno,
        udio_prompt=udio,
        generic_prompt=generic,
        translated_prompt=translated_prompt,
    )
