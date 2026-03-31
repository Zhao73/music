"""Chart data analyzer — connects chart patterns to the analysis pipeline.

Scores analyzed songs against chart patterns and provides optimization suggestions.
"""

from chart_data.knowledge_base import get_popularity_score, get_chart_patterns, CHART_PATTERNS
from music_knowledge.hit_formulas import get_genre_profile


def score_analysis_result(analysis_result) -> dict:
    """Score an AnalysisResult from pipeline.py against chart patterns.

    Args:
        analysis_result: AnalysisResult dataclass from pipeline.py

    Returns:
        dict: {
            "overall_score": 72.5,
            "factors": {"tempo": 85, "key": 90, ...},
            "suggestions": ["Consider faster tempo...", ...],
            "chart_comparison": {"your_bpm": 95, "chart_avg": 120, ...},
        }
    """
    # Extract params from analysis result
    params = {}

    if analysis_result.rhythm:
        params["bpm"] = analysis_result.rhythm.bpm

    if analysis_result.key:
        params["key"] = analysis_result.key.key

    if analysis_result.chords:
        params["chord_progression"] = analysis_result.chords.chord_progression

    if analysis_result.emotion:
        params["mood"] = analysis_result.emotion.overall_mood

    if analysis_result.duration_seconds:
        params["duration_seconds"] = analysis_result.duration_seconds

    if analysis_result.instruments:
        params["instruments"] = analysis_result.instruments.detected

    # Get base score
    result = get_popularity_score(params)

    # Add comparison data
    comparison = {}
    if params.get("bpm"):
        comparison["your_bpm"] = params["bpm"]
        comparison["chart_avg_bpm"] = CHART_PATTERNS["tempo"]["mean"]
    if params.get("key"):
        comparison["your_key"] = params["key"]
        comparison["top_keys"] = CHART_PATTERNS["key"]["most_common"][:5]
    if params.get("duration_seconds"):
        comparison["your_duration"] = params["duration_seconds"]
        comparison["chart_avg_duration"] = CHART_PATTERNS["duration_seconds"]["mean"]

    result["chart_comparison"] = comparison
    return result


def get_chart_optimized_params(genre: str = "pop") -> dict:
    """Return a parameter set optimized for chart success.

    Used by inspiration/generator.py's hit_optimized() function.
    """
    profile = get_genre_profile(genre)
    patterns = get_chart_patterns()

    return {
        "bpm": profile.get("bpm_sweet", patterns["tempo"]["mean"]),
        "key": profile["common_keys"][0] if profile.get("common_keys") else "C major",
        "chord_progression": profile["common_progressions"][0][0] if profile.get("common_progressions") else "I-V-vi-IV",
        "mood": profile["moods"][0] if profile.get("moods") else "happy / energetic",
        "instruments": profile.get("instruments", [])[:5],
        "vocal_style_tags": profile.get("vocal_styles", [])[:2],
        "drum_groove": profile["drum_grooves"][0] if profile.get("drum_grooves") else "straight 4/4 rock",
        "genre": genre,
    }


def format_chart_score(score_result: dict) -> str:
    """Format a chart score result as human-readable text."""
    lines = [
        f"Overall Chart Potential: {score_result['overall_score']:.0f}/100",
        "",
        "Factor Breakdown:",
    ]

    factor_labels = {
        "tempo": "Tempo/BPM",
        "key": "Musical Key",
        "chords": "Chord Progression",
        "mood": "Mood/Energy",
        "duration": "Duration",
    }

    for factor, score in score_result.get("factors", {}).items():
        label = factor_labels.get(factor, factor)
        bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
        lines.append(f"  {label:20s} [{bar}] {score:.0f}")

    comparison = score_result.get("chart_comparison", {})
    if comparison:
        lines.append("")
        lines.append("Comparison with Chart Hits:")
        if "your_bpm" in comparison:
            lines.append(f"  Your BPM: {comparison['your_bpm']:.0f} | Chart Average: {comparison['chart_avg_bpm']:.0f}")
        if "your_key" in comparison:
            lines.append(f"  Your Key: {comparison['your_key']} | Top Keys: {', '.join(comparison['top_keys'][:3])}")
        if "your_duration" in comparison:
            lines.append(f"  Your Duration: {comparison['your_duration']:.0f}s | Chart Average: {comparison['chart_avg_duration']:.0f}s")

    suggestions = score_result.get("suggestions", [])
    if suggestions:
        lines.append("")
        lines.append("Suggestions for Improvement:")
        for s in suggestions:
            lines.append(f"  • {s}")

    return "\n".join(lines)
