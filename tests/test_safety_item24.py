# Contracts for docs/specs/safety-module.md clarifier answer 24 (written A24 below), decided
# after the second verifier review, 2026-10-23. Written before the implementation; fixtures
# and fakes: test_safety_support.py, patterns: test_safety_item23.py. Nothing here touches a
# real Steam install (R7); nothing is deleted outside tmp_path (R6).
#
# apply(changes, *, backup_root, confirm, proc_root, userdata_roots) -> str
#   A second Ctrl-C during rollback (A24, AC8, A7, A23):
#     Setup: three targets (config, gus, engine). The first KeyboardInterrupt arrives while
#            the second target (gus) is being replaced, so only config holds new bytes. The
#            second KeyboardInterrupt arrives at rollback step k of config, for every k up to
#            and including the os.replace that would put config back (after that replace,
#            config is old again and nothing is left to report).
#     Post: apply raises SafetyError with code "rollback_failed"; no KeyboardInterrupt
#           escapes; the interrupt is not retried, so config still holds the new bytes; gus
#           and engine hold their old bytes.
#     Post: exactly one complete backup is kept and it verifies (copies match manifest).
#     Post: the error text names that backup folder, names config on a line that says "new",
#           and says where the old/original content is (the word "old" or "original...").
#     Post: no temp file is left in any target folder (AC3; A24 names SIGKILL as the only
#           case that may leave one).
#     Post: a later restore(backup_id) finishes the job: restored == [config], and the whole
#           Deck outside backup_root is byte- and mode-identical to before apply.
#   Ctrl-C at the final step (A24):
#     Setup: the KeyboardInterrupt arrives at the first release of the backup_root lock that
#            happens when every target already holds its new bytes and a complete backup
#            folder exists: flock(LOCK_UN) on the lock's fd, os.close of the lock's fd, or
#            close() of a file object opened on <backup_root>/.lock. The real call runs
#            first, then the interrupt is raised (a signal that arrives during a system call
#            is acted on when the call returns).
#     Post: apply returns the backup_id normally (the interrupt is not re-raised); every
#           target is fully new; the backup is complete; the lock is free afterwards; and
#           restore(backup_id) then gives the starting tree (round trip, every LAYOUT).
#
# restore(backup_id, *, backup_root, confirm, proc_root) -> dict
#   Ctrl-C at the final step (A24): same setup, with "every target already holds its old
#     bytes" as the trigger condition.
#     Post: restore returns its A19 dict (backup_id, restored = all three, skipped = [],
#           new_backup_id None); the Deck is back to its starting tree; the lock is free.
#   CLI (A24, AC15): main(["restore", id, "--backup-root", root]) with the same interrupt
#     returns 0 and prints the SHA-256 of each restored file; no traceback on stderr.
#   gid range (A24): a manifest record's gid must be an int with 0 <= gid < 2**32 - 1.
#     Pre:  gid in (2**32 - 1, 2**32, -1, "12", 1.5); with and without "overwrite".
#     Post: SafetyError("backup_corrupt"); the Deck and the backup root (apart from .lock)
#           are unchanged; no file or folder is created anywhere under the Deck except the
#           lock file (seen at os.open O_CREAT / O_TMPFILE, open() modes w/x/a, os.mkdir).
#     Post: gid 0 and gid 1000 are accepted: restore puts config back. The group then is that
#           gid, or (as a normal user, who may not give a file that group) the A23 warning
#           group_not_kept is logged for config.
#
# Running check (A22, A24 test gap): a same-user process whose environ and exe are
#   unreadable (non-dumpable) and whose cmdline has an argument that reaches the install
#   folder through a symlink counts as the game: apply and restore refuse with game_running.
#   Shapes: a link to the install folder, a link to its parent folder, a link file pointing at
#   a file in the install folder, and (layout "linked") the card's install_path goes through a
#   link while the argument uses the real path. Controls: through the same parent link, a
#   sibling folder "Fake Game 2" is not the game (no string-prefix match).
#
# Decisions where the spec is silent (ASSUMED, see the report):
#   - "which files hold which version" is checked as: the still-new file is named on a line
#     with the word "new", and the text says where the old/original content is; the wording
#     is otherwise free.
#   - The final step is modelled as the lock release only (not the last folder fsync).
#   - CLI stderr may hold a note about the interrupt, but no traceback.
#   - bool gids (True) and a missing gid are not covered by A24 and are not tested here.

import fcntl
import io
import builtins
import logging
import os
import re
import signal
import stat
from pathlib import Path

import pytest
from test_safety_apply import _changes, _verify_complete
from test_safety_item23 import _group_warnings, _record
from test_safety_restore import KEYS, NEW, OLD, _apply
from test_safety_support import (
    CONFIG_INI,
    CONFIG_NEW,
    LAYOUTS,
    REAL,
    Recorder,
    abs_path,
    add_process,
    cmdline_of,
    complete_ids,
    content_state,
    deck_state,
    environ,
    error_text,
    fd_path,
    make_deck,
    make_unreadable,
    manifest_files,
    mode_of,
    read_manifest,
    refusal,
    serve_fake_proc,
    sha,
    target_folder_names,
    write_manifest,
)

from deckforge import safety

HOWS = ("raise", "signal")
MAX_ROLLBACK_STEPS = 40
GAME_PID = 4242
NEW_WORD = re.compile(r"\bnew\b", re.IGNORECASE)
OLD_WORD = re.compile(r"\bold\b|\boriginal", re.IGNORECASE)


def _ctrl_c(how: str, what: str) -> None:
    """Deliver Ctrl-C: raise KeyboardInterrupt, or a real SIGINT (the default handler then
    raises KeyboardInterrupt)."""
    if how == "signal":
        assert signal.getsignal(signal.SIGINT) is signal.default_int_handler, (
            "the test runner changed the SIGINT handler"
        )
        signal.raise_signal(signal.SIGINT)
    raise KeyboardInterrupt(what)


def _read(path: Path) -> bytes:
    with REAL["io_open"](path, "rb") as handle:
        return handle.read()


# ---------------------------------------------------------------------------- double Ctrl-C


def _double_ctrl_c(monkeypatch, deck, second_at: int, how: str) -> dict:
    """First Ctrl-C at the os.replace of the second target; second Ctrl-C at write-side step
    `second_at` of the rollback of the first target (steps touching its folder)."""
    targets = {str(path) for path in deck.writable}
    folder = str(deck.config.parent)
    state: dict = {"replaced": [], "first": False, "rollback": [], "second": None}

    def in_folder(path: str | None) -> bool:
        return bool(path) and (path == folder or str(Path(path).parent) == folder)

    def hook(_rec, op, path, path2):
        if not state["first"]:
            if op == "replace" and path2 in targets:
                state["replaced"].append(path2)
                if len(state["replaced"]) == 2:
                    state["first"] = True
                    _ctrl_c(how, f"first Ctrl-C at {op} {path2}")
            return
        if state["second"] is not None or not (in_folder(path) or in_folder(path2)):
            return
        index = len(state["rollback"])
        state["rollback"].append((op, path, path2))
        if index == second_at:
            state["second"] = (op, path, path2)
            _ctrl_c(how, f"second Ctrl-C at {op} {path} {path2}")

    Recorder(monkeypatch, deck.base, hook=hook)
    return state


def _rollback_failed(call, *args, **kwargs) -> Exception:
    try:
        call(*args, **kwargs)
    except safety.SafetyError as error:
        assert error.code == "rollback_failed", f"expected rollback_failed, got {error.code}"
        return error
    except KeyboardInterrupt as escaped:
        pytest.fail(f"a bare KeyboardInterrupt escaped instead of rollback_failed: {escaped}")
    pytest.fail("the second Ctrl-C was swallowed: apply returned normally")


@pytest.mark.parametrize("layout", ["steam", "sd"])
@pytest.mark.parametrize("how", HOWS)
def test_a24_second_ctrl_c_during_rollback_is_rollback_failed_and_restore_finishes(
    tmp_path, monkeypatch, how, layout
):
    for second_at in range(MAX_ROLLBACK_STEPS):
        deck = make_deck(tmp_path / f"k{second_at}", layout)
        changes = _changes(deck)
        before = deck_state(deck)
        names = target_folder_names(deck.writable)
        state = _double_ctrl_c(monkeypatch, deck, second_at, how)
        error = _rollback_failed(safety.apply, changes, **deck.kw())
        monkeypatch.undo()
        label = f"second Ctrl-C at rollback step {second_at}: {state['second']}"
        assert state["first"], "the second target was never replaced"
        assert state["replaced"][0] == str(deck.config), state["replaced"]
        assert state["second"] is not None, (
            f"the rollback of config made only {len(state['rollback'])} write-side steps and "
            f"never replaced it: {state['rollback']}"
        )
        assert _read(deck.config) == CONFIG_NEW, f"{label}: config should still be new"
        assert _read(deck.gus) == OLD["gus"], label
        assert _read(deck.engine) == OLD["engine"], label
        assert target_folder_names(deck.writable) == names, f"{label}: temp file left"
        completes = complete_ids(safety.list_backups(str(deck.backup_root)))
        assert len(completes) == 1, f"{label}: {completes}"
        backup_id = completes[0]
        _verify_complete(deck, backup_id)
        said = error_text(error)
        assert str(deck.backup_root / backup_id) in said, f"{label}: backup folder not named"
        lines = [line for line in said.splitlines() if str(deck.config) in line]
        assert lines, f"{label}: the message does not name {deck.config}: {said}"
        assert any(NEW_WORD.search(line) for line in lines), (
            f"{label}: the message does not say {deck.config} holds the new content: {said}"
        )
        assert OLD_WORD.search(said), f"{label}: the message does not say where the old is"
        result = safety.restore(backup_id, **deck.rkw())
        assert result["restored"] == [str(deck.config)], label
        assert deck_state(deck) == before, f"{label}: a later restore does not finish the job"
        op, _path, path2 = state["second"]
        if op in ("replace", "rename") and path2 == str(deck.config):
            return
    pytest.fail(f"the rollback did not replace config within {MAX_ROLLBACK_STEPS} steps")


# ---------------------------------------------------------------------------- final-step Ctrl-C


class _ReleaseWatch:
    """A file object opened on the lock file; its close() counts as a lock release."""

    def __init__(self, inner, on_close) -> None:
        self._inner = inner
        self._on_close = on_close

    def close(self) -> None:
        self._inner.close()
        self._on_close("close() of the lock file object")

    def __enter__(self):
        self._inner.__enter__()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def __getattr__(self, name: str):
        return getattr(self._inner, name)


def _interrupt_on_lock_release(monkeypatch, deck, ready, how: str) -> dict:
    """Ctrl-C right after the first lock release for which ready() holds."""
    lock = abs_path(deck.backup_root / ".lock")
    fired: dict = {"at": None, "releases": []}

    def is_lock(target) -> bool:
        try:
            fd = target if isinstance(target, int) else target.fileno()
        except (AttributeError, ValueError, OSError):
            return False
        return fd_path(fd) == lock

    def fire(what: str) -> None:
        fired["releases"].append(what)
        if fired["at"] is None and ready():
            fired["at"] = what
            _ctrl_c(how, f"Ctrl-C at {what}")

    real_flock = fcntl.flock
    real_close = os.close

    def flock(fd, operation):
        result = real_flock(fd, operation)
        if operation & fcntl.LOCK_UN and is_lock(fd):
            fire("flock(LOCK_UN)")
        return result

    def close(fd):
        was_lock = is_lock(fd)
        real_close(fd)
        if was_lock:
            fire("os.close")

    def opener(real):
        def fake(file, *args, **kwargs):
            handle = real(file, *args, **kwargs)
            shown = fd_path(file) if isinstance(file, int) else abs_path(file)
            return _ReleaseWatch(handle, fire) if shown == lock else handle

        return fake

    monkeypatch.setattr(fcntl, "flock", flock)
    monkeypatch.setattr(os, "close", close)
    monkeypatch.setattr(io, "open", opener(io.open))
    monkeypatch.setattr(builtins, "open", opener(builtins.open))
    return fired


def _has_complete_backup(deck) -> bool:
    return any(
        not name.startswith(".") and (deck.backup_root / name / "manifest.json").is_file()
        for name in REAL["listdir"](deck.backup_root)
    )


def _all_hold(deck, contents: dict) -> bool:
    return all(_read(deck.files[key]) == data for key, data in contents.items())


def _lock_is_free(deck) -> bool:
    fd = REAL["os_open"](deck.backup_root / ".lock", os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return False
    finally:
        os.close(fd)
    return True


def _returned(call, *args, **kwargs):
    try:
        return call(*args, **kwargs)
    except KeyboardInterrupt as escaped:
        pytest.fail(f"the operation had succeeded but KeyboardInterrupt escaped: {escaped}")
    except safety.SafetyError as error:
        pytest.fail(f"the operation had succeeded but raised {error.code}: {error}")


@pytest.mark.parametrize("layout", LAYOUTS)
@pytest.mark.parametrize("how", HOWS)
def test_a24_ctrl_c_at_the_final_step_of_apply_still_returns_the_backup_id(
    tmp_path, monkeypatch, how, layout
):
    deck = make_deck(tmp_path, layout)
    changes = _changes(deck)
    before = deck_state(deck)
    names = target_folder_names(deck.writable)
    fired = _interrupt_on_lock_release(
        monkeypatch, deck, lambda: _all_hold(deck, NEW) and _has_complete_backup(deck), how
    )
    backup_id = _returned(safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    assert fired["at"], f"no lock release after the last write was seen: {fired['releases']}"
    assert isinstance(backup_id, str)
    assert complete_ids(safety.list_backups(str(deck.backup_root))) == [backup_id]
    _verify_complete(deck, backup_id)
    for key in KEYS:
        assert _read(deck.files[key]) == NEW[key], key
        assert mode_of(deck.files[key]) == 0o644, key
    assert target_folder_names(deck.writable) == names, "temp file left"
    assert _lock_is_free(deck), "the lock is still held after apply returned"
    safety.restore(backup_id, **deck.rkw())
    assert deck_state(deck) == before, "apply then restore is not a round trip"


@pytest.mark.parametrize("how", HOWS)
def test_a24_ctrl_c_at_the_final_step_of_restore_still_returns_its_result(
    tmp_path, monkeypatch, how
):
    deck = make_deck(tmp_path)
    before = deck_state(deck)
    backup_id = _apply(deck)
    fired = _interrupt_on_lock_release(monkeypatch, deck, lambda: _all_hold(deck, OLD), how)
    result = _returned(safety.restore, backup_id, **deck.rkw())
    monkeypatch.undo()
    assert fired["at"], f"no lock release after the last write was seen: {fired['releases']}"
    assert result["backup_id"] == backup_id
    assert sorted(result["restored"]) == sorted(str(deck.files[key]) for key in KEYS)
    assert result["skipped"] == []
    assert result["new_backup_id"] is None
    assert deck_state(deck) == before
    assert _lock_is_free(deck), "the lock is still held after restore returned"


@pytest.mark.parametrize("how", HOWS)
def test_a24_ctrl_c_at_the_final_step_of_cli_restore_prints_the_result_and_exits_0(
    tmp_path, monkeypatch, capsys, how
):
    deck = make_deck(tmp_path)
    before = deck_state(deck)
    backup_id = _apply(deck)
    serve_fake_proc(monkeypatch, deck.proc)
    fired = _interrupt_on_lock_release(monkeypatch, deck, lambda: _all_hold(deck, OLD), how)
    capsys.readouterr()
    try:
        code = safety.main(["restore", backup_id, "--backup-root", str(deck.backup_root)])
    except KeyboardInterrupt as escaped:
        pytest.fail(f"KeyboardInterrupt escaped from the CLI after a finished restore: {escaped}")
    monkeypatch.undo()
    out, err = capsys.readouterr()
    assert fired["at"], f"no lock release after the last write was seen: {fired['releases']}"
    assert code == 0, err
    assert "Traceback" not in err
    for key in KEYS:
        assert sha(OLD[key]) in out, f"the CLI did not print the result for {key}: {out}"
    assert deck_state(deck) == before


# ---------------------------------------------------------------------------- gid range


def _record_creations(monkeypatch) -> list[str]:
    """Every path created through os.open (O_CREAT or O_TMPFILE), open() with mode w/x/a,
    or os.mkdir. The calls still happen."""
    made: list[str] = []
    tmpfile = getattr(os, "O_TMPFILE", 0)
    real_os_open, real_io_open, real_mkdir = os.open, io.open, os.mkdir

    def shown(path, dir_fd=None) -> str:
        text = os.fsdecode(path)
        if dir_fd is not None and not Path(text).is_absolute():
            return abs_path(Path(fd_path(dir_fd), text))
        return abs_path(text)

    def os_open(path, flags, *args, **kwargs):
        if flags & os.O_CREAT or (tmpfile and flags & tmpfile == tmpfile):
            made.append(shown(path, kwargs.get("dir_fd")))
        return real_os_open(path, flags, *args, **kwargs)

    def any_open(file, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if not isinstance(file, int) and any(flag in mode for flag in "wxa"):
            made.append(shown(file))
        return real_io_open(file, *args, **kwargs)

    def mkdir(path, *args, **kwargs):
        made.append(shown(path, kwargs.get("dir_fd")))
        return real_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", os_open)
    monkeypatch.setattr(io, "open", any_open)
    monkeypatch.setattr(builtins, "open", any_open)
    monkeypatch.setattr(os, "mkdir", mkdir)
    return made


def _set_gid(deck, backup_id, gid) -> None:
    manifest = read_manifest(deck, backup_id)
    [item] = [item for item in manifest_files(manifest) if item["path"] == str(deck.config)]
    assert "gid" in item, f"the manifest records no gid (A23): {item}"
    item["gid"] = gid
    write_manifest(deck, backup_id, manifest)


BAD_GIDS = [2**32 - 1, 2**32, -1, "12", 1.5]
BAD_GID_IDS = ["2^32-1", "2^32", "minus1", "string12", "float1.5"]


@pytest.mark.parametrize("confirm", [frozenset(), frozenset({"overwrite"})], ids=["plain", "ow"])
@pytest.mark.parametrize("gid", BAD_GIDS, ids=BAD_GID_IDS)
def test_a24_restore_refuses_a_manifest_gid_out_of_range_before_any_write(
    tmp_path, monkeypatch, gid, confirm
):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck, ("config", "gus"))
    _set_gid(deck, backup_id, gid)
    lock = deck.backup_root / ".lock"
    lock.touch()
    before = deck_state(deck)
    names = target_folder_names([deck.config, deck.gus])
    backup_before = content_state(deck.backup_root, skip=[lock])
    made = _record_creations(monkeypatch)
    try:
        refusal("backup_corrupt", safety.restore, backup_id, **deck.rkw(confirm=confirm))
    finally:
        monkeypatch.undo()
    root = abs_path(deck.base)
    created = [
        path
        for path in made
        if (path == root or path.startswith(root + os.sep)) and path != abs_path(lock)
    ]
    assert created == [], f"restore created files before refusing: {created}"
    assert target_folder_names([deck.config, deck.gus]) == names, "temp file left"
    assert deck_state(deck) == before
    assert content_state(deck.backup_root, skip=[lock]) == backup_before
    assert _read(deck.config) == CONFIG_NEW


@pytest.mark.parametrize("gid", [0, 1000])
def test_a24_restore_accepts_gid_0_and_1000(tmp_path, caplog, gid):
    deck = make_deck(tmp_path)
    backup_id = _apply(deck, ("config",))
    _set_gid(deck, backup_id, gid)
    assert _record(deck, backup_id, deck.config)["gid"] == gid
    with caplog.at_level(logging.WARNING):
        result = safety.restore(backup_id, **deck.rkw())
    assert result["restored"] == [str(deck.config)]
    assert _read(deck.config) == CONFIG_INI
    assert mode_of(deck.config) == 0o644
    assert stat.S_ISREG(deck.config.lstat().st_mode)
    assert deck.config.stat().st_gid == gid or _group_warnings(caplog, deck.config), (
        f"group is {deck.config.stat().st_gid}, not {gid}, and no group_not_kept warning"
    )


# ---------------------------------------------------------------------------- symlinked arg


SYMLINK_SHAPES = ["link_to_install", "link_to_parent", "link_file", "linked_card_real_arg"]


def _deck_and_arg(tmp_path, shape: str) -> tuple:
    """A Deck and a cmdline argument that reaches the install folder through a link."""
    if shape == "linked_card_real_arg":
        deck = make_deck(tmp_path, "linked")
        real = Path(os.path.realpath(deck.install))
        assert str(real) != str(deck.install), "the linked layout has no link in install_path"
        return deck, str(real / "FakeGame.exe")
    deck = make_deck(tmp_path)
    links = deck.base / "links"
    links.mkdir()
    if shape == "link_to_install":
        link = links / "game"
        link.symlink_to(deck.install, target_is_directory=True)
        return deck, str(link / "FakeGame.exe")
    if shape == "link_to_parent":
        link = links / "common"
        link.symlink_to(deck.install.parent, target_is_directory=True)
        return deck, str(link / deck.install.name / "FakeGame.exe")
    if shape == "link_file":
        link = links / "launch.exe"
        link.symlink_to(deck.files["exe"])
        return deck, str(link)
    raise ValueError(shape)


def _hidden_game(deck, arg: str, monkeypatch) -> None:
    """A same-user, non-dumpable process: environ and exe unreadable, cmdline readable."""
    folder = add_process(
        deck.proc,
        GAME_PID,
        environ(HOME="/home/deck"),
        exe="/usr/bin/wine64-preloader",
        cmdline=cmdline_of("/usr/bin/wine64-preloader", arg),
    )
    make_unreadable(monkeypatch, folder / "environ", folder / "exe")


def _outside_proc(deck) -> dict:
    """The Deck outside backup_root and proc_root (the fake process's files are chmod 000
    and its exe link is unreadable while faked, so they are left out)."""
    return content_state(deck.base, skip=[deck.backup_root, deck.proc])


@pytest.mark.parametrize("shape", SYMLINK_SHAPES)
def test_a24_a_cmdline_path_reaching_the_install_through_a_link_is_game_running_at_apply(
    tmp_path, monkeypatch, shape
):
    deck, arg = _deck_and_arg(tmp_path, shape)
    changes = _changes(deck, ("config",))
    _hidden_game(deck, arg, monkeypatch)
    before = _outside_proc(deck)
    refusal("game_running", safety.apply, changes, **deck.kw())
    monkeypatch.undo()
    assert _outside_proc(deck) == before
    assert complete_ids(safety.list_backups(str(deck.backup_root))) == []


@pytest.mark.parametrize("shape", SYMLINK_SHAPES)
def test_a24_a_cmdline_path_reaching_the_install_through_a_link_is_game_running_at_restore(
    tmp_path, monkeypatch, shape
):
    deck, arg = _deck_and_arg(tmp_path, shape)
    backup_id = _apply(deck, ("config",))
    _hidden_game(deck, arg, monkeypatch)
    before = _outside_proc(deck)
    refusal("game_running", safety.restore, backup_id, **deck.rkw())
    monkeypatch.undo()
    assert _outside_proc(deck) == before
    assert _read(deck.config) == CONFIG_NEW


def test_a24_a_sibling_folder_reached_through_the_same_link_is_not_the_game(tmp_path, monkeypatch):
    deck = make_deck(tmp_path)
    sibling = deck.install.parent / f"{deck.install.name} 2"
    sibling.mkdir()
    (sibling / "FakeGame.exe").write_bytes(b"MZ")
    link = deck.base / "links" / "common"
    link.parent.mkdir()
    link.symlink_to(deck.install.parent, target_is_directory=True)
    _hidden_game(deck, str(link / sibling.name / "FakeGame.exe"), monkeypatch)
    backup_id = safety.apply(_changes(deck, ("config",)), **deck.kw())
    monkeypatch.undo()
    assert _read(deck.config) == CONFIG_NEW
    assert backup_id in complete_ids(safety.list_backups(str(deck.backup_root)))
