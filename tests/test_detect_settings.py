# Contracts for PR B2 of docs/specs/discover.md, criteria C6 (settings files), C7 (Tier I
# eligibility) and C8 (missing install folder). Written test-first: the cards from
# deckforge.discover.scan do not have the B2 fields yet. Observed through discover.scan.
#
# settings_files, criterion C6
#   Pre:  the card's engine (C2). Each engine that matched is searched. A game matching all
#         three engines ("ambiguous") gets every search. Whether a game matching only two
#         engines also gets the third search is not settled by the spec and is not tested.
#   Post: a list of {"path": absolute str, "class": "P" or "I", "kind": str}, sorted by path:
#           re_engine  <install>/config.ini                                  I  ini
#           unity      boot.config in a *_Data folder at the install root or
#                      one level below                                       I  boot_config
#                      <prefix>/user.reg, only if it is a file               P  registry
#           unreal     GameUserSettings.ini or Engine.ini (ignoring case) with Saved directly
#                      followed by Config (ignoring case) among its folders,
#                      found by walking (depth 6) from <prefix>/drive_c/users/steamuser/
#                      AppData/Local, Documents/My Games and My Documents/My Games  P  ini
#         Install-folder copies of Unreal ini files are not listed (no install search for
#         Unreal), and a settings file of an engine that did not match is not listed.
#   Post: a C6 start folder that is a link is used only if its real path is inside the
#         prefix's real path. A folder named dosdevices is never entered; links found in a
#         walk are never entered (C1), so dosdevices/z: and similar links lead nowhere.
#   Inv:  only names are inspected: no settings file is ever opened, and the only files a
#         scan opens are B9's three kinds.
#   Inv:  a game on an SD card whose prefix is in the root library (B4
#         prefix_in_other_library) is searched in that prefix, for C3 and for C6.
#
# tier_i_eligible, criterion C7
#   Post: true exactly when all of these hold (fails closed): kind == "game"; the install
#         folder exists; no walk for this card (install, Program Files, Program Files
#         (x86), the three C6 folders) was truncated; no unreadable warning; anticheat is
#         empty. Each condition is broken on its own against a fixture that is otherwise
#         eligible. Injectors and upscalers do not affect it.
#
# Missing install folder, criterion C8
#   Post: when B4 reports install_folder_missing (absent, a file, or only another case of
#         the name on disk): engine "unknown", engine_evidence [], upscalers [], injectors
#         [], settings_files [] (even with a prefix full of settings files), anticheat
#         holds only the curated entry if the appid is curated, tier_i_eligible False.
#
# Round trip: no write or restore path in B2; the read-only property that replaces it is in
# test_detect_walks.py.

import builtins
import errno
import io
import os
import pathlib
from pathlib import Path

import pytest

from deckforge import discover

APPID = 1086940
D10 = "/".join(f"d{n}" for n in range(1, 11))  # a name inside has depth 11
P6 = "p1/p2/p3/p4/p5/p6"  # a name inside has depth 7
PROGRAM_FILES = "drive_c/Program Files"
PROGRAM_FILES_X86 = "drive_c/Program Files (x86)"
STEAMUSER = "drive_c/users/steamuser"
LOCAL = f"{STEAMUSER}/AppData/Local"
DOCS = f"{STEAMUSER}/Documents/My Games"
MY_DOCS = f"{STEAMUSER}/My Documents/My Games"
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


def prefix_of(root: Path, appid: int = APPID) -> Path:
    return root / "steamapps" / "compatdata" / str(appid) / "pfx"


def pairs(card: dict) -> list[tuple[str, str | None]]:
    return [(issue["code"], issue["path"]) for issue in card["warnings"]]


def paths_of(card: dict, code: str) -> list:
    return [issue["path"] for issue in card["warnings"] if issue["code"] == code]


def setting(base: str, rel: str, cls: str, kind: str) -> dict:
    return {"path": str(Path(base, rel)), "class": cls, "kind": kind}


def by_path(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda entry: entry["path"])


def pfx_forms(start: str, rel: str) -> set[str]:
    """Both readings of C3's "pfx/<relative path>" (relative to the prefix or the start)."""
    return {f"pfx/{start}/{rel}", f"pfx/{rel}"}


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


def record_opens(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record every path opened through builtins.open, io.open, os.open and Path.open."""
    seen: list[str] = []
    real_open, real_os_open, real_path_open = builtins.open, os.open, pathlib.Path.open

    def note(file: object) -> None:
        if isinstance(file, str | bytes | os.PathLike):
            seen.append(os.fsdecode(os.fspath(file)))

    def fake_open(file, *args, **kwargs):
        note(file)
        return real_open(file, *args, **kwargs)

    def fake_os_open(path, *args, **kwargs):
        note(path)
        return real_os_open(path, *args, **kwargs)

    def fake_path_open(self, *args, **kwargs):
        note(self)
        return real_path_open(self, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(io, "open", fake_open)
    monkeypatch.setattr(os, "open", fake_os_open)
    monkeypatch.setattr(pathlib.Path, "open", fake_path_open)
    return seen


# ---------------------------------------------------------------------------- C6 RE Engine


def test_c6_re_engine_config_ini_at_the_install_root_is_class_i(tmp_path):
    card = game(
        tmp_path,
        ["re_chunk_000.pak", "config.ini", "natives/config.ini"],
        ["user.reg", f"{LOCAL}/G/Saved/Config/Engine.ini"],
    )
    assert card["engine"] == "re_engine"
    assert card["settings_files"] == [setting(card["install_path"], "config.ini", "I", "ini")]


# ---------------------------------------------------------------------------- C6 Unity


@pytest.mark.parametrize("data", ["Game_Data", "Sub/Game_Data"])
def test_c6_unity_boot_config_is_class_i_and_user_reg_is_class_p(tmp_path, data):
    card = game(
        tmp_path,
        [f"{data}/boot.config", "a/b/Old_Data/boot.config", "config.ini"],
        ["user.reg", f"{LOCAL}/G/Saved/Config/Engine.ini"],
    )
    assert card["engine"] == "unity"
    assert card["settings_files"] == by_path(
        [
            setting(card["install_path"], f"{data}/boot.config", "I", "boot_config"),
            setting(card["prefix_path"], "user.reg", "P", "registry"),
        ]
    )


@pytest.mark.parametrize(
    "prefix", [None, [], ["user.reg/"]], ids=["no-prefix", "no-user-reg", "user-reg-is-a-folder"]
)
def test_c6_unity_registry_is_listed_only_as_a_file(tmp_path, prefix):
    card = game(tmp_path, ["UnityPlayer.dll", "Game_Data/boot.config"], prefix)
    assert card["settings_files"] == [
        setting(card["install_path"], "Game_Data/boot.config", "I", "boot_config")
    ]


# ---------------------------------------------------------------------------- C6 Unreal

UNREAL_HITS = [
    f"{LOCAL}/Game/Saved/Config/Windows/GameUserSettings.ini",
    f"{LOCAL}/Saved/Config/Engine.ini",
    f"{DOCS}/Game/Saved/Config/WindowsNoEditor/Engine.ini",
    f"{MY_DOCS}/Other/saved/CONFIG/engine.INI",
]
UNREAL_MISSES = [
    f"{LOCAL}/Game/Saved/Logs/Engine.ini",
    f"{LOCAL}/Game/Config/Saved/Engine.ini",
    f"{LOCAL}/Game/Saved/Old/Config/Engine.ini",
    f"{LOCAL}/Game/Saved/Config/Windows/Input.ini",
    f"{LOCAL}/Game/Saved/Config/Windows/Engine.ini/",
    f"{LOCAL}/Engine.ini",
    f"{STEAMUSER}/AppData/Roaming/Game/Saved/Config/Engine.ini",
    f"{STEAMUSER}/Saved/Config/Engine.ini",
]


def test_c6_unreal_ini_files_under_saved_config_in_each_prefix_start_folder(tmp_path):
    card = game(
        tmp_path,
        [UNREAL_EXE, "Game/Saved/Config/Windows/Engine.ini", "config.ini"],
        ["user.reg", *UNREAL_HITS, *UNREAL_MISSES],
    )
    assert card["engine"] == "unreal"
    assert card["settings_files"] == by_path(
        [setting(card["prefix_path"], rel, "P", "ini") for rel in UNREAL_HITS]
    )


SETTINGS_DEPTH = {
    "depth-6-is-found": (f"{LOCAL}/Studio/Game/Saved/Config/Windows/Engine.ini", True),
    "depth-7-is-skipped": (f"{LOCAL}/Studio/Sub/Game/Saved/Config/Windows/Engine.ini", False),
}


@pytest.mark.parametrize(("rel", "found"), SETTINGS_DEPTH.values(), ids=SETTINGS_DEPTH)
def test_c6_unreal_search_walks_to_depth_6(tmp_path, rel, found):
    card = game(tmp_path, [UNREAL_EXE], [rel])
    start = str(Path(card["prefix_path"], LOCAL))
    expected = [setting(card["prefix_path"], rel, "P", "ini")] if found else []
    assert card["settings_files"] == expected
    assert paths_of(card, "scan_truncated") == ([] if found else [start])


def test_c6_an_unknown_engine_has_no_settings_files(tmp_path):
    card = game(
        tmp_path,
        ["config.ini", "Game_Data/level0", "Game/Saved/Config/Engine.ini"],
        ["user.reg", f"{LOCAL}/G/Saved/Config/Engine.ini"],
    )
    assert card["engine"] == "unknown"
    assert card["settings_files"] == []


def test_c6_an_ambiguous_game_gets_every_engine_search(tmp_path):
    card = game(
        tmp_path,
        ["re_chunk_000.pak", "config.ini", "UnityPlayer.dll", "Game_Data/boot.config", UNREAL_EXE],
        ["user.reg", f"{LOCAL}/G/Saved/Config/Windows/Engine.ini"],
    )
    assert card["engine"] == "ambiguous"
    install, prefix = card["install_path"], card["prefix_path"]
    assert card["settings_files"] == by_path(
        [
            setting(install, "config.ini", "I", "ini"),
            setting(install, "Game_Data/boot.config", "I", "boot_config"),
            setting(prefix, "user.reg", "P", "registry"),
            setting(prefix, f"{LOCAL}/G/Saved/Config/Windows/Engine.ini", "P", "ini"),
        ]
    )


# ---------------------------------------------------------------------------- C6 links


@pytest.mark.parametrize("target", ["absolute", "relative"])
def test_c6_a_start_folder_link_inside_the_prefix_is_used(tmp_path, target):
    real = f"{STEAMUSER}/LocalReal/G/Saved/Config/Engine.ini"
    root = build(tmp_path, [UNREAL_EXE], [real, f"{STEAMUSER}/AppData/"])
    pfx = prefix_of(root)
    link_to = pfx / STEAMUSER / "LocalReal" if target == "absolute" else Path("..", "LocalReal")
    (pfx / LOCAL).symlink_to(link_to, target_is_directory=True)
    card = card_of(root)
    [found] = card["settings_files"]
    assert (found["class"], found["kind"]) == ("P", "ini")
    assert Path(found["path"]).is_absolute()
    assert os.path.realpath(found["path"]) == os.path.realpath(pfx / real)


OUTSIDE_TARGETS = ["a-folder-elsewhere", "through-dosdevices-z", "a-sibling-of-the-prefix"]


@pytest.mark.parametrize("target", OUTSIDE_TARGETS)
def test_c6_a_start_folder_link_outside_the_prefix_is_not_used(tmp_path, target):
    kept = f"{LOCAL}/H/Saved/Config/GameUserSettings.ini"
    root = build(tmp_path, [UNREAL_EXE], [kept, f"{STEAMUSER}/Documents/", "dosdevices/"])
    pfx = prefix_of(root)
    zroot = tmp_path / "zroot"
    (pfx / "dosdevices" / "z:").symlink_to(zroot, target_is_directory=True)
    outside = {
        "a-folder-elsewhere": tmp_path / "elsewhere" / "games",
        "through-dosdevices-z": zroot / "games",
        "a-sibling-of-the-prefix": pfx.parent / "pfx_old" / "games",
    }[target]
    plant(outside, ["G/Saved/Config/Engine.ini"])
    link_to = pfx / "dosdevices" / "z:" / "games" if target == "through-dosdevices-z" else outside
    (pfx / DOCS).symlink_to(link_to, target_is_directory=True)
    card = card_of(root)
    assert card["settings_files"] == [setting(card["prefix_path"], kept, "P", "ini")]


def test_c6_dosdevices_and_links_to_other_drives_are_never_entered(tmp_path):
    zroot = tmp_path / "zroot"
    plant(zroot, ["Saved/Config/Engine.ini", f"{LOCAL}/G/Saved/Config/Engine.ini"])
    kept = f"{LOCAL}/Game/Saved/Config/Engine.ini"
    root = build(
        tmp_path,
        [UNREAL_EXE],
        [
            kept,
            f"{LOCAL}/dosdevices/Saved/Config/Engine.ini",
            f"{LOCAL}/Studio/dosdevices/Saved/Config/GameUserSettings.ini",
            "dosdevices/",
        ],
    )
    pfx = prefix_of(root)
    (pfx / "dosdevices" / "c:").symlink_to("../drive_c", target_is_directory=True)
    (pfx / "dosdevices" / "z:").symlink_to(zroot, target_is_directory=True)
    (pfx / LOCAL / "ZDrive").symlink_to(pfx / "dosdevices" / "z:", target_is_directory=True)
    card = card_of(root)
    assert card["settings_files"] == [setting(card["prefix_path"], kept, "P", "ini")]


# ---------------------------------------------------------------------------- C6 never opened


def test_c6_settings_files_are_never_opened(tmp_path, monkeypatch):
    root = build(
        tmp_path,
        ["re_chunk_000.pak", "config.ini", "UnityPlayer.dll", "Game_Data/boot.config", UNREAL_EXE],
        [
            "user.reg",
            f"{LOCAL}/G/Saved/Config/Engine.ini",
            f"{DOCS}/G/Saved/Config/GameUserSettings.ini",
        ],
    )
    with monkeypatch.context() as patch:
        opened = record_opens(patch)
        card = card_of(root)
    assert len(card["settings_files"]) == 5
    assert opened, "the recorder saw no open at all, so it cannot vouch for anything"
    allowed = {"libraryfolders.vdf", "config.vdf", f"appmanifest_{APPID}.acf"}
    assert {Path(path).name for path in opened} <= allowed
    settings = {os.path.realpath(entry["path"]) for entry in card["settings_files"]}
    assert settings.isdisjoint(os.path.realpath(path) for path in opened)


# ---------------------------------------------------------------------------- C6 + C3 SD card


def test_c6_and_c3_search_the_root_library_prefix_of_an_sd_card_game(tmp_path):
    sd = tmp_path / "sd"
    root = make_steam(tmp_path, sd)
    install, _ = add_game(sd)
    plant(install, ["UnityPlayer.dll", "Game_Data/boot.config"])
    pfx = prefix_of(root)
    plant(pfx, ["user.reg", f"{PROGRAM_FILES_X86}/EasyAntiCheat_EOS/"])
    card = card_of(root)
    assert card["prefix_path"] == str(pfx)
    assert card["settings_files"] == by_path(
        [
            setting(card["install_path"], "Game_Data/boot.config", "I", "boot_config"),
            setting(str(pfx), "user.reg", "P", "registry"),
        ]
    )
    [found] = card["anticheat"]
    assert found["system"] == "easyanticheat"
    assert found["evidence"][0] in pfx_forms(PROGRAM_FILES_X86, "EasyAntiCheat_EOS")


# ---------------------------------------------------------------------------- C7 eligibility

ELIGIBLE_INSTALL = [UNREAL_EXE, "OptiScaler.ini", "Game/Plugins/nvngx_dlss.dll"]
ELIGIBLE_PREFIX = [
    "user.reg",
    f"{LOCAL}/G/Saved/Config/Engine.ini",
    f"{PROGRAM_FILES}/Common Files/",
    f"{PROGRAM_FILES_X86}/Steam/",
]
INJECTOR_WARNING = ("injector_with_anticheat", None, "OptiScaler.ini")  # C5, path as is
ELIGIBILITY = {
    "all-conditions-hold": ({}, True, []),
    "kind-is-tool": ({"name": "Proton 9.0"}, False, []),
    "install-folder-missing": (
        {"install": None},
        False,
        [("install_folder_missing", "install", "")],
    ),
    "install-walk-truncated": (
        {"install": [*ELIGIBLE_INSTALL, f"{D10}/x.txt"]},
        False,
        [("scan_truncated", "install", "")],
    ),
    "program-files-walk-truncated": (
        {"prefix": [*ELIGIBLE_PREFIX, f"{PROGRAM_FILES}/{P6}/x.txt"]},
        False,
        [("scan_truncated", "prefix", PROGRAM_FILES)],
    ),
    "program-files-x86-walk-truncated": (
        {"prefix": [*ELIGIBLE_PREFIX, f"{PROGRAM_FILES_X86}/{P6}/x.txt"]},
        False,
        [("scan_truncated", "prefix", PROGRAM_FILES_X86)],
    ),
    "settings-walk-truncated": (
        {"prefix": [*ELIGIBLE_PREFIX, f"{DOCS}/{P6}/x.txt"]},
        False,
        [("scan_truncated", "prefix", DOCS)],
    ),
    "anticheat-in-install": (
        {"install": [*ELIGIBLE_INSTALL, "EasyAntiCheat/"]},
        False,
        [INJECTOR_WARNING],
    ),
    "anticheat-in-prefix": (
        {"prefix": [*ELIGIBLE_PREFIX, f"{PROGRAM_FILES_X86}/Common Files/BattlEye/"]},
        False,
        [INJECTOR_WARNING],
    ),
    "curated-anticheat": ({"appid": 553850}, False, [INJECTOR_WARNING]),
}


@pytest.mark.parametrize(("change", "eligible", "warnings"), ELIGIBILITY.values(), ids=ELIGIBILITY)
def test_c7_tier_i_eligible_needs_every_condition(tmp_path, change, eligible, warnings):
    setup = {"install": ELIGIBLE_INSTALL, "prefix": ELIGIBLE_PREFIX, **change}
    card = game(tmp_path, **setup)
    assert card["tier_i_eligible"] is eligible
    bases = {"install": card["install_path"], "prefix": card["prefix_path"]}
    expected = [
        (code, str(Path(bases[base], rel)) if base else rel) for code, base, rel in warnings
    ]
    assert pairs(card) == expected


UNREADABLE = {
    "install-subfolder": ("install", "Game/Plugins"),
    "program-files-subfolder": ("prefix", f"{PROGRAM_FILES}/Common Files"),
    "settings-subfolder": ("prefix", f"{LOCAL}/G"),
}


@pytest.mark.parametrize(("base", "rel"), UNREADABLE.values(), ids=UNREADABLE)
def test_c7_an_unreadable_folder_makes_the_card_ineligible(tmp_path, monkeypatch, base, rel):
    root = build(tmp_path, ELIGIBLE_INSTALL, ELIGIBLE_PREFIX)
    assert card_of(root)["tier_i_eligible"] is True  # control: the same tree, all readable
    folders = {"install": root / "steamapps" / "common" / "Game", "prefix": prefix_of(root)}
    refuse_listing(monkeypatch, folders[base] / rel)
    card = card_of(root)
    assert paths_of(card, "unreadable") == [str(Path(card[f"{base}_path"], rel))]
    assert card["tier_i_eligible"] is False


# ---------------------------------------------------------------------------- C8 missing folder


@pytest.mark.parametrize("missing", ["absent", "a-file", "other-case-only"])
def test_c8_missing_install_folder_gives_empty_detection(tmp_path, missing):
    root = make_steam(tmp_path)
    install, pfx = add_game(root)
    if missing == "a-file":
        put(install)
    if missing == "other-case-only":
        plant(install.parent / "game", [UNREAL_EXE, "EasyAntiCheat/", "nvngx_dlss.dll"])
    plant(pfx, ["user.reg", f"{LOCAL}/G/Saved/Config/Engine.ini"])
    card = card_of(root)
    assert ("install_folder_missing", card["install_path"]) in pairs(card)
    assert {field: card[field] for field in B2_FIELDS} == {
        "engine": "unknown",
        "engine_evidence": [],
        "anticheat": [],
        "tier_i_eligible": False,
        "upscalers": [],
        "injectors": [],
        "settings_files": [],
    }


@pytest.mark.parametrize(("appid", "system"), [(2183900, "easyanticheat"), (553850, "gameguard")])
def test_c8_missing_install_folder_keeps_the_curated_anticheat(tmp_path, appid, system):
    card = game(tmp_path, None, ["user.reg"], appid=appid)
    assert {field: card[field] for field in B2_FIELDS} == {
        "engine": "unknown",
        "engine_evidence": [],
        "anticheat": [{"system": system, "evidence": ["(curated)"]}],
        "tier_i_eligible": False,
        "upscalers": [],
        "injectors": [],
        "settings_files": [],
    }
