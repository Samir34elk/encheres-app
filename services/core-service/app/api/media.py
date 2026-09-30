"""Image proxy endpoints to bypass hotlink/CORS restrictions with local caching."""
import asyncio
import time
import httpx
from pathlib import Path
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse

BASE_IMAGE_URL = "https://encheres-domaine.gouv.fr/admin/media/catalog/product/"
TIMEOUT_SECONDS = 15
CACHE_DIR = Path("/app/media/images")

# Create cache directory if it doesn't exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Anti-blocage : même IP que le scraper, donc on limite les téléchargements
# simultanés vers le site et on ne redemande pas en boucle une image absente.
MAX_CONCURRENT_DOWNLOADS = 2
MISSING_TTL_SECONDS = 6 * 3600
_download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
_missing_until: dict[str, float] = {}

router = APIRouter()


def build_remote_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path

    # Clean duplicate path segments (scraper sometimes duplicates the base path)
    clean_path = path.lstrip('/')
    duplicate_prefix = "admin/media/catalog/product/"
    if clean_path.startswith(duplicate_prefix):
        clean_path = clean_path[len(duplicate_prefix):]

    return f"{BASE_IMAGE_URL}{clean_path}"


@router.get("/{path:path}")
async def proxy_image(path: str):
    """
    Serve image with local caching using original path structure.
    1. Check if image exists locally -> serve it directly (fast)
    2. If not, download from source, save locally, then serve
    """
    url = build_remote_url(path)

    # Clean path for local storage (preserve original structure)
    clean_path = path.lstrip('/')
    duplicate_prefix = "admin/media/catalog/product/"
    if clean_path.startswith(duplicate_prefix):
        clean_path = clean_path[len(duplicate_prefix):]

    # Use original path structure for caching
    cache_path = CACHE_DIR / clean_path

    # Serve from cache if exists
    if cache_path.exists():
        return FileResponse(
            cache_path,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=31536000"}
        )

    if _missing_until.get(url, 0) > time.monotonic():
        raise HTTPException(status_code=404, detail="Image unavailable")

    # Download and cache
    async with _download_semaphore:
        # Une autre requête a pu télécharger l'image pendant l'attente.
        if cache_path.exists():
            return FileResponse(
                cache_path,
                media_type="image/jpeg",
                headers={"Cache-Control": "public, max-age=31536000"}
            )
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
            try:
                upstream = await client.get(url)
            except httpx.RequestError as exc:
                raise HTTPException(status_code=502, detail=f"Image fetch failed: {exc}") from exc

    if upstream.status_code in (403, 429):
        # Ne pas propager un blocage au navigateur comme une erreur définitive.
        raise HTTPException(status_code=503, detail="Image temporarily unavailable")
    if upstream.status_code >= 400:
        _missing_until[url] = time.monotonic() + MISSING_TTL_SECONDS
        raise HTTPException(status_code=upstream.status_code, detail="Image unavailable")

    # Save to cache with original path structure
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'wb') as f:
            f.write(upstream.content)
        print(f"✓ Cached image: {cache_path}")
    except Exception as e:
        print(f"✗ Failed to cache image: {e}")
        # Continue even if caching fails
        pass

    content_type = upstream.headers.get("content-type", "image/jpeg")

    return Response(
        content=upstream.content,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=31536000"}
    )
