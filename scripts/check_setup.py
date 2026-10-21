"""Check that every account is connected. Prints PASS / FAIL for each part.

Usage: python scripts/check_setup.py
"""
import os
import sys

import requests

import buffer_api
from common import auth_headers, github_repo, load_config

results = []


def check(name, fn):
    try:
        detail = fn()
        results.append(True)
        print(f"PASS  {name}: {detail}")
    except Exception as e:
        results.append(False)
        print(f"FAIL  {name}: {e}")


cfg = load_config()


def site():
    r = requests.get(cfg["site_url"].rstrip("/") + "/wp-json/wp/v2/posts",
                     params={"per_page": 1, "_fields": "link"}, timeout=30)
    r.raise_for_status()
    return f"newest article {r.json()[0]['link']}"


def github():
    return github_repo(cfg)


def cloudflare():
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    if not account:
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID environment variable is missing")
    r = requests.get(
        f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/models/search",
        params={"search": "flux-1-schnell", "per_page": 1},
        headers=auth_headers("CLOUDFLARE_API_TOKEN"), timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Workers AI returned {r.status_code}: {r.text[:200]}")
    return "Workers AI is reachable and the token works"


def buffer():
    org, ch, board = buffer_api.find_pinterest(cfg)
    return f"Pinterest channel '{ch['name']}', board id {board}"


check("Website", site)
check("GitHub repo setting", github)
check("Cloudflare", cloudflare)
check("Buffer + Pinterest", buffer)
print()
print("All good!" if all(results) else "Fix the FAIL lines above, then run this again.")
sys.exit(0 if all(results) else 1)
