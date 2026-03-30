"""Build natural-language prompts for Lyria music generation.

Lyria works best with flowing descriptive text, not bracketed tags.
This module converts structured music parameters into Lyria-optimized prompts.
"""


def build_lyria_prompt(
    bpm: float = 120,
    key: str = "C major",
    chord_progression: str = "",
    lyrics: str = "",
    instruments: list[str] = None,
    mood: str = "",
    vocal_style_tags: list[str] = None,
    drum_groove: str = "",
    language: str = "English",
    genre: str = "",
) -> str:
    """Build a comprehensive Lyria-optimized prompt from music parameters.

    Returns a natural-language prompt that Lyria can interpret for generation.
    """
    parts = []

    # Genre and basic feel
    if genre:
        parts.append(f"A {genre} song")
    else:
        parts.append("A song")

    parts.append(f"in {key} at {bpm:.0f} BPM.")

    # Mood
    if mood:
        parts.append(f"The mood is {mood}.")

    # Instruments
    if instruments:
        inst_str = ", ".join(instruments)
        parts.append(f"Instruments: {inst_str}.")

    # Chord progression
    if chord_progression:
        parts.append(f"Chord progression: {chord_progression}.")

    # Drum groove
    if drum_groove and drum_groove != "no drums":
        parts.append(f"Drum pattern: {drum_groove}.")
    elif drum_groove == "no drums":
        parts.append("No drums.")

    # Vocal style
    if vocal_style_tags:
        style_str = ", ".join(vocal_style_tags)
        parts.append(f"Vocal style: {style_str}.")

    # Language
    if language and language != "English":
        parts.append(f"Sung in {language}.")

    # Lyrics
    if lyrics and lyrics.strip():
        parts.append(f"\nLyrics:\n{lyrics.strip()}")

    return " ".join(parts)


def build_suno_style_from_fields(
    bpm: float = 120,
    key: str = "C major",
    chord_progression: str = "",
    instruments: list[str] = None,
    mood: str = "",
    vocal_style_tags: list[str] = None,
    drum_groove: str = "",
    language: str = "English",
    genre: str = "",
) -> str:
    """Build a Suno Style string from individual fields (for Copy for Suno)."""
    parts = []
    if genre:
        parts.append(genre)
    parts.append(key)
    parts.append(f"{bpm:.0f} BPM")
    if mood:
        parts.append(mood)
    if instruments:
        parts.append(", ".join(instruments))
    if vocal_style_tags:
        parts.append(", ".join(vocal_style_tags))
    if chord_progression:
        parts.append(f"chords: {chord_progression}")
    if drum_groove:
        parts.append(drum_groove)
    if language:
        parts.append(language)
    return ", ".join(parts)


def build_udio_prompt_from_fields(
    bpm: float = 120,
    key: str = "C major",
    chord_progression: str = "",
    lyrics: str = "",
    instruments: list[str] = None,
    mood: str = "",
    vocal_style_tags: list[str] = None,
    drum_groove: str = "",
    language: str = "English",
    genre: str = "",
) -> str:
    """Build a Udio-format prompt from individual fields."""
    parts = []
    genre_str = genre or "Pop"
    inst_str = ", ".join(instruments) if instruments else "mixed instruments"
    vocal_str = ", ".join(vocal_style_tags) if vocal_style_tags else "natural"

    parts.append(f"{genre_str} song in {key}, {bpm:.0f} BPM.")
    if mood:
        parts.append(f"Mood: {mood}.")
    parts.append(f"Instruments: {inst_str}.")
    if chord_progression:
        parts.append(f"Chords: {chord_progression}.")
    if drum_groove:
        parts.append(f"Drums: {drum_groove}.")
    parts.append(f"Vocal: {vocal_str}.")
    if language and language != "English":
        parts.append(f"Sung in {language}.")

    prompt = " ".join(parts)
    if lyrics and lyrics.strip():
        prompt += f"\n\nLyrics:\n{lyrics.strip()}"

    return prompt
