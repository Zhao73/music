"""Build rich, strategic prompts for AI music generation tools.

Lyria: flowing descriptive text, ~500 word max, narrative style.
Suno v5.5: Style field (~200 chars) + Lyrics field with [Section] metatags + energy/vocal cues.
Udio: structured blocks, concise but detailed.

Uses hit_formulas knowledge base for enhanced quality when available.

Suno v5.5 key features:
- Negative prompting: "no autotune, no heavy reverb" at END of style
- Energy tags: [Energy: High], [Energy: Low] before sections
- Vocal Style tags: [Vocal Style: Whisper], [Vocal Style: Raspy] etc.
- Structure tags: [Verse], [Chorus], [Pre-Chorus], [Bridge], [Intro], [Outro], [Instrumental], [Break]
- Voices: clone your own voice (Pro/Premier only)
- Custom Models: train on your music catalog
- My Taste: auto-learns your preferences
"""

from music_knowledge.hit_formulas import (
    get_genre_profile,
    expand_vocal_tags,
    SECTION_DYNAMICS,
    VOCAL_ENGINEERING,
)


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
    hit_optimize: bool = False,
) -> str:
    """Build a rich, narrative Lyria-optimized prompt.

    When hit_optimize=True, uses proven hit-song formulas to enhance the prompt.
    Caps output at ~500 words for Lyria's practical limit.
    """
    profile = get_genre_profile(genre) if genre else get_genre_profile("pop")
    parts = []

    # --- Opening: genre + mood + atmosphere (not just "A song") ---
    mood_adj = _mood_to_adjective(mood)
    if genre and mood_adj:
        parts.append(f"An {mood_adj} {genre} track")
    elif genre:
        parts.append(f"A compelling {genre} track")
    elif mood_adj:
        parts.append(f"An {mood_adj} song")
    else:
        parts.append("A captivating song")

    parts.append(f"in {key} at {bpm:.0f} BPM.")

    # --- Mood & emotional landscape ---
    if mood:
        parts.append(f"The overall mood is {mood}, setting an immersive emotional tone throughout.")

    # --- Instruments with texture description ---
    if instruments:
        if len(instruments) <= 3:
            inst_str = " and ".join(instruments)
            parts.append(f"Featured instruments: {inst_str}.")
        else:
            primary = ", ".join(instruments[:3])
            supporting = ", ".join(instruments[3:])
            parts.append(f"Led by {primary}, supported by {supporting}.")

    # --- Chord progression with musical context ---
    if chord_progression:
        parts.append(f"The harmony follows a {chord_progression} chord progression, "
                      "providing a strong harmonic foundation.")

    # --- Section-by-section texture and dynamics ---
    section_desc = _build_section_narrative(genre, instruments, mood, drum_groove)
    if section_desc:
        parts.append(section_desc)

    # --- Drum groove with feel ---
    if drum_groove and drum_groove != "no drums":
        parts.append(f"The rhythm features a {drum_groove} pattern driving the momentum.")
    elif drum_groove == "no drums":
        parts.append("The arrangement is drumless, relying on melodic rhythm and space.")

    # --- Vocal style with engineering depth ---
    if vocal_style_tags:
        vocal_desc = expand_vocal_tags(vocal_style_tags)
        if vocal_desc:
            parts.append(f"Vocal delivery: {vocal_desc}.")
        else:
            parts.append(f"Vocal style: {', '.join(vocal_style_tags)}.")

    # --- Hit optimization hints ---
    if hit_optimize and profile:
        parts.append(_hit_optimize_text(profile, bpm, key, genre))

    # --- Language ---
    if language and language.lower() not in ("english", ""):
        parts.append(f"Sung in {language}.")

    # --- Lyrics ---
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
    negative_tags: list[str] = None,
) -> str:
    """Build an optimized Suno v5.5 Style string.

    v5.5 Best practices:
    - Genre + mood FIRST (highest impact, Suno weights early tokens more)
    - 1-2 genre tags, 2-3 instrument tags, 1-2 mood/energy tags
    - Vocal engineering terms Suno responds to
    - Negative prompts at END: "no autotune, no heavy reverb"
    - Comma-separated format (Suno parses better than paragraphs)
    """
    parts = []

    # Genre + mood first (most impactful for Suno)
    if genre:
        parts.append(genre)
    if mood:
        parts.append(mood)

    # Vocal engineering — Suno v5.5 responds well to specific vocal descriptors
    if vocal_style_tags:
        vocal_compact = _compact_vocal_for_suno(vocal_style_tags)
        if vocal_compact:
            parts.append(vocal_compact)

    # Key + BPM
    parts.append(f"{key}, {bpm:.0f} BPM")

    # Instruments (limit to 3-4 — Suno struggles with more)
    if instruments:
        parts.append(", ".join(instruments[:4]))

    # Chord progression
    if chord_progression:
        parts.append(f"chords: {chord_progression}")

    # Drum groove
    if drum_groove and drum_groove != "no drums":
        parts.append(drum_groove)
    elif drum_groove == "no drums":
        parts.append("no drums")

    # Language
    if language and language.lower() != "english":
        parts.append(language)

    # v5.5: Negative prompts at the END (Suno processes positives first)
    if negative_tags:
        neg_str = ", ".join(f"no {t}" for t in negative_tags)
        parts.append(neg_str)

    result = ", ".join(parts)
    return result


def build_suno_lyrics_from_fields(
    lyrics: str = "",
    sections: list = None,
    mood: str = "",
    vocal_style_tags: list[str] = None,
    energy_level: str = "",
) -> str:
    """Build Suno v5.5 Lyrics field with metatags.

    v5.5 supports:
    - Structure tags: [Verse], [Chorus], [Pre-Chorus], [Bridge], [Intro], [Outro]
    - Energy tags: [Energy: High], [Energy: Low]
    - Vocal delivery: [Vocal Style: Whisper], [Vocal Style: Raspy], etc.
    - Instrument cues: [Instrumental], [Guitar Solo], [Piano]
    - Tags must be on their own line, ABOVE the lyrics for that section
    """
    if not lyrics or not lyrics.strip():
        return ""

    # If lyrics already have [Section] tags, return as-is
    if "[" in lyrics and "]" in lyrics:
        return lyrics.strip()

    # Auto-structure: wrap plain lyrics with basic tags
    lines = [l.strip() for l in lyrics.strip().split("\n") if l.strip()]
    if not lines:
        return ""

    # Simple auto-structuring: split into verse/chorus chunks
    result = []
    chunk_size = 4
    section_cycle = ["Verse", "Chorus", "Verse", "Chorus", "Bridge", "Chorus"]
    section_idx = 0

    # Add energy cue for first section based on mood
    energy_map = {
        "happy / energetic": "High",
        "excited / uplifting": "High",
        "powerful / dramatic": "High",
        "angry / intense": "High",
        "calm / ambient": "Low",
        "peaceful / content": "Low",
        "sad / melancholic": "Low",
        "somber / reflective": "Low",
    }

    for i in range(0, len(lines), chunk_size):
        chunk = lines[i:i + chunk_size]
        if not chunk:
            break

        section_name = section_cycle[section_idx % len(section_cycle)]
        result.append(f"[{section_name}]")

        # v5.5: Add energy cue for chorus sections
        if section_name == "Chorus":
            result.append("[Energy: High]")
        elif section_name == "Bridge":
            result.append("[Energy: Low]")

        for line in chunk:
            result.append(line)
        result.append("")
        section_idx += 1

    return "\n".join(result)


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
    """Build a rich Udio-format prompt with structured detail."""
    genre_str = genre or "Pop"
    inst_str = ", ".join(instruments) if instruments else "mixed instruments"

    parts = []

    # Opening with atmosphere
    mood_adj = _mood_to_adjective(mood)
    if mood_adj:
        parts.append(f"{mood_adj.capitalize()} {genre_str} song in {key}, {bpm:.0f} BPM.")
    else:
        parts.append(f"{genre_str} song in {key}, {bpm:.0f} BPM.")

    if mood:
        parts.append(f"Mood: {mood}.")

    parts.append(f"Instruments: {inst_str}.")

    if chord_progression:
        parts.append(f"Chords: {chord_progression}.")

    if drum_groove and drum_groove != "no drums":
        parts.append(f"Drums: {drum_groove}.")
    elif drum_groove == "no drums":
        parts.append("No drums, melodic rhythm only.")

    # Rich vocal description
    if vocal_style_tags:
        vocal_desc = expand_vocal_tags(vocal_style_tags)
        parts.append(f"Vocals: {vocal_desc}.")
    else:
        parts.append("Vocals: natural, expressive delivery.")

    # Dynamics arc
    parts.append("Dynamics: building from intimate verse to powerful chorus.")

    if language and language.lower() != "english":
        parts.append(f"Sung in {language}.")

    prompt = " ".join(parts)
    if lyrics and lyrics.strip():
        prompt += f"\n\nLyrics:\n{lyrics.strip()}"

    return prompt


# =============================================================
# Internal helpers
# =============================================================

def _mood_to_adjective(mood: str) -> str:
    """Convert mood tag to a natural-sounding adjective."""
    if not mood:
        return ""
    mood_map = {
        "happy / energetic": "upbeat and energetic",
        "peaceful / content": "serene and peaceful",
        "excited / uplifting": "exhilarating and uplifting",
        "powerful / dramatic": "powerful and dramatic",
        "calm / ambient": "calm and atmospheric",
        "sad / melancholic": "melancholic and emotional",
        "angry / intense": "intense and fierce",
        "tense / anxious": "tense and suspenseful",
        "somber / reflective": "contemplative and somber",
        "romantic / emotional": "romantic and deeply emotional",
        "mysterious / dark": "dark and mysterious",
        "playful / fun": "playful and lighthearted",
        "epic / cinematic": "epic and cinematic",
        "neutral / moderate": "balanced and moderate",
    }
    return mood_map.get(mood, mood.split("/")[0].strip())


def _build_section_narrative(genre: str, instruments: list, mood: str, drum_groove: str) -> str:
    """Build a narrative describing how the song evolves section by section."""
    profile = get_genre_profile(genre) if genre else None
    if not profile:
        return ""

    # Pick representative instruments for the narrative
    lead = instruments[0] if instruments else "the lead instrument"
    accomp = instruments[1] if instruments and len(instruments) > 1 else "subtle accompaniment"

    structure = profile.get("structure", [])
    has_verse = any("Verse" in s for s in structure)
    has_chorus = any("Chorus" in s for s in structure)

    if not has_verse or not has_chorus:
        return ""

    verse_dyn = SECTION_DYNAMICS.get("Verse", {})
    chorus_dyn = SECTION_DYNAMICS.get("Chorus", {})

    narrative = (
        f"The song opens with {verse_dyn.get('description', 'an intimate verse')}, "
        f"featuring {lead} with {accomp}. "
        f"It builds into the chorus with {chorus_dyn.get('description', 'full power and energy')}, "
        f"creating a dynamic contrast that drives the emotional arc."
    )
    return narrative


def _hit_optimize_text(profile: dict, bpm: float, key: str, genre: str) -> str:
    """Generate hit-optimization hints for the prompt."""
    hints = []
    sweet_bpm = profile.get("bpm_sweet", 120)
    if abs(bpm - sweet_bpm) <= 10:
        hints.append("tempo in the commercial sweet spot")
    top_prog = profile["common_progressions"][0][0] if profile.get("common_progressions") else ""
    if top_prog:
        hints.append(f"classic {top_prog} harmonic movement")
    if key in profile.get("common_keys", []):
        hints.append("popular key for this genre")

    if hints:
        return f"Production notes: {', '.join(hints)}."
    return ""


def _compact_vocal_for_suno(tags: list[str]) -> str:
    """Convert vocal tags to compact Suno-friendly terms."""
    suno_map = {
        "vibrato-rich": "expressive vibrato",
        "straight-tone": "clean vocals",
        "breathy": "breathy intimate vocals",
        "bright": "bright clear vocals",
        "warm": "warm rich vocals",
        "dynamic": "dynamic vocals",
        "falsetto/head-voice": "soaring falsetto",
        "chest-voice-dominant": "powerful chest voice",
        "legato": "smooth legato vocals",
        "rhythmic-articulation": "rhythmic vocal delivery",
        "raspy/gritty": "raspy vocals",
        "smooth": "silky smooth vocals",
        "powerful belting": "powerful belting vocals",
        "whisper/soft": "whispered intimate vocals",
    }
    compact = []
    for tag in tags[:2]:  # Limit to 2 for Suno's character limit
        for key, val in suno_map.items():
            if key.lower() in tag.lower() or tag.lower() in key.lower():
                compact.append(val)
                break
        else:
            compact.append(tag)
    return ", ".join(compact)
