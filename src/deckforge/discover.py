"""Read-only scan of a Steam install: libraries, app manifests and Proton versions.

Implements PR B1 of docs/specs/discover.md (criteria B1-B9). `scan(steam_root)` returns the
libraries, one card per app manifest, and the compat tool Steam maps to each game.

It writes nothing. Only three kinds of file are opened, each in mode "rb" and only after
`stat` shows a regular file, so a FIFO is never opened and cannot hang a scan:
<root>/steamapps/libraryfolders.vdf (up to 1 MiB), <library>/steamapps/appmanifest_<x>.acf
(up to 1 MiB) and <root>/config/config.vdf (up to 16 MiB). Folders are listed with
os.scandir. Paths are joined with pathlib; for the normalized library strings used here
the result is the same string os.path.join gives.

A libraryfolders.vdf that cannot be used raises DiscoverError. Other problems become an
issue {"code", "path", "message"}; messages never quote file contents.
  errors         library_unreadable, manifest_unreadable, manifest_malformed,
                 manifest_incomplete, manifest_appid_mismatch, manifest_unsafe_installdir,
                 config_vdf_malformed
  warnings       library_entry_invalid, library_path_invalid, library_unavailable,
                 common_unreadable, config_vdf_missing, duplicate_appid
  card warnings  name_missing, stateflags_invalid, install_folder_missing,
                 prefix_in_other_library, prefix_unreadable, and from deckforge.detect
                 (B2: engine, anti-cheat, upscalers, injectors, settings files, Tier I)
                 scan_truncated, unreadable, not_entered, non_utf8_filename,
                 injector_with_anticheat
A folder that is not found, or has a path part that is not a folder, is absent. Any other
error while checking a folder is never silent (spec B4, R12): for steamapps, common and
either prefix (the game's own, or the root library's fallback) it is an issue; for an
install folder or shader cache it is logged at WARNING on logger "deckforge.discover",
with the path.

CLI: python -m deckforge.discover --steam-root PATH  (JSON on stdout; exit 2 on DiscoverError)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deckforge import detect, vdf

DISCOVER_VERSION = 1
_MIB = 1024 * 1024
_SMALL_CAP = _MIB  # libraryfolders.vdf and appmanifest_*.acf
_CONFIG_CAP = 16 * _MIB  # config/config.vdf
_DIGITS = re.compile(r"[0-9]+")
_MANIFEST_NAME = re.compile(r"appmanifest_(.+)\.acf", re.DOTALL)
_TOOL_PREFIXES = ("Proton ", "Steam Linux Runtime", "Steamworks Common Redistributables")
_COMPAT_TOOL_MAPPING = ("InstallConfigStore", "Software", "Valve", "Steam", "CompatToolMapping")
_FULLY_INSTALLED = 4  # StateFlags bit
_UNSAFE_INSTALLDIRS = ("", ".", "..")

_log = logging.getLogger("deckforge.discover")  # not __name__, which is __main__ under -m
_Issue = dict[str, Any]
_Library = tuple[dict[str, Any], list[str] | None]  # entry, steamapps names if available


class DiscoverError(Exception):
    """libraryfolders.vdf is missing or unusable, so no library can be listed (B1)."""


class _Refused(Exception):
    """A file that cannot be used. `code` is an issue code, or, from _load_vdf, one of
    "missing", "unreadable" and "malformed" for the caller to map to its own code."""

    def __init__(self, code: str, reason: str) -> None:
        super().__init__(reason)
        self.code = code


@dataclass(frozen=True)
class _Manifest:
    path: str
    appid: int
    installdir: str
    app: dict[str, Any]  # the AppState block


# ---------------------------------------------------------------------------- public


def scan(steam_root: str | os.PathLike[str]) -> dict[str, Any]:
    """Libraries, game cards and issues of the Steam install at `steam_root` (B1-B7).

    Raises DiscoverError if libraryfolders.vdf cannot be used. Reads only.
    """
    root = _absolute(steam_root)
    errors: list[_Issue] = []
    warnings: list[_Issue] = []
    libraries = _libraries(root, errors, warnings)
    config = _read_config(root, errors, warnings)
    found: list[tuple[dict[str, Any], str]] = []  # card, manifest path
    for entry, names in libraries:
        if names is not None:
            found += _library_cards(entry["path"], names, root, config, errors, warnings)
    found.sort(key=lambda item: (item[0]["appid"], item[0]["library"]))
    _flag_duplicates(found, warnings)
    return {
        "discover_version": DISCOVER_VERSION,
        "steam_root": root,
        "libraries": [entry for entry, _ in libraries],
        "games": [card for card, _ in found],
        "errors": _sort_issues(errors),
        "warnings": _sort_issues(warnings),
    }


def find_libraries(steam_root: str | os.PathLike[str]) -> list[dict[str, Any]]:
    """[{"path", "available"}] for every library, root first (B1, B2). Reads only."""
    return [entry for entry, _ in _libraries(_absolute(steam_root), [], [])]


def main(argv: list[str] | None = None) -> int:
    """CLI (B8): print scan() as JSON and return 0; return 2 on DiscoverError."""
    parser = argparse.ArgumentParser(
        prog="deckforge.discover",
        description="List the games of a Steam install as JSON. Reads only; writes nothing.",
        allow_abbrev=False,
    )
    parser.add_argument("--steam-root", required=True, help="the Steam folder to scan")
    args = parser.parse_args(argv)
    try:
        result = scan(args.steam_root)
    except DiscoverError as exc:
        sys.stderr.write(f"deckforge.discover: {exc}\n")
        return 2
    sys.stdout.write(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n")
    return 0


# ---------------------------------------------------------------------------- libraries


def _absolute(steam_root: str | os.PathLike[str]) -> str:
    """Same as os.path.abspath: absolute and normalized, links not resolved, ~ not expanded."""
    return os.path.normpath(Path(steam_root).absolute())


def _libraries(root: str, errors: list[_Issue], warnings: list[_Issue]) -> list[_Library]:
    """The root, then each listed library, de-duplicated by real path (B2)."""
    block = _read_libraryfolders(root)
    libraries = [_open_library(root, errors, warnings)]
    seen = {os.path.realpath(root)}
    for written in _listed_paths(block, warnings):
        if not written or "\\" in written or not Path(written).is_absolute():
            message = "library path is empty, relative or contains a backslash"
            warnings.append(_issue("library_path_invalid", written, message))
            libraries.append(({"path": written, "available": False}, None))
            continue
        path = os.path.normpath(written)
        real = os.path.realpath(path)
        if real not in seen:
            seen.add(real)
            libraries.append(_open_library(path, errors, warnings))
    return libraries


def _read_libraryfolders(root: str) -> dict[str, Any]:
    """The `libraryfolders` block of <root>/steamapps/libraryfolders.vdf (B1)."""
    path = Path(root, "steamapps", "libraryfolders.vdf")
    try:
        block = vdf.find(_load_vdf(path, _SMALL_CAP), "libraryfolders")
    except _Refused as exc:
        raise DiscoverError(f"cannot use {str(path)!r}: {exc}") from exc
    if not isinstance(block, dict):
        raise DiscoverError(f"cannot use {str(path)!r}: no libraryfolders block")
    return block


def _listed_paths(block: dict[str, Any], warnings: list[_Issue]) -> list[str]:
    """Path strings of the numbered entries in numeric key order; other keys are ignored."""
    paths = []
    for _, key in sorted((n, key) for key in block if (n := _as_int(key)) is not None):
        value = block[key]
        # Current layout: a block with a path key. Legacy layout: the path string itself.
        path = vdf.find(value, "path") if isinstance(value, dict) else value
        if isinstance(path, str):
            paths.append(path)
        else:
            message = "a numbered library entry has no path"
            warnings.append(_issue("library_entry_invalid", None, message))
    return paths


def _open_library(path: str, errors: list[_Issue], warnings: list[_Issue]) -> _Library:
    """The library entry, available only if <path>/steamapps is a folder scandir can list."""
    steamapps = Path(path, "steamapps")
    try:
        if not _folder_exists(steamapps):
            warnings.append(_issue("library_unavailable", path, "steamapps is not a folder"))
            return {"path": path, "available": False}, None
        with os.scandir(steamapps) as listing:
            names = sorted(entry.name for entry in listing)
    except OSError as exc:
        message = f"cannot check or list steamapps: {_why(exc)}"
        errors.append(_issue("library_unreadable", str(steamapps), message))
        warnings.append(_issue("library_unavailable", path, "steamapps cannot be read"))
        return {"path": path, "available": False}, None
    return {"path": path, "available": True}, names


# ---------------------------------------------------------------------------- manifests


def _library_cards(
    library: str,
    names: list[str],
    root: str,
    config: dict[str, Any] | None,
    errors: list[_Issue],
    warnings: list[_Issue],
) -> list[tuple[dict[str, Any], str]]:
    """(card, manifest path) for each accepted appmanifest_<x>.acf in one library (B3)."""
    install_folders = _install_folder_names(Path(library, "steamapps", "common"), warnings)
    found = []
    for name in names:
        match = _MANIFEST_NAME.fullmatch(name)
        if match is None:
            continue
        path = str(Path(library, "steamapps", name))
        try:
            manifest = _read_manifest(path, match.group(1))
        except _Refused as exc:
            errors.append(_issue(exc.code, path, str(exc)))
            continue
        found.append((_card(manifest, library, root, install_folders, config), path))
    return found


def _read_manifest(path: str, file_id: str) -> _Manifest:
    """Read and check one manifest; raises _Refused with its B3 code."""
    try:
        doc = _load_vdf(Path(path), _SMALL_CAP)
    except _Refused as exc:
        code = "manifest_malformed" if exc.code == "malformed" else "manifest_unreadable"
        raise _Refused(code, str(exc)) from exc
    app = vdf.find(doc, "AppState")
    if not isinstance(app, dict):
        raise _Refused("manifest_malformed", "no AppState block")
    appid_text, installdir = vdf.find(app, "appid"), vdf.find(app, "installdir")
    if not isinstance(appid_text, str) or not isinstance(installdir, str):
        raise _Refused("manifest_incomplete", "appid or installdir is missing")
    appid = _as_int(appid_text)
    if appid is None or appid != _as_int(file_id):
        message = "appid is not all digits or differs from the file name"
        raise _Refused("manifest_appid_mismatch", message)
    if (
        installdir in _UNSAFE_INSTALLDIRS
        or "/" in installdir
        or "\\" in installdir
        or Path(installdir).is_absolute()
    ):
        raise _Refused("manifest_unsafe_installdir", "installdir is not a plain folder name")
    return _Manifest(path, appid, installdir, app)


def _card(
    manifest: _Manifest,
    library: str,
    root: str,
    install_folders: frozenset[str],
    config: dict[str, Any] | None,
) -> dict[str, Any]:
    """The B1 fields of one game card (B4, B5)."""
    app, appid = manifest.app, manifest.appid
    warnings: list[_Issue] = []
    name = vdf.find(app, "name")
    if not isinstance(name, str):
        name = None
        warnings.append(_issue("name_missing", manifest.path, "the manifest has no name"))
    state_flags = _as_int(vdf.find(app, "StateFlags"))
    if state_flags is None:
        message = "StateFlags is missing or not an integer"
        warnings.append(_issue("stateflags_invalid", manifest.path, message))
    install_path = Path(library, "steamapps", "common", manifest.installdir)
    # Exact case: the name must be listed as written, even on a case-insensitive disk.
    has_folder = manifest.installdir in install_folders and _is_folder(install_path)
    if not has_folder:
        message = "install folder not found"
        warnings.append(_issue("install_folder_missing", str(install_path), message))
    prefix_path = _prefix_path(appid, library, root, warnings)
    kind = "tool" if _is_tool(name) else "game"
    walked = str(install_path) if has_folder else None
    detected, found = detect.card_fields(
        appid, kind=kind, state_flags=state_flags, install_path=walked, prefix_path=prefix_path
    )
    warnings += [_issue(code, path, message) for code, path, message in found]
    buildid = vdf.find(app, "buildid")
    shadercache = Path(library, "steamapps", "shadercache", str(appid))
    return {
        "appid": appid,
        "name": name,
        "kind": kind,
        "library": library,
        "installdir": manifest.installdir,
        "buildid": buildid if isinstance(buildid, str) else None,
        "state_flags": state_flags,
        "installed": state_flags is not None
        and (state_flags & _FULLY_INSTALLED) != 0
        and has_folder,
        "install_path": str(install_path),
        "prefix_path": prefix_path,
        "shadercache_path": str(shadercache) if _is_folder(shadercache) else None,
        "compat_tool": _compat_tool(config, appid),
        **detected,
        "warnings": _sort_issues(warnings),
    }


def _is_tool(name: str | None) -> bool:
    """Proton, Steam Linux Runtime and Steamworks redistributables (case-sensitive)."""
    return name is not None and (name == "Proton" or name.startswith(_TOOL_PREFIXES))


def _prefix_path(appid: int, library: str, root: str, warnings: list[_Issue]) -> str | None:
    """The game's own Proton prefix; if absent, the root library's (with a warning); else None.

    If either check fails with an error other than "absent", None and a prefix_unreadable
    warning for that path: later phases write into prefixes, so a guess is not allowed.
    """
    own = Path(library, "steamapps", "compatdata", str(appid), "pfx")
    in_root = Path(root, "steamapps", "compatdata", str(appid), "pfx")
    for path in [own] if library == root else [own, in_root]:
        try:
            if not _folder_exists(path):
                continue
        except OSError as exc:
            message = f"cannot check the Proton prefix ({_why(exc)}); no prefix is used"
            warnings.append(_issue("prefix_unreadable", str(path), message))
            return None
        if path != own:
            message = "the Proton prefix is in the root library"
            warnings.append(_issue("prefix_in_other_library", str(in_root), message))
        return str(path)
    return None


def _flag_duplicates(found: list[tuple[dict[str, Any], str]], warnings: list[_Issue]) -> None:
    """B6: a card whose appid equals the previous card's (games order) adds a warning."""
    for (previous, _), (card, path) in zip(found, found[1:], strict=False):
        if card["appid"] == previous["appid"]:
            message = "the same appid is installed in another library"
            warnings.append(_issue("duplicate_appid", path, message))


# ---------------------------------------------------------------------------- config.vdf


def _read_config(root: str, errors: list[_Issue], warnings: list[_Issue]) -> dict[str, Any] | None:
    """config.vdf, or None with an issue (B5). It holds account data: only _compat_tool reads it."""
    path = Path(root, "config", "config.vdf")
    try:
        return _load_vdf(path, _CONFIG_CAP)
    except _Refused as exc:
        if exc.code == "missing":
            message = "config.vdf not found; no compat_tool is known"
            warnings.append(_issue("config_vdf_missing", str(path), message))
        else:
            message = f"{exc}; no compat_tool is known"
            errors.append(_issue("config_vdf_malformed", str(path), message))
        return None


def _compat_tool(config: dict[str, Any] | None, appid: int) -> str | None:
    """The tool CompatToolMapping names for `appid`. Entry 0 is Steam's default: never used."""
    if config is None or appid == 0:
        return None
    name = vdf.find(config, *_COMPAT_TOOL_MAPPING, str(appid), "name")
    return name if isinstance(name, str) and name else None


# ---------------------------------------------------------------------------- helpers


def _load_vdf(path: Path, cap: int) -> dict[str, Any]:
    """Parse a regular file of at most `cap` bytes: strict UTF-8, one leading BOM allowed.

    Raises _Refused with code "missing", "unreadable" or "malformed".
    """
    try:
        info = path.stat()  # follows links, so a link to a regular file is read
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise _Refused("missing", "file not found") from exc
    except OSError as exc:
        raise _Refused("unreadable", f"cannot stat: {_why(exc)}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise _Refused("unreadable", "not a regular file")
    if info.st_size > cap:
        raise _Refused("unreadable", f"larger than {cap} bytes")
    try:
        with path.open("rb") as file:
            data = file.read(cap + 1)
    except OSError as exc:
        raise _Refused("unreadable", f"cannot read: {_why(exc)}") from exc
    if len(data) > cap:  # grew after the size check
        raise _Refused("unreadable", f"larger than {cap} bytes")
    try:
        return vdf.parse(data.decode("utf-8-sig"))
    except UnicodeDecodeError as exc:
        raise _Refused("malformed", "not UTF-8 text") from exc
    except vdf.VdfError as exc:
        raise _Refused("malformed", f"not valid VDF (line {exc.line})") from exc


def _folder_exists(path: Path) -> bool:
    """True for a folder (links followed); False if absent: not found, or a path part is
    not a folder. Any other OSError (permission, I/O, link loop) is raised."""
    try:
        return stat.S_ISDIR(path.stat().st_mode)
    except (FileNotFoundError, NotADirectoryError):
        return False


def _is_folder(path: Path) -> bool:
    """_folder_exists, but an error is logged at WARNING with the path and counts as False."""
    try:
        return _folder_exists(path)
    except OSError as exc:
        _log.warning("cannot check folder %s: %s", path, _why(exc))
        return False


def _install_folder_names(common: Path, warnings: list[_Issue]) -> frozenset[str]:
    """Names listed in steamapps/common; empty if absent, or with a common_unreadable
    warning if it exists but cannot be listed (its games then count as not installed)."""
    try:
        with os.scandir(common) as listing:
            return frozenset(entry.name for entry in listing)
    except (FileNotFoundError, NotADirectoryError):
        return frozenset()
    except OSError as exc:
        message = f"cannot list install folders ({_why(exc)}); its games count as not installed"
        warnings.append(_issue("common_unreadable", str(common), message))
        return frozenset()


def _as_int(value: object) -> int | None:
    """An all-ASCII-digit string as an int; None for anything else."""
    if not isinstance(value, str) or not _DIGITS.fullmatch(value):
        return None
    try:
        return int(value)
    except ValueError:  # more digits than Python's int-from-str limit
        return None


def _why(exc: OSError) -> str:
    return exc.strerror or type(exc).__name__


def _issue(code: str, path: str | None, message: str) -> _Issue:
    return {"code": code, "path": path, "message": message}


def _sort_issues(issues: list[_Issue]) -> list[_Issue]:
    return sorted(issues, key=lambda issue: (issue["code"], issue["path"] or ""))


if __name__ == "__main__":
    raise SystemExit(main())
