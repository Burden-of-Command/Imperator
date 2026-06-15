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
<text x="{x}" y="{y + 7}" text-anchor="middle" class="small">HOST HOME / STRENGTH</text>{threat}'''


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
.link{{fill:none;stroke:#736958;stroke-width:4}}
.crossing{{fill:none;stroke:#8b2f2b;stroke-width:5;marker-end:url(#arrow)}} .river{{fill:none;stroke:#809298;stroke-width:9;opacity:.6}}
</style>
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0 0L6 3L0 6Z" fill="#8b2f2b"/></marker></defs>
<rect width="1654" height="1169" fill="#e8e3d8"/>
<rect x="24" y="24" width="1606" height="1121" fill="none" stroke="#8b2f2b" stroke-width="4"/>
<text x="72" y="88" class="title">IMPERATOR</text>
<text x="74" y="125" class="sub">THE BURDEN OF THE DANUBE</text>
<path d="M420 390C650 335 900 345 1440 370" class="river"/>
<text x="1335" y="354" class="small" fill="#647b83">DANUBE</text>
<path d="M150 545H390H650H930H1220" class="road"/>
<path d="M390 545L650 545M650 545L930 545M930 545L1220 545" class="road"/>
<path d="M760 272L930 505M1030 307L1220 505" class="link"/>
<path d="M520 312L650 505M760 272L650 505M1030 307L930 505M1340 362L1220 505" class="crossing"/>
<path d="M1110 545L1040 545M820 545L760 545M545 545L495 545M288 545L252 545" class="crossing"/>
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
<text x="1175" y="912" class="label">COALITION  0  1  2  3  4  5</text>
<text x="1175" y="946" class="label">LOST LEGIONS / DEVASTATION</text>
<g>{"".join(tracks)}</g>
<text x="72" y="1140" class="small">NOT EVENTS WHICH DISTURB MEN, BUT THEIR JUDGMENTS CONCERNING THEM</text>
<text x="1582" y="1140" text-anchor="end" class="tiny">PROTOTYPE 0.5</text>
</svg>'''
    (OUT / "Imperator-Campaign-Mat.svg").write_text(svg)

    aid = '''<svg xmlns="http://www.w3.org/2000/svg" width="2.5in" height="3.5in" viewBox="0 0 750 1050">
<rect width="750" height="1050" rx="34" fill="#202522"/><rect x="20" y="20" width="710" height="1010" rx="28" fill="none" stroke="#ad8c4b" stroke-width="4"/>
<text x="55" y="90" fill="#eee8d8" font-family="Georgia" font-size="42" font-weight="bold">ROUND</text>
<text x="55" y="145" fill="#ad8c4b" font-family="Arial" font-size="17" letter-spacing="3">RECEIVE / DELIBERATE / ORDER / DESIGN / ENDURE</text>
<path d="M55 175H695" stroke="#ad8c4b"/>
<text x="55" y="235" fill="#ad8c4b" font-family="Arial" font-size="20" font-weight="bold">BASIC ORDERS: CHOOSE TWO DIFFERENT</text>
<text x="55" y="290" fill="#eee8d8" font-family="Georgia" font-size="26">
<tspan x="55">March: two Legions, one connection each.</tspan><tspan x="55" dy="40">Fortify: weaken Army or restore base.</tspan>
<tspan x="55" dy="40">Campaign: battle an Army in your space.</tspan><tspan x="55" dy="40">Petition: +1 Senate or Coalition -2.</tspan>
<tspan x="55" dy="40">Requisition: +2 Supply; -1 Rome/Senate.</tspan><tspan x="55" dy="40">Meditate: +1 Resolve; possibly -1 Fatigue.</tspan></text>
<path d="M55 570H695" stroke="#ad8c4b"/>
<text x="55" y="625" fill="#ad8c4b" font-family="Arial" font-size="20" font-weight="bold">BATTLE</text>
<text x="55" y="680" fill="#eee8d8" font-family="Georgia" font-size="22">
<tspan x="55">Rome = Legions + d6 + bonuses</tspan><tspan x="55" dy="34">Enemy = Army Strength + d6</tspan>
<tspan x="55" dy="49">Contain: +1; no Momentum/deep retreat</tspan><tspan x="55" dy="34">Set Battle: standard; may Exert +2</tspan>
<tspan x="55" dy="34">Force: +2, +1 Fatigue; failure loses L</tspan><tspan x="55" dy="49">Win 3+: -2 Strength, retreat home</tspan>
<tspan x="55" dy="34">Win 1-2: -1 Strength, retreat one</tspan><tspan x="55" dy="34">Loss: pay result and doctrine risk</tspan></text>
<text x="375" y="984" text-anchor="middle" fill="#ad8c4b" font-family="Arial" font-size="13" letter-spacing="2">COALITION 5: SECOND ARMY SURGES</text>
<text x="375" y="1010" text-anchor="middle" fill="#ad8c4b" font-family="Arial" font-size="13" letter-spacing="2">ASSENT ONCE PER ROUND</text>
</svg>'''
    (OUT / "Imperator-Order-Reference.svg").write_text(aid)
    marker_data = [
        ("R", "RAETIAN", "#5b4635"), ("M", "MARCOMANNI", "#704039"),
        ("Q", "QUADI", "#3f5350"), ("I", "IAZYGES", "#4a4c68"),
    ]
    markers = []
    for index, (letter, name, color) in enumerate(marker_data):
        x = index * 180
        markers.append(f'''<g transform="translate({x} 0)">
<rect x="8" y="8" width="164" height="164" rx="18" fill="{color}" stroke="#d6bd79" stroke-width="6"/>
<text x="90" y="91" text-anchor="middle" fill="#fff8e8" font-family="Georgia" font-size="72" font-weight="bold">{letter}</text>
<text x="90" y="137" text-anchor="middle" fill="#d6bd79" font-family="Arial" font-size="13" font-weight="bold" letter-spacing="2">{name}</text>
</g>''')
    marker_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="7.2in" height="1.8in" viewBox="0 0 720 180">
<rect width="720" height="180" fill="#e8e3d8"/>{"".join(markers)}</svg>'''
    (OUT / "Imperator-Army-Markers.svg").write_text(marker_svg)
    devastation_svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="7.2in" height="1.8in" viewBox="0 0 720 180">
<rect width="720" height="180" fill="#e8e3d8"/>
<g fill="#c8b3a0" stroke="#7c2d28" stroke-width="5">
<rect x="18" y="18" width="126" height="126" rx="10"/><rect x="158" y="18" width="126" height="126" rx="10"/>
<rect x="298" y="18" width="126" height="126" rx="10"/><rect x="438" y="18" width="126" height="126" rx="10"/>
<rect x="578" y="18" width="126" height="126" rx="10"/></g>
<g fill="#7c2d28" font-family="Arial" font-size="13" font-weight="bold" text-anchor="middle" letter-spacing="1">
<text x="81" y="84">DEVASTATED</text><text x="221" y="84">DEVASTATED</text><text x="361" y="84">DEVASTATED</text>
<text x="501" y="84">DEVASTATED</text><text x="641" y="84">DEVASTATED</text></g>
</svg>'''
    (OUT / "Imperator-Devastation-Markers.svg").write_text(devastation_svg)
    print("Built campaign mat, order reference, Army markers, and devastation markers.")


if __name__ == "__main__":
    main()
