from fastapi import APIRouter, Request, Response
from starlette.responses import StreamingResponse, PlainTextResponse
import httpx
import re
from typing import Dict, Iterable

router = APIRouter()

UPSTREAM_ORIGIN = "https://www.alethea.ai"

HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

ATTRIBUTE_URL_PATTERN = re.compile(
    r'(?P<attr>\b(?:src|href|action)\b)\s*=\s*([\'"])(?P<url>[^\'"]+)\2',
    flags=re.IGNORECASE,
)

CSS_URL_PATTERN = re.compile(
    r'url\(\s*([\'"]?)(?P<url>[^)\'"]+)\1\s*\)',
    flags=re.IGNORECASE,
)


def _to_proxy_url(original_url: str) -> str:
    if original_url.startswith("data:") or original_url.startswith("mailto:") or original_url.startswith("tel:"):
        return original_url
    if original_url.startswith("http://") or original_url.startswith("https://"):
        if original_url.startswith(UPSTREAM_ORIGIN):
            path = original_url[len(UPSTREAM_ORIGIN):]
            if not path.startswith("/"):
                path = "/" + path
            return f"/proxy/alethea{path}"
        return original_url
    if original_url.startswith("//"):
        # protocol-relative to absolute https
        absolute = "https:" + original_url
        if absolute.startswith(UPSTREAM_ORIGIN):
            path = absolute[len(UPSTREAM_ORIGIN):]
            if not path.startswith("/"):
                path = "/" + path
            return f"/proxy/alethea{path}"
        return original_url
    if original_url.startswith("/"):
        return f"/proxy/alethea{original_url}"
    # relative path
    return original_url


def _rewrite_html(content: str) -> str:
    def replace_attr(match: re.Match) -> str:
        attr = match.group("attr")
        url = match.group("url")
        return f'{attr}="{_to_proxy_url(url)}"'

    content = ATTRIBUTE_URL_PATTERN.sub(replace_attr, content)
    # rewrite CSS url()
    def replace_css(match: re.Match) -> str:
        url = match.group("url").strip()
        new_url = _to_proxy_url(url)
        quote = "'" if "'" in match.group(0) else ('"' if '"' in match.group(0) else '')
        if quote:
            return f"url({quote}{new_url}{quote})"
        return f"url({new_url})"

    content = CSS_URL_PATTERN.sub(replace_css, content)
    return content


def _filter_request_headers(headers: Dict[str, str]) -> Dict[str, str]:
    filtered: Dict[str, str] = {}
    for key, value in headers.items():
        lk = key.lower()
        if lk in HOP_BY_HOP_HEADERS:
            continue
        if lk == "host":
            continue
        # strip origin/referer to upstream
        if lk in ("origin", "referer"):
            continue
        filtered[key] = value
    filtered["Accept-Encoding"] = "identity"
    return filtered


def _filter_response_headers(headers: Iterable[tuple]) -> Dict[str, str]:
    new_headers: Dict[str, str] = {}
    for key, value in headers:
        lk = key.lower()
        if lk in HOP_BY_HOP_HEADERS:
            continue
        if lk in ("content-security-policy", "x-frame-options", "frame-options"):
            continue
        if lk == "location" and value.startswith(UPSTREAM_ORIGIN):
            new_headers[key] = value.replace(UPSTREAM_ORIGIN, "/proxy/alethea")
            continue
        new_headers[key] = value
    # permit embedding ourselves
    new_headers["X-Frame-Options"] = "ALLOWALL"
    new_headers["Content-Security-Policy"] = "frame-ancestors *; upgrade-insecure-requests"
    return new_headers


@router.api_route("/alethea/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def proxy_alethea(request: Request, full_path: str) -> Response:
    upstream_url = f"{UPSTREAM_ORIGIN}/{full_path}".rstrip("/")
    if request.url.query:
        upstream_url += f"?{request.url.query}"

    method = request.method.upper()
    body = await request.body()
    headers = _filter_request_headers(dict(request.headers))

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        upstream_response = await client.request(method, upstream_url, headers=headers, content=body)

    content_type = upstream_response.headers.get("content-type", "")
    proxied_headers = _filter_response_headers(upstream_response.headers.multi_items())

    # For HTML/text, rewrite links; for others, stream raw bytes
    if "text/html" in content_type or "text/" in content_type:
        text = upstream_response.text
        rewritten = _rewrite_html(text)
        return Response(
            content=rewritten,
            status_code=upstream_response.status_code,
            headers=proxied_headers,
            media_type=content_type.split(";")[0] if content_type else "text/html",
        )

    # For binary and other content types, stream bytes
    return Response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=proxied_headers,
        media_type=content_type.split(";")[0] if content_type else None,
    )




