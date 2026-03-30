"""Prompt templates for AI music generation — maximum reproduction fidelity."""

# Suno AI style prompt — structured for best Suno results
SUNO_TEMPLATE = """\
[Genre: {genre}]
[BPM: {bpm}]
[Key: {key}]
[Time Signature: {time_signature}]
[Mood: {mood}]
[Feel: {feel}]
[Energy: {energy}]
[Instruments: {instruments}]
[Vocal Range: {vocal_range}]
[Vocal Style: {vocal_style_tags}]
[Dynamics: {dynamics_marking}]
[Chord Progression: {chord_progression}]
[Drum Pattern: {drum_groove}]
[Language: {language}]

{structured_lyrics}
"""

# Complete reproduction prompt — ALL analysis details for 95%+ fidelity
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
- Vibrato: {vibrato}
- Register: {register}
- Tone: {tone}
- Articulation: {articulation}

## 7. Dynamics & Volume
- Overall: {dynamics_marking}
- Dynamic Range: {dynamic_range}
{volume_map}

## 8. Instruments
- {instruments}

## 9. Song Structure
{structure_detail}

## 10. Lyrics ({language})
{structured_lyrics}

## Reproduction Notes
{notes}
"""

# Udio style prompt — concise but complete
UDIO_TEMPLATE = """\
{genre} song in {key}, {bpm} BPM, {time_signature} time.
{feel}, {energy}. Mood: {mood}.
Chords: {chord_progression}
Instruments: {instruments}.
Vocal: {vocal_range}, {vocal_style_tags}.
{vibrato}. {tone}. {articulation}.
Dynamics: {dynamics_marking}, {dynamic_range} dynamic range.
Drums: {drum_groove}. Pattern: {drum_notation}
{melody_description}
{emotional_arc}

Lyrics ({language}):
{structured_lyrics}
"""
