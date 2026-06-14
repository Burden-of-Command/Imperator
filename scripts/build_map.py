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


def theater(x: int, y: int, name: str) -> str:
    threat = "".join(
        f'<circle cx="{x - 138 + i * 46}" cy="{y + 91}" r="17" fill="none" stroke="#8b2f2b" stroke-width="2"/>'
        f'<text x="{x - 138 + i * 46}" y="{y + 97}" text-anchor="middle" class="tiny">{i}</text>'
        for i in range(7)
    )
    return f'''<rect x="{x - 175}" y="{y - 80}" width="350" height="190" rx="12" class="box"/>
<text x="{x}" y="{y - 31}" text-anchor="middle" class="theater">{name}</text>
<text x="{x}" y="{y + 5}" text-anchor="middle" class="small">LEGIONS</text>
<rect x="{x - 122}" y="{y + 18}" width="244" height="35" rx="4" fill="none" stroke="#272722"/>
<text x="{x}" y="{y + 66}" text-anchor="middle" class="small">THREAT</text>{threat}'''


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
.theater{{font:700 25px Georgia;fill:#272722}} .label{{font:700 17px Arial;fill:#272722}}
.small{{font:700 13px Arial;letter-spacing:2px;fill:#8b2f2b}} .tiny{{font:12px Arial;fill:#272722}}
.n{{font:16px Georgia;fill:#272722}} .box{{fill:#eee9dd;stroke:#272722;stroke-width:3}}
</style>
<rect width="1654" height="1169" fill="#e8e3d8"/>
<rect x="24" y="24" width="1606" height="1121" fill="none" stroke="#8b2f2b" stroke-width="4"/>
<text x="72" y="88" class="title">IMPERATOR</text>
<text x="74" y="125" class="sub">THE BURDEN OF THE DANUBE</text>
<path d="M250 360H475M600 360H825M950 360H1175" stroke="#8b2f2b" stroke-width="8"/>
{theater(250, 360, "RAETIA")}
{theater(600, 360, "NORICUM")}
{theater(950, 360, "UPPER PANNONIA")}
{theater(1300, 360, "LOWER PANNONIA")}
<path d="M250 580V625M250 625H950M600 580V625M950 580V625" fill="none" stroke="#8b2f2b" stroke-width="5"/>
{theater(250, 805, "AQUILEIA / RESERVE")}
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
<text x="1582" y="1140" text-anchor="end" class="tiny">PROTOTYPE 0.1</text>
</svg>'''
    (OUT / "Imperator-Campaign-Mat.svg").write_text(svg)

    aid = '''<svg xmlns="http://www.w3.org/2000/svg" width="2.5in" height="3.5in" viewBox="0 0 750 1050">
<rect width="750" height="1050" rx="34" fill="#202522"/><rect x="20" y="20" width="710" height="1010" rx="28" fill="none" stroke="#ad8c4b" stroke-width="4"/>
<text x="55" y="90" fill="#eee8d8" font-family="Georgia" font-size="42" font-weight="bold">ROUND</text>
<text x="55" y="145" fill="#ad8c4b" font-family="Arial" font-size="17" letter-spacing="3">RECEIVE / DELIBERATE / ORDER / DESIGN / ENDURE</text>
<path d="M55 175H695" stroke="#ad8c4b"/>
<text x="55" y="235" fill="#ad8c4b" font-family="Arial" font-size="20" font-weight="bold">BASIC ORDERS: CHOOSE TWO DIFFERENT</text>
<text x="55" y="290" fill="#eee8d8" font-family="Georgia" font-size="26">
<tspan x="55">March: move up to two Legions.</tspan><tspan x="55" dy="40">Fortify: 1 Supply; -1 Threat.</tspan>
<tspan x="55" dy="40">Campaign: fight one battle.</tspan><tspan x="55" dy="40">Petition: 1 Treasury; +1 Senate.</tspan>
<tspan x="55" dy="40">Requisition: +2 Supply; -1 Rome/Senate.</tspan><tspan x="55" dy="40">Meditate: +1 Resolve; possibly -1 Fatigue.</tspan></text>
<path d="M55 570H695" stroke="#ad8c4b"/>
<text x="55" y="625" fill="#ad8c4b" font-family="Arial" font-size="20" font-weight="bold">BATTLE</text>
<text x="55" y="680" fill="#eee8d8" font-family="Georgia" font-size="25">
<tspan x="55">Rome = Legions + d6 + bonuses</tspan><tspan x="55" dy="38">Enemy = Threat + d6 + bonuses</tspan>
<tspan x="55" dy="55">Win 3+: -2 Threat, +1 Momentum</tspan><tspan x="55" dy="38">Win 1-2: -1 Threat, +1 Momentum</tspan>
<tspan x="55" dy="38">Tie: -1 Threat; -1 Supply or +1 Fatigue</tspan><tspan x="55" dy="38">Lose 1-2: -1 Supply, -1 Resolve</tspan>
<tspan x="55" dy="38">Lose 3+: lose Legion, -1 Rome</tspan></text>
<text x="375" y="990" text-anchor="middle" fill="#ad8c4b" font-family="Arial" font-size="15" letter-spacing="2">EXERT +2 / ASSENT ONCE PER ROUND</text>
</svg>'''
    (OUT / "Imperator-Order-Reference.svg").write_text(aid)
    print("Built campaign mat and order reference.")


if __name__ == "__main__":
    main()
