# Contracts for the verifier decisions in docs/specs/snapshot.md, clarifier item 4
# (2026-10-21: F1, W1, W2, W3, N1). Written test-first against feat/snapshot-collector at
# b4b20bc. Fixtures and readers: test_snapshot_support.py; the B9 change detector comes from
# test_discover_output.py. Starting point: the verifier's repro tests (r1-r5).
#
# F1 same appid in two libraries (S2 naming)
#   Pre:  discover.scan returns two or more cards with the same appid (B6 keeps both).
#   Post: walking scan["games"] in order, the first card of an appid copies its entry n to
#         settings/<appid>/<n>_<basename>; the k-th card of that appid (k = 2, 3, ...) uses
#         settings/<appid>-<k>/<n>_<basename>. Each member holds that card's file, byte for
#         byte (round trip: copy into the zip, then extract, gives identical bytes).
#   Post: an appid with a single card never gets a "-<k>" folder.
#   Inv:  zip member names are never duplicated (zip_members asserts it).
#   Inv:  every such member has its own manifest added-file record naming its source.
#   Open: whether a card with installed false still takes a k number is not decided; not
#         tested here.
#
# W1 logs folder refused as out_dir (S8)
#   Pre:  out_dir, after realpath on both sides, is <home>/deckforge/logs or inside it.
#   Post: SnapshotError; nothing on disk changes (clarifier 3: checked before anything is
#         created); main() returns 2 with one line on stderr and nothing on stdout.
#   Post: the default <home>/deckforge/snapshots and a sibling such as
#         <home>/deckforge/logs-old stay allowed.
#
# W2 non-Steam shortcuts (S3)
#   Post: an all-digit entry under steamapps/compatdata or steamapps/shadercache of any
#         available library whose appid is >= 2147483648 is not in sizes.json "orphans"; it
#         is in a top-level "non_steam" list as {"path", "size"}, size summed like S3
#         (lstat, links not followed).
#   Post: 2147483647 with no card is still an orphan (boundary).
#   Post: the CLI "orphans found" count does not include non-Steam entries.
#   ASSUMED: "non_steam" is present (an empty list) when there are no shortcuts, like
#         "orphans".
#
# W3 linked or non-folder plugin entries (S4)
#   Post: each entry of <home>/homebrew/plugins that is a link (to a folder, to a file, or
#         dangling) or is not a folder adds an issue with code plugin_folder_not_regular and
#         path = str(<plugins_dir>/<entry name>). Plugin issues may sit in any JSON file of
#         the zip (support-file convention).
#   Post: regular plugin folders are still listed as before; a plain file is still not
#         listed as a plugin (existing S4 test).
#
# N1 bad out_dir
#   Pre:  out_dir exists as a file (or a link to a file), or cannot be created (a parent is
#         a file, a dangling link, or mkdir fails with an OS error such as EACCES).
#   Post: build_snapshot raises SnapshotError, not a raw OSError; no zip, no .partial,
#         nothing on disk changes outside what already existed.
#   Post: main() returns 2, one non-empty line on stderr, nothing on stdout, no traceback.

import errno
import os
from pathlib import Path

import pytest
from test_discover_output import libraryfolders, mkdir, put
from test_discover_output import snapshot as tree_state
from test_snapshot_support import (
    NOW,
    UNREAL,
    WILDS,
    ZIP_NAME,
    added_records,
    all_json,
    game,
    issues_in,
    make_deck,
    run,
    size_bounds,
    zip_json,
    zip_members,
)

from deckforge import snapshot

FIRST_SHORTCUT = 2147483648  # 2**31: the lowest non-Steam shortcut appid
LAST_STEAM = 2147483647  # 2**31 - 1: an ordinary appid, so an orphan without a card
EXCLUDED_KINDS = {"reg", "registry"}
UNREAL_CONFIG = "pfx/drive_c/users/steamuser/AppData/Local/Game/Saved/Config/Windows"


def cli_args(deck, out) -> list[str]:
    return ["--steam-root", str(deck.steam), "--home", str(deck.home), "--out-dir", str(out)]


# ---------------------------------------------------------------------------- F1


def add_unreal_copy(library: Path, tag: str) -> dict[str, bytes]:
    """A second install of UNREAL in `library`, with its own prefix ini files whose bytes
    name the library. Returns basename -> bytes."""
    install = game(library, UNREAL)
    put(install / "Game/Binaries/Win64/Game-Win64-Shipping.exe", b"MZ")
    config = library / "steamapps" / "compatdata" / str(UNREAL) / UNREAL_CONFIG
    files = {
        "Engine.ini": f"[SystemSettings]\n; copy in {tag}\n".encode(),
        "GameUserSettings.ini": f"[ScalabilityGroups]\n; copy in {tag}\r\n\xff".encode("latin-1"),
    }
    for name, data in files.items():
        put(config / name, data)
    return files


def expected_settings(scan: dict) -> dict[str, Path]:
    """F1 naming over scan["games"] order: zip name -> source path for every copyable
    entry of every installed card."""
    seen: dict[int, int] = {}
    expected: dict[str, Path] = {}
    for entry in scan["games"]:
        appid = entry["appid"]
        seen[appid] = seen.get(appid, 0) + 1
        folder = str(appid) if seen[appid] == 1 else f"{appid}-{seen[appid]}"
        if entry["installed"] is not True:
            continue
        for n, item in enumerate(entry["settings_files"]):
            source = Path(item["path"])
            if item["kind"] in EXCLUDED_KINDS or source.is_symlink() or not source.is_file():
                continue
            if source.stat().st_size > 1024 * 1024:
                continue
            expected[f"settings/{folder}/{n}_{source.name}"] = source
    return expected


def test_f1_same_appid_in_two_libraries_second_card_uses_appid_dash_2(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    add_unreal_copy(deck.steam, "root")
    zip_path = run(deck)
    members = zip_members(zip_path)  # asserts no duplicate member names
    scan = zip_json(members, "scan.json")
    cards = [entry for entry in scan["games"] if entry["appid"] == UNREAL]
    assert len(cards) == 2
    first, second = (Path(entry["library"]) for entry in cards)
    assert first != second

    names = sorted(name for name in members if name.startswith(f"settings/{UNREAL}"))
    assert names == sorted(
        [f"settings/{UNREAL}/{n}_{base}" for n, base in _unreal_indexes(cards[0])]
        + [f"settings/{UNREAL}-2/{n}_{base}" for n, base in _unreal_indexes(cards[1])]
    )
    for name, source in expected_settings(scan).items():
        if name.startswith(f"settings/{UNREAL}"):
            library = first if name.startswith(f"settings/{UNREAL}/") else second
            assert str(source).startswith(str(library) + os.sep), (name, source)


def _unreal_indexes(entry: dict) -> list[tuple[int, str]]:
    return [
        (n, Path(item["path"]).name)
        for n, item in enumerate(entry["settings_files"])
        if item["kind"] not in EXCLUDED_KINDS
    ]


def test_f1_round_trip_each_card_keeps_its_own_bytes(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    add_unreal_copy(deck.steam, "root")
    members = zip_members(run(deck))
    expected = expected_settings(zip_json(members, "scan.json"))
    dashed = [name for name in expected if name.startswith(f"settings/{UNREAL}-2/")]
    assert len(dashed) == 2
    settings = {name for name in members if name.startswith("settings/")}
    assert settings == set(expected)
    for name, source in expected.items():
        assert members[name] == source.read_bytes(), name


def test_f1_three_copies_use_appid_dash_2_and_dash_3(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    third = deck.base / "usb"
    mkdir(third / "steamapps")
    entries = [
        ("0", str(deck.steam)),
        ("1", str(deck.sd)),
        ("2", str(deck.base / "gone")),
        ("3", str(third)),
    ]
    put(deck.steam / "steamapps" / "libraryfolders.vdf", libraryfolders(entries))
    add_unreal_copy(deck.steam, "root")
    add_unreal_copy(third, "usb")
    members = zip_members(run(deck))
    scan = zip_json(members, "scan.json")
    assert sum(entry["appid"] == UNREAL for entry in scan["games"]) == 3
    folders = {name.split("/")[1] for name in members if name.startswith(f"settings/{UNREAL}")}
    assert folders == {str(UNREAL), f"{UNREAL}-2", f"{UNREAL}-3"}
    expected = expected_settings(scan)
    assert {name for name in members if name.startswith("settings/")} == set(expected)
    for name, source in expected.items():
        assert members[name] == source.read_bytes(), name


def test_f1_manifest_records_each_member_with_its_own_source(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    add_unreal_copy(deck.steam, "root")
    members = zip_members(run(deck))
    manifest = zip_json(members, "manifest.json")
    for name, source in expected_settings(zip_json(members, "scan.json")).items():
        records = added_records(manifest, name, source)
        assert len(records) == 1, name
        assert len(members[name]) in records[0].values()


def test_f1_single_card_appids_get_no_dash_folder(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    add_unreal_copy(deck.steam, "root")
    members = zip_members(run(deck))
    folders = {name.split("/")[1] for name in members if name.startswith("settings/")}
    assert str(WILDS) in folders
    assert not any(folder.startswith(f"{WILDS}-") for folder in folders)
    assert not any(folder.endswith("-1") for folder in folders)


# ---------------------------------------------------------------------------- W1


def _logs_itself(deck):
    return deck.logs_dir


def _inside_logs(deck):
    return deck.logs_dir / "snaps"


def _link_into_logs(deck):
    link = deck.base / "logslink"
    link.symlink_to(deck.logs_dir, target_is_directory=True)
    return link / "snaps"


def _dotdot_into_logs(deck):
    return Path(f"{deck.home}/deckforge/snapshots/../logs/x")


def _logs_folder_is_a_link(deck):
    """<home>/deckforge/logs is itself a link to a real folder elsewhere; out_dir is inside
    the real folder (realpath on both sides)."""
    real = deck.base / "real-logs"
    deck.logs_dir.rename(real)
    deck.logs_dir.symlink_to(real, target_is_directory=True)
    return real / "snaps"


LOGS_REFUSED = {
    "logs-itself": _logs_itself,
    "inside-logs": _inside_logs,
    "link-into-logs": _link_into_logs,
    "dotdot-into-logs": _dotdot_into_logs,
    "logs-folder-is-a-link": _logs_folder_is_a_link,
}


@pytest.mark.parametrize("case", sorted(LOGS_REFUSED))
def test_w1_out_dir_in_logs_folder_is_refused_and_nothing_changes(tmp_path, monkeypatch, case):
    deck = make_deck(tmp_path, monkeypatch)
    out = LOGS_REFUSED[case](deck)
    before = tree_state(deck.base)
    with pytest.raises(snapshot.SnapshotError):
        run(deck, out=out)
    assert tree_state(deck.base) == before


def test_w1_cli_out_dir_in_logs_returns_2_with_one_line(tmp_path, monkeypatch, capsys):
    deck = make_deck(tmp_path, monkeypatch)
    before = tree_state(deck.base)
    assert snapshot.main(cli_args(deck, deck.logs_dir / "snaps")) == 2
    assert tree_state(deck.base) == before
    captured = capsys.readouterr()
    assert captured.out == ""
    message = captured.err.strip()
    assert message != ""
    assert "\n" not in message
    assert "Traceback" not in message


@pytest.mark.parametrize("name", ["snapshots", "logs-old", "logs2"])
def test_w1_default_and_sibling_folders_next_to_logs_are_allowed(tmp_path, monkeypatch, name):
    deck = make_deck(tmp_path, monkeypatch)
    out = deck.home / "deckforge" / name
    assert run(deck, out=out) == out / ZIP_NAME


# ---------------------------------------------------------------------------- W2


def sizes_of(deck) -> dict:
    return zip_json(zip_members(run(deck)), "sizes.json")


def add_shortcuts(deck) -> dict[str, Path]:
    root, sd = deck.steam / "steamapps", deck.sd / "steamapps"
    return {
        "root_compat": put(
            root / "compatdata" / "3141592653" / "pfx/drive_c/users/steamuser/x.sav", b"s" * 300
        ).parents[4],
        "root_shader": put(
            root / "shadercache" / str(FIRST_SHORTCUT) / "fozpipelinesv6/a.foz", b"f" * 700
        ).parents[1],
        "sd_compat": put(sd / "compatdata" / "4294967295" / "pfx/x.bin", b"b" * 1500).parents[1],
        "sd_shader": put(sd / "shadercache" / "2500000000" / "a.foz", b"a" * 90).parent,
    }


def test_w2_non_steam_shortcut_entries_are_not_orphans(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    shortcuts = add_shortcuts(deck)
    sizes = sizes_of(deck)
    orphan_paths = [entry["path"] for entry in sizes["orphans"]]
    for folder in shortcuts.values():
        assert str(folder) not in orphan_paths
        assert not any(Path(path).name == folder.name for path in orphan_paths)


def test_w2_non_steam_list_holds_path_and_size_per_entry(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    shortcuts = add_shortcuts(deck)
    sizes = sizes_of(deck)
    assert isinstance(sizes.get("non_steam"), list)
    listed = {entry["path"]: entry["size"] for entry in sizes["non_steam"]}
    assert set(listed) == {str(folder) for folder in shortcuts.values()}
    for entry in sizes["non_steam"]:
        assert set(entry) == {"path", "size"}
    for folder in shortcuts.values():
        lower, upper = size_bounds(folder)
        assert lower <= listed[str(folder)] <= upper, folder


def test_w2_boundary_2147483647_is_an_orphan_and_2147483648_is_not(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    compat = deck.steam / "steamapps" / "compatdata"
    below = put(compat / str(LAST_STEAM) / "pfx" / "x", b"x").parents[1]
    at = put(compat / str(FIRST_SHORTCUT) / "pfx" / "x", b"x").parents[1]
    sizes = sizes_of(deck)
    orphan_paths = {entry["path"] for entry in sizes["orphans"]}
    non_steam = {entry["path"] for entry in sizes.get("non_steam", [])}
    assert str(below) in orphan_paths
    assert str(below) not in non_steam
    assert str(at) in non_steam
    assert str(at) not in orphan_paths


def test_w2_ordinary_orphans_are_unchanged_by_shortcuts(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    baseline = sorted(entry["path"] for entry in sizes_of(deck)["orphans"])
    assert len(baseline) == 3
    add_shortcuts(deck)
    after = zip_json(zip_members(run(deck, out=deck.base / "second")), "sizes.json")
    assert sorted(entry["path"] for entry in after["orphans"]) == baseline


def test_w2_cli_orphan_count_excludes_non_steam_shortcuts(tmp_path, monkeypatch, capsys):
    deck = make_deck(tmp_path, monkeypatch)
    add_shortcuts(deck)
    assert snapshot.main(cli_args(deck, deck.out)) == 0
    out = capsys.readouterr().out
    lines = [text for text in out.splitlines() if str(deck.base) not in text]
    line = [text for text in lines if "orphan" in text.lower()]
    assert len(line) == 1
    assert line[0].rstrip().endswith(" 3"), line[0]


def test_w2_non_steam_list_is_empty_without_shortcuts(tmp_path, monkeypatch):
    """ASSUMED shape: the list is always present, like "orphans"."""
    deck = make_deck(tmp_path, monkeypatch)
    assert sizes_of(deck).get("non_steam") == []


# ---------------------------------------------------------------------------- W3


def plugin_issues(deck) -> tuple[list, list[tuple[str, str | None]]]:
    members = zip_members(run(deck))
    issues = [issue for doc in all_json(members) for issue in issues_in(doc)]
    return zip_json(members, "plugins.json"), issues


def _link_to_folder(deck) -> Path:
    real = deck.base / "dev-plugin"
    put(real / "plugin.json", '{"name": "DevPlugin"}')
    put(real / "package.json", '{"version": "1.0"}')
    entry = deck.plugins_dir / "DevPlugin"
    entry.symlink_to(real, target_is_directory=True)
    return entry


def _link_to_file(deck) -> Path:
    entry = deck.plugins_dir / "FileLink"
    entry.symlink_to(put(deck.base / "some-file.txt", "x"))
    return entry


def _dangling_link(deck) -> Path:
    entry = deck.plugins_dir / "Gone"
    entry.symlink_to(deck.base / "no-such-plugin", target_is_directory=True)
    return entry


def _plain_file(deck) -> Path:
    return deck.plugins_dir / "README.md"  # already in the fixture


PLUGIN_ENTRIES = {
    "link-to-folder": _link_to_folder,
    "link-to-file": _link_to_file,
    "dangling-link": _dangling_link,
    "plain-file": _plain_file,
}


@pytest.mark.parametrize("case", sorted(PLUGIN_ENTRIES))
def test_w3_link_or_non_folder_plugin_entry_adds_plugin_folder_not_regular(
    tmp_path, monkeypatch, case
):
    deck = make_deck(tmp_path, monkeypatch)
    entry = PLUGIN_ENTRIES[case](deck)
    _, issues = plugin_issues(deck)
    assert ("plugin_folder_not_regular", str(entry)) in issues


def test_w3_every_odd_entry_gets_its_own_issue_and_regular_folders_stay(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    entries = [make(deck) for make in PLUGIN_ENTRIES.values()]
    plugins, issues = plugin_issues(deck)
    flagged = sorted(path for code, path in issues if code == "plugin_folder_not_regular")
    assert flagged == sorted(str(entry) for entry in entries)
    assert {"folder": "PowerTools", "name": "PowerTools", "version": "2.0.1"} in plugins
    assert {"folder": "SimpleDeckyTDP", "name": "SimpleDeckyTDP", "version": "0.7.3"} in plugins


def test_w3_regular_plugin_folders_add_no_plugin_folder_not_regular(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    _, issues = plugin_issues(deck)
    for folder in ["PowerTools", "SimpleDeckyTDP", "broken-package"]:
        assert ("plugin_folder_not_regular", str(deck.plugins_dir / folder)) not in issues


# ---------------------------------------------------------------------------- N1


def _out_is_a_file(deck) -> Path:
    return put(deck.home / "notadir", b"x")


def _out_is_a_link_to_a_file(deck) -> Path:
    link = deck.home / "filelink"
    link.symlink_to(put(deck.base / "target-file", b"x"))
    return link


def _out_below_a_file(deck) -> Path:
    return put(deck.home / "blocker", b"x") / "snapshots"


def _out_is_a_dangling_link(deck) -> Path:
    link = deck.home / "danglink"
    link.symlink_to(deck.base / "nowhere", target_is_directory=True)
    return link


BAD_OUT = {
    "out-is-a-file": _out_is_a_file,
    "out-is-a-link-to-a-file": _out_is_a_link_to_a_file,
    "out-below-a-file": _out_below_a_file,
    "out-is-a-dangling-link": _out_is_a_dangling_link,
}


@pytest.mark.parametrize("case", sorted(BAD_OUT))
def test_n1_bad_out_dir_raises_snapshot_error_and_changes_nothing(tmp_path, monkeypatch, case):
    deck = make_deck(tmp_path, monkeypatch)
    out = BAD_OUT[case](deck)
    before = tree_state(deck.base)
    with pytest.raises(snapshot.SnapshotError):
        run(deck, out=out)
    assert tree_state(deck.base) == before


def deny_mkdir(monkeypatch: pytest.MonkeyPatch, inside: Path) -> list[str]:
    """os.mkdir fails with EACCES for any path inside `inside` (the tests run as root, so
    chmod cannot refuse it). Path.mkdir and os.makedirs both end in os.mkdir."""
    refused: list[str] = []
    real_mkdir = os.mkdir
    top = os.path.realpath(inside)

    def mkdir_denied(path, *args, **kwargs):
        real = os.path.realpath(os.fspath(path))
        if real == top or real.startswith(top + os.sep):
            refused.append(real)
            raise PermissionError(errno.EACCES, os.strerror(errno.EACCES), os.fspath(path))
        return real_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(os, "mkdir", mkdir_denied)
    return refused


def test_n1_out_dir_that_cannot_be_created_raises_snapshot_error(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    out = deck.base / "locked" / "snapshots"
    deny_mkdir(monkeypatch, deck.base / "locked")
    before = tree_state(deck.base)
    with pytest.raises(snapshot.SnapshotError):
        run(deck, out=out)
    assert tree_state(deck.base) == before


@pytest.mark.parametrize("case", sorted(BAD_OUT))
def test_n1_cli_bad_out_dir_returns_2_with_one_line(tmp_path, monkeypatch, capsys, case):
    deck = make_deck(tmp_path, monkeypatch)
    out = BAD_OUT[case](deck)
    before = tree_state(deck.base)
    assert snapshot.main(cli_args(deck, out)) == 2
    assert tree_state(deck.base) == before
    captured = capsys.readouterr()
    assert captured.out == ""
    message = captured.err.strip()
    assert message != ""
    assert "\n" not in message
    assert "Traceback" not in message


def test_n1_cli_out_dir_that_cannot_be_created_returns_2(tmp_path, monkeypatch, capsys):
    deck = make_deck(tmp_path, monkeypatch)
    deny_mkdir(monkeypatch, deck.base / "locked")
    assert snapshot.main(cli_args(deck, deck.base / "locked" / "snapshots")) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.strip() != ""
    assert "\n" not in captured.err.strip()


def test_n1_good_out_dir_still_works_after_the_fix(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    assert run(deck, now=NOW) == deck.out / ZIP_NAME
