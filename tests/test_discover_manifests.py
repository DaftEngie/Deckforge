# Contracts for deckforge.discover, PR B1 of docs/specs/discover.md: criteria B3 (manifests),
# B4 (card fields), B5 (Proton version) and B6 (duplicate appids), plus the FIFO cases of
# B1, B3 and B5. Written test-first; src/deckforge/discover.py does not exist yet.
#
# Manifests, criterion B3 (scan)
#   Pre:  find_libraries succeeds (B1); only libraries with available true are scanned.
#   Post: every entry of <library>/steamapps whose name is exactly appmanifest_<x>.acf
#         (case-sensitive, nothing before or after) is considered; other names, and files
#         in sub-folders, are ignored without an issue.
#   Post: only regular files are opened; a link to a regular file is read like the file.
#         The bytes are decoded as strict UTF-8 after one leading BOM is stripped.
#   Post: a manifest that fails makes no card and adds exactly one top-level error whose
#         path is the manifest's full path (os.path.join of the library path string,
#         "steamapps" and the entry name):
#           manifest_unreadable        not a regular file, larger than 1 MiB, or an OS error
#           manifest_malformed         not UTF-8, VdfError, or no AppState block
#           manifest_incomplete        appid or installdir missing (found with vdf.find)
#           manifest_appid_mismatch    <x> not all digits, appid not all digits, or differ
#           manifest_unsafe_installdir installdir "", ".", "..", has / or \, or absolute
#   Post: one failing manifest never stops the others from being read.
#   Inv:  issue messages never contain file contents: text planted in a refused manifest
#         appears nowhere in the result.
#
# Card fields, criterion B4 (one card per accepted manifest). PR B2 adds more fields; these
# tests neither require nor forbid them and check only the B1 fields:
#   appid            int (never bool)
#   name             str, or None with a name_missing card warning
#   kind             "tool" if name matches ^Proton( |$) or starts with "Steam Linux
#                    Runtime" or "Steamworks Common Redistributables" (case-sensitive),
#                    else "game" (also when name is None)
#   library          the library's path string, exactly as in "libraries"
#   installdir       str, as written
#   buildid          str, or None when missing (no warning)
#   state_flags      int, or None with a stateflags_invalid card warning (missing, or not
#                    an integer)
#   installed        (state_flags & 4) != 0 and the install folder exists; False when
#                    state_flags is None
#   install_path     <library>/steamapps/common/<installdir>, always set; if that folder does
#                    not exist with that exact case, an install_folder_missing card warning
#   prefix_path      <library>/steamapps/compatdata/<appid>/pfx if a folder; else that path
#                    under the root library if a folder, with a prefix_in_other_library
#                    card warning; else None
#   shadercache_path <library>/steamapps/shadercache/<appid> if a folder, else None
#   warnings         card issues, sorted by (code, path or "")
#   Inv: every path string is os.path.join of the library path string, never resolved.
#
# compat_tool, criterion B5
#   Pre:  <root>/config/config.vdf, a regular file of at most 16 MiB, strict UTF-8.
#   Post: find(cfg, "InstallConfigStore", "Software", "Valve", "Steam", "CompatToolMapping",
#         "<appid>", "name"), so key case is ignored and repeated keys are all tried; ""
#         becomes None. The appid 0 entry (Steam's global default) is never applied.
#   Post: file or config folder missing: one top-level config_vdf_missing warning, path =
#         <root>/config/config.vdf. Unreadable or malformed: one top-level
#         config_vdf_malformed issue. Either way every compat_tool is None.
#   Inv:  nothing else from config.vdf reaches the output (it holds account data).
#
# Duplicates, criterion B6
#   Post: the same appid in two libraries keeps both cards and adds one top-level
#         duplicate_appid warning whose path is the manifest of the later card in games
#         order, i.e. sorted by (appid, library), not library order.
#
# FIFOs: opening one for reading blocks until a writer appears, so each FIFO case runs in a
# child Python with a 10 s timeout and PYTHONPATH set to this repo's src/ explicitly.
#   B1: libraryfolders.vdf is a FIFO, so scan and find_libraries raise DiscoverError.
#   B3: a FIFO named appmanifest_1.acf gives manifest_unreadable; others are still read.
#   B5: config/config.vdf is a FIFO, so config_vdf_malformed and every compat_tool is None.
#
# Issues are {"code", "path", "message"}; tests read code and path only. Card-warning paths
# are not given by the spec, so only their codes and order are checked. PR B1 has no write
# or restore path, so there is no round trip here (read-only is proven in B9).
# Unusual setups covered: look-alike names, links to files, folders and nowhere, BOM, exact
# size limits, Latin-1 and UTF-16 text, appID key case, traversal-shaped installdirs,
# SD-card libraries with prefixes on the internal drive (F7), symlinked root and library,
# wrong-case install folders, lowercase "valve", a manifest for appid 0, and FIFOs.

import builtins
import errno
import io
import json
import os
import pathlib
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from deckforge import discover

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TIMEOUT_S = 10
MIB = 1024 * 1024
MARKER = "df-planted-manifest-text-81d4"
B1_FIELDS = (
    "appid",
    "name",
    "kind",
    "library",
    "installdir",
    "buildid",
    "state_flags",
    "installed",
    "install_path",
    "prefix_path",
    "shadercache_path",
    "compat_tool",
    "warnings",
)
PLANTED = (
    "df_planted_account_c41a",
    "76561190000004242",
    "df-planted-connectcache-91b7",
    "df_planted_tool_for_absent_app",
    "df_planted_global_default",
)
MAPPING = {"0": "df_planted_global_default", "999999": "df_planted_tool_for_absent_app"}


# ---------------------------------------------------------------------------- helpers


def q(text: str) -> str:
    """A VDF quoted string, escaped the way Steam writes it."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def manifest(
    appid: str | None = "70",
    *,
    name: str | None = "Hollow Test",
    installdir: str | None = "HollowTest",
    flags: str | None = "4",
    buildid: str | None = "17436010",
    appid_key: str = "appid",
    installdir_key: str = "installdir",
) -> str:
    """An appmanifest as Steam writes it. A None field is left out."""
    fields = [
        (appid_key, appid),
        ("universe", "1"),
        ("LauncherPath", "/home/deck/.local/share/Steam/ubuntu12_32/steam"),
        ("name", name),
        ("StateFlags", flags),
        (installdir_key, installdir),
        ("LastUpdated", "1740000000"),
        ("SizeOnDisk", "1048576"),
        ("buildid", buildid),
        ("LastOwner", "76561190000000000"),
        ("BytesToDownload", "0"),
    ]
    lines = ['"AppState"', "{"]
    lines += [f"\t{q(key)}\t\t{q(value)}" for key, value in fields if value is not None]
    lines += [
        '\t"InstalledDepots"',
        "\t{",
        '\t\t"2246341"',
        "\t\t{",
        '\t\t\t"manifest"\t\t"5555555555555555555"',
        '\t\t\t"size"\t\t"1048576"',
        "\t\t}",
        "\t}",
        '\t"UserConfig"',
        "\t{",
        '\t\t"language"\t\t"english"',
        "\t}",
        "}",
    ]
    return "\n".join(lines) + "\n"


def config_vdf(mapping: dict[str, str | None], *, valve: str = "Valve", after: str = "") -> str:
    """config.vdf as Steam writes it, with planted account data around CompatToolMapping.
    A None tool name writes an entry with no name key. `after` follows the Valve block."""
    entries = ""
    for appid, name in mapping.items():
        entries += f"\t\t\t\t\t{q(appid)}\n\t\t\t\t\t{{\n"
        if name is not None:
            entries += f'\t\t\t\t\t\t"name"\t\t{q(name)}\n'
        entries += '\t\t\t\t\t\t"config"\t\t""\n\t\t\t\t\t\t"priority"\t\t"250"\n\t\t\t\t\t}\n'
    return (
        '"InstallConfigStore"\n{\n\t"Software"\n\t{\n'
        f"\t\t{q(valve)}\n\t\t{{\n"
        '\t\t\t"Steam"\n\t\t\t{\n'
        '\t\t\t\t"AutoUpdateWindowEnabled"\t\t"0"\n'
        '\t\t\t\t"Accounts"\n\t\t\t\t{\n'
        f'\t\t\t\t\t"{PLANTED[0]}"\n\t\t\t\t\t{{\n\t\t\t\t\t\t"SteamID"\t\t"{PLANTED[1]}"\n'
        "\t\t\t\t\t}\n\t\t\t\t}\n"
        '\t\t\t\t"CompatToolMapping"\n\t\t\t\t{\n' + entries + "\t\t\t\t}\n"
        f'\t\t\t\t"ConnectCache"\n\t\t\t\t{{\n\t\t\t\t\t"7d1a2c"\t\t"{PLANTED[2]}"\n\t\t\t\t}}\n'
        "\t\t\t}\n\t\t}\n" + after + "\t}\n"
        '\t"Music"\n\t{\n\t\t"CrawlSteamInstallFolders"\t\t"1"\n\t}\n'
        "}\n"
    )


def add_game(
    library: Path,
    appid: int,
    *,
    name: str | None = "",
    installdir: str = "",
    flags: str | None = "4",
    buildid: str | None = "100",
    folder: bool = True,
) -> Path:
    """A manifest in `library` and, with `folder`, its install folder; returns the manifest
    path. Empty name and installdir default to "Game <appid>" and "Game<appid>"."""
    name = f"Game {appid}" if name == "" else name
    installdir = installdir or f"Game{appid}"
    path = library / "steamapps" / f"appmanifest_{appid}.acf"
    path.write_text(
        manifest(str(appid), name=name, installdir=installdir, flags=flags, buildid=buildid),
        encoding="utf-8",
    )
    if folder:
        (library / "steamapps" / "common" / installdir).mkdir()
    return path


def make_library(path: Path, *appids: int) -> Path:
    (path / "steamapps" / "common").mkdir(parents=True)
    for appid in appids:
        add_game(path, appid)
    return path


def _root(base: Path, libraries: tuple, config: str | None, appids: tuple) -> Path:
    root = make_library(base / "steam", *appids)
    blocks = "".join(
        f'\t"{n}"\n\t{{\n\t\t"path"\t\t{q(path)}\n\t\t"label"\t\t""\n\t\t"apps"\n\t\t{{\n'
        "\t\t}\n\t}\n"
        for n, path in enumerate([str(root), *(str(lib) for lib in libraries)])
    )
    (root / "steamapps" / "libraryfolders.vdf").write_text(
        '"libraryfolders"\n{\n' + blocks + "}\n", encoding="utf-8"
    )
    (root / "config").mkdir()
    (root / "config" / "config.vdf").write_text(
        config_vdf(MAPPING) if config is None else config, encoding="utf-8"
    )
    return root


def make_root(base: Path, *libraries: Path, config: str | None = None) -> Path:
    """A Steam root listing itself and `libraries`, with one installed game (appid 10) and
    config.vdf holding `config`, or the planted MAPPING when None."""
    return _root(base, libraries, config, (10,))


def bare_root(base: Path, *libraries: Path, config: str | None = None) -> Path:
    """Like make_root, but the root has no game of its own."""
    return _root(base, libraries, config, ())


def folder(path: Path) -> Path:
    path.mkdir(parents=True)
    return path


def pairs(issues: list[dict]) -> list[tuple[str, str | None]]:
    return [(issue["code"], issue["path"]) for issue in issues]


def cards(result: dict) -> list[tuple[int, str]]:
    return [(card["appid"], card["library"]) for card in result["games"]]


def card_of(result: dict, appid: int) -> dict:
    found = [card for card in result["games"] if card["appid"] == appid]
    assert len(found) == 1, f"expected one card for {appid}, got {len(found)}"
    return found[0]


def b1_view(card: dict) -> dict:
    missing = [field for field in B1_FIELDS if field not in card]
    assert missing == []
    return {field: card[field] for field in B1_FIELDS}


def codes(issues: list[dict]) -> list[str]:
    return [issue["code"] for issue in issues]


def tools(result: dict) -> dict[int, str | None]:
    return {card["appid"]: card["compat_tool"] for card in result["games"]}


def assert_nothing_planted(result: dict) -> None:
    text = json.dumps(result)
    leaked = [value for value in PLANTED if value in text]
    assert leaked == []


def padded(text: str, size: int) -> bytes:
    data = text.encode("utf-8")
    assert len(data) <= size
    return data + b" " * (size - len(data))


def refuse_to_open(monkeypatch: pytest.MonkeyPatch, target: Path) -> None:
    """Every Python route to open `target` raises an OSError (EIO); other files open."""
    blocked = os.path.realpath(target)
    real_open, real_os_open, real_path_open = builtins.open, os.open, pathlib.Path.open

    def hit(file: object) -> bool:
        if not isinstance(file, str | bytes | os.PathLike):
            return False
        return os.path.realpath(os.fsdecode(file)) == blocked

    def fail(file: object) -> OSError:
        return OSError(errno.EIO, "I/O error injected by test", os.fsdecode(file))

    def fake_open(file, *args, **kwargs):
        if hit(file):
            raise fail(file)
        return real_open(file, *args, **kwargs)

    def fake_os_open(path, *args, **kwargs):
        if hit(path):
            raise fail(path)
        return real_os_open(path, *args, **kwargs)

    def fake_path_open(self, *args, **kwargs):
        if hit(self):
            raise fail(self)
        return real_path_open(self, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(io, "open", fake_open)
    monkeypatch.setattr(os, "open", fake_os_open)
    monkeypatch.setattr(pathlib.Path, "open", fake_path_open)


# ---------------------------------------------------------------------------- B3 names


def test_b3_every_matching_manifest_in_every_available_library_is_read(tmp_path):
    sd = make_library(tmp_path / "sd", 20, 1086940)
    root = make_root(tmp_path, sd)
    add_game(root, 2246340)
    result = discover.scan(str(root))
    assert cards(result) == [
        (10, str(root)),
        (20, str(sd)),
        (1086940, str(sd)),
        (2246340, str(root)),
    ]
    assert result["errors"] == []
    assert result["warnings"] == []


@pytest.mark.parametrize(
    "entry",
    [
        "AppManifest_70.acf",
        "appmanifest_70.ACF",
        "Appmanifest_70.acf",
        "appmanifest_70.acf.bak",
        "appmanifest_70.acf~",
        "appmanifest_70.acf.tmp",
        "appmanifest_70.acf ",
        " appmanifest_70.acf",
        "xappmanifest_70.acf",
        "appmanifest70.acf",
        "appmanifest-70.acf",
        "appmanifest_70.vdf",
        "appmanifest_70",
        "temp/appmanifest_70.acf",
        "common/appmanifest_70.acf",
        "downloading/appmanifest_70.acf",
    ],
)
def test_b3_names_that_do_not_match_exactly_are_ignored(tmp_path, entry):
    root = make_root(tmp_path)
    target = root / "steamapps" / entry
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(manifest("70", name=f"Look-alike {MARKER}"), encoding="utf-8")
    (root / "steamapps" / "common" / "HollowTest").mkdir()
    result = discover.scan(str(root))
    assert cards(result) == [(10, str(root))]
    assert result["errors"] == []
    assert result["warnings"] == []
    assert MARKER not in json.dumps(result)


def test_b3_link_to_a_regular_manifest_is_read(tmp_path):
    root = make_root(tmp_path)
    stored = tmp_path / "elsewhere" / "stored_manifest.txt"
    stored.parent.mkdir()
    stored.write_text(manifest("70"), encoding="utf-8")
    (root / "steamapps" / "appmanifest_70.acf").symlink_to(stored)
    (root / "steamapps" / "common" / "HollowTest").mkdir()
    result = discover.scan(str(root))
    assert cards(result) == [(10, str(root)), (70, str(root))]
    assert result["games"][1]["name"] == "Hollow Test"
    assert result["errors"] == []


def test_b3_leading_bom_is_stripped(tmp_path):
    root = make_root(tmp_path)
    (root / "steamapps" / "appmanifest_70.acf").write_bytes(
        b"\xef\xbb\xbf" + manifest("70").encode("utf-8")
    )
    (root / "steamapps" / "common" / "HollowTest").mkdir()
    result = discover.scan(str(root))
    assert cards(result) == [(10, str(root)), (70, str(root))]
    assert result["errors"] == []


def test_b3_manifest_of_exactly_1_mib_is_read(tmp_path):
    root = make_root(tmp_path)
    path = root / "steamapps" / "appmanifest_70.acf"
    path.write_bytes(padded(manifest("70"), MIB))
    assert path.stat().st_size == MIB
    (root / "steamapps" / "common" / "HollowTest").mkdir()
    result = discover.scan(str(root))
    assert cards(result) == [(10, str(root)), (70, str(root))]
    assert result["errors"] == []


@pytest.mark.parametrize("appid_key", ["appid", "appID", "AppID", "APPID"])
@pytest.mark.parametrize("installdir_key", ["installdir", "InstallDir"])
def test_b3_appid_and_installdir_keys_are_found_ignoring_case(tmp_path, appid_key, installdir_key):
    root = make_root(tmp_path)
    (root / "steamapps" / "appmanifest_70.acf").write_text(
        manifest("70", appid_key=appid_key, installdir_key=installdir_key), encoding="utf-8"
    )
    (root / "steamapps" / "common" / "HollowTest").mkdir()
    result = discover.scan(str(root))
    assert cards(result) == [(10, str(root)), (70, str(root))]
    assert result["games"][1]["installdir"] == "HollowTest"
    assert result["errors"] == []


# ---------------------------------------------------------------------------- B3 errors


def _write(text: str | bytes):
    def build(path: Path, tmp_path: Path) -> None:
        path.write_bytes(text.encode("utf-8") if isinstance(text, str) else text)

    return build


def _directory(path: Path, tmp_path: Path) -> None:
    path.mkdir()
    (path / "inner.txt").write_text(MARKER, encoding="utf-8")


def _link_to_directory(path: Path, tmp_path: Path) -> None:
    target = tmp_path / "a_folder"
    target.mkdir()
    path.symlink_to(target, target_is_directory=True)


def _broken_link(path: Path, tmp_path: Path) -> None:
    path.symlink_to(tmp_path / "no_such_manifest.acf")


def _too_large(path: Path, tmp_path: Path) -> None:
    path.write_bytes(padded(manifest("70", name=MARKER), MIB + 1))


def _os_error(path: Path, tmp_path: Path) -> None:
    path.write_text(manifest("70", name=MARKER), encoding="utf-8")


BROKEN = {
    # id: (entry name, builder, expected code)
    "directory": ("appmanifest_70.acf", _directory, "manifest_unreadable"),
    "link-to-directory": ("appmanifest_70.acf", _link_to_directory, "manifest_unreadable"),
    "broken-link": ("appmanifest_70.acf", _broken_link, "manifest_unreadable"),
    "larger-than-1-mib": ("appmanifest_70.acf", _too_large, "manifest_unreadable"),
    "os-error-while-reading": ("appmanifest_70.acf", _os_error, "manifest_unreadable"),
    "latin1-not-utf8": (
        "appmanifest_70.acf",
        _write(manifest("70", name=f"Caf\xe9 {MARKER}").encode("latin-1")),
        "manifest_malformed",
    ),
    "utf16-not-utf8": (
        "appmanifest_70.acf",
        _write(manifest("70", name=MARKER).encode("utf-16")),
        "manifest_malformed",
    ),
    "vdf-error": (
        "appmanifest_70.acf",
        _write(manifest("70", name=MARKER).rsplit("}", 1)[0]),
        "manifest_malformed",
    ),
    "empty-file": ("appmanifest_70.acf", _write(""), "manifest_malformed"),
    "no-appstate-block": (
        "appmanifest_70.acf",
        _write(manifest("70", name=MARKER).replace('"AppState"', '"AppInfo"', 1)),
        "manifest_malformed",
    ),
    "appstate-is-a-string": (
        "appmanifest_70.acf",
        _write(f'"AppState"\t\t"70"\n"name"\t\t"{MARKER}"\n'),
        "manifest_malformed",
    ),
    "appid-missing": (
        "appmanifest_70.acf",
        _write(manifest(None, name=MARKER)),
        "manifest_incomplete",
    ),
    "installdir-missing": (
        "appmanifest_70.acf",
        _write(manifest("70", name=MARKER, installdir=None)),
        "manifest_incomplete",
    ),
    "file-id-not-digits": (
        "appmanifest_abc.acf",
        _write(manifest("70", name=MARKER)),
        "manifest_appid_mismatch",
    ),
    "file-id-mixed": (
        "appmanifest_70a.acf",
        _write(manifest("70", name=MARKER)),
        "manifest_appid_mismatch",
    ),
    "appid-value-not-digits": (
        "appmanifest_70.acf",
        _write(manifest("70a", name=MARKER)),
        "manifest_appid_mismatch",
    ),
    "appid-value-negative": (
        "appmanifest_70.acf",
        _write(manifest("-70", name=MARKER)),
        "manifest_appid_mismatch",
    ),
    "appid-value-empty": (
        "appmanifest_70.acf",
        _write(manifest("", name=MARKER)),
        "manifest_appid_mismatch",
    ),
    "ids-differ": (
        "appmanifest_70.acf",
        _write(manifest("71", name=MARKER)),
        "manifest_appid_mismatch",
    ),
    "installdir-empty": (
        "appmanifest_70.acf",
        _write(manifest("70", name=MARKER, installdir="")),
        "manifest_unsafe_installdir",
    ),
    "installdir-dot": (
        "appmanifest_70.acf",
        _write(manifest("70", name=MARKER, installdir=".")),
        "manifest_unsafe_installdir",
    ),
    "installdir-dotdot": (
        "appmanifest_70.acf",
        _write(manifest("70", name=MARKER, installdir="..")),
        "manifest_unsafe_installdir",
    ),
    "installdir-slash": (
        "appmanifest_70.acf",
        _write(manifest("70", name=MARKER, installdir="HollowTest/Binaries")),
        "manifest_unsafe_installdir",
    ),
    "installdir-traversal": (
        "appmanifest_70.acf",
        _write(manifest("70", name=MARKER, installdir="../../config")),
        "manifest_unsafe_installdir",
    ),
    "installdir-backslash": (
        "appmanifest_70.acf",
        _write(manifest("70", name=MARKER, installdir="Hollow\\Test")),
        "manifest_unsafe_installdir",
    ),
    "installdir-absolute": (
        "appmanifest_70.acf",
        _write(manifest("70", name=MARKER, installdir="ABSOLUTE")),
        "manifest_unsafe_installdir",
    ),
}


@pytest.mark.parametrize("case", sorted(BROKEN))
def test_b3_refused_manifest_makes_an_error_and_no_card(tmp_path, monkeypatch, case):
    entry, build, code = BROKEN[case]
    sd = make_library(tmp_path / "sd", 20)
    root = make_root(tmp_path, sd)
    path = sd / "steamapps" / entry
    if case == "installdir-absolute":
        target = tmp_path / "absolute_game"
        target.mkdir()
        _write(manifest("70", name=MARKER, installdir=str(target)))(path, tmp_path)
    else:
        build(path, tmp_path)
    # Folders that a wrongly accepted installdir would point at, so only the rule refuses.
    (sd / "steamapps" / "common" / "HollowTest" / "Binaries").mkdir(parents=True)
    if case == "os-error-while-reading":
        refuse_to_open(monkeypatch, path)
    result = discover.scan(str(root))
    assert pairs(result["errors"]) == [(code, str(path))]
    assert result["warnings"] == []
    assert cards(result) == [(10, str(root)), (20, str(sd))]
    assert MARKER not in json.dumps(result)


def test_b3_every_refused_manifest_is_reported_and_the_rest_still_scanned(tmp_path):
    sd = make_library(tmp_path / "sd", 20, 40)
    root = make_root(tmp_path, sd)
    add_game(root, 30)
    broken = {
        root / "steamapps" / "appmanifest_71.acf": ("manifest_incomplete", manifest(None)),
        root / "steamapps" / "appmanifest_72.acf": ("manifest_malformed", '"AppState"\n{\n'),
        sd / "steamapps" / "appmanifest_73.acf": ("manifest_appid_mismatch", manifest("74")),
        sd / "steamapps" / "appmanifest_75.acf": (
            "manifest_unsafe_installdir",
            manifest("75", installdir=".."),
        ),
        sd / "steamapps" / "appmanifest_76.acf": ("manifest_malformed", manifest("76")[:-3]),
    }
    for path, (_, text) in broken.items():
        path.write_text(text, encoding="utf-8")
    result = discover.scan(str(root))
    expected = sorted((code, str(path)) for path, (code, _) in broken.items())
    assert pairs(result["errors"]) == expected
    assert cards(result) == [(10, str(root)), (20, str(sd)), (30, str(root)), (40, str(sd))]
    assert result["warnings"] == []


# ---------------------------------------------------------------------------- B4 cards


def test_b4_root_library_card_has_every_field(tmp_path):
    config = config_vdf({**MAPPING, "2246340": "proton_9"})
    root = bare_root(tmp_path, config=config)
    add_game(
        root,
        2246340,
        name="Monster Hunter Wilds",
        installdir="MonsterHunterWilds",
        flags="4",
        buildid="17436010",
    )
    prefix = folder(root / "steamapps" / "compatdata" / "2246340" / "pfx")
    shaders = folder(root / "steamapps" / "shadercache" / "2246340")
    card = card_of(discover.scan(str(root)), 2246340)
    assert b1_view(card) == {
        "appid": 2246340,
        "name": "Monster Hunter Wilds",
        "kind": "game",
        "library": str(root),
        "installdir": "MonsterHunterWilds",
        "buildid": "17436010",
        "state_flags": 4,
        "installed": True,
        "install_path": str(root / "steamapps" / "common" / "MonsterHunterWilds"),
        "prefix_path": str(prefix),
        "shadercache_path": str(shaders),
        "compat_tool": "proton_9",
        "warnings": [],
    }
    assert type(card["appid"]) is int
    assert type(card["state_flags"]) is int
    assert type(card["installed"]) is bool


def test_b4_sd_card_library_card_uses_its_own_library(tmp_path):
    sd = make_library(tmp_path / "mmcblk0p1")
    root = bare_root(tmp_path, sd)
    add_game(sd, 2183900, name="Warhammer 40,000: Space Marine 2", installdir="Space Marine 2")
    prefix = folder(sd / "steamapps" / "compatdata" / "2183900" / "pfx")
    shaders = folder(sd / "steamapps" / "shadercache" / "2183900")
    folder(root / "steamapps" / "compatdata" / "2183900" / "pfx")
    folder(root / "steamapps" / "shadercache" / "2183900")
    card = card_of(discover.scan(str(root)), 2183900)
    assert b1_view(card) == {
        "appid": 2183900,
        "name": "Warhammer 40,000: Space Marine 2",
        "kind": "game",
        "library": str(sd),
        "installdir": "Space Marine 2",
        "buildid": "100",
        "state_flags": 4,
        "installed": True,
        "install_path": str(sd / "steamapps" / "common" / "Space Marine 2"),
        "prefix_path": str(prefix),
        "shadercache_path": str(shaders),
        "compat_tool": None,
        "warnings": [],
    }


def test_b4_non_ascii_name_is_kept_as_written(tmp_path):
    root = bare_root(tmp_path)
    add_game(root, 587620, name="Ōkami HD – 大神")
    assert card_of(discover.scan(str(root)), 587620)["name"] == "Ōkami HD – 大神"


def test_b4_missing_name_is_null_with_warning(tmp_path):
    root = bare_root(tmp_path)
    add_game(root, 70, name=None)
    card = card_of(discover.scan(str(root)), 70)
    assert card["name"] is None
    assert card["kind"] == "game"
    assert codes(card["warnings"]) == ["name_missing"]


@pytest.mark.parametrize(
    ("name", "kind"),
    [
        ("Proton 9.0", "tool"),
        ("Proton Experimental", "tool"),
        ("Proton Hotfix", "tool"),
        ("Proton", "tool"),
        ("Protonaut", "game"),
        ("ProtonUp-Qt", "game"),
        ("Proton-GE", "game"),
        ("Proton\t9.0", "game"),
        ("proton 9.0", "game"),
        ("PROTON 9.0", "game"),
        (" Proton 9.0", "game"),
        ("Not Proton 9.0", "game"),
        ("Steam Linux Runtime", "tool"),
        ("Steam Linux Runtime 3.0 (sniper)", "tool"),
        ("Steam Linux Runtime - Soldier", "tool"),
        ("steam linux runtime 3.0 (sniper)", "game"),
        ("Steam Linux", "game"),
        ("The Steam Linux Runtime", "game"),
        ("Steamworks Common Redistributables", "tool"),
        ("steamworks common redistributables", "game"),
        ("Steamworks Common", "game"),
        ("Monster Hunter Wilds", "game"),
        ("Helldivers™ 2", "game"),
    ],
)
def test_b4_kind_tool_rules(tmp_path, name, kind):
    root = bare_root(tmp_path)
    add_game(root, 1493710, name=name)
    card = card_of(discover.scan(str(root)), 1493710)
    assert card["name"] == name
    assert card["kind"] == kind
    assert card["warnings"] == []


@pytest.mark.parametrize(("buildid", "expected"), [("17436010", "17436010"), (None, None)])
def test_b4_buildid_is_str_or_null(tmp_path, buildid, expected):
    root = bare_root(tmp_path)
    add_game(root, 70, buildid=buildid)
    card = card_of(discover.scan(str(root)), 70)
    assert card["buildid"] == expected
    assert card["warnings"] == []


@pytest.mark.parametrize(
    ("flags", "installed"),
    [("4", True), ("6", True), ("1030", True), ("16", False), ("1026", False), ("0", False)],
)
def test_b4_state_flags_examples(tmp_path, flags, installed):
    root = bare_root(tmp_path)
    add_game(root, 70, flags=flags)
    card = card_of(discover.scan(str(root)), 70)
    assert card["state_flags"] == int(flags)
    assert type(card["state_flags"]) is int
    assert card["installed"] is installed
    assert card["warnings"] == []


@pytest.mark.parametrize("flags", [None, "", "abc", "4.0", "4 4", "four"])
def test_b4_invalid_state_flags_are_null_with_warning(tmp_path, flags):
    root = bare_root(tmp_path)
    add_game(root, 70, flags=flags)
    card = card_of(discover.scan(str(root)), 70)
    assert card["state_flags"] is None
    assert card["installed"] is False
    assert codes(card["warnings"]) == ["stateflags_invalid"]


def _no_folder(common: Path) -> None:
    del common


def _other_case_folder(common: Path) -> None:
    (common / "monsterhunterwilds").mkdir()


def _file_not_folder(common: Path) -> None:
    (common / "MonsterHunterWilds").write_text("not a folder", encoding="utf-8")


@pytest.mark.parametrize("build", [_no_folder, _other_case_folder, _file_not_folder])
@pytest.mark.parametrize("flags", ["4", "1030"])
def test_b4_install_folder_missing_means_not_installed(tmp_path, build, flags):
    root = bare_root(tmp_path)
    add_game(root, 70, installdir="MonsterHunterWilds", flags=flags, folder=False)
    build(root / "steamapps" / "common")
    card = card_of(discover.scan(str(root)), 70)
    assert card["install_path"] == str(root / "steamapps" / "common" / "MonsterHunterWilds")
    assert card["state_flags"] == int(flags)
    assert card["installed"] is False
    assert codes(card["warnings"]) == ["install_folder_missing"]


PREFIX_CASES = {
    # id: (game library, folders to create, expected prefix owner or None, warning codes)
    "own-library": ("sd", ["sd/pfx"], "sd", []),
    "own-library-wins-over-root": ("sd", ["sd/pfx", "root/pfx"], "sd", []),
    "root-fallback": ("sd", ["root/pfx"], "root", ["prefix_in_other_library"]),
    "own-pfx-is-a-file": ("sd", ["sd/pfx-file", "root/pfx"], "root", ["prefix_in_other_library"]),
    "nowhere": ("sd", [], None, []),
    "compatdata-without-pfx": ("sd", ["sd/compatdata", "root/compatdata"], None, []),
    "root-game-own": ("root", ["root/pfx"], "root", []),
    "root-game-never-uses-sd": ("root", ["sd/pfx"], None, []),
    "root-game-pfx-is-a-file": ("root", ["root/pfx-file"], None, []),
}


@pytest.mark.parametrize("case", sorted(PREFIX_CASES))
def test_b4_prefix_path_rules(tmp_path, case):
    where, layout, owner, expected_codes = PREFIX_CASES[case]
    sd = make_library(tmp_path / "sd")
    root = bare_root(tmp_path, sd)
    libraries = {"root": root, "sd": sd}
    add_game(libraries[where], 70)
    for item in layout:
        name, _, kind = item.partition("/")
        compat = libraries[name] / "steamapps" / "compatdata" / "70"
        if kind == "pfx":
            folder(compat / "pfx")
        elif kind == "pfx-file":
            folder(compat)
            (compat / "pfx").write_text("not a folder", encoding="utf-8")
        else:
            folder(compat)
    card = card_of(discover.scan(str(root)), 70)
    expected = None
    if owner is not None:
        expected = str(libraries[owner] / "steamapps" / "compatdata" / "70" / "pfx")
    assert card["prefix_path"] == expected
    assert codes(card["warnings"]) == expected_codes


@pytest.mark.parametrize(
    ("where", "cache_in", "expected"),
    [
        ("root", "root", "root"),
        ("sd", "sd", "sd"),
        ("sd", "root", None),
        ("root", "sd", None),
        ("root", None, None),
        ("root", "root-file", None),
    ],
)
def test_b4_shadercache_path_is_own_library_folder_or_null(tmp_path, where, cache_in, expected):
    sd = make_library(tmp_path / "sd")
    root = bare_root(tmp_path, sd)
    libraries = {"root": root, "sd": sd}
    add_game(libraries[where], 70)
    if cache_in == "root-file":
        folder(root / "steamapps" / "shadercache")
        (root / "steamapps" / "shadercache" / "70").write_text("x", encoding="utf-8")
    elif cache_in is not None:
        folder(libraries[cache_in] / "steamapps" / "shadercache" / "70")
    card = card_of(discover.scan(str(root)), 70)
    if expected is None:
        assert card["shadercache_path"] is None
    else:
        assert card["shadercache_path"] == str(
            libraries[expected] / "steamapps" / "shadercache" / "70"
        )
    assert card["warnings"] == []


def test_b4_paths_are_joined_from_the_library_string_not_resolved(tmp_path):
    real_root = tmp_path / "real"
    real_root.mkdir()
    sd_real = make_library(tmp_path / "sd_real")
    sd_link = tmp_path / "sd_link"
    sd_link.symlink_to(sd_real, target_is_directory=True)
    root = bare_root(real_root, sd_link)
    root_link = tmp_path / "steam_link"
    root_link.symlink_to(root, target_is_directory=True)
    add_game(sd_real, 70)
    add_game(root, 80)
    folder(root / "steamapps" / "compatdata" / "70" / "pfx")
    folder(sd_real / "steamapps" / "shadercache" / "70")
    folder(root / "steamapps" / "compatdata" / "80" / "pfx")
    folder(root / "steamapps" / "shadercache" / "80")
    result = discover.scan(str(root_link))
    sd_card, root_card = card_of(result, 70), card_of(result, 80)
    assert sd_card["library"] == str(sd_link)
    assert sd_card["install_path"] == str(sd_link / "steamapps" / "common" / "Game70")
    assert sd_card["prefix_path"] == str(root_link / "steamapps" / "compatdata" / "70" / "pfx")
    assert sd_card["shadercache_path"] == str(sd_link / "steamapps" / "shadercache" / "70")
    assert codes(sd_card["warnings"]) == ["prefix_in_other_library"]
    assert root_card["library"] == str(root_link)
    assert root_card["install_path"] == str(root_link / "steamapps" / "common" / "Game80")
    assert root_card["prefix_path"] == str(root_link / "steamapps" / "compatdata" / "80" / "pfx")
    assert root_card["shadercache_path"] == str(root_link / "steamapps" / "shadercache" / "80")


def test_b4_card_warnings_are_sorted_issues(tmp_path):
    sd = make_library(tmp_path / "sd")
    root = bare_root(tmp_path, sd)
    add_game(sd, 70, name=None, flags="x", folder=False)
    folder(root / "steamapps" / "compatdata" / "70" / "pfx")
    card = card_of(discover.scan(str(root)), 70)
    assert codes(card["warnings"]) == [
        "install_folder_missing",
        "name_missing",
        "prefix_in_other_library",
        "stateflags_invalid",
    ]
    for issue in card["warnings"]:
        assert set(issue) == {"code", "path", "message"}
        assert isinstance(issue["code"], str)
        assert issue["path"] is None or isinstance(issue["path"], str)
        assert isinstance(issue["message"], str)
    keys = [(issue["code"], issue["path"] or "") for issue in card["warnings"]]
    assert keys == sorted(keys)


# ---------------------------------------------------------------------------- B5 Proton


@pytest.mark.parametrize("valve", ["Valve", "valve"])
def test_b5_compat_tool_comes_from_compattoolmapping_ignoring_valve_case(tmp_path, valve):
    mapping = {**MAPPING, "2246340": "proton_9", "1086940": "proton_experimental"}
    sd = make_library(tmp_path / "sd")
    root = bare_root(tmp_path, sd, config=config_vdf(mapping, valve=valve))
    add_game(root, 2246340)
    add_game(sd, 1086940)
    add_game(root, 730)
    result = discover.scan(str(root))
    assert tools(result) == {730: None, 1086940: "proton_experimental", 2246340: "proton_9"}
    assert result["warnings"] == []
    assert result["errors"] == []
    assert_nothing_planted(result)


def test_b5_empty_or_missing_tool_name_is_null(tmp_path):
    mapping = {**MAPPING, "70": "", "80": None, "90": "proton_8"}
    root = bare_root(tmp_path, config=config_vdf(mapping))
    for appid in (70, 80, 90):
        add_game(root, appid)
    result = discover.scan(str(root))
    assert tools(result) == {70: None, 80: None, 90: "proton_8"}
    assert result["warnings"] == []


def test_b5_global_default_entry_0_is_never_applied(tmp_path):
    root = bare_root(tmp_path)
    add_game(root, 0, name="Appid zero")
    add_game(root, 70)
    result = discover.scan(str(root))
    assert tools(result) == {0: None, 70: None}
    assert_nothing_planted(result)


def test_b5_lookup_tries_every_matching_key_like_find(tmp_path):
    # "valve" comes last but has no CompatToolMapping; vdf.find then tries "Valve".
    later = '\t\t"valve"\n\t\t{\n\t\t\t"Steam"\n\t\t\t{\n\t\t\t\t"SurveyDate"\t\t"2026-01-01"\n'
    later += "\t\t\t}\n\t\t}\n"
    config = config_vdf({**MAPPING, "70": "proton_9"}, after=later)
    root = bare_root(tmp_path, config=config)
    add_game(root, 70)
    assert tools(discover.scan(str(root))) == {70: "proton_9"}


@pytest.mark.parametrize("layout", ["no-config-folder", "no-config-file"])
def test_b5_missing_config_vdf_is_a_warning_and_every_tool_is_null(tmp_path, layout):
    root = bare_root(tmp_path)
    add_game(root, 70)
    (root / "config" / "config.vdf").unlink()
    if layout == "no-config-folder":
        (root / "config").rmdir()
    result = discover.scan(str(root))
    assert [(i["code"], i["path"]) for i in result["warnings"]] == [
        ("config_vdf_missing", str(root / "config" / "config.vdf"))
    ]
    assert result["errors"] == []
    assert tools(result) == {70: None}


GOOD = config_vdf({**MAPPING, "70": "proton_9"})
UNUSABLE_CONFIGS = {
    "vdf-error-after-the-mapping": GOOD.rsplit("}", 1)[0].encode("utf-8"),
    "latin1-not-utf8": GOOD.replace("CrawlSteamInstallFolders", "Caf\xe9").encode("latin-1"),
    "utf16-not-utf8": GOOD.encode("utf-16"),
    "larger-than-16-mib": None,
    "a-folder": None,
    "cannot-be-read": None,
}


@pytest.mark.parametrize("case", sorted(UNUSABLE_CONFIGS))
def test_b5_unusable_config_vdf_is_malformed_and_every_tool_is_null(tmp_path, monkeypatch, case):
    root = bare_root(tmp_path)
    add_game(root, 70)
    target = root / "config" / "config.vdf"
    if case == "a-folder":
        target.unlink()
        target.mkdir()
    elif case == "cannot-be-read":
        target.write_text(GOOD, encoding="utf-8")
        refuse_to_open(monkeypatch, target)
    elif case == "larger-than-16-mib":
        target.write_bytes(padded(GOOD, 16 * MIB + 1))
    else:
        target.write_bytes(UNUSABLE_CONFIGS[case])
    result = discover.scan(str(root))
    top = result["errors"] + result["warnings"]
    assert codes(top) == ["config_vdf_malformed"]
    assert top[0]["path"] in {None, str(target)}
    assert tools(result) == {70: None}
    assert_nothing_planted(result)


def test_b5_config_vdf_of_exactly_16_mib_is_read(tmp_path):
    root = bare_root(tmp_path)
    add_game(root, 70)
    target = root / "config" / "config.vdf"
    target.write_bytes(padded(GOOD, 16 * MIB))
    assert target.stat().st_size == 16 * MIB
    result = discover.scan(str(root))
    assert tools(result) == {70: "proton_9"}
    assert result["warnings"] == []
    assert result["errors"] == []


def test_b5_nothing_else_from_config_vdf_reaches_the_output(tmp_path):
    sd = make_library(tmp_path / "sd")
    root = bare_root(tmp_path, sd, config=config_vdf({**MAPPING, "70": "proton_9"}))
    add_game(root, 70)
    add_game(sd, 80)
    result = discover.scan(str(root))
    assert_nothing_planted(result)
    for word in ("AutoUpdateWindowEnabled", "SteamID", "ConnectCache", "Accounts", "priority"):
        assert word not in json.dumps(result)
    assert {card["compat_tool"] for card in result["games"]} == {"proton_9", None}


# ---------------------------------------------------------------------------- B6 duplicates


@pytest.mark.parametrize(
    ("sd_name", "later"),
    [
        pytest.param("a_sdcard", "root", id="sd-path-sorts-first"),
        pytest.param("z_sdcard", "sd", id="sd-path-sorts-last"),
    ],
)
def test_b6_duplicate_appid_keeps_both_cards_and_warns_on_the_later_manifest(
    tmp_path, sd_name, later
):
    sd = make_library(tmp_path / sd_name, 70)
    root = make_root(tmp_path, sd)
    root_manifest = add_game(root, 70)
    sd_manifest = sd / "steamapps" / "appmanifest_70.acf"
    result = discover.scan(str(root))
    in_order = sorted([str(root), str(sd)])
    assert cards(result) == [(10, str(root)), (70, in_order[0]), (70, in_order[1])]
    for card in result["games"][1:]:
        assert card["install_path"] == str(Path(card["library"], "steamapps", "common", "Game70"))
    later_manifest = root_manifest if later == "root" else sd_manifest
    assert pairs(result["warnings"]) == [("duplicate_appid", str(later_manifest))]
    assert result["errors"] == []


def test_b6_a_refused_manifest_is_not_a_duplicate(tmp_path):
    sd = make_library(tmp_path / "sd")
    root = make_root(tmp_path, sd)
    add_game(root, 70)
    broken = sd / "steamapps" / "appmanifest_70.acf"
    broken.write_text(manifest("70", installdir=".."), encoding="utf-8")
    result = discover.scan(str(root))
    assert cards(result) == [(10, str(root)), (70, str(root))]
    assert pairs(result["errors"]) == [("manifest_unsafe_installdir", str(broken))]
    assert result["warnings"] == []


def test_b6_distinct_appids_across_libraries_are_not_duplicates(tmp_path):
    sd = make_library(tmp_path / "sd", 20, 30)
    root = make_root(tmp_path, sd)
    add_game(root, 40)
    result = discover.scan(str(root))
    assert [card["appid"] for card in result["games"]] == [10, 20, 30, 40]
    assert result["warnings"] == []


# ---------------------------------------------------------------------------- FIFOs

CHILD = """
import json
import sys

from deckforge import discover

try:
    result = getattr(discover, sys.argv[2])(sys.argv[1])
except discover.DiscoverError:
    sys.stdout.write("DiscoverError")
else:
    sys.stdout.write(json.dumps(result))
"""


def lstat_tree(top: Path) -> dict[str, tuple]:
    """Name, type, size, times and link target of every entry; contents not read."""
    state: dict[str, tuple] = {}
    pending = [top]
    while pending:
        path = pending.pop()
        info = path.lstat()
        entry: tuple = (info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        if stat.S_ISLNK(info.st_mode):
            entry += (str(path.readlink()),)
        if stat.S_ISDIR(info.st_mode):
            pending.extend(path.iterdir())
        state[str(path.relative_to(top))] = entry
    return state


def run_child(root: Path, function: str, cwd: Path) -> str:
    """Run discover.<function>(root) in a child Python; return its stdout."""
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    try:
        proc = subprocess.run(
            [sys.executable, "-c", CHILD, str(root), function],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"discover.{function} blocked for {TIMEOUT_S} s: it opened a FIFO")
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def fifo_case(tmp_path: Path, where: str) -> tuple[Path, Path, Path]:
    root = make_root(tmp_path / "data", config=config_vdf({**MAPPING, "10": "proton_9"}))
    target = {
        "manifest": root / "steamapps" / "appmanifest_1.acf",
        "libraryfolders": root / "steamapps" / "libraryfolders.vdf",
        "config": root / "config" / "config.vdf",
    }[where]
    target.unlink(missing_ok=True)
    os.mkfifo(target)
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    return root, target, cwd


def test_b3_fifo_manifest_is_unreadable_and_never_opened(tmp_path):
    root, fifo, cwd = fifo_case(tmp_path, "manifest")
    before = lstat_tree(tmp_path)
    result = json.loads(run_child(root, "scan", cwd))
    assert pairs(result["errors"]) == [("manifest_unreadable", str(fifo))]
    assert cards(result) == [(10, str(root))]
    assert result["games"][0]["compat_tool"] == "proton_9"
    assert result["warnings"] == []
    assert lstat_tree(tmp_path) == before


@pytest.mark.parametrize("function", ["scan", "find_libraries"])
def test_b1_fifo_libraryfolders_raises_discover_error(tmp_path, function):
    root, _, cwd = fifo_case(tmp_path, "libraryfolders")
    before = lstat_tree(tmp_path)
    assert run_child(root, function, cwd) == "DiscoverError"
    assert lstat_tree(tmp_path) == before


def test_b5_fifo_config_vdf_is_malformed_and_every_tool_is_null(tmp_path):
    root, fifo, cwd = fifo_case(tmp_path, "config")
    before = lstat_tree(tmp_path)
    result = json.loads(run_child(root, "scan", cwd))
    top = result["errors"] + result["warnings"]
    assert codes(top) == ["config_vdf_malformed"]
    assert top[0]["path"] in {None, str(fifo)}
    assert [(card["appid"], card["compat_tool"]) for card in result["games"]] == [(10, None)]
    assert lstat_tree(tmp_path) == before
