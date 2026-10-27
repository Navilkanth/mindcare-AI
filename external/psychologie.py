import json
import os
from typing import Any, Dict, List, Optional

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "https://psychologieetserenite.com/api/v1"
TIMEOUT = 10.0  # seconds

async def _get(path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Perform a GET request against the external API.

    Args:
        path: Relative path (e.g. "/concepts").
        params: Query‑string parameters.

    Returns:
        Parsed JSON response as a Python ``dict``.
    """
    url = f"{BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

# ---------------------------------------------------------------------------
# Public wrapper functions – thin ergonomics around the raw endpoints
# ---------------------------------------------------------------------------

async def list_concepts(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return the list of clinical concepts.

    Parameters
    ----------
    category: Optional[str]
        One of the allowed categories (attachment, cognition, couple, schema,
        mindfulness, addiction, developmental). If ``None`` all concepts are
        returned.
    """
    params = {"category": category} if category else None
    data = await _get("/concepts", params)
    return data.get("items", data)

async def get_concept(slug: str) -> Dict[str, Any]:
    """Retrieve a single concept by its slug (e.g. ``attachment-bowlby``)."""
    return await _get(f"/concepts/{slug}")

async def list_articles(
    lang: str = "en",
    limit: int = 20,
    offset: int = 0,
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Paginated list of blog articles.

    The external API returns a JSON array – we return it directly.
    """
    params: Dict[str, Any] = {"lang": lang, "limit": limit, "offset": offset}
    if category:
        params["category"] = category
    data = await _get("/articles", params)
    return data.get("items", data)

async def get_article(slug: str, lang: str = "en") -> Dict[str, Any]:
    """Fetch a single article by slug and language."""
    params = {"lang": lang}
    return await _get(f"/articles/{slug}", params)

async def list_books(
    status: Optional[str] = None,
    topic: Optional[str] = None,
    series: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return the catalogue of books.

    ``status`` can be ``available`` or ``out-of-stock`` – the API does not
    enforce an enum, so we simply forward the value.
    """
    params: Dict[str, Any] = {}
    if status:
        params["status"] = status
    if topic:
        params["topic"] = topic
    if series:
        params["series"] = series
    data = await _get("/books", params)
    return data.get("items", data)

async def get_book(slug: str) -> Dict[str, Any]:
    """Fetch book details, including the direct PDF download URL."""
    return await _get(f"/books/{slug}")

def load_openapi_spec() -> Dict[str, Any]:
    """Load the previously downloaded OpenAPI JSON from the data folder.

    Returns the raw spec as a dict. Raises ``FileNotFoundError`` if the file
    does not exist.
    """
    spec_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "psychologie_openapi.json"
    )
    spec_path = os.path.abspath(spec_path)
    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)

# End of module
