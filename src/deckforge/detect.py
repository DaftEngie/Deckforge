"""Signature detection for one game card (PR B2 of docs/specs/discover.md, criteria C1-C9).

`card_fields(appid, kind=, state_flags=, install_path=, prefix_path=)` returns the B2 card
fields (engine, engine_evidence, anticheat, upscalers, injectors, settings_files,
tier_i_eligible) and the card warnings it found as (code, path, message) tuples;
deckforge.discover turns those into issues. Only names are inspected: this module opens no
file, not even a settings file. Folders are listed with os.scandir; the only other calls
that touch the disk are stat and os.path.realpath.

Walks (C1) go breadth-first from a start folder (which may be a link), each folder's entries
sorted by name, to a depth limit (path parts below the start: 10 in the install folder, 6 in
the prefix), for at most 20,000 entries. A link found during a walk is matched by its name
but never entered, so it never counts as a folder; nor is a folder on another device. In
the install and Program Files walks either one adds not_entered (anti-cheat could sit behind
it); the C6 settings walks skip them silently, and never enter a folder named dosdevices.
  card warnings  scan_truncated (path = start folder), unreadable (a folder that cannot be
                 listed, or a start folder, entry, link target or user.reg that cannot be
                 checked), not_entered (absolute path), non_utf8_filename (one per name),
                 injector_with_anticheat (one per injector evidence path, with anti-cheat)
Tier I eligibility (C7) fails closed: a game, fully installed (state_flags exactly 4) with a
prefix, whose walks were all complete (no scan_truncated, unreadable or not_entered) and
found no anti-cheat. Settings files (C6) are regular files that are not links.
Evidence is relative to the start folder, "/"-joined, in on-disk case; prefix evidence is
"pfx/<path relative to the prefix>". A name that is not UTF-8 is shown with backslashreplace
in evidence and warning paths. A settings file whose path holds such a name is left out:
a path that does not exist on disk must never reach later phases.
"""

from __future__ import annotations

import os
import stat
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, NamedTuple

# Games with anti-cheat their files do not show (C3). Phase 3 reuses this list for R16.
CURATED_ANTICHEAT = {2183900: "easyanticheat", 553850: "gameguard"}

INSTALL_DEPTH = 10
PREFIX_DEPTH = 6
ENTRY_CAP = 20_000  # entries per start folder (files, folders and links)

_CURATED = "(curated)"
_PREFIX_SYSTEMS = ("easyanticheat", "battleye")  # gameguard is an install-only signature
_PROGRAM_FILES = (("drive_c", "Program Files"), ("drive_c", "Program Files (x86)"))
_STEAMUSER = ("drive_c", "users", "steamuser")
_UNREAL_SETTINGS_FOLDERS = (
    (*_STEAMUSER, "AppData", "Local"),
    (*_STEAMUSER, "Documents", "My Games"),
    (*_STEAMUSER, "My Documents", "My Games"),
)
_NEVER_ENTERED = "dosdevices"  # Wine's drive links (z: is the whole Deck), in C6 walks
_UPSCALERS = {
    "nvngx_dlss.dll": "dlss",
    "nvngx_dlssg.dll": "dlss_fg",
    "amd_fidelityfx_dx12.dll": "ffx_sdk",
    "amd_fidelityfx_vk.dll": "ffx_sdk",
    "ffx_fsr2_api_x64.dll": "fsr2",
    "libxess.dll": "xess",
}
_SHIPPING_SUFFIXES = ("-win64-shipping.exe", "-wingdk-shipping.exe")
_UNREAL_PLATFORMS = ("win64", "wingdk")
_UNITY_MARKERS = ("globalgamemanagers", "boot.config")
_UNREAL_INI = ("gameusersettings.ini", "engine.ini")
_INCOMPLETE = ("scan_truncated", "unreadable", "not_entered")  # any one: not Tier I eligible
_FULLY_INSTALLED = 4  # StateFlags with nothing pending (C7)

Finding = tuple[str, str, str]  # (code, path, message): one card warning
_Hits = defaultdict[tuple[str, str], list[str]]  # (category, name) -> evidence
_Setting = tuple[str, str, str]  # (absolute path, class, kind)


class _Entry(NamedTuple):
    """One entry a walk visited."""

    names: tuple[str, ...]  # path parts below the start folder, as listed
    folded: tuple[str, ...]  # the same parts, casefolded, for matching
    is_folder: bool  # a real folder; a link never counts as one
    is_file: bool  # a regular file that is not a link: the only kind settings_files lists

    @property
    def rel(self) -> str:
        """The evidence form: relative, "/"-joined, on-disk case, valid UTF-8 (C1)."""
        return "/".join(_text(name) for name in self.names)


# ---------------------------------------------------------------------------- public


def card_fields(
    appid: int,
    *,
    kind: str,
    state_flags: int | None,
    install_path: str | None,
    prefix_path: str | None,
) -> tuple[dict[str, Any], list[Finding]]:
    """The B2 fields of one card and its card warnings (C2-C8). Reads names only.

    `install_path` is None when the install folder is missing (C8): nothing is walked, and
    only a curated anti-cheat entry can be reported. `prefix_path` None skips the prefix;
    discover also gives None whenever it reports prefix_unreadable (B4).
    """
    notes: list[Finding] = []
    hits: _Hits = defaultdict(list)
    settings: list[_Setting] = []
    if appid in CURATED_ANTICHEAT:
        hits["anticheat", CURATED_ANTICHEAT[appid]].append(_CURATED)
    if install_path is not None:
        install = _walk(install_path, INSTALL_DEPTH, notes, required=True)
        _match_install(install, hits)
        if prefix_path is not None:
            _match_program_files(prefix_path, hits, notes)
        matched = {name for category, name in hits if category == "engine"}
        settings = _install_settings(install_path, install, matched)
        if prefix_path is not None:
            settings += _prefix_settings(prefix_path, matched, notes)
    engines = [name for name, _ in _grouped(hits, "engine")]
    anticheat = [{"system": name, "evidence": paths} for name, paths in _grouped(hits, "anticheat")]
    injectors = _named(hits, "injector")
    if anticheat:
        message = "an injector is installed in a game with anti-cheat"
        notes += [
            ("injector_with_anticheat", path, message)
            for injector in injectors
            for path in injector["evidence"]
        ]
    walks_complete = not any(code in _INCOMPLETE for code, _, _ in notes)
    fields = {
        "engine": (engines[0] if len(engines) == 1 else "ambiguous") if engines else "unknown",
        "engine_evidence": sorted(path for _, paths in _grouped(hits, "engine") for path in paths),
        "anticheat": anticheat,
        "upscalers": _named(hits, "upscaler"),
        "injectors": injectors,
        "settings_files": _deduplicated(settings),
        # C7 fails closed: a scan that could not look somewhere never says "eligible".
        "tier_i_eligible": kind == "game"
        and state_flags == _FULLY_INSTALLED
        and install_path is not None
        and prefix_path is not None
        and walks_complete
        and not anticheat,
    }
    return fields, notes


# ---------------------------------------------------------------------------- walks


def _walk(
    start: str,
    limit: int,
    notes: list[Finding],
    *,
    required: bool = False,
    settings: bool = False,
) -> list[_Entry]:
    """The entries below `start` in C1 order: breadth-first, each folder sorted by name.

    A start folder that is absent or not a folder gives no entries, with an unreadable note
    if it is `required`. Links and folders on another device are matched by name but not
    entered: a `settings` (C6) walk skips them silently, and dosdevices too; any other walk
    adds a not_entered note for a link to a folder or a folder on another device.
    """
    try:
        info = _lookup(start)
    except OSError as exc:
        notes.append(("unreadable", start, f"cannot check the folder: {exc}"))
        return []
    if info is None or not stat.S_ISDIR(info.st_mode):
        if required:
            notes.append(("unreadable", start, "the folder is no longer there"))
        return []
    device = info.st_dev
    found: list[_Entry] = []
    truncated = False
    queue: deque[tuple[_Entry, str]] = deque([(_Entry((), (), True, False), start)])
    while queue:
        parent, path = queue.popleft()
        try:
            with os.scandir(path) as listing:
                items = sorted(listing, key=lambda item: item.name)
        except OSError as exc:
            notes.append(("unreadable", _shown(start, parent.names), f"cannot list: {exc}"))
            continue
        for item in items:
            if len(found) == ENTRY_CAP:
                truncated = True
                queue.clear()
                break
            entry, enter = _visit(start, parent, item, device, settings, notes)
            found.append(entry)
            if enter and len(entry.names) < limit:
                queue.append((entry, item.path))
            elif enter:
                truncated |= _has_entries(item.path, _shown(start, entry.names), notes)
    if truncated:
        message = f"names below depth {limit} or past {ENTRY_CAP} entries were not checked"
        notes.append(("scan_truncated", start, message))
    return found


def _visit(
    start: str,
    parent: _Entry,
    item: os.DirEntry[str],
    device: int,
    settings: bool,
    notes: list[Finding],
) -> tuple[_Entry, bool]:
    """The entry for one listed item, and whether the walk enters it (see _walk)."""
    name = item.name
    names, folded = (*parent.names, name), (*parent.folded, name.casefold())
    if not _is_utf8(name):
        message = "the name is not UTF-8; evidence shows it with backslash escapes"
        notes.append(("non_utf8_filename", _shown(start, names), message))
    is_folder = is_file = enter = hidden = False
    try:
        is_folder = item.is_dir(follow_symlinks=False)
        is_file = item.is_file(follow_symlinks=False)
        if is_folder:
            hidden = item.stat(follow_symlinks=False).st_dev != device
            enter = not hidden and not (settings and folded[-1] == _NEVER_ENTERED)
        elif not settings and item.is_symlink():
            hidden = _links_to_folder(item)
    except OSError as exc:
        notes.append(("unreadable", _shown(start, names), f"cannot check the entry: {exc}"))
    if hidden and not settings:
        message = "a link to a folder or a folder on another disk; not searched"
        notes.append(("not_entered", _shown(start, names), message))
    return _Entry(names, folded, is_folder, is_file), enter


def _links_to_folder(item: os.DirEntry[str]) -> bool:
    """Whether a link leads to a folder, through any chain of links. A broken link (target
    not found, or a part of it is a file) does not; any other OSError is raised."""
    try:
        return item.is_dir()  # follows the link; returns False if the target is not found
    except NotADirectoryError:
        return False


def _has_entries(path: str, shown: str, notes: list[Finding]) -> bool:
    """Whether a folder at the depth limit has contents, which the walk then skips."""
    try:
        with os.scandir(path) as listing:
            return next(listing, None) is not None
    except OSError as exc:
        notes.append(("unreadable", shown, f"cannot list: {exc}"))
        return False


def _lookup(path: str, *, follow_symlinks: bool = True) -> os.stat_result | None:
    """stat (or lstat) of `path`; None if absent: not found, or a path part is not a
    folder. Any other OSError (permission, I/O, link loop) is raised."""
    try:
        return Path(path).stat(follow_symlinks=follow_symlinks)
    except (FileNotFoundError, NotADirectoryError):
        return None


# ---------------------------------------------------------------------------- signatures


def _match_install(entries: list[_Entry], hits: _Hits) -> None:
    """C2-C5 signatures in the install walk."""
    dinput8_folders = {
        entry.names[:-1]
        for entry in entries
        if not entry.is_folder and entry.folded[-1] == "dinput8.dll"
    }
    for entry in entries:
        name = entry.folded[-1]
        system = _anticheat(name)
        if system is not None:
            hits["anticheat", system].append(entry.rel)
        if entry.is_folder:
            if name == "reframework" and entry.names[:-1] in dinput8_folders:
                hits["injector", "reframework"].append(entry.rel)
            continue
        engine = _engine(entry.folded)
        if engine is not None:
            hits["engine", engine].append(entry.rel)
        if name in _UPSCALERS:
            hits["upscaler", _UPSCALERS[name]].append(entry.rel)
        if name == "optiscaler.ini":
            hits["injector", "optiscaler"].append(entry.rel)


def _match_program_files(prefix: str, hits: _Hits, notes: list[Finding]) -> None:
    """C3: EAC and BattlEye signatures in the prefix's two Program Files folders."""
    for parts in _PROGRAM_FILES:
        for entry in _walk(str(Path(prefix, *parts)), PREFIX_DEPTH, notes):
            system = _anticheat(entry.folded[-1])
            if system in _PREFIX_SYSTEMS:
                hits["anticheat", system].append("/".join(("pfx", *parts, entry.rel)))


def _anticheat(name: str) -> str | None:
    """The anti-cheat system a casefolded file or folder name belongs to (C3)."""
    if name.startswith("easyanticheat") or name == "start_protected_game.exe":
        return "easyanticheat"
    if name == "battleye" or name.startswith(("beservice", "beclient")):
        return "battleye"
    return "gameguard" if name == "gameguard" else None


def _engine(folded: tuple[str, ...]) -> str | None:
    """The engine a file points to, from its casefolded path below the install folder (C2)."""
    name, depth = folded[-1], len(folded)
    if (
        depth >= 3
        and folded[-3] == "binaries"
        and folded[-2] in _UNREAL_PLATFORMS
        and name.endswith(_SHIPPING_SUFFIXES)
    ):
        return "unreal"
    if (depth <= 2 and name == "unityplayer.dll") or (
        _in_unity_data(folded) and name in _UNITY_MARKERS
    ):
        return "unity"
    return "re_engine" if depth == 1 and name == "re_chunk_000.pak" else None


def _in_unity_data(folded: tuple[str, ...]) -> bool:
    """Directly inside a *_Data folder at the install root or one level below."""
    return 2 <= len(folded) <= 3 and folded[-2].endswith("_data")


# ---------------------------------------------------------------------------- settings files


def _install_settings(install: str, entries: list[_Entry], engines: set[str]) -> list[_Setting]:
    """C6 class I files in the install folder, for the engines that matched."""
    found = []
    for entry in entries:
        if not entry.is_file or not _is_plain(entry):
            continue
        name, path = entry.folded[-1], str(Path(install, *entry.names))
        if "re_engine" in engines and entry.folded == ("config.ini",):
            found.append((path, "I", "ini"))
        if "unity" in engines and name == "boot.config" and _in_unity_data(entry.folded):
            found.append((path, "I", "boot_config"))
    return found


def _prefix_settings(prefix: str, engines: set[str], notes: list[Finding]) -> list[_Setting]:
    """C6 class P files in the prefix: Unity's user.reg, Unreal's Saved/Config ini files."""
    found = []
    if "unity" in engines:
        registry = str(Path(prefix, "user.reg"))
        try:
            info = _lookup(registry, follow_symlinks=False)  # a link is never listed
        except OSError as exc:
            notes.append(("unreadable", registry, f"cannot check the file: {exc}"))
            info = None
        if info is not None and stat.S_ISREG(info.st_mode):
            found.append((registry, "P", "registry"))
    if "unreal" in engines:
        real_prefix = os.path.realpath(prefix)
        for parts in _UNREAL_SETTINGS_FOLDERS:
            start = str(Path(prefix, *parts))
            # A start folder that leads out of the prefix (a link to z:, say) is not used.
            if os.path.commonpath((os.path.realpath(start), real_prefix)) != real_prefix:
                continue
            for entry in _walk(start, PREFIX_DEPTH, notes, settings=True):
                if (
                    entry.is_file
                    and entry.folded[-1] in _UNREAL_INI
                    and _under_saved_config(entry.folded[:-1])
                    and _is_plain(entry)
                ):
                    found.append((str(Path(start, *entry.names)), "P", "ini"))
    return found


def _under_saved_config(folders: tuple[str, ...]) -> bool:
    """Whether casefolded folder names hold "saved" directly followed by "config"."""
    return ("saved", "config") in zip(folders, folders[1:], strict=False)


def _deduplicated(settings: list[_Setting]) -> list[dict[str, str]]:
    """Sorted by path; of entries with the same real path, the first is kept (C6)."""
    kept, seen = [], set()
    for path, cls, kind in sorted(settings):
        real = os.path.realpath(path)
        if real not in seen:
            seen.add(real)
            kept.append({"path": path, "class": cls, "kind": kind})
    return kept


# ---------------------------------------------------------------------------- helpers


def _grouped(hits: _Hits, category: str) -> list[tuple[str, list[str]]]:
    """(name, sorted evidence) for one category, sorted by name."""
    return [(name, sorted(paths)) for (cat, name), paths in sorted(hits.items()) if cat == category]


def _named(hits: _Hits, category: str) -> list[dict[str, Any]]:
    """[{"name", "evidence"}] for one category (C4, C5)."""
    return [{"name": name, "evidence": paths} for name, paths in _grouped(hits, category)]


def _text(name: str) -> str:
    """`name` as valid UTF-8 text: bytes that are not UTF-8 are shown as \\xNN (C1)."""
    return name if name.isascii() else os.fsencode(name).decode("utf-8", "backslashreplace")


def _is_utf8(name: str) -> bool:
    return _text(name) == name


def _is_plain(entry: _Entry) -> bool:
    """Whether every name on the entry's path is UTF-8, so its path can be written exactly."""
    return all(_is_utf8(name) for name in entry.names)


def _shown(start: str, names: tuple[str, ...]) -> str:
    """A warning path: the start folder joined with the relative parts, as text."""
    return str(Path(start, *(_text(name) for name in names)))
