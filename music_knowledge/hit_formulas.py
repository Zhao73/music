"""Hit song knowledge base — proven formulas for chart-worthy music.

Data sourced from published music industry research, Billboard/Spotify analysis,
and music theory best practices. No API calls required.
"""

# =============================================================
# Per-genre profiles with BPM ranges, keys, chords, instruments
# =============================================================

HIT_SONG_PROFILES = {
    "pop": {
        "bpm_range": (100, 130),
        "bpm_sweet": 120,
        "common_keys": ["C major", "G major", "D major", "A major", "F major"],
        "common_progressions": [
            ("I-V-vi-IV", 0.30),   # (progression, popularity weight)
            ("vi-IV-I-V", 0.20),
            ("I-IV-vi-V", 0.15),
            ("I-vi-IV-V", 0.12),
            ("I-IV-V-I", 0.08),
        ],
        "instruments": ["Vocals", "Piano / Keys", "Synthesizer / Electronic", "Bass", "Drums / Percussion", "Acoustic Guitar"],
        "moods": ["happy / energetic", "excited / uplifting", "romantic / emotional", "playful / fun"],
        "drum_grooves": ["straight 4/4 rock", "straight 8th notes", "funk groove"],
        "vocal_styles": ["dynamic", "bright", "powerful belting", "breathy"],
        "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Pre-Chorus", "Chorus", "Bridge", "Chorus", "Outro"],
    },
    "rock": {
        "bpm_range": (110, 145),
        "bpm_sweet": 130,
        "common_keys": ["E major", "A major", "G major", "D major", "E minor"],
        "common_progressions": [
            ("I-IV-V-I", 0.25),
            ("I-V-vi-IV", 0.20),
            ("I-bVII-IV-I", 0.15),
            ("i-bVII-bVI-V", 0.12),
            ("I-IV-I-V", 0.10),
        ],
        "instruments": ["Electric Guitar", "Bass", "Drums / Percussion", "Vocals", "Piano / Keys"],
        "moods": ["powerful / dramatic", "angry / intense", "excited / uplifting", "happy / energetic"],
        "drum_grooves": ["straight 4/4 rock", "double-time", "half-time"],
        "vocal_styles": ["raspy/gritty", "powerful belting", "dynamic", "chest-voice-dominant"],
        "structure": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Solo", "Chorus", "Outro"],
    },
    "edm": {
        "bpm_range": (125, 135),
        "bpm_sweet": 128,
        "common_keys": ["A minor", "C minor", "D minor", "F minor", "G minor"],
        "common_progressions": [
            ("vi-IV-I-V", 0.25),
            ("i-bVI-bVII-i", 0.20),
            ("i-bIII-bVII-IV", 0.15),
            ("i-iv-bVI-V", 0.12),
        ],
        "instruments": ["Synthesizer / Electronic", "Drums / Percussion", "Bass", "Vocals"],
        "moods": ["excited / uplifting", "happy / energetic", "powerful / dramatic", "epic / cinematic"],
        "drum_grooves": ["straight 4/4 rock", "straight 16th notes", "trap hi-hat"],
        "vocal_styles": ["breathy", "bright", "powerful belting", "falsetto/head-voice"],
        "structure": ["Intro", "Build", "Drop", "Break", "Build", "Drop", "Break", "Drop", "Outro"],
    },
    "hip-hop": {
        "bpm_range": (80, 100),
        "bpm_sweet": 90,
        "common_keys": ["C minor", "G minor", "D minor", "A minor", "F minor"],
        "common_progressions": [
            ("i-bVII-bVI-V", 0.25),
            ("i-iv-bVI-V", 0.20),
            ("i-bVI-bIII-bVII", 0.15),
            ("i-bVII-iv-i", 0.12),
        ],
        "instruments": ["Bass", "Drums / Percussion", "Synthesizer / Electronic", "Piano / Keys", "Vocals"],
        "moods": ["powerful / dramatic", "mysterious / dark", "angry / intense", "calm / ambient"],
        "drum_grooves": ["trap hi-hat", "straight 8th notes", "funk groove"],
        "vocal_styles": ["rhythmic-articulation", "raspy/gritty", "smooth", "dynamic"],
        "structure": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Verse", "Chorus", "Outro"],
    },
    "r&b": {
        "bpm_range": (65, 100),
        "bpm_sweet": 85,
        "common_keys": ["G major", "C major", "D major", "A minor", "E minor"],
        "common_progressions": [
            ("I-V-vi-IV", 0.20),
            ("ii-V-I-vi", 0.20),
            ("I-vi-ii-V", 0.18),
            ("vi-IV-I-V", 0.15),
        ],
        "instruments": ["Vocals", "Piano / Keys", "Bass", "Drums / Percussion", "Synthesizer / Electronic", "Electric Guitar"],
        "moods": ["romantic / emotional", "calm / ambient", "peaceful / content", "sad / melancholic"],
        "drum_grooves": ["shuffle / swing", "straight 8th notes", "funk groove"],
        "vocal_styles": ["smooth", "vibrato-rich", "falsetto/head-voice", "breathy", "dynamic"],
        "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Pre-Chorus", "Chorus", "Bridge", "Chorus", "Outro"],
    },
    "ballad": {
        "bpm_range": (60, 85),
        "bpm_sweet": 72,
        "common_keys": ["C major", "G major", "F major", "A minor", "D major"],
        "common_progressions": [
            ("I-V-vi-IV", 0.30),
            ("I-vi-IV-V", 0.20),
            ("vi-IV-I-V", 0.18),
            ("I-IV-vi-V", 0.12),
        ],
        "instruments": ["Vocals", "Piano / Keys", "Acoustic Guitar", "Strings", "Bass"],
        "moods": ["romantic / emotional", "sad / melancholic", "peaceful / content", "somber / reflective"],
        "drum_grooves": ["6/8 ballad", "sparse percussion", "straight 8th notes"],
        "vocal_styles": ["vibrato-rich", "warm", "breathy", "legato", "dynamic"],
        "structure": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Chorus", "Outro"],
    },
    "latin": {
        "bpm_range": (90, 130),
        "bpm_sweet": 100,
        "common_keys": ["A minor", "D minor", "G major", "C major", "E minor"],
        "common_progressions": [
            ("i-iv-V-i", 0.25),
            ("I-IV-V-I", 0.20),
            ("i-bVII-bVI-V", 0.18),
            ("I-V-vi-IV", 0.15),
        ],
        "instruments": ["Vocals", "Acoustic Guitar", "Bass", "Drums / Percussion", "Piano / Keys", "Brass (Trumpet, Sax)"],
        "moods": ["happy / energetic", "romantic / emotional", "playful / fun", "excited / uplifting"],
        "drum_grooves": ["Latin / bossa nova", "funk groove", "straight 8th notes"],
        "vocal_styles": ["vibrato-rich", "dynamic", "warm", "rhythmic-articulation"],
        "structure": ["Intro", "Verse", "Pre-Chorus", "Chorus", "Verse", "Chorus", "Bridge", "Chorus", "Outro"],
    },
    "country": {
        "bpm_range": (90, 140),
        "bpm_sweet": 115,
        "common_keys": ["G major", "C major", "D major", "A major", "E major"],
        "common_progressions": [
            ("I-IV-V-I", 0.30),
            ("I-V-vi-IV", 0.25),
            ("I-IV-I-V", 0.15),
            ("vi-IV-I-V", 0.10),
        ],
        "instruments": ["Vocals", "Acoustic Guitar", "Electric Guitar", "Bass", "Drums / Percussion", "Violin / Cello", "Mandolin"],
        "moods": ["happy / energetic", "romantic / emotional", "peaceful / content", "somber / reflective"],
        "drum_grooves": ["straight 4/4 rock", "shuffle / swing", "straight 8th notes"],
        "vocal_styles": ["warm", "vibrato-rich", "chest-voice-dominant", "legato"],
        "structure": ["Intro", "Verse", "Chorus", "Verse", "Chorus", "Bridge", "Chorus", "Outro"],
    },
}


# =============================================================
# Vocal engineering — expand simple tags into rich descriptions
# =============================================================

VOCAL_ENGINEERING = {
    "vibrato-rich": "expressive vibrato with warm oscillation, adding emotional depth to sustained notes",
    "straight-tone": "clean straight-tone delivery with precise pitch control, modern and polished",
    "breathy": "intimate breathy delivery with airy texture, creating closeness and vulnerability",
    "bright": "bright forward-placed vocals with crisp clarity cutting through the mix",
    "warm": "warm rounded vocal tone with rich lower harmonics and gentle presence",
    "dynamic": "dynamic vocal range shifting from soft intimate whispers to powerful soaring passages",
    "falsetto/head-voice": "ethereal falsetto passages floating above the instrumental, light and airy",
    "chest-voice-dominant": "powerful chest-voice delivery with full-bodied resonance and commanding presence",
    "legato": "smooth legato phrasing with seamless note connections and flowing melodic lines",
    "rhythmic-articulation": "precise rhythmic articulation with sharp consonants and punchy delivery",
    "raspy/gritty": "raw raspy vocal texture with gritty character and emotional edge",
    "smooth": "silky smooth vocal delivery with effortless transitions and buttery tone",
    "powerful belting": "soaring belt vocals with full power and stadium-filling projection",
    "whisper/soft": "delicate whispered vocals creating intimate atmosphere and hushed intensity",
}


# =============================================================
# Section dynamics — how each section should feel
# =============================================================

SECTION_DYNAMICS = {
    "Intro": {"dynamic": "p-mp", "texture": "sparse, building anticipation", "description": "gentle opening, setting the mood"},
    "Verse": {"dynamic": "mp", "texture": "intimate, stripped back", "description": "conversational delivery, lighter instrumentation"},
    "Pre-Chorus": {"dynamic": "mp→f", "texture": "building layers, rising tension", "description": "energy escalating, new elements entering"},
    "Chorus": {"dynamic": "f", "texture": "full band, maximum energy", "description": "powerful and wide, all instruments engaged"},
    "Bridge": {"dynamic": "mp-mf", "texture": "contrasting, different feel", "description": "shift in perspective, new harmonic territory"},
    "Solo": {"dynamic": "mf-f", "texture": "spotlight on lead instrument", "description": "virtuosic passage, emotional peak"},
    "Drop": {"dynamic": "ff", "texture": "maximum impact, bass-heavy", "description": "explosive energy release, full spectrum"},
    "Build": {"dynamic": "p→ff", "texture": "layering from minimal to maximal", "description": "tension building toward the drop"},
    "Break": {"dynamic": "p", "texture": "stripped down, breathing room", "description": "calm before the next storm"},
    "Outro": {"dynamic": "mf→p", "texture": "gradually fading", "description": "gentle wind-down, resolving tension"},
}

# Genre → mood compatibility map (for validation)
MOOD_GENRE_COMPAT = {
    "happy / energetic": ["pop", "edm", "latin", "country", "rock"],
    "peaceful / content": ["ballad", "r&b", "country", "pop"],
    "excited / uplifting": ["pop", "edm", "rock", "latin"],
    "powerful / dramatic": ["rock", "edm", "hip-hop", "pop"],
    "calm / ambient": ["ballad", "r&b", "hip-hop"],
    "sad / melancholic": ["ballad", "r&b", "pop", "country"],
    "angry / intense": ["rock", "hip-hop", "edm"],
    "tense / anxious": ["rock", "hip-hop", "edm"],
    "somber / reflective": ["ballad", "r&b", "country"],
    "romantic / emotional": ["ballad", "r&b", "pop", "latin", "country"],
    "mysterious / dark": ["hip-hop", "edm", "rock"],
    "playful / fun": ["pop", "latin", "country", "edm"],
    "epic / cinematic": ["edm", "rock", "pop"],
    "neutral / moderate": ["pop", "rock", "country", "r&b"],
}


def get_genre_profile(genre: str) -> dict:
    """Get the full hit-song profile for a genre."""
    genre_lower = genre.lower().strip()
    for key in HIT_SONG_PROFILES:
        if key in genre_lower or genre_lower in key:
            return HIT_SONG_PROFILES[key]
    return HIT_SONG_PROFILES.get("pop", {})


def get_section_dynamics(sections: list, genre: str = "pop") -> dict:
    """Return per-section dynamics/texture recommendations.

    Args:
        sections: list of section dicts with 'label' keys, or list of label strings
        genre: genre name for context

    Returns:
        dict mapping section label → dynamics info
    """
    result = {}
    for sec in sections:
        label = sec.get("label", sec) if isinstance(sec, dict) else str(sec)
        # Match against known section types
        for known_label, dynamics in SECTION_DYNAMICS.items():
            if known_label.lower() in label.lower():
                result[label] = dynamics
                break
        else:
            # Default for unknown sections
            result[label] = SECTION_DYNAMICS.get("Verse", {})
    return result


def expand_vocal_tags(tags: list[str]) -> str:
    """Expand simple vocal style tags into rich engineering descriptions."""
    if not tags:
        return ""
    descriptions = []
    for tag in tags:
        tag_lower = tag.lower().strip()
        for key, desc in VOCAL_ENGINEERING.items():
            if key.lower() in tag_lower or tag_lower in key.lower():
                descriptions.append(desc)
                break
        else:
            descriptions.append(tag)
    return "; ".join(descriptions)


def suggest_improvements(params: dict) -> list[str]:
    """Suggest hit-song optimizations for given parameters.

    Args:
        params: dict with keys like 'bpm', 'key', 'genre', 'chord_progression', etc.

    Returns:
        List of actionable improvement suggestions.
    """
    suggestions = []
    genre = params.get("genre", "pop").lower()
    profile = get_genre_profile(genre)
    if not profile:
        return suggestions

    bpm = params.get("bpm", 0)
    if bpm:
        lo, hi = profile["bpm_range"]
        if bpm < lo:
            suggestions.append(
                f"BPM {bpm:.0f} is below the typical {genre} range ({lo}-{hi}). "
                f"Consider {profile['bpm_sweet']} BPM for more commercial appeal."
            )
        elif bpm > hi:
            suggestions.append(
                f"BPM {bpm:.0f} is above the typical {genre} range ({lo}-{hi}). "
                f"Consider {profile['bpm_sweet']} BPM for a more natural feel."
            )

    key = params.get("key", "")
    if key and key not in profile["common_keys"]:
        top_keys = ", ".join(profile["common_keys"][:3])
        suggestions.append(
            f"Key '{key}' is uncommon for {genre} hits. "
            f"Most popular keys: {top_keys}."
        )

    chord = params.get("chord_progression", "")
    if chord:
        top_prog = profile["common_progressions"][0][0]
        prog_names = [p[0] for p in profile["common_progressions"]]
        if not any(p.replace(" ", "") in chord.replace(" ", "") for p in prog_names):
            suggestions.append(
                f"Consider the classic {top_prog} progression — "
                f"it's the most proven hit formula for {genre}."
            )

    mood = params.get("mood", "")
    if mood and mood in MOOD_GENRE_COMPAT:
        compatible = MOOD_GENRE_COMPAT[mood]
        if genre not in compatible:
            suggestions.append(
                f"Mood '{mood}' is unusual for {genre}. "
                f"Compatible genres: {', '.join(compatible[:3])}."
            )

    return suggestions


def build_dynamics_arc(sections: list) -> str:
    """Build a human-readable dynamics arc description from section list."""
    if not sections:
        return "gradual build from intimate verse to powerful chorus"

    dynamics_map = get_section_dynamics(sections)
    parts = []
    for label, info in dynamics_map.items():
        parts.append(f"{label}: {info['description']}")

    if not parts:
        return "gradual build from intimate verse to powerful chorus"

    return " → ".join(parts)
