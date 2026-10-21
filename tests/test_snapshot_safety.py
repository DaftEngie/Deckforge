# Contracts for deckforge.snapshot (docs/specs/snapshot.md): S8 output safety, S9 read-only
# everywhere else, S10 CLI, and the spec's unusual setups. Written test-first:
# src/deckforge/snapshot.py does not exist yet. Fixtures: test_snapshot_support.py; the B9
# change detector and open recorder come from test_discover_output.py.
#
# S8 build_snapshot output
#   Post: returns <out_dir>/deckforge-snapshot-<YYYYmmdd-HHMMSS>Z.zip (from `now`), a valid
#         zip; out_dir afterwards holds that one file and nothing else.
#   Post: out_dir is created with its missing parents (os.makedirs, exist_ok).
#   Post: the zip is written to <target>.partial and moved with os.replace(partial, target);
#         the partial exists when os.replace is called.
#   Post: target already exists: SnapshotError, and nothing on disk changes (the old file
#         keeps its bytes and lstat fields; no .partial).
#   Post: any error while writing (full disk: ENOSPC on a write; os.replace failing): the
#         same OSError propagates, not a SnapshotError, and neither the target nor the
#         .partial exists afterwards.
#   Pre:  out_dir, after realpath, is not steam_root, a library or <home>/homebrew, nor
#         inside one (steam_root also compared after realpath). Otherwise SnapshotError and,
#         stricter reading, nothing at all is created: not even out_dir. A sibling whose name
#         merely starts with the same text (steam-snapshots next to steam) is allowed.
#
# S9 read-only
#   Inv:  the B9 change detector (names, types, modes, sizes, mtimes, ctimes, inodes, links,
#         bytes; lstat, no link following) shows no change anywhere in the fixture outside
#         out_dir: the Steam tree, the SD library, home (homebrew, logs), the system files and
#         the current folder.
#   Inv:  every open for writing (mode with w, a, x or +, or os.open write flags) targets a
#         path inside out_dir.
#   Inv:  user.reg, system.reg, save files, loginusers.vdf and localconfig.vdf are never
#         opened; config/config.vdf is opened no more often than discover.scan alone opens it.
#   Inv:  every file opened for reading is one of: the B9 discover kinds, a non-registry
#         settings file of an installed card, one of the 5 newest logs, a plugin.json or
#         package.json, OS_RELEASE_PATH, BOARD_NAME_PATH, or a file inside out_dir.
#
# S10 main(argv)
#   Pre:  --steam-root is required (argparse exits 2 without it); --home defaults to
#         os.path.expanduser("~"); --out-dir defaults to <home>/deckforge/snapshots.
#   Post: success: stdout holds the zip path and the counts of settings files copied, logs
#         copied and orphans found; returns 0.
#   Post: SnapshotError: one non-empty line on stderr, nothing on stdout, returns 2.
#   Post: other exceptions propagate (R12). `python -m deckforge.snapshot` exits with main's
#         return value.
#
# Unusual setups (spec Safety section)
#   SD-card library: in every fixture (test_snapshot_inventory.py checks its orphans, disk
#   and settings). Flatpak Steam: --steam-root under ~/.var/app works. Steam running: a
#   settings file changing type or vanishing after the scan (test_snapshot_contents.py), and
#   the read-only checks here. Full disk: ENOSPC injected on the partial file's writes.
#
# Round trip: the one write path is the zip; test_snapshot_contents.py extracts copies and
# compares bytes. Here: a failed write must leave the disk exactly as before (apply-then-
# undo is "nothing happened").

import builtins
import errno
import io
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from test_discover_output import SRC, mkdir, put
from test_discover_output import record_opens as record_open_modes
from test_discover_output import snapshot as tree_state
from test_snapshot_support import (
    NEWEST_LOGS,
    NOW,
    REAL_SCAN,
    ZIP_NAME,
    is_inside,
    make_deck,
    patch_scan,
    run,
    zip_members,
)

from deckforge import discover, snapshot

WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND


class Boom(Exception):
    """An unexpected failure that snapshot must not catch."""


def outside_out(state: dict[str, tuple], deck, top: Path) -> dict[str, tuple]:
    """The detector's view of `top` with out_dir and everything below it left out."""
    rel = os.path.relpath(deck.out, top)
    return {
        key: value
        for key, value in state.items()
        if key != rel and not key.startswith(rel + os.sep)
    }


# ---------------------------------------------------------------------------- S8 naming


def test_s8_zip_path_name_and_contents_of_out_dir(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    zip_path = run(deck)
    assert zip_path == deck.out / ZIP_NAME
    assert zipfile.is_zipfile(zip_path)
    assert sorted(path.name for path in deck.out.iterdir()) == [ZIP_NAME]


def test_s8_out_dir_and_missing_parents_are_created(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    out = deck.base / "a" / "b" / "c"
    zip_path = run(deck, out=out)
    assert zip_path == out / ZIP_NAME
    assert zipfile.is_zipfile(zip_path)


def test_s8_existing_out_dir_is_fine(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    put(deck.out / "older-unrelated.zip", b"keep me")
    zip_path = run(deck)
    assert zip_path == deck.out / ZIP_NAME
    assert (deck.out / "older-unrelated.zip").read_bytes() == b"keep me"


def test_s8_zip_goes_through_partial_and_os_replace(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    real_replace = os.replace
    calls: list[tuple[str, str, bool]] = []

    def fake_replace(src, dst, *args, **kwargs):
        src_text, dst_text = os.fsdecode(src), os.fsdecode(dst)
        calls.append((src_text, dst_text, Path(src_text).is_file()))
        return real_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "replace", fake_replace)
    zip_path = run(deck)
    target = os.path.realpath(deck.out / ZIP_NAME)
    resolved = [(os.path.realpath(s), os.path.realpath(d), existed) for s, d, existed in calls]
    assert (target + ".partial", target, True) in resolved
    assert not Path(target + ".partial").exists()
    assert zipfile.is_zipfile(zip_path)


# ---------------------------------------------------------------------------- S8 overwrite


def test_s8_existing_target_is_refused_and_left_unchanged(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    put(deck.out / ZIP_NAME, b"an earlier snapshot")
    before = tree_state(deck.base)
    with pytest.raises(snapshot.SnapshotError):
        run(deck)
    assert tree_state(deck.base) == before
    assert (deck.out / ZIP_NAME).read_bytes() == b"an earlier snapshot"


def test_s8_second_run_in_the_same_second_is_refused(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    first = run(deck)
    before = tree_state(deck.base)
    with pytest.raises(snapshot.SnapshotError):
        run(deck)
    assert tree_state(deck.base) == before
    assert zipfile.is_zipfile(first)


def test_s8_existing_target_folder_is_refused(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    mkdir(deck.out / ZIP_NAME)
    before = tree_state(deck.base)
    with pytest.raises(snapshot.SnapshotError):
        run(deck)
    assert tree_state(deck.base) == before


# ---------------------------------------------------------------------------- S8 failures


class FullDisk:
    """Wraps a file object opened on the .partial file: every write fails with ENOSPC."""

    def __init__(self, inner, hits: list[str]) -> None:
        self._inner = inner
        self._hits = hits

    def write(self, data) -> int:
        self._hits.append("write")
        raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))

    def writelines(self, lines) -> None:
        self._hits.append("writelines")
        raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> None:
        self._inner.close()


def fill_disk_for_partials(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Any file opened for writing whose name ends in .partial is created, but every write
    to it fails with ENOSPC (also when opened through os.open plus os.fdopen)."""
    hits: list[str] = []
    partial_fds: set[int] = set()
    real_open, real_os_open, real_os_write = builtins.open, os.open, os.write

    def is_partial(file) -> bool:
        if isinstance(file, int):
            return file in partial_fds
        return isinstance(file, str | bytes | os.PathLike) and os.fsdecode(
            os.fspath(file)
        ).endswith(".partial")

    def fake_open(file, mode="r", *args, **kwargs):
        handle = real_open(file, mode, *args, **kwargs)
        if is_partial(file) and any(flag in mode for flag in "wax+"):
            return FullDisk(handle, hits)
        return handle

    def fake_os_open(path, flags, *args, **kwargs):
        fd = real_os_open(path, flags, *args, **kwargs)
        if flags & WRITE_FLAGS and is_partial(path):
            partial_fds.add(fd)
        return fd

    def fake_os_write(fd, data):
        if fd in partial_fds:
            hits.append("os.write")
            raise OSError(errno.ENOSPC, os.strerror(errno.ENOSPC))
        return real_os_write(fd, data)

    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(io, "open", fake_open)
    monkeypatch.setattr(os, "open", fake_os_open)
    monkeypatch.setattr(os, "write", fake_os_write)
    return hits


def test_s8_full_disk_removes_the_partial_and_reraises(tmp_path, monkeypatch):
    """Unusual setup: a full disk. The OSError reaches the caller unchanged."""
    deck = make_deck(tmp_path, monkeypatch)
    mkdir(deck.out)
    before = outside_out(tree_state(deck.base), deck, deck.base)
    with monkeypatch.context() as patch:
        hits = fill_disk_for_partials(patch)
        with pytest.raises(OSError) as caught:
            run(deck)
    assert hits, "no write reached the .partial file, so the full disk was not exercised"
    assert caught.value.errno == errno.ENOSPC
    assert not isinstance(caught.value, snapshot.SnapshotError)
    assert sorted(deck.out.iterdir()) == []
    assert outside_out(tree_state(deck.base), deck, deck.base) == before


def test_s8_failing_os_replace_removes_the_partial_and_reraises(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    mkdir(deck.out)
    seen: list[tuple[str, bool]] = []

    def failing_replace(src, dst, *args, **kwargs):
        seen.append((os.fsdecode(src), Path(os.fsdecode(src)).is_file()))
        raise OSError(errno.EIO, os.strerror(errno.EIO))

    monkeypatch.setattr(os, "replace", failing_replace)
    with pytest.raises(OSError) as caught:
        run(deck)
    assert caught.value.errno == errno.EIO
    assert seen
    assert seen[0][0].endswith(ZIP_NAME + ".partial")
    assert seen[0][1] is True
    assert sorted(deck.out.iterdir()) == []


def test_s8_unexpected_error_while_writing_removes_the_partial(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    mkdir(deck.out)
    real_zip_open = zipfile.ZipFile.open
    calls: list[str] = []

    def failing_zip_open(self, name, mode="r", *args, **kwargs):
        if mode == "w":
            calls.append(getattr(name, "filename", name))
            if len(calls) == 2:
                raise Boom("second member")
        return real_zip_open(self, name, mode, *args, **kwargs)

    monkeypatch.setattr(zipfile.ZipFile, "open", failing_zip_open)
    with pytest.raises(Boom):
        run(deck)
    assert len(calls) == 2
    assert sorted(deck.out.iterdir()) == []


def test_s8_other_exceptions_from_scan_propagate(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)

    def broken_scan(steam_root, *args, **kwargs):
        raise Boom(str(steam_root))

    patch_scan(monkeypatch, broken_scan)
    with pytest.raises(Boom):
        run(deck)
    leftovers = sorted(deck.out.iterdir()) if deck.out.exists() else []
    assert leftovers == []


# ---------------------------------------------------------------------------- S8 refusals


def _inside_steam(deck):
    return deck.steam, deck.steam / "snapshots"


def _steam_itself(deck):
    return deck.steam, deck.steam


def _inside_sd_library(deck):
    return deck.steam, deck.sd / "steamapps" / "snaps"


def _sd_library_itself(deck):
    return deck.steam, deck.sd


def _inside_homebrew(deck):
    return deck.steam, deck.home / "homebrew" / "snaps"


def _homebrew_itself(deck):
    return deck.steam, deck.home / "homebrew"


def _link_into_steam(deck):
    (deck.base / "outlink").symlink_to(deck.steam, target_is_directory=True)
    return deck.steam, deck.base / "outlink" / "snaps"


def _steam_root_given_as_link(deck):
    link = deck.base / "steamlink"
    link.symlink_to(deck.steam, target_is_directory=True)
    return link, deck.steam / "snaps"


def _dotdot_into_steam(deck):
    return deck.steam, Path(f"{deck.home}/../steam/snaps")


def _homebrew_via_link(deck):
    (deck.base / "brewlink").symlink_to(deck.home / "homebrew", target_is_directory=True)
    return deck.steam, deck.base / "brewlink" / "x"


REFUSED = {
    "inside-steam-root": _inside_steam,
    "steam-root-itself": _steam_itself,
    "inside-sd-library": _inside_sd_library,
    "sd-library-itself": _sd_library_itself,
    "inside-homebrew": _inside_homebrew,
    "homebrew-itself": _homebrew_itself,
    "link-into-steam-root": _link_into_steam,
    "steam-root-given-as-link": _steam_root_given_as_link,
    "dotdot-into-steam-root": _dotdot_into_steam,
    "link-into-homebrew": _homebrew_via_link,
}


@pytest.mark.parametrize("case", sorted(REFUSED))
def test_s8_out_dir_inside_steam_library_or_homebrew_is_refused(tmp_path, monkeypatch, case):
    deck = make_deck(tmp_path, monkeypatch)
    steam_root, out = REFUSED[case](deck)
    before = tree_state(deck.base)
    with pytest.raises(snapshot.SnapshotError):
        snapshot.build_snapshot(str(steam_root), str(deck.home), str(out), now=NOW)
    assert tree_state(deck.base) == before


@pytest.mark.parametrize("name", ["steam-snapshots", "steam2", "steamapps"])
def test_s8_sibling_with_a_similar_name_is_allowed(tmp_path, monkeypatch, name):
    deck = make_deck(tmp_path, monkeypatch)
    out = deck.base / name
    assert run(deck, out=out) == out / ZIP_NAME


def test_s8_homebrew_sibling_is_allowed(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    out = deck.home / "homebrew-snapshots"
    assert run(deck, out=out) == out / ZIP_NAME


# ---------------------------------------------------------------------------- S9 read-only


def test_s9_change_detector_sees_nothing_outside_out_dir(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    mkdir(deck.out)
    cwd = mkdir(tmp_path / "cwd")
    monkeypatch.chdir(cwd)
    before = outside_out(tree_state(tmp_path), deck, tmp_path)
    zip_path = run(deck)
    assert zipfile.is_zipfile(zip_path)
    assert outside_out(tree_state(tmp_path), deck, tmp_path) == before
    assert list(cwd.iterdir()) == []


def test_s9_named_trees_are_unchanged_when_out_dir_is_created(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    trees = [deck.steam, deck.sd, deck.home / "homebrew", deck.logs_dir, deck.sysdir]
    before = [tree_state(top) for top in trees]
    run(deck, out=deck.base / "out" / "snaps")
    assert [tree_state(top) for top in trees] == before


def test_s9_every_write_open_is_inside_out_dir(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    with monkeypatch.context() as patch:
        seen = record_open_modes(patch)
        run(deck)
    writes = []
    for route, file, mode in seen:
        if isinstance(file, int):
            continue  # an fd: its path was recorded by os.open
        if route == "os.open":
            if mode & WRITE_FLAGS:
                writes.append(os.fsdecode(file))
        elif any(flag in str(mode) for flag in "wax+"):
            writes.append(os.fsdecode(os.fspath(file)))
    assert writes, "the zip was written without any recorded open"
    outside = [path for path in writes if not is_inside(path, deck.out)]
    assert outside == []


def test_s9_private_files_are_never_opened(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    config_vdf = os.path.realpath(deck.steam / "config" / "config.vdf")
    with monkeypatch.context() as patch:
        baseline = record_open_modes(patch)
        discover.scan(str(deck.steam))
    with monkeypatch.context() as patch:
        seen = record_open_modes(patch)
        run(deck)
    opened = [
        os.path.realpath(os.fsdecode(os.fspath(file)))
        for _, file, _ in seen
        if not isinstance(file, int)
    ]
    for private in deck.private:
        assert os.path.realpath(private) not in opened, f"opened {private}"
    for path in opened:
        assert not path.endswith((".reg", ".sav")), f"opened {path}"
    scan_count = sum(
        1
        for _, file, _ in baseline
        if not isinstance(file, int) and os.path.realpath(os.fsdecode(file)) == config_vdf
    )
    assert scan_count >= 1
    assert opened.count(config_vdf) <= scan_count


def test_s9_only_expected_files_are_opened_for_reading(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    result = REAL_SCAN(str(deck.steam))
    allowed = {
        os.path.realpath(deck.steam / "steamapps" / "libraryfolders.vdf"),
        os.path.realpath(deck.steam / "config" / "config.vdf"),
        os.path.realpath(deck.sysdir / "os-release"),
        os.path.realpath(deck.sysdir / "board_name"),
    }
    for library in deck.libraries:
        allowed |= {os.path.realpath(p) for p in (library / "steamapps").glob("appmanifest_*.acf")}
    for card in result["games"]:
        if card["installed"]:
            allowed |= {
                os.path.realpath(entry["path"])
                for entry in card["settings_files"]
                if entry["kind"] not in ("reg", "registry")
            }
    allowed |= {os.path.realpath(deck.logs[name]) for name in NEWEST_LOGS}
    for plugin in deck.plugins_dir.iterdir():
        allowed |= {
            os.path.realpath(plugin / "plugin.json"),
            os.path.realpath(plugin / "package.json"),
        }
    with monkeypatch.context() as patch:
        seen = record_open_modes(patch)
        run(deck)
    unexpected = []
    for route, file, _ in seen:
        if isinstance(file, int):
            continue
        path = os.fsdecode(os.fspath(file))
        if is_inside(path, deck.out) or os.path.realpath(path) in allowed:
            continue
        unexpected.append(f"{route} {path}")
    assert unexpected == []


# ---------------------------------------------------------------------------- S10 CLI


def cli_args(deck) -> list[str]:
    return ["--steam-root", str(deck.steam), "--home", str(deck.home), "--out-dir", str(deck.out)]


def numbers_besides(text: str, zip_path: str) -> set[int]:
    return {int(n) for n in re.findall(r"\d+", text.replace(zip_path, " "))}


def test_s10_success_prints_path_and_counts_and_returns_0(tmp_path, monkeypatch, capsys):
    deck = make_deck(tmp_path, monkeypatch)
    assert snapshot.main(cli_args(deck)) == 0
    out = capsys.readouterr().out
    zips = list(deck.out.glob("deckforge-snapshot-*Z.zip"))
    assert len(zips) == 1
    assert str(zips[0]) in out
    members = zip_members(zips[0])
    settings = len([n for n in members if n.startswith("settings/")])
    logs = len([n for n in members if n.startswith("logs/")])
    assert (settings, logs) == (4, 5)
    assert {settings, logs, 3} <= numbers_besides(out, str(zips[0]))


def test_s10_counts_follow_the_tree(tmp_path, monkeypatch, capsys):
    deck = make_deck(tmp_path, monkeypatch)
    for name in ["a_wilds.csv", "b_wilds.csv", "c_sm2.csv", "d_sm2.csv", "e_hd2.csv"]:
        deck.logs[name].unlink()
    for n in range(7):
        put(deck.sd / "steamapps" / "shadercache" / str(7000 + n) / "x", b"x")
    assert snapshot.main(cli_args(deck)) == 0
    out = capsys.readouterr().out
    zips = list(deck.out.glob("*.zip"))
    assert len(zips) == 1
    assert {4, 2, 10} <= numbers_besides(out, str(zips[0]))


def test_s10_default_home_and_out_dir(tmp_path, monkeypatch, capsys):
    deck = make_deck(tmp_path, monkeypatch)
    monkeypatch.setenv("HOME", str(deck.home))
    assert Path("~").expanduser() == deck.home
    assert snapshot.main(["--steam-root", str(deck.steam)]) == 0
    zips = list((deck.home / "deckforge" / "snapshots").glob("deckforge-snapshot-*Z.zip"))
    assert len(zips) == 1
    assert str(zips[0]) in capsys.readouterr().out
    plugins = zip_members(zips[0])["plugins.json"]
    assert b"PowerTools" in plugins


def test_s10_out_dir_defaults_under_the_given_home(tmp_path, monkeypatch, capsys):
    deck = make_deck(tmp_path, monkeypatch)
    monkeypatch.setenv("HOME", str(tmp_path / "not_this_home"))
    assert snapshot.main(["--steam-root", str(deck.steam), "--home", str(deck.home)]) == 0
    zips = list((deck.home / "deckforge" / "snapshots").glob("*.zip"))
    assert len(zips) == 1
    assert not (tmp_path / "not_this_home").exists()
    capsys.readouterr()


@pytest.mark.parametrize("argv", [[], ["--steam-root"], ["--home", "x"]])
def test_s10_missing_steam_root_exits_2(tmp_path, monkeypatch, capsys, argv):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    with pytest.raises(SystemExit) as caught:
        snapshot.main(argv)
    assert caught.value.code == 2
    assert capsys.readouterr().out == ""
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("problem", ["out-dir-in-steam", "out-dir-in-homebrew", "no-steam"])
def test_s10_snapshot_error_returns_2_with_one_line(tmp_path, monkeypatch, capsys, problem):
    deck = make_deck(tmp_path, monkeypatch)
    args = cli_args(deck)
    if problem == "out-dir-in-steam":
        args[-1] = str(deck.steam / "snaps")
    elif problem == "out-dir-in-homebrew":
        args[-1] = str(deck.home / "homebrew" / "snaps")
    else:
        args[1] = str(deck.base / "no_such_steam")
    before = tree_state(deck.base)
    assert snapshot.main(args) == 2
    assert tree_state(deck.base) == before
    captured = capsys.readouterr()
    assert captured.out == ""
    message = captured.err.strip()
    assert message != ""
    assert "\n" not in message


def test_s10_other_exceptions_propagate(tmp_path, monkeypatch, capsys):
    deck = make_deck(tmp_path, monkeypatch)

    def broken_scan(steam_root, *args, **kwargs):
        raise Boom(str(steam_root))

    patch_scan(monkeypatch, broken_scan)
    with pytest.raises(Boom):
        snapshot.main(cli_args(deck))
    assert capsys.readouterr().out == ""


def test_s10_full_disk_propagates_from_main(tmp_path, monkeypatch, capsys):
    deck = make_deck(tmp_path, monkeypatch)
    with monkeypatch.context() as patch:
        fill_disk_for_partials(patch)
        with pytest.raises(OSError) as caught:
            snapshot.main(cli_args(deck))
    assert caught.value.errno == errno.ENOSPC
    assert list(deck.out.iterdir()) == []


def run_module(args: list[str], cwd: Path, home: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(SRC), "HOME": str(home)}
    return subprocess.run(
        [sys.executable, "-B", "-m", "deckforge.snapshot", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def test_s10_module_runs_main_as_a_script(tmp_path, monkeypatch):
    deck = make_deck(tmp_path, monkeypatch)
    cwd = mkdir(tmp_path / "cwd")
    ok = run_module(cli_args(deck), cwd, deck.home)
    assert ok.returncode == 0, ok.stderr
    zips = list(deck.out.glob("deckforge-snapshot-*Z.zip"))
    assert len(zips) == 1
    assert str(zips[0]) in ok.stdout
    usage = run_module([], cwd, deck.home)
    assert usage.returncode == 2
    assert usage.stdout == ""
    refused = run_module(
        ["--steam-root", str(deck.steam), "--out-dir", str(deck.steam / "x")], cwd, deck.home
    )
    assert refused.returncode == 2
    assert refused.stdout == ""
    assert "Traceback" not in refused.stderr
    assert "\n" not in refused.stderr.strip()
    assert list(cwd.iterdir()) == []


# ---------------------------------------------------------------------------- unusual setups


def test_unusual_flatpak_steam_root_under_home_works(tmp_path, monkeypatch, capsys):
    base = tmp_path / "data"
    flatpak = base / "home" / ".var" / "app" / "com.valvesoftware.Steam" / ".local/share/Steam"
    deck = make_deck(tmp_path, monkeypatch, steam=flatpak)
    assert deck.steam == flatpak
    assert snapshot.main(cli_args(deck)) == 0
    zips = list(deck.out.glob("*.zip"))
    assert len(zips) == 1
    assert str(zips[0]) in capsys.readouterr().out
    members = zip_members(zips[0])
    assert members["scan.json"].decode("ascii").count(str(flatpak)) > 0
