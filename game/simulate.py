#!/usr/bin/env python3
"""Coarse Monte Carlo balance model for IMPERATOR v0.2."""
from __future__ import annotations

import argparse
import json
import random
import statistics
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "game/game.json").read_text())
SCENARIOS = DATA["scenarios"]
SPACES = {space["id"]: space for space in DATA["spaces"]}
FRONTS = [key for key, space in SPACES.items() if space["kind"] == "front"]
BASES = [key for key, space in SPACES.items() if space["kind"] == "base"]


@dataclass
class Result:
    won: bool
    score: int
    momentum: int
    total_threat: int
    legions: int


def clamp(value: int, low: int = 0, high: int = 7) -> int:
    return max(low, min(high, value))


def route(start: str, goal: str) -> list[str]:
    queue = [[start]]
    visited = {start}
    while queue:
        path = queue.pop(0)
        if path[-1] == goal:
            return path
        for neighbor in SPACES[path[-1]]["adjacent"]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(path + [neighbor])
    return [start]


def defended(front: str, legions: dict[str, int]) -> bool:
    if legions[front] >= 1:
        return True
    return any(
        SPACES[neighbor]["kind"] == "base" and legions[neighbor] >= 2
        for neighbor in SPACES[front]["adjacent"]
    )


def play(scenario: dict, style: str, rng: random.Random) -> Result:
    tracks = dict(scenario["tracks"])
    threat = dict(scenario["threat"])
    legions = {key: scenario["legions"].get(key, 0) for key in SPACES}
    momentum = 0
    mercy = tracks["mercy"]
    named_momentum = {front: 0 for front in FRONTS}

    for round_no in range(scenario["rounds"]):
        # Crisis pressure represents the average severity of the scenario's era.
        pressure = 1 + (scenario["difficulty"] >= 3 and rng.random() < 0.18)
        target = rng.choice(FRONTS)
        threat[target] = clamp(threat[target] + pressure, 0, 6)
        if rng.random() < 0.10 + scenario["difficulty"] * 0.025:
            tracks[rng.choice(["rome", "senate", "resolve", "treasury", "supply"])] -= 1

        # Move a detachment along the shortest printed route to the urgent front.
        named_objectives = scenario["objective"].get("named", {})
        urgent = max(
            FRONTS,
            key=lambda t: threat[t] - legions[t] * 0.7
            + (2 if named_momentum[t] < named_objectives.get(t, 0) else 0),
        )
        if legions[urgent] == 0:
            candidates = [space for space in SPACES if legions[space] > 0]
            if candidates:
                source = min(candidates, key=lambda space: len(route(space, urgent)))
                path = route(source, urgent)
                destination = path[min(2 if threat[urgent] >= 4 else 1, len(path) - 1)]
                moved = min(2, legions[source])
                legions[source] -= moved
                legions[destination] += moved

        # Civil investment competes directly with a second military action.
        civil_need = min(tracks["rome"], tracks["senate"], tracks["resolve"], tracks["supply"])
        needs_mercy = mercy < scenario["objective"].get("mercy", 0)
        needs_senate = tracks["senate"] < scenario["objective"].get("senate", 0)
        civil = (
            (style == "civic" and rng.random() < 0.68)
            or (style == "adaptive" and (civil_need <= 3 or needs_mercy or needs_senate))
            or (style == "martial" and civil_need <= 2)
        )
        if civil:
            if needs_mercy and tracks["senate"] > 1:
                mercy = clamp(mercy + 1, 0, 6)
                tracks["senate"] -= 1
            elif needs_senate:
                tracks["senate"] = clamp(tracks["senate"] + 1)
                tracks["treasury"] -= 1
            else:
                weakest = min(["rome", "senate", "resolve", "supply"], key=lambda k: tracks[k])
                if weakest == "supply":
                    tracks["supply"] = clamp(tracks["supply"] + 2)
                    tracks["treasury"] -= 1
                else:
                    tracks[weakest] = clamp(tracks[weakest] + 1)
        elif tracks["fatigue"] >= 4:
            tracks["fatigue"] = max(0, tracks["fatigue"] - 2)
            if tracks["supply"] > 0:
                tracks["supply"] -= 1
                if legions[urgent] or any(
                    legions[n] and SPACES[n]["kind"] == "base"
                    for n in SPACES[urgent]["adjacent"]
                ):
                    threat[urgent] = max(0, threat[urgent] - 1)
        else:
            # Approximate the chosen card's Imperium half.
            if threat[urgent] >= 5 and tracks["supply"] > 0:
                tracks["supply"] -= 1
                threat[urgent] -= 1
            elif threat[urgent] >= 3:
                threat[urgent] -= 1

        # A Command effect plus two Basic Orders can produce two campaigns.
        remaining = scenario["rounds"] - round_no
        need = scenario["objective"].get("momentum", 0) - momentum
        battles = 2 if style == "martial" and tracks["fatigue"] <= 3 else 1
        if style == "adaptive" and need > remaining and tracks["fatigue"] <= 3:
            battles = 2
        fought = False
        for _ in range(battles):
            occupied_fronts = [front for front in FRONTS if legions[front] > 0]
            if not occupied_fronts:
                break
            urgent = max(
                occupied_fronts,
                key=lambda t: threat[t] - legions[t] * 0.6
                + (2 if named_momentum[t] < named_objectives.get(t, 0) else 0),
            )
            should_fight = (
                threat[urgent] >= 2 or need >= remaining or style == "martial"
            )
            if not should_fight:
                break
            fought = True
            committed = legions[urgent]
            paid = max(0, committed - 1)
            if tracks["supply"] < paid:
                committed = max(1, tracks["supply"] + 1)
                paid = committed - 1
            tracks["supply"] -= paid
            expected_margin = committed + (0 if civil else 1) - threat[urgent]
            exert = (
                style in ("martial", "adaptive")
                and expected_margin < 1
                and tracks["fatigue"] <= 3
                and tracks["resolve"] > 2
            )
            command_bonus = 1 if not civil else 0
            base_support = any(
                SPACES[n]["kind"] == "base" and legions[n] > 0
                for n in SPACES[urgent]["adjacent"]
            )
            roman = (
                committed + rng.randint(1, 6) + command_bonus
                + base_support + (2 if exert else 0)
            )
            enemy = threat[urgent] + rng.randint(1, 6) + (scenario["difficulty"] == 4)
            tracks["fatigue"] += (0 if rng.random() < 0.22 else 1) + exert
            margin = roman - enemy
            if margin >= 3:
                threat[urgent] = max(0, threat[urgent] - 2)
                momentum += 1
                named_momentum[urgent] += 1
            elif margin >= 0:
                threat[urgent] = max(0, threat[urgent] - 1)
                momentum += 1
                named_momentum[urgent] += 1
                if margin == 0:
                    tracks["supply"] -= 1
            elif margin >= -2:
                tracks["supply"] -= 1
                tracks["resolve"] -= 1
            else:
                legions[urgent] -= 1
                tracks["rome"] -= 1

            if rng.random() < 0.45 and margin < 3:
                # Assent is used when the roll was genuinely exposed.
                if style == "civic":
                    mercy = clamp(mercy + 1, 0, 6)
                else:
                    tracks["resolve"] = clamp(tracks["resolve"] + 1)
            need = scenario["objective"].get("momentum", 0) - momentum

        pressing = max(FRONTS, key=lambda t: threat[t])
        if threat[pressing] >= 4 and not defended(pressing, legions):
            tracks["rome"] -= 1
        if tracks["fatigue"] >= 5:
            tracks["resolve"] -= 1
        if style != "martial" and not fought:
            tracks["fatigue"] = max(0, tracks["fatigue"] - 1)

        for key in tracks:
            tracks[key] = clamp(tracks[key], 0, 6 if key == "fatigue" else 7)
        if min(tracks["rome"], tracks["senate"], tracks["resolve"]) <= 0:
            break
        if any(threat[t] >= 6 and not defended(t, legions) for t in FRONTS) or sum(legions.values()) <= 0:
            break

    objective = scenario["objective"]
    total_threat = sum(threat.values())
    won = (
        momentum >= objective.get("momentum", 0)
        and all(named_momentum[key] >= value for key, value in objective.get("named", {}).items())
        and total_threat <= objective.get("max_total_threat", 99)
        and tracks["senate"] >= objective.get("senate", 0)
        and tracks["resolve"] >= objective.get("resolve", 0)
        and mercy >= objective.get("mercy", 0)
        and min(tracks["rome"], tracks["senate"], tracks["resolve"]) > 0
        and not any(threat[t] >= 6 and not defended(t, legions) for t in FRONTS)
    )
    score = (
        momentum + tracks["rome"] + tracks["senate"] + tracks["resolve"]
        + tracks["treasury"] - tracks["fatigue"] - total_threat
    )
    return Result(won, score, momentum, total_threat, sum(legions.values()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=180)
    args = parser.parse_args()
    rng = random.Random(args.seed)
    print(f"IMPERATOR v{DATA['version']} coarse balance model ({args.games} games/style)")
    for scenario in SCENARIOS:
        rows = []
        for style in ("martial", "adaptive", "civic"):
            results = [play(scenario, style, rng) for _ in range(args.games)]
            rate = 100 * sum(r.won for r in results) / len(results)
            median = statistics.median(r.score for r in results)
            rows.append(f"{style}: {rate:4.1f}% win, score {median:4.1f}")
        print(f"{scenario['id']} {scenario['name']}: " + " | ".join(rows))


if __name__ == "__main__":
    main()
