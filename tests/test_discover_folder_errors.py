# Contracts for deckforge.discover: the B4 amendment in docs/specs/discover.md after
# verifier finding F1 (2026-10-11), "Errors while checking folders are never silent (R12)"
# and the amended prefix_path row. Written against the amended spec only.
#
# scan(steam_root), card field prefix_path
#   Post: the game's own prefix <library>/steamapps/compatdata/<appid>/pfx is a folder:
#         it is used.
#   Post: the own prefix is absent (not found, or a path part is not a folder): the root
#         library's prefix is used if it is a folder, with a prefix_in_other_library card
#         warning, and there is no prefix_unreadable warning.
#   Post: checking the own prefix fails with any other OS error (EIO, EACCES, ELOOP):
#         prefix_path is None and there is one prefix_unreadable card warning whose path is
#         the own prefix path. There is no fallback, even when the root library still has
#         a prefix for that appid. Other cards are unaffected.
#
# scan(steam_root), install folders
#   Post: <library>/steamapps/common exists but cannot be listed: one top-level
#         common_unreadable warning whose path is that folder; every game in that library
#         gets install_folder_missing and is not installed; other libraries are unaffected.
#
# Folder checks in general (R12)
#   Inv:  a folder check that fails with an OS error other than "not found" or "not a
#         folder" becomes an issue whose path is that folder, or a WARNING log record
#         (logger deckforge.discover) that contains the path. Truly missing folders
#         produce neither. The last two tests are the verifier's pin, kept as given except
#         that the tree now has a config.vdf, so a config_vdf_missing log line cannot
#         make the quiet test fail for an unrelated reason.
#
# Errors are injected by patching os.stat (which os.path.isdir and pathlib's Path.stat
# use), os.lstat and os.scandir for one path: the container runs as root, so chmod cannot
# create them. The link loop is a real symlink to itself inside tmp_path. discover only
# reads, so there is no write-then-restore round trip here.

import errno
import logging
import os
from pathlib import Path

import pytest

from deckforge import discover

SD_APPID = 2183900
ROOT_APPID = 2246340
CONFIG_VDF = (
    '"InstallConfigStore"\n{\n\t"Software"\n\t{\n\t\t"Valve"\n\t\t{\n\t\t\t"Steam"\n\t\t\t{\n'
    '\t\t\t\t"CompatToolMapping"\n\t\t\t\t{\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n}\n'
)


# ---------------------------------------------------------------------------- helpers


def q(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def put(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_tree(base):
    """The verifier's tree: Space Marine 2 on the SD card with its own prefix, and a stale
    prefix for the same appid on the internal drive. Plus a valid config.vdf."""
    root, sd = base / "steam", base / "mmcblk0p1"
    put(
        root / "steamapps" / "libraryfolders.vdf",
        '"libraryfolders"\n{\n'
        f'\t"0"\n\t{{\n\t\t"path"\t\t{q(str(root))}\n\t}}\n'
        f'\t"1"\n\t{{\n\t\t"path"\t\t{q(str(sd))}\n\t}}\n'
        "}\n",
    )
    put(
        sd / "steamapps" / "appmanifest_2183900.acf",
        '"AppState"\n{\n\t"appid"\t\t"2183900"\n\t"name"\t\t"Space Marine 2"\n'
        '\t"StateFlags"\t\t"4"\n\t"installdir"\t\t"Space Marine 2"\n}\n',
    )
    (sd / "steamapps" / "common" / "Space Marine 2").mkdir(parents=True)
    (sd / "steamapps" / "compatdata" / "2183900" / "pfx").mkdir(parents=True)
    (root / "steamapps" / "compatdata" / "2183900" / "pfx").mkdir(parents=True)
    put(root / "config" / "config.vdf", CONFIG_VDF)
    return root, sd


def make_deck(base: Path) -> tuple[Path, Path]:
    """make_tree plus Monster Hunter Wilds on the internal drive, with its own prefix."""
    root, sd = make_tree(base)
    put(
        root / "steamapps" / f"appmanifest_{ROOT_APPID}.acf",
        f'"AppState"\n{{\n\t"appid"\t\t"{ROOT_APPID}"\n\t"name"\t\t"Monster Hunter Wilds"\n'
        '\t"StateFlags"\t\t"4"\n\t"installdir"\t\t"MonsterHunterWilds"\n}\n',
    )
    (root / "steamapps" / "common" / "MonsterHunterWilds").mkdir(parents=True)
    prefix(root, ROOT_APPID).mkdir(parents=True)
    return root, sd


def prefix(library: Path, appid: int) -> Path:
    return library / "steamapps" / "compatdata" / str(appid) / "pfx"


def fail_stat(monkeypatch, target, code):
    blocked, real_stat = str(target), os.stat

    def fake_stat(path, *args, **kwargs):
        if os.fspath(path) == blocked:
            raise OSError(code, os.strerror(code), blocked)
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(os, "stat", fake_stat)


def fail_folder(monkeypatch: pytest.MonkeyPatch, target: Path, code: int, names=None) -> None:
    """os.stat, os.lstat and os.scandir (or only `names` of them) raise OSError(code) for
    `target`; every other path behaves normally."""
    blocked = os.path.normpath(target)
    real = {name: getattr(os, name) for name in names or ("stat", "lstat", "scandir")}

    def wrap(name):
        def fake(path=".", *args, **kwargs):
            if isinstance(path, str | bytes | os.PathLike) and (
                os.path.normpath(os.fsdecode(path)) == blocked
            ):
                raise OSError(code, os.strerror(code), os.fsdecode(path))
            return real[name](path, *args, **kwargs)

        return fake

    for name in real:
        monkeypatch.setattr(os, name, wrap(name))


def mentioned(result, records, path):
    issues = (
        result["errors"] + result["warnings"] + [i for c in result["games"] for i in c["warnings"]]
    )
    return any(i["path"] == str(path) for i in issues) or any(
        r.levelno >= logging.WARNING and str(path) in r.getMessage() for r in records
    )


def card_of(result: dict, appid: int) -> dict:
    found = [card for card in result["games"] if card["appid"] == appid]
    assert len(found) == 1, f"expected one card for {appid}, got {len(found)}"
    return found[0]


def pairs(issues: list[dict]) -> list[tuple[str, str | None]]:
    return [(issue["code"], issue["path"]) for issue in issues]


def codes(issues: list[dict]) -> list[str]:
    return [issue["code"] for issue in issues]


# ---------------------------------------------------------------------------- prefix_path


@pytest.mark.parametrize("where", ["sd", "root"])
@pytest.mark.parametrize("failure", ["eio", "eacces", "eloop"])
def test_b4_own_prefix_error_gives_prefix_unreadable_and_no_fallback(
    tmp_path, monkeypatch, failure, where
):
    root, sd = make_deck(tmp_path)
    library, appid = (sd, SD_APPID) if where == "sd" else (root, ROOT_APPID)
    other_library, other_appid = (root, ROOT_APPID) if where == "sd" else (sd, SD_APPID)
    own = prefix(library, appid)
    assert prefix(root, SD_APPID).is_dir()  # the stale prefix a fallback would pick
    if failure == "eloop":
        own.rmdir()
        own.symlink_to(own)  # a real link loop: os.stat raises ELOOP
    else:
        fail_folder(monkeypatch, own, {"eio": errno.EIO, "eacces": errno.EACCES}[failure])
    result = discover.scan(str(root))
    card = card_of(result, appid)
    assert card["prefix_path"] is None
    assert pairs(card["warnings"]) == [("prefix_unreadable", str(own))]
    other = card_of(result, other_appid)
    assert other["prefix_path"] == str(prefix(other_library, other_appid))
    assert other["warnings"] == []


def _remove_pfx(own: Path) -> None:
    own.rmdir()


def _path_part_is_a_file(own: Path) -> None:
    own.rmdir()
    own.parent.rmdir()
    own.parent.write_text("not a folder", encoding="utf-8")


def _no_compatdata_folder(own: Path) -> None:
    own.rmdir()
    own.parent.rmdir()
    own.parent.parent.rmdir()


@pytest.mark.parametrize(
    "make_absent",
    [_remove_pfx, _path_part_is_a_file, _no_compatdata_folder],
    ids=["pfx-removed", "path-part-is-a-file", "no-compatdata-folder"],
)
def test_b4_absent_own_prefix_still_falls_back_to_the_root_library(tmp_path, make_absent):
    root, sd = make_deck(tmp_path)
    make_absent(prefix(sd, SD_APPID))
    result = discover.scan(str(root))
    card = card_of(result, SD_APPID)
    assert card["prefix_path"] == str(prefix(root, SD_APPID))
    assert codes(card["warnings"]) == ["prefix_in_other_library"]
    assert result["warnings"] == []
    assert result["errors"] == []


# ---------------------------------------------------------------------------- common


@pytest.mark.parametrize("where", ["sd", "root"])
def test_b4_unlistable_common_is_a_top_level_warning_and_its_games_are_missing(
    tmp_path, monkeypatch, where
):
    root, sd = make_deck(tmp_path)
    if where == "sd":
        library, appid, installdir, other_appid = sd, SD_APPID, "Space Marine 2", ROOT_APPID
    else:
        library, appid, installdir, other_appid = root, ROOT_APPID, "MonsterHunterWilds", SD_APPID
    common = library / "steamapps" / "common"
    assert (common / installdir).is_dir()
    fail_folder(monkeypatch, common, errno.EACCES, names=("scandir",))
    result = discover.scan(str(root))
    assert pairs(result["warnings"]) == [("common_unreadable", str(common))]
    assert result["errors"] == []
    card = card_of(result, appid)
    assert card["install_path"] == str(common / installdir)
    assert card["installed"] is False
    assert codes(card["warnings"]) == ["install_folder_missing"]
    other = card_of(result, other_appid)
    assert other["installed"] is True
    assert other["warnings"] == []


# ---------------------------------------------------------------------------- verifier pin


@pytest.mark.parametrize("code", [errno.EIO, errno.EACCES], ids=["eio", "eacces"])
@pytest.mark.parametrize("which", ["own_prefix", "sd_steamapps"])
def test_b4_folder_check_errors_are_not_swallowed(tmp_path, monkeypatch, caplog, code, which):
    root, sd = make_tree(tmp_path)
    target = {
        "own_prefix": sd / "steamapps" / "compatdata" / "2183900" / "pfx",
        "sd_steamapps": sd / "steamapps",
    }[which]
    fail_stat(monkeypatch, target, code)
    with caplog.at_level(logging.WARNING):
        result = discover.scan(str(root))
    assert mentioned(result, caplog.records, target)


def test_b4_missing_folders_stay_quiet(tmp_path, caplog):
    root, sd = make_tree(tmp_path)
    (sd / "steamapps" / "compatdata" / "2183900" / "pfx").rmdir()
    with caplog.at_level(logging.WARNING):
        result = discover.scan(str(root))
    card = next(c for c in result["games"] if c["appid"] == 2183900)
    assert card["prefix_path"] == str(root / "steamapps" / "compatdata" / "2183900" / "pfx")
    assert [r.getMessage() for r in caplog.records] == []
