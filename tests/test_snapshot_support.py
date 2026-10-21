# Shared fixtures and readers for the deckforge.snapshot tests (docs/specs/snapshot.md,
# S1-S10). This file holds no tests. The contracts are at the top of each test file:
#   test_snapshot_contents.py   S1 scan.json, S2 settings files, S7 manifest
#   test_snapshot_inventory.py  S3 sizes and orphans, S4 Decky plugins, S5 logs, S6 system
#   test_snapshot_safety.py     S8 output safety, S9 read-only, S10 CLI
#
# Reused from the existing suites (R13), never copied: the B9 change detector and open
# recorder and the Steam tree builders of test_discover_output.py, and the scandir refusal
# helper of test_detect_settings.py.
#
# Shapes the spec does not name, and the reading these tests take (see the report):
#   - Skip and added-file records in manifest.json are found by content, not by key name:
#     a skip is any object with a "reason" key whose string values include the source path;
#     an added file is any object without "reason" whose values include the zip name, the
#     source path and the int size.
#   - Issues (plugins, sizes) are any object with a str "code"; plugin issues may sit in any
#     JSON file of the zip, size issues must sit in sizes.json.
#   - sizes.json (ASSUMED key names, the spec gives none): a top-level "games" list with
#     one object per card holding appid, library, shadercache (int or null) and compatdata
#     (int or null); a top-level "orphans" list of objects holding path and size; issues
#     anywhere inside.
#   - A folder's "total byte size" is checked between two bounds: the regular files' sizes
#     (lower) and every entry's lstat size including folders, links and the folder itself
#     (upper). Following a link breaks the upper bound by megabytes.
#   - system.json "disk" may be a mapping {path: {total, used, free}} or a list of
#     {path, total, used, free}.

import collections
import json
import os
import stat
import zipfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pytest
from test_discover_output import CONFIG_VDF, add_game, libraryfolders, mkdir, put

from deckforge import discover, snapshot

MiB = 1024 * 1024
NOW = datetime(2026, 10, 21, 14, 3, 9, tzinfo=UTC)
ZIP_NAME = "deckforge-snapshot-20261021-140309Z.zip"
REAL_SCAN = discover.scan
REAL_OS_RELEASE = "/etc/os-release"
REAL_BOARD_NAME = "/sys/devices/virtual/dmi/id/board_name"

WILDS = 2246340  # RE Engine, config.ini, root library
BIG_RE = 2050650  # RE Engine, config.ini of 1 MiB + 1 byte
PENDING = 883710  # RE Engine, StateFlags 1026: installed false
UNITY = 1061090  # SD card, boot.config + user.reg (kind "registry")
UNREAL = 1203220  # SD card, prefix ini files
ORPHAN_SHADER = 999001  # root shadercache, no card
ORPHAN_COMPAT = 999002  # root compatdata, no card
ORPHAN_SD = 999003  # SD compatdata, no card

WILDS_INI = b"[Render]\r\nUpscaler=FSR\r\nFrameGen=Off\r\n; caf\xe9 \x00\xff\n"
OS_RELEASE = (
    'NAME="SteamOS"\n'
    'PRETTY_NAME="SteamOS"\n'
    "VERSION_CODENAME=holo\n"
    "ID=steamos\n"
    "ID_LIKE=arch\n"
    'ANSI_COLOR="1;35"\n'
    'HOME_URL="https://www.steampowered.com/"\n'
    "# a comment line\n"
    "\n"
    "LOGO=steamos\n"
    "VARIANT_ID=steamdeck\n"
    "VERSION_ID=3.6.19\n"
    "BUILD_ID=20241023.1\n"
)
OS_RELEASE_KEPT = {
    "NAME": "SteamOS",
    "PRETTY_NAME": "SteamOS",
    "VERSION_ID": "3.6.19",
    "BUILD_ID": "20241023.1",
    "VARIANT_ID": "steamdeck",
}
# (name, mtime offset): the mtime order differs from the name and creation orders.
LOG_PLAN = [
    ("a_wilds.csv", 300),
    ("b_wilds.csv", 700),
    ("c_sm2.csv", 100),
    ("d_sm2.csv", 500),
    ("e_hd2.csv", 200),
    ("f_hd2.csv", 600),
    ("g_cp.csv", 400),
]
LOG_EPOCH = 1_760_000_000
NEWEST_LOGS = [name for name, _ in sorted(LOG_PLAN, key=lambda item: -item[1])][:5]
PLUGINS = {
    "PowerTools": ('{"name": "PowerTools", "author": "NGnius"}', '{"version": "2.0.1"}'),
    "SimpleDeckyTDP": ('{"name": "SimpleDeckyTDP"}', '{"version": "0.7.3"}'),
    "broken-package": ('{"name": "Broken Package"}', '{"version": "1.0.0",'),
}

Usage = collections.namedtuple("Usage", "total used free")


@dataclass
class Deck:
    base: Path
    steam: Path
    sd: Path
    home: Path
    out: Path
    sysdir: Path
    settings: dict[str, Path] = field(default_factory=dict)
    logs: dict[str, Path] = field(default_factory=dict)
    private: list[Path] = field(default_factory=list)

    @property
    def libraries(self) -> list[Path]:
        return [self.steam, self.sd]

    @property
    def plugins_dir(self) -> Path:
        return self.home / "homebrew" / "plugins"

    @property
    def logs_dir(self) -> Path:
        return self.home / "deckforge" / "logs"


# ---------------------------------------------------------------------------- building


def sparse(path: Path, size: int) -> Path:
    """A file of `size` zero bytes that takes no disk space."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.truncate(size)
    return path


def game(library: Path, appid: int, *, flags: str = "4") -> Path:
    """test_discover_output.add_game, with another StateFlags value if asked. Returns the
    install folder."""
    add_game(library, appid)
    if flags != "4":
        acf = library / "steamapps" / f"appmanifest_{appid}.acf"
        text = acf.read_text(encoding="utf-8")
        acf.write_text(text.replace('"StateFlags"\t\t"4"', f'"StateFlags"\t\t"{flags}"'), "utf-8")
    return library / "steamapps" / "common" / f"Game{appid}"


def build_deck(base: Path, steam: Path | None = None) -> Deck:
    """A Deck-like tree under `base`: Steam root plus SD-card library, a home with Decky
    plugins and frame-time logs, and the two system files. out_dir is not created."""
    home = base / "home"
    steam = steam or base / "steam"
    sd = base / "mmcblk0p1"
    deck = Deck(
        base=base,
        steam=steam,
        sd=sd,
        home=home,
        out=home / "deckforge" / "snapshots",
        sysdir=base / "sys",
    )
    entries = [("0", str(steam)), ("1", str(sd)), ("2", str(base / "gone"))]
    put(steam / "steamapps" / "libraryfolders.vdf", libraryfolders(entries))
    put(steam / "config" / "config.vdf", CONFIG_VDF)
    mkdir(sd / "steamapps")
    root_apps, sd_apps = steam / "steamapps", sd / "steamapps"

    wilds = game(steam, WILDS)
    put(wilds / "re_chunk_000.pak", b"\0" * 64)
    deck.settings["wilds"] = put(wilds / "config.ini", WILDS_INI)
    cache = root_apps / "shadercache" / str(WILDS)
    put(cache / "fozpipelinesv6" / "steamapprun_pipeline_cache.foz", b"\x01" * 250_000)
    put(cache / "fozmediav1" / "foz.idx", b"\x02" * 1000)
    outside = base / "outside"
    (cache / "big_link").symlink_to(sparse(outside / "big.bin", 3 * MiB))
    sparse(outside / "bigdir" / "inner.bin", 3 * MiB)
    (cache / "dir_link").symlink_to(outside / "bigdir", target_is_directory=True)
    wilds_pfx = root_apps / "compatdata" / str(WILDS) / "pfx"
    put(root_apps / "compatdata" / str(WILDS) / "config_info", "9.0-1\n")
    deck.private += [
        put(wilds_pfx / "user.reg", "WINE REGISTRY Version 2\n[Software\\\\Capcom] secret\n"),
        put(wilds_pfx / "system.reg", "WINE REGISTRY Version 2\n"),
        put(wilds_pfx / "drive_c/users/steamuser/AppData/Roaming/Capcom/data001.sav", b"save"),
    ]

    big = game(steam, BIG_RE)
    put(big / "re_chunk_000.pak", b"\0")
    deck.settings["big"] = sparse(big / "config.ini", MiB + 1)

    pending = game(steam, PENDING, flags="1026")
    put(pending / "re_chunk_000.pak", b"\0")
    deck.settings["pending"] = put(pending / "config.ini", b"[Pending]\n")

    unity = game(sd, UNITY)
    put(unity / "UnityPlayer.dll", b"MZ")
    deck.settings["unity_boot"] = put(unity / "Game_Data" / "boot.config", b"gfx-jobs=1\n")
    unity_pfx = sd_apps / "compatdata" / str(UNITY) / "pfx"
    deck.settings["unity_reg"] = put(unity_pfx / "user.reg", "WINE REGISTRY\n[Unity] token\n")
    deck.private += [deck.settings["unity_reg"], put(unity_pfx / "system.reg", "WINE\n")]

    unreal = game(sd, UNREAL)
    put(unreal / "Game/Binaries/Win64/Game-Win64-Shipping.exe", b"MZ")
    config = sd_apps / "compatdata" / str(UNREAL) / "pfx"
    config = config / "drive_c/users/steamuser/AppData/Local/Game/Saved/Config/Windows"
    deck.settings["unreal_engine"] = put(config / "Engine.ini", b"[SystemSettings]\nr.X=1\n")
    deck.settings["unreal_gus"] = put(config / "GameUserSettings.ini", b"[ScalabilityGroups]\n")
    put(root_apps / "compatdata" / str(UNREAL) / "stale.txt", b"x" * 10)  # has a card: no orphan

    put(root_apps / "shadercache" / str(ORPHAN_SHADER) / "a.foz", b"\x03" * 4096)
    deck.private.append(
        put(root_apps / "compatdata" / str(ORPHAN_COMPAT) / "pfx" / "user.reg", "WINE\n")
    )
    put(sd_apps / "compatdata" / str(ORPHAN_SD) / "pfx" / "x.bin", b"\x04" * 2048)
    put(root_apps / "compatdata" / "tmp-123" / "junk", b"j")
    put(root_apps / "shadercache" / "999004.old" / "junk", b"j")

    deck.private += [
        put(steam / "config" / "loginusers.vdf", '"users"\n{\n}\n'),
        put(steam / "userdata/12345/config/localconfig.vdf", '"UserLocalConfigStore"\n{\n}\n'),
        put(steam / "userdata" / "12345" / str(WILDS) / "remote" / "data001.sav", b"cloud"),
    ]

    for folder, (plugin_json, package_json) in PLUGINS.items():
        put(deck.plugins_dir / folder / "plugin.json", plugin_json)
        put(deck.plugins_dir / folder / "package.json", package_json)
    put(deck.plugins_dir / "README.md", "not a plugin folder\n")

    for n, (name, offset) in enumerate(LOG_PLAN):
        path = put(deck.logs_dir / name, f"fps,frametime\n45,22.{n}\n44,{n}.9\n" * (n + 1))
        os.utime(path, (LOG_EPOCH + offset, LOG_EPOCH + offset))
        deck.logs[name] = path
    newest = LOG_EPOCH + 10_000
    decoys = [put(deck.logs_dir / "notes.txt", "x"), put(deck.logs_dir / "x.csv.bak", "x")]
    decoys.append(mkdir(deck.logs_dir / "folder.csv"))
    link = deck.logs_dir / "link.csv"
    link.symlink_to(deck.logs["c_sm2.csv"])
    for decoy in decoys:
        os.utime(decoy, (newest, newest))
    os.utime(link, (newest, newest), follow_symlinks=False)

    put(deck.sysdir / "os-release", OS_RELEASE)
    put(deck.sysdir / "board_name", "Galileo\n")
    return deck


def make_deck(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, steam: Path | None = None) -> Deck:
    """build_deck plus the two system paths redirected through the module constants."""
    deck = build_deck(mkdir(tmp_path / "data"), steam)
    monkeypatch.setattr(snapshot, "OS_RELEASE_PATH", str(deck.sysdir / "os-release"))
    monkeypatch.setattr(snapshot, "BOARD_NAME_PATH", str(deck.sysdir / "board_name"))
    return deck


def run(deck: Deck, *, now: datetime = NOW, out: Path | str | None = None) -> Path:
    out_dir = deck.out if out is None else out
    result = snapshot.build_snapshot(str(deck.steam), str(deck.home), str(out_dir), now=now)
    assert isinstance(result, str)
    return Path(result)


# ---------------------------------------------------------------------------- scan patching


def patch_scan(monkeypatch: pytest.MonkeyPatch, fake: Callable[[str], dict]) -> None:
    """Make `fake` the deckforge.discover.scan that snapshot calls, however it imported it."""
    monkeypatch.setattr(discover, "scan", fake)
    if getattr(snapshot, "scan", None) is REAL_SCAN:
        monkeypatch.setattr(snapshot, "scan", fake)


def scan_then(monkeypatch: pytest.MonkeyPatch, action: Callable[[], object]) -> None:
    """The real scan runs, then `action` changes the tree before snapshot sees the result:
    what a running Steam or a user could do between the scan and the copy."""

    def fake(steam_root, *args, **kwargs):
        result = REAL_SCAN(steam_root, *args, **kwargs)
        action()
        return result

    patch_scan(monkeypatch, fake)


def scan_editing(monkeypatch: pytest.MonkeyPatch, edit: Callable[[dict], None]) -> None:
    """The real scan runs, then `edit` changes the returned result."""

    def fake(steam_root, *args, **kwargs):
        result = REAL_SCAN(steam_root, *args, **kwargs)
        edit(result)
        return result

    patch_scan(monkeypatch, fake)


def card(result: dict, appid: int) -> dict:
    found = [entry for entry in result["games"] if entry["appid"] == appid]
    assert len(found) == 1
    return found[0]


# ---------------------------------------------------------------------------- zip readers


def zip_members(zip_path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)), "duplicate member names"
        assert archive.testzip() is None
        return {name: archive.read(name) for name in names}


def zip_names(zip_path: Path) -> list[str]:
    with zipfile.ZipFile(zip_path) as archive:
        return archive.namelist()


def zip_json(members: dict[str, bytes], name: str):
    assert name in members, f"{name} missing from the zip"
    return json.loads(members[name].decode("utf-8"))


def dicts_in(obj) -> Iterator[dict]:
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from dicts_in(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from dicts_in(value)


def issues_in(obj) -> list[tuple[str, str | None]]:
    return [
        (entry["code"], entry.get("path"))
        for entry in dicts_in(obj)
        if isinstance(entry.get("code"), str)
    ]


def all_json(members: dict[str, bytes]) -> list:
    return [zip_json(members, name) for name in members if name.endswith(".json")]


def strs(entry: dict) -> set[str]:
    return {value for value in entry.values() if isinstance(value, str)}


def ints(entry: dict) -> set[int]:
    return {v for v in entry.values() if isinstance(v, int) and not isinstance(v, bool)}


def added_records(manifest: dict, zip_name: str, source: Path) -> list[dict]:
    return [
        entry
        for entry in dicts_in(manifest)
        if "reason" not in entry and zip_name in strs(entry) and str(source) in strs(entry)
    ]


def skip_reasons(manifest: dict, source: Path) -> list[str]:
    return [
        entry["reason"]
        for entry in dicts_in(manifest)
        if "reason" in entry and str(source) in strs(entry)
    ]


def mentions(obj, text: str) -> bool:
    if isinstance(obj, dict):
        return any(key == text or mentions(value, text) for key, value in obj.items())
    if isinstance(obj, list):
        return any(mentions(value, text) for value in obj)
    return obj == text


def size_bounds(folder: Path) -> tuple[int, int]:
    """(regular files only, every entry's lstat size including the folder), links not
    followed."""
    lower = upper = 0
    pending = [folder]
    while pending:
        path = pending.pop()
        info = path.lstat()
        upper += info.st_size
        if stat.S_ISREG(info.st_mode):
            lower += info.st_size
        elif stat.S_ISDIR(info.st_mode):
            pending.extend(path.iterdir())
    return lower, upper


def is_inside(path: str | Path, folder: Path) -> bool:
    real, top = os.path.realpath(path), os.path.realpath(folder)
    return real == top or real.startswith(top + os.sep)
