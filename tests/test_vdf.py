# Contracts for deckforge.vdf: PR A of docs/specs/discover.md, criteria V1 to V6.
# Written test-first; src/deckforge/vdf.py does not exist when this file is added.
#
# parse(text) -> dict
#   Pre:  `text` is a str. Decoding bytes and stripping a BOM are the caller's job (B1).
#   Post: returns a dict with str keys and str-or-dict values, nested up to 100 blocks.
#         Key case is preserved. Several top-level pairs are allowed; `{}` is an empty dict.
#   Post: tokens are quoted strings, unquoted runs (anything except whitespace, `"`, `{`
#         and `}`) and the two braces. Whitespace is exactly space, tab, CR and LF. `//`
#         starts a comment to the end of the line only where a new token could start (V1).
#   Post: inside quotes exactly four escapes are decoded (`\\`, `\"`, `\n`, `\t`). Any
#         other backslash is kept together with the next character. Unquoted tokens are
#         taken as written (V2).
#   Post: a key repeated at one level keeps only its last value; blocks are never merged.
#         Keys that differ only in case are different keys (V3).
#   Post: every case in the V4 table raises VdfError and nothing is returned. `err.line`
#         is the 1-based line the table names, and `str(err)` contains `line <n>` for that
#         same n. Lines are counted on LF only: CRLF is one break, and a lone CR or any
#         other Unicode line separator is not a break.
#   Inv:  never raises RecursionError, whatever the nesting depth (V4).
#   Inv:  no I/O; vdf.py imports only `__future__`, `re` and `typing` (V6).
#
# find(mapping, *keys) -> str | dict | None
#   Pre:  `mapping` is a dict from parse, or a block inside one. Its iteration order
#         stands for the file order. Every key is a str.
#   Post: with no keys, returns `mapping` itself (the same object).
#   Post: at each level, every key equal to the wanted key under `casefold()` is a
#         candidate. Candidates are tried from the last in the file to the first, and the
#         first one whose value resolves the whole remaining path is returned. A candidate
#         whose value is a str while keys remain does not resolve; the search moves on.
#   Post: returns None when no candidate path resolves. An empty-string value is a
#         resolved value and comes back as "", never as None.
#   Inv:  never modifies `mapping`.
#
# class VdfError(ValueError)
#   Inv:  carries an int attribute `line`, 1-based.
#
# Notes
# - PR A has no write or restore path, so there is no apply-then-restore round trip. The
#   nearest property is escape-then-parse: any str without NUL or CR, escaped with the
#   four V2 escapes and parsed back, comes out unchanged (test_v2_escaped_strings_round_trip).
# - The unusual inputs the spec names (CRLF, comments, unquoted tokens, the legacy
#   libraryfolders layout, `#include` and `#base`, `[$WIN32]`, NUL, deep nesting) are each
#   covered below, either as accepted input or as a refusal checked by VdfError and line.
# - Every fixture is an in-memory string shaped like a real Steam file. Nothing touches disk.

import ast
import builtins
import copy
import io
import os
import re
from pathlib import Path

import pytest

from deckforge import vdf

ROOT = Path(__file__).resolve().parents[1]
VDF_SOURCE = ROOT / "src" / "deckforge" / "vdf.py"


# ---------------------------------------------------------------------------- helpers


def assert_vdf_error(text: str, line: int) -> None:
    """parse(text) must raise VdfError whose `.line` and message both name `line`."""
    with pytest.raises(vdf.VdfError) as caught:
        vdf.parse(text)
    err = caught.value
    assert isinstance(err.line, int)
    assert not isinstance(err.line, bool)
    assert err.line == line, f"expected line {line}, got line {err.line}: {err}"
    assert re.search(rf"\bline {line}(?!\d)", str(err)), f"message lacks 'line {line}': {err}"


def iter_blocks(tree: dict):
    """Yield every dict in a parsed tree, without recursion."""
    stack = [tree]
    while stack:
        block = stack.pop()
        yield block
        stack.extend(value for value in block.values() if isinstance(value, dict))


def assert_str_tree(tree: object) -> None:
    assert isinstance(tree, dict)
    for block in iter_blocks(tree):
        for key, value in block.items():
            assert isinstance(key, str)
            assert isinstance(value, str | dict)


def nested(depth: int) -> str:
    """`depth` nested blocks; each key and `{` on its own line, so the n-th `{` is line 2n."""
    opening = "".join(f'"k{i}"\n{{\n' for i in range(depth))
    return opening + '"leaf" "x"\n' + "}\n" * depth


def nested_one_line(depth: int) -> str:
    return '"k" {' * depth + ' "leaf" "x" ' + "}" * depth


def escape(text: str) -> str:
    """Encode a str with the four V2 escapes."""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\t", "\\t")


def dump(tree: dict, depth: int = 0) -> str:
    """Write a tree as Steam-style text: tabs, one token pair per line."""
    pad = "\t" * depth
    out = []
    for key, value in tree.items():
        if isinstance(value, dict):
            out.append(f'{pad}"{escape(key)}"\n{pad}{{\n{dump(value, depth + 1)}{pad}}}\n')
        else:
            out.append(f'{pad}"{escape(key)}"\t\t"{escape(value)}"\n')
    return "".join(out)


# --------------------------------------------------------------- realistic Steam files

# steamapps/libraryfolders.vdf, current layout: numbered blocks with a "path" key.
LIBRARYFOLDERS_CURRENT = """\
"libraryfolders"
{
\t"0"
\t{
\t\t"path"\t\t"/home/deck/.local/share/Steam"
\t\t"label"\t\t""
\t\t"contentid"\t\t"4617403254307811000"
\t\t"totalsize"\t\t"0"
\t\t"update_clean_bytes_tally"\t\t"52818921554"
\t\t"time_last_update_verified"\t\t"1760000000"
\t\t"apps"
\t\t{
\t\t\t"228980"\t\t"441146312"
\t\t\t"1493710"\t\t"1350829036"
\t\t\t"2246340"\t\t"81234567890"
\t\t}
\t}
\t"1"
\t{
\t\t"path"\t\t"/run/media/mmcblk0p1"
\t\t"label"\t\t"SD card"
\t\t"contentid"\t\t"5823126934617712000"
\t\t"totalsize"\t\t"510770802688"
\t\t"update_clean_bytes_tally"\t\t"0"
\t\t"time_last_update_verified"\t\t"1760000000"
\t\t"apps"
\t\t{
\t\t\t"2183900"\t\t"74123456789"
\t\t\t"553850"\t\t"65432109876"
\t\t}
\t}
}
"""

LIBRARYFOLDERS_CURRENT_PARSED = {
    "libraryfolders": {
        "0": {
            "path": "/home/deck/.local/share/Steam",
            "label": "",
            "contentid": "4617403254307811000",
            "totalsize": "0",
            "update_clean_bytes_tally": "52818921554",
            "time_last_update_verified": "1760000000",
            "apps": {"228980": "441146312", "1493710": "1350829036", "2246340": "81234567890"},
        },
        "1": {
            "path": "/run/media/mmcblk0p1",
            "label": "SD card",
            "contentid": "5823126934617712000",
            "totalsize": "510770802688",
            "update_clean_bytes_tally": "0",
            "time_last_update_verified": "1760000000",
            "apps": {"2183900": "74123456789", "553850": "65432109876"},
        },
    }
}

# Legacy layout: "LibraryFolders", numbered keys whose value is the path itself. The
# Windows path is written with escaped backslashes, as Steam writes it.
LIBRARYFOLDERS_LEGACY = """\
"LibraryFolders"
{
\t"TimeNextStatsReport"\t\t"1630000000"
\t"ContentStatsID"\t\t"-4617403254307811000"
\t"1"\t\t"/run/media/mmcblk0p1"
\t"2"\t\t"D:\\\\SteamLibrary"
}
"""

LIBRARYFOLDERS_LEGACY_PARSED = {
    "LibraryFolders": {
        "TimeNextStatsReport": "1630000000",
        "ContentStatsID": "-4617403254307811000",
        "1": "/run/media/mmcblk0p1",
        "2": "D:\\SteamLibrary",
    }
}

# steamapps/appmanifest_2246340.acf
APPMANIFEST_ACF = """\
"AppState"
{
\t"appid"\t\t"2246340"
\t"universe"\t\t"1"
\t"LauncherPath"\t\t"/home/deck/.local/share/Steam/ubuntu12_32/steam"
\t"name"\t\t"Monster Hunter Wilds"
\t"StateFlags"\t\t"4"
\t"installdir"\t\t"MonsterHunterWilds"
\t"LastUpdated"\t\t"1759900000"
\t"LastPlayed"\t\t"1760000000"
\t"SizeOnDisk"\t\t"81234567890"
\t"StagingSize"\t\t"0"
\t"buildid"\t\t"20000000"
\t"LastOwner"\t\t"0"
\t"UpdateResult"\t\t"0"
\t"BytesToDownload"\t\t"0"
\t"BytesDownloaded"\t\t"0"
\t"BytesToStage"\t\t"0"
\t"BytesStaged"\t\t"0"
\t"TargetBuildID"\t\t"0"
\t"AutoUpdateBehavior"\t\t"0"
\t"AllowOtherDownloadsWhileRunning"\t\t"0"
\t"ScheduledAutoUpdate"\t\t"0"
\t"InstalledDepots"
\t{
\t\t"2246341"
\t\t{
\t\t\t"manifest"\t\t"6290000000000000000"
\t\t\t"size"\t\t"81234567890"
\t\t}
\t}
\t"SharedDepots"
\t{
\t\t"228988"\t\t"228980"
\t}
\t"UserConfig"
\t{
\t\t"language"\t\t"english"
\t}
\t"MountedConfig"
\t{
\t\t"language"\t\t"english"
\t}
}
"""

APPMANIFEST_PARSED = {
    "AppState": {
        "appid": "2246340",
        "universe": "1",
        "LauncherPath": "/home/deck/.local/share/Steam/ubuntu12_32/steam",
        "name": "Monster Hunter Wilds",
        "StateFlags": "4",
        "installdir": "MonsterHunterWilds",
        "LastUpdated": "1759900000",
        "LastPlayed": "1760000000",
        "SizeOnDisk": "81234567890",
        "StagingSize": "0",
        "buildid": "20000000",
        "LastOwner": "0",
        "UpdateResult": "0",
        "BytesToDownload": "0",
        "BytesDownloaded": "0",
        "BytesToStage": "0",
        "BytesStaged": "0",
        "TargetBuildID": "0",
        "AutoUpdateBehavior": "0",
        "AllowOtherDownloadsWhileRunning": "0",
        "ScheduledAutoUpdate": "0",
        "InstalledDepots": {"2246341": {"manifest": "6290000000000000000", "size": "81234567890"}},
        "SharedDepots": {"228988": "228980"},
        "UserConfig": {"language": "english"},
        "MountedConfig": {"language": "english"},
    }
}

# config/config.vdf, reduced to the CompatToolMapping block. Appid 0 is Steam's global
# default; an empty "name" means no tool chosen for that game.
CONFIG_VDF = """\
"InstallConfigStore"
{
\t"Software"
\t{
\t\t"Valve"
\t\t{
\t\t\t"Steam"
\t\t\t{
\t\t\t\t"AutoUpdateWindowEnabled"\t\t"0"
\t\t\t\t"CompatToolMapping"
\t\t\t\t{
\t\t\t\t\t"0"
\t\t\t\t\t{
\t\t\t\t\t\t"name"\t\t"proton_experimental"
\t\t\t\t\t\t"config"\t\t""
\t\t\t\t\t\t"priority"\t\t"75"
\t\t\t\t\t}
\t\t\t\t\t"2246340"
\t\t\t\t\t{
\t\t\t\t\t\t"name"\t\t"proton_9"
\t\t\t\t\t\t"config"\t\t""
\t\t\t\t\t\t"priority"\t\t"250"
\t\t\t\t\t}
\t\t\t\t\t"553850"
\t\t\t\t\t{
\t\t\t\t\t\t"name"\t\t""
\t\t\t\t\t\t"config"\t\t""
\t\t\t\t\t\t"priority"\t\t"250"
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t}
\t}
}
"""

CONFIG_VDF_PARSED = {
    "InstallConfigStore": {
        "Software": {
            "Valve": {
                "Steam": {
                    "AutoUpdateWindowEnabled": "0",
                    "CompatToolMapping": {
                        "0": {"name": "proton_experimental", "config": "", "priority": "75"},
                        "2246340": {"name": "proton_9", "config": "", "priority": "250"},
                        "553850": {"name": "", "config": "", "priority": "250"},
                    },
                }
            }
        }
    }
}

# config.vdf where a later lower-case "valve" block sits next to the real "Valve" one.
CONFIG_VDF_CASE_VARIANTS = """\
"InstallConfigStore"
{
\t"Software"
\t{
\t\t"Valve"
\t\t{
\t\t\t"Steam"
\t\t\t{
\t\t\t\t"CompatToolMapping"
\t\t\t\t{
\t\t\t\t\t"2183900"
\t\t\t\t\t{
\t\t\t\t\t\t"name"\t\t"GE-Proton9-20"
\t\t\t\t\t\t"config"\t\t""
\t\t\t\t\t\t"priority"\t\t"250"
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}
\t\t}
\t\t"valve"
\t\t{
\t\t\t"steam"
\t\t\t{
\t\t\t\t"SurveyDateVersion"\t\t"1"
\t\t\t}
\t\t}
\t}
}
"""

CONFIG_VDF_CASE_VARIANTS_PARSED = {
    "InstallConfigStore": {
        "Software": {
            "Valve": {
                "Steam": {
                    "CompatToolMapping": {
                        "2183900": {"name": "GE-Proton9-20", "config": "", "priority": "250"}
                    }
                }
            },
            "valve": {"steam": {"SurveyDateVersion": "1"}},
        }
    }
}

COMPAT = ("InstallConfigStore", "Software", "Valve", "Steam", "CompatToolMapping")

REALISTIC = [
    pytest.param(LIBRARYFOLDERS_CURRENT, LIBRARYFOLDERS_CURRENT_PARSED, id="libraryfolders"),
    pytest.param(LIBRARYFOLDERS_LEGACY, LIBRARYFOLDERS_LEGACY_PARSED, id="libraryfolders-legacy"),
    pytest.param(APPMANIFEST_ACF, APPMANIFEST_PARSED, id="appmanifest"),
    pytest.param(CONFIG_VDF, CONFIG_VDF_PARSED, id="config-vdf"),
    pytest.param(CONFIG_VDF_CASE_VARIANTS, CONFIG_VDF_CASE_VARIANTS_PARSED, id="config-case"),
]


# ------------------------------------------------------------------------ V1 grammar


@pytest.mark.parametrize(("text", "expected"), REALISTIC)
def test_v1_parses_realistic_steam_files(text, expected):
    result = vdf.parse(text)
    assert result == expected
    assert_str_tree(result)


@pytest.mark.parametrize(("text", "expected"), REALISTIC)
def test_v1_crlf_files_parse_the_same_as_lf(text, expected):
    assert "\r" not in text
    result = vdf.parse(text.replace("\n", "\r\n"))
    assert result == expected
    assert_str_tree(result)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param('"a" "b"', {"a": "b"}, id="one-pair"),
        pytest.param(
            '"a" "1"\n"b" "2"\n"c" { }', {"a": "1", "b": "2", "c": {}}, id="several-top-level"
        ),
        pytest.param('"a" {}', {"a": {}}, id="empty-block"),
        pytest.param('"a" {\n\t// nothing here\n}', {"a": {}}, id="block-with-only-a-comment"),
        pytest.param(
            '"a" { "b" { "c" "d" } "e" "f" }', {"a": {"b": {"c": "d"}, "e": "f"}}, id="nested"
        ),
        pytest.param('"" ""', {"": ""}, id="empty-strings"),
        pytest.param(
            '"k" "{ } // [$X] #include"', {"k": "{ } // [$X] #include"}, id="specials-in-quotes"
        ),
    ],
)
def test_v1_document_is_pairs_of_key_and_value_or_block(text, expected):
    result = vdf.parse(text)
    assert result == expected
    assert_str_tree(result)


def test_v1_key_case_is_preserved():
    result = vdf.parse('"AppState" { "StateFlags" "4" "InstallDir" "Wilds" }')
    assert result == {"AppState": {"StateFlags": "4", "InstallDir": "Wilds"}}
    assert list(result) == ["AppState"]
    assert sorted(result["AppState"]) == ["InstallDir", "StateFlags"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param("key value", {"key": "value"}, id="bare-key-and-value"),
        pytest.param(
            'AppState { appid 2246340 name "Monster Hunter Wilds" }',
            {"AppState": {"appid": "2246340", "name": "Monster Hunter Wilds"}},
            id="mixed-bare-and-quoted",
        ),
        pytest.param('"k" -1.5e3', {"k": "-1.5e3"}, id="number-like"),
        pytest.param('"k" a#b$c%d', {"k": "a#b$c%d"}, id="punctuation"),
        pytest.param('"k" /x', {"k": "/x"}, id="single-slash"),
        pytest.param('"name" Café', {"name": "Café"}, id="non-ascii"),
        pytest.param("key{a b}", {"key": {"a": "b"}}, id="ends-at-brace"),
        pytest.param('k"v"', {"k": "v"}, id="ends-at-quote"),
        pytest.param('"k"v', {"k": "v"}, id="starts-after-quote"),
        pytest.param('"a"{"b""c"}', {"a": {"b": "c"}}, id="no-whitespace-between-tokens"),
        pytest.param('"a""b""c""d"', {"a": "b", "c": "d"}, id="adjacent-quoted-strings"),
    ],
)
def test_v1_unquoted_tokens_run_until_whitespace_quote_or_brace(text, expected):
    assert vdf.parse(text) == expected


def test_v1_space_tab_cr_and_lf_separate_tokens():
    text = '"a"\t"b"\r\n"c" \r\n\t "d"\n\r"e"\r"f"'
    assert vdf.parse(text) == {"a": "b", "c": "d", "e": "f"}


@pytest.mark.parametrize(
    "char",
    ["\x0b", "\x0c", "\x1c", "\x85", "\xa0", "\u2028", "\u3000"],
    ids=["VT", "FF", "FS", "NEL", "NBSP", "LSEP", "IDEOGRAPHIC-SPACE"],
)
def test_v1_other_whitespace_characters_are_token_text(char):
    assert vdf.parse(f'"k" a{char}b') == {"k": f"a{char}b"}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param('// header\n"a" "b"', {"a": "b"}, id="leading-line"),
        pytest.param('"a" "b" // trailing', {"a": "b"}, id="trailing-without-newline"),
        pytest.param('"a" // between key and value\n"b"', {"a": "b"}, id="between-key-and-value"),
        pytest.param('"a" // before brace\n{ "b" "c" }', {"a": {"b": "c"}}, id="before-brace"),
        pytest.param('"a" {// after\n"b" "c"}// after', {"a": {"b": "c"}}, id="glued-to-braces"),
        pytest.param('"a" "b"// glued\n"c" "d"', {"a": "b", "c": "d"}, id="glued-to-quote"),
        pytest.param('"a" "b" // "x" { } [$WIN32] #include\n', {"a": "b"}, id="hides-tokens"),
        pytest.param('"a" "b" /// three slashes', {"a": "b"}, id="three-slashes"),
        pytest.param('"a" "b" // crlf\r\n"c" "d"\r\n', {"a": "b", "c": "d"}, id="crlf"),
    ],
)
def test_v1_comments_are_skipped_where_a_token_could_start(text, expected):
    assert vdf.parse(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param('"url" http://example.com/a', {"url": "http://example.com/a"}, id="url"),
        pytest.param('"k" a//b', {"k": "a//b"}, id="bare-token"),
        pytest.param(
            '"k" value//not-a-comment\n"n" "m"',
            {"k": "value//not-a-comment", "n": "m"},
            id="glued-to-bare-token",
        ),
        pytest.param('"k" "a // b"', {"k": "a // b"}, id="inside-quoted-value"),
        pytest.param('"k//x" "v"', {"k//x": "v"}, id="inside-quoted-key"),
    ],
)
def test_v1_double_slash_inside_a_token_is_not_a_comment(text, expected):
    assert vdf.parse(text) == expected


# ------------------------------------------------------------------------ V2 strings


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(r"a\\b", "a\\b", id="backslash"),
        pytest.param(r"a\"b", 'a"b', id="quote"),
        pytest.param(r"a\nb", "a\nb", id="newline"),
        pytest.param(r"a\tb", "a\tb", id="tab"),
        pytest.param(r"\"quoted\"", '"quoted"', id="quotes-at-both-ends"),
        pytest.param(r"\\", "\\", id="lone-escaped-backslash"),
        pytest.param(r"\\\"", '\\"', id="escaped-backslash-then-escaped-quote"),
        pytest.param(r"\\n", "\\n", id="escaped-backslash-then-n"),
        pytest.param(r"\\\\", "\\\\", id="two-escaped-backslashes"),
        pytest.param(r"\q\\\n", "\\q\\\n", id="kept-then-decoded"),
        pytest.param(r"C:\\Program Files (x86)\\Steam", "C:\\Program Files (x86)\\Steam", id="win"),
        pytest.param(r"C:\new\table", "C:\new\table", id="path-holding-n-and-t-escapes"),
    ],
)
def test_v2_decodes_the_four_escapes_inside_quotes(source, expected):
    assert vdf.parse(f'"k" "{source}"') == {"k": expected}


@pytest.mark.parametrize(
    "source",
    [
        r"a\qb",
        r"a\rb",
        r"C:\Games\Wilds",
        r"\u00e9",
        r"\x41",
        r"a\'b",
        r"a\/b",
        r"\0",
        r"a\{b}",
        r"end\ ",
    ],
)
def test_v2_other_backslash_is_kept_with_the_next_character(source):
    assert vdf.parse(f'"k" "{source}"') == {"k": source}


@pytest.mark.parametrize("source", [r"a\nb", r"C:\new\table", r"a\\b", r"a\qb", r"a\tb"])
def test_v2_unquoted_tokens_are_not_unescaped(source):
    assert vdf.parse(f'"k" {source}') == {"k": source}


def test_v2_escapes_are_decoded_in_keys_too():
    text = r'"a\"b" "1"' + "\n" + r'"tab\there" "2"' + "\n" + r'"keep\q" "3"'
    assert vdf.parse(text) == {'a"b': "1", "tab\there": "2", "keep\\q": "3"}


def test_v2_escaped_quote_does_not_end_the_string():
    assert vdf.parse(r'"k" "say \"hi\" { } // now"') == {"k": 'say "hi" { } // now'}


def test_v2_escaped_backslash_before_the_closing_quote_ends_the_string():
    text = r'"path" "D:\\Games\\"' + "\n" + '"next" "v"'
    assert vdf.parse(text) == {"path": "D:\\Games\\", "next": "v"}


def test_v2_non_ascii_text_is_kept():
    assert vdf.parse('"name" "Café ポケモン Ω"') == {"name": "Café ポケモン Ω"}


@pytest.mark.parametrize(
    ("text", "line"),
    [
        pytest.param('"a" "multi\nline"', 1, id="value-then-closed"),
        pytest.param('"a" "b"\n"c" "d\ne"\n', 2, id="value"),
        pytest.param('"a" "b"\n"c\nd" "e"', 2, id="key"),
        pytest.param('"a" "b"\n"c" "d\r\ne"', 2, id="crlf"),
        pytest.param('"a" "b"\n"c" "d\n\n\n', 2, id="never-closed"),
    ],
)
def test_v2_raw_newline_inside_quotes_is_an_error_at_the_opening_quote(text, line):
    assert_vdf_error(text, line)


TRICKY_STRINGS = [
    "",
    "plain",
    "with space",
    'quote"inside',
    'ends with quote"',
    "back\\slash",
    "trailing\\",
    "\\\\double",
    "tab\there",
    "new\nline",
    "\n",
    "braces { } inside",
    "// not a comment",
    "#include",
    "#base",
    "[$WIN32]",
    "\\q other backslash",
    "\\n backslash then n",
    '\\"',
    "C:\\Program Files (x86)\\Steam",
    "unicode ß ポケモン",
    "\x0b\x0c\x85\u2028",
    "  leading and trailing  ",
]

ROUND_TRIP_TREES = [
    pytest.param({"value": s, s: {"inner": s, "deeper": {s: s}}}, id=f"s{i}")
    for i, s in enumerate(TRICKY_STRINGS)
] + [
    pytest.param(
        {f"k{i}": s for i, s in enumerate(TRICKY_STRINGS)}
        | {"block": {s: str(i) for i, s in enumerate(TRICKY_STRINGS)}},
        id="all",
    )
]


@pytest.mark.parametrize("newline", ["\n", "\r\n"], ids=["lf", "crlf"])
@pytest.mark.parametrize("tree", ROUND_TRIP_TREES)
def test_v2_escaped_strings_round_trip(tree, newline):
    text = dump(tree).replace("\n", newline)
    assert vdf.parse(text) == tree


# ---------------------------------------------------------------------- V3 duplicates


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param('"a" "1"\n"a" "2"', {"a": "2"}, id="string-then-string"),
        pytest.param('"a" "1"\n"a" "2"\n"a" "3"', {"a": "3"}, id="three-times"),
        pytest.param(
            '"a" { "x" "1" "y" "2" }\n"a" { "z" "3" }',
            {"a": {"z": "3"}},
            id="block-then-block-not-merged",
        ),
        pytest.param('"a" { "x" "1" }\n"a" {}', {"a": {}}, id="block-then-empty-block"),
        pytest.param('"a" { "x" "1" }\n"a" "flat"', {"a": "flat"}, id="block-then-string"),
        pytest.param('"a" "flat"\n"a" { "x" "1" }', {"a": {"x": "1"}}, id="string-then-block"),
        pytest.param(
            '"root" { "k" "1" "sub" { "q" "1" } "k" "2" "sub" { "r" "2" } }',
            {"root": {"k": "2", "sub": {"r": "2"}}},
            id="inside-a-block",
        ),
        pytest.param('"a" { "a" "inner" }', {"a": {"a": "inner"}}, id="same-key-other-level"),
    ],
)
def test_v3_last_value_wins_and_blocks_are_never_merged(text, expected):
    assert vdf.parse(text) == expected


def test_v3_later_library_block_replaces_the_earlier_one_entirely():
    text = LIBRARYFOLDERS_CURRENT.replace('\t"1"\n', '\t"0"\n')
    assert vdf.parse(text) == {
        "libraryfolders": {"0": LIBRARYFOLDERS_CURRENT_PARSED["libraryfolders"]["1"]}
    }


def test_v3_keys_that_differ_only_in_case_are_not_duplicates():
    assert vdf.parse('"name" "x"\n"Name" "y"\n"NAME" "z"') == {
        "name": "x",
        "Name": "y",
        "NAME": "z",
    }
    assert vdf.parse('"name" "1"\n"Name" "2"\n"name" "3"') == {"name": "3", "Name": "2"}


# -------------------------------------------------------------------------- V4 errors


def test_v4_vdf_error_is_a_value_error():
    assert issubclass(vdf.VdfError, ValueError)
    with pytest.raises(ValueError):
        vdf.parse("")


@pytest.mark.parametrize(
    "text",
    ["", " ", "\n", "\r\n\r\n", "\t \n  \n", "// only", "// one\n// two\n", "\n\n\n// late\n\n"],
    ids=["empty", "space", "lf", "crlf", "mixed", "comment", "comments", "late-comment"],
)
def test_v4_empty_or_comment_only_input_reports_line_1(text):
    assert_vdf_error(text, 1)


@pytest.mark.parametrize(
    ("text", "line"),
    [
        pytest.param('"a', 1, id="key-at-start"),
        pytest.param('"a" "b', 1, id="value"),
        pytest.param('"a" "b"\n\n"c" "d', 3, id="value-on-line-3"),
        pytest.param('"a" "b"\n"c', 2, id="key-on-line-2"),
        pytest.param(r'"a" "ends with escaped quote\"', 1, id="escaped-quote-at-end"),
        pytest.param('"a" "b"\n"c" "d\\', 2, id="backslash-at-end"),
    ],
)
def test_v4_unterminated_string_reports_opening_line(text, line):
    assert_vdf_error(text, line)


@pytest.mark.parametrize(
    ("text", "line"),
    [
        pytest.param("}", 1, id="alone"),
        pytest.param('"a" "b"\n}', 2, id="after-pair"),
        pytest.param('"a" { "b" "c" }\n\n}', 3, id="after-closed-block"),
        pytest.param('"a"\n{\n}\n}\n"b" "c"', 4, id="extra-close"),
    ],
)
def test_v4_stray_close_brace_reports_its_line(text, line):
    assert_vdf_error(text, line)


@pytest.mark.parametrize(
    ("text", "line"),
    [
        pytest.param("{ }", 1, id="at-start"),
        pytest.param('"a" "b"\n{ "c" "d" }', 2, id="after-pair"),
        pytest.param('"a"\n{\n\t{\n\t}\n}', 3, id="inside-block"),
        pytest.param('"a" { } { }', 1, id="second-block-without-key"),
        pytest.param('"a" "b"\n\n{', 3, id="at-end"),
    ],
)
def test_v4_open_brace_where_a_key_is_expected_reports_its_line(text, line):
    assert_vdf_error(text, line)


@pytest.mark.parametrize(
    ("text", "line"),
    [
        pytest.param('"a"', 1, id="only-a-key"),
        pytest.param('"a" "b"\n"c"', 2, id="after-pair"),
        pytest.param('"a" "b"\n\n"c"\n// trailing comment\n\n', 3, id="before-comment"),
        pytest.param('"a" { "b" "c" }\nlonely', 2, id="unquoted-key"),
        pytest.param('"a" "b"\r\n"c"\r\n', 2, id="crlf"),
    ],
)
def test_v4_key_without_value_at_end_reports_key_line(text, line):
    assert_vdf_error(text, line)


@pytest.mark.parametrize(
    ("text", "line"),
    [
        pytest.param('"a" }', 1, id="spec-example"),
        pytest.param('"x" "y"\n"a"\n}', 3, id="top-level"),
        pytest.param('"a"\n{\n\t"b"\n}', 4, id="inside-block"),
        pytest.param('"a" { "b" }', 1, id="one-line-block"),
    ],
)
def test_v4_close_brace_where_a_value_is_expected_reports_its_line(text, line):
    assert_vdf_error(text, line)


@pytest.mark.parametrize(
    ("text", "line"),
    [
        pytest.param('"a" {', 1, id="one-level"),
        pytest.param('"a"\n{\n\t"b" "c"\n', 2, id="brace-on-own-line"),
        pytest.param('"a" {\n\t"b" {\n\t\t"c" "d"\n', 2, id="innermost-of-two"),
        pytest.param('"a" {\n\t"b" { "x" "y" }\n\t"c" "d"\n', 1, id="inner-one-closed"),
        pytest.param('"a" {\n\t"b" "c" // }\n', 1, id="close-brace-in-comment"),
        pytest.param('"a" {\n\t"b" "c }"\n', 1, id="close-brace-in-string"),
        pytest.param(LIBRARYFOLDERS_CURRENT.removesuffix("}\n"), 2, id="libraryfolders-outer"),
        pytest.param(
            LIBRARYFOLDERS_CURRENT.removesuffix("\t}\n}\n"), 19, id="libraryfolders-inner"
        ),
    ],
)
def test_v4_unclosed_block_reports_innermost_open_brace(text, line):
    assert_vdf_error(text, line)


@pytest.mark.parametrize(
    ("text", "line"),
    [
        pytest.param('#include "base.vdf"\n"a" "b"', 1, id="include-first"),
        pytest.param('"a" "b"\n#base "defaults.vdf"', 2, id="base-after-pair"),
        pytest.param('"a"\n{\n\t#include "x.vdf"\n}', 3, id="include-in-block"),
        pytest.param('// note\n"a" "b"\n\n#base\t"x"', 4, id="base-after-comment"),
    ],
)
def test_v4_unquoted_include_or_base_key_is_refused(text, line):
    assert_vdf_error(text, line)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param('"#include" "x"', {"#include": "x"}, id="quoted-include-key"),
        pytest.param('"#base" { "a" "b" }', {"#base": {"a": "b"}}, id="quoted-base-key"),
        pytest.param('"cmd" #include', {"cmd": "#include"}, id="include-as-value"),
        pytest.param('"cmd" #base', {"cmd": "#base"}, id="base-as-value"),
    ],
)
def test_v4_include_and_base_are_plain_text_when_quoted_or_a_value(text, expected):
    assert vdf.parse(text) == expected


@pytest.mark.parametrize(
    ("text", "line"),
    [
        pytest.param('"a" "b" [$WIN32]', 1, id="after-pair"),
        pytest.param('"a" "b"\n"c" "d" [$X360]\n"e" "f"', 2, id="middle-line"),
        pytest.param('[$WIN32]\n"a" "b"', 1, id="key-position"),
        pytest.param('"a" "b"\n"c" [$LINUX]', 2, id="value-position"),
        pytest.param('"a"\n{\n\t"b" "c" [!$OSX]\n}', 3, id="inside-block"),
        pytest.param('"a" "b"\n[x "c"', 2, id="any-bracket-token"),
        pytest.param('"a" [', 1, id="lone-bracket"),
    ],
)
def test_v4_unquoted_token_starting_with_bracket_is_refused(text, line):
    assert_vdf_error(text, line)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        pytest.param('"a" "[$WIN32]"', {"a": "[$WIN32]"}, id="quoted-value"),
        pytest.param('"[$WIN32]" "b"', {"[$WIN32]": "b"}, id="quoted-key"),
        pytest.param('"a" x[1]', {"a": "x[1]"}, id="bracket-not-first"),
        pytest.param('"a" ]', {"a": "]"}, id="closing-bracket"),
    ],
)
def test_v4_brackets_are_plain_text_when_quoted_or_not_first(text, expected):
    assert vdf.parse(text) == expected


@pytest.mark.parametrize(
    ("text", "line"),
    [
        pytest.param("\x00", 1, id="alone"),
        pytest.param('"a" "b\x00c"', 1, id="in-quoted-value"),
        pytest.param('"a" "b"\n"c\x00" "d"', 2, id="in-quoted-key"),
        pytest.param('"a" "b"\n\n// note \x00\n"c" "d"', 3, id="in-comment"),
        pytest.param('"a" "b"\n\x00', 2, id="after-document"),
        pytest.param('"a" "b"\r\n"c" x\x00y', 2, id="in-unquoted-token-crlf"),
        pytest.param('"a" {\n\t\x00\n}', 2, id="between-tokens"),
    ],
)
def test_v4_nul_character_reports_its_line(text, line):
    assert_vdf_error(text, line)


def test_v4_nesting_of_100_blocks_is_accepted():
    result = vdf.parse(nested(100))
    assert vdf.find(result, *[f"k{i}" for i in range(100)], "leaf") == "x"
    one_line = vdf.parse(nested_one_line(100))
    assert vdf.find(one_line, *["k"] * 100, "leaf") == "x"
    assert_str_tree(result)


def test_v4_nesting_deeper_than_100_reports_the_101st_open_brace():
    assert_vdf_error(nested(101), 202)
    assert_vdf_error(nested_one_line(101), 1)


@pytest.mark.parametrize(
    ("text", "line"),
    [
        pytest.param(nested(10_000), 202, id="brace-per-line"),
        pytest.param(nested_one_line(10_000), 1, id="single-line"),
    ],
)
def test_v4_ten_thousand_levels_raise_vdf_error_not_recursion_error(text, line):
    assert_vdf_error(text, line)


def test_v4_depth_counts_open_blocks_not_total_braces():
    siblings = "\n".join(f'"s{i}" {{ "v" "{i}" }}' for i in range(150))
    parsed = vdf.parse(siblings)
    assert len(parsed) == 150
    assert parsed["s149"] == {"v": "149"}
    two_chains = vdf.parse(nested(100) + nested(100).replace('"k', '"j'))
    assert vdf.find(two_chains, *[f"k{i}" for i in range(100)], "leaf") == "x"
    assert vdf.find(two_chains, *[f"j{i}" for i in range(100)], "leaf") == "x"


@pytest.mark.parametrize(
    ("text", "line"),
    [
        pytest.param('"a" "b"\r\n"c" "d"\r\n}\r\n', 3, id="stray-brace"),
        pytest.param('"a"\r\n{\r\n"b" "c"\r\n', 2, id="unclosed-block"),
        pytest.param('"a" "b"\r\n\r\n"c" "d', 3, id="unterminated-string"),
        pytest.param('"a" "b"\r\n"c" "d\r\ne"', 2, id="raw-newline-in-quotes"),
        pytest.param('"a" "b"\r\n"c"\r\n', 2, id="key-without-value"),
    ],
)
def test_v4_crlf_counts_as_one_line(text, line):
    assert_vdf_error(text, line)


def test_v4_lone_cr_does_not_start_a_new_line():
    assert_vdf_error('"a" "b"\r"c" "d"\r\r}', 1)


@pytest.mark.parametrize(
    "separator",
    ["\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"],
    ids=["VT", "FF", "FS", "GS", "RS", "NEL", "LSEP", "PSEP"],
)
def test_v4_only_lf_starts_a_new_line(separator):
    text = f'"a" "x{separator}y{separator}z"\n}}'
    assert_vdf_error(text, 2)


# -------------------------------------------------------------------------- V5 lookup

BRANCHY = {
    "a": {"b": {"c": "1"}, "B": {"x": "2"}},
    "A": {"b": {"y": "3"}},
}


@pytest.mark.parametrize(
    ("mapping", "keys", "expected"),
    [
        pytest.param({"AppState": {"appid": "1"}}, ("appstate", "APPID"), "1", id="ascii"),
        pytest.param({"appstate": {"AppID": "1"}}, ("AppState", "appid"), "1", id="ascii-rev"),
        pytest.param({"Straße": "v"}, ("STRASSE",), "v", id="sharp-s"),
        pytest.param({"STRASSE": "v"}, ("straße",), "v", id="sharp-s-rev"),
    ],
)
def test_v5_find_compares_keys_with_casefold(mapping, keys, expected):
    assert vdf.find(mapping, *keys) == expected


@pytest.mark.parametrize(
    ("mapping", "expected"),
    [
        pytest.param({"name": "first", "Name": "second"}, "second", id="lower-then-title"),
        pytest.param({"Name": "first", "name": "second"}, "second", id="title-then-lower"),
        pytest.param({"NAME": "1", "name": "2", "Name": "3"}, "3", id="three-variants"),
    ],
)
def test_v5_find_tries_the_last_matching_key_in_the_file_first(mapping, expected):
    assert vdf.find(mapping, "nAmE") == expected


def test_v5_find_on_parsed_duplicate_keys_differing_only_by_case():
    parsed = vdf.parse('"Name" "first"\n"NAME" "second"')
    assert parsed == {"Name": "first", "NAME": "second"}
    assert vdf.find(parsed, "name") == "second"


@pytest.mark.parametrize(
    ("keys", "expected"),
    [
        pytest.param(("a", "b", "c"), "1", id="backtracks-two-levels"),
        pytest.param(("a", "b", "x"), "2", id="backtracks-one-level"),
        pytest.param(("a", "b", "y"), "3", id="last-candidates-resolve"),
        pytest.param(("A", "B"), {"y": "3"}, id="first-resolving-block"),
        pytest.param(("a",), {"b": {"y": "3"}}, id="last-top-level-candidate"),
    ],
)
def test_v5_find_returns_the_first_candidate_that_resolves_the_whole_path(keys, expected):
    assert vdf.find(BRANCHY, *keys) == expected


@pytest.mark.parametrize(
    ("mapping", "keys", "expected"),
    [
        pytest.param({"a": {"b": "deep"}, "A": "flat"}, ("a", "b"), "deep", id="later-str"),
        pytest.param({"A": "flat", "a": {"b": "deep"}}, ("a", "b"), "deep", id="earlier-str"),
        pytest.param({"a": {"b": "deep"}, "A": "flat"}, ("a",), "flat", id="str-ends-path"),
    ],
)
def test_v5_find_skips_a_non_dict_candidate_and_tries_the_next(mapping, keys, expected):
    assert vdf.find(mapping, *keys) == expected


@pytest.mark.parametrize(
    ("mapping", "keys"),
    [
        pytest.param({"a": "flat"}, ("a", "b"), id="str-at-first-step"),
        pytest.param({"a": {"b": "x"}}, ("a", "b", "c"), id="str-at-second-step"),
        pytest.param({"a": {"b": ""}}, ("a", "b", "c"), id="empty-str-at-second-step"),
        pytest.param({"a": {"b": "x"}, "A": "flat"}, ("a", "b", "c"), id="every-candidate"),
    ],
)
def test_v5_find_returns_none_when_a_step_hits_a_non_dict(mapping, keys):
    assert vdf.find(mapping, *keys) is None


@pytest.mark.parametrize(
    ("mapping", "keys"),
    [
        pytest.param({}, ("a",), id="empty-mapping"),
        pytest.param({"a": "x"}, ("b",), id="missing-key"),
        pytest.param({"a": {"b": "x"}}, ("a", "c"), id="missing-nested-key"),
        pytest.param({"name": "x"}, ("nam",), id="prefix-is-not-a-match"),
        pytest.param({"name ": "x"}, ("name",), id="whitespace-matters"),
        pytest.param(BRANCHY, ("a", "b", "z"), id="no-candidate-resolves"),
    ],
)
def test_v5_find_returns_none_when_no_path_resolves(mapping, keys):
    assert vdf.find(mapping, *keys) is None


def test_v5_find_returns_an_empty_string_value_as_is():
    mapping = {"CompatToolMapping": {"553850": {"name": ""}}}
    result = vdf.find(mapping, "compattoolmapping", "553850", "NAME")
    assert isinstance(result, str)
    assert result == ""


def test_v5_find_with_no_keys_returns_the_mapping_itself():
    for mapping in ({}, {"a": "b"}, {"a": {"b": {}}}, vdf.parse(APPMANIFEST_ACF)):
        assert vdf.find(mapping) is mapping


def test_v5_find_returns_a_block_when_the_path_ends_on_one():
    parsed = vdf.parse(APPMANIFEST_ACF)
    assert vdf.find(parsed, "appstate", "userconfig") == {"language": "english"}


def test_v5_find_does_not_modify_the_mapping():
    mapping = copy.deepcopy(BRANCHY)
    for keys in [("a", "b", "c"), ("a", "b", "z"), ("A",), ("q",), ()]:
        vdf.find(mapping, *keys)
    assert mapping == BRANCHY
    assert list(mapping) == list(BRANCHY)
    assert list(mapping["a"]) == list(BRANCHY["a"])


def test_v5_find_reads_realistic_files_regardless_of_key_case():
    current = vdf.parse(LIBRARYFOLDERS_CURRENT)
    legacy = vdf.parse(LIBRARYFOLDERS_LEGACY)
    acf = vdf.parse(APPMANIFEST_ACF)
    assert vdf.find(current, "LibraryFolders", "1", "PATH") == "/run/media/mmcblk0p1"
    assert vdf.find(legacy, "libraryfolders", "2") == "D:\\SteamLibrary"
    assert vdf.find(legacy, "LIBRARYFOLDERS", "1") == "/run/media/mmcblk0p1"
    assert vdf.find(acf, "appstate", "APPID") == "2246340"
    assert vdf.find(acf, "AppState", "stateflags") == "4"
    assert vdf.find(acf, "AppState", "InstalledDepots", "2246341", "manifest") == (
        "6290000000000000000"
    )
    assert vdf.find(acf, "AppState", "buildid", "x") is None
    assert vdf.find(acf, "AppState", "missing") is None


@pytest.mark.parametrize(
    ("appid", "expected"),
    [
        pytest.param("2246340", "proton_9", id="set"),
        pytest.param("0", "proton_experimental", id="global-default-entry"),
        pytest.param("553850", "", id="empty-name"),
        pytest.param("2183900", None, id="not-listed"),
    ],
)
def test_v5_find_reads_compat_tool_mapping_from_config_vdf(appid, expected):
    config = vdf.parse(CONFIG_VDF)
    assert vdf.find(config, *COMPAT, appid, "name") == expected


def test_v5_find_falls_back_past_a_later_case_variant_block_in_config_vdf():
    config = vdf.parse(CONFIG_VDF_CASE_VARIANTS)
    assert vdf.find(config, *COMPAT, "2183900", "name") == "GE-Proton9-20"
    assert vdf.find(config, "InstallConfigStore", "Software", "VALVE") == {
        "steam": {"SurveyDateVersion": "1"}
    }
    assert vdf.find(config, *COMPAT, "2246340", "name") is None


# -------------------------------------------------------------------------- V6 purity

ALLOWED_IMPORTS = {"__future__", "re", "typing"}
IO_BUILTINS = {"open", "print", "input", "__import__", "eval", "exec", "breakpoint"}


def vdf_ast() -> ast.Module:
    return ast.parse(VDF_SOURCE.read_text(encoding="utf-8"), filename=str(VDF_SOURCE))


def test_v6_the_checked_source_is_the_module_under_test():
    assert Path(vdf.__file__).resolve() == VDF_SOURCE.resolve()


def test_v6_imports_only_future_re_and_typing():
    imported = set()
    for node in ast.walk(vdf_ast()):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add("." * node.level + (node.module or ""))
    assert sorted(imported - ALLOWED_IMPORTS) == []


def test_v6_makes_no_io_calls():
    offenders = []
    for node in ast.walk(vdf_ast()):
        if isinstance(node, ast.Name) and node.id in {"open", "__import__", "__builtins__"}:
            offenders.append(f"line {node.lineno}: {node.id}")
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in IO_BUILTINS:
            offenders.append(f"line {node.lineno}: {func.id}()")
        elif isinstance(func, ast.Attribute) and func.attr == "open":
            offenders.append(f"line {node.lineno}: .open()")
    assert offenders == []


def test_v6_parse_and_find_work_with_file_opening_disabled(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError(f"deckforge.vdf tried to open a file: {args!r}")

    monkeypatch.setattr(builtins, "open", refuse)
    monkeypatch.setattr(io, "open", refuse)
    monkeypatch.setattr(os, "open", refuse)
    config = vdf.parse(CONFIG_VDF)
    assert vdf.find(config, *COMPAT, "2246340", "name") == "proton_9"
    with pytest.raises(vdf.VdfError):
        vdf.parse('"a" {')
