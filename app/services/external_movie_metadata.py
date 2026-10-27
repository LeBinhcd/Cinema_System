"""Admin-only TMDB metadata retrieval with strict allowlist and sanitization."""
from __future__ import annotations
import html
import logging
import json
import os

import re
from datetime import datetime, timezone
from urllib.parse import quote
from urllib.request import Request, urlopen

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
logger = logging.getLogger(__name__)

MAX_RESPONSE_BYTES = 1_000_000
TIMEOUT_SECONDS = 8

class ExternalMetadataError(RuntimeError):
    pass


def _clean(value, limit=1200):
    if not isinstance(value, str):
        return ""
    value = html.unescape(re.sub(r"<[^>]*>", " ", value))
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", value)
    return " ".join(value.split())[:limit]



def _tmdb_get(path, key, params):
    query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
    request = Request(
        f"{TMDB_BASE_URL}{path}?api_key={quote(key)}&{query}",
        headers={"Accept": "application/json", "User-Agent": "CineVista/1.0"},
    )
    logger.info("[TMDB ->] path=%s params=%s", path, params)
    started = __import__("time").perf_counter()
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read(MAX_RESPONSE_BYTES + 1)
        logger.info(
            "[TMDB <-] path=%s status=200 duration_ms=%.1f response_bytes=%d",
            path,
            (__import__("time").perf_counter() - started) * 1000,
            len(payload),
        )
    except Exception as exc:
        logger.error(
            "[TMDB !!] path=%s error=%s duration_ms=%.1f",
            path,
            type(exc).__name__,
            (__import__("time").perf_counter() - started) * 1000,
        )
        raise ExternalMetadataError("Không thể lấy metadata phim từ TMDB.") from exc
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ExternalMetadataError("Metadata từ TMDB vượt quá giới hạn cho phép.")
    try:
        return json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ExternalMetadataError("TMDB trả về dữ liệu không hợp lệ.") from exc


def fetch_movie_metadata(title):
    """Fetch sanitized movie metadata from TMDB for the Admin-only description flow."""
    key = os.getenv("TMDB_API_KEY", "").strip()
    if not key:
        raise ExternalMetadataError("Chưa cấu hình TMDB_API_KEY cho chức năng lấy dữ liệu phim bên ngoài.")
    title = _clean(title, 255)
    if not title:
        raise ExternalMetadataError("Tên phim không được để trống.")
    try:
        data = _tmdb_get("/search/movie", key, {
            "language": "vi-VN",
            "query": title,
            "include_adult": "false",
        })
        results = data.get("results", [])
        if not results:
            raise ExternalMetadataError("TMDB không tìm thấy phim phù hợp.")
        result = results[0]
        movie_id = result.get("id")
        if not movie_id:
            raise ExternalMetadataError("TMDB trả về phim không hợp lệ.")
        details = _tmdb_get(f"/movie/{movie_id}", key, {"language": "vi-VN"})
        credits = _tmdb_get(f"/movie/{movie_id}/credits", key, {"language": "vi-VN"})
    except ExternalMetadataError:
        raise
    except (IndexError, TypeError, AttributeError) as exc:
        raise ExternalMetadataError("TMDB không trả về metadata hợp lệ.") from exc

    movie_id = details.get("id")
    name = _clean(details.get("title") or details.get("original_title"), 255)
    overview = _clean(details.get("overview") or result.get("overview"), 2000)
    genres = [_clean(item.get("name"), 80) for item in details.get("genres", []) if isinstance(item, dict)]
    director = next((
        _clean(item.get("name"), 120)
        for item in credits.get("crew", [])
        if isinstance(item, dict) and item.get("job") == "Director"
    ), "")
    cast = [
        _clean(item.get("name"), 120)
        for item in credits.get("cast", [])[:8]
        if isinstance(item, dict)
    ]
    if not movie_id or not name or not overview:
        raise ExternalMetadataError("Metadata TMDB thiếu thông tin cần thiết để sinh mô tả.")
    return {
        "provider": "tmdb",
        "source_url": f"https://www.themoviedb.org/movie/{movie_id}",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "title": name,
        "original_title": _clean(details.get("original_title"), 255),
        "release_date": _clean(details.get("release_date"), 20),
        "overview": overview,
        "genres": genres,
        "director": director,
        "cast": cast,
        "poster_url": (
            f"{TMDB_IMAGE_BASE_URL}{details['poster_path']}"
            if details.get("poster_path") else ""
        ),
    }

