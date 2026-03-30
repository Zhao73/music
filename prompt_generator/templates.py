"""Prompt templates for AI music generation tools."""

# Suno AI style prompt template
SUNO_TEMPLATE = """\
[Genre: {genre}]
[BPM: {bpm}]
[Key: {key}]
[Time Signature: {time_signature}]
[Mood/Feel: {feel}]
[Energy: {energy}]
[Instruments: {instruments}]
[Vocal Range: {vocal_range}]
[Language: {language}]

{structured_lyrics}
"""

# Generic / universal prompt template
GENERIC_TEMPLATE = """\
=== Music Recreation Prompt ===

## Musical Parameters
- BPM: {bpm}
- Key: {key}
- Time Signature: {time_signature}
- Mood/Feel: {feel}
- Energy Level: {energy}
- Instruments: {instruments}
- Vocal Range: {vocal_range}
- Melody: {melody_description}

## Song Structure
{structure_summary}

## Lyrics ({language})
{structured_lyrics}

## Additional Notes
{notes}
"""

# Udio style prompt template
UDIO_TEMPLATE = """\
{genre} song in {key}, {bpm} BPM, {feel}, {energy}.
Instruments: {instruments}.
Vocal range {vocal_range}. {melody_description}

Lyrics ({language}):
{structured_lyrics}
"""
