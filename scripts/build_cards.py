#!/usr/bin/env python3
"""Build minimalist poker cards and duplex-ready SVG print sheets."""
from __future__ import annotations

import base64
import html
import json
import re
from pathlib import Path
from textwrap import wrap

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "game/game.json").read_text())
OUT = ROOT / "dist/cards"
SHEETS = ROOT / "dist/print-sheets"
BACKS = ROOT / "dist/card-backs"

PALETTE = {
    "scenario": ("#e8e3d8", "#272722", "#8b2f2b"),
    "command": ("#202522", "#eee8d8", "#ad8c4b"),
    "crisis": ("#2a2422", "#eee8d8", "#9f493d"),
}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def text_lines(text: str, width: int, limit: int) -> list[str]:
    return wrap(text, width=width, break_long_words=False)[:limit]


def tspans(lines: list[str], x: int, gap: int) -> str:
    return "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else gap}">{html.escape(line)}</tspan>'
        for i, line in enumerate(lines)
    )


def card_svg(kind: str, card: dict) -> str:
    bg, ink, accent = PALETTE[kind]
    title = card["name"]
    if kind == "command":
        kicker = f'{card["id"]}  COMMAND / {card["tag"].upper()}'
        upper_label, lower_label = "IMPERIUM", "OFFICIUM"
        upper, lower = card["imperium"], card["officium"]
        footer = "THE FRONTIER AND ROME CLAIM THE SAME HOUR"
    elif kind == "crisis":
        kicker = f'{card["id"]}  CRISIS / GROUP {card["group"]}'
        upper_label, lower_label = "ARRIVAL", "ENEMY DESIGN"
        upper, lower = card["arrival"], card["design"]
        footer = "WHAT ARRIVES IS NOT YOURS. WHAT YOU DO IS."
    else:
        kicker = f'{card["id"]}  SCENARIO / DIFFICULTY {card["difficulty"]}'
        upper_label, lower_label = card["years"], f'{card["rounds"]} ROUNDS'
        objective = card["objective"]
        bits = [f'{objective.get("momentum", 0)} Momentum']
        if "max_total_threat" in objective:
            bits.append(f'Threat total <= {objective["max_total_threat"]}')
        if "mercy" in objective:
            bits.append(f'Mercy {objective["mercy"]}+')
        if "senate" in objective:
            bits.append(f'Senate {objective["senate"]}+')
        upper, lower = card["history"], "Objective: " + "; ".join(bits) + ". " + card["rule"]
        footer = "HISTORY SETS THE BURDEN. YOUR JUDGMENT SETS THE END."

    title_size = 42 if len(title) < 24 else 34
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="2.5in" height="3.5in" viewBox="0 0 750 1050">
<rect width="750" height="1050" rx="34" fill="{bg}"/>
<rect x="20" y="20" width="710" height="1010" rx="28" fill="none" stroke="{accent}" stroke-width="4"/>
<path d="M55 165H695M55 550H695M55 914H695" stroke="{accent}" stroke-width="2"/>
<text x="55" y="78" fill="{accent}" font-family="Arial,sans-serif" font-size="18" font-weight="bold" letter-spacing="2">{html.escape(kicker)}</text>
<text x="55" y="137" fill="{ink}" font-family="Georgia,serif" font-size="{title_size}" font-weight="bold">{html.escape(title)}</text>
<text x="55" y="215" fill="{accent}" font-family="Arial,sans-serif" font-size="20" font-weight="bold" letter-spacing="3">{html.escape(upper_label)}</text>
<text x="55" y="270" fill="{ink}" font-family="Georgia,serif" font-size="27">{tspans(text_lines(upper, 41, 7), 55, 34)}</text>
<text x="55" y="602" fill="{accent}" font-family="Arial,sans-serif" font-size="20" font-weight="bold" letter-spacing="3">{html.escape(lower_label)}</text>
<text x="55" y="657" fill="{ink}" font-family="Georgia,serif" font-size="27">{tspans(text_lines(lower, 41, 7), 55, 34)}</text>
<text x="375" y="965" text-anchor="middle" fill="{accent}" font-family="Arial,sans-serif" font-size="14" font-weight="bold" letter-spacing="2">{footer}</text>
<circle cx="375" cy="995" r="7" fill="{accent}"/>
</svg>'''


def back_svg(kind: str) -> str:
    bg, ink, accent = PALETTE[kind]
    name = {"command": "COMMAND", "crisis": "CRISIS", "scenario": "SCENARIO"}[kind]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="2.5in" height="3.5in" viewBox="0 0 750 1050">
<rect width="750" height="1050" rx="34" fill="{bg}"/>
<rect x="20" y="20" width="710" height="1010" rx="28" fill="none" stroke="{accent}" stroke-width="4"/>
<rect x="48" y="48" width="654" height="954" rx="20" fill="none" stroke="{accent}" stroke-width="1"/>
<circle cx="375" cy="505" r="215" fill="none" stroke="{accent}" stroke-width="3"/>
<circle cx="375" cy="505" r="155" fill="none" stroke="{accent}" stroke-width="2"/>
<path d="M375 260V750M130 505H620M202 332L548 678M548 332L202 678" stroke="{accent}" stroke-width="2" opacity=".7"/>
<text x="375" y="535" text-anchor="middle" fill="{ink}" font-family="Georgia,serif" font-size="102">M</text>
<text x="375" y="835" text-anchor="middle" fill="{ink}" font-family="Georgia,serif" font-size="36" font-weight="bold">IMPERATOR</text>
<text x="375" y="885" text-anchor="middle" fill="{accent}" font-family="Arial,sans-serif" font-size="19" font-weight="bold" letter-spacing="5">{name}</text>
</svg>'''


def embedded(path: Path, x: int, y: int) -> str:
    data = base64.b64encode(path.read_bytes()).decode()
    return f'<image href="data:image/svg+xml;base64,{data}" x="{x}" y="{y}" width="750" height="1050"/>'


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SHEETS.mkdir(parents=True, exist_ok=True)
    BACKS.mkdir(parents=True, exist_ok=True)
    back_paths = {}
    for kind in PALETTE:
        path = BACKS / f"{kind}-back.svg"
        path.write_text(back_svg(kind))
        back_paths[kind] = path

    cards = []
    for kind, source in (
        ("scenario", DATA["scenarios"]),
        ("command", DATA["commands"]),
        ("crisis", DATA["crises"]),
    ):
        for card in source:
            path = OUT / f'{card["id"]}-{slug(card["name"])}.svg'
            path.write_text(card_svg(kind, card))
            cards.append((kind, path))

    for offset in range(0, len(cards), 9):
        chunk = cards[offset:offset + 9]
        fronts, backs = [], []
        for i, (kind, path) in enumerate(chunk):
            col, row = i % 3, i // 3
            fronts.append(embedded(path, col * 750, row * 1050))
            backs.append(embedded(back_paths[kind], (2 - col) * 750, row * 1050))
        number = offset // 9 + 1
        root = '<svg xmlns="http://www.w3.org/2000/svg" width="7.5in" height="10.5in" viewBox="0 0 2250 3150">'
        (SHEETS / f"sheet-{number}-front.svg").write_text(root + "".join(fronts) + "</svg>")
        (SHEETS / f"sheet-{number}-back.svg").write_text(root + "".join(backs) + "</svg>")
    print(f"Built {len(cards)} cards and {(len(cards) + 8) // 9} duplex sheet pairs.")


if __name__ == "__main__":
    main()

