"""Image proxy endpoints to bypass hotlink/CORS restrictions."""
import httpx
from fastapi import APIRouter, HTTPException, Response

BASE_IMAGE_URL = "https://encheres-domaine.gouv.fr/admin/media/catalog/product/"
TIMEOUT_SECONDS = 15

router = APIRouter()


def build_remote_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{BASE_IMAGE_URL}{path.lstrip('/')}"


@router.get("/{path:path}")
async def proxy_image(path: str):
    """Stream an image from the official domain through the API to avoid hotlink blocking."""
    url = build_remote_url(path)

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, follow_redirects=True, verify=False) as client:
        try:
            upstream = await client.get(url)
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Image fetch failed: {exc}") from exc

    if upstream.status_code >= 400:
        raise HTTPException(status_code=upstream.status_code, detail="Image unavailable")

    content_type = upstream.headers.get("content-type", "image/jpeg")
    cache_control = upstream.headers.get("cache-control", "public, max-age=86400")

    return Response(
        content=upstream.content,
        media_type=content_type,
        headers={"Cache-Control": cache_control}
    )
