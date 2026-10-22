# Contracts for PR B2 of docs/specs/discover.md, criteria C2 (engine), C3 (anti-cheat), C4
# (upscalers) and C5 (injectors). Written test-first: the cards from
# deckforge.discover.scan do not have the B2 fields yet. Observed through discover.scan; the
# walk itself (depth 10 for the install folder, depth 6 for the prefix) is C1, in
# test_detect_walks.py. Every name below is compared ignoring case; evidence is the
# relative path with the on-disk case.
#
# engine and engine_evidence, criterion C2 (install walk)
#   unreal     a file named *-win64-shipping.exe or *-wingdk-shipping.exe directly inside
#              Binaries/Win64 or Binaries/WinGDK, at any depth the walk reaches
#   unity      UnityPlayer.dll at the install root or one level below; or a *_Data folder at
#              the root or one level below that contains globalgamemanagers or boot.config
#   re_engine  re_chunk_000.pak at the install root
#   Post: engine is the single engine matched; "unknown" when none matches; "ambiguous"
#         when more than one does. engine_evidence is the sorted list of every matched
#         relative path, merged across engines for "ambiguous". For the *_Data rule the
#         spec does not say whether the folder or the file inside it is the evidence; the
#         tests accept either one.
#
# anticheat, criterion C3
#   Post: a list of {"system", "evidence"}, one entry per system, sorted by system, each
#         evidence list sorted. File or folder names anywhere in the install walk:
#           easyanticheat  starts with easyanticheat, or is start_protected_game.exe
#           battleye       is battleye, or starts with beservice or beclient
#           gameguard      is gameguard
#   Post: <prefix>/drive_c/Program Files and <prefix>/drive_c/Program Files (x86) are also
#         walked, for the easyanticheat and battleye signatures only, with evidence
#         "pfx/<relative path>". Relative to the prefix or to the start folder is not
#         settled by the spec; the tests accept both. No other prefix folder is used.
#   Post: CURATED_ANTICHEAT (2183900 easyanticheat, 553850 gameguard) adds the evidence
#         item "(curated)" to that system, merged with any file evidence, also when the
#         game is not installed.
#
# upscalers, criterion C4
#   Post: a list of {"name", "evidence"} sorted by name, from these file names anywhere in
#         the install walk: nvngx_dlss.dll dlss, nvngx_dlssg.dll dlss_fg,
#         amd_fidelityfx_dx12.dll and amd_fidelityfx_vk.dll ffx_sdk,
#         ffx_fsr2_api_x64.dll fsr2, libxess.dll xess. Other names, even close ones, add
#         nothing; an empty list is a valid result.
#
# injectors, criterion C5
#   Post: a list of {"name", "evidence"} sorted by name: optiscaler for a file named
#         OptiScaler.ini; reframework for a folder named reframework whose parent folder
#         also contains dinput8.dll (evidence = the folder's relative path).
#   Post: when a card has any injector and a non-empty anticheat, each injector adds an
#         injector_with_anticheat card warning whose path is its evidence path; with
#         either list empty there is no such warning.
#
# Round trip: no write or restore path in B2; see test_detect_walks.py for the read-only
# property that replaces it.

import os

import pytest

from deckforge import discover

APPID = 1086940
D7 = "/".join(f"d{n}" for n in range(1, 8))  # seven folders, then Binaries/Win64/<exe>
UNREAL_EXE = "Game/Binaries/Win64/Game-Win64-Shipping.exe"
PROGRAM_FILES = "drive_c/Program Files"
PROGRAM_FILES_X86 = "drive_c/Program Files (x86)"


# ---------------------------------------------------------------------------- helpers


def q(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def manifest(appid: int, name: str, flags: str) -> bytes:
    return (
        f'"AppState"\n{{\n\t"appid"\t\t"{appid}"\n\t"name"\t\t{q(name)}\n'
        f'\t"StateFlags"\t\t"{flags}"\n\t"installdir"\t\t"Game"\n\t"buildid"\t\t"1"\n}}\n'
    ).encode()


def put(path, data: bytes = b""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def plant(base, entries) -> None:
    """Create each relative entry under base: a trailing "/" makes a folder, else an empty file."""
    for rel in entries:
        if rel.endswith("/"):
            (base / rel).mkdir(parents=True, exist_ok=True)
        else:
            put(base / rel)


def game(tmp_path, install=(), prefix=None, *, appid=APPID, flags="4") -> dict:
    """Scan a Steam root holding one game. install=None leaves out the install folder and
    prefix=None leaves out the prefix."""
    root = tmp_path / "steam"
    steamapps = root / "steamapps"
    vdf = f'"libraryfolders"\n{{\n\t"0"\n\t{{\n\t\t"path"\t\t{q(str(root))}\n\t}}\n}}\n'
    put(steamapps / "libraryfolders.vdf", vdf.encode())
    put(steamapps / f"appmanifest_{appid}.acf", manifest(appid, "Test Game", flags))
    if install is not None:
        (steamapps / "common" / "Game").mkdir(parents=True)
        plant(steamapps / "common" / "Game", install)
    if prefix is not None:
        (steamapps / "compatdata" / str(appid) / "pfx").mkdir(parents=True)
        plant(steamapps / "compatdata" / str(appid) / "pfx", prefix)
    found = [card for card in discover.scan(str(root))["games"] if card["appid"] == appid]
    assert len(found) == 1
    return found[0]


def paths_of(card: dict, code: str) -> list:
    return [issue["path"] for issue in card["warnings"] if issue["code"] == code]


def pfx_forms(start: str, rel: str) -> set[str]:
    """Both readings of "pfx/<relative path>" (relative to the prefix or to the start)."""
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


def ac(system: str, *evidence: str) -> dict:
    return {"system": system, "evidence": list(evidence)}


def item(name: str, *evidence: str) -> dict:
    return {"name": name, "evidence": list(evidence)}


# ---------------------------------------------------------------------------- C2 engine

ENGINE_CASES = {
    # Unreal: shipping executable directly inside Binaries/Win64 or Binaries/WinGDK.
    "unreal-win64": ([UNREAL_EXE], "unreal", [[UNREAL_EXE]]),
    "unreal-wingdk": (
        ["Game/Binaries/WinGDK/Game-WinGDK-Shipping.exe"],
        "unreal",
        [["Game/Binaries/WinGDK/Game-WinGDK-Shipping.exe"]],
    ),
    "unreal-any-case": (
        ["game/binaries/WIN64/GAME-win64-SHIPPING.EXE"],
        "unreal",
        [["game/binaries/WIN64/GAME-win64-SHIPPING.EXE"]],
    ),
    "unreal-binaries-at-root": (
        ["Binaries/Win64/X-Win64-Shipping.exe"],
        "unreal",
        [["Binaries/Win64/X-Win64-Shipping.exe"]],
    ),
    "unreal-at-depth-10": (
        [f"{D7}/Binaries/Win64/X-Win64-Shipping.exe"],
        "unreal",
        [[f"{D7}/Binaries/Win64/X-Win64-Shipping.exe"]],
    ),
    "unreal-two-executables": (
        ["B/Binaries/Win64/B-Win64-Shipping.exe", "A/Binaries/WinGDK/A-WinGDK-Shipping.exe"],
        "unreal",
        [["A/Binaries/WinGDK/A-WinGDK-Shipping.exe", "B/Binaries/Win64/B-Win64-Shipping.exe"]],
    ),
    # Unity: UnityPlayer.dll, or a *_Data folder holding a marker, at depth 1 or 2.
    "unity-player-at-root": (["UnityPlayer.dll"], "unity", [["UnityPlayer.dll"]]),
    "unity-player-any-case": (["unityplayer.DLL"], "unity", [["unityplayer.DLL"]]),
    "unity-player-one-below": (["Bin/UnityPlayer.dll"], "unity", [["Bin/UnityPlayer.dll"]]),
    "unity-data-globalgamemanagers": (
        ["Game_Data/globalgamemanagers", "Game_Data/level0"],
        "unity",
        [["Game_Data"], ["Game_Data/globalgamemanagers"]],
    ),
    "unity-data-boot-config": (
        ["Game_Data/boot.config"],
        "unity",
        [["Game_Data"], ["Game_Data/boot.config"]],
    ),
    "unity-data-one-below": (
        ["Sub/Game_Data/globalgamemanagers"],
        "unity",
        [["Sub/Game_Data"], ["Sub/Game_Data/globalgamemanagers"]],
    ),
    "unity-data-any-case": (
        ["GAME_DATA/GlobalGameManagers"],
        "unity",
        [["GAME_DATA"], ["GAME_DATA/GlobalGameManagers"]],
    ),
    # RE Engine: re_chunk_000.pak at the install root.
    "re-engine": (["re_chunk_000.pak", "natives/x64/a.pak"], "re_engine", [["re_chunk_000.pak"]]),
    "re-engine-any-case": (["RE_CHUNK_000.PAK"], "re_engine", [["RE_CHUNK_000.PAK"]]),
    # Nothing matches.
    "unknown-empty": ([], "unknown", [[]]),
    "unknown-other-files": (["Game.exe", "readme.txt", "Data/"], "unknown", [[]]),
    "unknown-shipping-exe-not-in-win64": (
        ["Game/Binaries/Game-Win64-Shipping.exe"],
        "unknown",
        [[]],
    ),
    "unknown-win64-not-in-binaries": (["Game/Bin/Win64/Game-Win64-Shipping.exe"], "unknown", [[]]),
    "unknown-win64-not-directly-in-binaries": (
        ["Game/Binaries/Other/Win64/Game-Win64-Shipping.exe"],
        "unknown",
        [[]],
    ),
    "unknown-shipping-exe-below-win64": (
        ["Game/Binaries/Win64/sub/Game-Win64-Shipping.exe"],
        "unknown",
        [[]],
    ),
    "unknown-win32": (["Game/Binaries/Win32/Game-Win64-Shipping.exe"], "unknown", [[]]),
    "unknown-not-shipping": (["Game/Binaries/Win64/Game-Win64-Test.exe"], "unknown", [[]]),
    "unknown-shipping-exe-at-root": (["Game-Win64-Shipping.exe"], "unknown", [[]]),
    "unknown-shipping-exe-is-a-folder": (
        ["Game/Binaries/Win64/Game-Win64-Shipping.exe/"],
        "unknown",
        [[]],
    ),
    "unknown-unreal-beyond-depth-10": (
        [f"{D7}/d8/Binaries/Win64/X-Win64-Shipping.exe"],
        "unknown",
        [[]],
    ),
    "unknown-unity-player-two-below": (["a/b/UnityPlayer.dll"], "unknown", [[]]),
    "unknown-unity-data-two-below": (["a/b/Game_Data/globalgamemanagers"], "unknown", [[]]),
    "unknown-unity-data-without-marker": (["Game_Data/level0"], "unknown", [[]]),
    "unknown-data-folder-without-underscore": (["GameData/globalgamemanagers"], "unknown", [[]]),
    "unknown-re-chunk-below-root": (["natives/re_chunk_000.pak"], "unknown", [[]]),
    "unknown-re-chunk-patch": (["re_chunk_000.pak.patch_001.pak"], "unknown", [[]]),
    # More than one engine.
    "ambiguous-re-and-unity": (
        ["re_chunk_000.pak", "UnityPlayer.dll"],
        "ambiguous",
        [["UnityPlayer.dll", "re_chunk_000.pak"]],
    ),
    "ambiguous-all-three": (
        ["re_chunk_000.pak", "Bin/UnityPlayer.dll", UNREAL_EXE],
        "ambiguous",
        [sorted(["re_chunk_000.pak", "Bin/UnityPlayer.dll", UNREAL_EXE])],
    ),
}


@pytest.mark.parametrize(("entries", "engine", "evidence"), ENGINE_CASES.values(), ids=ENGINE_CASES)
def test_c2_engine_and_sorted_evidence(tmp_path, entries, engine, evidence):
    card = game(tmp_path, entries)
    assert card["engine"] == engine
    assert card["engine_evidence"] in evidence


def test_c2_evidence_is_sorted_whatever_the_listing_order(tmp_path, monkeypatch):
    list_in_reverse(monkeypatch)
    entries = ["c/Binaries/Win64/C-Win64-Shipping.exe", "re_chunk_000.pak", "A/UnityPlayer.dll"]
    card = game(tmp_path, entries)
    assert card["engine"] == "ambiguous"
    assert card["engine_evidence"] == sorted(entries)


# ---------------------------------------------------------------------------- C3 anti-cheat

ANTICHEAT_HITS = {
    "eac-folder": (["EasyAntiCheat/"], [ac("easyanticheat", "EasyAntiCheat")]),
    "eac-folder-and-a-file-inside": (
        ["EasyAntiCheat/EasyAntiCheat_x64.dll", "EasyAntiCheat/Settings.json"],
        [ac("easyanticheat", "EasyAntiCheat", "EasyAntiCheat/EasyAntiCheat_x64.dll")],
    ),
    "eac-eos-setup": (
        ["EasyAntiCheat_EOS_Setup.exe"],
        [ac("easyanticheat", "EasyAntiCheat_EOS_Setup.exe")],
    ),
    "eac-deep-lower-case": (
        ["Engine/Binaries/ThirdParty/EOS/easyanticheat_x64.dll"],
        [ac("easyanticheat", "Engine/Binaries/ThirdParty/EOS/easyanticheat_x64.dll")],
    ),
    "eac-launcher": (
        ["start_protected_game.exe"],
        [ac("easyanticheat", "start_protected_game.exe")],
    ),
    "eac-launcher-any-case": (
        ["bin/Start_Protected_Game.EXE"],
        [ac("easyanticheat", "bin/Start_Protected_Game.EXE")],
    ),
    "battleye-folder": (["BattlEye/"], [ac("battleye", "BattlEye")]),
    "battleye-file-lower-case": (["battleye"], [ac("battleye", "battleye")]),
    "beservice": (["BEService_x64.exe"], [ac("battleye", "BEService_x64.exe")]),
    "beservice-lower-case-deep": (["bin/x/beservice.exe"], [ac("battleye", "bin/x/beservice.exe")]),
    "beclient-inside-battleye": (
        ["BattlEye/BEClient_x64.dll"],
        [ac("battleye", "BattlEye", "BattlEye/BEClient_x64.dll")],
    ),
    "gameguard-folder": (["GameGuard/GameGuard.des"], [ac("gameguard", "GameGuard")]),
    "gameguard-file-upper-case": (["bin/GAMEGUARD"], [ac("gameguard", "bin/GAMEGUARD")]),
}


@pytest.mark.parametrize(("entries", "expected"), ANTICHEAT_HITS.values(), ids=ANTICHEAT_HITS)
def test_c3_install_signatures(tmp_path, entries, expected):
    assert game(tmp_path, entries)["anticheat"] == expected


ANTICHEAT_MISSES = [
    "my_easyanticheat.dll",
    "EAC/eac_launcher.exe",
    "start_protected_game.exe.bak",
    "BattlEyeLauncher.exe",
    "BEDaisy.sys",
    "GameGuard.des",
    "NotGameGuard/",
    "nProtect/",
]


@pytest.mark.parametrize("entry", ANTICHEAT_MISSES)
def test_c3_names_close_to_a_signature_do_not_match(tmp_path, entry):
    assert game(tmp_path, [entry])["anticheat"] == []


def test_c3_systems_and_evidence_are_sorted(tmp_path, monkeypatch):
    list_in_reverse(monkeypatch)
    card = game(
        tmp_path,
        [
            "GameGuard/",
            "BattlEye/",
            "a/easyanticheat.sys",
            "Z/EasyAntiCheat_x64.dll",
            "EasyAntiCheat/",
        ],
    )
    assert card["anticheat"] == [
        ac("battleye", "BattlEye"),
        ac(
            "easyanticheat",
            *sorted(["EasyAntiCheat", "Z/EasyAntiCheat_x64.dll", "a/easyanticheat.sys"]),
        ),
        ac("gameguard", "GameGuard"),
    ]


PREFIX_HITS = {
    "eac-in-program-files-x86": (
        [f"{PROGRAM_FILES_X86}/EasyAntiCheat_EOS/"],
        "easyanticheat",
        pfx_forms(PROGRAM_FILES_X86, "EasyAntiCheat_EOS"),
    ),
    "eac-launcher-in-program-files": (
        [f"{PROGRAM_FILES}/Game/start_protected_game.exe"],
        "easyanticheat",
        pfx_forms(PROGRAM_FILES, "Game/start_protected_game.exe"),
    ),
    "battleye-in-program-files": (
        [f"{PROGRAM_FILES}/Common Files/BattlEye/"],
        "battleye",
        pfx_forms(PROGRAM_FILES, "Common Files/BattlEye"),
    ),
    "beservice-in-program-files-x86": (
        [f"{PROGRAM_FILES_X86}/Game/BEService.exe"],
        "battleye",
        pfx_forms(PROGRAM_FILES_X86, "Game/BEService.exe"),
    ),
}


@pytest.mark.parametrize(("entries", "system", "forms"), PREFIX_HITS.values(), ids=PREFIX_HITS)
def test_c3_prefix_program_files_signatures_have_pfx_evidence(tmp_path, entries, system, forms):
    [found] = game(tmp_path, [], entries)["anticheat"]
    assert found["system"] == system
    [evidence] = found["evidence"]
    assert evidence in forms


PREFIX_MISSES = [
    f"{PROGRAM_FILES}/GameGuard/",  # gameguard is an install-only signature
    "drive_c/windows/EasyAntiCheat/",
    "drive_c/ProgramData/BattlEye/",
    "drive_c/users/steamuser/AppData/Local/EasyAntiCheat/",
    "EasyAntiCheat/",
]


@pytest.mark.parametrize("entry", PREFIX_MISSES)
def test_c3_prefix_is_searched_only_in_program_files_for_eac_and_battleye(tmp_path, entry):
    assert game(tmp_path, [], [entry])["anticheat"] == []


def test_c3_install_and_prefix_evidence_merge_into_one_system(tmp_path):
    card = game(tmp_path, ["EasyAntiCheat/"], [f"{PROGRAM_FILES_X86}/EasyAntiCheat_EOS/"])
    [found] = card["anticheat"]
    assert found["system"] == "easyanticheat"
    assert len(found["evidence"]) == 2
    assert found["evidence"][0] == "EasyAntiCheat"
    assert found["evidence"][1] in pfx_forms(PROGRAM_FILES_X86, "EasyAntiCheat_EOS")


CURATED_CASES = {
    "eac-curated-only": (2183900, [], None, [ac("easyanticheat", "(curated)")]),
    "gameguard-curated-only": (553850, [], None, [ac("gameguard", "(curated)")]),
    "eac-curated-merged-with-files": (
        2183900,
        ["EasyAntiCheat/"],
        None,
        [ac("easyanticheat", "(curated)", "EasyAntiCheat")],
    ),
    "gameguard-curated-merged-with-files": (
        553850,
        ["GameGuard/"],
        None,
        [ac("gameguard", "(curated)", "GameGuard")],
    ),
    "curated-next-to-another-system": (
        553850,
        ["BattlEye/"],
        None,
        [ac("battleye", "BattlEye"), ac("gameguard", "(curated)")],
    ),
    "curated-not-installed-folder-present": (
        2183900,
        [],
        "2",
        [ac("easyanticheat", "(curated)")],
    ),
    "curated-not-installed-folder-missing": (
        2183900,
        None,
        "2",
        [ac("easyanticheat", "(curated)")],
    ),
}


@pytest.mark.parametrize(
    ("appid", "entries", "flags", "expected"), CURATED_CASES.values(), ids=CURATED_CASES
)
def test_c3_curated_entries_add_curated_evidence(tmp_path, appid, entries, flags, expected):
    card = game(tmp_path, entries, appid=appid, flags=flags or "4")
    assert card["anticheat"] == expected
    if flags == "2":
        assert card["installed"] is False


def test_c3_curated_evidence_merges_with_prefix_evidence(tmp_path):
    card = game(tmp_path, [], [f"{PROGRAM_FILES_X86}/EasyAntiCheat_EOS/"], appid=2183900)
    [found] = card["anticheat"]
    assert found["system"] == "easyanticheat"
    assert found["evidence"][0] == "(curated)"
    assert len(found["evidence"]) == 2
    assert found["evidence"][1] in pfx_forms(PROGRAM_FILES_X86, "EasyAntiCheat_EOS")


def test_c3_no_anticheat_is_an_empty_list(tmp_path):
    assert game(tmp_path, ["Game.exe"], [f"{PROGRAM_FILES}/Common Files/"])["anticheat"] == []


# ---------------------------------------------------------------------------- C4 upscalers

UPSCALER_FILES = [
    ("nvngx_dlss.dll", "dlss"),
    ("nvngx_dlssg.dll", "dlss_fg"),
    ("amd_fidelityfx_dx12.dll", "ffx_sdk"),
    ("amd_fidelityfx_vk.dll", "ffx_sdk"),
    ("ffx_fsr2_api_x64.dll", "fsr2"),
    ("libxess.dll", "xess"),
    ("NVNGX_DLSS.DLL", "dlss"),
    ("LibXeSS.dll", "xess"),
]


@pytest.mark.parametrize(("filename", "name"), UPSCALER_FILES)
def test_c4_each_upscaler_file(tmp_path, filename, name):
    rel = f"Game/Binaries/Win64/{filename}"
    assert game(tmp_path, [rel])["upscalers"] == [item(name, rel)]


def test_c4_upscalers_are_sorted_by_name_with_sorted_evidence(tmp_path, monkeypatch):
    list_in_reverse(monkeypatch)
    card = game(
        tmp_path,
        [
            "libxess.dll",
            "Game/Binaries/Win64/nvngx_dlss.dll",
            "Engine/Plugins/DLSS/nvngx_dlss.dll",
            "Engine/Plugins/DLSS/nvngx_dlssg.dll",
            "amd_fidelityfx_vk.dll",
            "bin/amd_fidelityfx_dx12.dll",
            "ffx_fsr2_api_x64.dll",
        ],
    )
    assert card["upscalers"] == [
        item("dlss", "Engine/Plugins/DLSS/nvngx_dlss.dll", "Game/Binaries/Win64/nvngx_dlss.dll"),
        item("dlss_fg", "Engine/Plugins/DLSS/nvngx_dlssg.dll"),
        item("ffx_sdk", "amd_fidelityfx_vk.dll", "bin/amd_fidelityfx_dx12.dll"),
        item("fsr2", "ffx_fsr2_api_x64.dll"),
        item("xess", "libxess.dll"),
    ]


def test_c4_other_names_add_nothing(tmp_path):
    entries = [
        "nvngx_dlssd.dll",
        "nvngx_dlss.dll.bak",
        "sl.dlss_g.dll",
        "amd_fidelityfx_dx11.dll",
        "ffx_fsr2_api_dx12_x64.dll",
        "libxess_dx11.dll",
    ]
    assert game(tmp_path, entries)["upscalers"] == []


# ---------------------------------------------------------------------------- C5 injectors

INJECTOR_CASES = {
    "optiscaler-at-root": (["OptiScaler.ini"], [item("optiscaler", "OptiScaler.ini")]),
    "optiscaler-deep-any-case": (
        ["Game/Binaries/Win64/optiscaler.INI"],
        [item("optiscaler", "Game/Binaries/Win64/optiscaler.INI")],
    ),
    "reframework": (["reframework/", "dinput8.dll"], [item("reframework", "reframework")]),
    "reframework-any-case": (
        ["REFramework/plugins/", "DINPUT8.DLL"],
        [item("reframework", "REFramework")],
    ),
    "reframework-below-root": (
        ["bin/reframework/", "bin/dinput8.dll"],
        [item("reframework", "bin/reframework")],
    ),
    "both-sorted": (
        ["reframework/", "dinput8.dll", "OptiScaler.ini"],
        [item("optiscaler", "OptiScaler.ini"), item("reframework", "reframework")],
    ),
    "reframework-without-dinput8": (["reframework/autorun/"], []),
    "dinput8-inside-reframework": (["reframework/dinput8.dll"], []),
    "dinput8-in-another-folder": (["a/reframework/", "b/dinput8.dll"], []),
    "reframework-is-a-file": (["reframework", "dinput8.dll"], []),
    "optiscaler-look-alikes": (["OptiScaler.ini.bak", "OptiScaler.dll", "OptiScaler.log"], []),
}


@pytest.mark.parametrize(("entries", "expected"), INJECTOR_CASES.values(), ids=INJECTOR_CASES)
def test_c5_injectors(tmp_path, entries, expected):
    assert game(tmp_path, entries)["injectors"] == expected


WARNING_CASES = {
    "optiscaler-with-eac": ({"install": ["OptiScaler.ini", "EasyAntiCheat/"]}, ["OptiScaler.ini"]),
    "both-injectors-with-battleye": (
        {"install": ["bin/OptiScaler.ini", "reframework/", "dinput8.dll", "BattlEye/"]},
        ["bin/OptiScaler.ini", "reframework"],
    ),
    "optiscaler-with-curated-anticheat": (
        {"install": ["OptiScaler.ini"], "appid": 2183900},
        ["OptiScaler.ini"],
    ),
    "optiscaler-with-prefix-anticheat": (
        {"install": ["OptiScaler.ini"], "prefix": [f"{PROGRAM_FILES}/BattlEye/"]},
        ["OptiScaler.ini"],
    ),
    "injector-without-anticheat": ({"install": ["OptiScaler.ini"]}, []),
    "anticheat-without-injector": ({"install": ["EasyAntiCheat/"]}, []),
}


@pytest.mark.parametrize(("setup", "expected"), WARNING_CASES.values(), ids=WARNING_CASES)
def test_c5_each_injector_on_an_anticheat_card_adds_a_warning(tmp_path, setup, expected):
    card = game(tmp_path, **setup)
    assert paths_of(card, "injector_with_anticheat") == expected
