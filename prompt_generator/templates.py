"""Prompt templates for AI music generation tools — full reproduction detail."""

# Suno AI style prompt template — maximum detail for faithful reproduction
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
[Language: {language}]
[Vocal Style: {vocal_style_tags}]
[Dynamics: {dynamics_marking}]

{structured_lyrics}
"""

# Generic / universal prompt — complete reproduction prompt with ALL analysis details
GENERIC_TEMPLATE = """\
=== COMPLETE MUSIC REPRODUCTION PROMPT ===

## Basic Musical Parameters
- BPM: {bpm}
- Key: {key}
- Time Signature: {time_signature}
- Genre: {genre}

## Mood & Emotion
- Overall Mood: {mood}
- Mood Tags: {mood_tags}
- Emotional Arc: {emotional_arc}
- Energy Curve: {energy_curve}

## Rhythm & Feel
- Feel: {feel}
- Energy Level: {energy}
- Rhythm Description: {rhythm_description}

## Melody & Pitch
- Vocal Range: {vocal_range}
- Melody Character: {melody_description}
- Melodic Contour: {melody_contour}
- Melody Notation (first 50 notes): {melody_notation}

## Vocal Style & Technique
- Vocal Style Tags: [{vocal_style_tags}]
- Vibrato: {vibrato}
- Register: {register}
- Tone Quality: {tone}
- Articulation: {articulation}

## Dynamics & Volume
- Overall Dynamics: {dynamics_marking}
- Dynamic Range: {dynamic_range}
- Volume Map: {volume_map}
- Dynamic Events: {dynamic_events}

## Instruments
- {instruments}

## Song Structure
{structure_detail}

## Lyrics ({language})
{structured_lyrics}

## Reproduction Notes
{notes}
"""

# Udio style prompt template — concise but detailed
UDIO_TEMPLATE = """\
{genre} song in {key}, {bpm} BPM, {time_signature} time.
{feel}, {energy}. Mood: {mood}.
Instruments: {instruments}.
Vocal: {vocal_range}, {vocal_style_tags}.
{vibrato}. {tone}. {articulation}.
Dynamics: {dynamics_marking}, {dynamic_range} dynamic range.
{melody_description}
{emotional_arc}

Lyrics ({language}):
{structured_lyrics}
"""
