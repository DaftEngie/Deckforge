# Contracts for deckforge.discover, PR B1 of docs/specs/discover.md: criteria B7 (output),
# B8 (CLI) and B9 (read-only), with the Safety section's "no writes, no subprocesses, no
# network". Written test-first; src/deckforge/discover.py does not exist yet.
#
# Output, criterion B7 (scan)
#   Post: the keys are exactly discover_version, steam_root, libraries, games, errors and
#         warnings. discover_version is the int 1 (not a bool).
#   Post: games are sorted by (appid, library); errors and warnings are sorted by
#         (code, path or ""). Every issue is {"code": str, "path": str or None,
#         "message": str}.
#   Inv:  no timestamps or other run-dependent data: two scans of one tree are equal, and
#         two trees built in a different creation order give equal results once their
#         root paths are replaced by one placeholder. ext4 lists small folders in hash
#         order whatever the creation order, so the second tree is also listed through
#         an os.scandir wrapper that reverses every listing (the spec makes os.scandir
#         the one listing call so that tests can patch it).
#
# CLI, criterion B8 (main, argv defaulting to None)
#   Pre:  argv is a list of str, or None to read sys.argv[1:]. --steam-root is required.
#   Post: on success, stdout receives exactly the B8 JSON text of scan(root) (indent 2,
#         sorted keys, ASCII only) plus one newline, in a single write call, and main
#         returns 0, even when errors or warnings are present.
#   Post: no --steam-root: argparse exits with SystemExit(2) and stdout stays empty.
#   Post: DiscoverError: one non-empty line on stderr (no file contents), nothing on stdout,
#         returns 2.
#   Post: any other exception propagates unchanged (no catch-all, R12).
#   Inv:  writes no files and leaves the current folder as it was. `python -m
#         deckforge.discover` runs main and exits with its return value.
#
# Read-only, criterion B9 (scan, find_libraries and main)
#   Inv:  the Steam tree is unchanged by a run: every entry keeps its name, type, mode,
#         size, modification and change times, inode, link count, link target and file
#         bytes. The detector uses lstat and never follows links.
#   Inv:  the only files opened are <root>/steamapps/libraryfolders.vdf,
#         <library>/steamapps/appmanifest_*.acf and <root>/config/config.vdf, each read-only
#         and each a regular file (or a link to one). Settings files, prefixes, other .vdf
#         files and look-alike names are never opened.
#   Inv:  folders are listed with os.scandir (each available library's steamapps is).
#
# Source rules for src/deckforge/discover.py, checked on its syntax tree (B9)
#   Imports only __future__, argparse, json, logging, os, stat, sys, pathlib, re, fnmatch,
#   dataclasses, typing, collections and deckforge.* (relative imports inside deckforge).
#   No attribute call named write, write_text, write_bytes, unlink, remove, rmdir, mkdir,
#   makedirs, rename, replace, touch, chmod, symlink_to, hardlink_to, symlink, link or
#   truncate, except sys.stdout.write and sys.stderr.write; no import of those names and
#   no getattr of them by literal name.
#   Every open(...) call passes a literal mode "r" or "rb"; os.open is not used (its flags
#   are not a literal mode), and open is never passed around as a value.
#   Listing uses os.scandir only: no listdir, walk, fwalk, iterdir, glob or rglob, and no
#   scandir imported under another name, so tests can patch os.scandir.
#   Safety section: no process or other file-changing os calls (system, popen, spawn*,
#   exec*, fork, kill, utime, chown, ...), and no eval, exec, compile or __import__.
#
# The write-then-restore round trip of the test-author rules does not apply: PR B1 has no
# write path. Its property is the opposite one, checked across several tree shapes: any
# number of runs leaves every byte and every lstat field as it was.

import ast
import builtins
import io
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from deckforge import discover

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
DISCOVER_SOURCE = SRC / "deckforge" / "discover.py"
MARKER = "df-planted-cli-text-0b6e"
TOP_LEVEL_KEYS = {"discover_version", "steam_root", "libraries", "games", "errors", "warnings"}
CONFIG_VDF = (
    '"InstallConfigStore"\n{\n\t"Software"\n\t{\n\t\t"Valve"\n\t\t{\n\t\t\t"Steam"\n\t\t\t{\n'
    '\t\t\t\t"CompatToolMapping"\n\t\t\t\t{\n'
    '\t\t\t\t\t"10"\n\t\t\t\t\t{\n\t\t\t\t\t\t"name"\t\t"proton_9"\n\t\t\t\t\t}\n'
    '\t\t\t\t\t"2246340"\n\t\t\t\t\t{\n\t\t\t\t\t\t"name"\t\t"proton_9"\n\t\t\t\t\t}\n'
    "\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n}\n"
)
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
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
MANIFEST_NAME = re.compile(r"appmanifest_.+\.acf")


# ---------------------------------------------------------------------------- helpers


def q(text: str) -> str:
    """A VDF quoted string, escaped the way Steam writes it."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def manifest(appid: str, name: str | None, installdir: str | None = None) -> str:
    lines = ['"AppState"', "{", f'\t"appid"\t\t{q(appid)}', '\t"universe"\t\t"1"']
    if name is not None:
        lines.append(f'\t"name"\t\t{q(name)}')
    lines.append('\t"StateFlags"\t\t"4"')
    if installdir is not None:
        lines.append(f'\t"installdir"\t\t{q(installdir)}')
    lines += ['\t"buildid"\t\t"100"', "}"]
    return "\n".join(lines) + "\n"


def mkdir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def put(path: Path, data: str | bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
    return path


def add_game(library: Path, appid: int, name: str | None = None) -> None:
    mkdir(library / "steamapps" / "common" / f"Game{appid}")
    (library / "steamapps" / f"appmanifest_{appid}.acf").write_text(
        manifest(str(appid), name or f"Game {appid}", f"Game{appid}"), encoding="utf-8"
    )


def libraryfolders(entries: list[tuple[str, str]]) -> str:
    blocks = "".join(
        f'\t{q(key)}\n\t{{\n\t\t"path"\t\t{q(path)}\n\t\t"label"\t\t""\n\t}}\n'
        for key, path in entries
    )
    return '"libraryfolders"\n{\n\t"contentstatsid"\t\t"-4917390201925046562"\n' + blocks + "}\n"


def make_root(base: Path, *libraries: Path, config: bool = True) -> Path:
    root = mkdir(base / "steam" / "steamapps").parent
    entries = [(str(n), str(path)) for n, path in enumerate([root, *libraries])]
    (root / "steamapps" / "libraryfolders.vdf").write_text(
        libraryfolders(entries), encoding="utf-8"
    )
    if config:
        mkdir(root / "config")
        (root / "config" / "config.vdf").write_text(CONFIG_VDF, encoding="utf-8")
    return root


def pairs(issues: list[dict]) -> list[tuple[str, str | None]]:
    return [(issue["code"], issue["path"]) for issue in issues]


def expected_stdout(root: Path) -> str:
    return json.dumps(discover.scan(str(root)), indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def busy_tree(base: Path) -> Path:
    """A tree whose scan has games, errors and warnings, and a non-ASCII game name."""
    sd = mkdir(base / "sd")
    root = make_root(base, sd, base / "gone", config=False)
    add_game(root, 2246340, "Monster Hunter Wilds")
    add_game(sd, 587620, "Ōkami HD 大神")
    (sd / "steamapps" / "appmanifest_71.acf").write_text('"AppState"\n{\n', encoding="utf-8")
    return root


class WriteRecorder:
    """Stands in for sys.stdout and keeps every write call."""

    encoding = "utf-8"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def write(self, text: str) -> int:
        self.calls.append(text)
        return len(text)

    def flush(self) -> None:
        return None


class ReversedListing:
    """Behaves like the iterator os.scandir returns, with the entries in reverse order."""

    def __init__(self, entries: list) -> None:
        self._entries = iter(entries[::-1])

    def __iter__(self) -> "ReversedListing":
        return self

    def __next__(self):
        return next(self._entries)

    def __enter__(self) -> "ReversedListing":
        return self

    def __exit__(self, *exc_info: object) -> None:
        return None

    def close(self) -> None:
        return None


def list_in_reverse(monkeypatch: pytest.MonkeyPatch) -> None:
    real_scandir = os.scandir

    def reversed_scandir(path="."):
        with real_scandir(path) as listing:
            return ReversedListing(list(listing))

    monkeypatch.setattr(os, "scandir", reversed_scandir)


class Boom(Exception):
    """An unexpected failure that main must not catch."""


def run_module(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    return subprocess.run(
        [sys.executable, "-m", "deckforge.discover", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


# ---------------------------------------------------------------------------- B7 output


def test_b7_top_level_keys_and_version(tmp_path):
    root = make_root(tmp_path)
    add_game(root, 70)
    result = discover.scan(str(root))
    assert set(result) == TOP_LEVEL_KEYS
    assert result["discover_version"] == 1
    assert type(result["discover_version"]) is int
    assert result["steam_root"] == str(root)
    assert result["libraries"] == [{"path": str(root), "available": True}]
    assert [card["appid"] for card in result["games"]] == [70]
    assert result["errors"] == []
    assert result["warnings"] == []


def test_b7_result_is_plain_json_data(tmp_path):
    result = discover.scan(str(busy_tree(tmp_path)))
    assert json.loads(json.dumps(result)) == result


def test_b7_games_are_sorted_by_appid_then_library(tmp_path):
    a_sd = mkdir(tmp_path / "a_sd" / "steamapps").parent
    m_usb = mkdir(tmp_path / "m_usb" / "steamapps").parent
    root = make_root(tmp_path, m_usb, a_sd)
    placement = [(root, 2246340), (m_usb, 70), (root, 70), (a_sd, 1086940), (a_sd, 70)]
    placement += [(m_usb, 10), (root, 9)]
    for library, appid in placement:
        add_game(library, appid)
    result = discover.scan(str(root))
    got = [(card["appid"], card["library"]) for card in result["games"]]
    assert got == sorted((appid, str(library)) for library, appid in placement)
    assert got[2:5] == [(70, str(a_sd)), (70, str(m_usb)), (70, str(root))]


def test_b7_issue_lists_are_sorted_by_code_then_path(tmp_path):
    sd = mkdir(tmp_path / "sd" / "steamapps").parent
    root = make_root(tmp_path, tmp_path / "zz_gone", sd, tmp_path / "aa_gone", config=False)
    lf = root / "steamapps" / "libraryfolders.vdf"
    text = lf.read_text(encoding="utf-8").rsplit("}", 1)[0]
    text += '\t"7"\n\t{\n\t\t"label"\t\t"no path"\n\t}\n\t"8"\t\t"relative"\n}\n'
    lf.write_text(text, encoding="utf-8")
    add_game(root, 70)
    add_game(sd, 70)
    broken = {
        root / "steamapps" / "appmanifest_81.acf": ("manifest_malformed", '"AppState"\n{\n'),
        sd / "steamapps" / "appmanifest_82.acf": ("manifest_malformed", "{"),
        sd / "steamapps" / "appmanifest_83.acf": ("manifest_incomplete", manifest("83", "x")),
        root / "steamapps" / "appmanifest_84.acf": (
            "manifest_appid_mismatch",
            manifest("85", "x", "X"),
        ),
    }
    for path, (_, content) in broken.items():
        path.write_text(content, encoding="utf-8")
    result = discover.scan(str(root))
    later = max(str(root), str(sd))
    expected_warnings = [
        ("config_vdf_missing", str(root / "config" / "config.vdf")),
        ("duplicate_appid", str(Path(later, "steamapps", "appmanifest_70.acf"))),
        ("library_entry_invalid", None),
        ("library_path_invalid", "relative"),
        ("library_unavailable", str(tmp_path / "aa_gone")),
        ("library_unavailable", str(tmp_path / "zz_gone")),
    ]
    assert pairs(result["warnings"]) == expected_warnings
    expected_errors = sorted((code, str(path)) for path, (code, _) in broken.items())
    assert pairs(result["errors"]) == expected_errors
    for issue in result["errors"] + result["warnings"]:
        assert set(issue) == {"code", "path", "message"}
        assert isinstance(issue["message"], str)


def test_b7_two_scans_of_one_tree_are_equal(tmp_path, monkeypatch):
    root = busy_tree(tmp_path)
    first = discover.scan(str(root))
    assert discover.scan(str(root)) == first
    with monkeypatch.context() as patch:
        list_in_reverse(patch)
        assert discover.scan(str(root)) == first


def _build_in_order(base: Path, reverse: bool) -> Path:
    root, sd, usb = base / "steam", base / "sd", base / "usb"
    keyed = [("0", str(root)), ("1", str(sd)), ("2", str(usb)), ("3", str(base / "gone"))]
    steps = [
        lambda: mkdir(root / "config"),
        lambda: put(root / "config" / "config.vdf", CONFIG_VDF),
        lambda: mkdir(root / "steamapps"),
        lambda: put(
            root / "steamapps" / "libraryfolders.vdf",
            libraryfolders(keyed[::-1] if reverse else keyed),
        ),
        lambda: add_game(root, 2246340, "Monster Hunter Wilds"),
        lambda: add_game(root, 70),
        lambda: add_game(sd, 70),
        lambda: add_game(sd, 30),
        lambda: add_game(usb, 20),
        lambda: add_game(usb, 1086940),
        lambda: mkdir(root / "steamapps" / "compatdata" / "30" / "pfx"),
        lambda: mkdir(sd / "steamapps" / "shadercache" / "30"),
        lambda: mkdir(usb / "steamapps" / "compatdata" / "20" / "pfx"),
        lambda: put(sd / "steamapps" / "appmanifest_91.acf", "{"),
        lambda: put(usb / "steamapps" / "appmanifest_92.acf", "{"),
        lambda: put(root / "steamapps" / "appmanifest_93.acf", "{"),
        lambda: put(usb / "steamapps" / "appmanifest_94.acf", manifest("94", None, "Game94")),
    ]
    for step in steps[::-1] if reverse else steps:
        step()
    return root


def test_b7_creation_and_listing_order_do_not_change_the_result(tmp_path, monkeypatch):
    base_a, base_b = mkdir(tmp_path / "tree_a"), mkdir(tmp_path / "tree_b")
    root_a = _build_in_order(base_a, reverse=False)
    root_b = _build_in_order(base_b, reverse=True)
    text_a = json.dumps(discover.scan(str(root_a)), sort_keys=True)
    with monkeypatch.context() as patch:
        list_in_reverse(patch)
        text_b = json.dumps(discover.scan(str(root_b)), sort_keys=True)
    assert str(base_b) not in text_a
    assert str(base_a) not in text_b
    assert text_a.replace(str(base_a), "<BASE>") == text_b.replace(str(base_b), "<BASE>")


# ---------------------------------------------------------------------------- B8 CLI


def test_b8_main_prints_exactly_the_scan_json_and_returns_0_despite_issues(tmp_path, capsys):
    root = busy_tree(tmp_path)
    expected = expected_stdout(root)
    result = json.loads(expected)
    assert result["errors"] != []
    assert result["warnings"] != []
    assert "\\u014ckami" in expected
    assert discover.main(["--steam-root", str(root)]) == 0
    assert capsys.readouterr().out == expected


def test_b8_main_accepts_the_equals_form(tmp_path, capsys):
    root = busy_tree(tmp_path)
    expected = expected_stdout(root)
    assert discover.main([f"--steam-root={root}"]) == 0
    assert capsys.readouterr().out == expected


def test_b8_stdout_gets_the_json_in_one_write(tmp_path, monkeypatch):
    root = busy_tree(tmp_path)
    expected = expected_stdout(root)
    recorder = WriteRecorder()
    monkeypatch.setattr(sys, "stdout", recorder)
    assert discover.main(["--steam-root", str(root)]) == 0
    assert [text for text in recorder.calls if text] == [expected]


def test_b8_main_without_argv_reads_sys_argv(tmp_path, monkeypatch, capsys):
    root = busy_tree(tmp_path)
    expected = expected_stdout(root)
    monkeypatch.setattr(sys, "argv", ["deckforge.discover", "--steam-root", str(root)])
    assert discover.main() == 0
    assert capsys.readouterr().out == expected


@pytest.mark.parametrize(
    "argv",
    [[], ["--steam-root"], ["--steamroot", "x"], ["x"]],
    ids=["none", "no-value", "typo", "positional"],
)
def test_b8_missing_steam_root_flag_exits_2(tmp_path, monkeypatch, capsys, argv):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as caught:
        discover.main(argv)
    assert caught.value.code == 2
    assert capsys.readouterr().out == ""


def test_b8_missing_steam_root_flag_exits_2_from_sys_argv(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["deckforge.discover"])
    with pytest.raises(SystemExit) as caught:
        discover.main()
    assert caught.value.code == 2
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("problem", ["missing", "unparsable", "no-key", "no-root"])
def test_b8_discover_error_returns_2_with_one_line_on_stderr(tmp_path, capsys, problem):
    root = make_root(tmp_path)
    lf = root / "steamapps" / "libraryfolders.vdf"
    if problem == "missing":
        lf.unlink()
    elif problem == "unparsable":
        lf.write_text(f'"libraryfolders"\n{{\n\t"{MARKER}"\n', encoding="utf-8")
    elif problem == "no-key":
        lf.write_text(f'"InstallConfigStore"\n{{\n\t"label"\t\t"{MARKER}"\n}}\n', encoding="utf-8")
    else:
        root = tmp_path / "no_such_steam"
    assert discover.main(["--steam-root", str(root)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    message = captured.err.strip()
    assert message != ""
    assert "\n" not in message
    assert MARKER not in captured.err


def test_b8_other_exceptions_propagate_unchanged(tmp_path, monkeypatch, capsys):
    root = busy_tree(tmp_path)

    def broken_scandir(path="."):
        raise Boom(os.fsdecode(path))

    monkeypatch.setattr(os, "scandir", broken_scandir)
    with pytest.raises(Boom):
        discover.main(["--steam-root", str(root)])
    assert capsys.readouterr().out == ""


def test_b8_cwd_is_unchanged_and_no_file_is_written_there(tmp_path, monkeypatch, capsys):
    root = busy_tree(tmp_path / "data")
    empty = mkdir(tmp_path / "empty_cwd")
    monkeypatch.chdir(empty)
    assert discover.main(["--steam-root", str(root)]) == 0
    assert capsys.readouterr().out.startswith("{")
    assert Path.cwd() == empty
    assert list(empty.iterdir()) == []


def test_b8_relative_steam_root_is_taken_from_the_cwd(tmp_path, monkeypatch, capsys):
    root = busy_tree(tmp_path)
    expected = expected_stdout(root)
    monkeypatch.chdir(tmp_path)
    assert discover.main(["--steam-root", "steam"]) == 0
    assert capsys.readouterr().out == expected
    assert Path.cwd() == tmp_path


def test_b8_module_runs_main_as_a_script(tmp_path):
    root = busy_tree(tmp_path / "data")
    empty = mkdir(tmp_path / "empty_cwd")
    expected = expected_stdout(root)
    ok = run_module(["--steam-root", str(root)], empty)
    assert ok.returncode == 0, ok.stderr
    assert ok.stdout == expected
    usage = run_module([], empty)
    assert usage.returncode == 2
    assert usage.stdout == ""
    missing = run_module(["--steam-root", str(tmp_path / "no_such_steam")], empty)
    assert missing.returncode == 2
    assert missing.stdout == ""
    assert missing.stderr.strip() != ""
    assert "\n" not in missing.stderr.strip()
    assert "Traceback" not in missing.stderr
    assert list(empty.iterdir()) == []


# ---------------------------------------------------------------------------- source rules


def source_tree() -> ast.Module:
    return ast.parse(DISCOVER_SOURCE.read_text(encoding="utf-8"), filename=str(DISCOVER_SOURCE))


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


def mode_argument(call: ast.Call, position: int) -> ast.AST | None:
    for keyword in call.keywords:
        if keyword.arg == "mode":
            return keyword.value
    return call.args[position] if len(call.args) > position else None


def test_b9_the_checked_source_is_the_module_under_test():
    assert Path(discover.__file__).resolve() == DISCOVER_SOURCE.resolve()


def test_b9_imports_only_the_allowlist():
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


def test_b9_no_banned_attribute_calls():
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
            and call.args[1].value in BANNED_CALLS
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


def test_b9_every_open_call_uses_a_literal_read_mode():
    tree = source_tree()
    offenders = []
    open_funcs = set()
    for call in calls(tree):
        func = call.func
        if isinstance(func, ast.Name) and func.id == "open":
            mode = mode_argument(call, 1)
        elif isinstance(func, ast.Attribute) and func.attr == "open":
            if dotted(func) == "os.open":
                offenders.append(f"line {call.lineno}: os.open() takes flags, not a mode")
                continue
            mode = mode_argument(call, 0)
        else:
            continue
        open_funcs.add(id(func))
        if not (isinstance(mode, ast.Constant) and mode.value in ("r", "rb")):
            offenders.append(f"line {call.lineno}: open() without a literal 'r' or 'rb' mode")
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "open" and id(node) not in open_funcs:
            offenders.append(f"line {node.lineno}: open used as a value")
    assert offenders == []


def test_b9_folders_are_listed_only_with_os_scandir():
    offenders = []
    for node in ast.walk(source_tree()):
        if isinstance(node, ast.Attribute) and node.attr in OTHER_LISTING:
            offenders.append(f"line {node.lineno}: .{node.attr}")
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "scandir"
            and dotted(node) != ("os.scandir")
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


def test_b9_no_process_or_other_file_changing_calls():
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


# ---------------------------------------------------------------------------- trees


def deck_manifest(appid: int, installdir: str) -> str:
    return (
        f'"AppState"\n{{\n\t"appid"\t\t"{appid}"\n\t"name"\t\t"Game {appid}"\n'
        f'\t"StateFlags"\t\t"4"\n\t"installdir"\t\t{q(installdir)}\n\t"buildid"\t\t"7"\n}}\n'
    )


def add_deck_game(library: Path, appid: int) -> None:
    put(library / "steamapps" / f"appmanifest_{appid}.acf", deck_manifest(appid, f"Game{appid}"))
    put(library / "steamapps" / "common" / f"Game{appid}" / "GameUserSettings.ini", "[x]\n")
    put(library / "steamapps" / "common" / f"Game{appid}" / "config.ini", "[Render]\n")
    put(library / "steamapps" / "common" / f"Game{appid}" / "Game_Data" / "boot.config", "")
    put(library / "steamapps" / "compatdata" / str(appid) / "pfx" / "user.reg", "WINE\n")
    put(library / "steamapps" / "compatdata" / str(appid) / "config_info", "9.0\n")
    put(library / "steamapps" / "shadercache" / str(appid) / "fozpipelinesv6" / "a.foz", b"\0")


def deck_libraryfolders(paths: list[str], legacy: bool = False) -> str:
    if legacy:
        body = "".join(f"\t{q(str(n))}\t\t{q(path)}\n" for n, path in enumerate(paths, 1))
        return '"LibraryFolders"\n{\n\t"TimeNextStatsReport"\t\t"1700000000"\n' + body + "}\n"
    body = "".join(
        f'\t"{n}"\n\t{{\n\t\t"path"\t\t{q(path)}\n\t\t"label"\t\t""\n\t}}\n'
        for n, path in enumerate(paths)
    )
    return '"libraryfolders"\n{\n' + body + "}\n"


def deck_tree(base: Path, *, legacy: bool = False, config: bool = True) -> tuple[Path, list]:
    """A Deck-like install: internal drive, SD card, decoy files Steam keeps next to the
    three readable kinds, broken manifests and links. Returns (root to scan, libraries
    that must be listed)."""
    root = base / "steam"
    sd = base / "mmcblk0p1"
    steamapps = root / "steamapps"
    paths = [str(root), str(sd), str(base / "gone"), "relative/lib", str(base / "file_lib")]
    put(
        steamapps / "libraryfolders.vdf",
        deck_libraryfolders(paths[1:] if legacy else paths, legacy),
    )
    put(steamapps / "libraryfolders.vdf.bak", "decoy")
    put(base / "file_lib" / "steamapps", "not a folder")
    for library, appid in [(root, 10), (root, 2246340), (sd, 20), (sd, 2183900)]:
        add_deck_game(library, appid)
    put(steamapps / "appmanifest_70.acf.bak", deck_manifest(70, "Game70"))
    put(steamapps / "AppManifest_71.acf", deck_manifest(71, "Game71"))
    put(steamapps / "appmanifest_72.acf.tmp", deck_manifest(72, "Game72"))
    put(steamapps / "workshop" / "appworkshop_10.acf", '"AppWorkshop"\n{\n}\n')
    put(steamapps / "downloading" / "appmanifest_73.acf", deck_manifest(73, "Game73"))
    put(sd / "steamapps" / "appmanifest_21.acf", '"AppState"\n{\n')
    (sd / "steamapps" / "appmanifest_22.acf").mkdir()
    (sd / "steamapps" / "appmanifest_23.acf").symlink_to(base / "no_such_file.acf")
    (sd / "steamapps" / "appmanifest_24.acf").symlink_to(sd / "steamapps" / "common")
    if config:
        put(root / "config" / "config.vdf", CONFIG_VDF)
    put(root / "config" / "loginusers.vdf", '"users"\n{\n}\n')
    put(root / "config" / "libraryfolders.vdf", deck_libraryfolders([str(base / "elsewhere")]))
    put(
        root / "userdata" / "12345" / "config" / "localconfig.vdf", '"UserLocalConfigStore"\n{\n}\n'
    )
    put(base / "relative" / "lib" / "steamapps" / "appmanifest_30.acf", deck_manifest(30, "Game30"))
    return root, [root, sd]


def symlinked_tree(base: Path) -> tuple[Path, list]:
    root, listed = deck_tree(base / "real")
    link = base / "steam_link"
    link.symlink_to(root, target_is_directory=True)
    return link, listed


TREES = {
    "deck-like": deck_tree,
    "legacy-layout": lambda base: deck_tree(base, legacy=True),
    "no-config-vdf": lambda base: deck_tree(base, config=False),
    "symlinked-root": symlinked_tree,
}


# ---------------------------------------------------------------------------- recorders


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


def record_opens(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, object, object]]:
    """Record every open through builtins.open, io.open, os.open and pathlib.Path.open."""
    seen: list[tuple[str, object, object]] = []
    real_open, real_os_open, real_path_open = builtins.open, os.open, pathlib.Path.open

    def fake_open(file, mode="r", *args, **kwargs):
        seen.append(("open", file, mode))
        return real_open(file, mode, *args, **kwargs)

    def fake_os_open(path, flags, *args, **kwargs):
        seen.append(("os.open", path, flags))
        return real_os_open(path, flags, *args, **kwargs)

    def fake_path_open(self, mode="r", *args, **kwargs):
        seen.append(("Path.open", self, mode))
        return real_path_open(self, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", fake_open)
    monkeypatch.setattr(io, "open", fake_open)
    monkeypatch.setattr(os, "open", fake_os_open)
    monkeypatch.setattr(pathlib.Path, "open", fake_path_open)
    return seen


def record_listings(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    seen: list[str] = []
    real_scandir = os.scandir

    def fake_scandir(path="."):
        if isinstance(path, str | bytes | os.PathLike):
            seen.append(os.path.realpath(os.fsdecode(path)))
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", fake_scandir)
    return seen


def run(entry_point: str, root: Path, capsys: pytest.CaptureFixture) -> None:
    if entry_point == "main":
        assert discover.main(["--steam-root", str(root)]) == 0
        assert capsys.readouterr().out.startswith("{")
    else:
        getattr(discover, entry_point)(str(root))


def kind_of_opened(file: object, root: Path, libraries: list[Path]) -> str | None:
    """Which of the three allowed kinds an opened path is, or None."""
    if not isinstance(file, str | bytes | os.PathLike):
        return None
    path = Path(os.fsdecode(file))
    folder = os.path.realpath(path.parent)
    if path.name == "libraryfolders.vdf" and folder == os.path.realpath(root / "steamapps"):
        return "libraryfolders"
    if path.name == "config.vdf" and folder == os.path.realpath(root / "config"):
        return "config"
    listed = {os.path.realpath(library / "steamapps") for library in libraries}
    if MANIFEST_NAME.fullmatch(path.name) and folder in listed:
        return "manifest"
    return None


# ---------------------------------------------------------------------------- runtime


@pytest.mark.parametrize("entry_point", ["scan", "find_libraries", "main"])
def test_b9_only_the_three_kinds_of_file_are_opened_read_only(
    tmp_path, monkeypatch, capsys, entry_point
):
    root, libraries = deck_tree(tmp_path)
    with monkeypatch.context() as patch:
        seen = record_opens(patch)
        run(entry_point, root, capsys)
    kinds = set()
    for route, file, mode in seen:
        kind = kind_of_opened(file, root, libraries)
        assert kind is not None, f"{route} opened {file!r}"
        assert Path(os.fsdecode(file)).is_file(), f"{route} opened a non-regular {file!r}"
        if route == "os.open":
            assert isinstance(mode, int)
            assert mode & WRITE_FLAGS == 0, f"os.open flags {mode:#o} for {file!r}"
        else:
            assert mode in ("r", "rb"), f"{route} mode {mode!r} for {file!r}"
        kinds.add(kind)
    # The recorder must have seen the reads the entry point cannot do without.
    if entry_point == "find_libraries":
        assert "libraryfolders" in kinds
    else:
        assert kinds == {"libraryfolders", "config", "manifest"}


def test_b9_each_available_library_is_listed_with_os_scandir(tmp_path, monkeypatch, capsys):
    root, libraries = deck_tree(tmp_path)
    with monkeypatch.context() as patch:
        seen = record_listings(patch)
        discover.scan(str(root))
    wanted = {os.path.realpath(library / "steamapps") for library in libraries}
    assert wanted <= set(seen)


@pytest.mark.parametrize("shape", sorted(TREES))
def test_b9_runs_change_nothing_on_disk(tmp_path, monkeypatch, capsys, shape):
    data = tmp_path / "data"
    data.mkdir()
    root, _ = TREES[shape](data)
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    before = snapshot(tmp_path)
    for _ in range(2):
        discover.scan(str(root))
        discover.find_libraries(str(root))
        run("main", root, capsys)
    assert snapshot(tmp_path) == before
