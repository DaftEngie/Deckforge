r"""Parser for Valve's text KeyValues format (VDF), as used by Steam's .vdf and .acf files.

Supported: quoted and unquoted tokens, `{ }` blocks, `//` comments where a token could
start, the escapes `\\`, `\"`, `\n` and `\t` inside quotes (any other backslash is kept
as written), and LF or CRLF line ends. A key repeated at one level keeps only its last
value; blocks are never merged. Key case is preserved; `find` ignores it.

Refused with VdfError (docs/specs/discover.md, V4): empty input, NUL characters,
unterminated strings or raw newlines inside quotes, misplaced braces, a key with no
value, unclosed blocks, nesting deeper than 100 blocks, unquoted `#include` / `#base`
keys and unquoted `[...]` conditionals. Binary VDF is out of scope.

Text in, dicts out: no I/O. Decoding bytes and stripping a BOM are the caller's job.
Error messages name a line but never quote file contents (config.vdf holds account data).
"""

from __future__ import annotations

import re
from typing import Any

_MAX_DEPTH = 100
_DIRECTIVES = ("#include", "#base")
# Opening quote and body, up to the closing quote. Possessive `*+` (Python 3.11+) keeps no
# backtracking state, so memory stays flat on a long string; the two branches start with
# different characters, so it matches exactly what a plain `*` would.
_STRING_PREFIX = r'"(?:[^"\\\n]|\\[^\n])*+'
_TOKEN = re.compile(
    r"(?P<space>[ \t\r\n]+)"
    r"|(?P<comment>//[^\n]*)"
    r"|(?P<quoted>" + _STRING_PREFIX + r'")'
    r"|(?P<open>\{)"
    r"|(?P<close>\})"
    r'|(?P<bare>[^ \t\r\n"{}]+)'
)
_UNCLOSED_STRING = re.compile(_STRING_PREFIX)
_ESCAPE = re.compile(r"\\(.)")
_ESCAPES = {"\\": "\\", '"': '"', "n": "\n", "t": "\t"}


class VdfError(ValueError):
    """Text that is not valid VDF or uses a refused feature. `.line` is 1-based."""

    def __init__(self, problem: str, line: int) -> None:
        super().__init__(f"{problem} at line {line}")
        self.line = line


def parse(text: str) -> dict[str, Any]:
    """Parse VDF text into nested dicts whose values are str or dict.

    Raises VdfError for every case in the V4 table and returns nothing partial.
    Iterative, so deep nesting never raises RecursionError.
    """
    nul = text.find("\x00")
    if nul >= 0:
        raise VdfError("NUL character", text.count("\n", 0, nul) + 1)
    root: dict[str, Any] = {}
    block = root
    parents: list[tuple[dict[str, Any], int]] = []  # enclosing block, line of the brace
    key: str | None = None  # set while a value is expected
    key_line = 0
    seen_token = False
    pos, line = 0, 1
    while pos < len(text):
        match = _TOKEN.match(text, pos)
        if match is None:  # every character but a quote starts some token
            raise VdfError(_bad_string_problem(text, pos), line)
        kind, token, pos = match.lastgroup, match.group(), match.end()
        if kind in ("space", "comment"):
            line += token.count("\n")
            continue
        seen_token = True
        if kind == "bare" and token.startswith("["):
            raise VdfError("unquoted token starting with '[' (conditional)", line)
        if key is None:
            if kind == "open":
                raise VdfError("'{' where a key is expected", line)
            if kind == "close":
                if not parents:
                    raise VdfError("'}' with no open block", line)
                block, _ = parents.pop()
            elif kind == "bare" and token in _DIRECTIVES:
                raise VdfError(f"unsupported {token} directive", line)
            else:
                key, key_line = _token_text(kind, token), line
        elif kind == "close":
            raise VdfError("'}' where a value is expected", line)
        elif kind == "open":
            if len(parents) == _MAX_DEPTH:
                raise VdfError(f"nesting deeper than {_MAX_DEPTH} blocks", line)
            child: dict[str, Any] = {}
            _store(block, key, child)
            parents.append((block, line))
            block, key = child, None
        else:
            _store(block, key, _token_text(kind, token))
            key = None
    if not seen_token:
        raise VdfError("empty document", 1)
    if key is not None:
        raise VdfError("key with no value at end of input", key_line)
    if parents:
        raise VdfError("'{' never closed", parents[-1][1])
    return root


def find(mapping: dict[str, Any], *keys: str) -> str | dict[str, Any] | None:
    """Follow `keys` through nested dicts, comparing keys with casefold().

    At each level every matching key is a candidate, tried from the last in the file
    to the first; the first value that resolves the whole remaining path is returned.
    Returns None if no path resolves. With no keys, returns `mapping` itself.
    """
    pending: list[tuple[Any, int]] = [(mapping, 0)]
    while pending:
        node, depth = pending.pop()
        if depth == len(keys):
            return node
        if isinstance(node, dict):
            wanted = keys[depth].casefold()
            # Pushed in file order, so the last match in the file is popped first.
            pending.extend((v, depth + 1) for k, v in node.items() if k.casefold() == wanted)
    return None


def _token_text(kind: str | None, token: str) -> str:
    """A key or value token as text: quotes stripped and escapes decoded if quoted."""
    if kind != "quoted":
        return token
    return _ESCAPE.sub(lambda m: _ESCAPES.get(m.group(1), m.group(0)), token[1:-1])


def _store(block: dict[str, Any], key: str, value: str | dict[str, Any]) -> None:
    """Last value wins; re-inserting keeps dict order equal to the file order `find` uses."""
    block.pop(key, None)
    block[key] = value


def _bad_string_problem(text: str, start: int) -> str:
    """Why the quoted string opened at `start` has no closing quote on its line."""
    prefix = _UNCLOSED_STRING.match(text, start)
    end = prefix.end() if prefix else start
    if text.startswith("\n", end) or text.startswith("\\\n", end):
        return "raw newline inside a quoted string opened"
    return "unterminated quoted string opened"
