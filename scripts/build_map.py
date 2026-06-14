#!/usr/bin/env python3
"""Build the A4 campaign mat and a poker-sized order reference."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist"


def track(label: str, y: int, maximum: int = 7) -> str:
    cells = []
    for value in range(maximum + 1):
        x = 555 + value * 66
        cells.append(
            f'<rect x="{x}" y="{y}" width="62" height="48" rx="4" fill="none" stroke="#8b2f2b" stroke-width="2"/>'
            f'<text x="{x + 31}" y="{y + 32}" text-anchor="middle" class="n">{value}</text>'
        )
    return f'<text x="525" y="{y + 32}" text-anchor="end" class="label">{label}</text>' + "".join(cells)


def base_node(x: int, y: int, name: str) -> str:
    return f'''<rect x="{x - 96}" y="{y - 40}" width="192" height="80" rx="10" class="base"/>
<text x="{x}" y="{y - 7}" text-anchor="middle" class="place">{name}</text>
<text x="{x}" y="{y + 22}" text-anchor="middle" class="small">LEGIONS</text>'''


def front_node(x: int, y: int, name: str) -> str:
    threat = "".join(
        f'<circle cx="{x - 84 + i * 28}" cy="{y + 43}" r="12" fill="none" stroke="#8b2f2b" stroke-width="2"/>'
        f'<text x="{x - 84 + i * 28}" y="{y + 48}" text-anchor="middle" class="tiny">{i}</text>'
        for i in range(7)
    )
    return f'''<path d="M{x - 112} {y - 62}L{x + 112} {y - 62}L{x + 98} {y + 70}L{x - 98} {y + 70}Z" class="front"/>
<text x="{x}" y="{y - 25}" text-anchor="middle" class="place">{name}</text>
<text x="{x}" y="{y + 7}" text-anchor="middle" class="small">LEGIONS / THREAT</text>{threat}'''


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tracks = [
        track("ROME", 680), track("SENATE", 745), track("RESOLVE", 810),
        track("TREASURY", 875), track("SUPPLY", 940),
        track("FATIGUE", 1005, 6), track("MERCY", 1070, 6),
    ]
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="11.69in" height="8.27in" viewBox="0 0 1654 1169">
<style>
.title{{font:700 46px Georgia;fill:#272722}} .sub{{font:18px Arial;letter-spacing:4px;fill:#8b2f2b}}
.theater{{font:700 25px Georgia;fill:#272722}} .place{{font:700 16px Georgia;fill:#272722}} .label{{font:700 17px Arial;fill:#272722}}
.small{{font:700 13px Arial;letter-spacing:2px;fill:#8b2f2b}} .tiny{{font:12px Arial;fill:#272722}}
.n{{font:16px Georgia;fill:#272722}} .box,.base{{fill:#eee9dd;stroke:#272722;stroke-width:3}}
.front{{fill:#ddd4c3;stroke:#8b2f2b;stroke-width:3}} .road{{fill:none;stroke:#736958;stroke-width:7}}
.crossing{{fill:none;stroke:#8b2f2b;stroke-width:5}} .river{{fill:none;stroke:#809298;stroke-width:9;opacity:.6}}
</style>
<rect width="1654" height="1169" fill="#e8e3d8"/>
<rect x="24" y="24" width="1606" height="1121" fill="none" stroke="#8b2f2b" stroke-width="4"/>
<text x="72" y="88" class="title">IMPERATOR</text>
<text x="74" y="125" class="sub">THE BURDEN OF THE DANUBE</text>
<path d="M420 390C650 335 900 345 1440 370" class="river"/>
<text x="1335" y="354" class="small" fill="#647b83">DANUBE</text>
<path d="M150 545H390H650H930H1220" class="road"/>
<path d="M390 545L650 545M650 545L930 545M930 545L1220 545" class="road"/>
<path d="M650 505L520 312M650 505L760 272M930 505L760 272M930 505L1030 307M1220 505L1030 307M1220 505L1340 362" class="crossing"/>
{front_node(520, 240, "RAETIAN FRONTIER")}
{front_node(760, 200, "MARCOMANNIA")}
{front_node(1030, 235, "LANDS OF THE QUADI")}
{front_node(1340, 290, "PLAIN OF THE IAZYGES")}
{base_node(150, 545, "AQUILEIA")}
{base_node(390, 545, "VIRUNUM")}
{base_node(650, 545, "LAURIACUM")}
{base_node(930, 545, "CARNUNTUM")}
{base_node(1220, 545, "SIRMIUM")}
<text x="690" y="625" text-anchor="middle" class="small">ROMAN ROAD: MARCH ONE PRINTED CONNECTION</text>
<rect x="1140" y="680" width="380" height="270" rx="12" class="box"/>
<text x="1330" y="728" text-anchor="middle" class="theater">CAMPAIGN RECORD</text>
<text x="1175" y="782" class="label">ROUND</text>
<path d="M1175 805H1485" stroke="#272722"/>
<text x="1175" y="850" class="label">MOMENTUM</text>
<path d="M1175 873H1485" stroke="#272722"/>
<text x="1175" y="918" class="label">LOST LEGIONS</text>
<rect x="1340" y="886" width="145" height="42" fill="none" stroke="#272722"/>
<g>{"".join(tracks)}</g>
<text x="72" y="1140" class="small">NOT EVENTS WHICH DISTURB MEN, BUT THEIR JUDGMENTS CONCERNING THEM</text>
<text x="1582" y="1140" text-anchor="end" class="tiny">PROTOTYPE 0.2</text>
</svg>'''
    (OUT / "Imperator-Campaign-Mat.svg").write_text(svg)

    aid = '''<svg xmlns="http://www.w3.org/2000/svg" width="2.5in" height="3.5in" viewBox="0 0 750 1050">
<rect width="750" height="1050" rx="34" fill="#202522"/><rect x="20" y="20" width="710" height="1010" rx="28" fill="none" stroke="#ad8c4b" stroke-width="4"/>
<text x="55" y="90" fill="#eee8d8" font-family="Georgia" font-size="42" font-weight="bold">ROUND</text>
<text x="55" y="145" fill="#ad8c4b" font-family="Arial" font-size="17" letter-spacing="3">RECEIVE / DELIBERATE / ORDER / DESIGN / ENDURE</text>
<path d="M55 175H695" stroke="#ad8c4b"/>
<text x="55" y="235" fill="#ad8c4b" font-family="Arial" font-size="20" font-weight="bold">BASIC ORDERS: CHOOSE TWO DIFFERENT</text>
<text x="55" y="290" fill="#eee8d8" font-family="Georgia" font-size="26">
<tspan x="55">March: two Legions, one connection.</tspan><tspan x="55" dy="40">Fortify: 1 Supply; -1 adjacent Threat.</tspan>
<tspan x="55" dy="40">Campaign: battle in enemy settlement.</tspan><tspan x="55" dy="40">Petition: 1 Treasury; +1 Senate.</tspan>
<tspan x="55" dy="40">Requisition: +2 Supply; -1 Rome/Senate.</tspan><tspan x="55" dy="40">Meditate: +1 Resolve; possibly -1 Fatigue.</tspan></text>
<path d="M55 570H695" stroke="#ad8c4b"/>
<text x="55" y="625" fill="#ad8c4b" font-family="Arial" font-size="20" font-weight="bold">BATTLE</text>
<text x="55" y="680" fill="#eee8d8" font-family="Georgia" font-size="25">
<tspan x="55">Rome = Legions + d6 + bonuses</tspan><tspan x="55" dy="38">Enemy = Threat + d6 + bonuses</tspan>
<tspan x="55" dy="55">Win 3+: -2 Threat, +1 Momentum</tspan><tspan x="55" dy="38">Win 1-2: -1 Threat, +1 Momentum</tspan>
<tspan x="55" dy="38">Tie: -1 Threat; -1 Supply or +1 Fatigue</tspan><tspan x="55" dy="38">Lose 1-2: -1 Supply, -1 Resolve</tspan>
<tspan x="55" dy="38">Lose 3+: lose Legion, -1 Rome</tspan></text>
<text x="375" y="965" text-anchor="middle" fill="#ad8c4b" font-family="Arial" font-size="14" letter-spacing="2">BASE SUPPORT +1 / EXERT +2</text>
<text x="375" y="995" text-anchor="middle" fill="#ad8c4b" font-family="Arial" font-size="14" letter-spacing="2">ASSENT ONCE PER ROUND</text>
</svg>'''
    (OUT / "Imperator-Order-Reference.svg").write_text(aid)
    print("Built campaign mat and order reference.")


if __name__ == "__main__":
    main()
