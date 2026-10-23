# Shared fixtures, fakes and readers for the deckforge.safety tests
# (docs/specs/safety-module.md, AC1-AC15 and the binding clarifier answers 1-20, written
# here as A1-A20). This file holds no tests. The contracts sit at the top of each file:
#   test_safety_plan.py     plan, Change, preview          AC1 AC4 AC7 A1-A4 A10
#   test_safety_apply.py    apply: backup, atomic write    AC2 AC3 AC8 AC10 A5-A9 A11 A14
#   test_safety_guards.py   apply/restore refusals         AC9 AC11 AC13 A13-A18
#   test_safety_restore.py  restore, list_backups          AC5 AC6 AC10 AC12 AC14 A5 A12
#                                                          A19 A20
#   test_safety_cli.py      main                           AC15 A18
#
# Everything lives under pytest's tmp_path; nothing reads or writes a real Steam install
# (R7) and nothing is deleted outside tmp_path (R6). The game card is built by the real
# deckforge.detect.card_fields over a fake install and prefix, so its shape is exactly what
# discover produces (appid, name, library, install_path, prefix_path, anticheat,
# tier_i_eligible, settings_files [{path, class, kind}]).
#
# Fakes, and how they work:
#   proc_root      a folder of <pid>/environ files (NUL-separated KEY=VALUE) and optional
#                  <pid>/exe links, plus non-pid entries ("self", "sys", "version") that
#                  real /proc also has.
#   unreadable     opens of one path through os.open, io.open and builtins.open raise
#                  PermissionError(EACCES), as real /proc does for another user's environ;
#                  the file is also chmod 000 (enough on its own when not root).
#   other owner    os.stat / os.lstat / os.fstat, and the stat() of entries os.scandir
#                  yields, report st_uid = <current uid> + 4242 for the chosen paths; when
#                  the tests run as root the paths are also really chowned to that uid.
#   statvfs        os.statvfs (shutil.disk_usage uses it too) reports 0 free blocks
#                  (full_disk), or exactly N free bytes in 1-byte blocks (low_disk), for
#                  paths inside the chosen folders.
#   process death  simulate_exit: after a Crash, collect dropped file objects and close
#                  every fd still open under the Deck (frees a held flock), as the kernel
#                  does when a process dies.
#   deletions      record_deletions: every os.unlink / remove / rmdir / removedirs and
#                  shutil.rmtree call is recorded (and still performed).
#   lock holder    a second Python process that holds fcntl.flock(LOCK_EX) on
#                  <backup_root>/.lock until its stdin is closed.
#   Recorder       counts every write-side step that touches the fixture (os.replace,
#                  os.rename, os.fsync, os.write, os.sendfile, os.copy_file_range, os.mkdir,
#                  os.chmod, os.fchmod and write() on files opened for writing through
#                  io.open / builtins.open / os.fdopen) and can raise at step k: OSError
#                  (an error the code must handle) or Crash, a BaseException that models
#                  the process dying (no handler of the code under test may swallow it).
#                  fd paths come from /proc/self/fd (Linux).
#
# Readers for shapes the spec does not name (ASSUMED, see the report):
#   - manifest.json per-file records: the "files" list if present, otherwise the one list
#     of objects that all hold a "path" key.
#   - backup copies: found by content (any regular file in the backup folder other than
#     manifest.json), since the spec does not name them.
#   - list_backups entries: dicts; the entry of a folder holds its name as "backup_id" or
#     as the last part of a string value; "incomplete" is any of: a value equal to
#     "incomplete", "incomplete": True, or "complete": False.
#   - preview warnings: a list of str codes, or of dicts with a "code".

from __future__ import annotations

import builtins
import errno
import gc
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from test_discover_output import put

from deckforge import detect

APPID = 2246340
OTHER_APPID = 1061090
ACCOUNT = "12345678"
SECOND_ACCOUNT = "87654321"
MiB = 1024 * 1024
FOREIGN_UID_OFFSET = 4242

CONFIG_INI = b"[Render]\r\nUpscaler=FSR\r\nFrameGen=Off\r\nShadow=High\r\n"
CONFIG_NEW = b"[Render]\r\nUpscaler=DLSS\r\nFrameGen=Off\r\nShadow=High\r\n"
GUS_INI = b"[/Script/Engine.GameUserSettings]\nResolutionSizeX=1280\nResolutionSizeY=800\n"
GUS_NEW = b"[/Script/Engine.GameUserSettings]\nResolutionSizeX=960\nResolutionSizeY=600\n"
ENGINE_INI = b"[SystemSettings]\nr.Shadow.MaxResolution=1024\n"
ENGINE_NEW = b"[SystemSettings]\nr.Shadow.MaxResolution=512\n"
BOOT_CONFIG = b"gfx-enable-gfx-jobs=1\n"
USER_REG = b"WINE REGISTRY Version 2\n[Software\\\\Fake] 1700000000\n"
SAVE = b"SAVE\x00\x01\x02"

FILE_MISSING_TEXT = "launch the game once, then retry"
TARGET_UNAVAILABLE_TEXT = "insert the SD card or check the library"
CHANGED_TEXT = (
    "changed since DeckForge applied it (you, the game, or a Steam update/verify may have "
    "changed it)"
)
CLOUD_TEXT = "may sync to your other devices"

# A11: <YYYYmmdd-HHMMSS>-<appid>-<8 hex from secrets.token_hex(4)> (lowercase hex).
ID_PATTERN = re.compile(rf"^(\d{{8}}-\d{{6}})-{APPID}-([0-9a-f]{{8}})$")

LAYOUTS = ("steam", "sd", "flatpak", "linked")

REAL = {
    "replace": os.replace,
    "rename": os.rename,
    "fsync": os.fsync,
    "write": os.write,
    "sendfile": os.sendfile,
    "copy_file_range": getattr(os, "copy_file_range", None),
    "mkdir": os.mkdir,
    "chmod": os.chmod,
    "fchmod": os.fchmod,
    "io_open": io.open,
    "builtins_open": builtins.open,
    "os_open": os.open,
    "stat": os.stat,
    "lstat": os.lstat,
    "fstat": os.fstat,
    "access": os.access,
    "statvfs": os.statvfs,
    "scandir": os.scandir,
    "listdir": os.listdir,
    "unlink": os.unlink,
    "remove": os.remove,
    "rmdir": os.rmdir,
}


class Crash(BaseException):
    """The process dies here: not an Exception, so no `except Exception` may catch it."""


# ---------------------------------------------------------------------------- the Deck


@dataclass
class Deck:
    base: Path
    library: Path
    steam_root: Path
    install: Path
    prefix: Path
    home: Path
    backup_root: Path
    proc: Path
    userdata: Path
    card: dict[str, Any]
    files: dict[str, Path] = field(default_factory=dict)

    @property
    def config(self) -> Path:
        return self.files["config"]

    @property
    def gus(self) -> Path:
        return self.files["gus"]

    @property
    def engine(self) -> Path:
        return self.files["engine"]

    @property
    def writable(self) -> list[Path]:
        """The card's three ini files that plan accepts on this (tier I eligible) card."""
        return [self.config, self.gus, self.engine]

    def kw(self, **overrides: Any) -> dict[str, Any]:
        """Keyword arguments for apply."""
        base = {
            "backup_root": str(self.backup_root),
            "proc_root": str(self.proc),
            "userdata_roots": (str(self.userdata),),
        }
        base.update(overrides)
        return base

    def rkw(self, **overrides: Any) -> dict[str, Any]:
        """Keyword arguments for restore."""
        base = {"backup_root": str(self.backup_root), "proc_root": str(self.proc)}
        base.update(overrides)
        return base


def _library_for(base: Path, layout: str) -> tuple[Path, Path]:
    """(library as the card names it, Steam root holding config/ and userdata/)."""
    home_steam = base / "home" / ".local" / "share" / "Steam"
    if layout == "steam":
        return home_steam, home_steam
    if layout == "sd":  # SD-card library, a name with a space and non-English characters
        return base / "run" / "media" / "deck" / "SD Kártya 大", home_steam
    if layout == "flatpak":
        flat = base / "home" / ".var" / "app" / "com.valvesoftware.Steam" / ".local"
        flat = flat / "share" / "Steam"
        return flat, flat
    if layout == "linked":  # the library is reached through a link in a parent folder
        real = base / "mnt" / "real library"
        real.mkdir(parents=True)
        home_steam.parent.mkdir(parents=True)
        home_steam.symlink_to(real, target_is_directory=True)
        return home_steam, home_steam
    raise ValueError(layout)


def remotecache(appid: int, keys: Iterable[str]) -> str:
    """A remotecache.vdf whose file keys are `keys`."""
    lines = [f'"{appid}"', "{", '\t"ChangeNumber"\t\t"7"', '\t"ostype"\t\t"-184"']
    for key in keys:
        lines += [f'\t"{key}"', "\t{", '\t\t"root"\t\t"2"', '\t\t"size"\t\t"12"', "\t}"]
    lines.append("}")
    return "\n".join(lines) + "\n"


def make_deck(tmp_path: Path, layout: str = "steam") -> Deck:
    """A Deck-like tree under tmp_path/deck with one game (APPID) whose card comes from
    deckforge.detect: config.ini (I, ini), FakeGame_Data/boot.config (I, boot_config),
    user.reg (P, registry), GameUserSettings.ini and Engine.ini (P, ini)."""
    base = tmp_path.resolve() / "deck"
    base.mkdir(parents=True)
    library, steam_root = _library_for(base, layout)
    install = library / "steamapps" / "common" / "Fake Game"
    prefix = library / "steamapps" / "compatdata" / str(APPID) / "pfx"
    config_dir = prefix / "drive_c" / "users" / "steamuser" / "AppData" / "Local" / "FakeGame"
    files = {
        "pak": put(install / "re_chunk_000.pak", b"\0" * 64),
        "config": put(install / "config.ini", CONFIG_INI),
        "exe": put(install / "FakeGame.exe", b"MZ\x90\x00game"),
        "unity": put(install / "UnityPlayer.dll", b"MZ"),
        "boot": put(install / "FakeGame_Data" / "boot.config", BOOT_CONFIG),
        "shipping": put(
            install / "Binaries" / "Win64" / "FakeGame-Win64-Shipping.exe", b"MZ\x90\x00"
        ),
        "userreg": put(prefix / "user.reg", USER_REG),
        "sysreg": put(prefix / "system.reg", b"WINE REGISTRY Version 2\n"),
        "gus": put(config_dir / "Saved" / "Config" / "Windows" / "GameUserSettings.ini", GUS_INI),
        "engine": put(config_dir / "Saved" / "Config" / "Windows" / "Engine.ini", ENGINE_INI),
        "save": put(config_dir / "Saved" / "SaveGames" / "slot1.sav", SAVE),
        "configvdf": put(steam_root / "config" / "config.vdf", '"InstallConfigStore"\n{\n}\n'),
        "localconfig": put(
            steam_root / "userdata" / ACCOUNT / "config" / "localconfig.vdf",
            '"UserLocalConfigStore"\n{\n}\n',
        ),
    }
    userdata = steam_root / "userdata"
    files["remotecache"] = put(
        userdata / ACCOUNT / str(APPID) / "remotecache.vdf",
        remotecache(APPID, ["Saved/SaveGames/slot1.sav"]),
    )
    # Another game's cloud list names our files: it must not count for APPID.
    put(
        userdata / ACCOUNT / str(OTHER_APPID) / "remotecache.vdf",
        remotecache(OTHER_APPID, ["config.ini", "Saved/Config/Windows/GameUserSettings.ini"]),
    )
    (userdata / SECOND_ACCOUNT).mkdir(parents=True)
    for path in files.values():
        path.chmod(0o644)

    fields, _notes = detect.card_fields(
        APPID, kind="game", state_flags=4, install_path=str(install), prefix_path=str(prefix)
    )
    card = {
        "appid": APPID,
        "name": "Fake Game",
        "kind": "game",
        "library": str(library),
        "install_path": str(install),
        "prefix_path": str(prefix),
        **fields,
    }
    listed = {(entry["path"], entry["class"], entry["kind"]) for entry in card["settings_files"]}
    expected = {
        (str(files["config"]), "I", "ini"),
        (str(files["boot"]), "I", "boot_config"),
        (str(files["userreg"]), "P", "registry"),
        (str(files["gus"]), "P", "ini"),
        (str(files["engine"]), "P", "ini"),
    }
    assert listed == expected, f"fixture card changed: {listed}"
    assert card["anticheat"] == [] and card["tier_i_eligible"] is True

    home = base / "home"
    backup_root = home / "deckforge" / "backups"
    backup_root.mkdir(parents=True)
    proc = base / "proc"
    build_proc(proc)
    return Deck(
        base=base,
        library=library,
        steam_root=steam_root,
        install=install,
        prefix=prefix,
        home=home,
        backup_root=backup_root,
        proc=proc,
        userdata=userdata,
        card=card,
        files=files,
    )


def with_anticheat(card: dict[str, Any]) -> dict[str, Any]:
    """The same card with Easy Anti-Cheat found (detect then reports tier_i_eligible False)."""
    return {
        **card,
        "anticheat": [{"system": "easyanticheat", "evidence": ["EasyAntiCheat/x.dll"]}],
        "tier_i_eligible": False,
    }


def with_entry(card: dict[str, Any], path: str | Path, kind: str = "ini") -> dict[str, Any]:
    """The card with one more settings_files entry (a forged card)."""
    entry = {"path": str(path), "class": "I", "kind": kind}
    return {**card, "settings_files": [*card["settings_files"], entry]}


# ---------------------------------------------------------------------------- proc_root


def environ(**values: str) -> bytes:
    return b"".join(f"{key}={value}".encode() + b"\0" for key, value in values.items())


def add_process(
    proc: Path, pid: int, env: bytes | None = None, exe: str | Path | None = None
) -> Path:
    folder = proc / str(pid)
    folder.mkdir(parents=True, exist_ok=True)
    if env is not None:
        (folder / "environ").write_bytes(env)
    if exe is not None:
        (folder / "exe").symlink_to(exe)
    return folder


def build_proc(proc: Path) -> None:
    """Processes that must NOT count as the game: no Steam ids, SteamAppId=0, an appid that
    merely starts with APPID's digits, another game, a kernel thread (empty environ)."""
    proc.mkdir(parents=True)
    add_process(proc, 1, environ(PATH="/usr/bin", HOME="/home/deck"), exe="/usr/lib/systemd")
    add_process(proc, 2, environ(SteamAppId="0", SteamGameId="0"))
    add_process(proc, 3, environ(SteamAppId=f"{APPID}1", STEAM_COMPAT_APP_ID=f"{APPID}1"))
    add_process(proc, 4, environ(SteamAppId=str(OTHER_APPID), STEAM_COMPAT_APP_ID="1061090"))
    add_process(proc, 5, b"")
    add_process(proc, 6, environ(XSteamAppId=str(APPID), LAST="x"))
    (proc / "self").symlink_to("1")
    (proc / "sys" / "kernel").mkdir(parents=True)
    (proc / "version").write_text("Linux version 6.1.52-valve16-1-neptune\n")


def _matches(path: Any, chosen: set[str]) -> bool:
    if isinstance(path, int):
        path = fd_path(path)
        if not path:
            return False
    if not isinstance(path, str | bytes | os.PathLike):
        return False
    return abs_path(path) in chosen


def make_unreadable(monkeypatch: pytest.MonkeyPatch, *paths: Path) -> None:
    """Opening any of `paths` for reading raises PermissionError(EACCES)."""
    chosen = {abs_path(path) for path in paths}
    for path in paths:
        if path.is_file():
            path.chmod(0)

    def denied(path: Any) -> PermissionError:
        return PermissionError(errno.EACCES, "Permission denied", os.fsdecode(path))

    def fake_os_open(path, flags, *args, **kwargs):
        if _matches(path, chosen):
            raise denied(path)
        return REAL["os_open"](path, flags, *args, **kwargs)

    def fake_open(file, *args, **kwargs):
        if not isinstance(file, int) and _matches(file, chosen):
            raise denied(file)
        return REAL["io_open"](file, *args, **kwargs)

    monkeypatch.setattr(os, "open", fake_os_open)
    monkeypatch.setattr(io, "open", fake_open)
    monkeypatch.setattr(builtins, "open", fake_open)


class _OwnedBy:
    """A stat result whose st_uid (and st_gid) are replaced."""

    def __init__(self, real: os.stat_result, uid: int) -> None:
        self._real = real
        self.st_uid = uid
        self.st_gid = uid

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real, name)

    def __getitem__(self, index: int) -> Any:
        if index == stat.ST_UID or index == stat.ST_GID:
            return self.st_uid
        return self._real[index]


def make_foreign(monkeypatch: pytest.MonkeyPatch, *paths: Path) -> int:
    """`paths` look owned by another user; returns that uid."""
    uid = os.getuid() + FOREIGN_UID_OFFSET
    chosen = {abs_path(path) for path in paths}
    if os.geteuid() == 0:
        for path in paths:
            os.chown(path, uid, uid, follow_symlinks=False)

    def wrap(real: Callable[..., os.stat_result]) -> Callable[..., Any]:
        def fake(path, *args, **kwargs):
            result = real(path, *args, **kwargs)
            return _OwnedBy(result, uid) if _matches(path, chosen) else result

        return fake

    monkeypatch.setattr(os, "stat", wrap(REAL["stat"]))
    monkeypatch.setattr(os, "lstat", wrap(REAL["lstat"]))
    monkeypatch.setattr(os, "fstat", wrap(REAL["fstat"]))

    def fake_scandir(path=".", *args, **kwargs):
        return _Scandir(REAL["scandir"](path, *args, **kwargs), chosen, uid)

    monkeypatch.setattr(os, "scandir", fake_scandir)
    return uid


class _Entry:
    """An os.DirEntry whose stat() reports another owner for the chosen paths."""

    def __init__(self, inner: os.DirEntry, chosen: set[str], uid: int) -> None:
        self._inner = inner
        self._chosen = chosen
        self._uid = uid
        self.name = inner.name
        self.path = inner.path

    def stat(self, *, follow_symlinks: bool = True) -> Any:
        result = self._inner.stat(follow_symlinks=follow_symlinks)
        return _OwnedBy(result, self._uid) if abs_path(self.path) in self._chosen else result

    def __fspath__(self) -> str:
        return os.fspath(self._inner)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class _Scandir:
    """The iterator os.scandir returns, yielding _Entry objects."""

    def __init__(self, inner: Any, chosen: set[str], uid: int) -> None:
        self._inner = inner
        self._chosen = chosen
        self._uid = uid

    def __iter__(self) -> _Scandir:
        return self

    def __next__(self) -> _Entry:
        return _Entry(next(self._inner), self._chosen, self._uid)

    def __enter__(self) -> _Scandir:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._inner.close()

    def close(self) -> None:
        self._inner.close()


def lock_folder(monkeypatch: pytest.MonkeyPatch, folder: Path) -> None:
    """`folder` cannot be written to: mode 0o555, and (for root, who ignores modes)
    os.access(W_OK) is False and creating an entry inside raises PermissionError."""
    folder.chmod(0o555)
    real = abs_path(folder)

    def inside(path: Any) -> bool:
        if isinstance(path, int):
            return False
        return str(Path(abs_path(path)).parent) == real

    def denied(path: Any) -> PermissionError:
        return PermissionError(errno.EACCES, "Permission denied", os.fsdecode(path))

    def fake_access(path, mode, *args, **kwargs):
        if not isinstance(path, int) and abs_path(path) == real and mode & os.W_OK:
            return False
        return REAL["access"](path, mode, *args, **kwargs)

    def fake_os_open(path, flags, *args, **kwargs):
        if flags & os.O_CREAT and inside(path):
            raise denied(path)
        return REAL["os_open"](path, flags, *args, **kwargs)

    def fake_open(file, mode="r", *args, **kwargs):
        if any(flag in mode for flag in "wax+") and inside(file):
            raise denied(file)
        return REAL["io_open"](file, mode, *args, **kwargs)

    def fake_mkdir(path, *args, **kwargs):
        if inside(path):
            raise denied(path)
        return REAL["mkdir"](path, *args, **kwargs)

    monkeypatch.setattr(os, "access", fake_access)
    monkeypatch.setattr(os, "open", fake_os_open)
    monkeypatch.setattr(io, "open", fake_open)
    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(os, "mkdir", fake_mkdir)


def full_disk(monkeypatch: pytest.MonkeyPatch, *folders: Path) -> list[str]:
    """os.statvfs reports no free space for any path inside `folders`; returns the paths
    it was asked about."""
    roots = [os.path.realpath(folder) for folder in folders]
    asked: list[str] = []

    def fake(path):
        real = os.path.realpath(os.fsdecode(path)) if not isinstance(path, int) else ""
        asked.append(real)
        result = REAL["statvfs"](path)
        if any(real == root or real.startswith(root + os.sep) for root in roots):
            return os.statvfs_result(
                (4096, 4096, result.f_blocks, 0, 0, result.f_files, 0, 0, result.f_flag, 255)
            )
        return result

    monkeypatch.setattr(os, "statvfs", fake)
    return asked


def low_disk(monkeypatch: pytest.MonkeyPatch, free: dict[Path, int]) -> None:
    """os.statvfs reports exactly free[folder] bytes available (1-byte blocks, so f_bavail
    * f_frsize == free[folder]) for any path inside that folder; other paths are real."""
    roots = {os.path.realpath(folder): amount for folder, amount in free.items()}

    def fake(path):
        result = REAL["statvfs"](path)
        if isinstance(path, int):
            return result
        real = os.path.realpath(os.fsdecode(path))
        for root, amount in roots.items():
            if real == root or real.startswith(root + os.sep):
                return os.statvfs_result(
                    (
                        1,
                        1,
                        max(amount, 1) * 4,
                        amount,
                        amount,
                        result.f_files,
                        100,
                        100,
                        result.f_flag,
                        255,
                    )
                )
        return result

    monkeypatch.setattr(os, "statvfs", fake)


def record_deletions(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    """Every os.unlink / os.remove / os.rmdir / os.removedirs / shutil.rmtree call, as
    (function, absolute path). The calls still happen."""
    seen: list[tuple[str, str]] = []

    def wrap(name: str, real: Callable[..., Any]) -> Callable[..., Any]:
        def fake(path, *args, **kwargs):
            shown = fd_path(path) if isinstance(path, int) else abs_path(path)
            seen.append((name, shown))
            return real(path, *args, **kwargs)

        return fake

    monkeypatch.setattr(os, "unlink", wrap("unlink", REAL["unlink"]))
    monkeypatch.setattr(os, "remove", wrap("remove", REAL["remove"]))
    monkeypatch.setattr(os, "rmdir", wrap("rmdir", REAL["rmdir"]))
    monkeypatch.setattr(os, "removedirs", wrap("removedirs", os.removedirs))
    monkeypatch.setattr(shutil, "rmtree", wrap("rmtree", shutil.rmtree))
    return seen


def simulate_exit(top: Path) -> None:
    """After a Crash: what the kernel does when the process dies. Unreachable file objects
    are collected (closing them), then every fd still open on a path under `top` (a raw
    os.open fd, such as the held .lock) is closed, which frees its flock."""
    gc.collect()
    root = abs_path(top)
    fds = [int(child.name) for child in Path("/proc/self/fd").iterdir()]
    for fd in fds:
        path = fd_path(fd)
        if path == root or path.startswith(root + os.sep):
            try:
                os.close(fd)
            except OSError as error:
                if error.errno != errno.EBADF:
                    raise


# ---------------------------------------------------------------------------- the lock

_HOLDER = (
    "import fcntl, sys\n"
    "handle = open(sys.argv[1], 'a')\n"
    "fcntl.flock(handle, fcntl.LOCK_EX)\n"
    "print('held', flush=True)\n"
    "sys.stdin.read()\n"
)


def hold_lock(lock_path: Path) -> subprocess.Popen:
    """A second process holding flock(LOCK_EX) on lock_path until release()."""
    holder = subprocess.Popen(
        [sys.executable, "-c", _HOLDER, str(lock_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "held"
    return holder


def release(holder: subprocess.Popen) -> None:
    assert holder.stdin is not None
    holder.stdin.close()
    assert holder.wait(timeout=30) == 0
    if holder.stdout is not None:
        holder.stdout.close()


# ---------------------------------------------------------------------------- recorder


def fd_path(fd: int) -> str:
    try:
        return str(Path(f"/proc/self/fd/{fd}").readlink())
    except OSError:
        return ""


class _Tracked:
    """A file object opened for writing whose write() calls count as steps."""

    def __init__(self, inner: Any, path: str, recorder: Recorder) -> None:
        self._inner = inner
        self._path = path
        self._recorder = recorder

    def write(self, data: Any) -> Any:
        self._recorder.step("write", self._path)
        return self._inner.write(data)

    def writelines(self, lines: Iterable[Any]) -> None:
        self._recorder.step("write", self._path)
        self._inner.writelines(lines)

    def close(self) -> None:
        self._inner.close()
        self._recorder.closed(self._path)

    def __enter__(self) -> _Tracked:
        self._inner.__enter__()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def __iter__(self):
        return iter(self._inner)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)


class Recorder:
    """Records write-side steps that touch `root`; raises at step `fail_at`.

    `make_error(op, path)` builds the exception (default: OSError ENOSPC for writes, EIO
    otherwise). `persistent` keeps failing every later step whose path passes `keep_failing`
    (used to make a rollback fail too). `hook(recorder, op, path, path2)` runs before each
    recorded step and may act (edit a file, add a process)."""

    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        root: Path,
        *,
        fail_at: int | None = None,
        make_error: Callable[[str, str], BaseException] | None = None,
        keep_failing: Callable[[str, str, str | None], bool] | None = None,
        hook: Callable[[Recorder, str, str, str | None], None] | None = None,
    ) -> None:
        self.root = abs_path(root)
        self.steps: list[tuple[str, str, str | None]] = []
        self.fail_at = fail_at
        self.make_error = make_error or default_error
        self.keep_failing = keep_failing
        self.failed = False
        self.hook = hook
        self.on_close: Callable[[str], None] | None = None
        self._install(monkeypatch)

    def inside(self, path: str | None) -> bool:
        if not path:
            return False
        path = abs_path(path)
        return path == self.root or path.startswith(self.root + os.sep)

    def step(self, op: str, path: str, path2: str | None = None) -> None:
        if not (self.inside(path) or self.inside(path2)):
            return
        if self.hook is not None:
            self.hook(self, op, path, path2)
        index = len(self.steps)
        self.steps.append((op, path, path2))
        if self.failed and self.keep_failing is not None and self.keep_failing(op, path, path2):
            raise self.make_error(op, path)
        if index == self.fail_at:
            self.failed = True
            raise self.make_error(op, path)

    def closed(self, path: str) -> None:
        if self.on_close is not None and self.inside(path):
            self.on_close(path)

    def _install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        rec = self

        def replace(src, dst, *args, **kwargs):
            rec.step("replace", _text(src), _text(dst))
            return REAL["replace"](src, dst, *args, **kwargs)

        def rename(src, dst, *args, **kwargs):
            rec.step("rename", _text(src), _text(dst))
            return REAL["rename"](src, dst, *args, **kwargs)

        def fsync(fd):
            rec.step("fsync", fd_path(fd if isinstance(fd, int) else fd.fileno()))
            return REAL["fsync"](fd)

        def write(fd, data):
            rec.step("write", fd_path(fd))
            return REAL["write"](fd, data)

        def sendfile(out_fd, in_fd, *args, **kwargs):
            rec.step("write", fd_path(out_fd))
            return REAL["sendfile"](out_fd, in_fd, *args, **kwargs)

        def copy_file_range(src, dst, *args, **kwargs):
            rec.step("write", fd_path(dst))
            return REAL["copy_file_range"](src, dst, *args, **kwargs)

        def mkdir(path, *args, **kwargs):
            rec.step("mkdir", _text(path))
            return REAL["mkdir"](path, *args, **kwargs)

        def chmod(path, mode, *args, **kwargs):
            shown = fd_path(path) if isinstance(path, int) else _text(path)
            rec.step("chmod", shown)
            return REAL["chmod"](path, mode, *args, **kwargs)

        def fchmod(fd, mode):
            rec.step("chmod", fd_path(fd))
            return REAL["fchmod"](fd, mode)

        def opener(real: Callable[..., Any]) -> Callable[..., Any]:
            def fake(file, mode="r", *args, **kwargs):
                handle = real(file, mode, *args, **kwargs)
                if not any(flag in mode for flag in "wax+"):
                    return handle
                shown = fd_path(file) if isinstance(file, int) else _text(file)
                return _Tracked(handle, shown, rec) if rec.inside(shown) else handle

            return fake

        monkeypatch.setattr(os, "replace", replace)
        monkeypatch.setattr(os, "rename", rename)
        monkeypatch.setattr(os, "fsync", fsync)
        monkeypatch.setattr(os, "write", write)
        monkeypatch.setattr(os, "sendfile", sendfile)
        if REAL["copy_file_range"] is not None:
            monkeypatch.setattr(os, "copy_file_range", copy_file_range)
        monkeypatch.setattr(os, "mkdir", mkdir)
        monkeypatch.setattr(os, "chmod", chmod)
        monkeypatch.setattr(os, "fchmod", fchmod)
        monkeypatch.setattr(io, "open", opener(REAL["io_open"]))
        monkeypatch.setattr(builtins, "open", opener(REAL["builtins_open"]))


def _text(path: Any) -> str:
    return abs_path(path)


def abs_path(path: Any) -> str:
    """os.path.abspath without following links (spelled so the PTH lint rules pass)."""
    return os.path.normpath(Path(os.fsdecode(path)).absolute())


def default_error(op: str, path: str) -> OSError:
    code = errno.ENOSPC if op == "write" else errno.EIO
    return OSError(code, os.strerror(code), path)


def crash(op: str, path: str) -> Crash:
    return Crash(f"power cut at {op} {path}")


# ---------------------------------------------------------------------------- readers


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def mode_of(path: Path) -> int:
    return stat.S_IMODE(path.lstat().st_mode)


def content_state(top: Path, skip: Iterable[Path] = ()) -> dict[str, tuple]:
    """Names, types, permission bits, bytes and link targets under `top` (not mtimes or
    inodes, which an atomic replace changes). Paths in `skip` are left out with their
    contents."""
    skipped = {abs_path(path) for path in skip}
    state: dict[str, tuple] = {}
    pending = [top]
    while pending:
        path = pending.pop()
        if abs_path(path) in skipped:
            continue
        info = path.lstat()
        kind = stat.S_IFMT(info.st_mode)
        entry: tuple = (kind, stat.S_IMODE(info.st_mode))
        if stat.S_ISLNK(info.st_mode):
            entry += (str(path.readlink()),)
        elif stat.S_ISREG(info.st_mode):
            entry += (_read_any(path),)
        elif stat.S_ISDIR(info.st_mode):
            names = sorted(child.name for child in path.iterdir())
            entry += (tuple(names),)
            pending.extend(path / name for name in names)
        state[str(path.relative_to(top))] = entry
    return state


def _read_any(path: Path) -> bytes:
    with REAL["io_open"](path, "rb") as handle:
        return handle.read()


def deck_state(deck: Deck) -> dict[str, tuple]:
    """content_state of the whole Deck except the backup root."""
    return content_state(deck.base, skip=[deck.backup_root])


def all_paths(top: Path) -> set[str]:
    return set(content_state(top))


def backup_folders(deck: Deck) -> list[str]:
    return sorted(child.name for child in deck.backup_root.iterdir() if child.name != ".lock")


def read_manifest(deck: Deck, backup_id: str) -> dict[str, Any]:
    with REAL["io_open"](deck.backup_root / backup_id / "manifest.json", "rb") as handle:
        return json.loads(handle.read())


def manifest_files(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(manifest.get("files"), list):
        return manifest["files"]
    lists = [
        value
        for value in manifest.values()
        if isinstance(value, list)
        and value
        and all(isinstance(item, dict) and "path" in item for item in value)
    ]
    assert len(lists) == 1, f"no single per-file list in the manifest: {manifest}"
    return lists[0]


def write_manifest(deck: Deck, backup_id: str, manifest: dict[str, Any]) -> None:
    path = deck.backup_root / backup_id / "manifest.json"
    with REAL["io_open"](path, "wb") as handle:
        handle.write(json.dumps(manifest).encode("utf-8"))


def backup_copies(deck: Deck, backup_id: str) -> list[Path]:
    """Every regular file in the backup folder other than manifest.json."""
    folder = deck.backup_root / backup_id
    found = []
    for dirpath, _dirs, names in os.walk(folder):
        for name in names:
            path = Path(dirpath, name)
            if path != folder / "manifest.json" and stat.S_ISREG(path.lstat().st_mode):
                found.append(path)
    return sorted(found)


def copy_holding(deck: Deck, backup_id: str, data: bytes) -> Path:
    """The backup copy whose bytes are `data` (exactly one is expected)."""
    hits = [path for path in backup_copies(deck, backup_id) if _read_any(path) == data]
    assert hits, f"no backup copy holds {data[:40]!r}"
    return hits[0]


def is_incomplete(entry: dict[str, Any]) -> bool:
    return (
        any(value == "incomplete" for value in entry.values())
        or entry.get("incomplete") is True
        or entry.get("complete") is False
    )


def names_folder(entry: dict[str, Any], name: str) -> bool:
    if entry.get("backup_id") == name:
        return True
    return any(
        isinstance(value, str) and (value == name or value.endswith(os.sep + name))
        for value in entry.values()
    )


def entry_for(entries: list[dict[str, Any]], name: str) -> dict[str, Any]:
    hits = [entry for entry in entries if names_folder(entry, name)]
    assert len(hits) == 1, f"{name}: {entries}"
    return hits[0]


def complete_ids(entries: list[dict[str, Any]]) -> list[str]:
    return [entry["backup_id"] for entry in entries if not is_incomplete(entry)]


def warning_codes(warnings: list[Any]) -> list[str]:
    return [item["code"] if isinstance(item, dict) else item for item in warnings]


def error_text(exc: BaseException) -> str:
    """str(exc) plus every string (or list of strings) attribute it carries."""
    parts = [str(exc)]
    for value in vars(exc).values():
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list | tuple):
            parts.extend(str(item) for item in value)
        elif isinstance(value, dict):
            parts.extend(str(item) for item in value.values())
    return "\n".join(parts)


def target_folder_names(paths: Iterable[Path]) -> dict[str, list[str]]:
    return {
        str(path.parent): sorted(child.name for child in path.parent.iterdir()) for path in paths
    }


# ---------------------------------------------------------------------------- calls


def refusal(code: str, call: Callable[..., Any], *args: Any, **kwargs: Any) -> Exception:
    """Run `call`; it must raise SafetyError with this code. Returns the error."""
    from deckforge import safety

    with pytest.raises(safety.SafetyError) as info:
        call(*args, **kwargs)
    assert info.value.code == code, f"expected {code}, got {info.value.code}: {info.value}"
    return info.value


def plan_and_apply(
    deck: Deck,
    targets: Iterable[tuple[Path | str, bytes]],
    card: dict[str, Any] | None = None,
    **overrides: Any,
) -> str:
    from deckforge import safety

    changes = [safety.plan(card or deck.card, str(path), data) for path, data in targets]
    return safety.apply(changes, **deck.kw(**overrides))


def refused_at_plan_or_apply(
    code: str,
    deck: Deck,
    targets: Iterable[tuple[Path | str, bytes]],
    card: dict[str, Any] | None = None,
    **overrides: Any,
) -> Exception:
    """The refusal may come from plan or from apply (the spec does not say which)."""
    return refusal(code, plan_and_apply, deck, list(targets), card, **overrides)
