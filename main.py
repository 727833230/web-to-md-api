"""Web-to-Markdown API — 网页内容提取并转为结构化 Markdown"""

import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Tuple
from pydantic import BaseModel
import trafilatura

app = FastAPI(title="Web-to-Markdown API", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

USER_AGENT = (
    "Mozilla/5.0 (compatible; WebToMarkdown/1.0; +web-to-md-api)"
)
TIMEOUT = 30.0


class Options(BaseModel):
    include_links: bool = True
    include_images: bool = False
    include_tables: bool = True


class ConvertRequest(BaseModel):
    url: str
    options: Options = Options()


async def _fetch(url: str) -> Tuple[str, str]:
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
        ct = resp.headers.get("content-type", "").lower()
        return resp.text, ct


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/convert")
async def convert(req: ConvertRequest):
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(400, "URL must start with http:// or https://")

    # Fetch page
    try:
        html, content_type = await _fetch(url)
    except httpx.TimeoutException:
        raise HTTPException(504, "URL fetch timed out")
    except httpx.HTTPStatusError as e:
        raise HTTPException(502, f"URL returned HTTP {e.response.status_code}")
    except Exception as e:
        raise HTTPException(502, f"Failed to fetch URL: {e}")

    # Only HTML content is supported
    if not content_type.startswith("text/html"):
        return {
            "url": url,
            "title": None,
            "markdown": "",
            "metadata": {},
            "word_count": 0,
            "note": f"Not an HTML page: {content_type}",
            "status": "skipped",
        }

    opts = req.options

    # Extract metadata (title, description, author, date, site_name)
    doc = trafilatura.bare_extraction(
        html,
        url=url,
        favor_recall=True,
        include_links=opts.include_links,
        include_images=opts.include_images,
        include_tables=opts.include_tables,
    )

    # Extract main content as Markdown
    md = trafilatura.extract(
        html,
        output_format="markdown",
        url=url,
        favor_recall=True,
        include_links=opts.include_links,
        include_images=opts.include_images,
        include_tables=opts.include_tables,
    )

    if not md:
        return {
            "url": url,
            "title": getattr(doc, "title", None) if doc else None,
            "markdown": "",
            "metadata": _pick_meta(doc),
            "word_count": 0,
            "note": "No extractable content found",
            "status": "empty",
        }

    return {
        "url": url,
        "title": getattr(doc, "title", None) if doc else None,
        "markdown": md,
        "metadata": _pick_meta(doc),
        "word_count": len(md.split()),
        "status": "ok",
    }


def _pick_meta(doc) -> dict:
    if doc is None:
        return {}
    d = doc.as_dict() if hasattr(doc, "as_dict") else {}
    return {k: d[k] for k in ("description", "author", "date", "sitename") if d.get(k)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
