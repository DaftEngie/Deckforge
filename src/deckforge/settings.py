"""deckforge.settings: read a game's graphics settings through engine maps (read-only).

Spec: docs/specs/settings-read.md (S1-S10, clarifier answers 1-18, which win).

Maps are JSON files in the `maps` folder next to this module (S2, answer 9). Settings
files are read through snapshot._read_file: lstat first, regular files only, opened with
os.open and O_NOFOLLOW, at most 1 MiB (S1, answer 18). Registry files are never opened.
Nothing is written (S9).
"""

import argparse
import json
import logging
import math
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deckforge import discover
from deckforge.discover import _why
from deckforge.snapshot import _EXCLUDED_KINDS, _SETTINGS_CAP, _read_file, _Skip

MAPS_DIR = Path(__file__).resolve().parent / "maps"
TYPES = ("level", "percent", "enum", "bool", "number")
CONFIDENCES = ("documented", "matched", "likely")
NO_MAP_TEXT = "no map: change graphics settings in the game's menu"
ANTICHEAT_TEXT = "settings files only; DeckForge will never inject into this game"

_MAP_FIELDS = ("id", "engine", "label", "match", "knobs")
_MATCH_FIELDS = ("file_name", "sections", "keys")
_KNOB_FIELDS = ("id", "label", "section", "key", "type", "confidence", "source")
_UTF16_BOMS = (b"\xff\xfe", b"\xfe\xff")
_UTF8_BOM = b"\xef\xbb\xbf"
_ARRAY_PREFIXES = ("+", "-", ".", "!")
_PLAIN_INT = re.compile(r"-?[0-9]{1,9}")

_log = logging.getLogger("deckforge.settings")  # not __name__, which is __main__ under -m


class SettingsError(Exception):
    """A settings file or a map cannot be used (S1, S2, answer 9)."""


@dataclass(frozen=True)
class Ini:
    """A parsed INI file (S1): first value wins; repeated keys are in `duplicates`."""

    sections: dict[str, dict[str, str]]
    duplicates: list[tuple[str, str]]
    encoding: str


# ---------------------------------------------------------------------------- S1 INI


def read_ini(path: str | os.PathLike[str]) -> Ini:
    """S1, answers 10, 11, 14, 18: read and parse one settings file; raises SettingsError."""
    return _read_ini_checked(os.fspath(path))[0]


def _read_ini_checked(path: str) -> tuple[Ini, bool]:
    """S1 and answer 17: the Ini, and whether size or mtime (ns) changed while reading.
    "Before" is the lstat taken before opening, "after" the lstat taken after reading."""
    before = _stamp(path)
    try:
        data = _read_file(path, _SETTINGS_CAP)
    except _Skip as exc:
        _log.debug("settings file %s refused: %s", path, exc)
        raise SettingsError(f"{path}: {exc}") from exc
    text, encoding = _decode(path, data)
    ini = _parse(text, encoding)
    try:
        after = _stamp(path)
    except SettingsError:  # removed after reading: the values read are still reported
        return ini, True
    return ini, after != before


def _stamp(path: str) -> tuple[int, int]:
    """Size and mtime in ns from lstat (answer 17); SettingsError if lstat fails."""
    try:
        info = os.lstat(path)
    except OSError as exc:
        _log.debug("lstat failed for %s: %s", path, _why(exc))
        raise SettingsError(f"{path}: cannot check: {_why(exc)}") from exc
    return info.st_size, info.st_mtime_ns


def _decode(path: str, data: bytes) -> tuple[str, str]:
    """S1, answer 14: UTF-16 by BOM (no fallback), UTF-8 (BOM stripped), else Latin-1."""
    if data.startswith(_UTF16_BOMS):
        try:
            return data.decode("utf-16"), "utf-16"
        except UnicodeDecodeError as exc:
            _log.debug("bad UTF-16 in %s: %s", path, exc)
            raise SettingsError(f"{path}: UTF-16 BOM but invalid UTF-16: {exc.reason}") from exc
    encoding = "utf-8"
    if data.startswith(_UTF8_BOM):
        data, encoding = data[len(_UTF8_BOM) :], "utf-8-sig"
    try:
        return data.decode("utf-8"), encoding
    except UnicodeDecodeError:
        _log.debug("%s is not UTF-8; reading it as Latin-1", path)
        return data.decode("latin-1"), "latin-1"


def _parse(text: str, encoding: str) -> Ini:
    """S1 line rules, answers 10 and 11 (case kept, repeated sections merge, first wins)."""
    sections: dict[str, dict[str, str]] = {}
    duplicates: list[tuple[str, str]] = []
    current = ""
    for raw in text.split("\n"):
        line = raw.strip()
        if not line or line[0] in ";#":
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections.setdefault(current, {})
            continue
        if "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if key.startswith(_ARRAY_PREFIXES):
            continue
        section = sections.setdefault(current, {})
        if key in section:
            duplicates.append((current, key))
        else:
            section[key] = value
    return Ini(sections, duplicates, encoding)


# ---------------------------------------------------------------------------- S2 maps


def load_maps() -> list[dict[str, Any]]:
    """S2, S3, answer 9: the validated maps of MAPS_DIR/*.json, sorted by id."""
    paths = sorted(MAPS_DIR.glob("*.json"))
    if not paths:
        raise SettingsError(f"no maps (*.json) found in {MAPS_DIR}")
    maps: list[dict[str, Any]] = []
    seen: dict[str, str] = {}
    for path in paths:
        map_dict = _load_map(path)
        if map_dict["id"] in seen:
            raise SettingsError(
                f"{path.name}: duplicate map id {map_dict['id']!r} (also in {seen[map_dict['id']]})"
            )
        seen[map_dict["id"]] = path.name
        maps.append(map_dict)
    return sorted(maps, key=lambda m: m["id"])


def _load_map(path: Path) -> dict[str, Any]:
    """S2: one map file, parsed and validated; SettingsError names the file."""
    try:
        map_dict = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _log.debug("cannot load map %s: %s", path, exc)
        raise SettingsError(f"{path.name}: cannot load: {exc}") from exc
    problem = _map_problem(map_dict)
    if problem:
        raise SettingsError(f"{path.name}: {problem}")
    return map_dict


def _missing(obj: Any, fields: tuple[str, ...], where: str) -> str | None:
    """S2: the first missing field of `obj`, or None."""
    if not isinstance(obj, dict):
        return f"{where} is not an object"
    for name in fields:
        if name not in obj:
            return f"{where} is missing field {name!r}"
    return None


def _map_problem(map_dict: Any) -> str | None:
    """S2: what is wrong with a map, or None."""
    problem = _missing(map_dict, _MAP_FIELDS, "map") or _missing(
        map_dict["match"], _MATCH_FIELDS, "match"
    )
    if problem:
        return problem
    if not isinstance(map_dict["knobs"], list):
        return "knobs is not a list"
    ids: set[Any] = set()
    for n, knob in enumerate(map_dict["knobs"]):
        problem = _knob_problem(knob, f"knob {n}")
        if problem:
            return problem
        if knob["id"] in ids:
            return f"duplicate knob id {knob['id']!r}"
        ids.add(knob["id"])
    return None


def _knob_problem(knob: Any, where: str) -> str | None:
    """S2, answer 1: what is wrong with one knob, or None."""
    problem = _missing(knob, _KNOB_FIELDS, where)
    if problem:
        return problem
    where = f"knob {knob['id']!r}"
    if knob["type"] not in TYPES:
        return f"{where} has unknown type {knob['type']!r}"
    if knob["confidence"] not in CONFIDENCES:
        return f"{where} has unknown confidence {knob['confidence']!r}"
    if not isinstance(knob["source"], str) or not knob["source"].strip():
        return f"{where} has an empty source"
    if knob["type"] in ("level", "enum", "bool"):
        values = knob.get("values")
        if not isinstance(values, list) or not values:
            return f"{where} of type {knob['type']} has no values"
    if knob["type"] == "percent":
        low, high = knob.get("min"), knob.get("max")
        if not _is_number(low) or not _is_number(high) or low > high:
            return f"{where} of type percent needs min <= max (min={low!r}, max={high!r})"
    return None


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


# ---------------------------------------------------------------------------- S4 match


def match_maps(ini: Ini, file_name: str, maps: list[dict[str, Any]]) -> list[str]:
    """S4, answers 10 and 15: ids of the maps whose whole fingerprint holds."""
    return [m["id"] for m in maps if _matches(ini, file_name, m["match"])]


def _matches(ini: Ini, file_name: str, match: dict[str, Any]) -> bool:
    """S2 `match`: file name ignoring case; sections and keys exact (answer 10)."""
    if file_name.casefold() != match["file_name"].casefold():
        return False
    if not all(section in ini.sections for section in match["sections"]):
        return False
    return all(key in ini.sections.get(section, {}) for section, key in match["keys"])


# ---------------------------------------------------------------------------- S5 report


def read_settings(card: dict[str, Any], maps: list[dict[str, Any]]) -> dict[str, Any]:
    """S5-S7, answers 6, 8, 12, 14, 16, 17: the report for one installed scan card."""
    entries: list[dict[str, Any]] = []
    unmapped: list[str] = []
    issues: list[dict[str, Any]] = []
    tried = failed = 0
    by_id = {m["id"]: m for m in maps}
    for item in card["settings_files"]:
        path = item["path"]
        if item["kind"] in _EXCLUDED_KINDS:
            issues.append({"code": "registry_not_read", "path": path})
            continue
        tried += 1
        try:
            ini, changed = _read_ini_checked(path)
        except SettingsError as exc:
            failed += 1
            issues.append({"code": "settings_unreadable", "path": path, "why": str(exc)})
            continue
        if changed:
            issues.append({"code": "changed_during_read", "path": path})
        ids = match_maps(ini, Path(path).name, maps)
        if not ids:
            unmapped.append(path)
        entries += [_entry(by_id[map_id], path, ini) for map_id in ids]
    issues += _conflicts(entries)
    return {
        "appid": card["appid"],
        "name": card["name"],
        "engine": card["engine"],
        "anticheat": card["anticheat"],
        "status": _status(entries, tried, failed),
        "maps": entries,
        "unmapped_files": unmapped,
        "issues": issues,
    }


def _entry(map_dict: dict[str, Any], path: str, ini: Ini) -> dict[str, Any]:
    """S5, answer 8: one map entry for one settings file."""
    return {
        "map_id": map_dict["id"],
        "file": path,
        "encoding": ini.encoding,
        "duplicates": [[section, key] for section, key in ini.duplicates],
        "knobs": [_knob_report(knob, ini) for knob in map_dict["knobs"]],
    }


def _knob_report(knob: dict[str, Any], ini: Ini) -> dict[str, Any]:
    """S5, answers 7 and 8: one knob as read; only the knob's own section is used."""
    value = ini.sections.get(knob["section"], {}).get(knob["key"])
    return {
        "id": knob["id"],
        "label": knob["label"],
        "section": knob["section"],
        "key": knob["key"],
        "type": knob["type"],
        "present": value is not None,
        "value": value,
        "known": value is not None and _is_known(knob, value),
        "confidence": knob["confidence"],
    }


def _is_known(knob: dict[str, Any], value: str) -> bool:
    """S5, answers 1, 10, 13: is `value` one the map knows?"""
    if knob["type"] == "percent":
        if not _PLAIN_INT.fullmatch(value):
            return False
        return knob["min"] <= int(value) <= knob["max"]
    if knob["type"] == "number":
        try:
            number = float(value)
        except ValueError:
            return False
        low, high = knob.get("min"), knob.get("max")
        in_low = low is None or number >= low
        in_high = high is None or number <= high
        return math.isfinite(number) and in_low and in_high
    return value in knob["values"]


def _conflicts(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Answer 12: one issue per knob present with different values in two files of a map,
    naming the first file (card order) where it is present."""
    first: dict[tuple[str, str], tuple[str, str]] = {}
    issues: list[dict[str, Any]] = []
    flagged: set[tuple[str, str]] = set()
    for item in entries:
        for knob in item["knobs"]:
            if not knob["present"]:
                continue
            where = (item["map_id"], knob["id"])
            seen = first.setdefault(where, (item["file"], knob["value"]))
            if seen[1] != knob["value"] and where not in flagged:
                flagged.add(where)
                issues.append(
                    {
                        "code": "conflicting_files",
                        "path": seen[0],
                        "map_id": item["map_id"],
                        "knob": knob["id"],
                    }
                )
    return issues


def _status(entries: list[dict[str, Any]], tried: int, failed: int) -> str:
    """S6, answer 6: the first status rule that holds."""
    if not entries:
        return "unreadable" if tried and failed == tried else "no_map"
    present = [k for item in entries for k in item["knobs"] if k["present"]]
    if not present:
        return "mapped_empty"
    if not all(k["known"] for k in present):
        return "mapped_with_unknown_values"
    return "mapped"


# ---------------------------------------------------------------------------- S8 CLI


def main(argv: list[str] | None = None) -> int:
    """S8: report installed games as text or JSON; 2 on SettingsError or DiscoverError."""
    parser = argparse.ArgumentParser(
        prog="deckforge.settings",
        description="Show the graphics settings DeckForge understands for each game (read-only).",
        allow_abbrev=False,
    )
    parser.add_argument("--steam-root", required=True, help="the Steam folder to scan")
    parser.add_argument("--appid", type=int, action="append", help="only this game (repeatable)")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = parser.parse_args(argv)
    try:
        reports = _reports(args.steam_root, args.appid)
    except (SettingsError, discover.DiscoverError) as exc:
        message = " ".join(str(exc).split())
        sys.stderr.write(f"deckforge.settings: {message}\n")
        return 2
    if args.json:
        sys.stdout.write(json.dumps(reports, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write("".join(_text_block(report) for report in reports))
    return 0


def _reports(steam_root: str, appids: list[int] | None) -> list[dict[str, Any]]:
    """S8: the reports of the installed cards (or the listed appids), sorted by appid."""
    maps = load_maps()
    cards = [card for card in discover.scan(steam_root)["games"] if card["installed"]]
    if appids:
        installed = {card["appid"] for card in cards}
        missing = [str(appid) for appid in appids if appid not in installed]
        if missing:
            raise SettingsError(f"appid not installed: {', '.join(missing)}")
        tools = [str(c["appid"]) for c in cards if c["appid"] in appids and c["kind"] != "game"]
        if tools:
            raise SettingsError(f"appid is a tool, not a game: {', '.join(tools)}")
        cards = [card for card in cards if card["appid"] in appids]
    cards = [card for card in cards if card["kind"] == "game"]
    cards.sort(key=lambda card: card["appid"])
    return [read_settings(card, maps) for card in cards]


def _text_block(report: dict[str, Any]) -> str:
    """S6-S8: one text block per game; present knobs as `label: value`, `(?)` if unknown."""
    lines = [f"{report['name']} ({report['appid']}): {report['status']}"]
    if report["anticheat"]:
        lines.append(f"  {ANTICHEAT_TEXT}")
    if report["status"] == "no_map":
        lines.append(f"  {NO_MAP_TEXT}")
    for item in report["maps"]:
        lines.append(f"  map {item['map_id']} ({Path(item['file']).name})")
        for knob in item["knobs"]:
            if knob["present"]:
                mark = "" if knob["known"] else " (?)"
                lines.append(f"    {knob['label']}: {knob['value']}{mark}")
    for path in report["unmapped_files"]:
        lines.append(f"  unmapped file: {Path(path).name}")
    for issue in report["issues"]:
        lines.append(f"  issue {issue['code']}: {Path(issue['path']).name}")
    return "\n".join(lines) + "\n\n"


if __name__ == "__main__":
    raise SystemExit(main())
