# Contracts for deckforge.discover, PR B1 of docs/specs/discover.md: criteria B1 (root) and
# B2 (libraries). Written test-first; src/deckforge/discover.py does not exist yet.
#
# class DiscoverError(Exception)
#   Raised by scan and find_libraries when libraryfolders.vdf cannot be used (B1). Its
#   message never contains file contents (the CLI prints it as one line, see B8).
#
# find_libraries(steam_root) -> list of {"path": str, "available": bool}
#   Pre:  steam_root is a str or os.PathLike. It is made absolute with os.path.abspath: not
#         resolved through links, and a leading ~ is a plain folder name, never expanded.
#   Pre:  <root>/steamapps/libraryfolders.vdf exists, is a regular file of at most 1 MiB,
#         can be read, is strict UTF-8 (one leading BOM is accepted), parses as VDF and has
#         a `libraryfolders` key found with vdf.find (so any letter case). Otherwise it
#         raises DiscoverError, and so does scan.
#   Post: the root comes first, then every numbered key (all digits) in numeric order, so
#         "10" comes after "2". Other keys are ignored. A numbered value is either a block
#         with a `path` key (current layout) or the path string itself (legacy layout).
#   Post: a numbered block with no `path` is skipped with a library_entry_invalid warning
#         whose path is None.
#   Post: a path that is empty, relative or contains a backslash stays in the list with
#         available false and a library_path_invalid warning whose path is the text as
#         written. It is never resolved against the current folder.
#   Post: other paths are os.path.normpath'ed, then de-duplicated by os.path.realpath; the
#         first one wins, so the root wins over a listed copy of itself.
#   Post: available is true only if <path>/steamapps is a folder os.scandir can list. Not a
#         folder: library_unavailable warning (path = the library path). A folder that
#         cannot be listed: library_unreadable error and library_unavailable warning.
#   Inv:  reads only; equal to scan(steam_root)["libraries"].
#
# scan(steam_root) -> dict
#   Post: "steam_root" is os.path.abspath(steam_root) as a str; "libraries" is as above;
#         library warnings and errors are in the top-level "warnings" and "errors" lists.
#
# Issues are {"code", "path", "message"}. These tests read code and path only, never the
# message text. PR B1 has no write or restore path, so there is no apply-then-restore round
# trip here; the read-only property is proven in the B9 tests.
# Unusual setups covered: legacy layout, BOM, symlinked root, a root folder literally named
# "~", Windows-style and relative library paths, symlinked and repeated library paths,
# missing, file-shaped and unlistable steamapps folders, and size, encoding and syntax
# failures of libraryfolders.vdf (each refused with DiscoverError).

import builtins
import errno
import io
import os
import pathlib
from pathlib import Path

import pytest

from deckforge import discover

MIB = 1024 * 1024
MARKER = "df-planted-library-text-5c2e"
CONFIG_VDF = (
    '"InstallConfigStore"\n{\n\t"Software"\n\t{\n\t\t"Valve"\n\t\t{\n\t\t\t"Steam"\n\t\t\t{\n'
    '\t\t\t\t"CompatToolMapping"\n\t\t\t\t{\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n}\n'
)


# ---------------------------------------------------------------------------- helpers


def q(text: str) -> str:
    """A VDF quoted string, escaped the way Steam writes it."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def current_entry(key: str, path: str) -> str:
    return (
        f"\t{q(key)}\n\t{{\n"
        f'\t\t"path"\t\t{q(path)}\n'
        '\t\t"label"\t\t""\n'
        '\t\t"contentid"\t\t"4851329021884932012"\n'
        '\t\t"totalsize"\t\t"0"\n'
        '\t\t"update_clean_bytes_tally"\t\t"0"\n'
        '\t\t"time_last_update_verified"\t\t"0"\n'
        '\t\t"apps"\n\t\t{\n\t\t\t"1086940"\t\t"130511364539"\n\t\t}\n'
        "\t}\n"
    )


def current_layout(*entries: tuple[str, str], extra: str = "") -> str:
    """libraryfolders.vdf as current Steam writes it: numbered blocks with a path key."""
    body = "".join(current_entry(key, path) for key, path in entries)
    return (
        '"libraryfolders"\n{\n\t"contentstatsid"\t\t"-4917390201925046562"\n' + body + extra + "}\n"
    )


def legacy_layout(*entries: tuple[str, str]) -> str:
    """libraryfolders.vdf as older Steam wrote it: numbered keys whose value is the path."""
    lines = [
        '"LibraryFolders"',
        "{",
        '\t"TimeNextStatsReport"\t\t"1700000000"',
        '\t"ContentStatsID"\t\t"-4917390201925046562"',
    ]
    lines += [f"\t{q(key)}\t\t{q(path)}" for key, path in entries]
    return "\n".join([*lines, "}"]) + "\n"


def manifest(appid: int, name: str) -> str:
    return (
        '"AppState"\n{\n'
        f'\t"appid"\t\t"{appid}"\n'
        '\t"universe"\t\t"1"\n'
        f'\t"name"\t\t{q(name)}\n'
        '\t"StateFlags"\t\t"4"\n'
        f'\t"installdir"\t\t"Game{appid}"\n'
        '\t"buildid"\t\t"100"\n'
        "}\n"
    )


def make_library(path: Path, *appids: int) -> Path:
    """A library folder with one installed game per appid."""
    (path / "steamapps" / "common").mkdir(parents=True)
    for appid in appids:
        (path / "steamapps" / f"appmanifest_{appid}.acf").write_text(
            manifest(appid, f"Game {appid}"), encoding="utf-8"
        )
        (path / "steamapps" / "common" / f"Game{appid}").mkdir()
    return path


def make_root(base: Path, *entries: tuple[str, str], name: str = "steam") -> Path:
    """A Steam root whose libraryfolders.vdf lists itself as "0" (as Steam does), then
    `entries`. Includes a valid config.vdf and one installed game, appid 10."""
    root = make_library(base / name, 10)
    write_libraryfolders(root, current_layout(("0", str(root)), *entries))
    (root / "config").mkdir()
    (root / "config" / "config.vdf").write_text(CONFIG_VDF, encoding="utf-8")
    return root


def write_libraryfolders(root: Path, text: str | bytes) -> None:
    target = root / "steamapps" / "libraryfolders.vdf"
    if isinstance(text, str):
        text = text.encode("utf-8")
    target.write_bytes(text)


def pairs(issues: list[dict]) -> list[tuple[str, str | None]]:
    return [(issue["code"], issue["path"]) for issue in issues]


def lib(path: Path | str, available: bool = True) -> dict:
    return {"path": str(path), "available": available}


def library_names(result: dict) -> set[str]:
    return {card["library"] for card in result["games"]}


def refuse_to_open(monkeypatch: pytest.MonkeyPatch, target: Path) -> None:
    """Every Python route to open `target` raises PermissionError; other files open."""
    blocked = os.path.realpath(target)
    real_open, real_os_open, real_path_open = builtins.open, os.open, pathlib.Path.open

    def hit(file: object) -> bool:
        if not isinstance(file, str | bytes | os.PathLike):
            return False
        return os.path.realpath(os.fsdecode(file)) == blocked

    def deny(file: object) -> PermissionError:
        return PermissionError(errno.EACCES, "refused by test", os.fsdecode(file))

    def fake_open(file, *args, **kwargs):
        if hit(file):
            raise deny(file)
        return real_open(file, *args, **kwargs)

    def fake_os_open(path, *args, **kwargs):
        if hit(path):
            raise deny(path)
        return real_os_open(path, *args, **kwargs)

    def fake_path_open(self, *args, **kwargs):
        if hit(self):
            raise deny(self)
        return real_path_open(self, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(io, "open", fake_open)
    monkeypatch.setattr(os, "open", fake_os_open)
    monkeypatch.setattr(pathlib.Path, "open", fake_path_open)


def refuse_to_list(monkeypatch: pytest.MonkeyPatch, target: Path) -> None:
    """os.scandir raises PermissionError for `target` (the container runs as root, so
    chmod cannot make a folder unlistable)."""
    blocked = os.path.realpath(target)
    real_scandir = os.scandir

    def fake_scandir(path="."):
        if isinstance(path, str | bytes | os.PathLike) and (
            os.path.realpath(os.fsdecode(path)) == blocked
        ):
            raise PermissionError(errno.EACCES, "refused by test", os.fsdecode(path))
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", fake_scandir)


# ---------------------------------------------------------------------------- B1 root


@pytest.mark.parametrize(
    "argument",
    ["steam", "steam/", "./steam", "steam//", "other/../steam", "./other/./../steam/."],
)
def test_b1_relative_root_is_made_absolute_and_normalized(tmp_path, monkeypatch, argument):
    root = make_root(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = discover.scan(argument)
    assert result["steam_root"] == str(root)
    assert isinstance(result["steam_root"], str)
    assert result["libraries"][0] == lib(root)
    assert discover.find_libraries(argument)[0] == lib(root)


def test_b1_absolute_root_with_dot_parts_is_normalized(tmp_path):
    root = make_root(tmp_path)
    argument = f"{tmp_path}/x/../steam/./"
    assert discover.scan(argument)["steam_root"] == str(root)


def test_b1_pathlike_root_is_accepted_and_reported_as_str(tmp_path):
    root = make_root(tmp_path)
    result = discover.scan(root)
    assert result["steam_root"] == str(root)
    assert type(result["steam_root"]) is str
    assert discover.find_libraries(root) == [lib(root)]


def test_b1_symlinked_root_is_kept_as_given_not_resolved(tmp_path):
    real = make_root(tmp_path, name="real_steam")
    link = tmp_path / "steam_link"
    link.symlink_to(real, target_is_directory=True)
    result = discover.scan(str(link))
    assert result["steam_root"] == str(link)
    # libraryfolders.vdf lists the real path as "0", as Steam does: the same real path,
    # so the root (as given) wins and the listed copy is dropped (B2).
    assert result["libraries"] == [lib(link)]
    assert discover.find_libraries(str(link)) == [lib(link)]
    assert [card["library"] for card in result["games"]] == [str(link)]
    assert result["games"][0]["install_path"] == str(link / "steamapps" / "common" / "Game10")
    assert result["warnings"] == []
    assert result["errors"] == []


def test_b1_tilde_is_a_folder_name_not_home(tmp_path, monkeypatch):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    root = make_root(tmp_path, name="~")
    monkeypatch.chdir(tmp_path)
    result = discover.scan("~")
    assert result["steam_root"] == str(root)
    assert result["libraries"] == [lib(root)]
    assert discover.find_libraries("~") == [lib(root)]


@pytest.mark.parametrize("function", ["scan", "find_libraries"])
@pytest.mark.parametrize("layout", ["no_file", "no_steamapps", "no_root"])
def test_b1_missing_libraryfolders_raises_discover_error(tmp_path, function, layout):
    assert issubclass(discover.DiscoverError, Exception)
    root = tmp_path / "steam"
    if layout != "no_root":
        root.mkdir()
    if layout == "no_file":
        (root / "steamapps").mkdir()
    with pytest.raises(discover.DiscoverError):
        getattr(discover, function)(str(root))


def _padded(text: str, size: int) -> bytes:
    data = text.encode("utf-8")
    assert len(data) <= size
    return data + b" " * (size - len(data))


UNUSABLE = {
    "directory": None,
    "larger_than_1_mib": "too_large",
    "latin1_not_utf8": f'"libraryfolders"\n{{\n\t"0"\n\t{{\n\t\t"path"\t\t"/caf\xe9 {MARKER}"\n'
    "\t}\n}\n".encode("latin-1"),
    "utf16_not_utf8": f'"libraryfolders"\n{{\n\t"note"\t\t"{MARKER}"\n}}\n'.encode("utf-16"),
    "unclosed_block": f'"libraryfolders"\n{{\n\t"0"\n\t{{\n\t\t"label"\t\t"{MARKER}"\n',
    "stray_brace": f'"libraryfolders"\n{{\n}}\n}}\n"{MARKER}"\t\t"x"\n',
    "empty_file": "",
    "no_libraryfolders_key": f'"InstallConfigStore"\n{{\n\t"label"\t\t"{MARKER}"\n}}\n',
}


@pytest.mark.parametrize("function", ["scan", "find_libraries"])
@pytest.mark.parametrize("case", sorted(UNUSABLE))
def test_b1_unusable_libraryfolders_raises_discover_error(tmp_path, function, case):
    root = make_root(tmp_path)
    target = root / "steamapps" / "libraryfolders.vdf"
    content = UNUSABLE[case]
    if case == "directory":
        target.unlink()
        target.mkdir()
    elif content == "too_large":
        target.write_bytes(_padded(current_layout(("0", str(root))), MIB + 1))
    else:
        write_libraryfolders(root, content)
    with pytest.raises(discover.DiscoverError) as caught:
        getattr(discover, function)(str(root))
    assert MARKER not in str(caught.value)


@pytest.mark.parametrize("function", ["scan", "find_libraries"])
def test_b1_libraryfolders_that_cannot_be_read_raises_discover_error(
    tmp_path, monkeypatch, function
):
    root = make_root(tmp_path)
    refuse_to_open(monkeypatch, root / "steamapps" / "libraryfolders.vdf")
    with pytest.raises(discover.DiscoverError):
        getattr(discover, function)(str(root))


def test_b1_libraryfolders_of_exactly_1_mib_is_accepted(tmp_path):
    sd = make_library(tmp_path / "sd", 20)
    root = make_root(tmp_path)
    write_libraryfolders(root, _padded(current_layout(("0", str(root)), ("1", str(sd))), MIB))
    assert (root / "steamapps" / "libraryfolders.vdf").stat().st_size == MIB
    result = discover.scan(str(root))
    assert result["libraries"] == [lib(root), lib(sd)]
    assert [card["appid"] for card in result["games"]] == [10, 20]


@pytest.mark.parametrize("layout", [current_layout, legacy_layout])
def test_b1_leading_bom_is_accepted(tmp_path, layout):
    sd = make_library(tmp_path / "sd", 20)
    root = make_root(tmp_path)
    write_libraryfolders(root, b"\xef\xbb\xbf" + layout(("1", str(sd))).encode("utf-8"))
    result = discover.scan(str(root))
    assert result["libraries"] == [lib(root), lib(sd)]
    assert discover.find_libraries(str(root)) == [lib(root), lib(sd)]
    assert result["warnings"] == []


# ---------------------------------------------------------------------------- B2 libraries


def test_b2_current_layout_lists_root_then_numbered_blocks(tmp_path):
    sd = make_library(tmp_path / "sd", 20)
    root = make_root(tmp_path, ("1", str(sd)))
    assert discover.find_libraries(str(root)) == [lib(root), lib(sd)]
    result = discover.scan(str(root))
    assert result["libraries"] == [lib(root), lib(sd)]
    assert [(card["appid"], card["library"]) for card in result["games"]] == [
        (10, str(root)),
        (20, str(sd)),
    ]
    assert result["warnings"] == []
    assert result["errors"] == []


def test_b2_legacy_layout_uses_path_strings(tmp_path):
    sd = make_library(tmp_path / "sd", 20)
    root = make_root(tmp_path)
    write_libraryfolders(root, legacy_layout(("1", str(sd))))
    assert discover.find_libraries(str(root)) == [lib(root), lib(sd)]
    result = discover.scan(str(root))
    assert result["libraries"] == [lib(root), lib(sd)]
    assert library_names(result) == {str(root), str(sd)}
    assert result["warnings"] == []


def test_b2_current_and_legacy_values_may_be_mixed(tmp_path):
    sd = make_library(tmp_path / "sd", 20)
    usb = make_library(tmp_path / "usb", 30)
    root = make_root(tmp_path)
    text = current_layout(("1", str(sd)), extra=f'\t"2"\t\t{q(str(usb))}\n')
    write_libraryfolders(root, text)
    assert discover.find_libraries(str(root)) == [lib(root), lib(sd), lib(usb)]


def test_b2_numbered_keys_sort_numerically(tmp_path):
    one = make_library(tmp_path / "lib_one", 1001)
    two = make_library(tmp_path / "lib_two", 1002)
    ten = make_library(tmp_path / "lib_ten", 1010)
    root = make_root(tmp_path, ("10", str(ten)), ("2", str(two)), ("1", str(one)))
    expected = [lib(root), lib(one), lib(two), lib(ten)]
    assert discover.find_libraries(str(root)) == expected
    assert discover.scan(str(root))["libraries"] == expected


def test_b2_legacy_numbered_keys_sort_numerically(tmp_path):
    two = make_library(tmp_path / "lib_two")
    ten = make_library(tmp_path / "lib_ten")
    root = make_root(tmp_path)
    write_libraryfolders(root, legacy_layout(("10", str(ten)), ("2", str(two))))
    assert discover.find_libraries(str(root)) == [lib(root), lib(two), lib(ten)]


def test_b2_non_numbered_keys_are_ignored(tmp_path):
    hidden = [make_library(tmp_path / f"hidden_{n}", 900 + n) for n in range(4)]
    sd = make_library(tmp_path / "sd", 20)
    extra = "".join(
        current_entry(key, str(path))
        for key, path in zip(["extra", "1a", "x1", "label"], hidden, strict=True)
    )
    root = make_root(tmp_path, ("1", str(sd)))
    write_libraryfolders(root, current_layout(("0", str(root)), ("1", str(sd)), extra=extra))
    assert discover.find_libraries(str(root)) == [lib(root), lib(sd)]
    result = discover.scan(str(root))
    assert result["libraries"] == [lib(root), lib(sd)]
    assert [card["appid"] for card in result["games"]] == [10, 20]
    assert result["warnings"] == []


def test_b2_numbered_block_without_path_is_skipped_with_warning(tmp_path):
    sd = make_library(tmp_path / "sd", 20)
    no_path = '\t"1"\n\t{\n\t\t"label"\t\t"SD card"\n\t\t"apps"\n\t\t{\n\t\t}\n\t}\n'
    root = make_root(tmp_path)
    text = current_layout(("0", str(root)), extra=no_path + current_entry("2", str(sd)))
    write_libraryfolders(root, text)
    assert discover.find_libraries(str(root)) == [lib(root), lib(sd)]
    result = discover.scan(str(root))
    assert result["libraries"] == [lib(root), lib(sd)]
    assert pairs(result["warnings"]) == [("library_entry_invalid", None)]
    assert result["errors"] == []


@pytest.mark.parametrize(
    "written",
    [
        pytest.param("", id="empty"),
        pytest.param("relative/SteamLibrary", id="relative"),
        pytest.param("D:\\SteamLibrary", id="windows"),
        pytest.param("BACKSLASH", id="absolute-with-backslash"),
    ],
)
@pytest.mark.parametrize("layout", [current_layout, legacy_layout])
def test_b2_invalid_library_path_stays_unavailable_with_warning(
    tmp_path, monkeypatch, written, layout
):
    if written == "BACKSLASH":
        # A real, valid-looking library whose name contains a backslash: still refused.
        written = str(make_library(tmp_path / "SteamLibrary\\sd", 30))
    make_library(tmp_path / "relative" / "SteamLibrary", 40)
    monkeypatch.chdir(tmp_path)
    sd = make_library(tmp_path / "sd", 20)
    root = make_root(tmp_path)
    write_libraryfolders(root, layout(("1", written), ("2", str(sd))))
    for libraries in (discover.find_libraries(str(root)), discover.scan(str(root))["libraries"]):
        assert len(libraries) == 3
        assert libraries[0] == lib(root)
        assert libraries[1]["available"] is False
        assert libraries[1]["path"] in {written, os.path.normpath(written)}
        assert libraries[2] == lib(sd)
    result = discover.scan(str(root))
    assert pairs(result["warnings"]) == [("library_path_invalid", written)]
    assert [card["appid"] for card in result["games"]] == [10, 20]


@pytest.mark.parametrize(
    ("cwd_name", "written"),
    [
        pytest.param("steam", ".", id="dot-while-cwd-is-root"),
        pytest.param("steam", "steamapps/..", id="parent-while-cwd-is-root"),
        pytest.param("", "elsewhere", id="relative-to-a-real-library"),
    ],
)
def test_b2_relative_library_path_is_never_resolved_against_cwd(
    tmp_path, monkeypatch, cwd_name, written
):
    make_library(tmp_path / "elsewhere", 50)
    root = make_root(tmp_path, ("1", written))
    monkeypatch.chdir(tmp_path / cwd_name)
    expected_paths = {written, os.path.normpath(written)}
    for libraries in (discover.find_libraries(str(root)), discover.scan(str(root))["libraries"]):
        assert len(libraries) == 2
        assert libraries[0] == lib(root)
        assert libraries[1]["available"] is False
        assert libraries[1]["path"] in expected_paths
    result = discover.scan(str(root))
    assert pairs(result["warnings"]) == [("library_path_invalid", written)]
    assert [(card["appid"], card["library"]) for card in result["games"]] == [(10, str(root))]


def test_b2_listed_paths_are_normalized(tmp_path):
    sd = make_library(tmp_path / "sd", 20)
    usb = make_library(tmp_path / "usb", 30)
    root = make_root(tmp_path, ("1", f"{sd}/./"), ("2", f"{tmp_path}//nowhere/../usb"))
    expected = [lib(root), lib(sd), lib(usb)]
    assert discover.find_libraries(str(root)) == expected
    result = discover.scan(str(root))
    assert result["libraries"] == expected
    assert [(card["library"], card["install_path"]) for card in result["games"]] == [
        (str(root), str(root / "steamapps" / "common" / "Game10")),
        (str(sd), str(sd / "steamapps" / "common" / "Game20")),
        (str(usb), str(usb / "steamapps" / "common" / "Game30")),
    ]
    assert result["warnings"] == []


def test_b2_libraries_are_deduplicated_by_real_path_first_wins(tmp_path):
    sd_real = make_library(tmp_path / "sd_real", 20)
    sd_link = tmp_path / "media" / "sd_link"
    sd_link.parent.mkdir()
    sd_link.symlink_to(sd_real, target_is_directory=True)
    root = make_root(tmp_path)
    root_link = tmp_path / "steam_link"
    root_link.symlink_to(root, target_is_directory=True)
    text = current_layout(
        ("0", str(root)),
        ("1", str(sd_link)),
        ("2", str(sd_real)),
        ("3", f"{sd_real}/"),
        ("4", str(root_link)),
        ("5", f"{root}/steamapps/.."),
    )
    write_libraryfolders(root, text)
    expected = [lib(root), lib(sd_link)]
    assert discover.find_libraries(str(root)) == expected
    result = discover.scan(str(root))
    assert result["libraries"] == expected
    assert [(card["appid"], card["library"]) for card in result["games"]] == [
        (10, str(root)),
        (20, str(sd_link)),
    ]
    assert result["games"][1]["install_path"] == str(sd_link / "steamapps" / "common" / "Game20")
    assert result["warnings"] == []


def test_b2_root_wins_over_an_earlier_listed_alias(tmp_path):
    root = make_root(tmp_path)
    root_link = tmp_path / "steam_link"
    root_link.symlink_to(root, target_is_directory=True)
    write_libraryfolders(root, current_layout(("0", str(root_link)), ("1", str(root))))
    assert discover.find_libraries(str(root)) == [lib(root)]
    assert discover.scan(str(root_link))["libraries"] == [lib(root_link)]


def _no_library_folder(path: Path) -> None:
    path.mkdir()


def _steamapps_is_a_file(path: Path) -> None:
    path.mkdir()
    (path / "steamapps").write_text("not a folder", encoding="utf-8")


def _steamapps_is_a_broken_link(path: Path) -> None:
    path.mkdir()
    (path / "steamapps").symlink_to(path / "gone", target_is_directory=True)


@pytest.mark.parametrize(
    "build",
    [
        pytest.param(None, id="path-missing"),
        pytest.param(_no_library_folder, id="no-steamapps"),
        pytest.param(_steamapps_is_a_file, id="steamapps-is-a-file"),
        pytest.param(_steamapps_is_a_broken_link, id="steamapps-is-a-broken-link"),
    ],
)
def test_b2_library_without_steamapps_folder_is_unavailable(tmp_path, build):
    gone = tmp_path / "sd"
    if build is not None:
        build(gone)
    usb = make_library(tmp_path / "usb", 30)
    root = make_root(tmp_path, ("1", str(gone)), ("2", str(usb)))
    expected = [lib(root), lib(gone, available=False), lib(usb)]
    assert discover.find_libraries(str(root)) == expected
    result = discover.scan(str(root))
    assert result["libraries"] == expected
    assert pairs(result["warnings"]) == [("library_unavailable", str(gone))]
    assert result["errors"] == []
    assert library_names(result) == {str(root), str(usb)}


@pytest.mark.parametrize("which", ["sd", "root"])
def test_b2_unlistable_steamapps_is_unreadable_and_unavailable(tmp_path, monkeypatch, which):
    sd = make_library(tmp_path / "sd", 20)
    root = make_root(tmp_path, ("1", str(sd)))
    blocked = sd if which == "sd" else root
    other = root if which == "sd" else sd
    refuse_to_list(monkeypatch, blocked / "steamapps")
    expected = [lib(root, available=which != "root"), lib(sd, available=which != "sd")]
    assert discover.find_libraries(str(root)) == expected
    result = discover.scan(str(root))
    assert result["libraries"] == expected
    assert [issue["code"] for issue in result["errors"]] == ["library_unreadable"]
    assert result["errors"][0]["path"] in {str(blocked), str(blocked / "steamapps")}
    assert pairs(result["warnings"]) == [("library_unavailable", str(blocked))]
    assert library_names(result) == {str(other)}


def test_b2_find_libraries_equals_scan_libraries_and_has_the_spec_shape(tmp_path):
    sd = make_library(tmp_path / "sd", 20)
    root = make_root(tmp_path, ("2", "relative"), ("1", str(sd)), ("3", str(tmp_path / "gone")))
    found = discover.find_libraries(str(root))
    assert found == discover.scan(str(root))["libraries"]
    assert [entry["available"] for entry in found] == [True, True, False, False]
    for entry in found:
        assert set(entry) == {"path", "available"}
        assert type(entry["path"]) is str
        assert type(entry["available"]) is bool
