"""Random / Inspiration generator — musically valid parameter sets.

Generates complete, coherent music parameter sets for creative exploration.
Uses hit_formulas knowledge base to ensure musical validity.
"""

import random
from dataclasses import dataclass, field

from music_knowledge.hit_formulas import (
    HIT_SONG_PROFILES,
    MOOD_GENRE_COMPAT,
    get_genre_profile,
)


@dataclass
class InspirationResult:
    bpm: float = 120.0
    key: str = "C major"
    chord_progression: str = "I-V-vi-IV"
    mood: str = "happy / energetic"
    genre: str = "pop"
    instruments: list[str] = field(default_factory=list)
    vocal_style_tags: list[str] = field(default_factory=list)
    drum_groove: str = "straight 4/4 rock"
    language: str = "English"
    section_structure: list[str] = field(default_factory=list)
    description: str = ""
    seed: int = 0


# All available genres
GENRES = list(HIT_SONG_PROFILES.keys())

# All keys organized by quality
MAJOR_KEYS = [
    "C major", "G major", "D major", "A major", "E major", "F major",
    "B major", "C# major", "D# major", "F# major", "G# major", "A# major",
]
MINOR_KEYS = [
    "A minor", "E minor", "D minor", "G minor", "C minor", "F minor",
    "B minor", "C# minor", "F# minor", "G# minor", "D# minor", "A# minor",
]

LANGUAGES = [
    "English", "Chinese", "Japanese", "Korean", "Spanish",
    "French", "Portuguese", "German", "Italian", "Thai",
]


def random_from_genre(genre: str, seed: int = None) -> InspirationResult:
    """Generate complete musically valid parameters for a given genre."""
    rng = random.Random(seed)
    actual_seed = seed if seed is not None else rng.randint(0, 999999)
    rng = random.Random(actual_seed)

    profile = get_genre_profile(genre)

    # BPM — weighted toward sweet spot
    lo, hi = profile["bpm_range"]
    sweet = profile["bpm_sweet"]
    bpm = _weighted_bpm(rng, lo, hi, sweet)

    # Key — weighted toward common keys
    common_keys = profile["common_keys"]
    if rng.random() < 0.7:
        key = rng.choice(common_keys)
    else:
        all_keys = MAJOR_KEYS + MINOR_KEYS
        key = rng.choice(all_keys)

    # Chord progression — weighted by popularity
    progs = profile["common_progressions"]
    chord_progression = _weighted_choice(rng, progs)

    # Mood — pick compatible mood
    moods = profile["moods"]
    mood = rng.choice(moods)

    # Instruments — pick 3-6 from genre set
    all_inst = profile["instruments"]
    n_inst = rng.randint(3, min(6, len(all_inst)))
    instruments = rng.sample(all_inst, n_inst)

    # Vocal style — pick 1-3
    all_vocal = profile["vocal_styles"]
    n_vocal = rng.randint(1, min(3, len(all_vocal)))
    vocal_style_tags = rng.sample(all_vocal, n_vocal)

    # Drum groove
    drum_groove = rng.choice(profile["drum_grooves"])

    # Structure
    section_structure = list(profile["structure"])

    # Language
    language = rng.choice(LANGUAGES) if rng.random() < 0.3 else "English"

    description = (
        f"A {mood.split('/')[0].strip()} {genre} track at {bpm:.0f} BPM in {key}, "
        f"featuring {', '.join(instruments[:3])} with {chord_progression} progression."
    )

    return InspirationResult(
        bpm=round(bpm, 1),
        key=key,
        chord_progression=chord_progression,
        mood=mood,
        genre=genre,
        instruments=instruments,
        vocal_style_tags=vocal_style_tags,
        drum_groove=drum_groove,
        language=language,
        section_structure=section_structure,
        description=description,
        seed=actual_seed,
    )


def fully_random(seed: int = None) -> InspirationResult:
    """Generate a fully random but musically valid parameter set."""
    rng = random.Random(seed)
    actual_seed = seed if seed is not None else rng.randint(0, 999999)
    genre = random.Random(actual_seed).choice(GENRES)
    return random_from_genre(genre, seed=actual_seed)


def random_from_mood(mood: str, seed: int = None) -> InspirationResult:
    """Generate parameters starting from a mood, picking compatible genre."""
    rng = random.Random(seed)
    actual_seed = seed if seed is not None else rng.randint(0, 999999)
    rng = random.Random(actual_seed)

    compatible_genres = MOOD_GENRE_COMPAT.get(mood, GENRES)
    # Filter to genres we have profiles for
    available = [g for g in compatible_genres if g in HIT_SONG_PROFILES]
    if not available:
        available = GENRES

    genre = rng.choice(available)
    result = random_from_genre(genre, seed=actual_seed)
    result.mood = mood  # Override mood to match request
    result.description = (
        f"A {mood.split('/')[0].strip()} {genre} track at {result.bpm:.0f} BPM in {result.key}, "
        f"featuring {', '.join(result.instruments[:3])} with {result.chord_progression} progression."
    )
    return result


def mutate_params(
    params: dict,
    variation: float = 0.3,
    seed: int = None,
) -> InspirationResult:
    """Apply controlled mutations to existing parameters.

    Args:
        params: dict with keys matching InspirationResult fields
        variation: 0.0 = identical, 1.0 = very different
        seed: random seed for reproducibility
    """
    rng = random.Random(seed)
    actual_seed = seed if seed is not None else rng.randint(0, 999999)
    rng = random.Random(actual_seed)

    genre = params.get("genre", "pop")
    profile = get_genre_profile(genre)

    # BPM mutation
    orig_bpm = params.get("bpm", 120.0)
    bpm_delta = rng.gauss(0, variation * 20)
    new_bpm = max(50, min(200, orig_bpm + bpm_delta))

    # Key mutation — shift by semitones based on variation
    orig_key = params.get("key", "C major")
    if rng.random() < variation:
        # Shift key
        all_keys = MAJOR_KEYS if "major" in orig_key else MINOR_KEYS
        idx = all_keys.index(orig_key) if orig_key in all_keys else 0
        shift = rng.choice([-2, -1, 1, 2])
        new_key = all_keys[(idx + shift) % len(all_keys)]
    else:
        new_key = orig_key

    # Chord progression mutation
    orig_chords = params.get("chord_progression", "I-V-vi-IV")
    if rng.random() < variation and profile.get("common_progressions"):
        new_chords = _weighted_choice(rng, profile["common_progressions"])
    else:
        new_chords = orig_chords

    # Mood mutation
    orig_mood = params.get("mood", "happy / energetic")
    if rng.random() < variation:
        moods = profile.get("moods", ["happy / energetic"])
        new_mood = rng.choice(moods)
    else:
        new_mood = orig_mood

    # Instruments mutation — swap 1-2
    orig_instruments = params.get("instruments", profile.get("instruments", [])[:4])
    new_instruments = list(orig_instruments)
    if rng.random() < variation and profile.get("instruments"):
        n_swap = rng.randint(1, min(2, len(new_instruments)))
        available = [i for i in profile["instruments"] if i not in new_instruments]
        for _ in range(n_swap):
            if available and new_instruments:
                idx = rng.randint(0, len(new_instruments) - 1)
                replacement = rng.choice(available)
                available.remove(replacement)
                new_instruments[idx] = replacement

    # Vocal style mutation
    orig_vocal = params.get("vocal_style_tags", ["dynamic"])
    if rng.random() < variation and profile.get("vocal_styles"):
        new_vocal = rng.sample(profile["vocal_styles"], min(2, len(profile["vocal_styles"])))
    else:
        new_vocal = list(orig_vocal)

    # Drum groove mutation
    orig_drum = params.get("drum_groove", "straight 4/4 rock")
    if rng.random() < variation and profile.get("drum_grooves"):
        new_drum = rng.choice(profile["drum_grooves"])
    else:
        new_drum = orig_drum

    description = (
        f"Variation of original (seed {actual_seed}, {variation:.0%} mutation): "
        f"{new_mood.split('/')[0].strip()} {genre} at {new_bpm:.0f} BPM in {new_key}."
    )

    return InspirationResult(
        bpm=round(new_bpm, 1),
        key=new_key,
        chord_progression=new_chords,
        mood=new_mood,
        genre=genre,
        instruments=new_instruments,
        vocal_style_tags=new_vocal,
        drum_groove=new_drum,
        language=params.get("language", "English"),
        section_structure=profile.get("structure", []),
        description=description,
        seed=actual_seed,
    )


def hit_optimized(genre: str = "pop", seed: int = None) -> InspirationResult:
    """Generate parameters specifically optimized for chart potential.

    Always picks from proven "hit" ranges:
    - BPM near the genre sweet spot
    - Most common keys
    - #1 most popular chord progression
    - High-energy mood
    """
    rng = random.Random(seed)
    actual_seed = seed if seed is not None else rng.randint(0, 999999)
    rng = random.Random(actual_seed)

    profile = get_genre_profile(genre)

    # BPM — very close to sweet spot
    sweet = profile["bpm_sweet"]
    bpm = sweet + rng.gauss(0, 3)  # Very tight around sweet spot

    # Key — top 2 most common
    key = rng.choice(profile["common_keys"][:2])

    # Chord — #1 most popular
    chord_progression = profile["common_progressions"][0][0]

    # Mood — first (most common/upbeat)
    mood = profile["moods"][0]

    # Full instrument set
    instruments = profile["instruments"][:5]

    # Best vocal styles
    vocal_style_tags = profile["vocal_styles"][:2]

    # Standard groove
    drum_groove = profile["drum_grooves"][0]

    # Standard hit structure
    section_structure = list(profile["structure"])

    description = (
        f"Chart-optimized {genre} hit formula: {bpm:.0f} BPM in {key}, "
        f"{chord_progression} progression — the most proven combination for commercial success."
    )

    return InspirationResult(
        bpm=round(bpm, 1),
        key=key,
        chord_progression=chord_progression,
        mood=mood,
        genre=genre,
        instruments=instruments,
        vocal_style_tags=vocal_style_tags,
        drum_groove=drum_groove,
        language="English",
        section_structure=section_structure,
        description=description,
        seed=actual_seed,
    )


def format_inspiration(result: InspirationResult) -> str:
    """Format an InspirationResult as human-readable text."""
    lines = [
        f"🎵 {result.description}",
        "",
        f"Genre:       {result.genre}",
        f"BPM:         {result.bpm:.0f}",
        f"Key:         {result.key}",
        f"Chords:      {result.chord_progression}",
        f"Mood:        {result.mood}",
        f"Instruments: {', '.join(result.instruments)}",
        f"Vocals:      {', '.join(result.vocal_style_tags)}",
        f"Drums:       {result.drum_groove}",
        f"Language:    {result.language}",
        f"Structure:   {' → '.join(result.section_structure)}",
        f"Seed:        {result.seed}",
    ]
    return "\n".join(lines)


# =============================================================
# Internal helpers
# =============================================================

def _weighted_bpm(rng: random.Random, lo: float, hi: float, sweet: float) -> float:
    """Generate BPM weighted toward the sweet spot."""
    # 70% chance near sweet spot, 30% anywhere in range
    if rng.random() < 0.7:
        return sweet + rng.gauss(0, (hi - lo) * 0.1)
    return rng.uniform(lo, hi)


def _weighted_choice(rng: random.Random, weighted_items: list[tuple]) -> str:
    """Pick from a list of (item, weight) tuples using weighted random."""
    items = [item for item, _ in weighted_items]
    weights = [w for _, w in weighted_items]
    total = sum(weights)
    r = rng.random() * total
    cumulative = 0
    for item, weight in zip(items, weights):
        cumulative += weight
        if r <= cumulative:
            return item
    return items[-1]
