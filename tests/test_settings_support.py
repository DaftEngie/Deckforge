# Shared data and helpers for the deckforge.settings tests (docs/specs/settings-read.md,
# S1-S10 and clarifier answers 1-18). This file holds no tests. The contracts are at the top
# of each test file:
#   test_settings_ini.py     S1 read_ini, answers 10, 11, 14, 18
#   test_settings_maps.py    S2 load_maps validation, S3 built-in maps, answers 1-3, 5, 9, 13
#   test_settings_report.py  S4 match_maps, S5-S7 read_settings, S10, answers 4, 6-8, 12-17
#   test_settings_cli.py     S7 text, S8 CLI, S9 read-only
#
# Reused from the existing suites (R13), never copied: the Steam-tree writers (manifest,
# libraryfolders, put, mkdir, CONFIG_VDF), the lstat change detector and the open recorder
# of test_discover_output.py.
#
# Real-data fixtures (S10, answer 15): trimmed copies of Fede's 2026-10-21 files, under their
# real base names. Only the sections the spec names are kept, and only some of their lines.
# Lines that could identify a machine or a player (CPU, display device, adapter, client id)
# are left out. Values and line endings are as in the real files (LF for the two Capcom
# files, CRLF for the two Unreal files).

import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from test_discover_output import CONFIG_VDF, libraryfolders, manifest, mkdir, put

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PACKAGE = SRC / "deckforge"
MAPS_DIR = PACKAGE / "maps"
MiB = 1024 * 1024

BUILTIN_IDS = ["re-appoption-section", "re-graphics-section", "unreal-scalability"]
UNREAL = "unreal-scalability"
RE_GRAPHICS = "re-graphics-section"
RE_APPOPTION = "re-appoption-section"

# Answer 8: frozen key sets.
GAME_KEYS = {"appid", "name", "engine", "anticheat", "status", "maps", "unmapped_files", "issues"}
MAP_ENTRY_KEYS = {"map_id", "file", "encoding", "duplicates", "knobs"}
KNOB_KEYS = {"id", "label", "section", "key", "type", "present", "value", "known", "confidence"}
ISSUE_KEYS = {
    "registry_not_read": {"code", "path"},
    "settings_unreadable": {"code", "path", "why"},
    "changed_during_read": {"code", "path"},
    "conflicting_files": {"code", "path", "map_id", "knob"},
}
STATUSES = {"unreadable", "no_map", "mapped_empty", "mapped_with_unknown_values", "mapped"}

NO_MAP_TEXT = "no map: change graphics settings in the game's menu"
ANTICHEAT_TEXT = "settings files only; DeckForge will never inject into this game"
DD2_SOURCE = "key names only, no menu evidence; Fede's DD2 config.ini 2026-10-21"

# ---------------------------------------------------------------------------- real data

# Monster Hunter Wilds, appid 2246340, steamapps/common/MonsterHunterWilds/config.ini.
# [Graphics] trimmed to the map's keys plus a few others (AOSetting, the excluded conflict;
# keys whose values hold ( ) , : and .), then [Graphics/FSR3], [Graphics/RayTracing] (which
# has its own Quality and AOSetting) and a trimmed [RenderConfig] (answer 4).
WILDS_INI = (
    b"[Graphics]\n"
    b"AOSetting=LOW\n"
    b"Algorithm=FSR3\n"
    b"AlgorithmFG=NONE\n"
    b"AntiAliasing=NONE\n"
    b"Bloom_Enable=True\n"
    b"Bloom_ReductionLevel=2\n"
    b"ContactShadowSetting=OFF\n"
    b"DOF_Enable=True\n"
    b"GIQuality=LOW\n"
    b"GrassPushCollision=False\n"
    b"GroundQuality=HIGH\n"
    b"IBLRaymarchScale=0.75\n"
    b"ImageQualityRate=1\n"
    b"MeshCullingSetting=HIGH\n"
    b"MotionBlur_Enable=True\n"
    b"NormalWindowResolution=(1280,800)\n"
    b"Quality=Balanced\n"
    b"ResourceOption=High\n"
    b"SSR_Enable=False\n"
    b"SSSSS_Enable=False\n"
    b"SamplerQuality=Bilinear\n"
    b"ShaderConvertVersion=Product:1.42.0.2,File:1.42.0.2\n"
    b"ShadowCastDistanceType=MIDDLE\n"
    b"ShadowQuality=LOWEST\n"
    b"SpeedTreeWindLOD=True\n"
    b"SpeedTreeWind_Branch=0\n"
    b"SpeedTreeWind_Global=0\n"
    b"SpeedTreeWind_Leaf=0\n"
    b"StreamingTextureQuality=HIGH\n"
    b"UseLowShellFur=False\n"
    b"UseLowWaterSimulation=True\n"
    b"VRSSetting=Off\n"
    b"VolumetricFogControl_Enable=True\n"
    b"VolumetricFogControl_TextureSize=W54xH30xD32\n"
    b"WindSimulationQuality=OFF\n"
    b"[Graphics/FSR3]\n"
    b"EnableSharpness=True\n"
    b"Sharpness=0.65\n"
    b"[Graphics/RayTracing]\n"
    b"AOSetting=CUSTOM\n"
    b"Enable=False\n"
    b"GIEnable=False\n"
    b"Quality=STANDARD\n"
    b"ReflectionEnable=True\n"
    b"ShadowEnable=False\n"
    b"SpecularRoughnessThresholdQuality=STANDARD\n"
    b"[RenderConfig]\n"
    b"AOSetting=LOW\n"
    b"AntiAliasing=NONE\n"
    b"ContactShadowSetting=OFF\n"
    b"ImageQualityRate=1\n"
    b"SamplerQuality=Bilinear\n"
    b"ShadowQuality=LOWEST\n"
    b"VRSSetting=Off\n"
    b"VSync=true\n"
)

# Dragon's Dogma 2, appid 2054970, config.ini: [AppOption] trimmed (TargetDisplay, a display
# device name, is left out). FSR3=Balanced and DLSS=None are decoys next to the real knobs.
DD2_INI = (
    b"[AppOption]\n"
    b"AntiAliasing=TAA\n"
    b"DLSS=None\n"
    b"FSR3=Balanced\n"
    b"FSR3_FrameGeneraion=OFF\n"
    b"FrameRate=Max60\n"
    b"ImageQualityRate=5\n"
    b"MeshQuality=LOW\n"
    b"RefreshRate=60.00Hz\n"
    b"Resolution=1280x800\n"
    b"ShadowQuality=Low\n"
    b"StreamingTextureQuality=High\n"
    b"TextureQuality=High\n"
    b"TextureQualityAndStreamingTextureBufferSize=High__00_25\n"
    b"UpscalingAlgorithm=FSR3\n"
    b"UpscalingQuality=Balanced\n"
    b"UpscalingSharpness=7\n"
    b"VSync=ON\n"
)

# DRAGON BALL: Sparking! ZERO, appid 1790600, GameUserSettings.ini, [ScalabilityGroups].
SPARKING_GUS = (
    b"[ScalabilityGroups]\r\n"
    b"sg.ResolutionQuality=100\r\n"
    b"sg.ViewDistanceQuality=1\r\n"
    b"sg.AntiAliasingQuality=3\r\n"
    b"sg.ShadowQuality=1\r\n"
    b"sg.GlobalIlluminationQuality=3\r\n"
    b"sg.ReflectionQuality=3\r\n"
    b"sg.PostProcessQuality=1\r\n"
    b"sg.TextureQuality=3\r\n"
    b"sg.EffectsQuality=1\r\n"
    b"sg.FoliageQuality=3\r\n"
    b"sg.ShadingQuality=3\r\n"
    b"\r\n"
)

# REMATCH, appid 2138720, GameUserSettings.ini, [ScalabilityGroups].
REMATCH_GUS = b"[ScalabilityGroups]\r\nsg.ResolutionQuality=87\r\nsg.ShadingQuality=0\r\n\r\n"

# Hand-computed from the text above.
WILDS_KNOBS = {
    ("Graphics", "Algorithm"): "FSR3",
    ("Graphics", "AlgorithmFG"): "NONE",
    ("Graphics", "Quality"): "Balanced",
    ("Graphics/FSR3", "Sharpness"): "0.65",
    ("Graphics", "AntiAliasing"): "NONE",
    ("Graphics", "ImageQualityRate"): "1",
    ("Graphics/RayTracing", "Enable"): "False",
    ("Graphics", "StreamingTextureQuality"): "HIGH",
    ("Graphics", "SamplerQuality"): "Bilinear",
    ("Graphics", "UseLowShellFur"): "False",
    ("Graphics", "SpeedTreeWind_Branch"): "0",
    ("Graphics", "SpeedTreeWind_Global"): "0",
    ("Graphics", "SpeedTreeWind_Leaf"): "0",
    ("Graphics", "GrassPushCollision"): "False",
    ("Graphics", "WindSimulationQuality"): "OFF",
    ("Graphics", "GroundQuality"): "HIGH",
    ("Graphics", "UseLowWaterSimulation"): "True",
    ("Graphics", "ShadowQuality"): "LOWEST",
    ("Graphics", "ShadowCastDistanceType"): "MIDDLE",
    ("Graphics", "GIQuality"): "LOW",
    ("Graphics", "ContactShadowSetting"): "OFF",
    ("Graphics", "Bloom_Enable"): "True",
    ("Graphics", "Bloom_ReductionLevel"): "2",
    ("Graphics", "MotionBlur_Enable"): "True",
    ("Graphics", "SSR_Enable"): "False",
    ("Graphics", "SSSSS_Enable"): "False",
    ("Graphics", "DOF_Enable"): "True",
    ("Graphics", "VolumetricFogControl_Enable"): "True",
    ("Graphics", "VolumetricFogControl_TextureSize"): "W54xH30xD32",
    ("Graphics", "VRSSetting"): "Off",
}
# docs/research/wilds-settings-map.md rows marked "matched"; every other knob is "likely".
WILDS_MATCHED = {
    ("Graphics", "Algorithm"),
    ("Graphics", "AlgorithmFG"),
    ("Graphics", "Quality"),
    ("Graphics/FSR3", "Sharpness"),
    ("Graphics", "SamplerQuality"),
    ("Graphics", "WindSimulationQuality"),
    ("Graphics", "ShadowQuality"),
    ("Graphics", "ContactShadowSetting"),
    ("Graphics", "MotionBlur_Enable"),
    ("Graphics", "SSR_Enable"),
    ("Graphics", "SSSSS_Enable"),
    ("Graphics", "DOF_Enable"),
    ("Graphics", "VRSSetting"),
}
# Values seen in another of Fede's files, per the research doc (frame generation on).
WILDS_ALSO_SEEN = {("Graphics", "AlgorithmFG"): {"FSR3"}}

# Answer 5: key -> (type, values or None for number, value in Fede's file).
DD2_KNOBS = {
    "UpscalingAlgorithm": ("enum", ["FSR3"], "FSR3"),
    "UpscalingQuality": ("enum", ["Balanced"], "Balanced"),
    "UpscalingSharpness": ("number", None, "7"),
    "FSR3_FrameGeneraion": ("bool", ["OFF", "ON"], "OFF"),
    "TextureQuality": ("enum", ["High"], "High"),
    "ShadowQuality": ("enum", ["Low"], "Low"),
    "FrameRate": ("enum", ["Max60"], "Max60"),
    "VSync": ("bool", ["OFF", "ON"], "ON"),
}

UNREAL_LEVEL_KEYS = [
    "sg.ViewDistanceQuality",
    "sg.AntiAliasingQuality",
    "sg.ShadowQuality",
    "sg.GlobalIlluminationQuality",
    "sg.ReflectionQuality",
    "sg.PostProcessQuality",
    "sg.TextureQuality",
    "sg.EffectsQuality",
    "sg.FoliageQuality",
    "sg.ShadingQuality",
]
UNREAL_KEYS = ["sg.ResolutionQuality", *UNREAL_LEVEL_KEYS]
UNREAL_DOCUMENTED = {
    "sg.PostProcessQuality",
    "sg.ShadowQuality",
    "sg.TextureQuality",
    "sg.EffectsQuality",
}
SPARKING_VALUES = {
    "sg.ResolutionQuality": "100",
    "sg.ViewDistanceQuality": "1",
    "sg.AntiAliasingQuality": "3",
    "sg.ShadowQuality": "1",
    "sg.GlobalIlluminationQuality": "3",
    "sg.ReflectionQuality": "3",
    "sg.PostProcessQuality": "1",
    "sg.TextureQuality": "3",
    "sg.EffectsQuality": "1",
    "sg.FoliageQuality": "3",
    "sg.ShadingQuality": "3",
}
REMATCH_VALUES = {"sg.ResolutionQuality": "87", "sg.ShadingQuality": "0"}
BOOL_PAIRS = (["False", "True"], ["false", "true"], ["OFF", "ON"])

# ---------------------------------------------------------------------------- cards


def write(path: Path, data: str | bytes) -> Path:
    """test_discover_output.put, returning the path (bytes are written as given)."""
    return put(path, data)


def entry(path: Path | str, kind: str = "ini", cls: str = "I") -> dict:
    return {"path": str(path), "class": cls, "kind": kind}


def make_card(
    files=(),
    *,
    appid: int = 4000,
    name: str = "Test Game",
    engine: str = "unknown",
    anticheat=(),
    installed: bool = True,
    kind: str = "game",
) -> dict:
    """A card with every discover field (B4, C2-C7). `files` holds settings_files entries
    (see `entry`); they are sorted by path as C6 does."""
    return {
        "appid": appid,
        "name": name,
        "kind": kind,
        "library": "/fake/library",
        "installdir": "Game",
        "buildid": "1",
        "state_flags": 4 if installed else 1026,
        "installed": installed,
        "install_path": "/fake/library/steamapps/common/Game",
        "prefix_path": None,
        "shadercache_path": None,
        "compat_tool": None,
        "warnings": [],
        "engine": engine,
        "engine_evidence": [],
        "anticheat": [dict(item) for item in anticheat],
        "tier_i_eligible": False,
        "upscalers": [],
        "injectors": [],
        "settings_files": sorted((dict(item) for item in files), key=lambda e: e["path"]),
    }


# ---------------------------------------------------------------------------- maps


def knob(
    knob_id: str,
    key: str,
    knob_type: str = "enum",
    *,
    section: str = "S",
    values=("a", "b"),
    **extra,
) -> dict:
    result = {
        "id": knob_id,
        "label": f"Label {knob_id}",
        "section": section,
        "key": key,
        "type": knob_type,
        "confidence": "likely",
        "source": "test note",
    }
    if knob_type in ("level", "enum", "bool"):
        result["values"] = list(values)
    result.update(extra)
    return result


def make_map(
    map_id: str = "test-map",
    *,
    file_name: str = "test.ini",
    sections=("S",),
    keys=(),
    knobs=(),
) -> dict:
    return {
        "id": map_id,
        "engine": "test",
        "label": f"Map {map_id}",
        "match": {
            "file_name": file_name,
            "sections": list(sections),
            "keys": [list(pair) for pair in keys],
        },
        "knobs": [dict(item) for item in knobs],
    }


# ---------------------------------------------------------------------------- reports


def entries_for(report: dict, map_id: str) -> list[dict]:
    return [item for item in report["maps"] if item["map_id"] == map_id]


def only_entry(report: dict, map_id: str) -> dict:
    found = entries_for(report, map_id)
    assert len(found) == 1, f"expected one {map_id} entry, got {len(found)}"
    return found[0]


def by_key(map_entry: dict) -> dict[tuple[str, str], dict]:
    knobs = {(k["section"], k["key"]): k for k in map_entry["knobs"]}
    assert len(knobs) == len(map_entry["knobs"]), "two knobs read the same key"
    return knobs


def unmapped_paths(report: dict) -> list[str]:
    """unmapped_files entries, as paths. The spec does not give the entry shape: a path
    string, or an object with a "path" key, are both read."""
    paths = []
    for item in report["unmapped_files"]:
        paths.append(item if isinstance(item, str) else item["path"])
    return paths


def issue_pairs(report: dict) -> list[tuple[str, str | None]]:
    return sorted((issue["code"], issue["path"]) for issue in report["issues"])


def issues_of(report: dict, code: str) -> list[dict]:
    return [issue for issue in report["issues"] if issue["code"] == code]


def as_pairs(duplicates) -> list[list[str]]:
    return [list(pair) for pair in duplicates]


def builtin_map(maps: list[dict], map_id: str) -> dict:
    found = [m for m in maps if m["id"] == map_id]
    assert len(found) == 1
    return found[0]


def map_knob(map_dict: dict, section: str, key: str) -> dict:
    found = [k for k in map_dict["knobs"] if k["section"] == section and k["key"] == key]
    assert len(found) == 1, f"{map_dict['id']}: {len(found)} knobs for [{section}] {key}"
    return found[0]


# ---------------------------------------------------------------------------- Steam tree

WILDS, DD2, SPARKING, REMATCH = 2246340, 2054970, 1790600, 2138720
AC_GAME = 3000001  # Unreal, EasyAntiCheat folder, unknown values
UNITY_GAME = 1061090  # boot.config + user.reg
PLAIN = 70  # unknown engine, no settings files
BIG = 2050650  # RE Engine, config.ini of 1 MiB + 1 byte
PENDING = 883710  # RE Engine, StateFlags 1026: installed false
PROTON = 2805730  # kind "tool" (name matches ^Proton( |$)), installed (item 19)
RUNTIME = 1628350  # kind "tool" (Steam Linux Runtime), installed (item 19)

NAMES = {
    WILDS: "Monster Hunter Wilds",
    DD2: "Dragon's Dogma 2",
    SPARKING: "DRAGON BALL: Sparking! ZERO",
    REMATCH: "REMATCH",
    AC_GAME: "Anti-Cheat UE Game",
    UNITY_GAME: "Unity Test Game",
    PLAIN: "Plain Game",
    BIG: "Big Config Game",
    PENDING: "Pending Update Game",
    PROTON: "Proton 9.0",
    RUNTIME: "Steam Linux Runtime 3.0 (sniper)",
}
TREE_STATUS = {
    PLAIN: "no_map",
    UNITY_GAME: "no_map",
    SPARKING: "mapped",
    BIG: "unreadable",
    DD2: "mapped",
    REMATCH: "mapped",
    WILDS: "mapped",
    AC_GAME: "mapped_with_unknown_values",
}
AC_GUS = b"[ScalabilityGroups]\r\nsg.ResolutionQuality=100.000000\r\nsg.ShadowQuality=7\r\n"
AC_GUS += b"sg.TextureQuality=2\r\n"
UNREAL_CONFIG = "drive_c/users/steamuser/AppData/Local/{game}/Saved/Config/Windows"


def add_game(library: Path, appid: int, installdir: str, flags: str = "4") -> Path:
    text = manifest(str(appid), NAMES[appid], installdir)
    if flags != "4":
        text = text.replace('"StateFlags"\t\t"4"', f'"StateFlags"\t\t"{flags}"')
    put(library / "steamapps" / f"appmanifest_{appid}.acf", text)
    return mkdir(library / "steamapps" / "common" / installdir)


def prefix(library: Path, appid: int) -> Path:
    return library / "steamapps" / "compatdata" / str(appid) / "pfx"


def build_tree(base: Path) -> dict:
    """A Steam root with the four real-data games, five synthetic ones and two installed
    tools (Proton, Steam Linux Runtime; spec item 19). Returns
    {"root": Path, "files": {label: Path}}."""
    root = base / "steam"
    put(root / "steamapps" / "libraryfolders.vdf", libraryfolders([("0", str(root))]))
    put(root / "config" / "config.vdf", CONFIG_VDF)
    files: dict[str, Path] = {}

    wilds = add_game(root, WILDS, "MonsterHunterWilds")
    put(wilds / "re_chunk_000.pak", b"\0" * 16)
    files["wilds"] = put(wilds / "config.ini", WILDS_INI)

    dd2 = add_game(root, DD2, "DragonsDogma2")
    put(dd2 / "re_chunk_000.pak", b"\0" * 16)
    files["dd2"] = put(dd2 / "config.ini", DD2_INI)

    for appid, installdir, game, data in [
        (SPARKING, "DRAGON BALL Sparking! ZERO", "SparkingZERO", SPARKING_GUS),
        (REMATCH, "REMATCH", "Rematch", REMATCH_GUS),
        (AC_GAME, "AntiCheatGame", "ACGame", AC_GUS),
    ]:
        install = add_game(root, appid, installdir)
        put(install / game / "Binaries" / "Win64" / f"{game}-Win64-Shipping.exe", b"MZ")
        config = prefix(root, appid) / UNREAL_CONFIG.format(game=game)
        files[f"{appid}_gus"] = put(config / "GameUserSettings.ini", data)
    files["sparking_engine"] = put(
        prefix(root, SPARKING) / UNREAL_CONFIG.format(game="SparkingZERO") / "Engine.ini",
        b"[Core.System]\r\nPaths=../../../Engine/Content\r\n+Paths=%GAMEDIR%Content\r\n",
    )
    mkdir(root / "steamapps" / "common" / "AntiCheatGame" / "EasyAntiCheat")

    unity = add_game(root, UNITY_GAME, "UnityGame")
    put(unity / "UnityPlayer.dll", b"MZ")
    files["unity_boot"] = put(unity / "Game_Data" / "boot.config", b"gfx-enable-gfx-jobs=1\n")
    files["unity_reg"] = put(prefix(root, UNITY_GAME) / "user.reg", b"WINE REGISTRY Version 2\n")

    add_game(root, PLAIN, "PlainGame")

    big = add_game(root, BIG, "BigGame")
    put(big / "re_chunk_000.pak", b"\0")
    files["big"] = sized(big / "config.ini", MiB + 1)

    pending = add_game(root, PENDING, "PendingGame", flags="1026")
    put(pending / "re_chunk_000.pak", b"\0")
    files["pending"] = put(pending / "config.ini", WILDS_INI)

    add_game(root, PROTON, "Proton 9.0")
    add_game(root, RUNTIME, "SteamLinuxRuntime_sniper")
    return {"root": root, "files": files}


def sized(path: Path, size: int, head: bytes = b"[Graphics]\nShaderConvertVersion=1\n") -> Path:
    """A file of exactly `size` bytes: `head`, then one long comment line."""
    assert size > len(head) + 1
    return put(path, head + b";" * (size - len(head) - 1) + b"\n")


# ---------------------------------------------------------------------------- package copy


def copy_package(base: Path, maps: dict[str, object] | None) -> Path:
    """A copy of src/deckforge under base/pkg, with `maps` as its maps folder (file name ->
    JSON-able object or raw str). maps=None leaves the folder out. Answer 9 says maps are
    found by path next to settings.py, so the copy loads these maps and not the shipped
    ones. Returns the folder to put on sys.path."""
    pkg = base / "pkg"
    shutil.copytree(
        PACKAGE, pkg / "deckforge", ignore=shutil.ignore_patterns("__pycache__", "maps")
    )
    if maps is not None:
        folder = mkdir(pkg / "deckforge" / "maps")
        for name, content in maps.items():
            text = content if isinstance(content, str) else json.dumps(content, indent=2)
            put(folder / name, text)
    return pkg


LOAD_MAPS_CODE = """
import json, sys
sys.path.insert(0, sys.argv[1])
from deckforge import settings
out = {"file": settings.__file__}
try:
    out["ids"] = [m["id"] for m in settings.load_maps()]
except settings.SettingsError as exc:
    out["error"] = str(exc)
print(json.dumps(out))
"""

MAIN_CODE = """
import sys
sys.path.insert(0, sys.argv[1])
from deckforge import settings
raise SystemExit(settings.main(sys.argv[2:]))
"""


def python(code: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-I", "-B", "-c", code, *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def load_maps_in(pkg: Path, cwd: Path) -> dict:
    """Run load_maps from the copied package; {"file", "ids"} or {"file", "error"}."""
    done = python(LOAD_MAPS_CODE, [str(pkg)], cwd)
    assert done.returncode == 0, done.stderr
    result = json.loads(done.stdout)
    assert Path(result["file"]).resolve() == (pkg / "deckforge" / "settings.py").resolve()
    return result


def main_in(pkg: Path, args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return python(MAIN_CODE, [str(pkg), *args], cwd)


def minimal_root(base: Path) -> Path:
    """A Steam root with one Unreal game whose GameUserSettings.ini is real data."""
    root = base / "steam"
    put(root / "steamapps" / "libraryfolders.vdf", libraryfolders([("0", str(root))]))
    put(root / "config" / "config.vdf", CONFIG_VDF)
    install = add_game(root, REMATCH, "REMATCH")
    put(install / "Rematch" / "Binaries" / "Win64" / "Rematch-Win64-Shipping.exe", b"MZ")
    config = prefix(root, REMATCH) / UNREAL_CONFIG.format(game="Rematch")
    put(config / "GameUserSettings.ini", REMATCH_GUS)
    return root


# ---------------------------------------------------------------------------- FIFO guard


def unblock_fifo(path: Path, done: threading.Event) -> None:
    """If a reader opened the FIFO and waits, give it an INI so it returns (and the test
    fails on the missing SettingsError instead of hanging)."""
    while not done.wait(0.2):
        try:
            fd = os.open(path, os.O_WRONLY | os.O_NONBLOCK)
        except OSError:
            continue
        try:
            os.write(fd, b"[S]\nk=v\n")
        finally:
            os.close(fd)
        return
