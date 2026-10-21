"""Read-only Deck snapshot: one zip to upload for remote analysis (docs/specs/snapshot.md).

`build_snapshot(steam_root, home, out_dir, *, now)` writes one new zip,
<out_dir>/deckforge-snapshot-<YYYYmmdd-HHMMSS>Z.zip, and returns its path. It holds:
  scan.json      deckforge.discover.scan(steam_root), B8 text (S1)
  settings/      settings files of installed cards, settings/<appid>/<n>_<basename> (S2)
  sizes.json     shader cache and compatdata sizes per card, and orphan folders (S3)
  plugins.json   Decky plugins: folder, name, version (S4)
  logs/          the 5 newest frame-time logs, *.csv in <home>/deckforge/logs (S5)
  system.json    os-release keys, kernel, board name, disk usage (S6)
  manifest.json  copied files, skips with a reason, issues, version and time (S7)

Nothing outside out_dir is written (S9). Copied files are checked with lstat and opened
with O_NOFOLLOW, so a link's target is never read; folder sizes are summed with os.scandir
and lstat, never following links. Registry files (kind "reg" or "registry") are never
opened. out_dir is refused (SnapshotError) inside steam_root, a library or <home>/homebrew,
before anything is created; an existing target is never overwritten (S8). The zip is
written to <target>.partial and moved into place; on any error the partial is removed and
the error re-raised.

CLI: python -m deckforge.snapshot --steam-root PATH [--home PATH] [--out-dir PATH]
(prints the zip path and counts; exit 2 on SnapshotError)
"""

import argparse
import json
import logging
import os
import shutil
import stat
import sys
import zipfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from deckforge import discover
from deckforge.detect import _lookup
from deckforge.discover import _as_int, _issue, _why

SNAPSHOT_VERSION = 1
OS_RELEASE_PATH = "/etc/os-release"
BOARD_NAME_PATH = "/sys/devices/virtual/dmi/id/board_name"

_MIB = 1024 * 1024
_SETTINGS_CAP = _MIB
_PLUGIN_CAP = _MIB
_LOG_CAP = 20 * _MIB
_SYSTEM_CAP = 64 * 1024
_LOG_COUNT = 5
_EXCLUDED_KINDS = ("reg", "registry")
_OS_RELEASE_KEYS = ("NAME", "PRETTY_NAME", "VERSION_ID", "BUILD_ID", "VARIANT_ID")
_CACHE_FOLDERS = ("shadercache", "compatdata")
_READ_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC

_log = logging.getLogger("deckforge.snapshot")  # not __name__, which is __main__ under -m
_Issue = dict[str, Any]


class SnapshotError(Exception):
    """The snapshot cannot be made: the scan failed, or out_dir or the target is refused."""


class _Skip(Exception):
    """A file that is not copied. `reason` is a manifest skip reason (S2, S5)."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass
class _Result:
    path: str
    settings_copied: int = 0
    logs_copied: int = 0
    orphans: int = 0


@dataclass
class _Manifest:
    files: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)
    issues: list[_Issue] = field(default_factory=list)

    def skip(self, source: str, error: _Skip) -> None:
        self.skipped.append({"source": source, "reason": error.reason, "message": str(error)})


# ---------------------------------------------------------------------------- public


def build_snapshot(
    steam_root: str | os.PathLike[str],
    home: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    *,
    now: datetime,
) -> str:
    """Write the snapshot zip and return its path (S1-S9). Reads only, except out_dir."""
    return _build(steam_root, home, out_dir, now).path


def main(argv: list[str] | None = None) -> int:
    """CLI (S10): print the zip path and counts and return 0; return 2 on SnapshotError."""
    parser = argparse.ArgumentParser(
        prog="deckforge.snapshot",
        description="Write one read-only snapshot zip of this Deck for remote analysis.",
        allow_abbrev=False,
    )
    parser.add_argument("--steam-root", required=True, help="the Steam folder to scan")
    parser.add_argument("--home", help="the home folder (default: ~)")
    parser.add_argument("--out-dir", help="the zip's folder (default: <home>/deckforge/snapshots)")
    args = parser.parse_args(argv)
    home = args.home if args.home is not None else str(Path("~").expanduser())
    out_dir = args.out_dir
    if out_dir is None:
        out_dir = str(Path(home, "deckforge", "snapshots"))
    try:
        result = _build(args.steam_root, home, out_dir, datetime.now(UTC))
    except SnapshotError as exc:
        sys.stderr.write(f"deckforge.snapshot: {exc}\n")
        return 2
    sys.stdout.write(
        f"{result.path}\n"
        f"settings files copied: {result.settings_copied}\n"
        f"logs copied: {result.logs_copied}\n"
        f"orphans found: {result.orphans}\n"
    )
    return 0


# ---------------------------------------------------------------------------- build


def _build(
    steam_root: str | os.PathLike[str],
    home: str | os.PathLike[str],
    out_dir: str | os.PathLike[str],
    now: datetime,
) -> _Result:
    when = now.astimezone(UTC)
    home_text = os.fspath(home)
    try:
        scan = discover.scan(steam_root)
    except discover.DiscoverError as exc:
        raise SnapshotError(f"cannot scan Steam: {exc}") from exc
    _refuse_out_dir(steam_root, home_text, out_dir, scan)
    target = Path(out_dir, f"deckforge-snapshot-{when:%Y%m%d-%H%M%S}Z.zip")
    if _lookup(str(target), follow_symlinks=False) is not None:
        raise SnapshotError(f"{str(target)!r} already exists; it is never overwritten")

    manifest = _Manifest()
    sizes = _sizes(scan)
    plugins = _plugins(Path(home_text, "homebrew", "plugins"), manifest.issues)
    logs = _newest_logs(Path(home_text, "deckforge", "logs"), manifest.issues)
    system = _system(home_text, scan)

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    partial = Path(f"{target}.partial")
    try:
        handle = partial.open("xb")
    except FileExistsError as exc:
        raise SnapshotError(f"{str(partial)!r} already exists; remove it and retry") from exc
    result = _Result(str(target), orphans=len(sizes["orphans"]))
    done = False
    try:
        with handle, zipfile.ZipFile(handle, "w", zipfile.ZIP_DEFLATED) as archive:
            stamp = when.timetuple()[:6]
            _add(archive, stamp, "scan.json", _json_text(scan))
            _add(archive, stamp, "sizes.json", _json_text(sizes))
            _add(archive, stamp, "plugins.json", _json_text(plugins))
            _add(archive, stamp, "system.json", _json_text(system))
            result.settings_copied = _copy_settings(archive, stamp, scan, manifest)
            result.logs_copied = _copy_logs(archive, stamp, logs, manifest)
            document = {
                "snapshot_version": SNAPSHOT_VERSION,
                "created_utc": when.isoformat(),
                "files": manifest.files,
                "skipped": manifest.skipped,
                "issues": manifest.issues,
            }
            _add(archive, stamp, "manifest.json", _json_text(document))
        partial.replace(target)
        done = True
    finally:
        if not done:
            _log.warning("snapshot not written; removing %s", partial)
            partial.unlink(missing_ok=True)
    return result


def _refuse_out_dir(
    steam_root: str | os.PathLike[str],
    home: str,
    out_dir: str | os.PathLike[str],
    scan: dict[str, Any],
) -> None:
    """S8: out_dir must not be steam_root, a library or <home>/homebrew, nor inside one,
    after realpath on both sides. Checked before anything is created."""
    real_out = os.path.realpath(out_dir)
    guarded = [os.fspath(steam_root), str(Path(home, "homebrew"))]
    guarded += [entry["path"] for entry in scan["libraries"] if Path(entry["path"]).is_absolute()]
    for folder in guarded:
        real = os.path.realpath(folder)
        if os.path.commonpath([real_out, real]) == real:
            raise SnapshotError(f"out_dir {os.fspath(out_dir)!r} is inside {folder!r}")


def _add(archive: zipfile.ZipFile, stamp: tuple[int, ...], name: str, data: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=stamp)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, data)


def _json_text(value: Any) -> bytes:
    """B8 serialization, final newline included."""
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")


# ---------------------------------------------------------------------------- S2 settings


def _copy_settings(
    archive: zipfile.ZipFile, stamp: tuple[int, ...], scan: dict[str, Any], manifest: _Manifest
) -> int:
    copied = 0
    for card in scan["games"]:
        if card["installed"] is not True:
            continue
        for n, entry in enumerate(card["settings_files"]):
            source = entry["path"]
            try:
                if entry["kind"] in _EXCLUDED_KINDS:
                    raise _Skip("excluded_kind", "registry files are never copied")
                data = _read_file(source, _SETTINGS_CAP)
            except _Skip as skip:
                manifest.skip(source, skip)
                continue
            name = f"settings/{card['appid']}/{n}_{Path(source).name}"
            _add(archive, stamp, name, data)
            manifest.files.append({"zip_name": name, "source": source, "size": len(data)})
            copied += 1
    return copied


def _read_file(path: str, cap: int) -> bytes:
    """The bytes of a regular file (not a link) of at most `cap` bytes; raises _Skip."""
    try:
        info = Path(path).lstat()
    except OSError as exc:
        raise _Skip("unreadable", f"cannot check: {_why(exc)}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise _Skip("not_regular", "not a regular file")
    if info.st_size > cap:
        raise _Skip("too_large", f"larger than {cap} bytes")
    try:
        fd = os.open(path, _READ_FLAGS)  # O_NOFOLLOW: replaced by a link since lstat fails
    except OSError as exc:
        raise _Skip("unreadable", f"cannot open: {_why(exc)}") from exc
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):  # replaced by a FIFO or folder since lstat
            raise _Skip("not_regular", "not a regular file")
        chunks: list[bytes] = []
        total = 0
        while total <= cap:
            chunk = os.read(fd, min(cap + 1 - total, _MIB))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
    except OSError as exc:
        raise _Skip("unreadable", f"cannot read: {_why(exc)}") from exc
    finally:
        os.close(fd)
    if total > cap:  # grew after the size check
        raise _Skip("too_large", f"larger than {cap} bytes")
    return b"".join(chunks)


# ---------------------------------------------------------------------------- S3 sizes


def _sizes(scan: dict[str, Any]) -> dict[str, Any]:
    issues: list[_Issue] = []
    games = []
    for card in scan["games"]:
        appid, library = card["appid"], card["library"]
        shadercache = card["shadercache_path"]
        compatdata = str(Path(library, "steamapps", "compatdata", str(appid)))
        games.append(
            {
                "appid": appid,
                "library": library,
                "shadercache": None if shadercache is None else _size(shadercache, issues),
                "compatdata": _size(compatdata, issues),
            }
        )
    known = {card["appid"] for card in scan["games"]}
    orphans = []
    for library in scan["libraries"]:
        if not library["available"]:
            continue
        for kind in _CACHE_FOLDERS:
            folder = str(Path(library["path"], "steamapps", kind))
            for path in _orphan_paths(folder, known, issues):
                orphans.append({"path": path, "size": _size(path, issues)})
    return {"games": games, "orphans": orphans, "issues": issues}


def _orphan_paths(folder: str, known: set[int], issues: list[_Issue]) -> list[str]:
    """All-digit entries of `folder` whose appid has no card, sorted by name."""
    try:
        with os.scandir(folder) as listing:
            names = sorted(entry.name for entry in listing)
    except (FileNotFoundError, NotADirectoryError):
        return []
    except OSError as exc:
        _log.warning("cannot list %s: %s", folder, _why(exc))
        issues.append(_issue("size_unreadable", folder, f"cannot list: {_why(exc)}"))
        return []
    found = []
    for name in names:
        appid = _as_int(name)
        if appid is not None and appid not in known:
            found.append(str(Path(folder, name)))
    return found


def _size(top: str, issues: list[_Issue]) -> int | None:
    """Total size of the regular files under `top` (lstat, links never followed); None if
    absent. A folder that cannot be listed adds a size_unreadable issue with its path."""
    try:
        info = _lookup(top, follow_symlinks=False)
    except OSError as exc:
        _log.warning("cannot check %s: %s", top, _why(exc))
        issues.append(_issue("size_unreadable", top, f"cannot check: {_why(exc)}"))
        return None
    if info is None:
        return None
    if not stat.S_ISDIR(info.st_mode):
        return info.st_size if stat.S_ISREG(info.st_mode) else 0
    total = 0
    pending = [top]
    while pending:
        folder = pending.pop()
        try:
            with os.scandir(folder) as listing:
                for entry in listing:
                    entry_info = entry.stat(follow_symlinks=False)
                    if stat.S_ISDIR(entry_info.st_mode):
                        pending.append(entry.path)
                    elif stat.S_ISREG(entry_info.st_mode):
                        total += entry_info.st_size
        except OSError as exc:
            _log.warning("cannot size %s: %s", folder, _why(exc))
            issues.append(_issue("size_unreadable", folder, f"cannot list: {_why(exc)}"))
    return total


# ---------------------------------------------------------------------------- S4 plugins


def _plugins(plugins_dir: Path, issues: list[_Issue]) -> list[dict[str, Any]]:
    try:
        with os.scandir(plugins_dir) as listing:
            folders = sorted(entry.name for entry in listing if entry.is_dir(follow_symlinks=False))
    except (FileNotFoundError, NotADirectoryError):
        issues.append(_issue("decky_not_found", str(plugins_dir), "no Decky plugins folder"))
        return []
    except OSError as exc:
        _log.warning("cannot list %s: %s", plugins_dir, _why(exc))
        issues.append(_issue("decky_unreadable", str(plugins_dir), f"cannot list: {_why(exc)}"))
        return []
    return [
        {
            "folder": folder,
            "name": _plugin_field(plugins_dir / folder / "plugin.json", "name", issues),
            "version": _plugin_field(plugins_dir / folder / "package.json", "version", issues),
        }
        for folder in folders
    ]


def _plugin_field(path: Path, key: str, issues: list[_Issue]) -> str | None:
    """The string `key` of a UTF-8 JSON object file; None plus an issue otherwise."""
    try:
        data = _read_file(str(path), _PLUGIN_CAP)
    except _Skip as skip:
        issues.append(_issue(f"plugin_file_{skip.reason}", str(path), str(skip)))
        return None
    try:
        document = json.loads(data.decode("utf-8"))
    except UnicodeDecodeError:
        issues.append(_issue("plugin_file_invalid", str(path), "not UTF-8 text"))
        return None
    except json.JSONDecodeError as exc:
        issues.append(_issue("plugin_file_invalid", str(path), f"not JSON (line {exc.lineno})"))
        return None
    value = document.get(key) if isinstance(document, dict) else None
    if not isinstance(value, str):
        issues.append(_issue("plugin_key_missing", str(path), f"no string {key!r} key"))
        return None
    return value


# ---------------------------------------------------------------------------- S5 logs


def _newest_logs(logs_dir: Path, issues: list[_Issue]) -> list[str]:
    """Paths of the 5 newest regular *.csv files (lstat), newest first."""
    try:
        with os.scandir(logs_dir) as listing:
            found = []
            for entry in listing:
                if not entry.name.endswith(".csv"):
                    continue
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISREG(info.st_mode):
                    found.append((-info.st_mtime_ns, entry.name, entry.path))
    except (FileNotFoundError, NotADirectoryError):
        issues.append(_issue("logs_not_found", str(logs_dir), "no frame-time logs folder"))
        return []
    except OSError as exc:
        _log.warning("cannot list %s: %s", logs_dir, _why(exc))
        issues.append(_issue("logs_unreadable", str(logs_dir), f"cannot list: {_why(exc)}"))
        return []
    return [path for _, _, path in sorted(found)[:_LOG_COUNT]]


def _copy_logs(
    archive: zipfile.ZipFile, stamp: tuple[int, ...], logs: list[str], manifest: _Manifest
) -> int:
    copied = 0
    for source in logs:
        try:
            data = _read_file(source, _LOG_CAP)
        except _Skip as skip:
            manifest.skip(source, skip)
            continue
        name = f"logs/{Path(source).name}"
        _add(archive, stamp, name, data)
        manifest.files.append({"zip_name": name, "source": source, "size": len(data)})
        copied += 1
    return copied


# ---------------------------------------------------------------------------- S6 system


def _system(home: str, scan: dict[str, Any]) -> dict[str, Any]:
    issues: list[_Issue] = []
    os_release = _read_text(OS_RELEASE_PATH, issues)
    board = _read_text(BOARD_NAME_PATH, issues)
    paths = [home] + [entry["path"] for entry in scan["libraries"] if entry["available"]]
    disk = []
    for path in paths:
        try:
            usage = shutil.disk_usage(path)
        except OSError as exc:
            _log.warning("cannot read disk usage of %s: %s", path, _why(exc))
            issues.append(_issue("disk_unreadable", path, f"cannot read: {_why(exc)}"))
            continue
        disk.append({"path": path, "total": usage.total, "used": usage.used, "free": usage.free})
    return {
        "os_release": {} if os_release is None else _os_release(os_release),
        "kernel": os.uname().release,
        "board": None if board is None else board.rstrip("\n"),
        "disk": disk,
        "issues": issues,
    }


def _read_text(path: str, issues: list[_Issue]) -> str | None:
    """A small UTF-8 system file; links are followed (/etc/os-release usually is one). None
    plus an issue if it is not a regular file or cannot be read."""
    try:
        if not stat.S_ISREG(Path(path).stat().st_mode):
            issues.append(_issue("system_file_unreadable", path, "not a regular file"))
            return None
        with Path(path).open("rb") as handle:
            data = handle.read(_SYSTEM_CAP)
    except OSError as exc:
        issues.append(_issue("system_file_unreadable", path, f"cannot read: {_why(exc)}"))
        return None
    return data.decode("utf-8", errors="replace")


def _os_release(text: str) -> dict[str, str]:
    """The kept KEY=value pairs, one level of matching quotes removed."""
    kept = {}
    for line in text.splitlines():
        key, sep, value = line.strip().partition("=")
        if not sep or key not in _OS_RELEASE_KEYS:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        kept[key] = value
    return kept


if __name__ == "__main__":
    raise SystemExit(main())
