#!/usr/bin/env python3
"""Coarse Monte Carlo balance model for IMPERATOR v0.6."""
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
CRISES = DATA["crises"]
CRISES_BY_GROUP = {
    group: [card for card in CRISES if card["group"] == group]
    for group in {card["group"] for card in CRISES}
}
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
    mandate: int
    named_complete: bool


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


def retreat(host: str, hosts: dict[str, str], decisive: bool = False) -> None:
    position = hosts[host]
    if position == host:
        return
    path = route(position, host)
    hosts[host] = host if decisive else path[1]


def activate_host(
    active_host: str,
    order: str,
    strength: dict[str, int],
    hosts: dict[str, str],
    legions: dict[str, int],
    tracks: dict[str, int],
    devastated: set[str],
    rng: random.Random,
) -> int:
    if strength[active_host] == 0:
        strength[active_host] = 1
        hosts[active_host] = active_host
        return 0
    if order == "muster" and strength[active_host] < 6:
        strength[active_host] += 1
        if active_host == "raetian_frontier" and strength[active_host] >= 4:
            tracks["supply"] -= 1
        return 1 if active_host == "quadi" else 0

    current = hosts[active_host]
    if legions[current] > 0:
        destination = current
    else:
        path = route(current, "aquileia")
        destination = path[1] if len(path) > 1 else current
        hosts[active_host] = destination
    if destination == current and legions[destination] == 0:
        return 0
    if legions[destination] > 0:
        base_bonus = int(SPACES[destination]["kind"] == "base" and destination not in devastated)
        roman = legions[destination] + rng.randint(1, 6) + base_bonus
        cavalry_bonus = int(active_host == "iazyges" and legions[destination] < 2)
        enemy = strength[active_host] + rng.randint(1, 6) + cavalry_bonus
        margin = roman - enemy
        if margin > 0:
            strength[active_host] = max(0, strength[active_host] - 1)
            retreat(active_host, hosts)
        elif margin <= -3:
            legions[destination] -= 1
            tracks["rome"] -= 1
        elif margin < 0:
            tracks["resolve"] -= 1
        if destination == "aquileia" and hosts[active_host] == "aquileia":
            tracks["rome"] = 0
    elif destination == "aquileia":
        tracks["rome"] = 0
    elif SPACES[destination]["kind"] == "base":
        devastated.add(destination)
        tracks["rome"] -= 1
        if active_host == "marcomannia":
            tracks["rome"] -= 1
        resource = "supply" if tracks["supply"] >= tracks["treasury"] else "treasury"
        tracks[resource] -= 1
    return 0


def play(scenario: dict, style: str, rng: random.Random) -> Result:
    tracks = dict(scenario["tracks"])
    strength = dict(scenario["threat"])
    hosts = dict(scenario["hosts"])
    legions = {key: scenario["legions"].get(key, 0) for key in SPACES}
    momentum = 0
    mercy = tracks["mercy"]
    named_momentum = {front: 0 for front in FRONTS}
    coalition = 0
    devastated: set[str] = set()
    senate_five_awarded = False
    rain_miracle_used = False
    mandate = 0
    mandate_flags: set[str] = set()

    for round_no in range(scenario["rounds"]):
        crisis = rng.choice(CRISES_BY_GROUP[scenario["groups"][round_no]])
        for target, amount in crisis.get("pressure", {}).items():
            if target == "highest":
                target = max(FRONTS, key=lambda front: strength[front])
            strength[target] = clamp(strength[target] + amount, 0, 6)
        for track, amount in crisis.get("track_loss", {}).items():
            if rng.random() < 0.65:
                tracks[track] -= amount

        # Move a detachment along the shortest printed route to the urgent front.
        named_objectives = scenario["objective"].get("named", {})
        urgent = max(
            FRONTS,
            key=lambda t: strength[t] + max(0, 4 - len(route(hosts[t], "aquileia")))
            - legions[hosts[t]] * 0.7
            + (5 if named_momentum[t] < named_objectives.get(t, 0) else 0),
        )
        target_space = hosts[urgent]
        mandate_target = None
        if scenario["id"] == "S01":
            missing = [
                base for base in ("lauriacum", "carnuntum", "sirmium")
                if legions[base] == 0
            ]
            if missing:
                mandate_target = min(
                    missing,
                    key=lambda base: min(
                        len(route(source, base))
                        for source in SPACES if legions[source] > 0
                    ),
                )
        elif scenario["id"] == "S03" and legions["marcomannia"] < 2:
            mandate_target = "marcomannia"
        elif scenario["id"] == "S05":
            mandate_target = hosts["iazyges"]
            urgent = "iazyges"
        elif scenario["id"] == "S07":
            missing = [
                front for front in ("marcomannia", "quadi")
                if legions[front] == 0
            ]
            if missing:
                mandate_target = missing[0]
        if mandate_target:
            target_space = mandate_target
        needs_reinforcement = legions[target_space] == 0 or (
            scenario["id"] == "S03"
            and target_space == "marcomannia"
            and legions[target_space] < 2
        )
        if needs_reinforcement:
            candidates = [space for space in SPACES if legions[space] > 0]
            if mandate_target:
                candidates = [space for space in candidates if space != target_space]
            if candidates:
                source = min(candidates, key=lambda space: len(route(space, target_space)))
                path = route(source, target_space)
                destination = path[min(2 if strength[urgent] >= 4 else 1, len(path) - 1)]
                reserve = 0
                if scenario["id"] == "S01" and source in ("lauriacum", "carnuntum", "sirmium"):
                    reserve = 1
                elif scenario["id"] == "S03" and source == "marcomannia":
                    reserve = 2
                elif scenario["id"] == "S07" and source in ("marcomannia", "quadi"):
                    reserve = 1
                moved = min(2, max(0, legions[source] - reserve))
                legions[source] -= moved
                legions[destination] += moved
                if scenario["id"] == "S03" and legions["marcomannia"] >= 2:
                    mandate = 1

        # Civil investment competes directly with a second military action.
        civil_need = min(tracks["rome"], tracks["senate"], tracks["resolve"], tracks["supply"])
        needs_mercy = mercy < scenario["objective"].get("mercy", 0)
        needs_senate = tracks["senate"] < scenario["objective"].get("senate", 0)
        needs_mandate = mandate < scenario["objective"].get("mandate", 0)
        civil = (
            (style == "civic" and rng.random() < 0.68)
            or (
                style == "adaptive"
                and (
                    civil_need <= 3 or needs_mercy or needs_senate
                    or (scenario["id"] in ("S04", "S05", "S06") and needs_mandate)
                )
            )
            or (style == "martial" and civil_need <= 2)
        )
        if civil:
            if coalition >= 2 and tracks["treasury"] > 0 and (
                style == "civic" or (style == "adaptive" and rng.random() < 0.55)
            ):
                tracks["treasury"] -= 1
                coalition = max(0, coalition - 2)
                if scenario["id"] == "S04" and strength["quadi"] <= 3:
                    mandate = min(2, mandate + 1)
            elif (needs_mercy or scenario["id"] == "S05") and tracks["senate"] > 1:
                eligible = [
                    front for front in FRONTS
                    if hosts[front] == front and strength[front] <= 1 and legions[front] > 0
                ]
                if eligible:
                    settled = min(eligible, key=lambda front: strength[front])
                    strength[settled] = 0
                    mercy = clamp(mercy + 1, 0, 6)
                    tracks["senate"] -= 1
                    if scenario["id"] == "S04" and settled == "quadi":
                        mandate = 2
                else:
                    tracks["resolve"] = clamp(tracks["resolve"] + 1)
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
                if legions[target_space] or any(
                    legions[n] and SPACES[n]["kind"] == "base"
                    for n in SPACES[target_space]["adjacent"]
                ):
                    strength[urgent] = max(0, strength[urgent] - 1)
        else:
            # Approximate the chosen card's Imperium half.
            if strength[urgent] >= 5 and tracks["supply"] > 0:
                tracks["supply"] -= 1
                strength[urgent] -= 1
            elif strength[urgent] >= 3:
                strength[urgent] -= 1

        if (
            scenario["id"] == "S06"
            and tracks["senate"] >= 5
            and not senate_five_awarded
        ):
            senate_five_awarded = True
            momentum += 2

        # A Command effect plus two Basic Orders can produce two campaigns.
        remaining = scenario["rounds"] - round_no
        need = scenario["objective"].get("momentum", 0) - momentum
        battles = 2 if style == "martial" and tracks["fatigue"] <= 3 else 1
        if style == "adaptive" and need > remaining and tracks["fatigue"] <= 3:
            battles = 2
        fought = False
        for _ in range(battles):
            engaged_hosts = [front for front in FRONTS if legions[hosts[front]] > 0 and strength[front] > 0]
            if not engaged_hosts:
                break
            urgent = max(
                engaged_hosts,
                key=lambda t: strength[t] - legions[hosts[t]] * 0.6
                + (5 if named_momentum[t] < named_objectives.get(t, 0) else 0),
            )
            should_fight = (
                strength[urgent] >= 2 or need >= remaining or style == "martial"
            )
            if not should_fight:
                break
            fought = True
            battle_space = hosts[urgent]
            committed = legions[battle_space]
            paid = max(0, committed - 1)
            if tracks["supply"] < paid:
                committed = max(1, tracks["supply"] + 1)
                paid = committed - 1
            tracks["supply"] -= paid
            expected_margin = committed + (0 if civil else 1) - strength[urgent]
            if (
                style == "martial" and committed >= 2 and tracks["fatigue"] <= 3
            ):
                doctrine = "force"
            elif expected_margin < -1:
                doctrine = "contain"
            else:
                doctrine = "set"
            exert = (
                doctrine == "set"
                and style in ("martial", "adaptive")
                and expected_margin < 1
                and tracks["fatigue"] <= 3
                and tracks["resolve"] > 2
            )
            command_bonus = 1 if not civil else 0
            base_support = (
                SPACES[battle_space]["kind"] == "base"
                and battle_space not in devastated
            ) or any(
                SPACES[n]["kind"] == "base"
                and n not in devastated
                and legions[n] > 0
                for n in SPACES[battle_space]["adjacent"]
            )
            roman_die = rng.randint(1, 6)
            enemy_die = rng.randint(1, 6)
            scenario_bonus = int(scenario["id"] == "S03" and urgent == "marcomannia")
            enemy_bonus = int(
                scenario["id"] == "S05" and urgent == "iazyges" and committed < 3
            )
            roman = (
                committed + roman_die + command_bonus + scenario_bonus
                + base_support + (2 if exert else 0)
                + (1 if doctrine == "contain" else 0)
                + (2 if doctrine == "force" else 0)
            )
            enemy = strength[urgent] + enemy_die + enemy_bonus
            tracks["fatigue"] += (0 if rng.random() < 0.22 else 1) + exert + (doctrine == "force")
            margin = roman - enemy
            if (
                scenario["id"] == "S04"
                and margin < 0
                and not rain_miracle_used
                and tracks["treasury"] > 0
            ):
                rain_miracle_used = True
                tracks["treasury"] -= 1
                roman = committed + 4 + command_bonus + scenario_bonus + base_support
                roman += (1 if doctrine == "contain" else 0) + (2 if doctrine == "force" else 0)
                enemy = strength[urgent] + 4 + enemy_bonus
                margin = roman - enemy
            if margin >= 3:
                strength[urgent] = max(0, strength[urgent] - 2)
                retreat(urgent, hosts, decisive=doctrine != "contain")
                if doctrine != "contain":
                    momentum += 1
                    named_momentum[urgent] += 1
            elif margin >= 0:
                strength[urgent] = max(0, strength[urgent] - 1)
                retreat(urgent, hosts)
                if doctrine != "contain":
                    momentum += 1
                    named_momentum[urgent] += 1
                if margin == 0:
                    tracks["supply"] -= 1
            elif margin >= -2:
                tracks["supply"] -= 1
                tracks["resolve"] -= 1
            else:
                legions[battle_space] -= 1
                tracks["rome"] -= 1
            if doctrine == "force" and margin <= 0:
                legions[battle_space] = max(0, legions[battle_space] - 1)

            if rng.random() < 0.45 and margin < 3:
                # Assent is used when the roll was genuinely exposed.
                if style == "civic" or (style == "adaptive" and needs_mercy):
                    mercy = clamp(mercy + 1, 0, 6)
                else:
                    tracks["resolve"] = clamp(tracks["resolve"] + 1)
            need = scenario["objective"].get("momentum", 0) - momentum

        active_host = crisis["host"]
        if active_host == "highest":
            active_host = max(
                FRONTS,
                key=lambda front: (
                    strength[front],
                    -len(route(hosts[front], "aquileia")),
                ),
            )
        coalition += activate_host(
            active_host, crisis["order"], strength, hosts, legions, tracks, devastated, rng
        )
        coalition += 1
        if coalition >= DATA.get("coalition_threshold", 4) and tracks["rome"] > 0:
            coalition = 0
            surge_host = max(
                [front for front in FRONTS if front != active_host],
                key=lambda front: (
                    strength[front],
                    -len(route(hosts[front], "aquileia")),
                ),
            )
            surge_order = (
                "muster"
                if hosts[surge_host] == surge_host and strength[surge_host] < 3
                else "raid"
            )
            coalition += activate_host(
                surge_host, surge_order, strength, hosts, legions, tracks, devastated, rng
            )
        if tracks["fatigue"] >= 5:
            tracks["resolve"] -= 1
        if scenario["id"] == "S08" and round_no + 1 in (3, 6):
            tracks["fatigue"] = max(0, tracks["fatigue"] - 2)
            tracks["supply"] = min(7, tracks["supply"] + 1)
            coalition = max(0, coalition - 2)
            lowest_state = min(("rome", "senate", "resolve"), key=lambda key: tracks[key])
            tracks[lowest_state] = min(7, tracks[lowest_state] + 1)
            strongest = max(FRONTS, key=lambda front: strength[front])
            strength[strongest] = min(6, strength[strongest] + 1)
        if scenario["id"] == "S08" and round_no + 1 == 8:
            tracks["resolve"] -= 1
        if style != "martial" and not fought:
            tracks["fatigue"] = max(0, tracks["fatigue"] - 1)

        if scenario["id"] == "S06" and civil and tracks["senate"] >= 5:
            mandate_flags.add(f"legitimacy-{round_no}")
            mandate = min(2, mandate + 1)
        if (
            scenario["id"] == "S07"
            and legions["marcomannia"] > 0
            and legions["quadi"] > 0
        ):
            mandate_flags.add(f"occupation-{round_no}")
            mandate = min(2, mandate + 1)
        if scenario["id"] == "S08":
            if (
                round_no + 1 >= 3
                and all(base not in devastated for base in ("aquileia", "virunum", "lauriacum"))
                and all(hosts[front] not in ("aquileia", "virunum", "lauriacum") for front in FRONTS)
            ):
                mandate_flags.add("defense")
            if round_no + 1 >= 6 and tracks["senate"] >= 4 and mercy >= 2:
                mandate_flags.add("state")
            if any(strength[front] == 0 for front in FRONTS):
                mandate_flags.add("treaty")
            mandate = len(mandate_flags)

        for key in tracks:
            tracks[key] = clamp(tracks[key], 0, 6 if key == "fatigue" else 7)
        if min(tracks["rome"], tracks["senate"], tracks["resolve"]) <= 0:
            break
        if sum(legions.values()) <= 0:
            break

    objective = scenario["objective"]
    total_threat = sum(strength.values())
    if scenario["id"] == "S01":
        mandate = sum(
            legions[base] > 0
            and base not in devastated
            and all(hosts[front] != base for front in FRONTS)
            for base in ("lauriacum", "carnuntum", "sirmium")
        )
    elif scenario["id"] == "S02":
        mandate = sum(
            base not in devastated and all(hosts[front] != base for front in FRONTS)
            for base in ("aquileia", "virunum", "lauriacum")
        )
    elif scenario["id"] == "S05":
        mandate = int(strength["iazyges"] <= 1 and mercy >= 3)
    won = (
        momentum >= objective.get("momentum", 0)
        and all(named_momentum[key] >= value for key, value in objective.get("named", {}).items())
        and total_threat <= objective.get("max_total_threat", 99)
        and tracks["senate"] >= objective.get("senate", 0)
        and tracks["resolve"] >= objective.get("resolve", 0)
        and mercy >= objective.get("mercy", 0)
        and mandate >= objective.get("mandate", 0)
        and min(tracks["rome"], tracks["senate"], tracks["resolve"]) > 0
        and "aquileia" not in hosts.values()
    )
    score = (
        momentum + tracks["rome"] + tracks["senate"] + tracks["resolve"]
        + tracks["treasury"] - tracks["fatigue"] - total_threat - len(devastated)
    )
    named_complete = all(
        named_momentum[key] >= value
        for key, value in objective.get("named", {}).items()
    )
    return Result(
        won, score, momentum, total_threat, sum(legions.values()),
        mandate, named_complete
    )


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
