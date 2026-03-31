"""Prompt templates for AI music generation — matched to actual tool UIs."""

# ============================================================
# SUNO — Custom Mode has TWO separate input fields:
#   1. "歌詞" (Lyrics) — paste lyrics here
#   2. "スタイル" (Style) — paste style description here
# Our output must be split into two copyable sections.
# ============================================================

# Goes into Suno's "スタイル / Style" text box
# Strategy: genre + mood first (highest impact), then vocal, then technical
SUNO_STYLE_TEMPLATE = """\
{genre}, {mood}, {energy}, {vocal_engineering}, {bpm} BPM in {key}, {time_signature}, {instruments}, {dynamics_arc}, chords: {chord_progression}, {drum_groove}, {language}\
"""

# Goes into Suno's "歌詞 / Lyrics" text box
# Suno recognizes [Verse], [Chorus], [Bridge], [Intro], [Outro] markers
SUNO_LYRICS_TEMPLATE = """\
{structured_lyrics}\
"""

# ============================================================
# LYRIA — flowing narrative format, ~500 word max
# ============================================================
LYRIA_TEMPLATE = """\
An {mood_adjective} {genre} track in {key} at {bpm} BPM. {mood_sentence}

{section_narrative}

Instruments: {instruments}. {chord_sentence}

Vocal delivery: {vocal_engineering}. {dynamics_arc_sentence}

{drum_sentence}

{language_sentence}
{lyrics_block}\
"""

# ============================================================
# Complete reproduction prompt — ALL analysis details
# For reference / Udio / other tools
# ============================================================
GENERIC_TEMPLATE = """\
=== COMPLETE MUSIC REPRODUCTION PROMPT ===
=== Target: 95%+ faithful reproduction  ===

## 1. Core Musical Parameters
- BPM: {bpm}
- Key: {key}
- Time Signature: {time_signature}
- Genre: {genre}

## 2. Mood & Emotion
- Overall Mood: {mood}
- Mood Tags: {mood_tags}
- Emotional Arc: {emotional_arc}
- Energy Curve: {energy_curve}

## 3. Chord Progression (CRITICAL for reproduction)
- Main Progression: {chord_progression}
- Chords per Section:
{chord_per_section}

## 4. Rhythm & Drum Pattern
- Feel: {feel}
- Energy Level: {energy}
- Groove: {drum_groove}
- Drum Pattern (grid):
{drum_notation}
- Kick:  |{kick_pattern}|
- Snare: |{snare_pattern}|
- HiHat: |{hihat_pattern}|

## 5. Melody & Pitch
- Vocal Range: {vocal_range}
- Melody Character: {melody_description}
- Melodic Contour: {melody_contour}
- Note Sequence: {melody_notation}

## 6. Vocal Style & Technique
- Style Tags: [{vocal_style_tags}]
- Vocal Engineering: {vocal_engineering}
- Vibrato: {vibrato}
- Register: {register}
- Tone: {tone}
- Articulation: {articulation}

## 7. Dynamics & Volume
- Overall: {dynamics_marking}
- Dynamic Range: {dynamic_range}
- Dynamics Arc: {dynamics_arc}
{volume_map}

## 8. Instruments
- {instruments}

## 9. Texture Evolution
- {texture_evolution}

## 10. Song Structure
{structure_detail}

## 11. Lyrics ({language})
{structured_lyrics}

## Reproduction Notes
{notes}
"""

# Udio style prompt — concise single block
UDIO_TEMPLATE = """\
{genre} song in {key}, {bpm} BPM, {time_signature} time.
{feel}, {energy}. Mood: {mood}.
Chords: {chord_progression}
Instruments: {instruments}.
Vocal: {vocal_range}, {vocal_engineering}.
{vibrato}. {tone}. {articulation}.
Dynamics: {dynamics_marking}, {dynamic_range} dynamic range. {dynamics_arc}.
Drums: {drum_groove}. Pattern: {drum_notation}
{melody_description}
{emotional_arc}

Lyrics ({language}):
{structured_lyrics}
"""
