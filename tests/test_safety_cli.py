# Contracts for deckforge.safety.main, the command line (docs/specs/safety-module.md: AC15,
# the end-to-end check, and clarifier answers A5, A12, A18, A19). Written before the
# implementation; fixtures and fakes: test_safety_support.py.
#
# main(argv=None) -> int
#   Commands: list | show <backup_id> | restore <backup_id> [--confirm-overwrite]; apply
#   is a library call only. Shared flag --backup-root, written after the command (ASSUMED:
#   "shared flag" read as a flag every command accepts), default
#   Path.home()/deckforge/backups, which is created (parents=True) when missing (A18).
#   Post: list   -> 0; stdout names every backup folder; .tmp-* and manifest-less folders
#                   are on a line saying "incomplete" (A5); times are labelled "Deck clock"
#                   (A12, checked case-insensitively); nothing on stderr.
#   Post: show   -> 0; stdout holds every file's path, sha256_before and sha256_after.
#   Post: restore-> 0; files back byte for byte; stdout prints the SHA-256 of each restored
#                   file (end-to-end check step 3: "matching SHA-256 values").
#                   --confirm-overwrite passes "overwrite" (Q3); stdout then names the new
#                   backup id (ASSUMED: Fede needs it to get his edited file back).
#   Post: SafetyError -> returns 2, stderr is exactly one line containing the code. For
#         changed_since_apply the changed content is shown too (Q3: "shows the difference
#         and stops"): it appears in stdout or in that one stderr line.
#   Post: any other exception propagates (AC15, R12).
#   Post: "apply" is not a command: argparse refuses it (SystemExit, non-zero) or main
#         returns non-zero; nothing is written either way.
#   Inv:  `python -m deckforge.safety` runs main and exits with its code.
#   Note: main has no --proc-root, so restore through the CLI reads the real /proc (read
#         only); no process on the test machine carries the fake game's appid.

import os
import subprocess
import sys

import pytest
from test_safety_support import (
    CONFIG_INI,
    CONFIG_NEW,
    ENGINE_INI,
    ENGINE_NEW,
    GUS_INI,
    GUS_NEW,
    REAL,
    backup_folders,
    copy_holding,
    deck_state,
    hold_lock,
    make_deck,
    release,
    sha,
)
from test_settings_support import SRC

from deckforge import safety

OLD = {"config": CONFIG_INI, "gus": GUS_INI, "engine": ENGINE_INI}
NEW = {"config": CONFIG_NEW, "gus": GUS_NEW, "engine": ENGINE_NEW}
KEYS = ("config", "gus", "engine")
USER_EDIT = b"[Render]\r\nUpscaler=Mine\r\nFrameGen=Off\r\nShadow=High\r\n"


class Boom(Exception):
    """Not a SafetyError and not an OSError: main must let it through."""


def _apply(deck, keys=KEYS):
    changes = [safety.plan(deck.card, str(deck.files[key]), NEW[key]) for key in keys]
    return safety.apply(changes, **deck.kw())


def _root(deck):
    return ["--backup-root", str(deck.backup_root)]


def _one_error_line(err: str, code: str | None = None) -> str:
    lines = err.splitlines()
    assert len(lines) == 1, f"expected one stderr line, got {lines!r}"
    if code is not None:
        assert code in lines[0], lines[0]
    return lines[0]


# ---------------------------------------------------------------------------- list


def test_ac15_list_names_every_backup_marks_incomplete_ones_and_returns_0(tmp_path, capsys):
    deck = make_deck(tmp_path)
    first = _apply(deck, ("config",))
    second = _apply(deck, ("gus",))
    appid = deck.card["appid"]
    tmp = deck.backup_root / f".tmp-20261022-101010-{appid}-aaaaaaaa"
    tmp.mkdir()
    bare = deck.backup_root / f"20261022-101011-{appid}-bbbbbbbb"
    bare.mkdir()
    capsys.readouterr()
    assert safety.main(["list", *_root(deck)]) == 0
    out, err = capsys.readouterr()
    assert err == ""
    assert first in out and second in out
    for folder in (tmp, bare):
        lines = [line for line in out.splitlines() if folder.name in line]
        assert lines, folder.name
        assert any("incomplete" in line.lower() for line in lines), lines
    for backup_id in (first, second):
        lines = [line for line in out.splitlines() if backup_id in line]
        assert not any("incomplete" in line.lower() for line in lines), lines
    assert "deck clock" in out.lower()
    assert tmp.is_dir() and bare.is_dir(), "list never deletes"


def test_ac15_list_of_an_empty_backup_root_returns_0(tmp_path, capsys):
    deck = make_deck(tmp_path)
    assert safety.main(["list", *_root(deck)]) == 0
    assert capsys.readouterr().err == ""


# ---------------------------------------------------------------------------- show


def test_ac15_show_prints_each_path_and_both_hashes(tmp_path, capsys):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    before = deck_state(deck)
    capsys.readouterr()
    assert safety.main(["show", backup_id, *_root(deck)]) == 0
    out, err = capsys.readouterr()
    assert err == ""
    for key in KEYS:
        assert str(deck.files[key]) in out
        assert sha(OLD[key]) in out
        assert sha(NEW[key]) in out
    assert deck_state(deck) == before, "show writes nothing"


def test_ac15_show_of_an_unknown_id_returns_2_with_one_line(tmp_path, capsys):
    deck = make_deck(tmp_path)
    _apply(deck)
    capsys.readouterr()
    code = safety.main(["show", "20991231-235959-2246340-deadbeef", *_root(deck)])
    assert code == 2
    _one_error_line(capsys.readouterr().err)


# ---------------------------------------------------------------------------- restore


def test_ac15_restore_puts_files_back_and_prints_matching_sha256(tmp_path, capsys):
    deck = make_deck(tmp_path)
    before = deck_state(deck)
    backup_id = _apply(deck)
    capsys.readouterr()
    assert safety.main(["restore", backup_id, *_root(deck)]) == 0
    out, err = capsys.readouterr()
    assert err == ""
    assert deck_state(deck) == before
    for key in KEYS:
        assert sha(OLD[key]) in out
        assert sha(deck.files[key].read_bytes()) == sha(OLD[key])


def test_ac15_q3_changed_file_returns_2_shows_it_and_overwrite_restores(tmp_path, capsys):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    deck.config.write_bytes(USER_EDIT)
    before = deck_state(deck)
    folders = backup_folders(deck)
    capsys.readouterr()
    assert safety.main(["restore", backup_id, *_root(deck)]) == 2
    out, err = capsys.readouterr()
    _one_error_line(err, "changed_since_apply")
    assert "Upscaler=Mine" in out + err, "the difference is shown"
    assert deck_state(deck) == before
    assert backup_folders(deck) == folders

    assert safety.main(["restore", backup_id, "--confirm-overwrite", *_root(deck)]) == 0
    out, err = capsys.readouterr()
    assert err == ""
    for key in KEYS:
        assert deck.files[key].read_bytes() == OLD[key]
    [new_id] = sorted(set(backup_folders(deck)) - set(folders))
    assert new_id in out
    assert copy_holding(deck, new_id, USER_EDIT)


def _corrupt(deck, backup_id):
    copy_holding(deck, backup_id, CONFIG_INI).write_bytes(b"[Render]\r\n")


def test_ac15_restoring_a_corrupt_backup_returns_2_with_the_code(tmp_path, capsys):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    _corrupt(deck, backup_id)
    before = deck_state(deck)
    capsys.readouterr()
    assert safety.main(["restore", backup_id, *_root(deck)]) == 2
    _one_error_line(capsys.readouterr().err, "backup_corrupt")
    assert deck_state(deck) == before


def test_ac15_restore_while_another_process_holds_the_lock_returns_2_busy(tmp_path, capsys):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    holder = hold_lock(deck.backup_root / ".lock")
    try:
        capsys.readouterr()
        assert safety.main(["restore", backup_id, *_root(deck)]) == 2
        _one_error_line(capsys.readouterr().err, "busy")
        assert deck.config.read_bytes() == CONFIG_NEW
    finally:
        release(holder)
    assert safety.main(["restore", backup_id, *_root(deck)]) == 0
    assert deck.config.read_bytes() == CONFIG_INI


@pytest.mark.parametrize("command", [["list"], ["show", "x"], ["restore", "x"]])
@pytest.mark.parametrize("shape", ["missing", "relative", "file"])
def test_ac15_a18_a_bad_backup_root_returns_2_and_creates_nothing(
    tmp_path, capsys, monkeypatch, command, shape
):
    deck = make_deck(tmp_path)
    a_file = deck.home / "a-file"
    a_file.write_text("x")
    monkeypatch.chdir(deck.home)
    root = {
        "missing": str(deck.home / "no" / "backups"),
        "relative": "deckforge/backups",
        "file": str(a_file),
    }[shape]
    before = deck_state(deck)
    assert safety.main([*command, "--backup-root", root]) == 2
    _one_error_line(capsys.readouterr().err, "bad_backup_root")
    assert not (deck.home / "no").exists()
    assert deck_state(deck) == before


def test_ac15_other_exceptions_propagate(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    _apply(deck)
    root = os.path.realpath(deck.backup_root)

    def guarded(real):
        def fake(path=".", *args, **kwargs):
            if not isinstance(path, int) and os.path.realpath(os.fsdecode(path)) == root:
                raise Boom("the backup folder vanished mid-read")
            return real(path, *args, **kwargs)

        return fake

    monkeypatch.setattr(os, "scandir", guarded(REAL["scandir"]))
    monkeypatch.setattr(os, "listdir", guarded(REAL["listdir"]))
    with pytest.raises(Boom):
        safety.main(["list", *_root(deck)])


def test_ac15_apply_is_a_library_call_not_a_command(tmp_path, capsys):
    deck = make_deck(tmp_path)
    before = deck_state(deck)
    try:
        code = safety.main(["apply", str(deck.config), *_root(deck)])
    except SystemExit as stop:
        code = stop.code
    assert code not in (0, None)
    assert deck_state(deck) == before
    assert backup_folders(deck) == []


# ---------------------------------------------------------------------------- A18 default


def test_a18_the_default_backup_root_is_home_deckforge_backups(tmp_path, monkeypatch, capsys):
    deck = make_deck(tmp_path)  # its backup_root is <home>/deckforge/backups
    backup_id = _apply(deck)
    monkeypatch.setenv("HOME", str(deck.home))
    capsys.readouterr()
    assert safety.main(["list"]) == 0
    assert backup_id in capsys.readouterr().out
    assert safety.main(["restore", backup_id]) == 0
    assert deck.config.read_bytes() == CONFIG_INI


def test_a18_the_default_backup_root_is_created_under_home(tmp_path, monkeypatch, capsys):
    deck = make_deck(tmp_path)
    home = deck.base / "fresh home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    assert safety.main(["list"]) == 0
    assert (home / "deckforge" / "backups").is_dir()
    assert capsys.readouterr().err == ""


# ---------------------------------------------------------------------------- python -m


def _run(args, home):
    return subprocess.run(
        [sys.executable, "-B", "-m", "deckforge.safety", *args],
        cwd=home,
        env={**os.environ, "PYTHONPATH": str(SRC), "HOME": str(home)},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_ac15_python_dash_m_runs_main_with_its_exit_codes(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck)
    done = _run(["list"], deck.home)
    assert done.returncode == 0, done.stderr
    assert backup_id in done.stdout
    done = _run(["restore", "20991231-235959-2246340-deadbeef"], deck.home)
    assert done.returncode == 2
    _one_error_line(done.stderr)
    done = _run(["restore", backup_id], deck.home)
    assert done.returncode == 0, done.stderr
    assert deck.config.read_bytes() == CONFIG_INI
    assert sha(CONFIG_INI) in done.stdout
