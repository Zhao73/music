"""FastAPI REST API for MusicLens - analyze music and generate with Lyria."""

import os
import sys
import json
import tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from pipeline import analyze
from music_generation.lyria_client import is_available as lyria_available, generate_music
from music_generation.prompt_builder import build_lyria_prompt, build_suno_style_from_fields, build_udio_prompt_from_fields
from inspiration.generator import (
    fully_random, random_from_genre, random_from_mood,
    mutate_params, hit_optimized, format_inspiration,
)
from chart_data.knowledge_base import get_popularity_score, get_chart_patterns
from chart_data.fetcher import is_billboard_available, fetch_billboard_hot100
from chart_data.analyzer import format_chart_score

app = FastAPI(
    title="MusicLens API",
    description="Analyze music files and generate music with Google Lyria 3 Pro.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize(obj):
    """Convert analysis objects to JSON-safe dicts (handles numpy types)."""
    if obj is None:
        return None
    if isinstance(obj, (int, float, str, bool)):
        return obj
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(i) for i in obj]
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _serialize(getattr(obj, k)) for k in obj.__dataclass_fields__}
    return str(obj)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    bpm: float = 120
    key: str = "C major"
    chord_progression: str = ""
    lyrics: str = ""
    instruments: list[str] = Field(default_factory=list)
    mood: str = ""
    vocal_style_tags: list[str] = Field(default_factory=list)
    drum_groove: str = ""
    language: str = "English"
    genre: str = ""
    api_key: str = ""


class PromptRequest(BaseModel):
    bpm: float = 120
    key: str = "C major"
    chord_progression: str = ""
    lyrics: str = ""
    instruments: list[str] = Field(default_factory=list)
    mood: str = ""
    vocal_style_tags: list[str] = Field(default_factory=list)
    drum_groove: str = ""
    language: str = "English"
    genre: str = ""


class InspireRequest(BaseModel):
    mode: str = "fully_random"  # fully_random, genre, mood, hit_formula
    genre: str = "pop"
    mood: str = ""
    seed: int = None


class MutateRequest(BaseModel):
    params: dict = Field(default_factory=dict)
    variation: float = 0.3
    seed: int = None


class ChartScoreRequest(BaseModel):
    bpm: float = 0
    key: str = ""
    chord_progression: str = ""
    mood: str = ""
    duration_seconds: float = 0


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    """Health check — includes Lyria availability status."""
    return {
        "status": "ok",
        "lyria_available": lyria_available(),
    }


@app.post("/api/analyze")
async def analyze_audio(
    file: UploadFile = File(...),
    source_language: str = "auto",
    target_language: str = "",
):
    """Upload an audio file and receive full analysis results as JSON."""
    suffix = os.path.splitext(file.filename or "audio.wav")[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        result = analyze(
            audio_path=tmp_path,
            source_language=source_language if source_language != "auto" else None,
            target_language=target_language or None,
        )
        return JSONResponse(content=_serialize(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)


@app.post("/api/generate")
def generate(req: GenerateRequest):
    """Generate music via Lyria from structured parameters. Returns audio file."""
    prompt = build_lyria_prompt(
        bpm=req.bpm,
        key=req.key,
        chord_progression=req.chord_progression,
        lyrics=req.lyrics,
        instruments=req.instruments or None,
        mood=req.mood,
        vocal_style_tags=req.vocal_style_tags or None,
        drum_groove=req.drum_groove,
        language=req.language,
        genre=req.genre,
    )

    result = generate_music(prompt, api_key=req.api_key or None)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)

    return FileResponse(
        result.audio_path,
        media_type=result.mime_type or "audio/wav",
        filename="generated_music" + os.path.splitext(result.audio_path)[1],
    )


@app.post("/api/prompt")
def build_prompt(req: PromptRequest):
    """Build prompts for Lyria / Suno / Udio without generating audio."""
    lyria = build_lyria_prompt(
        bpm=req.bpm, key=req.key, chord_progression=req.chord_progression,
        lyrics=req.lyrics, instruments=req.instruments or None, mood=req.mood,
        vocal_style_tags=req.vocal_style_tags or None, drum_groove=req.drum_groove,
        language=req.language, genre=req.genre,
    )
    suno = build_suno_style_from_fields(
        bpm=req.bpm, key=req.key, chord_progression=req.chord_progression,
        instruments=req.instruments or None, mood=req.mood,
        vocal_style_tags=req.vocal_style_tags or None, drum_groove=req.drum_groove,
        language=req.language, genre=req.genre,
    )
    udio = build_udio_prompt_from_fields(
        bpm=req.bpm, key=req.key, chord_progression=req.chord_progression,
        lyrics=req.lyrics, instruments=req.instruments or None, mood=req.mood,
        vocal_style_tags=req.vocal_style_tags or None, drum_groove=req.drum_groove,
        language=req.language, genre=req.genre,
    )
    return {"lyria_prompt": lyria, "suno_style": suno, "udio_prompt": udio}


# ---------------------------------------------------------------------------
# Inspiration Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/inspire")
def inspire(req: InspireRequest):
    """Generate random musically-valid parameters for inspiration."""
    if req.mode == "genre":
        result = random_from_genre(req.genre, seed=req.seed)
    elif req.mode == "mood":
        result = random_from_mood(req.mood, seed=req.seed)
    elif req.mode == "hit_formula":
        result = hit_optimized(req.genre, seed=req.seed)
    else:
        result = fully_random(seed=req.seed)

    return _serialize(result)


@app.post("/api/mutate")
def mutate(req: MutateRequest):
    """Mutate existing parameters with controlled variation."""
    result = mutate_params(req.params, variation=req.variation, seed=req.seed)
    return _serialize(result)


# ---------------------------------------------------------------------------
# Chart Data Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/charts/patterns")
def chart_patterns():
    """Return the static chart patterns knowledge base."""
    return get_chart_patterns()


@app.post("/api/charts/score")
def chart_score(req: ChartScoreRequest):
    """Score parameters against chart patterns."""
    params = {
        "bpm": req.bpm,
        "key": req.key,
        "chord_progression": req.chord_progression,
        "mood": req.mood,
        "duration_seconds": req.duration_seconds,
    }
    # Remove empty values
    params = {k: v for k, v in params.items() if v}
    result = get_popularity_score(params)
    return result


@app.get("/api/charts/billboard")
def billboard_hot100():
    """Fetch current Billboard Hot 100 (requires billboard.py)."""
    if not is_billboard_available():
        return {"error": "billboard.py not installed", "tracks": []}
    tracks = fetch_billboard_hot100()
    return {"tracks": tracks}
