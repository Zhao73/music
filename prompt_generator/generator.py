"""Assembles analysis results into AI music generation prompts."""

from dataclasses import dataclass
from prompt_generator.templates import SUNO_TEMPLATE, GENERIC_TEMPLATE, UDIO_TEMPLATE

from config import LANGUAGE_OPTIONS


@dataclass
class PromptResult:
    suno_prompt: str
    udio_prompt: str
    generic_prompt: str
    translated_prompt: str  # Generic prompt with translated lyrics


def _guess_genre(instruments: list[str], bpm: float, energy: str, feel: str) -> str:
    """Heuristic genre guess based on analysis results."""
    inst_lower = " ".join(instruments).lower()

    if "electronic" in inst_lower or "synthesizer" in inst_lower:
        if bpm > 120:
            return "Electronic / EDM"
        return "Electronic / Synth Pop"
    if "guitar (electric)" in inst_lower and "drums" in inst_lower:
        if "high" in energy:
            return "Rock"
        return "Pop Rock"
    if "acoustic guitar" in inst_lower:
        return "Folk / Acoustic"
    if "piano" in inst_lower or "keys" in inst_lower:
        if "slow" in feel:
            return "Ballad"
        return "Pop"
    if "strings" in inst_lower:
        return "Orchestral / Cinematic"

    if bpm > 130:
        return "Dance Pop"
    if bpm < 80:
        return "Ballad"
    return "Pop"


def _build_structured_lyrics(lyrics_text: str, sections: list) -> str:
    """Combine lyrics with section labels."""
    if not sections:
        return lyrics_text

    lines = lyrics_text.strip().split("\n") if lyrics_text else []
    if not lines:
        return lyrics_text

    result_parts = []
    for section in sections:
        result_parts.append(f"\n[{section.label}]")
        # Find lyrics that fall within this section's time range
        # Since we may not have perfect alignment, just distribute lyrics
        result_parts.append("")  # placeholder for lyrics under section

    # Simple approach: just add section markers to the lyrics
    # This is approximate since we don't have per-word timestamps
    if lines:
        n_sections = len(sections)
        lines_per_section = max(1, len(lines) // n_sections)

        result = []
        for i, section in enumerate(sections):
            result.append(f"[{section.label}]")
            start_idx = i * lines_per_section
            end_idx = start_idx + lines_per_section if i < n_sections - 1 else len(lines)
            for line in lines[start_idx:end_idx]:
                if line.strip():
                    result.append(line.strip())
            result.append("")

        return "\n".join(result)

    return lyrics_text


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
    sections: list,
    source_lang: str,
    target_lang: str = None,
) -> PromptResult:
    """Generate AI music generation prompts from analysis results."""
    genre = _guess_genre(instruments, bpm, energy, feel)
    instruments_str = ", ".join(instruments)
    lang_name = LANGUAGE_OPTIONS.get(source_lang, source_lang)
    structured_lyrics = _build_structured_lyrics(lyrics_text, sections)
    structure_summary = " → ".join(s.label for s in sections) if sections else "Unknown"

    # Suno prompt
    suno = SUNO_TEMPLATE.format(
        genre=genre,
        bpm=f"{bpm:.0f}",
        key=key,
        time_signature=time_signature,
        feel=feel,
        energy=energy,
        instruments=instruments_str,
        vocal_range=vocal_range,
        language=lang_name,
        structured_lyrics=structured_lyrics,
    )

    # Udio prompt
    udio = UDIO_TEMPLATE.format(
        genre=genre,
        key=key,
        bpm=f"{bpm:.0f}",
        feel=feel,
        energy=energy,
        instruments=instruments_str,
        vocal_range=vocal_range,
        melody_description=melody_description,
        language=lang_name,
        structured_lyrics=structured_lyrics,
    )

    # Generic prompt
    generic = GENERIC_TEMPLATE.format(
        bpm=f"{bpm:.0f}",
        key=key,
        time_signature=time_signature,
        feel=feel,
        energy=energy,
        instruments=instruments_str,
        vocal_range=vocal_range,
        melody_description=melody_description,
        structure_summary=structure_summary,
        language=lang_name,
        structured_lyrics=structured_lyrics,
        notes=f"Genre suggestion: {genre}",
    )

    # Translated version
    translated_prompt = ""
    if translated_text and target_lang:
        target_lang_name = LANGUAGE_OPTIONS.get(target_lang, target_lang)
        translated_structured = _build_structured_lyrics(translated_text, sections)
        translated_prompt = GENERIC_TEMPLATE.format(
            bpm=f"{bpm:.0f}",
            key=key,
            time_signature=time_signature,
            feel=feel,
            energy=energy,
            instruments=instruments_str,
            vocal_range=vocal_range,
            melody_description=melody_description,
            structure_summary=structure_summary,
            language=target_lang_name,
            structured_lyrics=translated_structured,
            notes=f"Genre suggestion: {genre}. "
            f"This is a {target_lang_name} version of the original {lang_name} song. "
            f"Keep the same melody, rhythm, and emotion.",
        )

    return PromptResult(
        suno_prompt=suno,
        udio_prompt=udio,
        generic_prompt=generic,
        translated_prompt=translated_prompt,
    )
