#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path("/Users/rainy/Code/Museum/Museum")
DATA_PATH = ROOT / "backend/api/data/official_content.json"
STATIC_ROOT = ROOT / "backend/static/official"

BASE = "https://en.gmfyg.org.cn/"

EXHIBITION_PAGES = [
    ("permanent", "https://en.gmfyg.org.cn/permanentexhibitions.html", 4),
    ("special", "https://en.gmfyg.org.cn/specialexhibitions.html", 6),
    ("previous", "https://en.gmfyg.org.cn/previousexhibitions.html", 5),
]

EVENT_PAGE = ("events", "https://en.gmfyg.org.cn/eventsandactivities.html", 6)

COLLECTION_PAGES = [
    ("jade", "Jade Sculpture", "https://en.gmfyg.org.cn/jadesculpture.html", 10),
    ("ceramics", "Ceramics", "https://en.gmfyg.org.cn/ceramics.html", 10),
    ("metal", "Metal Crafts", "https://en.gmfyg.org.cn/metalcrafts.html", 10),
    ("textile", "Textile and Embroidery", "https://en.gmfyg.org.cn/textileandembroidery.html", 10),
    ("lacquer", "Lacquerware and Lacquer Artistry", "https://en.gmfyg.org.cn/lacquerwareandlacquerartistry.html", 10),
]


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def clean(text: str) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return " ".join(text.split())


def resolve(url: str) -> str:
    return urllib.parse.urljoin(BASE, url)


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return text or "item"


def download_image(kind: str, slug: str, url: str) -> str:
    ext = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".jpg"
    folder = STATIC_ROOT / kind
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{slug}{ext}"
    path = folder / filename
    if not path.exists():
        urllib.request.urlretrieve(url, path)
    return f"/static/official/{kind}/{filename}"


def parse_listing_items(page_html: str, with_meta: bool = True) -> list[dict]:
    if with_meta:
        pattern = re.compile(
            r'<li[^>]*>\s*<span><a href="(?P<link>[^"]+)"><img src="(?P<img>[^"]+)" alt="(?P<alt>[^"]*)"[^>]*></a></span>\s*'
            r'<dl[^>]*>\s*<dt><a href="[^"]+">(?P<title>.*?)</a></dt>\s*<b>(?P<date>.*?)</b>\s*<dd>(?P<location>.*?)</dd>',
            re.S,
        )
    else:
        pattern = re.compile(
            r'<li[^>]*>\s*<span><a href="(?P<link>[^"]+)"><img src="(?P<img>[^"]+)" alt="(?P<alt>[^"]*)"[^>]*></a></span>\s*'
            r'<dl[^>]*>\s*<dt><a href="[^"]+">(?P<title>.*?)</a></dt>',
            re.S,
        )

    items = []
    for match in pattern.finditer(page_html):
        data = {key: clean(value) for key, value in match.groupdict(default="").items()}
        items.append(data)
    return items


def parse_detail(url: str) -> dict:
    html_text = fetch(url)
    title_match = re.search(r"<title>\s*(.*?)\s*</title>", html_text, re.S)
    subtitle_match = re.search(r"<subtitle>(.*?)</subtitle>", html_text, re.S)
    body_match = re.search(r"<!--enpcontent-->(.*?)<!--/enpcontent-->", html_text, re.S)
    image_match = re.search(r'<!--enpcontent-->.*?<img[^>]+src="([^"]+)"', html_text, re.S)

    paragraphs = []
    if body_match:
        paragraphs = [clean(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", body_match.group(1), re.S)]
        paragraphs = [p for p in paragraphs if p]

    return {
        "title": clean(title_match.group(1)) if title_match else "",
        "subtitle": clean(subtitle_match.group(1)) if subtitle_match else "",
        "body": "\n".join(paragraphs),
        "image": resolve(image_match.group(1)) if image_match else "",
    }


def scrape_exhibitions() -> list[dict]:
    results = []
    for category, url, limit in EXHIBITION_PAGES:
        items = parse_listing_items(fetch(url), with_meta=True)[:limit]
        for item in items:
            detail_url = resolve(item["link"])
            detail = parse_detail(detail_url)
            slug = slugify(detail["title"] or item["title"])
            image_url = detail["image"] or resolve(item["img"])
            results.append(
                {
                    "source_url": detail_url,
                    "category": category,
                    "title": detail["title"] or item["title"],
                    "date_range": item["date"],
                    "location": item["location"],
                    "summary": (detail["body"] or item["alt"]).strip(),
                    "image_url": image_url,
                    "image_local": download_image("exhibitions", slug, image_url),
                }
            )
    return results


def scrape_events() -> list[dict]:
    category, url, limit = EVENT_PAGE
    items = parse_listing_items(fetch(url), with_meta=False)[:limit]
    results = []
    for item in items:
        detail_url = resolve(item["link"])
        detail = parse_detail(detail_url)
        slug = slugify(detail["title"] or item["title"])
        image_url = detail["image"] or resolve(item["img"])
        body = detail["body"]
        results.append(
            {
                "source_url": detail_url,
                "category": category,
                "title": detail["title"] or item["title"],
                "summary": body.strip(),
                "image_url": image_url,
                "image_local": download_image("activities", slug, image_url),
            }
        )
    return results


def scrape_collections() -> list[dict]:
    results = []
    for key, category_name, url, limit in COLLECTION_PAGES:
        items = parse_listing_items(fetch(url), with_meta=False)[:limit]
        for item in items:
            detail_url = resolve(item["link"])
            detail = parse_detail(detail_url)
            slug = slugify(detail["title"] or item["title"])
            image_url = detail["image"] or resolve(item["img"])
            results.append(
                {
                    "source_url": detail_url,
                    "category_key": key,
                    "category_name": detail["subtitle"] or category_name,
                    "title": detail["title"] or item["title"],
                    "summary": detail["subtitle"] or category_name,
                    "image_url": image_url,
                    "image_local": download_image("collections", slug, image_url),
                }
            )
    return results


def main() -> int:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATIC_ROOT.mkdir(parents=True, exist_ok=True)

    payload = {
      "source": "https://en.gmfyg.org.cn/",
      "exhibitions": scrape_exhibitions(),
      "activities": scrape_events(),
      "collections": scrape_collections(),
    }
    DATA_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(f"Wrote {DATA_PATH}")
    print(f"Exhibitions: {len(payload['exhibitions'])}")
    print(f"Activities: {len(payload['activities'])}")
    print(f"Collections: {len(payload['collections'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
