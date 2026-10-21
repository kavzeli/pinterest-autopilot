"""Print the newest articles that still need pins, as JSON.

Usage: python scripts/get_articles.py [--count 10]
"""
import argparse
import html
import json
import re
import sys

import requests

from common import load_config, load_posted


def clean(text):
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=10)
    args = ap.parse_args()

    cfg = load_config()
    url = cfg["site_url"].rstrip("/") + "/wp-json/wp/v2/posts"
    r = requests.get(
        url,
        params={"per_page": args.count, "_fields": "id,link,title,date,excerpt,content"},
        timeout=30,
        headers={"User-Agent": "pinterest-autopilot/1.0"},
    )
    if r.status_code != 200:
        sys.exit(f"Could not read articles ({r.status_code}) from {url}: {r.text[:300]}")

    posted = load_posted()
    max_per = int(cfg.get("max_pins_per_article", 2))
    out = []
    for p in r.json():
        link = p["link"]
        previous = [x for x in posted if x.get("article_url") == link]
        if len(previous) >= max_per:
            continue
        out.append(
            {
                "article_url": link,
                "title": clean(p["title"]["rendered"]),
                "date": p["date"],
                "pins_already_made": len(previous),
                "previous_headlines": [x.get("headline") for x in previous],
                "excerpt": clean(p.get("excerpt", {}).get("rendered"))[:400],
                "content_preview": clean(p.get("content", {}).get("rendered"))[:2500],
            }
        )
    # Articles never pinned first, then newest first.
    out.sort(key=lambda a: (a["pins_already_made"], -int(re.sub(r"\D", "", a["date"])[:12] or 0)))
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
