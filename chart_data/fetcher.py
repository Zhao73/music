"""Optional live chart data fetching — Billboard and Spotify.

All functions gracefully degrade if dependencies are not installed.
"""

# Optional imports
try:
    import billboard
    BILLBOARD_AVAILABLE = True
except ImportError:
    billboard = None
    BILLBOARD_AVAILABLE = False

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    SPOTIFY_AVAILABLE = True
except ImportError:
    spotipy = None
    SPOTIFY_AVAILABLE = False


def is_billboard_available() -> bool:
    return BILLBOARD_AVAILABLE


def is_spotify_available() -> bool:
    return SPOTIFY_AVAILABLE


def fetch_billboard_hot100(date: str = None) -> list[dict]:
    """Fetch current Billboard Hot 100 chart.

    Args:
        date: Optional date string 'YYYY-MM-DD'. None for current chart.

    Returns:
        List of dicts: [{"rank": 1, "title": "...", "artist": "...", "weeks": 5}, ...]
        Empty list if billboard.py is not installed.
    """
    if not BILLBOARD_AVAILABLE:
        return []

    try:
        if date:
            chart = billboard.ChartData("hot-100", date=date)
        else:
            chart = billboard.ChartData("hot-100")

        results = []
        for entry in chart:
            results.append({
                "rank": entry.rank,
                "title": entry.title,
                "artist": entry.artist,
                "weeks": entry.weeks,
                "peak": entry.peakPos,
                "last_week": entry.lastPos,
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]


def fetch_billboard_global200(date: str = None) -> list[dict]:
    """Fetch Billboard Global 200 chart."""
    if not BILLBOARD_AVAILABLE:
        return []

    try:
        if date:
            chart = billboard.ChartData("billboard-global-200", date=date)
        else:
            chart = billboard.ChartData("billboard-global-200")

        results = []
        for entry in chart:
            results.append({
                "rank": entry.rank,
                "title": entry.title,
                "artist": entry.artist,
                "weeks": entry.weeks,
            })
        return results
    except Exception as e:
        return [{"error": str(e)}]


def fetch_spotify_features(
    track_ids: list[str],
    client_id: str = "",
    client_secret: str = "",
) -> list[dict]:
    """Fetch Spotify audio features for given track IDs.

    Args:
        track_ids: list of Spotify track IDs
        client_id: Spotify API client ID
        client_secret: Spotify API client secret

    Returns:
        List of audio feature dicts. Empty if spotipy not installed.
    """
    if not SPOTIFY_AVAILABLE:
        return []

    if not client_id or not client_secret:
        return []

    try:
        auth = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret,
        )
        sp = spotipy.Spotify(auth_manager=auth)
        features = sp.audio_features(track_ids)
        return [f for f in features if f is not None]
    except Exception as e:
        return [{"error": str(e)}]


def search_spotify_track(
    query: str,
    client_id: str = "",
    client_secret: str = "",
    limit: int = 5,
) -> list[dict]:
    """Search for tracks on Spotify.

    Returns:
        List of dicts: [{"id": "...", "title": "...", "artist": "...", "album": "..."}, ...]
    """
    if not SPOTIFY_AVAILABLE or not client_id or not client_secret:
        return []

    try:
        auth = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret,
        )
        sp = spotipy.Spotify(auth_manager=auth)
        results = sp.search(q=query, type="track", limit=limit)
        tracks = []
        for item in results.get("tracks", {}).get("items", []):
            tracks.append({
                "id": item["id"],
                "title": item["name"],
                "artist": ", ".join(a["name"] for a in item["artists"]),
                "album": item["album"]["name"],
            })
        return tracks
    except Exception as e:
        return [{"error": str(e)}]


def analyze_chart_patterns(features: list[dict]) -> dict:
    """Aggregate Spotify audio features into statistical patterns.

    Args:
        features: list of Spotify audio_features dicts

    Returns:
        dict with aggregated stats (same format as knowledge_base.CHART_PATTERNS)
    """
    if not features or "error" in features[0]:
        return {}

    def _stats(values):
        if not values:
            return {"mean": 0, "min": 0, "max": 0}
        return {
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        }

    tempos = [f["tempo"] for f in features if "tempo" in f]
    danceability = [f["danceability"] for f in features if "danceability" in f]
    energy = [f["energy"] for f in features if "energy" in f]
    valence = [f["valence"] for f in features if "valence" in f]
    acousticness = [f["acousticness"] for f in features if "acousticness" in f]
    loudness = [f["loudness"] for f in features if "loudness" in f]
    duration = [f["duration_ms"] / 1000 for f in features if "duration_ms" in f]

    # Key distribution
    key_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    key_counts = {}
    for f in features:
        if "key" in f and "mode" in f:
            k = key_names[f["key"] % 12]
            mode = "major" if f["mode"] == 1 else "minor"
            full_key = f"{k} {mode}"
            key_counts[full_key] = key_counts.get(full_key, 0) + 1

    total = sum(key_counts.values()) or 1
    key_dist = {k: v / total for k, v in sorted(key_counts.items(), key=lambda x: -x[1])}

    return {
        "tempo": _stats(tempos),
        "danceability": _stats(danceability),
        "energy": _stats(energy),
        "valence": _stats(valence),
        "acousticness": _stats(acousticness),
        "loudness_db": _stats(loudness),
        "duration_seconds": _stats(duration),
        "key_distribution": key_dist,
        "sample_size": len(features),
    }
