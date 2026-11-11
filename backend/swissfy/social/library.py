import logging
import re
from urllib.parse import quote

import requests
from rest_framework.exceptions import APIException, ValidationError

logger = logging.getLogger(__name__)

IMDB_URL = "https://v3.sg.media-imdb.com/suggestion"
IMDB_IMAGES = "https://m.media-amazon.com/images/M/"
IMDB_IMAGE_SUFFIX = "._V1_.jpg"
STEAM_URL = "https://store.steampowered.com/api"
STEAM_IMAGES = "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/"
STEAM_PARAMS = {"cc": "CH", "l": "german"}
COVERS = {
    "imdb": re.compile(r"^imdb/([\w@-]+)$"),
    "steam": re.compile(r"^steam/(\d+)$"),
}
IMDB_TYPES = {
    "movies": {"movie", "tvMovie"},
    "series": {"tvSeries", "tvMiniSeries"},
}
KINDS = [*IMDB_TYPES, "games"]
MAX_FAVORITES = 3
TIMEOUT = 10


class LibraryUnavailable(APIException):
    status_code = 503
    default_detail = "Die Bibliothek ist gerade nicht erreichbar."


def fetch(url, **params):
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError):
        logger.warning("library request failed", exc_info=True)
        raise LibraryUnavailable


def imdb_suggestions(term):
    return fetch(f"{IMDB_URL}/x/{quote(term.lower())}.json").get("d", [])


def imdb_cover(data):
    image = (data.get("i") or {}).get("imageUrl") or ""
    if image.startswith(IMDB_IMAGES) and image.endswith(IMDB_IMAGE_SUFFIX):
        path = f"imdb/{image.removeprefix(IMDB_IMAGES).removesuffix(IMDB_IMAGE_SUFFIX)}"
        if COVERS["imdb"].match(path):
            return path
    return ""


def imdb_item(data):
    return {
        "id": data["id"],
        "title": data.get("l") or "",
        "year": str(data.get("y") or ""),
        "cover": imdb_cover(data),
    }


def steam_item(id, title, year=""):
    return {"id": str(id), "title": title, "year": year, "cover": f"steam/{id}"}


def search(kind, query):
    if kind == "games":
        items = fetch(f"{STEAM_URL}/storesearch/", term=query, **STEAM_PARAMS).get("items", [])
        return [steam_item(data["id"], data.get("name") or "") for data in items]
    return [
        imdb_item(data) for data in imdb_suggestions(query) if data.get("qid") in IMDB_TYPES[kind]
    ]


def details(kind, id):
    if kind == "games" and re.fullmatch(r"\d+", id):
        app = fetch(f"{STEAM_URL}/appdetails", appids=id, **STEAM_PARAMS).get(id) or {}
        data = app.get("data") or {}
        if app.get("success") and data.get("type") == "game":
            year = re.search(r"\d{4}", (data.get("release_date") or {}).get("date") or "")
            return steam_item(id, data.get("name") or "", year[0] if year else "")
    elif kind in IMDB_TYPES and re.fullmatch(r"tt\d+", id):
        for data in imdb_suggestions(id):
            if data.get("id") == id and data.get("qid") in IMDB_TYPES[kind]:
                return imdb_item(data)
    raise ValidationError({f"favorite_{kind}": "Titel nicht gefunden."})


def cover_urls(path):
    for source, pattern in COVERS.items():
        match = pattern.match(path)
        if not match:
            continue
        if source == "imdb":
            return [f"{IMDB_IMAGES}{match[1]}._V1_UX342_.jpg"]
        return [
            f"{STEAM_IMAGES}{match[1]}/{name}" for name in ("library_600x900.jpg", "header.jpg")
        ]
    return []


def fetch_cover(path):
    for url in cover_urls(path):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
        except requests.RequestException:
            continue
        content_type = response.headers.get("Content-Type", "")
        if content_type.startswith("image/"):
            return response.content, content_type
    return None
