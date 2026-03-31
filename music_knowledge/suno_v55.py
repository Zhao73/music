"""Suno v5.5 metatags reference — complete tag library for optimal prompting.

Based on community-verified tags from OpenMusicPrompt, HookGenius, and JackRighteous
guides, updated for Suno v5/v5.5 (March 2026).

Key v5.5 principles:
- Tags go in Lyrics field ONLY, each on its own line
- Style field: comma-separated descriptors, genre+mood first
- Negative prompting: "no X" at END of style field
- Max 3-4 instrument tags (more confuses the AI)
- Energy cues below section tags: [Energy: High]
"""

# =============================================================
# Structure Tags — define song sections
# =============================================================

STRUCTURE_TAGS = [
    "[Intro]",
    "[Verse]",
    "[Verse 1]",
    "[Verse 2]",
    "[Pre-Chorus]",
    "[Chorus]",
    "[Post-Chorus]",
    "[Bridge]",
    "[Outro]",
    "[Instrumental]",
    "[Interlude]",
    "[Break]",
    "[Solo]",
    "[Guitar Solo]",
    "[Piano Solo]",
    "[Drop]",
    "[Build]",
    "[Hook]",
    "[Refrain]",
    "[Coda]",
    "[End]",
]

# =============================================================
# Vocal Delivery Tags — control singing style per section
# =============================================================

VOCAL_TAGS = [
    "[Vocal Style: Whisper]",
    "[Vocal Style: Shouting]",
    "[Vocal Style: Melismatic]",     # R&B runs
    "[Vocal Style: Monotone]",       # Experimental rap
    "[Vocal Style: Raspy]",          # Blues/rock grit
    "[Vocal Style: Falsetto]",
    "[Vocal Style: Belt]",
    "[Vocal Style: Spoken Word]",
    "[Vocal Style: Rap]",
    "[Vocal Style: Scream]",
    "[Whispered]",
    "[Spoken]",
    "[Rap]",
    "[Singing]",
    "[Humming]",
    "[Chanting]",
    "[Harmony: High]",
    "[Harmony: Low]",
    "[Vocal Ad-libs]",
    "[Choir: Gospel]",
    "[Choir]",
    "[Voice: Auto-tune]",
    "[Duet]",
    "[Call and Response]",
    "[A Cappella]",
]

# =============================================================
# Energy & Mood Tags — control dynamics per section
# =============================================================

ENERGY_TAGS = [
    "[Energy: High]",
    "[Energy: Medium]",
    "[Energy: Low]",
    "[Energy: Building]",
    "[Energy: Fading]",
    "[Euphoric]",
    "[High Energy]",
    "[Low Energy]",
    "[Mood: Uplifting]",
    "[Mood: Dark]",
    "[Mood: Melancholic]",
    "[Mood: Aggressive]",
    "[Mood: Dreamy]",
    "[Mood: Triumphant]",
    "[Intense]",
    "[Gentle]",
    "[Explosive]",
    "[Calm]",
]

# =============================================================
# Instrument Tags — highlight specific sounds
# =============================================================

INSTRUMENT_TAGS = [
    "[Piano]",
    "[Acoustic Guitar]",
    "[Electric Guitar]",
    "[Distorted Guitar]",
    "[Bass]",
    "[808s]",
    "[Drums]",
    "[Strings]",
    "[Synth]",
    "[Orchestra]",
    "[Brass]",
    "[Saxophone]",
    "[Trumpet]",
    "[Violin]",
    "[Flute]",
    "[Harp]",
    "[Organ]",
    "[Beat Drop]",
]

# =============================================================
# Production Tags — sonic characteristics
# =============================================================

PRODUCTION_TAGS = [
    "[Lo-fi]",
    "[Hi-fi]",
    "[Reverb Heavy]",
    "[Dry Mix]",
    "[Stereo Wide]",
    "[Mono]",
    "[Distorted]",
    "[Clean]",
    "[Compressed]",
    "[Vinyl Crackle]",
    "[Tape Saturation]",
]

# =============================================================
# Style field descriptors — for the Style input box
# =============================================================

# Genre descriptors (use 1-2 max)
GENRE_DESCRIPTORS = [
    "Pop", "Rock", "Hip-Hop", "R&B", "Soul", "EDM", "Electronic",
    "Country", "Folk", "Jazz", "Blues", "Classical", "Metal",
    "Punk", "Reggae", "Latin", "K-Pop", "J-Pop", "Afrobeats",
    "Drill", "Trap", "Lo-fi", "Ambient", "Indie", "Alternative",
    "Gospel", "Funk", "Disco", "Synthwave", "Grunge", "Emo",
    "Ska", "Bluegrass", "Bossa Nova", "Flamenco", "Celtic",
]

# Mood descriptors (use 1-2 max)
MOOD_DESCRIPTORS = [
    "uplifting", "melancholic", "aggressive", "dreamy", "euphoric",
    "dark", "bright", "nostalgic", "romantic", "intense", "peaceful",
    "triumphant", "haunting", "playful", "mysterious", "epic",
    "cinematic", "intimate", "raw", "polished",
]

# Vocal descriptors for style field
VOCAL_DESCRIPTORS = [
    "male vocals", "female vocals", "deep male voice", "high female voice",
    "breathy vocals", "powerful vocals", "raspy vocals", "smooth vocals",
    "falsetto", "belting", "whispered vocals", "auto-tuned vocals",
    "choir harmonies", "layered vocals", "solo vocalist",
]

# Common negative prompts (place at END of style)
NEGATIVE_PROMPTS = [
    "no autotune", "no heavy reverb", "no falsetto", "no screaming",
    "no drums", "no bass drop", "no electronic sounds", "no distortion",
    "no spoken word", "no rap section", "no choir", "no fade out",
]

# =============================================================
# v5.5 Specific Features
# =============================================================

V55_FEATURES = {
    "voices": {
        "description": "Clone your own voice for AI-generated songs",
        "availability": "Pro and Premier subscribers only",
        "requirements": "Clean acapella or produced track + voice verification",
        "tips": [
            "Record in a quiet environment with minimal background noise",
            "Avoid heavy reverb or effects on the source audio",
            "Upload 30+ seconds of clear singing for best results",
            "Voice verification matches your live speech to your singing",
        ],
    },
    "custom_models": {
        "description": "Train Suno on your original music catalog",
        "availability": "Pro and Premier subscribers (up to 3 models)",
        "requirements": "Minimum 6 original songs",
        "tips": [
            "Use songs that represent your consistent style",
            "More songs = better model quality",
            "Name your model descriptively for easy selection",
        ],
    },
    "my_taste": {
        "description": "AI learns your preferences over time",
        "availability": "All users",
        "tips": [
            "Keep using Suno regularly — it learns from your choices",
            "Detailed prompts always override My Taste preferences",
            "Works best with the magic wand auto-style feature",
        ],
    },
    "negative_prompting": {
        "description": "Tell Suno what NOT to include",
        "format": "Add 'no X' at the end of your style prompt",
        "examples": ["no autotune", "no heavy reverb", "no falsetto", "no drums"],
    },
    "studio_mode": {
        "description": "Stem separation, section editing, longer generation",
        "features": ["Stem export", "Section-level editing", "Extended duration", "Higher quality output"],
    },
}


def get_section_energy(section_label: str, mood: str = "") -> str:
    """Get the recommended energy tag for a section.

    Returns a Suno v5.5 energy metatag string.
    """
    high_energy = {"Chorus", "Drop", "Hook", "Post-Chorus"}
    building = {"Pre-Chorus", "Build"}
    low_energy = {"Intro", "Verse", "Bridge", "Outro", "Break", "Interlude"}

    for he in high_energy:
        if he.lower() in section_label.lower():
            return "[Energy: High]"
    for be in building:
        if be.lower() in section_label.lower():
            return "[Energy: Building]"
    for le in low_energy:
        if le.lower() in section_label.lower():
            if "sad" in mood.lower() or "melancholic" in mood.lower():
                return "[Energy: Low]"
            return "[Energy: Medium]"
    return ""


def get_vocal_tag_for_section(section_label: str, vocal_style: str = "") -> str:
    """Get the recommended vocal delivery tag for a section."""
    label_lower = section_label.lower()

    if "intro" in label_lower:
        if "whisper" in vocal_style.lower() or "breathy" in vocal_style.lower():
            return "[Vocal Style: Whisper]"
        return ""
    if "chorus" in label_lower:
        if "belt" in vocal_style.lower() or "powerful" in vocal_style.lower():
            return "[Vocal Style: Belt]"
        return ""
    if "bridge" in label_lower:
        return "[Vocal Style: Falsetto]" if "falsetto" in vocal_style.lower() else ""
    if "rap" in label_lower:
        return "[Vocal Style: Rap]"

    return ""


def build_optimal_suno_prompt(
    genre: str = "Pop",
    mood: str = "uplifting",
    instruments: list[str] = None,
    vocal_desc: str = "female vocals",
    bpm: float = 120,
    key: str = "C major",
    negative: list[str] = None,
) -> str:
    """Build an optimal Suno v5.5 style prompt following best practices.

    Format: genre, mood, vocal, key+BPM, instruments, negative (at end)
    """
    parts = [genre, mood, vocal_desc, f"{key}, {bpm:.0f} BPM"]

    if instruments:
        parts.extend(instruments[:3])  # Max 3 instruments in style

    # Negative prompts ALWAYS at the end
    if negative:
        parts.extend(f"no {n}" for n in negative)

    return ", ".join(parts)
