# Contracts for PR B2 of docs/specs/discover.md after the verifier's fail-open findings
# (spec commit 33a1b5f): the B4 prefix_path row, C1 "Not entered (safety)", C6 (only the
# engines that matched are searched; only regular, non-link settings files are listed) and
# C7 (installed; a usable prefix; no not_entered). Written against the amended spec only.
# Everything is observed through discover.scan, the public surface.
#
# prefix_path, criterion B4 (as amended)
#   Post: checking the game's own prefix fails with an OS error other than "absent" (EIO,
#         EACCES, ELOOP): prefix_path is None and the card has one prefix_unreadable
#         warning, path = the own prefix path. No fallback, even when the root library has a
#         clean prefix for that appid.
#   Post: the own prefix is absent and checking the root library's prefix fails with such an
#         error: prefix_path is None and one prefix_unreadable warning, path = the root
#         library's prefix path. No prefix_in_other_library warning, since no prefix is used.
#   Post: no prefix anywhere (the game was never launched): prefix_path is None, no warning.
#
# not_entered, criterion C1
#   Pre:  the install walk, or a C3 walk from <prefix>/drive_c/Program Files or
#         <prefix>/drive_c/Program Files (x86).
#   Post: an entry found in the walk that is a link to a folder (wherever the folder is, even
#         inside the same walk, and through a chain of links), or a folder whose st_dev
#         differs from the start folder's, is not entered and adds one not_entered card
#         warning, path = os.path.join(start folder path, the entry's relative path).
#   Post: broken links and links to files add nothing. A start folder that is itself a link
#         is followed: it adds nothing, what lies behind it counts, and the depth limit still
#         bounds the walk (scan_truncated, path = the start folder, when something is cut off).
#   Post: the C6 settings walks skip links to folders, other-device folders, folders named
#         dosdevices and start folders reached through Proton's My Documents link silently:
#         no not_entered.
#
# settings_files, criterion C6 (as amended)
#   Post: only regular files that are not links are listed: a dangling link, a link to a
#         file (inside or outside the prefix) or a FIFO with a settings name is left out; a
#         regular settings file next to it is still listed.
#   Post: a link that points at another listed settings file does not displace it in the
#         real-path de-duplication: the regular file's own path is listed.
#   Post: Proton's My Documents -> Documents link gives one entry, under the Documents path
#         (the first path in sorted order).
#   Post: a game matching two engines gets the searches of those two only: Unreal + Unity
#         never lists RE Engine's config.ini, and config.ini alone is not an RE signature, so
#         the engine is "ambiguous" with Unreal and Unity evidence only.
#
# tier_i_eligible, criterion C7 (as amended)
#   Post: False whenever any one of these holds, on a fixture that is otherwise eligible:
#         installed is False (StateFlags "1026" or "16" with the install folder present);
#         prefix_path is None (unreadable or absent); a prefix_unreadable warning; a
#         not_entered warning; a truncated walk; kind == "tool" (walked all the same).
#   Inv:  fails closed: a scan that could not look somewhere never says eligible, even when
#         the only anti-cheat on disk sits in the place it could not look.
#
# Error injection: the container runs as root, so chmod cannot make EIO or EACCES. They are
# injected for one folder and everything below it by patching os.stat, os.lstat, os.scandir
# and pathlib.Path.stat (and the DirEntry a listing returns for it). The link loop is a real
# self-link inside tmp_path. Other devices are faked the way test_detect_walks.py does.
#
# Round trip: B2 has no write or restore path, so there is nothing to apply and restore. The
# read-only property that replaces it (two scans leave the tree byte- and lstat-identical) is
# in test_detect_walks.py.

import errno
import os
import pathlib
from pathlib import Path

import pytest

from deckforge import discover

APPID = 1086940
EAC_RUNTIME_APPID = 1826330
P5 = "p1/p2/p3/p4/p5"  # five folders: a name inside has depth 6
DEEP = "/".join(f"p{n}" for n in range(1, 41))  # 40 folders, far past the prefix limit of 6
PROGRAM_FILES = "drive_c/Program Files"
PROGRAM_FILES_X86 = "drive_c/Program Files (x86)"
STEAMUSER = "drive_c/users/steamuser"
LOCAL = f"{STEAMUSER}/AppData/Local"
DOCS = f"{STEAMUSER}/Documents/My Games"
UNREAL_EXE = "Game/Binaries/Win64/Game-Win64-Shipping.exe"
ELIGIBLE_INSTALL = [UNREAL_EXE, "OptiScaler.ini", "Game/Plugins/nvngx_dlss.dll"]
ELIGIBLE_PREFIX = [
    "user.reg",
    f"{LOCAL}/G/Saved/Config/Engine.ini",
    f"{PROGRAM_FILES}/Common Files/",
    f"{PROGRAM_FILES_X86}/Steam/",
]


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


def eligible(tmp_path: Path) -> Path:
    """A Steam root holding one game that meets every C7 condition."""
    return build(tmp_path, ELIGIBLE_INSTALL, ELIGIBLE_PREFIX)


def deck(tmp_path: Path, where: str, *, stale: bool) -> tuple[Path, Path]:
    """An eligible game in the root library or on an SD card, with its own prefix. With
    stale=True an SD-card game also has a clean prefix for its appid in the root library,
    the one a fallback would pick. Returns (steam root, the game's own prefix)."""
    sd = tmp_path / "sd"
    root = make_steam(tmp_path, sd)
    install, own = add_game(root if where == "root" else sd)
    install.mkdir(parents=True)
    plant(install, ELIGIBLE_INSTALL)
    own.mkdir(parents=True)
    plant(own, ELIGIBLE_PREFIX)
    if where == "sd" and stale:
        plant(prefix_of(root), ELIGIBLE_PREFIX)
    return root, own


def install_of(root: Path) -> Path:
    return root / "steamapps" / "common" / "Game"


def prefix_of(root: Path, appid: int = APPID) -> Path:
    return root / "steamapps" / "compatdata" / str(appid) / "pfx"


def card_of(root: Path, appid: int = APPID) -> dict:
    found = [card for card in discover.scan(str(root))["games"] if card["appid"] == appid]
    assert len(found) == 1
    return found[0]


def game(tmp_path: Path, install=(), prefix=None, **fields) -> dict:
    return card_of(build(tmp_path, install, prefix, **fields), fields.get("appid", APPID))


def pairs(card: dict) -> list[tuple[str, str | None]]:
    return [(issue["code"], issue["path"]) for issue in card["warnings"]]


def paths_of(card: dict, code: str) -> list:
    return [issue["path"] for issue in card["warnings"] if issue["code"] == code]


def ac(system: str, *evidence: str) -> dict:
    return {"system": system, "evidence": list(evidence)}


def setting(base: str, rel: str, cls: str, kind: str) -> dict:
    return {"path": str(Path(base, rel)), "class": cls, "kind": kind}


def by_path(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda entry: entry["path"])


def link_to_folder(link: Path, target: Path | str) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(target, target_is_directory=True)


def make_entry(path: Path, shape: str, outside: Path) -> None:
    """Create `path` as a regular file, a dangling link, a link to a regular file at
    `outside`, or a FIFO."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if shape == "regular-file":
        path.write_bytes(b"")
    elif shape == "dangling-link":
        path.symlink_to(outside.parent / "no_such_file")
    elif shape == "link-to-a-file":
        put(outside)
        path.symlink_to(outside)
    elif shape == "fifo":
        os.mkfifo(path)
    else:
        raise AssertionError(f"unknown shape {shape}")


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


class FailingEntry:
    """A DirEntry whose stat(), is_dir() and is_file() raise the given OSError."""

    def __init__(self, entry: os.DirEntry, error: OSError) -> None:
        self._entry = entry
        self._error = error

    def __getattr__(self, name: str):
        return getattr(self._entry, name)

    def __fspath__(self) -> str:
        return self._entry.path

    def stat(self, *, follow_symlinks: bool = True):
        raise self._error

    def is_dir(self, *, follow_symlinks: bool = True) -> bool:
        raise self._error

    def is_file(self, *, follow_symlinks: bool = True) -> bool:
        raise self._error


def fail_below(monkeypatch: pytest.MonkeyPatch, target: Path, code: int) -> None:
    """os.stat, os.lstat, os.scandir and pathlib.Path.stat raise OSError(code) for `target`
    and every path below it (spelled as given or through its real path), and so does a
    DirEntry for one of them; every other path behaves normally."""
    tops = {os.path.normpath(target), os.path.realpath(target)}
    real_stat, real_lstat, real_scandir = os.stat, os.lstat, os.scandir
    real_path_stat = pathlib.Path.stat

    def blocked(path) -> bool:
        if not isinstance(path, str | bytes | os.PathLike):
            return False
        text = os.path.normpath(os.fsdecode(os.fspath(path)))
        return any(text == top or text.startswith(top + os.sep) for top in tops)

    def error(path) -> OSError:
        return OSError(code, os.strerror(code), os.fsdecode(os.fspath(path)))

    def fake_stat(path, *args, **kwargs):
        if blocked(path):
            raise error(path)
        return real_stat(path, *args, **kwargs)

    def fake_lstat(path, *args, **kwargs):
        if blocked(path):
            raise error(path)
        return real_lstat(path, *args, **kwargs)

    def fake_scandir(path="."):
        if blocked(path):
            raise error(path)
        with real_scandir(path) as listing:
            return Listing(
                [FailingEntry(e, error(e.path)) if blocked(e.path) else e for e in listing]
            )

    def fake_path_stat(self, *, follow_symlinks=True):
        if blocked(self):
            raise error(self)
        return real_path_stat(self, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(os, "stat", fake_stat)
    monkeypatch.setattr(os, "lstat", fake_lstat)
    monkeypatch.setattr(os, "scandir", fake_scandir)
    monkeypatch.setattr(pathlib.Path, "stat", fake_path_stat)


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


# ---------------------------------------------------------------------------- 1. unreadable prefix

PREFIX_FAILURES = ["eio", "eacces", "eloop"]
ERRNO = {"eio": errno.EIO, "eacces": errno.EACCES}


def break_prefix(monkeypatch: pytest.MonkeyPatch, pfx: Path, failure: str) -> None:
    """EIO or EACCES is injected for pfx and below; ELOOP is a real self-link put in its
    place (the folder is moved aside, nothing is deleted)."""
    if failure == "eloop":
        pfx.rename(pfx.with_name("pfx_moved_aside"))
        pfx.symlink_to(pfx)
    else:
        fail_below(monkeypatch, pfx, ERRNO[failure])


@pytest.mark.parametrize("where", ["root", "sd"])
@pytest.mark.parametrize("failure", PREFIX_FAILURES)
def test_c7_an_own_prefix_that_cannot_be_checked_makes_the_card_ineligible(
    tmp_path, monkeypatch, failure, where
):
    root, own = deck(tmp_path, where, stale=True)
    assert card_of(root)["tier_i_eligible"] is True  # control: the same tree, readable
    break_prefix(monkeypatch, own, failure)
    card = card_of(root)
    assert card["prefix_path"] is None
    assert pairs(card) == [("prefix_unreadable", str(own))]
    assert card["tier_i_eligible"] is False


@pytest.mark.parametrize("failure", PREFIX_FAILURES)
def test_b4_c7_a_root_library_prefix_that_cannot_be_checked_is_unreadable_and_ineligible(
    tmp_path, monkeypatch, failure
):
    sd = tmp_path / "sd"
    root = make_steam(tmp_path, sd)
    install, _ = add_game(sd)
    plant(install, ELIGIBLE_INSTALL)
    shared = prefix_of(root)
    plant(shared, [*ELIGIBLE_PREFIX, f"{PROGRAM_FILES_X86}/EasyAntiCheat/"])
    control = card_of(root)  # readable: the fallback is used and its anti-cheat is seen
    assert control["prefix_path"] == str(shared)
    assert ("prefix_in_other_library", str(shared)) in pairs(control)
    assert control["anticheat"] == [ac("easyanticheat", f"pfx/{PROGRAM_FILES_X86}/EasyAntiCheat")]
    break_prefix(monkeypatch, shared, failure)
    card = card_of(root)
    assert card["prefix_path"] is None
    assert pairs(card) == [("prefix_unreadable", str(shared))]
    assert card["anticheat"] == []  # the prefix walks could not run
    assert card["tier_i_eligible"] is False


# ---------------------------------------------------------------------------- 2. no prefix


@pytest.mark.parametrize("where", ["root", "sd"])
def test_c7_a_game_never_launched_has_no_prefix_and_is_ineligible(tmp_path, where):
    root, own = deck(tmp_path, where, stale=False)
    assert card_of(root)["tier_i_eligible"] is True  # control: the same game, launched
    compatdata_entry = own.parent
    compatdata_entry.rename(compatdata_entry.with_name(f"{APPID}_moved_aside"))
    card = card_of(root)
    assert card["prefix_path"] is None
    assert pairs(card) == []
    assert card["tier_i_eligible"] is False


# ---------------------------------------------------------------------------- 3. not installed


@pytest.mark.parametrize("flags", ["1026", "16"])
def test_c7_a_game_not_fully_installed_is_ineligible(tmp_path, flags):
    control = game(tmp_path / "control", ELIGIBLE_INSTALL, ELIGIBLE_PREFIX, flags="4")
    assert control["tier_i_eligible"] is True
    card = game(tmp_path / "case", ELIGIBLE_INSTALL, ELIGIBLE_PREFIX, flags=flags)
    assert Path(card["install_path"]).is_dir()
    assert paths_of(card, "install_folder_missing") == []
    assert card["installed"] is False
    assert card["tier_i_eligible"] is False


# ---------------------------------------------------------------------------- 4. not_entered


def install_link_target(tmp_path: Path, install: Path, case: str) -> Path:
    hidden = tmp_path / "hidden"
    plant(hidden, ["EasyAntiCheat/", "BattlEye/BEClient_x64.dll"])
    if case == "to-a-folder-outside":
        return hidden
    if case == "to-the-install-folder":
        return install
    chain = tmp_path / "chain"
    link_to_folder(chain, hidden)
    return chain  # a link to a link to the folder holding anti-cheat


INSTALL_LINKS = {
    "to-a-folder-outside": "Plugins",
    "to-the-install-folder": "Game/Binaries/loop",
    "through-a-chain-of-links": "Engine/Content/Chain",
}


@pytest.mark.parametrize(("case", "rel"), INSTALL_LINKS.items(), ids=INSTALL_LINKS)
def test_c1_c7_a_link_to_a_folder_in_the_install_walk_adds_not_entered(tmp_path, case, rel):
    root = eligible(tmp_path)
    assert card_of(root)["tier_i_eligible"] is True  # control: no link yet
    install = install_of(root)
    link_to_folder(install / rel, install_link_target(tmp_path, install, case))
    card = card_of(root)
    assert pairs(card) == [("not_entered", str(Path(card["install_path"], rel)))]
    assert card["anticheat"] == []
    assert card["tier_i_eligible"] is False


@pytest.mark.parametrize("rel", ["Mounted", "Engine/Plugins/Mounted"])
def test_c1_c7_a_folder_on_another_device_in_the_install_walk_adds_not_entered(
    tmp_path, monkeypatch, rel
):
    root = build(tmp_path, [*ELIGIBLE_INSTALL, f"{rel}/EasyAntiCheat/"], ELIGIBLE_PREFIX)
    control = card_of(root)  # same device: the anti-cheat inside is seen
    assert control["anticheat"] == [ac("easyanticheat", f"{rel}/EasyAntiCheat")]
    other_device(monkeypatch, install_of(root) / rel)
    card = card_of(root)
    assert pairs(card) == [("not_entered", str(Path(card["install_path"], rel)))]
    assert card["anticheat"] == []
    assert card["tier_i_eligible"] is False


PROGRAM_FILES_CASES = ["link-to-a-folder-outside", "link-to-a-folder-inside-the-walk", "device"]
STARTS = {"program-files": PROGRAM_FILES, "program-files-x86": PROGRAM_FILES_X86}


@pytest.mark.parametrize("start", STARTS.values(), ids=STARTS)
@pytest.mark.parametrize("case", PROGRAM_FILES_CASES)
def test_c1_c7_a_link_or_other_device_in_a_program_files_walk_adds_not_entered(
    tmp_path, monkeypatch, case, start
):
    root = build(tmp_path, ELIGIBLE_INSTALL, [*ELIGIBLE_PREFIX, f"{start}/Shared/"])
    assert card_of(root)["tier_i_eligible"] is True  # control
    entry = prefix_of(root) / start / "Game" / "Plugins"
    if case == "link-to-a-folder-outside":
        hidden = tmp_path / "hidden"
        plant(hidden, ["EasyAntiCheat/", "BattlEye/"])
        link_to_folder(entry, hidden)
    elif case == "link-to-a-folder-inside-the-walk":
        link_to_folder(entry, Path("..", "..", "Shared"))
    else:
        plant(entry, ["EasyAntiCheat/"])
        control = card_of(root)  # same device: the anti-cheat inside is seen
        assert control["anticheat"] == [
            ac("easyanticheat", f"pfx/{start}/Game/Plugins/EasyAntiCheat")
        ]
        other_device(monkeypatch, entry)
    card = card_of(root)
    assert pairs(card) == [("not_entered", str(Path(card["prefix_path"], start, "Game/Plugins")))]
    assert card["anticheat"] == []
    assert card["tier_i_eligible"] is False


HARMLESS_LINK_PLACES = {
    "install": ("install", "Game/Old"),
    "program-files": ("prefix", f"{PROGRAM_FILES}/Common Files/Old"),
    "program-files-x86": ("prefix", f"{PROGRAM_FILES_X86}/Steam/Old"),
}


@pytest.mark.parametrize("shape", ["dangling-link", "link-to-a-file"])
@pytest.mark.parametrize(("base", "rel"), HARMLESS_LINK_PLACES.values(), ids=HARMLESS_LINK_PLACES)
def test_c1_c7_broken_links_and_links_to_files_add_no_not_entered(tmp_path, base, rel, shape):
    root = eligible(tmp_path)
    folder = {"install": install_of(root), "prefix": prefix_of(root)}[base]
    make_entry(folder / rel, shape, tmp_path / "outside" / "notes.txt")
    card = card_of(root)
    assert pairs(card) == []
    assert card["tier_i_eligible"] is True


@pytest.mark.parametrize("target", ["inside-the-prefix", "outside-the-prefix"])
@pytest.mark.parametrize("start", STARTS.values(), ids=STARTS)
def test_c1_a_program_files_start_folder_that_is_a_link_is_followed(tmp_path, start, target):
    kept = [entry for entry in ELIGIBLE_PREFIX if not entry.startswith(f"{start}/")]
    root = build(tmp_path, ELIGIBLE_INSTALL, kept)
    pfx = prefix_of(root)
    real = pfx / "drive_c" / "pf_real" if target == "inside-the-prefix" else tmp_path / "pf_real"
    plant(real, ["Common Files/", "EasyAntiCheat/"])
    link_to_folder(pfx / start, real)
    card = card_of(root)
    assert paths_of(card, "not_entered") == []
    assert paths_of(card, "scan_truncated") == []
    assert card["anticheat"] == [ac("easyanticheat", f"pfx/{start}/EasyAntiCheat")]
    assert card["tier_i_eligible"] is False


def test_c1_c7_links_and_mounts_skipped_by_the_settings_walks_add_no_not_entered(
    tmp_path, monkeypatch
):
    docs_ini = f"{DOCS}/H/Saved/Config/GameUserSettings.ini"
    root = build(
        tmp_path,
        ELIGIBLE_INSTALL,
        [
            *ELIGIBLE_PREFIX,
            docs_ini,
            "dosdevices/",
            f"{LOCAL}/dosdevices/G/Saved/Config/Engine.ini",
            f"{LOCAL}/Mounted/G/Saved/Config/Engine.ini",
        ],
    )
    pfx = prefix_of(root)
    zroot = tmp_path / "zroot"
    plant(zroot, ["EasyAntiCheat/", "G/Saved/Config/Engine.ini"])
    link_to_folder(pfx / "dosdevices" / "c:", Path("..", "drive_c"))
    link_to_folder(pfx / "dosdevices" / "z:", zroot)
    link_to_folder(pfx / STEAMUSER / "My Documents", Path("Documents"))
    link_to_folder(pfx / LOCAL / "ZDrive", pfx / "dosdevices" / "z:")
    other_device(monkeypatch, pfx / LOCAL / "Mounted")
    card = card_of(root)
    assert pairs(card) == []
    assert card["settings_files"] == by_path(
        [
            setting(card["prefix_path"], f"{LOCAL}/G/Saved/Config/Engine.ini", "P", "ini"),
            setting(card["prefix_path"], docs_ini, "P", "ini"),
        ]
    )
    assert card["tier_i_eligible"] is True


# ---------------------------------------------------------------------------- 5. regular files only

SHAPES = {"regular-file": True, "dangling-link": False, "link-to-a-file": False, "fifo": False}


@pytest.mark.parametrize(("shape", "listed"), SHAPES.items(), ids=SHAPES)
def test_c6_re_engine_config_ini_is_listed_only_as_a_regular_file(tmp_path, shape, listed):
    root = build(tmp_path, ["re_chunk_000.pak"], ELIGIBLE_PREFIX)
    make_entry(install_of(root) / "config.ini", shape, tmp_path / "outside" / "config.ini")
    card = card_of(root)
    assert card["engine"] == "re_engine"
    expected = [setting(card["install_path"], "config.ini", "I", "ini")] if listed else []
    assert card["settings_files"] == expected


@pytest.mark.parametrize("target", ["inside-the-prefix", "outside-the-prefix"])
def test_c6_an_engine_ini_link_under_saved_config_is_not_listed(tmp_path, target):
    kept = f"{LOCAL}/A/Saved/Config/Windows/GameUserSettings.ini"
    other = f"{LOCAL}/B/Saved/Config/Windows/Engine.ini"  # a regular file, listed
    root = build(tmp_path, [UNREAL_EXE], [kept, other])
    pfx = prefix_of(root)
    outside = put(tmp_path / "outside" / "Engine.ini")
    (pfx / LOCAL / "A/Saved/Config/Windows/Engine.ini").symlink_to(
        pfx / other if target == "inside-the-prefix" else outside
    )
    card = card_of(root)
    assert card["settings_files"] == by_path(
        [
            setting(card["prefix_path"], kept, "P", "ini"),
            setting(card["prefix_path"], other, "P", "ini"),
        ]
    )


def test_c6_a_fifo_named_gameusersettings_ini_is_not_listed(tmp_path):
    kept = f"{LOCAL}/G/Saved/Config/Windows/Engine.ini"
    root = build(tmp_path, [UNREAL_EXE], [kept])
    os.mkfifo(prefix_of(root) / LOCAL / "G/Saved/Config/Windows/GameUserSettings.ini")
    card = card_of(root)
    assert card["settings_files"] == [setting(card["prefix_path"], kept, "P", "ini")]


USER_REG_SHAPES = {
    "regular-file": True,
    "link-to-a-file-in-the-prefix": False,
    "link-to-a-file-outside": False,
    "dangling-link": False,
    "fifo": False,
}


@pytest.mark.parametrize(("shape", "listed"), USER_REG_SHAPES.items(), ids=USER_REG_SHAPES)
def test_c6_unity_user_reg_is_listed_only_as_a_regular_file(tmp_path, shape, listed):
    root = build(tmp_path, ["UnityPlayer.dll", "Game_Data/boot.config"], ["userdef.reg"])
    pfx = prefix_of(root)
    if shape == "link-to-a-file-in-the-prefix":
        (pfx / "user.reg").symlink_to("userdef.reg")
    else:
        outside = tmp_path / "outside" / "user.reg"
        make_entry(pfx / "user.reg", shape.replace("-outside", ""), outside)
    card = card_of(root)
    expected = [setting(card["install_path"], "Game_Data/boot.config", "I", "boot_config")]
    if listed:
        expected.append(setting(card["prefix_path"], "user.reg", "P", "registry"))
    assert card["settings_files"] == by_path(expected)


# ---------------------------------------------------------------------------- 6. pins


def test_c6_my_documents_link_is_listed_once_under_documents(tmp_path):
    rel = f"{DOCS}/G/Saved/Config/Windows/GameUserSettings.ini"
    root = build(tmp_path, [UNREAL_EXE], [rel])
    link_to_folder(prefix_of(root) / STEAMUSER / "My Documents", Path("Documents"))
    card = card_of(root)
    assert card["settings_files"] == [setting(card["prefix_path"], rel, "P", "ini")]


def test_c1_c7_a_program_files_link_to_a_deep_tree_is_bounded_and_truncated(tmp_path):
    kept = [entry for entry in ELIGIBLE_PREFIX if not entry.startswith(f"{PROGRAM_FILES}/")]
    root = build(tmp_path, ELIGIBLE_INSTALL, [*kept, f"drive_c/deep/{DEEP}/EasyAntiCheat/"])
    link_to_folder(prefix_of(root) / PROGRAM_FILES, Path("deep"))
    card = card_of(root)
    assert pairs(card) == [("scan_truncated", str(Path(card["prefix_path"], PROGRAM_FILES)))]
    assert card["anticheat"] == []
    assert card["tier_i_eligible"] is False


def test_c7_a_tool_card_is_walked_and_never_eligible(tmp_path):
    card = game(
        tmp_path,
        ["v2/lib64/easyanticheat_x64.so", "v2/lib/libstdc++.so.6"],
        appid=EAC_RUNTIME_APPID,
        name="Proton EasyAntiCheat Runtime",
    )
    assert card["kind"] == "tool"
    assert card["anticheat"] == [ac("easyanticheat", "v2/lib64/easyanticheat_x64.so")]
    assert card["tier_i_eligible"] is False


def test_c6_a_two_engine_game_gets_only_the_searches_of_the_engines_that_matched(tmp_path):
    engine_ini = f"{LOCAL}/G/Saved/Config/Windows/Engine.ini"
    card = game(
        tmp_path,
        [UNREAL_EXE, "UnityPlayer.dll", "Game_Data/boot.config", "config.ini"],
        ["user.reg", engine_ini],
    )
    assert card["engine"] == "ambiguous"
    assert card["engine_evidence"] == sorted(
        [UNREAL_EXE, "UnityPlayer.dll", "Game_Data/boot.config"]
    )
    install, prefix = card["install_path"], card["prefix_path"]
    assert card["settings_files"] == by_path(
        [
            setting(install, "Game_Data/boot.config", "I", "boot_config"),
            setting(prefix, "user.reg", "P", "registry"),
            setting(prefix, engine_ini, "P", "ini"),
        ]
    )
