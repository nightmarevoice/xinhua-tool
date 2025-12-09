from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit

import httpx
from fastapi import APIRouter, Request, Response
from starlette.responses import StreamingResponse

router = APIRouter()

TARGET_BASE = "https://www.alethea.ai/"

# Hop-by-hop headers that must not be forwarded
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def build_target_url(path: str, query_params: Dict[str, List[str]]) -> str:
    # Ensure we preserve query string
    query_tuples: List[Tuple[str, str]] = []
    for key, values in query_params.items():
        for v in values:
            query_tuples.append((key, v))
    query_str = urlencode(query_tuples, doseq=True)
    base_with_path = urljoin(TARGET_BASE, path)
    parts = list(urlsplit(base_with_path))
    parts[3] = query_str  # query
    return urlunsplit(parts)


def sanitize_outgoing_headers(headers: Dict[str, str]) -> Dict[str, str]:
    sanitized: Dict[str, str] = {}
    for k, v in headers.items():
        lk = k.lower()
        if lk in HOP_BY_HOP_HEADERS:
            continue
        # Do not forward Host; httpx will set it based on target
        if lk == "host":
            continue
        sanitized[k] = v
    return sanitized


def sanitize_incoming_headers(headers: Iterable[Tuple[bytes, bytes]]) -> List[Tuple[bytes, bytes]]:
    cleaned: List[Tuple[bytes, bytes]] = []
    for raw_k, raw_v in headers:
        k = raw_k.decode("latin-1")
        v = raw_v.decode("latin-1")
        lk = k.lower()
        # Strip frame blocking headers
        if lk in ("x-frame-options", "content-security-policy"):
            # Remove entirely; especially removes frame-ancestors restrictions
            continue
        if lk in HOP_BY_HOP_HEADERS:
            continue
        # Prevent downstream from caching potentially rewritten content
        if lk in ("etag",):
            continue
        # Rewrite cookie Domain to host-less so it sticks to our proxy host
        if lk == "set-cookie":
            # naive domain removal; keep rest of attributes
            cookie = v
            segments = []
            for seg in cookie.split(";"):
                if seg.strip().lower().startswith("domain="):
                    # skip Domain attribute
                    continue
                segments.append(seg)
            v = ";".join(segments)
        cleaned.append((k.encode("latin-1"), v.encode("latin-1")))
    return cleaned


def rewrite_location(location: Optional[str], request: Request) -> Optional[str]:
    if not location:
        return location
    # If redirect points back to target site, map it to our proxy path
    try:
        target_netloc = urlsplit(TARGET_BASE).netloc
        loc_parts = urlsplit(location)
        if loc_parts.netloc == "" and location.startswith("/"):
            # Absolute path on same host -> keep but under proxy prefix
            return request.url_for("proxy_root") + location.lstrip("/")
        if loc_parts.netloc == target_netloc:
            # Rewrite to our proxy base + path + query
            proxied_base = request.url_for("proxy_root")
            rebuilt = proxied_base + (loc_parts.path.lstrip("/"))
            if loc_parts.query:
                rebuilt += f"?{loc_parts.query}"
            return rebuilt
    except Exception:
        return location
    return location


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def proxy(request: Request, path: str):
    target_url = build_target_url(path, dict(request.query_params.multi_items()))

    # Prepare outgoing request
    outgoing_headers = sanitize_outgoing_headers(dict(request.headers))
    # Ensure we present as a normal browser to avoid bot blocks
    outgoing_headers.setdefault(
        "user-agent",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    )

    # Body (if any)
    body = await request.body()

    timeout = httpx.Timeout(20.0, read=40.0)
    async with httpx.AsyncClient(follow_redirects=False, timeout=timeout) as client:
        upstream_response = await client.request(
            request.method,
            target_url,
            content=body if body else None,
            headers=outgoing_headers,
        )

    # Rewrite headers
    response_headers = sanitize_incoming_headers(upstream_response.headers.raw)

    # Location header rewrite for redirects
    loc = upstream_response.headers.get("location")
    new_loc = rewrite_location(loc, request)
    if new_loc and new_loc != loc:
        # Replace or add header
        response_headers = [(k, v) for (k, v) in response_headers if k.decode("latin-1").lower() != "location"]
        response_headers.append((b"location", new_loc.encode("latin-1")))

    # Stream body
    async def iter_stream():
        async for chunk in upstream_response.aiter_raw():
            yield chunk

    return StreamingResponse(
        iter_stream(),
        status_code=upstream_response.status_code,
        headers=dict((k.decode("latin-1"), v.decode("latin-1")) for k, v in response_headers),
        media_type=upstream_response.headers.get("content-type"),
    )


@router.get("/", name="proxy_root")
async def proxy_root():
    # Simple endpoint to build base URL with url_for in rewrite_location
    return Response(status_code=204)




