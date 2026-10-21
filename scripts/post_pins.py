"""Add the pins in a plan to your Buffer queue (Buffer posts them to Pinterest).

Run this only AFTER the pin images are committed and pushed to GitHub, because
Buffer downloads each image from its public GitHub link.

Usage:
  python scripts/post_pins.py plan.json [--branch main] [--dry-run]
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

import buffer_api
from common import load_config, load_posted, raw_url, save_posted


def wait_until_public(url, timeout=240):
    """GitHub can take a minute to serve a newly pushed file."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.head(url, timeout=20, allow_redirects=True)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(10)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    pins = plan["pins"]

    if args.dry_run:
        for p in pins:
            print(json.dumps({k: p.get(k) for k in ("pin_title", "article_url", "image_path")}, ensure_ascii=False))
            print("  image link:", raw_url(cfg, p["image_path"], args.branch))
        return

    _, channel, board_id = buffer_api.find_pinterest(cfg)
    print(f"Posting to Buffer channel '{channel['name']}' (board {board_id})")

    posted = load_posted()
    ok, failed = 0, 0
    for i, p in enumerate(pins, 1):
        img = raw_url(cfg, p["image_path"], args.branch)
        if not wait_until_public(img):
            print(f"[pin {i}] FAILED: image is not public yet: {img}", file=sys.stderr)
            failed += 1
            continue
        try:
            post = buffer_api.create_pin(
                channel_id=channel["id"],
                board_id=board_id,
                text=p["description"][:500],
                title=p["pin_title"][:100],
                link=p["article_url"],
                image_url=img,
            )
        except buffer_api.BufferError as e:
            print(f"[pin {i}] FAILED: {e}", file=sys.stderr)
            failed += 1
            continue
        ok += 1
        print(f"[pin {i}] queued in Buffer, scheduled for {post.get('dueAt')}")
        posted.append(
            {
                "date": plan.get("date"),
                "article_url": p["article_url"],
                "headline": p["headline"],
                "pin_title": p["pin_title"],
                "image_url": img,
                "buffer_post_id": post.get("id"),
                "due_at": post.get("dueAt"),
                "queued_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        )
        save_posted(posted)  # save after each pin so a crash never double-posts

    print(f"Done: {ok} queued, {failed} failed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
