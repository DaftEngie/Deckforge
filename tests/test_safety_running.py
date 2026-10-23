# Contracts for the game-running check after clarifier answer 22
# (docs/specs/safety-module.md, "Decided after the first CI run, 2026-10-23"), written A22
# here. A22 replaces A16's handling of unreadable processes; AC9's environ and exe signals
# and the proc_root-unreadable fail-closed rule stay as tested in test_safety_guards.py.
# Fixtures and fakes: test_safety_support.py (fake proc_root with <pid>/cmdline, environ,
# exe; unreadable / vanished / other-owner fakes that work as root and as a normal user).
#
# The check, run by apply(changes, *, proc_root, ...) and restore(backup_id, *, proc_root):
#   Pre:  proc_root is a readable folder of <pid>/ entries (plus non-pid entries).
#   Post: for every process owned by the current user:
#         - cmdline is read and split on NUL. The process runs the game if any argument
#           is exactly "AppId=<appid>" (Steam's `reaper SteamLaunch AppId=<appid> -- ...`).
#           Look-alikes never count: AppId=<appid>0, AppId=<appid>x, XAppId=<appid>,
#           --AppId=<appid>, another game's AppId.
#         - apply only (restore has no card): it also runs the game if any argument is a
#           path inside the card's install_path (a sibling folder whose name merely starts
#           with the install folder's name is not inside).
#         - environ is also read when readable; SteamAppId=<appid> or
#           STEAM_COMPAT_APP_ID=<appid> counts as before.
#         Any match -> SafetyError game_running; nothing changes, no backup folder.
#   Post: unreadable environ (and exe), readable cmdline (a non-dumpable process such as
#         steamwebhelper or ssh-agent) -> not a refusal; the cmdline decides.
#   Post: unreadable cmdline, readable environ -> the environ decides (ASSUMED from rule 4:
#         only "both unreadable" refuses).
#   Post: same-user process with cmdline AND environ both unreadable -> cannot_check_running.
#   Post: a process that vanishes while being read (ENOENT or ESRCH from the open, or its
#         folder gone after proc_root was listed) is skipped.
#   Post: another user's process is skipped, even with cmdline, environ and exe all
#         unreadable.
#   Inv:  the check also runs just before each target rename (A16, unchanged): a game that
#         starts after the backup is built, seen only through its cmdline, is caught.
#   Inv:  a refusal changes nothing outside the backup root and leaves no backup folder.
#
# Not tested (the spec does not decide them): whether a readable cmdline of ANOTHER user's
# process counts; whether one argument holding spaces ("reaper SteamLaunch AppId=..." as a
# single rewritten argv) counts; whether a path inside prefix_path counts; whether a path
# argument is compared after resolving links.

import errno
from pathlib import Path

import pytest
from test_safety_support import (
    APPID,
    CONFIG_INI,
    CONFIG_NEW,
    GUS_NEW,
    LAYOUTS,
    OTHER_APPID,
    Recorder,
    add_process,
    backup_folders,
    cmdline_of,
    content_state,
    environ,
    make_deck,
    make_foreign,
    make_unreadable,
    make_vanished,
    reaper_cmdline,
    refusal,
    target_folder_names,
    vanish_after_listing,
)

from deckforge import safety

PID = 5100
ELSEWHERE_EXE = "/home/deck/.local/share/Steam/steamapps/common/Some Other Game/Other.exe"
WEBHELPER = cmdline_of(
    "/home/deck/.local/share/Steam/ubuntu12_64/steamwebhelper",
    "--type=renderer",
    "--lang=en-US",
)


def _changes(deck):
    return [
        safety.plan(deck.card, str(deck.config), CONFIG_NEW),
        safety.plan(deck.card, str(deck.gus), GUS_NEW),
    ]


def _state(deck):
    """Everything outside the backup root and the fake proc_root (whose modes the
    unreadable fake changes)."""
    return content_state(deck.base, skip=[deck.backup_root, deck.proc])


def _assert_untouched(deck, before):
    assert _state(deck) == before
    assert backup_folders(deck) == []


def _applied(deck):
    backup_id = safety.apply(_changes(deck), **deck.kw())
    assert deck.config.read_bytes() == CONFIG_NEW
    return backup_id


def _apply_succeeds(deck):
    """apply goes through: the process under test did not count as the game."""
    backup_id = safety.apply(_changes(deck), **deck.kw())
    assert backup_id in backup_folders(deck)
    assert deck.config.read_bytes() == CONFIG_NEW


# ---------------------------------------------------------------------------- AppId=


@pytest.mark.parametrize("env", ["plain", "unreadable"])
def test_a22_a_reaper_steamlaunch_appid_cmdline_is_game_running(tmp_path, monkeypatch, env):
    # The game exe argument is outside the fake install, so only AppId= can match; with
    # "unreadable" the environ (and exe) are hidden too, so the cmdline alone decides.
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    folder = add_process(
        deck.proc,
        PID,
        environ(HOME="/home/deck"),
        exe="/home/deck/.steam/root/ubuntu12_32/reaper",
        cmdline=reaper_cmdline(f"AppId={APPID}", ELSEWHERE_EXE),
    )
    before = _state(deck)
    if env == "unreadable":
        make_unreadable(monkeypatch, folder / "environ", folder / "exe")
    refusal("game_running", safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    _assert_untouched(deck, before)


def test_a22_restore_refuses_while_reaper_runs_the_game(tmp_path):
    deck = make_deck(tmp_path)
    backup_id = _applied(deck)
    add_process(
        deck.proc,
        PID,
        environ(HOME="/home/deck"),
        cmdline=reaper_cmdline(f"AppId={APPID}", ELSEWHERE_EXE),
    )
    before = _state(deck)
    refusal("game_running", safety.restore, backup_id, **deck.rkw())
    assert _state(deck) == before
    assert deck.config.read_bytes() == CONFIG_NEW


@pytest.mark.parametrize(
    "argument",
    [
        f"AppId={APPID}0",
        f"AppId={APPID}x",
        f"XAppId={APPID}",
        f"--AppId={APPID}",
        f"AppId={OTHER_APPID}",
        "AppId=",
    ],
)
def test_a22_appid_look_alikes_in_cmdline_do_not_count(tmp_path, argument):
    deck = make_deck(tmp_path)
    add_process(
        deck.proc,
        PID,
        environ(HOME="/home/deck"),
        cmdline=reaper_cmdline(argument, ELSEWHERE_EXE),
    )
    _apply_succeeds(deck)


@pytest.mark.parametrize("argument", [f"AppId={APPID}0", f"AppId={APPID}x"])
def test_a22_restore_ignores_appid_look_alikes(tmp_path, argument):
    deck = make_deck(tmp_path)
    backup_id = _applied(deck)
    add_process(deck.proc, PID, environ(HOME="/home/deck"), cmdline=reaper_cmdline(argument, "x"))
    result = safety.restore(backup_id, **deck.rkw())
    assert result["backup_id"] == backup_id
    assert deck.config.read_bytes() == CONFIG_INI


# ---------------------------------------------------------------------------- paths


@pytest.mark.parametrize("layout", LAYOUTS)
@pytest.mark.parametrize("key", ["exe", "shipping"])
def test_a22_a_cmdline_argument_inside_install_path_is_game_running(tmp_path, layout, key):
    # Spelled from the card's install_path, so it holds spaces and non-English characters
    # on the SD-card layout, and the link path on the "linked" layout.
    deck = make_deck(tmp_path, layout)
    changes = _changes(deck)
    game_exe = Path(deck.card["install_path"]) / deck.files[key].relative_to(deck.install)
    add_process(
        deck.proc,
        PID,
        environ(HOME="/home/deck"),
        cmdline=cmdline_of(
            "/home/deck/.local/share/Steam/steamapps/common/Proton 9.0 (Beta)/proton",
            "waitforexitandrun",
            game_exe,
        ),
    )
    before = _state(deck)
    refusal("game_running", safety.apply, changes, **deck.kw())
    _assert_untouched(deck, before)


def test_a22_a_path_in_a_sibling_folder_with_the_same_prefix_does_not_count(tmp_path):
    # ".../common/Fake Game2/x.exe" starts with the install path as a string but is not
    # inside it; ".../common/Other/x.exe" and the install folder's parent are not either.
    deck = make_deck(tmp_path)
    install = deck.card["install_path"]
    add_process(
        deck.proc,
        PID,
        environ(HOME="/home/deck"),
        cmdline=cmdline_of(
            "/usr/bin/wine64",
            f"{install}2/FakeGame.exe",
            str(Path(install).parent / "Other" / "x.exe"),
            str(Path(install).parent),
        ),
    )
    _apply_succeeds(deck)


# ---------------------------------------------------------------------------- unreadable


def test_a22_a_non_dumpable_process_with_unrelated_cmdline_does_not_block_apply(
    tmp_path, monkeypatch
):
    # steamwebhelper-like: environ and exe unreadable even for its own user, cmdline fine.
    deck = make_deck(tmp_path)
    folder = add_process(
        deck.proc, PID, environ(SteamAppId=str(APPID)), exe="/usr/bin/ssh-agent", cmdline=WEBHELPER
    )
    make_unreadable(monkeypatch, folder / "environ", folder / "exe")
    _apply_succeeds(deck)


def test_a22_a_non_dumpable_process_with_unrelated_cmdline_does_not_block_restore(
    tmp_path, monkeypatch
):
    deck = make_deck(tmp_path)
    backup_id = _applied(deck)
    folder = add_process(deck.proc, PID, environ(PATH="/usr/bin"), cmdline=WEBHELPER)
    make_unreadable(monkeypatch, folder / "environ")
    safety.restore(backup_id, **deck.rkw())
    monkeypatch.undo()
    assert deck.config.read_bytes() == CONFIG_INI


def test_a22_an_unreadable_cmdline_with_a_readable_game_environ_is_game_running(
    tmp_path, monkeypatch
):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    folder = add_process(deck.proc, PID, environ(SteamAppId=str(APPID)), cmdline=WEBHELPER)
    before = _state(deck)
    make_unreadable(monkeypatch, folder / "cmdline")
    refusal("game_running", safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    _assert_untouched(deck, before)


def test_a22_an_unreadable_cmdline_with_a_readable_plain_environ_does_not_block(
    tmp_path, monkeypatch
):
    deck = make_deck(tmp_path)
    folder = add_process(deck.proc, PID, environ(PATH="/usr/bin"), cmdline=WEBHELPER)
    make_unreadable(monkeypatch, folder / "cmdline")
    _apply_succeeds(deck)


def test_a22_both_cmdline_and_environ_unreadable_is_cannot_check_running(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    folder = add_process(deck.proc, PID, environ(PATH="/usr/bin"), cmdline=WEBHELPER)
    before = _state(deck)
    make_unreadable(monkeypatch, folder / "cmdline", folder / "environ")
    refusal("cannot_check_running", safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    _assert_untouched(deck, before)


def test_a22_restore_with_cmdline_and_environ_unreadable_is_cannot_check_running(
    tmp_path, monkeypatch
):
    deck = make_deck(tmp_path)
    backup_id = _applied(deck)
    folder = add_process(deck.proc, PID, environ(PATH="/usr/bin"), cmdline=WEBHELPER)
    make_unreadable(monkeypatch, folder / "cmdline", folder / "environ")
    refusal("cannot_check_running", safety.restore, backup_id, **deck.rkw())
    monkeypatch.undo()
    assert deck.config.read_bytes() == CONFIG_NEW


# ---------------------------------------------------------------------------- vanishing


@pytest.mark.parametrize("code", [errno.ENOENT, errno.ESRCH], ids=["ENOENT", "ESRCH"])
def test_a22_a_process_vanishing_while_being_read_is_skipped(tmp_path, monkeypatch, code):
    deck = make_deck(tmp_path)
    folder = add_process(deck.proc, PID, environ(PATH="/usr/bin"), exe="/usr/bin/x")
    make_vanished(monkeypatch, folder / "cmdline", folder / "environ", folder / "exe", code=code)
    _apply_succeeds(deck)


def test_a22_a_process_gone_after_proc_root_was_listed_is_skipped(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    folder = add_process(deck.proc, PID, environ(PATH="/usr/bin"), exe="/usr/bin/x")
    vanish_after_listing(monkeypatch, deck.proc, folder)
    _apply_succeeds(deck)
    assert not folder.exists(), "the fake never fired: proc_root was not listed"


@pytest.mark.parametrize("code", [errno.ENOENT, errno.ESRCH], ids=["ENOENT", "ESRCH"])
def test_a22_restore_skips_a_process_vanishing_while_being_read(tmp_path, monkeypatch, code):
    deck = make_deck(tmp_path)
    backup_id = _applied(deck)
    folder = add_process(deck.proc, PID, environ(PATH="/usr/bin"))
    make_vanished(monkeypatch, folder / "cmdline", folder / "environ", code=code)
    safety.restore(backup_id, **deck.rkw())
    monkeypatch.undo()
    assert deck.config.read_bytes() == CONFIG_INI


# ---------------------------------------------------------------------------- other user


def _foreign_hidden_game(deck, monkeypatch):
    # Everything about it says "the game", but it belongs to another user and nothing
    # can be read: it is skipped.
    folder = add_process(
        deck.proc,
        PID,
        environ(SteamAppId=str(APPID)),
        exe=deck.files["exe"],
        cmdline=reaper_cmdline(f"AppId={APPID}", deck.files["exe"]),
    )
    fields = [folder / "cmdline", folder / "environ", folder / "exe"]
    make_foreign(monkeypatch, folder, *fields)
    make_unreadable(monkeypatch, *fields)


def test_a22_another_users_process_with_everything_unreadable_is_skipped(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    _foreign_hidden_game(deck, monkeypatch)
    safety.apply(changes, **deck.kw())
    monkeypatch.undo()
    assert deck.config.read_bytes() == CONFIG_NEW


def test_a22_restore_skips_another_users_process_with_everything_unreadable(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    backup_id = _applied(deck)
    _foreign_hidden_game(deck, monkeypatch)
    safety.restore(backup_id, **deck.rkw())
    monkeypatch.undo()
    assert deck.config.read_bytes() == CONFIG_INI


# ---------------------------------------------------------------------------- late start


def test_a22_a_game_seen_only_by_cmdline_after_the_backup_is_caught_before_the_rename(
    tmp_path, monkeypatch
):
    deck = make_deck(tmp_path)
    changes = _changes(deck)
    names = target_folder_names([deck.config, deck.gus])
    before = content_state(deck.base, skip=[deck.backup_root, deck.proc])
    root = str(deck.backup_root)

    def hook(_rec, op, path, path2):
        moved_backup = op in ("rename", "replace") and Path(path).name.startswith(".tmp-")
        if moved_backup and str(Path(path2).parent) == root:
            add_process(
                deck.proc,
                PID,
                environ(HOME="/home/deck"),
                cmdline=reaper_cmdline(f"AppId={APPID}", ELSEWHERE_EXE),
            )

    Recorder(monkeypatch, deck.base, hook=hook)
    refusal("game_running", safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    assert (deck.proc / str(PID)).exists(), "the backup folder was never renamed"
    assert content_state(deck.base, skip=[deck.backup_root, deck.proc]) == before
    assert target_folder_names([deck.config, deck.gus]) == names
