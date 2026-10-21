# Contracts for deckforge.snapshot (docs/specs/snapshot.md): S3 sizes and orphans, S4 Decky
# plugins, S5 frame-time logs, S6 system facts. Written test-first: src/deckforge/snapshot.py
# does not exist yet. Fixtures, readers and the assumed sizes.json shape:
# test_snapshot_support.py.
#
# S3 sizes.json
#   Post: one entry per scan card (appid, library) with the total byte size of its
#         shadercache_path and of <library>/steamapps/compatdata/<appid> (the card's own
#         library, as written), or null when the folder is absent.
#   Post: sizes walk with os.scandir and lstat and never follow links: a size lies between
#         the regular files' total and the total of every entry's lstat size, so a link to a
#         3 MiB file or folder outside adds at most the link's own size.
#   Post: orphans = every all-digit entry under shadercache and compatdata of each available
#         library whose appid has no card in scan.json (in any library), with path and size.
#         Non-digit names are ignored; a compatdata folder whose card sits in another
#         library is not an orphan.
#   Post: a folder that cannot be listed while sizing gives a size_unreadable issue in
#         sizes.json whose path is that folder (stricter reading: the folder that failed,
#         not only the top folder); the snapshot still completes.
#   Inv:  sizing opens no file (checked in test_snapshot_safety.py).
#
# S4 plugins.json
#   Post: a list of {"folder", "name", "version"}, one per folder of <home>/homebrew/plugins
#         (plain files there are ignored), sorted by folder. name comes from plugin.json,
#         version from package.json, each a regular file of at most 1 MiB holding UTF-8 JSON.
#   Post: a missing, non-regular, oversized, non-UTF-8 or invalid-JSON file gives null for
#         its field plus an issue whose path is that file (the spec does not say which JSON
#         file holds plugin issues, so every JSON member is searched).
#   Post: no homebrew/plugins folder: plugins.json is [] and a decky_not_found issue exists.
#
# S5 logs/
#   Post: the 5 newest regular files matching *.csv in <home>/deckforge/logs, by mtime, are
#         copied byte for byte to logs/<basename>, in the zip newest first (stricter reading
#         of "newest first"). Links, folders and other names are never taken, even when
#         newer. Fewer than 5: all of them.
#   Post: a csv larger than 20 MiB is not copied and has a too_large skip record; 20 MiB
#         exactly is copied.
#   Post: no logs folder: no logs/ members and manifest.json mentions logs_not_found.
#
# S6 system.json
#   Post: os_release holds only NAME, PRETTY_NAME, VERSION_ID, BUILD_ID and VARIANT_ID, with
#         os-release quoting removed (stricter reading), read from OS_RELEASE_PATH.
#   Post: kernel == os.uname().release.
#   Post: board is the board_name text with the trailing newline removed ("Galileo" OLED,
#         "Jupiter" LCD), read from BOARD_NAME_PATH; unreadable (missing, a folder, an OS
#         error) gives null.
#   Post: disk holds shutil.disk_usage (total, used, free) for home and for each available
#         library, and never for an unavailable one.
#   Inv:  OS_RELEASE_PATH and BOARD_NAME_PATH are module constants whose defaults are the
#         real paths, so tests can redirect them.
#
# Round trip: logs are copied byte for byte (checked on every copied log). Sizing, plugins
# and system facts write nothing back.

import builtins
import errno
import io
import os
import shutil
import zipfile

import pytest
from test_detect_settings import refuse_listing
from test_discover_output import mkdir, put
from test_snapshot_support import (
    LOG_EPOCH,
    NEWEST_LOGS,
    ORPHAN_COMPAT,
    ORPHAN_SD,
    ORPHAN_SHADER,
    OS_RELEASE_KEPT,
    PENDING,
    PLUGINS,
    REAL_BOARD_NAME,
    REAL_OS_RELEASE,
    REAL_SCAN,
    UNITY,
    UNREAL,
    WILDS,
    MiB,
    Usage,
    all_json,
    issues_in,
    make_deck,
    mentions,
    run,
    size_bounds,
    skip_reasons,
    zip_json,
    zip_members,
    zip_names,
)

from deckforge import snapshot

# ---------------------------------------------------------------------------- S3 helpers


def sizes_of(deck) -> dict:
    return zip_json(zip_members(run(deck)), "sizes.json")


def entry_for(sizes: dict, appid: int, library) -> dict:
    found = [
        entry
        for entry in sizes["games"]
        if entry.get("appid") == appid and entry.get("library") == str(library)
    ]
    assert len(found) == 1, f"{appid} in {library}: {found}"
    return found[0]


def within(value, folder) -> None:
    lower, upper = size_bounds(folder)
    assert type(value) is int, value
    assert lower <= value <= upper, (value, lower, upper)


def orphans_of(sizes: dict) -> dict[str, int]:
    return {entry["path"]: entry["size"] for entry in sizes["orphans"]}


# ---------------------------------------------------------------------------- S3 sizes


def test_s3_every_card_has_a_sizes_entry(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    cards = {(card["appid"], card["library"]) for card in REAL_SCAN(str(deck.steam))["games"]}
    sizes = sizes_of(deck)
    assert {(entry["appid"], entry["library"]) for entry in sizes["games"]} == cards
    assert (PENDING, str(deck.steam)) in cards


def test_s3_shadercache_and_compatdata_sizes_do_not_follow_links(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    apps = deck.steam / "steamapps"
    sizes = sizes_of(deck)
    wilds = entry_for(sizes, WILDS, deck.steam)
    within(wilds["shadercache"], apps / "shadercache" / str(WILDS))
    assert wilds["shadercache"] >= 251_000
    assert wilds["shadercache"] < 3 * MiB
    within(wilds["compatdata"], apps / "compatdata" / str(WILDS))


def test_s3_absent_folders_give_null(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    sizes = sizes_of(deck)
    unity = entry_for(sizes, UNITY, deck.sd)
    assert unity["shadercache"] is None
    within(unity["compatdata"], deck.sd / "steamapps" / "compatdata" / str(UNITY))
    pending = entry_for(sizes, PENDING, deck.steam)
    assert pending["shadercache"] is None
    assert pending["compatdata"] is None


def test_s3_compatdata_is_taken_from_the_cards_own_library(tmp_path, monkeypatch):
    """UNREAL's card is on the SD card; a compatdata/<appid> folder in the root library is
    neither its size nor an orphan."""
    deck = make_deck(tmp_path, monkeypatch)
    sizes = sizes_of(deck)
    unreal = entry_for(sizes, UNREAL, deck.sd)
    within(unreal["compatdata"], deck.sd / "steamapps" / "compatdata" / str(UNREAL))
    root_copy = deck.steam / "steamapps" / "compatdata" / str(UNREAL)
    assert str(root_copy) not in orphans_of(sizes)


def test_s3_orphans_are_all_digit_entries_with_no_card(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    root_apps, sd_apps = deck.steam / "steamapps", deck.sd / "steamapps"
    expected = {
        root_apps / "shadercache" / str(ORPHAN_SHADER),
        root_apps / "compatdata" / str(ORPHAN_COMPAT),
        sd_apps / "compatdata" / str(ORPHAN_SD),
    }
    orphans = orphans_of(sizes_of(deck))
    assert set(orphans) == {str(path) for path in expected}
    for path in expected:
        within(orphans[str(path)], path)
    assert orphans[str(root_apps / "shadercache" / str(ORPHAN_SHADER))] >= 4096


def test_s3_orphans_in_an_sd_card_library_are_found(tmp_path, monkeypatch):
    """Unusual setup: an SD-card library is handled like any other."""
    deck = make_deck(tmp_path, monkeypatch)
    extra = put(deck.sd / "steamapps" / "shadercache" / "4242" / "x.foz", b"\x05" * 777).parent
    orphans = orphans_of(sizes_of(deck))
    assert str(extra) in orphans
    within(orphans[str(extra)], extra)


def test_s3_orphan_size_does_not_follow_links(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    orphan = deck.steam / "steamapps" / "shadercache" / str(ORPHAN_SHADER)
    (orphan / "out_link").symlink_to(deck.base / "outside" / "big.bin")
    (orphan / "dir_link").symlink_to(deck.base / "outside" / "bigdir", target_is_directory=True)
    orphans = orphans_of(sizes_of(deck))
    within(orphans[str(orphan)], orphan)
    assert orphans[str(orphan)] < MiB


def test_s3_size_error_becomes_size_unreadable_issue(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    nested = deck.steam / "steamapps" / "shadercache" / str(WILDS) / "fozpipelinesv6"
    orphan = deck.steam / "steamapps" / "compatdata" / str(ORPHAN_COMPAT)
    with monkeypatch.context() as patch:
        refused = refuse_listing(patch, nested)
        members = zip_members(run(deck))
    assert refused
    issues = issues_in(zip_json(members, "sizes.json"))
    assert ("size_unreadable", str(nested)) in issues
    with monkeypatch.context() as patch:
        refused = refuse_listing(patch, orphan)
        members = zip_members(run(deck, out=deck.base / "second"))
    assert refused
    assert ("size_unreadable", str(orphan)) in issues_in(zip_json(members, "sizes.json"))


# ---------------------------------------------------------------------------- S4 plugins


def plugins_and_issues(deck) -> tuple[list, list]:
    members = zip_members(run(deck))
    issues = [issue for doc in all_json(members) for issue in issues_in(doc)]
    return zip_json(members, "plugins.json"), issues


def test_s4_plugins_are_listed_sorted_by_folder(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    plugins, issues = plugins_and_issues(deck)
    assert plugins == [
        {"folder": "PowerTools", "name": "PowerTools", "version": "2.0.1"},
        {"folder": "SimpleDeckyTDP", "name": "SimpleDeckyTDP", "version": "0.7.3"},
        {"folder": "broken-package", "name": "Broken Package", "version": None},
    ]
    broken = deck.plugins_dir / "broken-package" / "package.json"
    assert str(broken) in {path for _, path in issues}
    assert sorted(PLUGINS) == [entry["folder"] for entry in plugins]


def test_s4_missing_plugins_folder_gives_empty_list_and_decky_not_found(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    (deck.home / "homebrew").rename(deck.base / "homebrew.moved")
    plugins, issues = plugins_and_issues(deck)
    assert plugins == []
    assert "decky_not_found" in {code for code, _ in issues}


def test_s4_homebrew_without_plugins_folder_is_decky_not_found(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    deck.plugins_dir.rename(deck.base / "plugins.moved")
    plugins, issues = plugins_and_issues(deck)
    assert plugins == []
    assert "decky_not_found" in {code for code, _ in issues}


def _missing_package(plugin):
    (plugin / "package.json").unlink()
    return plugin / "package.json", "version"


def _missing_plugin_json(plugin):
    (plugin / "plugin.json").unlink()
    return plugin / "plugin.json", "name"


def _non_utf8(plugin):
    (plugin / "plugin.json").write_bytes(b'{"name": "Caf\xe9"}')
    return plugin / "plugin.json", "name"


def _oversized(plugin):
    padding = " " * (MiB + 1)
    (plugin / "plugin.json").write_text('{"name": "Big"' + padding + "}", encoding="utf-8")
    return plugin / "plugin.json", "name"


def _invalid_json(plugin):
    (plugin / "package.json").write_text("version = 3", encoding="utf-8")
    return plugin / "package.json", "version"


def _link(plugin):
    real = put(plugin.parent.parent / "elsewhere.json", '{"name": "Linked"}')
    (plugin / "plugin.json").unlink()
    (plugin / "plugin.json").symlink_to(real)
    return plugin / "plugin.json", "name"


def _folder(plugin):
    (plugin / "package.json").unlink()
    mkdir(plugin / "package.json")
    return plugin / "package.json", "version"


PLUGIN_PROBLEMS = {
    "missing-package-json": _missing_package,
    "missing-plugin-json": _missing_plugin_json,
    "non-utf8": _non_utf8,
    "oversized": _oversized,
    "invalid-json": _invalid_json,
    "link": _link,
    "folder": _folder,
}


@pytest.mark.parametrize("problem", sorted(PLUGIN_PROBLEMS))
def test_s4_bad_plugin_file_gives_null_and_an_issue(tmp_path, monkeypatch, problem):
    deck = make_deck(tmp_path, monkeypatch)
    bad_file, field = PLUGIN_PROBLEMS[problem](deck.plugins_dir / "PowerTools")
    plugins, issues = plugins_and_issues(deck)
    power = [entry for entry in plugins if entry["folder"] == "PowerTools"]
    assert len(power) == 1
    assert power[0][field] is None
    other = "version" if field == "name" else "name"
    assert power[0][other] == {"name": "PowerTools", "version": "2.0.1"}[other]
    assert str(bad_file) in {path for _, path in issues}
    assert {"folder": "SimpleDeckyTDP", "name": "SimpleDeckyTDP", "version": "0.7.3"} in plugins


def test_s4_plugin_json_of_exactly_1_mib_is_read(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    head = '{"name": "Edge"'
    text = head + " " * (MiB - len(head) - 1) + "}"
    assert len(text.encode("utf-8")) == MiB
    (deck.plugins_dir / "PowerTools" / "plugin.json").write_text(text, encoding="utf-8")
    plugins, _ = plugins_and_issues(deck)
    assert plugins[0] == {"folder": "PowerTools", "name": "Edge", "version": "2.0.1"}


def test_s4_plain_files_in_plugins_are_not_listed(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    plugins, _ = plugins_and_issues(deck)
    assert "README.md" not in [entry["folder"] for entry in plugins]


# ---------------------------------------------------------------------------- S5 logs


def log_members(zip_path) -> list[str]:
    return [name for name in zip_names(zip_path) if name.startswith("logs/")]


def test_s5_five_newest_csv_logs_are_copied_newest_first(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    assert NEWEST_LOGS == ["b_wilds.csv", "f_hd2.csv", "d_sm2.csv", "g_cp.csv", "a_wilds.csv"]
    zip_path = run(deck)
    assert log_members(zip_path) == [f"logs/{name}" for name in NEWEST_LOGS]
    members = zip_members(zip_path)
    for name in NEWEST_LOGS:
        assert members[f"logs/{name}"] == deck.logs[name].read_bytes()


def test_s5_links_folders_and_other_names_are_never_taken(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    names = log_members(run(deck))
    for decoy in ["link.csv", "folder.csv", "notes.txt", "x.csv.bak"]:
        assert f"logs/{decoy}" not in names
    assert not [name for name in names if name.startswith("logs/folder.csv/")]


def test_s5_fewer_than_five_logs_are_all_copied(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    for name in ["a_wilds.csv", "b_wilds.csv", "c_sm2.csv", "d_sm2.csv"]:
        deck.logs.pop(name).unlink()
    assert log_members(run(deck)) == ["logs/f_hd2.csv", "logs/g_cp.csv", "logs/e_hd2.csv"]


def test_s5_log_over_20_mib_is_skipped_as_too_large(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    big = deck.logs_dir / "huge.csv"
    with big.open("wb") as handle:
        handle.truncate(20 * MiB + 1)
    newest = LOG_EPOCH + 5_000
    os.utime(big, (newest, newest))
    zip_path = run(deck)
    names = log_members(zip_path)
    assert "logs/huge.csv" not in names
    assert names[:4] == [f"logs/{name}" for name in NEWEST_LOGS[:4]]
    manifest = zip_json(zip_members(zip_path), "manifest.json")
    assert skip_reasons(manifest, big) == ["too_large"]


def test_s5_log_of_exactly_20_mib_is_copied(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    edge = deck.logs_dir / "edge.csv"
    with edge.open("wb") as handle:
        handle.truncate(20 * MiB)
    newest = LOG_EPOCH + 5_000
    os.utime(edge, (newest, newest))
    zip_path = run(deck)
    assert log_members(zip_path)[0] == "logs/edge.csv"
    with zipfile.ZipFile(zip_path) as archive:
        assert archive.getinfo("logs/edge.csv").file_size == 20 * MiB


def test_s5_missing_logs_folder_is_noted(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    deck.logs_dir.rename(deck.base / "logs.moved")
    zip_path = run(deck)
    assert log_members(zip_path) == []
    assert mentions(zip_json(zip_members(zip_path), "manifest.json"), "logs_not_found")


def test_s5_logs_present_do_not_note_logs_not_found(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    manifest = zip_json(zip_members(run(deck)), "manifest.json")
    assert not mentions(manifest, "logs_not_found")


# ---------------------------------------------------------------------------- S6 system


def system_of(deck) -> dict:
    return zip_json(zip_members(run(deck)), "system.json")


def test_s6_path_constants_default_to_the_real_files():
    assert os.fspath(snapshot.OS_RELEASE_PATH) == REAL_OS_RELEASE
    assert os.fspath(snapshot.BOARD_NAME_PATH) == REAL_BOARD_NAME


def test_s6_os_release_keeps_only_the_five_keys(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    assert system_of(deck)["os_release"] == OS_RELEASE_KEPT


def test_s6_kernel_comes_from_uname(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    assert system_of(deck)["kernel"] == os.uname().release


@pytest.mark.parametrize("board", ["Galileo", "Jupiter"])
def test_s6_board_name_is_read_from_the_constant_path(tmp_path, monkeypatch, board):
    deck = make_deck(tmp_path, monkeypatch)
    (deck.sysdir / "board_name").write_text(board + "\n", encoding="utf-8")
    assert system_of(deck)["board"] == board


@pytest.mark.parametrize("problem", ["missing", "folder", "os-error"])
def test_s6_unreadable_board_name_gives_null(tmp_path, monkeypatch, problem):
    deck = make_deck(tmp_path, monkeypatch)
    board = deck.sysdir / "board_name"
    if problem == "missing":
        board.unlink()
    elif problem == "folder":
        board.unlink()
        board.mkdir()
    else:
        real_open = builtins.open

        def fake_open(file, *args, **kwargs):
            if isinstance(file, str | os.PathLike) and os.fspath(file) == str(board):
                raise OSError(errno.EIO, os.strerror(errno.EIO), str(board))
            return real_open(file, *args, **kwargs)

        monkeypatch.setattr(builtins, "open", fake_open)
        monkeypatch.setattr(io, "open", fake_open)
    assert system_of(deck)["board"] is None


def test_s6_missing_os_release_does_not_fail_the_snapshot(tmp_path, monkeypatch):
    """Not in the spec's words; reading: an unreadable /etc/os-release is reported as empty
    or null, like the board, and never stops the snapshot."""
    deck = make_deck(tmp_path, monkeypatch)
    (deck.sysdir / "os-release").unlink()
    assert system_of(deck)["os_release"] in (None, {})


def disk_entries(system: dict) -> dict[str, tuple]:
    disk = system["disk"]
    if isinstance(disk, dict):
        return {path: (v["total"], v["used"], v["free"]) for path, v in disk.items()}
    assert isinstance(disk, list)
    return {v["path"]: (v["total"], v["used"], v["free"]) for v in disk}


def test_s6_disk_usage_for_home_and_each_available_library(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    fakes = {
        os.path.realpath(deck.home): Usage(512 * 10**9, 300 * 10**9, 212 * 10**9),
        os.path.realpath(deck.steam): Usage(511 * 10**9, 301 * 10**9, 210 * 10**9),
        os.path.realpath(deck.sd): Usage(1024 * 10**9, 100 * 10**9, 924 * 10**9),
    }
    asked: list[str] = []

    def fake_disk_usage(path):
        real = os.path.realpath(os.fspath(path))
        asked.append(real)
        assert real in fakes, f"disk_usage asked for {path!r}"
        return fakes[real]

    monkeypatch.setattr(shutil, "disk_usage", fake_disk_usage)
    entries = disk_entries(system_of(deck))
    assert set(asked) == set(fakes)
    by_real = {os.path.realpath(path): values for path, values in entries.items()}
    assert by_real == {path: tuple(usage) for path, usage in fakes.items()}
    assert os.path.realpath(deck.base / "gone") not in asked
