"""Tiny Buffer GraphQL client (https://developers.buffer.com)."""
import json
import time

import requests

from common import auth_headers

API = "https://api.buffer.com"


class BufferError(RuntimeError):
    pass


def gql(query):
    headers = {"Content-Type": "application/json", **auth_headers("BUFFER_API_KEY")}
    for attempt in range(3):
        r = requests.post(API, headers=headers, json={"query": query}, timeout=60)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", "30"))
            time.sleep(min(wait, 120))
            continue
        break
    if r.status_code == 401 or r.status_code == 403:
        raise BufferError(
            f"Buffer refused the request ({r.status_code}). Check the Buffer network "
            "secret (host api.buffer.com, header Authorization, prefix Bearer)."
        )
    if r.status_code != 200:
        raise BufferError(f"Buffer returned {r.status_code}: {r.text[:400]}")
    data = r.json()
    if data.get("errors"):
        raise BufferError(json.dumps(data["errors"])[:800])
    return data["data"]


def s(value):
    """Quote a Python string as a GraphQL string literal."""
    return json.dumps(value or "", ensure_ascii=False)


def organizations():
    return gql("query { account { organizations { id name } } }")["account"]["organizations"]


def channels(org_id):
    q = (
        "query { channels(input: { organizationId: %s }) { id name service } }" % s(org_id)
    )
    return gql(q)["channels"]


def pinterest_boards(org_id, channel_id):
    q = (
        "query { channels(input: { organizationId: %s }) { id service "
        "metadata { ... on PinterestMetadata { boards { serviceId name } } } } }" % s(org_id)
    )
    for ch in gql(q)["channels"]:
        if ch["id"] == channel_id:
            return ((ch.get("metadata") or {}).get("boards")) or []
    return []


def find_pinterest(cfg):
    """Return (org_id, channel, board_service_id)."""
    orgs = organizations()
    if not orgs:
        raise BufferError("No Buffer organization found for this API key.")
    for org in orgs:
        for ch in channels(org["id"]):
            if (ch.get("service") or "").lower() != "pinterest":
                continue
            board_id = (cfg.get("pinterest_board_service_id") or "").strip()
            if not board_id:
                wanted = (cfg.get("pinterest_board_name") or "").strip().lower()
                try:
                    boards = pinterest_boards(org["id"], ch["id"])
                except BufferError as e:
                    raise BufferError(
                        "Could not list Pinterest boards automatically. Put the board's "
                        f"ID in config.json as pinterest_board_service_id. Details: {e}"
                    )
                match = [b for b in boards if b["name"].strip().lower() == wanted] or (
                    boards if len(boards) == 1 else []
                )
                if not match:
                    names = ", ".join(b["name"] for b in boards) or "(none found)"
                    raise BufferError(
                        f"No Pinterest board named '{cfg.get('pinterest_board_name')}'. "
                        f"Boards on this channel: {names}. Fix pinterest_board_name in config.json."
                    )
                board_id = match[0]["serviceId"]
            return org["id"], ch, board_id
    raise BufferError("No Pinterest channel is connected in Buffer. Connect Pinterest first.")


def create_pin(channel_id, board_id, text, title, link, image_url):
    q = """mutation {
  createPost(input: {
    text: %s,
    channelId: %s,
    schedulingType: automatic,
    mode: addToQueue,
    assets: [{ image: { url: %s } }],
    metadata: { pinterest: { boardServiceId: %s, title: %s, url: %s } }
  }) {
    ... on PostActionSuccess { post { id dueAt } }
    ... on MutationError { message }
  }
}""" % (s(text), s(channel_id), s(image_url), s(board_id), s(title), s(link))
    res = gql(q)["createPost"]
    if "message" in res and not res.get("post"):
        raise BufferError(res["message"])
    return res["post"]
