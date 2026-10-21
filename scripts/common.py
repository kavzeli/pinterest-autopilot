"""Shared helpers: config, posted log, HTTP auth headers."""
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"
POSTED_PATH = ROOT / "data" / "posted.json"


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_posted():
    if POSTED_PATH.exists():
        with open(POSTED_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_posted(items):
    POSTED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(POSTED_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)


def auth_headers(env_name):
    """Add a Bearer header only if the key is in an environment variable.

    In a Claude Code cloud environment you store the key as a *network secret*
    instead, and the proxy adds the header for you, so nothing is needed here.
    """
    key = os.environ.get(env_name, "").strip()
    return {"Authorization": f"Bearer {key}"} if key else {}


def github_repo(cfg):
    repo = (cfg.get("github_repo") or "").strip()
    if repo and "YOUR-GITHUB-USERNAME" not in repo:
        return repo
    try:
        url = subprocess.check_output(
            ["git", "-C", str(ROOT), "remote", "get-url", "origin"], text=True
        ).strip()
        m = re.search(r"([^/:]+)/([^/]+?)(?:\.git)?$", url)
        if m:
            return f"{m.group(1)}/{m.group(2)}"
    except Exception:
        pass
    raise SystemExit(
        "Set \"github_repo\" in config.json to your-username/your-repo-name."
    )


def raw_url(cfg, rel_path, branch="main"):
    return (
        f"https://raw.githubusercontent.com/{github_repo(cfg)}/refs/heads/"
        f"{branch}/{rel_path}"
    )
