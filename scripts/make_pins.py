"""Make pin images from a plan file.

For each pin in the plan: generate a background photo with Flux on Cloudflare
Workers AI, then lay the headline and branding over it (1000 x 1500 px).

Usage:
  python scripts/make_pins.py plan.json            # normal run
  python scripts/make_pins.py plan.json --offline  # skip Flux, use a soft gradient
"""
import argparse
import base64
import io
import json
import os
import random
import re
import sys
from datetime import date
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from common import ROOT, auth_headers, load_config

W, H = 1000, 1500
FONTS = ROOT / "fonts"
FLUX_MODEL = "@cf/black-forest-labs/flux-1-schnell"
PROMPT_SUFFIX = (
    ", vertical composition, soft natural light, calm and airy, high quality "
    "lifestyle photography, no text, no letters, no words, no watermark, no logo"
)


# ---------- fonts ----------
def serif(size, italic=False, weight="SemiBold"):
    path = FONTS / ("Lora-Italic-Variable.ttf" if italic else "Lora-Variable.ttf")
    f = ImageFont.truetype(str(path), size)
    name = f"{weight} Italic" if italic else weight
    try:
        f.set_variation_by_name(name)
    except Exception:
        pass
    return f


def sans(size, weight="Regular"):
    return ImageFont.truetype(str(FONTS / f"Inter-{weight}.otf"), size)


def hex_rgb(h, alpha=None):
    h = h.lstrip("#")
    rgb = tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
    return rgb + (alpha,) if alpha is not None else rgb


# ---------- background ----------
def flux_background(prompt, seed):
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    if not account:
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID is not set")
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{FLUX_MODEL}"
    r = requests.post(
        url,
        headers=auth_headers("CLOUDFLARE_API_TOKEN"),
        json={"prompt": (prompt + PROMPT_SUFFIX)[:2048], "steps": 6, "seed": seed},
        timeout=120,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Cloudflare returned {r.status_code}: {r.text[:300]}")
    data = r.json()
    b64 = (data.get("result") or {}).get("image") or data.get("image")
    if not b64:
        raise RuntimeError(f"No image in Cloudflare response: {str(data)[:300]}")
    return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")


def gradient_background(cfg, seed):
    rnd = random.Random(seed)
    c = cfg["colors"]
    img = Image.new("RGB", (W, H), hex_rgb(c["cream"]))
    d = ImageDraw.Draw(img)
    for col in (c["sage"], c["sand"], c["sage"]):
        r = rnd.randint(300, 600)
        x, y = rnd.randint(-100, W + 100), rnd.randint(-100, H + 100)
        d.ellipse([x - r, y - r, x + r, y + r], fill=hex_rgb(col))
    return img.filter(ImageFilter.GaussianBlur(160))


def cover(img, w, h):
    """Scale and centre-crop img to exactly w x h."""
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale) + 1, round(img.height * scale) + 1), Image.LANCZOS)
    left = (img.width - w) // 2
    top = (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


# ---------- text layout ----------
def text_w(draw, s, font):
    return draw.textlength(s, font=font)


def wrap_words(draw, words, fonts_for, max_w):
    """words: list of (word, is_highlight). Returns lines as lists of the same."""
    lines, cur, cur_w = [], [], 0
    for word, hl in words:
        f = fonts_for(hl)
        ww = text_w(draw, word, f)
        sp = text_w(draw, " ", f)
        if cur and cur_w + sp + ww > max_w:
            lines.append(cur)
            cur, cur_w = [], 0
        cur_w += (sp if cur else 0) + ww
        cur.append((word, hl))
    if cur:
        lines.append(cur)
    return lines


def headline_words(headline, highlight):
    hl = (highlight or "").strip().lower()
    words = headline.split()
    return [(w, bool(hl) and re.sub(r"\W", "", w.lower()) == re.sub(r"\W", "", hl)) for w in words]


def fit_headline(draw, headline, highlight, max_w, max_lines, start, minimum):
    words = headline_words(headline, highlight)
    size = start
    while True:
        reg, ita = serif(size), serif(size, italic=True)
        lines = wrap_words(draw, words, lambda h: ita if h else reg, max_w)
        if len(lines) <= max_lines or size <= minimum:
            return size, reg, ita, lines
        size -= 4


def draw_headline(draw, lines, reg, ita, x, y, line_h, color, hl_color, align="left", width=None):
    for line in lines:
        widths = [text_w(draw, w, ita if h else reg) for w, h in line]
        space = text_w(draw, " ", reg)
        total = sum(widths) + space * (len(line) - 1)
        cx = x + (width - total) / 2 if align == "center" else x
        for (w, h), ww in zip(line, widths):
            draw.text((cx, y), w, font=ita if h else reg, fill=hl_color if h else color)
            cx += ww + space
        y += line_h
    return y


def wrap_plain(draw, text, font, max_w, max_lines):
    words = [(w, False) for w in (text or "").split()]
    lines = [" ".join(w for w, _ in l) for l in wrap_words(draw, words, lambda h: font, max_w)]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .,;:") + "…"
    return lines


def draw_spaced(draw, xy, text, font, fill, spacing):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += text_w(draw, ch, font) + spacing
    return x


def spaced_width(draw, text, font, spacing):
    return sum(text_w(draw, ch, font) + spacing for ch in text) - spacing


# ---------- templates ----------
def template_photo_top(bg, pin, cfg):
    c = cfg["colors"]
    img = Image.new("RGB", (W, H), hex_rgb(c["cream"]))
    img.paste(cover(bg, W, 880), (0, 0))
    d = ImageDraw.Draw(img)
    panel_top = 820
    d.rounded_rectangle([0, panel_top, W, H + 60], radius=56, fill=hex_rgb(c["cream"]))

    pad = 80
    y = panel_top + 62
    kicker = (pin.get("kicker") or "").upper()
    if kicker:
        draw_spaced(d, (pad, y), kicker, sans(24, "SemiBold"), hex_rgb(c["sage"]), 4.5)
        y += 54

    footer_y = H - 92
    sub_font = sans(30)
    sub_lines = wrap_plain(d, pin.get("subline"), sub_font, W - 2 * pad, 2)
    sub_h = len(sub_lines) * 42 + (26 if sub_lines else 0)
    avail = footer_y - 40 - y - sub_h

    size, reg, ita, lines = fit_headline(d, pin["headline"], pin.get("highlight"), W - 2 * pad, 4, 84, 48)
    while len(lines) * size * 1.12 > avail and size > 44:
        size, reg, ita, lines = fit_headline(d, pin["headline"], pin.get("highlight"), W - 2 * pad, 4, size - 4, 44)
    y = draw_headline(d, lines, reg, ita, pad, y, size * 1.12, hex_rgb(c["ink"]), hex_rgb(c["sage"]))

    if sub_lines:
        y += 22
        for line in sub_lines:
            d.text((pad, y), line, font=sub_font, fill=(74, 88, 80))
            y += 42

    d.text((pad, footer_y), cfg["brand_name"], font=serif(34), fill=hex_rgb(c["ink"]))
    url_font = sans(25, "SemiBold")
    url = cfg["brand_url_text"]
    d.text((W - pad - text_w(d, url, url_font), footer_y + 6), url, font=url_font, fill=hex_rgb(c["sage"]))
    return img


def template_photo_full(bg, pin, cfg):
    c = cfg["colors"]
    img = cover(bg, W, H).convert("RGBA")
    forest = hex_rgb(c["forest"])
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    start = 460
    for yy in range(start, H):
        t = (yy - start) / (H - start)
        a = int(235 * min(1, t * 1.35) ** 1.2)
        gd.line([(0, yy), (W, yy)], fill=forest + (a,))
    img = Image.alpha_composite(img, grad).convert("RGB")
    d = ImageDraw.Draw(img)

    pad = 80
    cream, sand = hex_rgb(c["cream"]), hex_rgb(c["sand"])
    kicker = (pin.get("kicker") or "").upper()
    kfont = sans(24, "SemiBold")
    size, reg, ita, lines = fit_headline(d, pin["headline"], pin.get("highlight"), W - 2 * pad, 4, 88, 52)
    sub_font = sans(30)
    sub_lines = wrap_plain(d, pin.get("subline"), sub_font, W - 2 * pad, 2)
    cta = pin.get("cta") or "Read the full guide →"
    cfont = sans(28, "Bold")

    # Measure from the bottom up.
    brand_h, cta_h = 40, 78
    block = (54 if kicker else 0) + len(lines) * size * 1.1 + (30 + len(sub_lines) * 42 if sub_lines else 0) + 44 + cta_h + 36 + brand_h
    y = H - 80 - block

    if kicker:
        kw = spaced_width(d, kicker, kfont, 4.5)
        draw_spaced(d, ((W - kw) / 2, y), kicker, kfont, sand, 4.5)
        y += 54
    y = draw_headline(d, lines, reg, ita, pad, y, size * 1.1, cream, sand, align="center", width=W - 2 * pad)
    if sub_lines:
        y += 30
        for line in sub_lines:
            d.text(((W - text_w(d, line, sub_font)) / 2, y), line, font=sub_font, fill=(214, 224, 210))
            y += 42
    y += 44
    cw = text_w(d, cta, cfont) + 88
    d.rounded_rectangle([(W - cw) / 2, y, (W + cw) / 2, y + cta_h], radius=cta_h / 2, fill=sand)
    d.text(((W - text_w(d, cta, cfont)) / 2, y + 22), cta, font=cfont, fill=forest)
    y += cta_h + 36
    bfont = serif(32, weight="Regular")
    d.text(((W - text_w(d, cfg["brand_name"], bfont)) / 2, y), cfg["brand_name"], font=bfont, fill=cream)
    return img


TEMPLATES = {"photo-top": template_photo_top, "photo-full": template_photo_full}


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:50] or "pin"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--offline", action="store_true", help="skip Flux and use a gradient background")
    args = ap.parse_args()

    cfg = load_config()
    plan_path = Path(args.plan)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    day = plan.get("date") or date.today().isoformat()
    out_dir = ROOT / "pins" / day
    out_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for i, pin in enumerate(plan["pins"], 1):
        seed = random.randint(1, 2_000_000_000)
        try:
            if args.offline:
                raise RuntimeError("offline mode")
            bg = flux_background(pin["image_prompt"], seed)
            pin["background"] = "flux"
        except Exception as e:
            print(f"[pin {i}] Flux background failed, using gradient instead: {e}", file=sys.stderr)
            bg = gradient_background(cfg, seed)
            pin["background"] = "gradient"
            failures += 0 if args.offline else 1
        tpl = TEMPLATES.get(pin.get("template"), template_photo_top)
        img = tpl(bg, pin, cfg)
        name = f"{i:02d}-{slugify(pin['headline'])}.jpg"
        path = out_dir / name
        img.save(path, "JPEG", quality=90, optimize=True)
        pin["image_path"] = str(path.relative_to(ROOT)).replace(os.sep, "/")
        print(f"[pin {i}] saved {pin['image_path']} ({pin['background']})")

    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    if failures:
        print(f"WARNING: {failures} pin(s) used the gradient fallback because Flux failed.", file=sys.stderr)


if __name__ == "__main__":
    main()
