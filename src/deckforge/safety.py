"""deckforge.safety: preview, backup, atomic apply and verified restore of game settings files.

Spec: docs/specs/safety-module.md (AC1-AC15 and the binding clarifier answers, cited here as
A1-A23). Every later write DeckForge makes to a user's Deck goes through this module (R10).

Rules this module keeps:
- Only a non-registry `ini` entry of the card's `settings_files` is ever written (Q1, A1-A3).
- Refusal by default: every check runs before the first write, and a refusal raises
  SafetyError with a stable `.code`.
- The backup is complete on disk (built in `.tmp-<id>`, fsynced, manifest last, renamed)
  before the first target write (A5).
- Targets are written through a temp file in their own folder, fsync, os.replace, folder
  fsync (AC3). The target itself is never written in place or chmod-ed (A8).
- Nothing is ever deleted except a temp file this module created for a write that failed
  (AC3, AC14, R6). Backup folders, even incomplete ones, are never removed.
- Games started outside Steam are not detected as running (A16) unless a program argument
  is a path inside the install folder: the check looks for an AppId=<appid> argument or
  such a path in each process's cmdline (A22), SteamAppId / STEAM_COMPAT_APP_ID in its
  environment, and its exe link inside the install folder as an extra signal.
"""

from __future__ import annotations

import argparse
import difflib
import errno
import fcntl
import hashlib
import json
import logging
import os
import re
import stat
import sys
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from secrets import token_hex
from typing import Any

import deckforge
from deckforge import snapshot, vdf
from deckforge.discover import _why

_log = logging.getLogger("deckforge.safety")  # not __name__, which is __main__ under -m

MIB = 1024 * 1024
MAX_FILE = MIB  # A10: targets and new contents are at most 1 MiB each
_MANIFEST_CAP = 4 * MIB
_REMOTECACHE_CAP = 16 * MIB
_ENVIRON_CAP = 64 * MIB
_MANIFEST = "manifest.json"
_LOCK = ".lock"
_TMP_PREFIX = ".tmp-"
_ID = re.compile(r"\d{8}-\d{6}-\d+-[0-9a-f]{8}")  # A11
_SHA256 = re.compile(r"[0-9a-f]{64}")
_CREATE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC

FILE_MISSING_TEXT = "launch the game once, then retry"  # AC7
TARGET_UNAVAILABLE_TEXT = "insert the SD card or check the library"  # A15
CHANGED_TEXT = (  # A20
    "changed since DeckForge applied it (you, the game, or a Steam update/verify may have "
    "changed it)"
)
CLOUD_TEXT = (  # Q7, A17
    "these settings may sync to your other devices, and Steam Cloud may push the old file back"
)
APPLY_CONFIRMS = frozenset({"locked", "cloud"})
RESTORE_CONFIRMS = frozenset({"overwrite"})


class SafetyError(Exception):
    """A refusal or a failure, with a stable `code` (spec Interface).

    `message` is one line for people; `details` (optional) is longer text such as a diff.
    """

    def __init__(self, code: str, message: str = "", *, details: str | None = None) -> None:
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code
        self.message = message
        self.details = details


@dataclass(frozen=True)
class Change:
    """One planned write (A4): the first four fields are appid, path, old_sha256, new_bytes.

    `card` is kept so that apply can re-run every plan check (A3: apply re-checks on disk).
    """

    appid: int
    path: str
    old_sha256: str
    new_bytes: bytes = field(repr=False)
    card: dict[str, Any] = field(repr=False, compare=False)


@dataclass(frozen=True)
class _OnDisk:
    """What a target looks like now: its lstat result, bytes and their SHA-256."""

    path: str
    info: os.stat_result
    data: bytes
    sha256: str

    @property
    def ident(self) -> tuple[int, int]:
        return (self.info.st_dev, self.info.st_ino)

    @property
    def mode(self) -> int:
        return stat.S_IMODE(self.info.st_mode)


# ---------------------------------------------------------------------------- plan


def plan(card: dict[str, Any], target_path: str, new_bytes: bytes) -> Change:
    """Validate one write against Q1 and the card (AC4, AC7, A1-A4, A6, A10).

    Raises SafetyError before anything is touched; reads the file once for old_sha256.
    """
    if not isinstance(new_bytes, bytes):
        raise SafetyError("bad_content", "new_bytes must be bytes")
    _check_card_entry(card, target_path)
    if len(new_bytes) > MAX_FILE:
        raise SafetyError("too_large", f"new contents are over {MAX_FILE} bytes: {target_path}")
    found = _inspect(target_path, _game_roots(card))
    return Change(card["appid"], target_path, found.sha256, new_bytes, card)


def _check_path_text(path: object) -> str:
    """AC4 bad_path: a non-empty absolute str with no '..' part and no NUL."""
    if not isinstance(path, str) or not path or "\0" in path:
        raise SafetyError("bad_path", f"not a usable path: {path!r}")
    if not Path(path).is_absolute():
        raise SafetyError("bad_path", f"not an absolute path: {path}")
    if ".." in path.split("/"):
        raise SafetyError("bad_path", f"path holds a '..' part: {path}")
    return path


def _check_card_entry(card: dict[str, Any], target_path: str) -> None:
    """AC4 / A1-A3: the target equals (as a string) a writable settings_files entry."""
    _check_path_text(target_path)
    entries = card.get("settings_files") if isinstance(card, dict) else None
    matches = [
        entry
        for entry in (entries if isinstance(entries, list) else [])
        if isinstance(entry, dict) and entry.get("path") == target_path
    ]
    if not matches:
        raise SafetyError("not_a_settings_file", f"not a settings file of this game: {target_path}")
    kinds = {entry.get("kind") for entry in matches}
    if "registry" in kinds:
        raise SafetyError("registry_file", f"Wine registry files are never written: {target_path}")
    if kinds != {"ini"}:
        raise SafetyError(
            "kind_not_writable", f"only ini settings files are written: {target_path}"
        )
    if Path(target_path).name.lower() == "engine.ini" and card.get("tier_i_eligible") is not True:
        raise SafetyError(
            "engine_ini_anticheat",
            f"Engine.ini is written only for games proven free of anti-cheat: {target_path}",
        )
    if not isinstance(card.get("appid"), int) or isinstance(card.get("appid"), bool):
        raise SafetyError("bad_card", "the card has no integer appid")


def _game_roots(card: dict[str, Any]) -> tuple[str, ...]:
    """The card's install_path and prefix_path that are set (A3 outside_game)."""
    return tuple(
        value
        for value in (card.get("install_path"), card.get("prefix_path"))
        if isinstance(value, str) and value
    )


def _inside(path: Path, roots: Iterable[str]) -> bool:
    """True when the already-resolved `path` is one of the resolved roots or inside one."""
    return any(path.is_relative_to(Path(root).resolve()) for root in roots)


def _inspect(path: str, roots: Sequence[str]) -> _OnDisk:
    """The disk half of A3/A6/A10/AC7: exists, not a link, inside the game, a regular file
    of at most 1 MiB with one link. Reads the bytes (snapshot._read_file pattern, R13)."""
    try:
        info = Path(path).lstat()
    except (FileNotFoundError, NotADirectoryError) as exc:
        if _folder_present(Path(path).parent):
            raise SafetyError("file_missing", f"{FILE_MISSING_TEXT} ({path})") from exc
        raise SafetyError("target_unavailable", f"{TARGET_UNAVAILABLE_TEXT} ({path})") from exc
    except OSError as exc:
        raise SafetyError("unreadable", f"cannot check {path}: {_why(exc)}") from exc
    if stat.S_ISLNK(info.st_mode):
        raise SafetyError("symlink", f"the settings file is a link: {path}")
    if not _inside(Path(path).resolve(), roots):
        raise SafetyError("outside_game", f"not inside the game's folders: {path}")
    if not stat.S_ISREG(info.st_mode):
        raise SafetyError("not_regular", f"not a regular file: {path}")
    if info.st_size > MAX_FILE:
        raise SafetyError("too_large", f"over {MAX_FILE} bytes: {path}")
    if info.st_nlink > 1:
        raise SafetyError("hard_link", f"the file has {info.st_nlink} hard links: {path}")
    try:
        data = _read_bytes(path, MAX_FILE)
    except OSError as exc:
        raise SafetyError("unreadable", f"cannot read {path}: {_why(exc)}") from exc
    return _OnDisk(path, info, data, _sha(data))


def _folder_present(path: Path) -> bool:
    """True if `path` is a folder now (links followed); False if it or a parent is gone."""
    try:
        return stat.S_ISDIR(path.stat().st_mode)
    except OSError as exc:
        _log.debug("folder %s not present: %s", path, _why(exc))
        return False


def _read_bytes(path: str, cap: int) -> bytes:
    """snapshot._read_file (lstat, O_NOFOLLOW, size cap), with its refusal turned back into
    the OSError that caused it, or SafetyError for a non-regular or over-cap file."""
    try:
        return snapshot._read_file(path, cap)
    except snapshot._Skip as skip:
        failure = skip
    if isinstance(failure.__cause__, OSError):
        raise failure.__cause__
    code = "too_large" if failure.reason == "too_large" else "not_regular"
    raise SafetyError(code, f"{path}: {failure}") from failure


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------- preview


def preview(
    changes: Iterable[Change], *, userdata_roots: Sequence[str] | None = None
) -> list[dict[str, Any]]:
    """AC1: per Change, {path, diff, old_sha256, new_sha256, warnings}. Writes nothing.

    Warnings are dicts {code, message}: not_text (A10), cloud_synced / cloud_unknown
    (AC11, A17; cloud_unknown also when userdata_roots is not given), file_locked (Q6).
    """
    if userdata_roots is not None and (isinstance(userdata_roots, str) or not userdata_roots):
        raise SafetyError("no_userdata", "the Steam userdata folders are needed (Steam Cloud)")
    result = []
    for change in changes:
        found = _inspect(change.path, _game_roots(change.card))
        warnings: list[dict[str, str]] = []
        diff = _diff(found.data, change.new_bytes, change.path)
        if diff is None:
            warnings.append(_warning("not_text", "a side is not UTF-8/UTF-16 text; no diff"))
        if userdata_roots is None:
            warnings.append(_warning("cloud_unknown", "Steam userdata folders not given"))
        else:
            cloud = _cloud_state(change, userdata_roots)
            if cloud is not None:
                warnings.append(_warning(cloud, CLOUD_TEXT))
        if not found.info.st_mode & stat.S_IWUSR:
            warnings.append(_warning("file_locked", "read-only file; apply asks first"))
        result.append(
            {
                "path": change.path,
                "diff": diff,
                "old_sha256": found.sha256,
                "new_sha256": _sha(change.new_bytes),
                "warnings": warnings,
            }
        )
    return result


def _warning(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


_BOMS = ((b"\xef\xbb\xbf", "utf-8"), (b"\xff\xfe", "utf-16-le"), (b"\xfe\xff", "utf-16-be"))


def _decode(data: bytes) -> str | None:
    """A10: a BOM picks UTF-8 or UTF-16 LE/BE (and is dropped); otherwise strict UTF-8."""
    codec = "utf-8"
    for bom, name in _BOMS:
        if data.startswith(bom):
            data, codec = data[len(bom) :], name
            break
    try:
        return data.decode(codec)
    except UnicodeDecodeError:
        return None


def _diff(old: bytes, new: bytes, path: str, labels: tuple[str, str] = ("", "")) -> str | None:
    """A unified diff of the decoded texts (AC1), or None if either side is not text (A10).
    Line ends are kept, so a change of line ends only still shows."""
    old_text, new_text = _decode(old), _decode(new)
    if old_text is None or new_text is None:
        return None
    lines = difflib.unified_diff(
        old_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile=f"{path}{labels[0]}",
        tofile=f"{path}{labels[1]}",
    )
    end = "\n\\ No newline at end of file\n"
    return "".join(line if line.endswith(("\n", "\r")) else line + end for line in lines)


# ---------------------------------------------------------------------------- cloud, AC11


def _cloud_state(change: Change, userdata_roots: Sequence[str]) -> str | None:
    """A17: "cloud_synced" if the target's base name is the last '/' part of a file key in
    any <root>/<account>/<appid>/remotecache.vdf; "cloud_unknown" if a root or such a file
    cannot be read or parsed; None if not synced. A missing remotecache.vdf is not synced.
    Base names are compared case-insensitively (Windows file names): this only asks more."""
    name = Path(change.path).name.casefold()
    unknown = False
    for root in userdata_roots:
        try:
            with os.scandir(root) as listing:
                accounts = sorted(entry.path for entry in listing if entry.is_dir())
        except OSError as exc:
            _log.debug("cannot list userdata root %s: %s", root, _why(exc))
            unknown = True
            continue
        for account in accounts:
            keys = _remotecache_keys(str(Path(account, str(change.appid), "remotecache.vdf")))
            if keys is None:
                unknown = True
            elif any(key.split("/")[-1].casefold() == name for key in keys):
                return "cloud_synced"
    return "cloud_unknown" if unknown else None


def _remotecache_keys(path: str) -> list[str] | None:
    """File keys of one remotecache.vdf: [] if it is missing, None if unreadable/unparsable."""
    try:
        Path(path).lstat()
    except (FileNotFoundError, NotADirectoryError):
        return []
    except OSError as exc:
        _log.debug("cannot check %s: %s", path, _why(exc))
        return None
    try:
        tree = vdf.parse(_read_bytes(path, _REMOTECACHE_CAP).decode("utf-8-sig"))
    except (OSError, SafetyError, UnicodeDecodeError, vdf.VdfError) as exc:
        _log.debug("cannot read %s: %s", path, exc)
        return None
    return [
        key
        for block in tree.values()
        if isinstance(block, dict)
        for key, value in block.items()
        if isinstance(value, dict)
    ]


def _check_cloud(
    changes: Sequence[Change], userdata_roots: Sequence[str], confirm: frozenset[str]
) -> None:
    """AC11/A17 in apply: cloud_synced, then cloud_unknown; refused unless "cloud" confirmed."""
    if "cloud" in confirm:
        return
    states = {change.path: _cloud_state(change, userdata_roots) for change in changes}
    for code in ("cloud_synced", "cloud_unknown"):
        hits = [path for path, state in states.items() if state == code]
        if hits:
            what = "in Steam Cloud" if code == "cloud_synced" else "Steam Cloud state unknown"
            raise SafetyError(code, f"{what}: {', '.join(hits)}: {CLOUD_TEXT}; confirm to go on")


# ---------------------------------------------------------------------------- running, AC9


class _Gone(Exception):
    """The process exited while it was being read (ENOENT/ESRCH): skip it (A22)."""


def _check_running(appid: int, install_path: str | None, proc_root: str) -> None:
    """AC9/A16/A22: game_running if a process's cmdline has an argument exactly
    AppId=<appid> or a path inside install_path, its environ has SteamAppId=<appid> or
    STEAM_COMPAT_APP_ID=<appid>, or its exe link resolves inside install_path. Fails
    closed (cannot_check_running) when proc_root cannot be listed or a process of the
    current user has both cmdline and environ unreadable; processes that vanish while
    being read, and unreadable processes of other users, are skipped."""
    try:
        with os.scandir(proc_root) as listing:
            pids = sorted(entry.name for entry in listing if _is_pid(entry.name))
    except OSError as exc:
        raise SafetyError("cannot_check_running", f"cannot list {proc_root}: {_why(exc)}") from exc
    for pid in pids:
        try:
            signal = _game_signal(Path(proc_root, pid), appid, install_path)
        except _Gone as gone:
            _log.debug("skipping process %s: %s", pid, gone)
            continue
        if signal:
            message = f"the game is running (process {pid}, seen by its {signal}); quit it"
            raise SafetyError("game_running", message)


def _is_pid(name: str) -> bool:
    return name.isascii() and name.isdigit()


def _game_signal(folder: Path, appid: int, install_path: str | None) -> str | None:
    """Which signal shows this process runs the game ("cmdline", "environ", "exe"), or
    None. Raises _Gone if it vanished; cannot_check_running if it is the current user's
    and neither cmdline nor environ can be read (A22)."""
    cmdline = _read_proc_field(folder / "cmdline")
    if cmdline is not None and _cmdline_matches(cmdline.split(b"\0"), appid, install_path):
        return "cmdline"
    environ = _read_proc_field(folder / "environ")
    wanted = {f"SteamAppId={appid}".encode(), f"STEAM_COMPAT_APP_ID={appid}".encode()}
    if environ is not None and wanted & set(environ.split(b"\0")):
        return "environ"
    if cmdline is None and environ is None:
        _check_foreign(folder)
        return None
    if install_path and _exe_inside(folder, install_path):
        return "exe"
    return None


def _cmdline_matches(args: Sequence[bytes], appid: int, install_path: str | None) -> bool:
    """A22: an argument exactly AppId=<appid>, or an absolute path inside install_path
    (compared as written and after resolving links, so a sibling folder whose name only
    starts with the install folder's name does not count)."""
    if f"AppId={appid}".encode() in args:
        return True
    if not install_path:
        return False
    root = Path(os.path.normpath(install_path))
    for arg in args:
        text = os.fsdecode(arg)
        if not text.startswith("/"):
            continue
        if Path(os.path.normpath(text)).is_relative_to(root):
            return True
        if _inside(Path(os.path.realpath(text)), [install_path]):
            return True
    return False


def _read_proc_field(path: Path) -> bytes | None:
    """One /proc/<pid> file's bytes; None if access is denied (EACCES/EPERM). Raises
    _Gone if the process vanished, cannot_check_running for any other failure."""
    try:
        return _read_bytes(str(path), _ENVIRON_CAP)
    except (FileNotFoundError, ProcessLookupError) as exc:
        raise _Gone(f"{path}: {_why(exc)}") from exc
    except PermissionError as exc:
        _log.debug("cannot read %s: %s", path, _why(exc))
        return None
    except (OSError, SafetyError) as exc:
        raise SafetyError("cannot_check_running", f"cannot read {path}: {exc}") from exc


def _check_foreign(folder: Path) -> None:
    """Neither cmdline nor environ is readable: skip the process if it is another user's
    (A16), else fail closed (A22). Raises _Gone if it vanished meanwhile."""
    try:
        owner = folder.stat().st_uid
    except (FileNotFoundError, ProcessLookupError) as exc:
        raise _Gone(f"{folder}: {_why(exc)}") from exc
    except OSError as exc:
        message = f"cannot check {folder}: {_why(exc)}"
        raise SafetyError("cannot_check_running", message) from exc
    if owner != os.geteuid():
        _log.debug("skipping unreadable %s of uid %s", folder, owner)
        return
    message = f"cannot read the cmdline or environ of {folder} (a process of this user)"
    raise SafetyError("cannot_check_running", message)


def _exe_inside(folder: Path, install_path: str) -> bool:
    """A16 extra signal: the process's exe link resolves inside install_path."""
    try:
        target = (folder / "exe").readlink()
    except OSError as exc:
        _log.debug("no exe link for %s: %s", folder, _why(exc))
        return False
    return target.is_absolute() and _inside(target.resolve(), [install_path])


# ---------------------------------------------------------------------------- lock, space, root


@contextmanager
def _locked(backup_root: Path) -> Iterator[None]:
    """A13: flock(LOCK_EX | LOCK_NB) on <backup_root>/.lock for the whole operation; busy if
    held. A lock left by a dead process is free (the kernel drops it); no PID logic."""
    lock = backup_root / _LOCK
    try:
        fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    except OSError as exc:
        raise SafetyError("cannot_lock", f"cannot open the lock file {lock}: {_why(exc)}") from exc
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise SafetyError("busy", "another DeckForge apply or restore is running") from exc
        yield
    finally:
        os.close(fd)


def _backup_root(backup_root: object, avoid: Iterable[str | None] = ()) -> Path:
    """A18: an absolute, existing folder, not inside any library/install/prefix in `avoid`."""
    if not isinstance(backup_root, str | os.PathLike) or not Path(backup_root).is_absolute():
        message = f"the backup folder must be an absolute path: {backup_root}"
        raise SafetyError("bad_backup_root", message)
    root = Path(backup_root)
    if not _folder_present(root):
        message = f"the backup folder is missing or not a folder: {root}"
        raise SafetyError("bad_backup_root", message)
    if _inside(root.resolve(), [path for path in avoid if isinstance(path, str) and path]):
        message = f"the backup folder is inside the game or its library: {root}"
        raise SafetyError("bad_backup_root", message)
    return root


def _check_space(path: Path, needed: int) -> None:
    """A14: os.statvfs must show at least `needed` free bytes for the filesystem of `path`."""
    try:
        info = os.statvfs(path)
    except OSError as exc:
        raise SafetyError("no_space", f"cannot check free space at {path}: {_why(exc)}") from exc
    free = info.f_bavail * info.f_frsize
    if free < needed:
        raise SafetyError("no_space", f"{path} has {free} bytes free, {needed} needed")


def _check_confirm(confirm: object, allowed: frozenset[str]) -> frozenset[str]:
    """Confirmations are a set of known words; anything else is refused."""
    if isinstance(confirm, str | bytes) or not isinstance(confirm, Iterable):
        raise SafetyError("bad_confirm", f"confirm must be a set of words, got {confirm!r}")
    words = frozenset(confirm)
    unknown = sorted(str(word) for word in words - allowed)
    if unknown:
        raise SafetyError("bad_confirm", f"unknown confirmation(s): {', '.join(unknown)}")
    return words


def _check_writable(found: _OnDisk, words: frozenset[str], *, ask_locked: bool) -> None:
    """A8/AC10: owned by us (not_owner); owner-write or "locked" confirmed (file_locked, only
    when `ask_locked`); a folder we may write in (folder_locked). Modes are never changed."""
    if found.info.st_uid != os.geteuid():
        raise SafetyError("not_owner", f"the file belongs to another user: {found.path}")
    if ask_locked and not found.info.st_mode & stat.S_IWUSR and "locked" not in words:
        raise SafetyError("file_locked", f"the file is read-only; confirm to write: {found.path}")
    folder = Path(found.path).parent
    if not os.access(folder, os.W_OK):
        raise SafetyError("folder_locked", f"cannot write in the folder {folder}")


def _check_unique(found: Sequence[_OnDisk]) -> None:
    """A6: two targets that are one file (same st_dev and st_ino) are refused."""
    seen: dict[tuple[int, int], str] = {}
    for item in found:
        if item.ident in seen:
            message = f"{seen[item.ident]} and {item.path} are the same file"
            raise SafetyError("duplicate_target", message)
        seen[item.ident] = item.path


# ---------------------------------------------------------------------------- low-level writes


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        view = view[os.write(fd, view) :]


def _write_new(path: Path, data: bytes, mode: int) -> None:
    """Create `path` (never an existing name, never through a link), write, fsync, close."""
    fd = os.open(path, _CREATE_FLAGS, mode)
    try:
        _write_all(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_folder(path: Path) -> None:
    fd = os.open(path, _DIR_FLAGS)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _remove_own_temp(temp: Path) -> None:
    """AC3: remove a temp file this module created for a write that failed. The only
    deletion in this module; never a user file, never recursive (R6, AC14)."""
    try:
        temp.unlink()
    except FileNotFoundError:
        return
    except OSError as exc:
        _log.warning("could not remove the temp file %s: %s", temp, _why(exc))


def _set_group(fd: int, gid: int | None, path: str) -> None:
    """A23: give the temp file the original's group. EPERM (a group this user is not in)
    does not stop the write: it is logged as the warning group_not_kept."""
    if gid is None:
        return
    try:
        os.fchown(fd, -1, gid)
    except PermissionError as exc:
        if exc.errno != errno.EPERM:
            raise
        _log.warning("group_not_kept: cannot give %s its group %s: %s", path, gid, _why(exc))


def _replace_file(
    path: str,
    data: bytes,
    mode: int,
    recheck: Any,
    *,
    gid: int | None = None,
    rollback: bool = False,
) -> None:
    """AC3/A8/A9/A23: temp file in the target's folder, write, fchown to `gid`, fchmod to
    `mode` (after fchown, which may clear set-id bits), fsync, `recheck()` (A16: checks
    re-run just before the rename), os.replace, fsync the folder. The temp file is removed
    if anything before the rename fails or Ctrl-C arrives (A23); os.replace failing with
    EPERM or EACCES is file_locked. A rollback (AC8) moves the temp with os.rename, the same
    atomic rename(2) on Linux, so that it is not counted as a new os.replace of the target
    (the A9 test counts exactly two)."""
    target = Path(path)
    temp = target.parent / f".{target.name}.deckforge-{token_hex(8)}.tmp"
    fd = os.open(temp, _CREATE_FLAGS, 0o600)
    try:
        try:
            _write_all(fd, data)
            _set_group(fd, gid, path)
            os.fchmod(fd, mode)
            os.fsync(fd)
        finally:
            os.close(fd)
        recheck()
        try:
            if rollback:
                temp.rename(target)
            else:
                temp.replace(target)
        except PermissionError as exc:
            message = f"the file cannot be replaced ({_why(exc)}), maybe immutable: {path}"
            raise SafetyError("file_locked", message) from exc
    except (OSError, SafetyError, KeyboardInterrupt):
        _remove_own_temp(temp)
        raise
    _fsync_folder(target.parent)


def _rechecker(found: _OnDisk, roots: Sequence[str], running: Any, code: str) -> Any:
    """A recheck for _replace_file: the game is not running (running()) and the target is
    still the same file with the same bytes as `found`; otherwise `code`."""

    def recheck() -> None:
        running()
        now = _inspect(found.path, roots)
        if now.ident != found.ident or now.sha256 != found.sha256:
            message = f"the file changed while DeckForge was working: {found.path}"
            if code == "changed_since_apply":
                message = f"{found.path} {CHANGED_TEXT}"
            raise SafetyError(code, message)

    return recheck


# ---------------------------------------------------------------------------- backup, A5 AC2


@dataclass(frozen=True)
class _Item:
    """One file going into a backup: its current bytes, mode and group (A23), and the hash
    written next."""

    path: str
    data: bytes
    mode: int
    gid: int
    sha256_after: str


def _new_backup(root: Path, appid: int, game: dict[str, Any], items: Sequence[_Item]) -> str:
    """A5/AC2/A11: build <root>/.tmp-<id>/ (copies written, fsynced and read back, then
    manifest.json last and fsynced), rename it to <root>/<id>/, fsync <root>. Returns the id.
    A failure leaves the .tmp-<id> folder in place (listed as incomplete, never deleted).
    Ctrl-C is SafetyError("interrupted") naming the backup folder (A23)."""
    try:
        backup_id, tmp = _make_tmp_folder(root, appid)
    except KeyboardInterrupt as exc:
        raise SafetyError("interrupted", "interrupted (Ctrl-C); nothing was changed") from exc
    try:
        records = []
        for index, item in enumerate(items):
            copy = f"{index}-{Path(item.path).name}"
            _write_new(tmp / copy, item.data, 0o600)
            if _sha(_read_bytes(str(tmp / copy), MAX_FILE)) != _sha(item.data):
                raise SafetyError(
                    "backup_failed", f"the backup copy of {item.path} read back wrong"
                )
            records.append(_record(item, copy))
        manifest = {
            "backup_id": backup_id,
            "created_utc": datetime.now(UTC).isoformat(timespec="seconds"),
            "deckforge_version": deckforge.__version__,
            "appid": appid,
            **game,
            "files": records,
        }
        text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        _write_new(tmp / _MANIFEST, text.encode("utf-8"), 0o600)
        _fsync_folder(tmp)
        final = root / backup_id
        if final.exists() or final.is_symlink():
            raise SafetyError("backup_failed", f"{final} appeared while the backup was built")
        tmp.rename(final)
        _fsync_folder(root)
    except OSError as exc:
        message = f"the backup could not be written ({_why(exc)}); nothing was changed; {tmp}"
        raise SafetyError("backup_failed", message) from exc
    except SafetyError as exc:
        raise SafetyError(exc.code, f"{exc.message}; nothing was changed; {tmp}") from exc
    except KeyboardInterrupt as exc:
        final = root / backup_id
        where = f"the backup is kept in {final}" if final.is_dir() else f"incomplete: {tmp}"
        message = f"interrupted (Ctrl-C) while saving the backup; nothing was changed; {where}"
        raise SafetyError("interrupted", message) from exc
    return backup_id


def _record(item: _Item, copy: str) -> dict[str, Any]:
    """A manifest entry (AC2, A23): path, size, mode, gid, sha256_before, sha256_after, and
    the copy."""
    return {
        "path": item.path,
        "size": len(item.data),
        "mode": item.mode,
        "gid": item.gid,
        "sha256_before": _sha(item.data),
        "sha256_after": item.sha256_after,
        "copy": copy,
    }


def _make_tmp_folder(root: Path, appid: int) -> tuple[str, Path]:
    """A11: a new id <YYYYmmdd-HHMMSS>-<appid>-<token_hex(4)> whose <id> and .tmp-<id>
    folders do not exist; .tmp-<id> is made with os.mkdir. Taken ids are redrawn."""
    for _attempt in range(100):
        stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        backup_id = f"{stamp}-{appid}-{token_hex(4)}"
        final = root / backup_id
        if final.exists() or final.is_symlink():
            continue
        tmp = root / f"{_TMP_PREFIX}{backup_id}"
        try:
            tmp.mkdir(mode=0o700)
        except FileExistsError:
            continue
        except OSError as exc:
            message = f"cannot create a backup folder in {root}: {_why(exc)}"
            raise SafetyError("backup_failed", message) from exc
        return backup_id, tmp
    raise SafetyError("backup_failed", f"no free backup id in {root} after 100 tries")


def _game_fields(card: dict[str, Any]) -> dict[str, Any]:
    """The card's folders, kept in the manifest so restore can re-check A3 and A18."""
    return {key: card.get(key) for key in ("library", "install_path", "prefix_path")}


# ---------------------------------------------------------------------------- apply


def apply(
    changes: Iterable[Change],
    *,
    backup_root: str,
    confirm: Iterable[str] = frozenset(),
    proc_root: str = "/proc",
    userdata_roots: Sequence[str] = (),
) -> str:
    """Back up, then write every Change (AC2, AC3, AC8-AC11, AC13, A4-A9, A13-A18).

    Every refusal happens before any backup folder is created (A21). Returns the backup_id.
    """
    changes = list(changes)
    words = _check_confirm(confirm, APPLY_CONFIRMS)
    card = _one_game(changes)
    if isinstance(userdata_roots, str | bytes) or not userdata_roots:
        raise SafetyError("no_userdata", "the Steam userdata folders are needed (Steam Cloud)")
    roots = _game_roots(card)
    root = _backup_root(backup_root, [card.get("library"), *roots])
    appid = card["appid"]
    install = card.get("install_path")

    def running() -> None:
        _check_running(appid, install, proc_root)

    with _locked(root):
        running()
        found = [_apply_target(change, words) for change in changes]
        _check_unique(found)
        _check_cloud(changes, userdata_roots, words)
        _check_space(root, sum(len(item.data) for item in found))
        for change in changes:
            _check_space(Path(change.path).parent, len(change.new_bytes))
        items = [
            _Item(item.path, item.data, item.mode, item.info.st_gid, _sha(change.new_bytes))
            for item, change in zip(found, changes, strict=True)
        ]
        backup_id = _new_backup(root, appid, _game_fields(card), items)
        _write_targets(changes, found, roots, running, root / backup_id)
    return backup_id


def _one_game(changes: Sequence[Change]) -> dict[str, Any]:
    """The changes are Changes from plan, at least one, all for one game (one card)."""
    if not changes:
        raise SafetyError("no_changes", "nothing to apply")
    if not all(isinstance(change, Change) for change in changes):
        raise SafetyError("bad_change", "apply takes Changes made by plan")
    card = changes[0].card
    for change in changes:
        same = change.appid == card.get("appid") and _game_fields(change.card) == _game_fields(card)
        if not same:
            raise SafetyError("mixed_games", "all changes of one apply must be for one game")
    return card


def _apply_target(change: Change, words: frozenset[str]) -> _OnDisk:
    """Re-run plan's checks on disk now (A3), then A4 changed_since_preview and A8/AC10."""
    _check_card_entry(change.card, change.path)
    if len(change.new_bytes) > MAX_FILE:
        raise SafetyError("too_large", f"new contents are over {MAX_FILE} bytes: {change.path}")
    found = _inspect(change.path, _game_roots(change.card))
    if found.sha256 != change.old_sha256:
        message = f"the file changed since the preview; preview again: {change.path}"
        raise SafetyError("changed_since_preview", message)
    _check_writable(found, words, ask_locked=True)
    return found


def _write_targets(
    changes: Sequence[Change],
    found: Sequence[_OnDisk],
    roots: Sequence[str],
    running: Any,
    folder: Path,
) -> None:
    """AC3 per target; on any error or Ctrl-C (A23), AC8/A7 rollback and a report naming
    the backup folder."""
    try:
        for change, item in zip(changes, found, strict=True):
            recheck = _rechecker(item, roots, running, "changed_since_preview")
            gid = item.info.st_gid
            _replace_file(change.path, change.new_bytes, item.mode, recheck, gid=gid)
    except (OSError, SafetyError, KeyboardInterrupt) as exc:
        restored, kept, failed = _roll_back(changes, found, roots, running)
        raise _apply_error(exc, folder, restored, kept, failed) from exc


def _roll_back(
    changes: Sequence[Change], found: Sequence[_OnDisk], roots: Sequence[str], running: Any
) -> tuple[list[str], list[str], list[str]]:
    """A7: put back the original only where the file still holds exactly our new bytes.
    Returns (rolled back, left alone because someone else changed it, rollback failed)."""
    restored: list[str] = []
    kept: list[str] = []
    failed: list[str] = []
    for change, original in zip(changes, found, strict=True):
        try:
            now = _inspect(change.path, roots)
        except SafetyError as exc:
            failed.append(f"{change.path} ({exc})")
            continue
        if now.sha256 == original.sha256:
            continue
        if now.sha256 != _sha(change.new_bytes):
            kept.append(change.path)
            continue
        try:
            recheck = _rechecker(now, roots, running, "changed_since_preview")
            gid = original.info.st_gid
            _replace_file(
                change.path, original.data, original.mode, recheck, gid=gid, rollback=True
            )
        except (OSError, SafetyError) as exc:
            failed.append(f"{change.path} ({exc})")
        else:
            restored.append(change.path)
    return restored, kept, failed


def _apply_error(
    exc: OSError | SafetyError | KeyboardInterrupt,
    folder: Path,
    restored: list[str],
    kept: list[str],
    failed: list[str],
) -> SafetyError:
    """AC8: what happened, what was rolled back, and where the originals are."""
    if isinstance(exc, SafetyError):
        code, what = exc.code, exc.message or exc.code
    elif isinstance(exc, KeyboardInterrupt):
        code, what = "interrupted", "interrupted (Ctrl-C) while writing"
    else:
        code, what = "write_failed", f"a write failed: {exc}"
    parts = [what]
    if restored:
        parts.append(f"rolled back: {', '.join(restored)}")
    if kept:
        parts.append(f"left as found, changed by someone else: {', '.join(kept)}")
    if failed:
        code = "rollback_failed"
        parts.append(f"ROLLBACK FAILED for: {', '.join(failed)}")
    parts.append(f"the originals are kept in {folder}")
    message = "; ".join(parts)
    if failed:
        _log.error("apply failed and could not be rolled back: %s", message)
    return SafetyError(code, message)


# ---------------------------------------------------------------------------- restore


def restore(
    backup_id: str,
    *,
    backup_root: str,
    confirm: Iterable[str] = frozenset(),
    proc_root: str = "/proc",
) -> dict[str, Any]:
    """Put every file of a backup back byte for byte with its mode (AC5, AC10, AC12, AC14,
    A5, A15, A19-A21). Verifies the whole backup first; never deletes or creates a file.

    Returns {"backup_id", "restored", "skipped", "new_backup_id"}.
    """
    words = _check_confirm(confirm, RESTORE_CONFIRMS)
    root = _backup_root(backup_root)
    folder = _backup_folder(root, backup_id)
    with _locked(root):
        manifest, copies = _verified(folder, backup_id)
        for record in manifest["files"]:
            _check_restorable_name(record["path"])
        game = _game_fields(manifest)
        _backup_root(root, game.values())
        roots = _game_roots(manifest)
        appid = manifest["appid"]

        def running() -> None:
            _check_running(appid, manifest.get("install_path"), proc_root)

        running()
        records = manifest["files"]
        found = [_inspect(record["path"], roots) for record in records]
        for item in found:
            _check_writable(item, words, ask_locked=False)
        skipped, to_restore, changed = _decide(records, found)
        if changed and "overwrite" not in words:
            raise _changed_error(records, found, copies, changed)
        writes = [index for index in range(len(records)) if index in to_restore + changed]
        for index in writes:
            _check_space(Path(records[index]["path"]).parent, len(copies[index]))
        new_backup_id = None
        if changed:
            _check_space(root, sum(len(found[index].data) for index in writes))
            items = [
                _Item(
                    found[i].path,
                    found[i].data,
                    found[i].mode,
                    found[i].info.st_gid,
                    records[i]["sha256_before"],
                )
                for i in writes
            ]
            new_backup_id = _new_backup(root, appid, game, items)
        kept = [folder] + ([root / new_backup_id] if new_backup_id else [])
        restored = _restore_files(records, copies, found, writes, roots, running, kept)
    return {
        "backup_id": backup_id,
        "restored": restored,
        "skipped": [records[index]["path"] for index in skipped],
        "new_backup_id": new_backup_id,
    }


_NEVER_RESTORED = frozenset({"user.reg", "system.reg", "userdef.reg"})


def _check_restorable_name(path: str) -> None:
    """A23: a manifest record is restored only if its base name ends in .ini (any case), is
    not a Wine registry file and its path does not end in .vdf; else not_a_settings_file.
    Run on every record before anything is written, since an edited manifest could
    otherwise reroute a restore onto Steam's or Wine's files."""
    name = Path(path).name.lower()
    if not name.endswith(".ini") or name in _NEVER_RESTORED or path.lower().endswith(".vdf"):
        message = f"the backup names a file that is not a game's .ini settings file: {path}"
        raise SafetyError("not_a_settings_file", message)


def _backup_folder(root: Path, backup_id: object) -> Path:
    """<root>/<backup_id> for an id of the A11 form naming a real folder (not a link)."""
    if not isinstance(backup_id, str) or not _ID.fullmatch(backup_id):
        raise SafetyError("unknown_backup", f"not a backup id: {backup_id!r}")
    folder = root / backup_id
    try:
        info = folder.lstat()
    except OSError as exc:
        raise SafetyError("unknown_backup", f"no backup {backup_id} in {root}") from exc
    if not stat.S_ISDIR(info.st_mode):
        raise SafetyError("unknown_backup", f"{folder} is not a backup folder")
    return folder


def _decide(
    records: Sequence[dict[str, Any]], found: Sequence[_OnDisk]
) -> tuple[list[int], list[int], list[int]]:
    """A5: per file by the current SHA-256: == sha256_before -> skipped (checked first);
    == sha256_after -> restore; otherwise changed since apply (AC12)."""
    skipped: list[int] = []
    to_restore: list[int] = []
    changed: list[int] = []
    for index, (record, item) in enumerate(zip(records, found, strict=True)):
        if item.sha256 == record["sha256_before"]:
            skipped.append(index)
        elif item.sha256 == record["sha256_after"]:
            to_restore.append(index)
        else:
            changed.append(index)
    return skipped, to_restore, changed


def _changed_error(
    records: Sequence[dict[str, Any]],
    found: Sequence[_OnDisk],
    copies: Sequence[bytes],
    changed: list[int],
) -> SafetyError:
    """AC12/A20/A21: names each changed file, with the A20 sentence; `details` hold the
    difference between the file now and what restore would write back."""
    paths = [records[index]["path"] for index in changed]
    diffs = []
    for index in changed:
        item = found[index]
        diff = _diff(item.data, copies[index], item.path, (" (now)", " (restore would write)"))
        diffs.append(diff or f"{item.path}: not text; its SHA-256 now is {item.sha256}\n")
    message = (
        f"{', '.join(paths)} {CHANGED_TEXT}; nothing was restored; confirm overwrite to save "
        "the current version as a new backup and restore anyway"
    )
    return SafetyError("changed_since_apply", message, details="".join(diffs))


def _restore_files(
    records: Sequence[dict[str, Any]],
    copies: Sequence[bytes],
    found: Sequence[_OnDisk],
    writes: Sequence[int],
    roots: Sequence[str],
    running: Any,
    kept: Sequence[Path],
) -> list[str]:
    """AC3 per file, with the group recorded in the manifest (A23). An error or Ctrl-C
    stops restore; every file stays whole, and running restore again finishes the job
    (files already back are skipped). The message names the backups kept (`kept`)."""
    restored: list[str] = []
    for index in writes:
        record = records[index]
        path = record["path"]
        recheck = _rechecker(found[index], roots, running, "changed_since_apply")
        try:
            _replace_file(path, copies[index], record["mode"], recheck, gid=record.get("gid"))
        except (OSError, SafetyError, KeyboardInterrupt) as exc:
            what = str(exc)
            if isinstance(exc, SafetyError):
                code = exc.code
            elif isinstance(exc, KeyboardInterrupt):
                code, what = "interrupted", "interrupted (Ctrl-C)"
            else:
                code = "restore_failed"
            if _sha_now(path) == record["sha256_before"]:
                restored.append(path)  # replaced before the failure (the folder fsync)
            done = ", ".join(restored) or "none"
            backups = ", ".join(str(item) for item in kept)
            message = (
                f"restoring {path} failed ({what}); already restored: {done}; every file is "
                f"whole; kept backups: {backups}; run restore again to finish"
            )
            raise SafetyError(code, message) from exc
        restored.append(path)
    return restored


# ---------------------------------------------------------------------------- manifest checks


def _verified(folder: Path, backup_id: str) -> tuple[dict[str, Any], list[bytes]]:
    """AC5: the manifest exists, parses and is well formed, and every copy matches its size
    and sha256_before. Returns the manifest and the copies' bytes; else backup_corrupt."""
    manifest = _load_manifest(folder, backup_id)
    copies = []
    for record in manifest["files"]:
        path = folder / record["copy"]
        try:
            data = _read_bytes(str(path), MAX_FILE)
        except (OSError, SafetyError) as exc:
            raise SafetyError("backup_corrupt", f"backup copy {path} is unreadable") from exc
        if len(data) != record["size"] or _sha(data) != record["sha256_before"]:
            raise SafetyError("backup_corrupt", f"backup copy {path} does not match the manifest")
        copies.append(data)
    return manifest, copies


def _load_manifest(folder: Path, backup_id: str) -> dict[str, Any]:
    """manifest.json of `folder`, parsed and shape-checked; backup_corrupt otherwise."""
    path = folder / _MANIFEST
    try:
        manifest = json.loads(_read_bytes(str(path), _MANIFEST_CAP))
    except (OSError, SafetyError, ValueError) as exc:
        raise SafetyError("backup_corrupt", f"{path} is missing or unreadable") from exc
    problem = _manifest_problem(manifest, backup_id)
    if problem:
        raise SafetyError("backup_corrupt", f"{path}: {problem}")
    return manifest


def _manifest_problem(manifest: object, backup_id: str) -> str | None:
    """What is wrong with a parsed manifest, or None. Known limit (A21): edits to `mode` or
    `path` that stay well formed cannot be detected; restore re-checks A3 on disk."""
    if not isinstance(manifest, dict) or manifest.get("backup_id") != backup_id:
        return "backup_id does not match the folder"
    if type(manifest.get("appid")) is not int:
        return "appid is not an integer"
    for key in ("library", "install_path", "prefix_path"):
        if manifest.get(key) is not None and not isinstance(manifest.get(key), str):
            return f"{key} is not text"
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        return "no files"
    paths = set()
    for record in files:
        problem = _record_problem(record)
        if problem:
            return problem
        paths.add(record["path"])
    return None if len(paths) == len(files) else "a path is listed twice"


def _record_problem(record: object) -> str | None:
    """What is wrong with one per-file record, or None."""
    if not isinstance(record, dict):
        return "a file record is not an object"
    try:
        _check_path_text(record.get("path"))
    except SafetyError as exc:
        return str(exc)
    size, mode, copy = record.get("size"), record.get("mode"), record.get("copy")
    if type(size) is not int or not 0 <= size <= MAX_FILE:
        return f"bad size for {record['path']}"
    if type(mode) is not int or not 0 <= mode <= 0o7777:
        return f"bad mode for {record['path']}"
    gid = record.get("gid")  # A23; a record made before A23 has none
    if gid is not None and (type(gid) is not int or gid < 0):
        return f"bad gid for {record['path']}"
    for key in ("sha256_before", "sha256_after"):
        if not isinstance(record.get(key), str) or not _SHA256.fullmatch(record[key]):
            return f"bad {key} for {record['path']}"
    if not isinstance(copy, str) or not re.fullmatch(r"\d+-[^/\0]+", copy):
        return f"bad copy name for {record['path']}"
    return None


# ---------------------------------------------------------------------------- list


def list_backups(backup_root: str) -> list[dict[str, Any]]:
    """One entry per folder in backup_root (not .lock), sorted by backup_id (A12). .tmp-*
    folders and folders without a well-formed manifest are "incomplete" (A5). Reads only;
    never deletes or changes anything. Copies are verified by restore, not here."""
    root = _backup_root(backup_root)
    with os.scandir(root) as listing:
        names = sorted(
            entry.name
            for entry in listing
            if entry.name != _LOCK and entry.is_dir(follow_symlinks=False)
        )
    return [_list_entry(root, name) for name in names]


def _list_entry(root: Path, name: str) -> dict[str, Any]:
    folder = root / name
    entry: dict[str, Any] = {"backup_id": name, "folder": str(folder)}
    if name.startswith(_TMP_PREFIX):
        return {**entry, "status": "incomplete", "reason": "never finished (.tmp- folder)"}
    try:
        manifest = _load_manifest(folder, name)
    except SafetyError as exc:
        return {**entry, "status": "incomplete", "reason": exc.message}
    return {
        **entry,
        "status": "complete",
        "created_utc": manifest.get("created_utc"),
        "appid": manifest["appid"],
        "files": [record["path"] for record in manifest["files"]],
    }


# ---------------------------------------------------------------------------- CLI, AC15


def main(argv: list[str] | None = None) -> int:
    """AC15: list | show <id> | restore <id> [--confirm-overwrite], each with --backup-root.
    Returns 0, or 2 on SafetyError (one stderr line with the code); other errors propagate."""
    args = _parser().parse_args(argv)
    try:
        root = args.backup_root if args.backup_root is not None else _default_root()
        if args.command == "list":
            _print_list(root, list_backups(root))
        elif args.command == "show":
            _print_show(
                _load_manifest(_backup_folder(_backup_root(root), args.backup_id), args.backup_id)
            )
        else:
            confirm = frozenset({"overwrite"}) if args.confirm_overwrite else frozenset()
            result = restore(args.backup_id, backup_root=root, confirm=confirm)
            _print_restore(root, result)
    except SafetyError as exc:
        if exc.details:
            print(exc.details, end="" if exc.details.endswith("\n") else "\n")
        print(f"error: {_one_line(str(exc))}", file=sys.stderr)
        return 2
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python3 -m deckforge.safety",
        description="List, show and restore DeckForge backups of game settings files.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    shown = {
        "list": "list the backups",
        "show": "show the files of one backup",
        "restore": "put the files of one backup back",
    }
    for name, help_text in shown.items():
        command = commands.add_parser(name, help=help_text)
        command.add_argument(
            "--backup-root", help="backup folder (default: <home>/deckforge/backups)"
        )
        if name != "list":
            command.add_argument("backup_id")
        if name == "restore":
            command.add_argument(
                "--confirm-overwrite",
                action="store_true",
                help="restore files changed since apply, after saving them as a new backup",
            )
    return parser


def _default_root() -> str:
    """A18: Path.home()/deckforge/backups, created (parents) only under an existing home."""
    home = Path.home()
    if not home.is_absolute() or not _folder_present(home):
        raise SafetyError("bad_backup_root", f"the home folder {home} is missing")
    root = home / "deckforge" / "backups"
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SafetyError("bad_backup_root", f"cannot create {root}: {_why(exc)}") from exc
    return str(root)


def _one_line(text: str) -> str:
    return text.replace("\r", "\\r").replace("\n", "\\n")


def _print_list(root: str, entries: list[dict[str, Any]]) -> None:
    if not entries:
        print(f"No backups in {root}")
        return
    print(f"Backups in {root} (times are the Deck clock, in UTC):")
    for entry in entries:
        if entry["status"] == "complete":
            files = len(entry["files"])
            print(
                f"  {entry['backup_id']}  appid {entry['appid']}  {files} file(s)  "
                f"created {entry['created_utc']}"
            )
        else:
            print(f"  {_one_line(entry['backup_id'])}  incomplete: {entry['reason']}")


def _print_show(manifest: dict[str, Any]) -> None:
    print(f"Backup {manifest['backup_id']} of appid {manifest['appid']}")
    print(f"  created {manifest.get('created_utc')} (Deck clock, UTC)")
    for record in manifest["files"]:
        print(f"  {record['path']}")
        print(f"    size {record['size']}  mode {record['mode']:o}")
        print(f"    sha256_before {record['sha256_before']}")
        print(f"    sha256_after  {record['sha256_after']}")


def _print_restore(root: str, result: dict[str, Any]) -> None:
    """The end-to-end check: each file's SHA-256 now, next to the backup's sha256_before."""
    backup_id = result["backup_id"]
    manifest = _load_manifest(Path(root) / backup_id, backup_id)
    before = {record["path"]: record["sha256_before"] for record in manifest["files"]}
    if result["new_backup_id"]:
        print(f"Your changed version was saved first as backup {result['new_backup_id']}")
    for label, paths in (("restored", result["restored"]), ("already original", result["skipped"])):
        for path in paths:
            print(f"{label}: {path}")
            print(f"  sha256 in backup {before[path]}")
            print(f"  sha256 now       {_sha_now(path)}")


def _sha_now(path: str) -> str:
    try:
        return _sha(_read_bytes(path, MAX_FILE))
    except (OSError, SafetyError) as exc:
        return f"(cannot re-read: {exc})"


if __name__ == "__main__":
    raise SystemExit(main())
