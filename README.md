# IMPERATOR: The Burden of the Danube

A compact solo wargame about command, endurance, and political duty during the
Marcomannic Wars, c. 166-180 CE.

You are Marcus Aurelius. Six legions are not enough for every frontier. A
campaign that saves Pannonia may empty the treasury; a necessary levy may cost
the Senate; clemency may secure peace or give an enemy time to gather.

## Design Pillars

- **Small footprint:** 40 cards, one A4 campaign mat, 18 cubes, and two d6.
- **Armies on the map:** legions and four coalition Hosts march between named
  bases, crossings, and homelands.
- **One-step opposition:** each Crisis activates one Host with one order:
  Muster or Raid.
- **One burden, two claims:** every Command card is used either for its military
  order or its civil order.
- **History under pressure:** plague, Aquileia, the Quadi, the Iazyges,
  Avidius Cassius, taxation, diplomacy, and succession appear as linked crises.
- **Stoic rather than heroic:** victory means preserving the state without
  surrendering judgment, legitimacy, or humanity.
- **Replayable scenarios:** seven historical episodes and a linked grand
  campaign use the same compact system.

## Contents

- 16 Command cards
- 16 Crisis cards
- 8 Scenario cards
- 1 compact node-map campaign mat
- 6 legion cubes, 4 Host markers, 4 Strength cubes, and 8 track cubes
- 2 standard six-sided dice

## Start Here

Read [RULES.md](RULES.md), choose **The Gathering Storm**, and place the cubes
as shown on its Scenario card. A first game takes about 35-50 minutes.

## Web Playtest

```bash
python3 -m http.server 4173
```

Open `http://localhost:4173/web/`. The browser edition automates setup, legal
movement, Crisis sequencing, Host orders, battles, retreats, tracks, and
scenario scoring.

## Repository

- `game/game.json` - canonical cards, scenarios, and map data
- `game/simulate.py` - strategy-aware balance simulator
- `scripts/build_cards.py` - individual cards and duplex-ready SVG sheets
- `scripts/build_map.py` - A4 campaign mat and compact player aid
- `web/` - local browser-playable guided edition
- `RULES.md` - complete prototype rules
- `HISTORICAL_NOTES.md` - history, terminology, and design boundaries
- `PLAYTEST.md` - test protocol and balance targets
- `DESIGN_TARGET.md` - evidence gates for an exceptional-game ambition
- `dist/` - generated print-and-play files

## Build

```bash
python3 game/simulate.py --games 5000
python3 scripts/build_cards.py
python3 scripts/build_map.py
```

This is a development prototype. Historical dates and sequences are sometimes
compressed, but uncertainty is identified rather than presented as fact.
