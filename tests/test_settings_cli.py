# Contracts for deckforge.settings.main and the module's read-only guarantee
# (docs/specs/settings-read.md, S6-S9, with clarifier answers 6 and 8).
#
# main(argv=None) -> int
#   Pre:  argv is a list of str, or None to read sys.argv[1:]. --steam-root is required;
#         --appid takes an int and may repeat; --json switches the output.
#   Post: runs deckforge.discover.scan(steam_root) and reports every installed card, or only
#         the listed appids. Cards with installed false are never reported. ASSUMED: the
#         fixture has no tool cards (Proton), because the spec does not say whether
#         "every installed game" includes kind "tool".
#   Post: --json: stdout is exactly json.dumps(reports, indent=2, sort_keys=True) + "\n",
#         reports sorted by appid, each equal to read_settings(card, load_maps()) for its
#         card (the S5 report with status, answer 8 key sets).
#   Post: text: one block per game holding its name once, its status, the id of each
#         matched map and one line per present knob, "label: value", with "(?)" when the
#         value is not known; absent knobs get no line. A no_map game shows "no map: change
#         graphics settings in the game's menu" (S6). A game with a non-empty anticheat
#         list shows "settings files only; DeckForge will never inject into this game"
#         (S7); others do not. Blocks are found by the game names; their order is not
#         specified.
#   Post: returns 0 on success, also when games are no_map or unreadable.
#   Post: SettingsError or DiscoverError -> exactly one line on stderr, nothing on stdout,
#         returns 2. An --appid that is not installed (unknown, or installed false) is the
#         same, and the line names the appid.
#   Post: argparse errors (no --steam-root, non-int --appid) exit with SystemExit(2).
#   Post: any other exception propagates (R12).
#   Inv:  `python -m deckforge.settings` runs main and exits with its code.
#
# Read-only, S9 (main in both modes and read_settings)
#   Inv:  the fixture tree is byte-for-byte unchanged, every lstat field (mode, size, mtime,
#         ctime, inode, links, link target) included; nothing is created in the cwd; no
#         logging handler is added to any logger.
#   Inv:  the only files opened are the scan's three kinds, the maps' JSON files, and the
#         non-registry settings files on installed cards, all read-only. Registry files are
#         never opened.
#   Property (in place of a write/restore round trip, as this module has no write path):
#   any number of runs over each fixture tree leaves it as it was.

import json
import logging
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
from test_discover_output import kind_of_opened, record_opens
from test_discover_output import snapshot as tree_state
from test_settings_support import (
    AC_GAME,
    ANTICHEAT_TEXT,
    BIG,
    DD2,
    GAME_KEYS,
    ISSUE_KEYS,
    KNOB_KEYS,
    MAP_ENTRY_KEYS,
    MAPS_DIR,
    NAMES,
    NO_MAP_TEXT,
    PENDING,
    PLAIN,
    RE_APPOPTION,
    RE_GRAPHICS,
    REMATCH,
    REMATCH_VALUES,
    SPARKING,
    SPARKING_VALUES,
    SRC,
    TREE_STATUS,
    UNITY_GAME,
    UNREAL,
    WILDS,
    WILDS_KNOBS,
    build_tree,
    builtin_map,
    by_key,
    copy_package,
    main_in,
    map_knob,
    minimal_root,
    only_entry,
    unmapped_paths,
)

from deckforge import discover, settings

REAL_SCAN = discover.scan
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
SG = "ScalabilityGroups"


class Boom(Exception):
    """An unexpected failure that main must not catch."""


@pytest.fixture
def tree(tmp_path) -> dict:
    return build_tree(tmp_path / "data")


def run_main(argv: list[str], capsys) -> tuple[int, str, str]:
    code = settings.main(argv)
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def json_reports(tree: dict, capsys, *extra: str) -> list[dict]:
    code, out, err = run_main(["--steam-root", str(tree["root"]), "--json", *extra], capsys)
    assert code == 0, err
    return json.loads(out)


def text_blocks(text: str, appids) -> dict[int, str]:
    """Split the text output at the game names (each must occur exactly once)."""
    starts = []
    for appid in appids:
        name = NAMES[appid]
        assert text.count(name) == 1, f"{name!r} occurs {text.count(name)} times"
        starts.append((text.index(name), appid))
    starts.sort()
    blocks = {}
    for n, (start, appid) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(text)
        blocks[appid] = text[start:end]
    return blocks


def has_word(block: str, word: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", block) is not None


def knob_lines(block: str, label: str) -> list[str]:
    return [line.strip() for line in block.splitlines() if line.strip().startswith(f"{label}: ")]


def assert_knob_line(block: str, label: str, value: str, known: bool) -> None:
    pattern = re.compile(rf"^{re.escape(label)}: {re.escape(value)}(?:\s|$)")
    lines = [line for line in knob_lines(block, label) if pattern.match(line)]
    assert len(lines) >= 1, f"no line '{label}: {value}' in:\n{block}"
    for line in lines:
        assert ("(?)" in line) is (not known), line


def patch_scan(monkeypatch: pytest.MonkeyPatch, fake) -> None:
    monkeypatch.setattr(discover, "scan", fake)
    if getattr(settings, "scan", None) is REAL_SCAN:
        monkeypatch.setattr(settings, "scan", fake)


# ---------------------------------------------------------------------------- S8 JSON


def test_s8_json_lists_installed_games_sorted_by_appid_with_status(tree, capsys):
    code, out, err = run_main(["--steam-root", str(tree["root"]), "--json"], capsys)
    assert code == 0, err
    reports = json.loads(out)
    assert out == json.dumps(reports, indent=2, sort_keys=True) + "\n"
    assert [r["appid"] for r in reports] == sorted(TREE_STATUS)
    assert {r["appid"]: r["status"] for r in reports} == TREE_STATUS
    assert PENDING not in [r["appid"] for r in reports]
    assert err == ""


def test_s8_json_reports_equal_read_settings_of_each_card(tree, capsys):
    maps = settings.load_maps()
    cards = sorted(
        (card for card in discover.scan(str(tree["root"]))["games"] if card["installed"]),
        key=lambda card: card["appid"],
    )
    expected = [settings.read_settings(card, maps) for card in cards]
    _, out, _ = run_main(["--steam-root", str(tree["root"]), "--json"], capsys)
    assert out == json.dumps(expected, indent=2, sort_keys=True) + "\n"


def test_a8_json_key_sets_are_frozen(tree, capsys):
    reports = json_reports(tree, capsys)
    issue_codes = set()
    for report in reports:
        assert set(report) == GAME_KEYS
        for item in report["maps"]:
            assert set(item) == MAP_ENTRY_KEYS
            for knob in item["knobs"]:
                assert set(knob) == KNOB_KEYS
        for issue in report["issues"]:
            assert set(issue) == ISSUE_KEYS[issue["code"]], issue
            issue_codes.add(issue["code"])
    assert issue_codes == {"registry_not_read", "settings_unreadable"}


def test_s7_a8_json_copies_engine_and_anticheat_from_the_cards(tree, capsys):
    cards = {card["appid"]: card for card in discover.scan(str(tree["root"]))["games"]}
    for report in json_reports(tree, capsys):
        card = cards[report["appid"]]
        assert report["engine"] == card["engine"]
        assert report["anticheat"] == card["anticheat"]
        assert report["name"] == NAMES[report["appid"]]
    assert [a["system"] for a in cards[AC_GAME]["anticheat"]] == ["easyanticheat"]


def test_s10_json_real_games(tree, capsys):
    reports = {r["appid"]: r for r in json_reports(tree, capsys)}
    files = tree["files"]
    wilds = only_entry(reports[WILDS], RE_GRAPHICS)
    assert wilds["file"] == str(files["wilds"])
    assert {pair: k["value"] for pair, k in by_key(wilds).items()} == WILDS_KNOBS
    assert [m["map_id"] for m in reports[DD2]["maps"]] == [RE_APPOPTION]
    sparking = by_key(only_entry(reports[SPARKING], UNREAL))
    assert {key: sparking[(SG, key)]["value"] for key in SPARKING_VALUES} == SPARKING_VALUES
    assert unmapped_paths(reports[SPARKING]) == [str(files["sparking_engine"])]
    rematch = by_key(only_entry(reports[REMATCH], UNREAL))
    assert {key for (_, key), k in rematch.items() if k["present"]} == set(REMATCH_VALUES)


def test_s5_json_issues_for_registry_and_unreadable_games(tree, capsys):
    reports = {r["appid"]: r for r in json_reports(tree, capsys)}
    files = tree["files"]
    assert reports[UNITY_GAME]["issues"] == [
        {"code": "registry_not_read", "path": str(files["unity_reg"])}
    ]
    assert unmapped_paths(reports[UNITY_GAME]) == [str(files["unity_boot"])]
    big = reports[BIG]["issues"]
    assert [(i["code"], i["path"]) for i in big] == [("settings_unreadable", str(files["big"]))]
    assert reports[PLAIN]["issues"] == []
    assert reports[PLAIN]["maps"] == []


def test_s8_appid_filter_reports_only_the_listed_games(tree, capsys):
    reports = json_reports(tree, capsys, "--appid", str(WILDS), "--appid", str(REMATCH))
    assert [r["appid"] for r in reports] == [REMATCH, WILDS]


def test_s8_appid_filter_in_text_mode(tree, capsys):
    code, out, _ = run_main(["--steam-root", str(tree["root"]), "--appid", str(DD2)], capsys)
    assert code == 0
    assert NAMES[DD2] in out
    for appid in TREE_STATUS:
        if appid != DD2:
            assert NAMES[appid] not in out


@pytest.mark.parametrize("appid", [PENDING, 999999], ids=["installed-false", "unknown"])
@pytest.mark.parametrize("mode", [[], ["--json"]], ids=["text", "json"])
def test_s8_appid_not_installed_exits_2_naming_it(tree, capsys, appid, mode):
    argv = ["--steam-root", str(tree["root"]), "--appid", str(WILDS), "--appid", str(appid)]
    code, out, err = run_main(argv + mode, capsys)
    assert code == 2
    assert out == ""
    assert len(err.splitlines()) == 1
    assert str(appid) in err


# ---------------------------------------------------------------------------- S8 text


def test_s6_s8_text_blocks_show_name_status_and_maps(tree, capsys):
    code, out, err = run_main(["--steam-root", str(tree["root"])], capsys)
    assert code == 0, err
    assert NAMES[PENDING] not in out
    blocks = text_blocks(out, TREE_STATUS)
    for appid, status in TREE_STATUS.items():
        assert has_word(blocks[appid], status), f"{status} missing for {NAMES[appid]}"
        for other in set(TREE_STATUS.values()) - {status}:
            assert not has_word(blocks[appid], other), f"{other} shown for {NAMES[appid]}"
    for appid, map_id in [
        (WILDS, RE_GRAPHICS),
        (DD2, RE_APPOPTION),
        (SPARKING, UNREAL),
        (REMATCH, UNREAL),
        (AC_GAME, UNREAL),
    ]:
        assert map_id in blocks[appid]


def test_s6_text_no_map_games_point_to_the_game_menu(tree, capsys):
    _, out, _ = run_main(["--steam-root", str(tree["root"])], capsys)
    blocks = text_blocks(out, TREE_STATUS)
    for appid in (PLAIN, UNITY_GAME):
        assert NO_MAP_TEXT in blocks[appid]
    for appid in (WILDS, DD2, SPARKING, REMATCH, AC_GAME):
        assert NO_MAP_TEXT not in blocks[appid]


def test_s7_text_anticheat_line_only_for_anticheat_games(tree, capsys):
    _, out, _ = run_main(["--steam-root", str(tree["root"])], capsys)
    blocks = text_blocks(out, TREE_STATUS)
    assert ANTICHEAT_TEXT in blocks[AC_GAME]
    for appid in TREE_STATUS:
        if appid != AC_GAME:
            assert ANTICHEAT_TEXT not in blocks[appid]


def test_s8_text_present_knobs_as_label_value(tree, capsys):
    maps = settings.load_maps()
    unreal = builtin_map(maps, UNREAL)
    _, out, _ = run_main(["--steam-root", str(tree["root"])], capsys)
    blocks = text_blocks(out, TREE_STATUS)
    for key, value in SPARKING_VALUES.items():
        assert_knob_line(blocks[SPARKING], map_knob(unreal, SG, key)["label"], value, True)
    wilds = builtin_map(maps, RE_GRAPHICS)
    for (section, key), value in WILDS_KNOBS.items():
        assert_knob_line(blocks[WILDS], map_knob(wilds, section, key)["label"], value, True)


def test_s8_text_absent_knobs_are_not_shown(tree, capsys):
    unreal = builtin_map(settings.load_maps(), UNREAL)
    _, out, _ = run_main(["--steam-root", str(tree["root"])], capsys)
    block = text_blocks(out, TREE_STATUS)[REMATCH]
    present = {map_knob(unreal, SG, key)["label"] for key in REMATCH_VALUES}
    for key, value in REMATCH_VALUES.items():
        assert_knob_line(block, map_knob(unreal, SG, key)["label"], value, True)
    for k in unreal["knobs"]:
        if k["key"] not in REMATCH_VALUES and k["label"] not in present:
            assert knob_lines(block, k["label"]) == [], k["key"]


def test_s8_text_unknown_values_are_marked(tree, capsys):
    unreal = builtin_map(settings.load_maps(), UNREAL)
    _, out, _ = run_main(["--steam-root", str(tree["root"])], capsys)
    block = text_blocks(out, TREE_STATUS)[AC_GAME]
    label = {key: map_knob(unreal, SG, key)["label"] for key in UNREAL_KEYS_IN_AC}
    assert_knob_line(block, label["sg.ResolutionQuality"], "100.000000", False)
    assert_knob_line(block, label["sg.ShadowQuality"], "7", False)
    assert_knob_line(block, label["sg.TextureQuality"], "2", True)


UNREAL_KEYS_IN_AC = ["sg.ResolutionQuality", "sg.ShadowQuality", "sg.TextureQuality"]


# ---------------------------------------------------------------------------- S8 errors


def test_s8_missing_steam_root_exits_2(capsys):
    with pytest.raises(SystemExit) as caught:
        settings.main(["--json"])
    assert caught.value.code == 2
    assert capsys.readouterr().out == ""


def test_s8_non_integer_appid_exits_2(tree, capsys):
    with pytest.raises(SystemExit) as caught:
        settings.main(["--steam-root", str(tree["root"]), "--appid", "wilds"])
    assert caught.value.code == 2


@pytest.mark.parametrize("mode", [[], ["--json"]], ids=["text", "json"])
def test_s8_discover_error_returns_2_with_one_stderr_line(tmp_path, capsys, mode):
    (tmp_path / "steam" / "steamapps").mkdir(parents=True)
    code, out, err = run_main(["--steam-root", str(tmp_path / "steam"), *mode], capsys)
    assert code == 2
    assert out == ""
    assert len(err.splitlines()) == 1
    assert err.strip()


@pytest.mark.parametrize(
    "maps",
    [{}, {"broken.json": {"id": "broken"}}],
    ids=["zero-maps", "invalid-map"],
)
def test_s8_settings_error_returns_2_with_one_stderr_line(tmp_path, maps):
    pkg = copy_package(tmp_path, maps)
    root = minimal_root(tmp_path / "data")
    done = main_in(pkg, ["--steam-root", str(root), "--json"], tmp_path)
    assert done.returncode == 2, done.stderr
    assert done.stdout == ""
    assert len(done.stderr.splitlines()) == 1
    assert "Traceback" not in done.stderr


def test_s8_other_exceptions_propagate(tree, monkeypatch, capsys):
    def explode(*args, **kwargs):
        raise Boom("unexpected")

    patch_scan(monkeypatch, explode)
    with pytest.raises(Boom):
        settings.main(["--steam-root", str(tree["root"])])


def test_s8_main_without_argv_reads_sys_argv(tree, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["settings", "--steam-root", str(tree["root"]), "--json"])
    assert settings.main() == 0
    assert [r["appid"] for r in json.loads(capsys.readouterr().out)] == sorted(TREE_STATUS)


def test_s8_module_runs_main_as_a_script(tree, tmp_path):
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    done = subprocess.run(
        [sys.executable, "-B", "-m", "deckforge.settings", "--steam-root", str(tree["root"])],
        cwd=cwd,
        env={**os.environ, "PYTHONPATH": str(SRC)},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    assert NAMES[WILDS] in done.stdout
    assert list(cwd.iterdir()) == []


# ---------------------------------------------------------------------------- S9 read-only


def handler_state() -> dict[str, list]:
    loggers = [logging.getLogger()]
    loggers += [
        logger
        for logger in logging.Logger.manager.loggerDict.values()
        if isinstance(logger, logging.Logger)
    ]
    return {logger.name: list(logger.handlers) for logger in loggers}


TREES = {
    "nine-games": lambda base: build_tree(base)["root"],
    "one-unreal-game": minimal_root,
}


@pytest.mark.parametrize("shape", sorted(TREES))
def test_s9_runs_change_nothing_and_add_no_logging_handlers(tmp_path, monkeypatch, capsys, shape):
    root = TREES[shape](tmp_path / "data")
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    before = tree_state(tmp_path)
    handlers = handler_state()
    maps = settings.load_maps()
    for _ in range(2):
        assert settings.main(["--steam-root", str(root)]) == 0
        assert settings.main(["--steam-root", str(root), "--json"]) == 0
        for card in discover.scan(str(root))["games"]:
            if card["installed"]:
                settings.read_settings(card, maps)
    capsys.readouterr()
    assert tree_state(tmp_path) == before
    after = handler_state()
    for name, current in after.items():
        assert current == handlers.get(name, []), f"logger {name!r} got a handler"


def test_s9_only_allowed_files_are_opened_read_only(tree, monkeypatch, capsys):
    root = tree["root"]
    cards = discover.scan(str(root))["games"]
    allowed = {
        os.path.realpath(item["path"])
        for card in cards
        if card["installed"]
        for item in card["settings_files"]
        if item["kind"] not in ("reg", "registry")
    }
    registry = {
        os.path.realpath(item["path"])
        for card in cards
        for item in card["settings_files"]
        if item["kind"] in ("reg", "registry")
    }
    assert registry, "the fixture must have a registry file"
    maps_dir = os.path.realpath(MAPS_DIR)
    with monkeypatch.context() as patch:
        seen = record_opens(patch)
        assert settings.main(["--steam-root", str(root), "--json"]) == 0
    capsys.readouterr()
    opened_settings = set()
    for route, file, mode in seen:
        if not isinstance(file, str | bytes | os.PathLike):
            continue
        real = os.path.realpath(os.fsdecode(file))
        assert real not in registry, f"{route} opened a registry file {real}"
        if route == "os.open":
            assert mode & WRITE_FLAGS == 0, f"os.open flags {mode:#o} for {real}"
        else:
            assert mode in ("r", "rb"), f"{route} mode {mode!r} for {real}"
        if real in allowed:
            opened_settings.add(real)
            continue
        if str(Path(real).parent) == maps_dir and real.endswith(".json"):
            continue
        assert kind_of_opened(file, root, [root]) is not None, f"{route} opened {real}"
    assert os.path.realpath(tree["files"]["pending"]) not in opened_settings
    # The oversized file may be refused by its lstat size before any open.
    assert allowed - {os.path.realpath(tree["files"]["big"])} <= opened_settings


def test_s9_the_cli_writes_nothing_in_the_cwd(tree, tmp_path, monkeypatch, capsys):
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    settings.main(["--steam-root", str(tree["root"]), "--json"])
    capsys.readouterr()
    assert list(Path(cwd).iterdir()) == []
