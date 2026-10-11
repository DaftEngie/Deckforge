# Contracts for PR B2 of docs/specs/discover.md, criteria C1 (walks) and C9 (purity of
# src/deckforge/detect.py). Written test-first: detect.py does not exist yet and the cards
# from deckforge.discover.scan do not have the B2 fields. Everything is observed through
# discover.scan, the public surface; deckforge.detect is imported lazily so that each test
# fails on its own.
#
# Fields B2 adds to every card in scan(root)["games"] (shared by the three B2 test files)
#   engine, engine_evidence, anticheat, tier_i_eligible, upscalers, injectors and
#   settings_files, and the card warning codes scan_truncated, unreadable,
#   non_utf8_filename and injector_with_anticheat (B1 issue shape, warnings kept sorted).
#
# Walk, criterion C1 (the spec names no walk function; it is observed through evidence)
#   Pre:  a start folder, which may itself be a link and is then followed: the card's
#         install_path (depth limit 10); <prefix>/drive_c/Program Files and
#         <prefix>/drive_c/Program Files (x86) (depth limit 6); the three C6 settings
#         folders (depth limit 6).
#   Post: entries are visited breadth-first, each folder's entries sorted by name. Depth is
#         the number of path parts below the start folder: a name at depth 10 (install) or
#         6 (prefix) is matched, nothing deeper is.
#   Post: at most 20,000 entries (files, folders and links) per start folder; the start
#         folder itself is not counted. The cap of one walk does not limit another.
#   Post: exactly one scan_truncated card warning, path = the start folder, when the cap
#         cut entries off or a folder at the depth limit has contents; none otherwise
#         (an empty folder at the limit, a link, or another disk skips nothing).
#   Post: a link is matched by its name, even a broken one, and is never entered.
#   Post: a folder whose st_dev differs from the start folder's is not entered.
#   Post: a folder os.scandir cannot list adds one unreadable card warning, path = that
#         folder (the start folder joined with the relative parts, the way B4 builds paths),
#         and the walk goes on with the other folders.
#   Post: a name that is not valid UTF-8 shows in evidence as
#         os.fsencode(name).decode("utf-8", "backslashreplace") and adds a
#         non_utf8_filename card warning. Valid UTF-8 names are kept as they are, without it.
#   Inv:  evidence paths are relative to the start folder, use "/", keep the on-disk case,
#         and are valid UTF-8 text.
#
# Purity, criterion C9
#   Inv:  detect.CURATED_ANTICHEAT == {2183900: "easyanticheat", 553850: "gameguard"}.
#   Inv:  detect.py imports only __future__, argparse, json, logging, os, stat, sys,
#         pathlib, re, fnmatch, dataclasses, typing, collections and deckforge.*; makes no
#         attribute call named in the B9 banned list (str.replace included), except
#         sys.stdout.write and sys.stderr.write; lists folders only with os.scandir; starts
#         no process; uses no eval, exec, compile or __import__.
#   Inv:  detect.py opens no files at all. Its source has no open, os.open, Path.open,
#         read_text, read_bytes or fdopen. At run time no open call has a detect.py frame
#         on its stack, while detect.py does list folders through os.scandir.
#
# Round trip: B2 has no write or restore path, so there is nothing to apply and restore.
# The property used instead is B9's, over B2-specific trees (links, a link loop, broken
# links, non-UTF-8 names, dosdevices links, settings files of every class): two scans
# leave every byte and every lstat field of the tree unchanged.

import ast
import builtins
import errno
import importlib
import inspect
import io
import os
import pathlib
import stat
from pathlib import Path

import pytest

from deckforge import discover

ROOT = Path(__file__).resolve().parents[1]
DETECT_SOURCE = ROOT / "src" / "deckforge" / "detect.py"
DETECT_REAL = os.path.realpath(DETECT_SOURCE)
APPID = 1086940
CAP = 20_000
D9 = "/".join(f"d{n}" for n in range(1, 10))  # nine folders: a name inside has depth 10
D10 = f"{D9}/d10"
P5 = "p1/p2/p3/p4/p5"  # five folders: a name inside has depth 6
PROGRAM_FILES = "drive_c/Program Files"
LOCAL = "drive_c/users/steamuser/AppData/Local"
UNREAL_EXE = "Game/Binaries/Win64/Game-Win64-Shipping.exe"
B2_FIELDS = {
    "engine",
    "engine_evidence",
    "anticheat",
    "tier_i_eligible",
    "upscalers",
    "injectors",
    "settings_files",
}
ALLOWED_IMPORTS = {
    "__future__",
    "argparse",
    "json",
    "logging",
    "os",
    "stat",
    "sys",
    "pathlib",
    "re",
    "fnmatch",
    "dataclasses",
    "typing",
    "collections",
}
BANNED_CALLS = {
    "write",
    "write_text",
    "write_bytes",
    "unlink",
    "remove",
    "rmdir",
    "mkdir",
    "makedirs",
    "rename",
    "replace",
    "touch",
    "chmod",
    "symlink_to",
    "hardlink_to",
    "symlink",
    "link",
    "truncate",
}
ALLOWED_WRITES = {"sys.stdout.write", "sys.stderr.write"}
OTHER_LISTING = {"listdir", "walk", "fwalk", "iterdir", "glob", "rglob"}
OPENING = {"open", "read_text", "read_bytes", "fdopen", "open_code"}
PROCESS_OR_CHANGE = {
    "system",
    "popen",
    "execl",
    "execle",
    "execlp",
    "execlpe",
    "execv",
    "execve",
    "execvp",
    "execvpe",
    "spawnl",
    "spawnle",
    "spawnlp",
    "spawnlpe",
    "spawnv",
    "spawnve",
    "spawnvp",
    "spawnvpe",
    "fork",
    "forkpty",
    "posix_spawn",
    "posix_spawnp",
    "kill",
    "killpg",
    "utime",
    "chown",
    "lchown",
    "fchown",
    "fchmod",
    "lchmod",
    "ftruncate",
    "removedirs",
    "renames",
    "mkfifo",
    "mknod",
    "setxattr",
    "removexattr",
    "startfile",
}
DYNAMIC_CODE = {"eval", "exec", "compile", "__import__"}


# ---------------------------------------------------------------------------- helpers


def q(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def manifest(appid: int, name: str, flags: str) -> bytes:
    return (
        f'"AppState"\n{{\n\t"appid"\t\t"{appid}"\n\t"name"\t\t{q(name)}\n'
        f'\t"StateFlags"\t\t"{flags}"\n\t"installdir"\t\t"Game"\n\t"buildid"\t\t"1"\n}}\n'
    ).encode()


def put(path: Path, data: bytes = b"") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def plant(base: Path, entries) -> None:
    """Create each relative entry under base: a trailing "/" makes a folder, else an empty file."""
    for rel in entries:
        if rel.endswith("/"):
            (base / rel).mkdir(parents=True, exist_ok=True)
        else:
            put(base / rel)


def make_steam(base: Path, *libraries: Path) -> Path:
    root = base / "steam"
    blocks = "".join(
        f'\t"{n}"\n\t{{\n\t\t"path"\t\t{q(str(path))}\n\t}}\n'
        for n, path in enumerate([root, *libraries])
    )
    put(root / "steamapps" / "libraryfolders.vdf", f'"libraryfolders"\n{{\n{blocks}}}\n'.encode())
    for library in libraries:
        (library / "steamapps").mkdir(parents=True, exist_ok=True)
    return root


def add_game(
    library: Path, appid: int = APPID, *, name: str = "Test Game", flags: str = "4"
) -> tuple[Path, Path]:
    """Write the manifest; return (install folder, prefix folder), neither created yet."""
    steamapps = library / "steamapps"
    put(steamapps / f"appmanifest_{appid}.acf", manifest(appid, name, flags))
    return steamapps / "common" / "Game", steamapps / "compatdata" / str(appid) / "pfx"


def build(tmp_path: Path, install=(), prefix=None, **fields) -> Path:
    """A Steam root with one game; install=None leaves out the install folder, and
    prefix=None leaves out the prefix."""
    root = make_steam(tmp_path)
    folder, pfx = add_game(root, **fields)
    if install is not None:
        folder.mkdir(parents=True)
        plant(folder, install)
    if prefix is not None:
        pfx.mkdir(parents=True)
        plant(pfx, prefix)
    return root


def card_of(root: Path, appid: int = APPID) -> dict:
    found = [card for card in discover.scan(str(root))["games"] if card["appid"] == appid]
    assert len(found) == 1
    return found[0]


def game(tmp_path: Path, install=(), prefix=None, **fields) -> dict:
    return card_of(build(tmp_path, install, prefix, **fields), fields.get("appid", APPID))


def paths_of(card: dict, code: str) -> list:
    return [issue["path"] for issue in card["warnings"] if issue["code"] == code]


def named(card: dict) -> dict[str, list[str]]:
    """Every upscaler, injector and anti-cheat system on the card, with its evidence."""
    found = {item["name"]: item["evidence"] for item in card["upscalers"] + card["injectors"]}
    found.update({item["system"]: item["evidence"] for item in card["anticheat"]})
    return found


def pfx_forms(start: str, rel: str) -> set[str]:
    """C3 prefix evidence is "pfx/<relative path>". Relative to the prefix or to the walk's
    start folder is not settled by the spec, so both are accepted."""
    return {f"pfx/{start}/{rel}", f"pfx/{rel}"}


class Listing:
    """Behaves like the iterator os.scandir returns, over a prepared list of entries."""

    def __init__(self, entries: list) -> None:
        self._entries = iter(entries)

    def __iter__(self) -> "Listing":
        return self

    def __next__(self):
        return next(self._entries)

    def __enter__(self) -> "Listing":
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def close(self) -> None:
        return None


def list_in_reverse(monkeypatch: pytest.MonkeyPatch) -> None:
    """os.scandir yields names in reverse sorted order, so a walk that does not sort its
    entries itself visits them in a different order from one that does."""
    real_scandir = os.scandir

    def reversed_scandir(path="."):
        with real_scandir(path) as listing:
            return Listing(sorted(listing, key=lambda entry: entry.name, reverse=True))

    monkeypatch.setattr(os, "scandir", reversed_scandir)


def refuse_listing(monkeypatch: pytest.MonkeyPatch, folder: Path) -> list[str]:
    """os.scandir raises PermissionError for `folder` (however the path is spelled)."""
    targets = {os.fsdecode(folder), os.path.realpath(folder)}
    real_scandir = os.scandir
    refused: list[str] = []

    def fake_scandir(path="."):
        if isinstance(path, str | bytes | os.PathLike):
            text = os.path.normpath(os.fsdecode(os.fspath(path)))
            if text in targets:
                refused.append(text)
                raise PermissionError(errno.EACCES, os.strerror(errno.EACCES), text)
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", fake_scandir)
    return refused


class OtherDevice:
    """A stat result that reports another st_dev and passes every other field through."""

    def __init__(self, result: os.stat_result) -> None:
        self._result = result

    def __getattr__(self, name: str):
        return getattr(self._result, name)

    @property
    def st_dev(self) -> int:
        return self._result.st_dev + 1


class MovedEntry:
    """A DirEntry whose stat() reports another device for the moved folder and below."""

    def __init__(self, entry: os.DirEntry, moved) -> None:
        self._entry = entry
        self._moved = moved

    def __getattr__(self, name: str):
        return getattr(self._entry, name)

    def __fspath__(self) -> str:
        return self._entry.path

    def stat(self, *, follow_symlinks: bool = True):
        result = self._entry.stat(follow_symlinks=follow_symlinks)
        return OtherDevice(result) if self._moved(self._entry.path) else result


def other_device(monkeypatch: pytest.MonkeyPatch, mount: Path) -> None:
    """`mount` and everything below it look like another disk to os.stat, os.lstat,
    pathlib (which calls os.stat) and DirEntry.stat; nothing else changes."""
    tops = {os.fsdecode(mount), os.path.realpath(mount)}
    real_stat, real_lstat, real_scandir = os.stat, os.lstat, os.scandir

    def moved(path) -> bool:
        if not isinstance(path, str | bytes | os.PathLike):
            return False
        text = os.path.normpath(os.fsdecode(os.fspath(path)))
        return any(text == top or text.startswith(top + os.sep) for top in tops)

    def fake_stat(path, *args, **kwargs):
        result = real_stat(path, *args, **kwargs)
        return OtherDevice(result) if moved(path) else result

    def fake_lstat(path, *args, **kwargs):
        result = real_lstat(path, *args, **kwargs)
        return OtherDevice(result) if moved(path) else result

    def fake_scandir(path="."):
        with real_scandir(path) as listing:
            return Listing([MovedEntry(entry, moved) for entry in listing])

    monkeypatch.setattr(os, "stat", fake_stat)
    monkeypatch.setattr(os, "lstat", fake_lstat)
    monkeypatch.setattr(os, "scandir", fake_scandir)


def from_detect() -> bool:
    """True if a frame of src/deckforge/detect.py is on the current call stack."""
    frame = inspect.currentframe()
    while frame is not None:
        if os.path.realpath(frame.f_code.co_filename) == DETECT_REAL:
            return True
        frame = frame.f_back
    return False


def record(monkeypatch: pytest.MonkeyPatch) -> tuple[list, list]:
    """Record every open (builtins.open, io.open, os.open, Path.open) and every os.scandir
    call, each with whether detect.py is on the stack."""
    opens: list[tuple[object, bool]] = []
    listings: list[tuple[str, bool]] = []
    real_open, real_os_open, real_path_open = builtins.open, os.open, pathlib.Path.open
    real_scandir = os.scandir

    def fake_open(file, mode="r", *args, **kwargs):
        opens.append((file, from_detect()))
        return real_open(file, mode, *args, **kwargs)

    def fake_os_open(path, flags, *args, **kwargs):
        opens.append((path, from_detect()))
        return real_os_open(path, flags, *args, **kwargs)

    def fake_path_open(self, mode="r", *args, **kwargs):
        opens.append((self, from_detect()))
        return real_path_open(self, mode, *args, **kwargs)

    def fake_scandir(path="."):
        if isinstance(path, str | bytes | os.PathLike):
            listings.append((os.path.realpath(os.fsdecode(os.fspath(path))), from_detect()))
        return real_scandir(path)

    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(io, "open", fake_open)
    monkeypatch.setattr(os, "open", fake_os_open)
    monkeypatch.setattr(pathlib.Path, "open", fake_path_open)
    monkeypatch.setattr(os, "scandir", fake_scandir)
    return opens, listings


# ---------------------------------------------------------------------------- C1 depth

DEPTH_CASES = {
    "file-at-depth-10-is-found": (
        [f"{D9}/nvngx_dlss.dll"],
        {"dlss": [f"{D9}/nvngx_dlss.dll"]},
        False,
    ),
    "folder-at-depth-10-is-matched-by-name": (
        [f"{D9}/EasyAntiCheat/"],
        {"easyanticheat": [f"{D9}/EasyAntiCheat"]},
        False,
    ),
    "file-at-depth-11-is-skipped": ([f"{D10}/nvngx_dlss.dll"], {}, True),
    "folder-at-depth-10-holding-an-empty-folder": ([f"{D10}/d11/"], {}, True),
    "empty-folder-at-depth-10-skips-nothing": ([f"{D10}/"], {}, False),
    "files-and-empty-folders-at-depth-10": (
        [f"{D9}/nvngx_dlss.dll", f"{D9}/d10/", f"{D9}/zz/"],
        {"dlss": [f"{D9}/nvngx_dlss.dll"]},
        False,
    ),
}


@pytest.mark.parametrize(
    ("entries", "expected", "truncated"), DEPTH_CASES.values(), ids=DEPTH_CASES
)
def test_c1_install_walk_reaches_depth_10_and_truncates_only_when_something_is_skipped(
    tmp_path, entries, expected, truncated
):
    card = game(tmp_path, entries)
    assert named(card) == expected
    assert paths_of(card, "scan_truncated") == ([card["install_path"]] if truncated else [])


PREFIX_DEPTH_CASES = {
    "name-at-depth-6-is-found": ([f"{PROGRAM_FILES}/{P5}/EasyAntiCheat_EOS.exe"], True, False),
    "name-at-depth-7-is-skipped": ([f"{PROGRAM_FILES}/{P5}/p6/EasyAntiCheat_EOS.exe"], False, True),
    "empty-folder-at-depth-6-skips-nothing": ([f"{PROGRAM_FILES}/{P5}/p6/"], False, False),
}


@pytest.mark.parametrize(
    ("entries", "found", "truncated"), PREFIX_DEPTH_CASES.values(), ids=PREFIX_DEPTH_CASES
)
def test_c1_prefix_walk_reaches_depth_6_and_truncates_only_when_something_is_skipped(
    tmp_path, entries, found, truncated
):
    card = game(tmp_path, [], entries)
    start = str(Path(card["prefix_path"], PROGRAM_FILES))
    if found:
        [item] = card["anticheat"]
        assert item["system"] == "easyanticheat"
        [evidence] = item["evidence"]
        assert evidence in pfx_forms(PROGRAM_FILES, f"{P5}/EasyAntiCheat_EOS.exe")
    else:
        assert card["anticheat"] == []
    assert paths_of(card, "scan_truncated") == ([start] if truncated else [])


# ---------------------------------------------------------------------------- C1 cap and order


@pytest.fixture(scope="module")
def capped_steam(tmp_path_factory) -> Path:
    """An install folder with CAP + 1 entries. Breadth-first with sorted names, entry
    number CAP is b/libxess.dll and entry CAP + 1 is b/nvngx_dlss.dll:
    a, b, nvngx_dlssg.dll, then a/f00000 ... a/f19995, then b/libxess.dll, b/nvngx_dlss.dll.
    Depth-first would reach b/nvngx_dlss.dll and miss nvngx_dlssg.dll; an unsorted order
    would reach other entries. The prefix holds its own small Program Files walk."""
    base = tmp_path_factory.mktemp("cap")
    root = make_steam(base)
    install, pfx = add_game(root)
    bulk = install / "a"
    bulk.mkdir(parents=True)
    for n in range(CAP - 4):
        (bulk / f"f{n:05d}").touch()
    plant(install, ["b/libxess.dll", "b/nvngx_dlss.dll", "nvngx_dlssg.dll"])
    plant(pfx, [f"{PROGRAM_FILES}/EasyAntiCheat/"])
    return root


def test_c1_cap_keeps_the_first_20000_entries_in_sorted_breadth_first_order(
    capped_steam, monkeypatch
):
    list_in_reverse(monkeypatch)  # the walk must sort; it cannot rely on listing order
    card = card_of(capped_steam)
    assert card["upscalers"] == [
        {"name": "dlss_fg", "evidence": ["nvngx_dlssg.dll"]},
        {"name": "xess", "evidence": ["b/libxess.dll"]},
    ]


def test_c1_cap_hit_adds_one_scan_truncated_warning_for_the_install_folder(
    capped_steam, monkeypatch
):
    list_in_reverse(monkeypatch)
    card = card_of(capped_steam)
    assert paths_of(card, "scan_truncated") == [card["install_path"]]


def test_c1_cap_is_counted_per_start_folder(capped_steam, monkeypatch):
    list_in_reverse(monkeypatch)
    card = card_of(capped_steam)
    [item] = card["anticheat"]
    assert item["system"] == "easyanticheat"
    assert item["evidence"][0] in pfx_forms(PROGRAM_FILES, "EasyAntiCheat")


# ---------------------------------------------------------------------------- C1 links


def test_c1_a_link_to_a_folder_is_never_entered(tmp_path):
    outside = tmp_path / "outside"
    plant(outside, ["EasyAntiCheat/", "nvngx_dlss.dll", "deep/BattlEye/"])
    root = make_steam(tmp_path)
    install, _ = add_game(root)
    install.mkdir(parents=True)
    (install / "Plugins").symlink_to(outside, target_is_directory=True)
    (install / "loop").symlink_to(install, target_is_directory=True)
    card = card_of(root)
    assert named(card) == {}
    assert paths_of(card, "scan_truncated") == []
    assert paths_of(card, "unreadable") == []


def test_c1_a_link_is_matched_by_its_name(tmp_path):
    outside = tmp_path / "outside"
    plant(outside, ["empty/", "real.dll"])
    root = make_steam(tmp_path)
    install, _ = add_game(root)
    (install / "bin").mkdir(parents=True)
    (install / "EasyAntiCheat").symlink_to(outside / "empty", target_is_directory=True)
    (install / "bin" / "nvngx_dlssg.dll").symlink_to(outside / "real.dll")
    (install / "BEService_x64.exe").symlink_to(tmp_path / "no_such_file.exe")  # broken
    card = card_of(root)
    assert named(card) == {
        "battleye": ["BEService_x64.exe"],
        "dlss_fg": ["bin/nvngx_dlssg.dll"],
        "easyanticheat": ["EasyAntiCheat"],
    }


def test_c1_an_install_folder_that_is_a_link_is_followed(tmp_path):
    real = tmp_path / "elsewhere" / "Game"
    plant(real, ["re_chunk_000.pak", "natives/x64/libxess.dll"])
    root = make_steam(tmp_path)
    install, _ = add_game(root)
    install.parent.mkdir(parents=True)
    install.symlink_to(real, target_is_directory=True)
    card = card_of(root)
    assert (card["engine"], card["engine_evidence"]) == ("re_engine", ["re_chunk_000.pak"])
    assert named(card) == {"xess": ["natives/x64/libxess.dll"]}


# ---------------------------------------------------------------------------- C1 disks


def test_c1_a_folder_on_another_device_is_not_entered(tmp_path, monkeypatch):
    root = make_steam(tmp_path)
    install, _ = add_game(root)
    plant(install, ["Mounted/EasyAntiCheat/", "Mounted/nvngx_dlss.dll", "Same/nvngx_dlssg.dll"])
    control = card_of(root)
    assert named(control) == {
        "dlss": ["Mounted/nvngx_dlss.dll"],
        "dlss_fg": ["Same/nvngx_dlssg.dll"],
        "easyanticheat": ["Mounted/EasyAntiCheat"],
    }
    other_device(monkeypatch, install / "Mounted")
    card = card_of(root)
    assert named(card) == {"dlss_fg": ["Same/nvngx_dlssg.dll"]}
    assert paths_of(card, "scan_truncated") == []
    assert paths_of(card, "unreadable") == []


# ---------------------------------------------------------------------------- C1 unreadable

UNREADABLE_CASES = {
    "a-subfolder": (
        "Locked",
        ["Locked/EasyAntiCheat/", "Open/nvngx_dlss.dll", "zzz/libxess.dll"],
        {"dlss": ["Open/nvngx_dlss.dll"], "xess": ["zzz/libxess.dll"]},
    ),
    "a-deeper-folder": (
        "Open/Locked",
        ["Open/Locked/EasyAntiCheat/", "Open/nvngx_dlss.dll", "Open/zzz/libxess.dll"],
        {"dlss": ["Open/nvngx_dlss.dll"], "xess": ["Open/zzz/libxess.dll"]},
    ),
    "the-install-folder": ("", ["EasyAntiCheat/", "nvngx_dlss.dll"], {}),
}


@pytest.mark.parametrize(
    ("locked", "entries", "expected"), UNREADABLE_CASES.values(), ids=UNREADABLE_CASES
)
def test_c1_an_unreadable_folder_is_reported_and_the_walk_continues(
    tmp_path, monkeypatch, locked, entries, expected
):
    root = build(tmp_path, entries)
    assert "easyanticheat" in named(card_of(root))  # control: readable, the marker is seen
    install = root / "steamapps" / "common" / "Game"
    refused = refuse_listing(monkeypatch, install / locked)
    card = card_of(root)
    assert refused, "the walk never tried to list the folder"
    assert paths_of(card, "unreadable") == [str(Path(card["install_path"], locked))]
    assert named(card) == expected


# ---------------------------------------------------------------------------- C1 names


def test_c1_non_utf8_names_use_backslashreplace_and_add_a_warning(tmp_path):
    cafe = os.fsdecode(b"Caf\xe9")  # Latin-1 bytes, not valid UTF-8
    marker = os.fsdecode(b"EasyAntiCheat\xff")
    card = game(tmp_path, [f"{cafe}/nvngx_dlss.dll", f"{marker}/"])
    assert named(card) == {
        "dlss": ["Caf\\xe9/nvngx_dlss.dll"],
        "easyanticheat": ["EasyAntiCheat\\xff"],
    }
    assert paths_of(card, "non_utf8_filename") != []
    for evidence in named(card).values():
        for text in evidence:
            text.encode("utf-8")  # strict: no lone surrogates reach the evidence


def test_c1_valid_utf8_names_are_kept_without_a_warning(tmp_path):
    card = game(tmp_path, ["大神/Ōkami/nvngx_dlss.dll"])
    assert named(card) == {"dlss": ["大神/Ōkami/nvngx_dlss.dll"]}
    assert paths_of(card, "non_utf8_filename") == []


def test_c1_evidence_paths_are_relative_slash_separated_and_keep_disk_case(tmp_path):
    rel = "Engine/Plugins/Runtime/Nvidia/DLSS/Binaries/ThirdParty/Win64/NvNGX_DLSS.dll"
    card = game(tmp_path, [rel])
    assert card["upscalers"] == [{"name": "dlss", "evidence": [rel]}]


# ---------------------------------------------------------------------------- C9 source


def detect_module():
    return importlib.import_module("deckforge.detect")


def source_tree() -> ast.Module:
    return ast.parse(DETECT_SOURCE.read_text(encoding="utf-8"), filename=str(DETECT_SOURCE))


def dotted(node: ast.AST) -> str | None:
    """ "a.b.c" for a chain of names and attributes, else None."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return ".".join(reversed(parts))


def calls(tree: ast.Module) -> list[ast.Call]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.Call)]


def test_c9_curated_anticheat_is_the_spec_constant():
    assert detect_module().CURATED_ANTICHEAT == {2183900: "easyanticheat", 553850: "gameguard"}


def test_c9_the_checked_source_is_the_module_under_test():
    assert Path(detect_module().__file__).resolve() == DETECT_SOURCE.resolve()


def test_c9_imports_only_the_allowlist():
    offenders = []
    for node in ast.walk(source_tree()):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level == 1:  # from . import x, inside the deckforge package
                continue
            names = ["." * node.level + (node.module or "")]
        else:
            continue
        for name in names:
            top = name.split(".")[0]
            if top not in ALLOWED_IMPORTS and top != "deckforge":
                offenders.append(f"line {node.lineno}: {name}")
    assert offenders == []


def test_c9_no_banned_attribute_calls():
    tree = source_tree()
    offenders = []
    for call in calls(tree):
        func = call.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr in BANNED_CALLS
            and dotted(func) not in ALLOWED_WRITES
        ):
            offenders.append(f"line {call.lineno}: .{func.attr}()")
        if (
            isinstance(func, ast.Name)
            and func.id == "getattr"
            and len(call.args) > 1
            and isinstance(call.args[1], ast.Constant)
            and call.args[1].value in BANNED_CALLS | OPENING
        ):
            offenders.append(f"line {call.lineno}: getattr(..., {call.args[1].value!r})")
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            offenders += [
                f"line {node.lineno}: import of {alias.name}"
                for alias in node.names
                if alias.name in BANNED_CALLS
            ]
    assert offenders == []


def test_c9_folders_are_listed_only_with_os_scandir():
    offenders = []
    for node in ast.walk(source_tree()):
        if isinstance(node, ast.Attribute) and node.attr in OTHER_LISTING:
            offenders.append(f"line {node.lineno}: .{node.attr}")
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "scandir"
            and dotted(node) != "os.scandir"
        ):
            offenders.append(f"line {node.lineno}: {dotted(node)}")
        if isinstance(node, ast.Name) and node.id == "scandir":
            offenders.append(f"line {node.lineno}: bare scandir")
        if isinstance(node, ast.ImportFrom):
            offenders += [
                f"line {node.lineno}: import of {alias.name}"
                for alias in node.names
                if alias.name == "scandir" or alias.name in OTHER_LISTING
            ]
    assert offenders == []


def test_c9_no_process_or_other_file_changing_calls():
    tree = source_tree()
    offenders = []
    for call in calls(tree):
        if isinstance(call.func, ast.Attribute) and call.func.attr in PROCESS_OR_CHANGE:
            offenders.append(f"line {call.lineno}: .{call.func.attr}()")
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in DYNAMIC_CODE:
            offenders.append(f"line {node.lineno}: {node.id}")
        if isinstance(node, ast.ImportFrom):
            offenders += [
                f"line {node.lineno}: import of {alias.name}"
                for alias in node.names
                if alias.name in PROCESS_OR_CHANGE
            ]
    assert offenders == []


def test_c9_source_opens_no_files():
    offenders = []
    for node in ast.walk(source_tree()):
        if isinstance(node, ast.Name) and node.id == "open":
            offenders.append(f"line {node.lineno}: open")
        if isinstance(node, ast.Attribute) and node.attr in OPENING:
            offenders.append(f"line {node.lineno}: .{node.attr}")
        if isinstance(node, ast.ImportFrom):
            offenders += [
                f"line {node.lineno}: import of {alias.name}"
                for alias in node.names
                if alias.name in OPENING
            ]
    assert offenders == []


# ---------------------------------------------------------------------------- C9 run time


def every_kind_tree(base: Path) -> Path:
    """A game matching all three engines, with every settings class, injectors, upscalers
    and a prefix holding the C3 and C6 start folders."""
    root = make_steam(base)
    install, pfx = add_game(root)
    plant(
        install,
        [
            "re_chunk_000.pak",
            "config.ini",
            "UnityPlayer.dll",
            "Game_Data/boot.config",
            UNREAL_EXE,
            "OptiScaler.ini",
            "reframework/plugins/",
            "dinput8.dll",
            "Game/Plugins/DLSS/nvngx_dlss.dll",
        ],
    )
    plant(
        pfx,
        [
            "user.reg",
            f"{LOCAL}/G/Saved/Config/Windows/Engine.ini",
            f"{PROGRAM_FILES}/Common Files/readme.txt",
        ],
    )
    return root


def test_c9_detect_opens_no_file_and_lists_folders_with_os_scandir(tmp_path, monkeypatch):
    root = every_kind_tree(tmp_path)
    with monkeypatch.context() as patch:
        opens, listings = record(patch)
        card = card_of(root)
    assert opens, "the recorder saw no open at all, so it cannot vouch for anything"
    assert [file for file, in_detect in opens if in_detect] == []
    walked = {path for path, in_detect in listings if in_detect}
    assert os.path.realpath(Path(card["install_path"], "Game_Data")) in walked
    assert os.path.realpath(Path(card["prefix_path"], LOCAL, "G", "Saved")) in walked
    assert len(card["settings_files"]) == 4


def links_tree(base: Path) -> Path:
    outside = base / "outside"
    plant(outside, ["EasyAntiCheat/x.txt", "real.dll", "games/G/Saved/Config/Engine.ini"])
    root = make_steam(base)
    install, pfx = add_game(root)
    plant(install, [UNREAL_EXE, "bin/"])
    (install / "Plugins").symlink_to(outside, target_is_directory=True)
    (install / "loop").symlink_to(install, target_is_directory=True)
    (install / "EasyAntiCheat").symlink_to(outside / "EasyAntiCheat", target_is_directory=True)
    (install / "bin" / "nvngx_dlss.dll").symlink_to(outside / "real.dll")
    (install / "BEService.exe").symlink_to(base / "no_such_file.exe")
    plant(pfx, ["user.reg", "dosdevices/", f"{LOCAL}/G/Saved/Config/Engine.ini"])
    (pfx / "dosdevices" / "c:").symlink_to("../drive_c", target_is_directory=True)
    (pfx / "dosdevices" / "z:").symlink_to(outside, target_is_directory=True)
    docs = pfx / "drive_c" / "users" / "steamuser" / "Documents"
    docs.mkdir(parents=True)
    (docs / "My Games").symlink_to(outside / "games", target_is_directory=True)
    return root


def non_utf8_tree(base: Path) -> Path:
    root = make_steam(base)
    install, pfx = add_game(root)
    odd = os.fsdecode(b"Caf\xe9")
    plant(install, [f"{odd}/nvngx_dlss.dll", f"{odd}/{odd}/", UNREAL_EXE])
    plant(pfx, [f"{PROGRAM_FILES}/{odd}/BEClient.dll", f"{LOCAL}/{odd}/Saved/Config/Engine.ini"])
    return root


def snapshot(top: Path) -> dict[str, tuple]:
    """Every entry under `top` (and `top` itself), read with lstat; links are not followed."""
    state: dict[str, tuple] = {}
    pending = [top]
    while pending:
        path = pending.pop()
        info = path.lstat()
        entry: tuple = (
            stat.S_IFMT(info.st_mode),
            info.st_mode,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
            info.st_ino,
            info.st_nlink,
        )
        if stat.S_ISLNK(info.st_mode):
            entry += (str(path.readlink()),)
        elif stat.S_ISREG(info.st_mode):
            entry += (path.read_bytes(),)
        elif stat.S_ISDIR(info.st_mode):
            names = sorted(child.name for child in path.iterdir())
            entry += (tuple(names),)
            pending.extend(path / name for name in names)
        state[str(path.relative_to(top))] = entry
    return state


TREES = {"every-kind": every_kind_tree, "links": links_tree, "non-utf8": non_utf8_tree}


@pytest.mark.parametrize("shape", sorted(TREES))
def test_c9_scans_change_nothing_on_disk(tmp_path, shape):
    data = tmp_path / "data"
    root = TREES[shape](data)
    before = snapshot(data)
    for _ in range(2):
        [card] = discover.scan(str(root))["games"]
        assert set(card) >= B2_FIELDS  # the B2 walks really ran
    assert snapshot(data) == before
