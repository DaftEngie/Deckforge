# Spec: `deckforge.vdf` + `deckforge.discover` — read-only scan of a Steam install

Status: **APPROVED FOR AN UNATTENDED RUN, 2026-10-11.** Fede asked for Phase 1 work
overnight. This module only reads files, so it can proceed while the safety-spec
questions (Q1–Q7) are open. The clarifier's review (2026-10-11) was folded in with
conservative defaults. The items Fede must confirm are listed at the bottom.
Design context: `docs/design/LAUNCH_FLOW.md`, Stage 1 (branch `design/overnight-rethink`).

## Goal (one sentence, user-visible)

Given the path to a Steam folder, DeckForge lists every installed game with what it needs
to know before touching anything: build, engine, anti-cheat, upscalers shipped, Proton
prefix, and where the settings files live. It changes nothing on disk.

## Delivery: three small PRs (R15), stacked

| PR | Module | ACs |
|---|---|---|
| A | `src/deckforge/vdf.py` — Valve text KeyValues parser | V1–V6 |
| B1 | `src/deckforge/discover.py` — libraries, manifests, paths, Proton version, JSON, CLI | B1–B9 |
| B2 | `src/deckforge/detect.py` + integration — walks, engine, anti-cheat, upscalers, injectors, settings files, Tier I eligibility | C1–C9 |

All three: standard library only (R8). Tests are new files under `tests/`, with every
fixture built under pytest's `tmp_path`. `conftest.py` and `tests/fixtures/golden/` are
protected and are not used.

---

## PR A — `deckforge.vdf`

Interface: `parse(text: str) -> dict`, `find(mapping, *keys)`, and
`class VdfError(ValueError)`, which has an int attribute `.line` (1-based).

- **V1 Grammar.** A document is zero or more pairs; a pair is a key token followed by
  either a value token or `{` pairs `}`.
  - **Tokens:**
    - Quoted strings.
    - Unquoted tokens: any run of characters except whitespace, `"`, `{` and `}`.
    - `{` and `}`.
  - **Whitespace** is space, tab, `\r` and `\n`.
  - **Comments:** `//` starts a comment, running to the end of the line, only where a
    new token could start.
  - **Result:** nested `dict`s with `str` keys and values that are `str` or `dict`. Key
    case is preserved.
- **V2 Strings.**
  - Inside quotes, the escapes `\\`, `\"`, `\n` and `\t` are decoded. Any other backslash
    is kept as written, together with the character after it.
  - A raw newline inside quotes is an error.
- **V3 Duplicates.** A repeated key at the same level: the last value wins and replaces
  the earlier one entirely. Blocks are never merged.
- **V4 Errors.** `parse` raises `VdfError` and returns no partial result when it finds
  any of the cases below. The message contains `line <n>`, matching `.line`.

  | Case | `.line` is the line of |
  |---|---|
  | Empty input, or only whitespace and comments | 1 |
  | Unterminated string, or a raw newline inside quotes | The opening quote |
  | Stray `}` | That `}` |
  | `{` where a key is expected | That `{` |
  | Key with no value at the end of input | The key |
  | `}` where a value is expected (e.g. `"a" }`) | That `}` |
  | `{` never closed at the end of input | The innermost unclosed `{` |
  | An unquoted `#include` or `#base` token in key position | That token |
  | Any unquoted token starting with `[` (conditionals such as `[$WIN32]`) | That token |
  | A NUL character anywhere | The NUL character |
  | Nesting deeper than 100 blocks | The 101st `{` |

  - Lines are counted on `\n`; `\r\n` counts as one line.
  - Deep nesting must never raise `RecursionError`.
- **V5 Lookup.** `find(mapping, *keys)` walks nested dicts, comparing keys with
  `casefold()`.
  - At each level it tries every matching key, the last one in the file first, and
    returns the first value that resolves the whole remaining path.
  - It returns `None` if no path resolves, or if a step hits a non-dict.
  - `find(m)` with no keys returns `m`.
- **V6 Purity.** `vdf.py` imports only from this list: `__future__`, `re`, `typing`.
  It does no I/O.

## PR B1 — `deckforge.discover`: libraries, manifests, paths, CLI

Interface:
- `scan(steam_root: str | os.PathLike) -> dict`
- `find_libraries(steam_root) -> list[dict]`
- `class DiscoverError(Exception)`
- `main(argv: list[str] | None = None) -> int`
- A module `__main__` guard: `raise SystemExit(main())`.

**Issue shape (used everywhere).** An issue is
`{"code": str, "path": str | None, "message": str}`.
- Lists of issues are sorted by `(code, path or "")`.
- Tests check `code` and `path`, never the message text.
- Messages never include file contents (`config.vdf` holds account data); they may
  include line numbers.

- **B1 Root.**
  - `steam_root` in the output is the argument made absolute and normalized
    (`os.path.abspath`), not resolved through links. `~` is not expanded.
  - If `<root>/steamapps/libraryfolders.vdf` is missing, `scan` and `find_libraries`
    raise `DiscoverError`. The same happens if that file is not a regular file, is
    larger than 1 MiB, cannot be read, is not UTF-8, fails to parse, or has no
    `libraryfolders` key (looked up with `find`; a leading BOM is accepted).
- **B2 Libraries.** `find_libraries` returns `[{"path": str, "available": bool}]`. The
  root comes first, then the file's numbered keys in numeric order ("10" after "2").
  - A numbered key's value is either a block with a `path` key (current format) or the
    path string itself (legacy format).
  - Non-numbered keys are ignored.
  - A numbered block with no `path` adds a `library_entry_invalid` warning (path
    `None`) and is skipped.
  - A path that is empty, not absolute, or contains `\` stays in the list with
    `available: false` and adds a `library_path_invalid` warning (path = the text as
    written). It is never resolved against the current folder.
  - Listed paths are normalized (`os.path.normpath`). Libraries are de-duplicated by
    their real path (`os.path.realpath`); the first one wins, so the root wins over a
    listed duplicate.
  - `available` is true only if `<path>/steamapps` is a folder that `os.scandir` can
    list.
    - Not a folder: `available: false` and a `library_unavailable` warning (path = the
      library path).
    - A folder that can't be listed: `available: false`, a `library_unreadable` error,
      and a `library_unavailable` warning.
- **B3 Manifests.** In each available library, every entry of `steamapps` whose name
  matches `appmanifest_<x>.acf` exactly (case-sensitive) is read. Only regular files are
  opened (a link to a regular file is fine). Files are decoded as strict UTF-8, with a
  leading BOM stripped. Errors (no card is made):

  | Code | When |
  |---|---|
  | `manifest_unreadable` | Not a regular file, larger than 1 MiB, or an OS error while reading |
  | `manifest_malformed` | Not UTF-8, `VdfError`, or no `AppState` block |
  | `manifest_incomplete` | `appid` or `installdir` missing (looked up with `find`) |
  | `manifest_appid_mismatch` | `<x>` is not all digits, the `appid` value is not all digits, or the two differ |
  | `manifest_unsafe_installdir` | `installdir` is empty, `.` or `..`, contains `/` or `\`, or is absolute |

  The issue's `path` is the manifest's full path. Other manifests are still scanned.
- **B4 Card fields (B1 part).**

  | Field | Value |
  |---|---|
  | `appid` | int |
  | `name` | str, or `null` with a `name_missing` card warning |
  | `kind` | `"tool"` if the name matches `^Proton( |$)`, or starts with `Steam Linux Runtime` or `Steamworks Common Redistributables` (case-sensitive); otherwise `"game"` |
  | `library` | The library's path string |
  | `installdir` | str |
  | `buildid` | str or `null` |
  | `state_flags` | int, or `null` with a `stateflags_invalid` card warning if missing or not an integer |
  | `installed` | `(state_flags & 4) != 0` **and** the install folder exists. Examples: `"4"`, `"6"`, `"1030"` → true; `"16"`, `"1026"` → false |
  | `install_path` | `<library>/steamapps/common/<installdir>`. If that folder does not exist (exact case), add an `install_folder_missing` card warning |
  | `prefix_path` | `<library>/steamapps/compatdata/<appid>/pfx` if it is a folder. If it is **absent** (not found, or a path part is not a folder), the same path under the root library, if that is a folder (then add a `prefix_in_other_library` card warning). Otherwise `null`. If checking the game's own prefix fails with any other OS error (permission, I/O, link loop), there is **no fallback**: `prefix_path` is `null` and a `prefix_unreadable` card warning is added (path = the game's own prefix path). Later phases write into prefixes, so a guess is never allowed (verifier F1/Q2, 2026-10-11) |
  | `shadercache_path` | `<library>/steamapps/shadercache/<appid>` if it is a folder, else `null` |
  | `compat_tool` | See B5 |
  | `warnings` | Card issues, sorted |

  Path strings are built with `os.path.join` from the library's path string. They are
  not resolved.

  **Errors while checking folders are never silent (R12).** When a folder check (for
  `steamapps`, `common`, an install folder, a prefix or a shader cache) fails with an
  OS error other than "not found" or "not a folder", one of two things must happen. The
  problem becomes an issue whose path is that folder, or it is logged at WARNING level
  with that path (logger `deckforge.discover`). If `<library>/steamapps/common` exists
  but cannot be listed, a top-level `common_unreadable` warning is added (path = that
  folder), and the games in that library get `install_folder_missing` as before.
- **B5 Proton version.** Read `<root>/config/config.vdf` (regular file, ≤16 MiB, UTF-8).
  - `compat_tool` = `find(cfg, "InstallConfigStore", "Software", "Valve", "Steam",
    "CompatToolMapping", "<appid>", "name")`. An empty string becomes `null`.
  - The appid `0` entry (Steam's global default) is never applied. `null` means "not
    set for this game", not "no Proton".
  - File or `config` folder missing → a top-level `config_vdf_missing` warning (path =
    the expected file path). Unreadable or malformed → `config_vdf_malformed`. Both set
    every `compat_tool` to `null`. Nothing else from `config.vdf` ever reaches the
    output.
- **B6 Duplicates.** If the same appid appears in two libraries, both cards are kept and a
  top-level `duplicate_appid` warning is added (path = the later manifest's path, in
  `games` order).
- **B7 Output.** `scan` returns:
  - `discover_version`: the int `1`.
  - `steam_root`.
  - `libraries`, `games`, `errors` and `warnings` as above. `games` is sorted by
    `(appid, library)`.
  - There are no timestamps. Two scans of the same tree give equal results, and so do
    two trees built in a different creation order (apart from root paths).
- **B8 CLI.** `main(["--steam-root", PATH])` writes
  `json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n"` to stdout in
  one write and returns `0`, even if `errors` or `warnings` are non-empty.
  - A missing `--steam-root` exits with `SystemExit(2)` (argparse).
  - `DiscoverError` → a one-line message on stderr, return `2`.
  - Other exceptions are not caught; Python exits 1 with a traceback (R12: no
    catch-all).
  - stdout carries only the JSON.
  - The CLI writes no files. The current folder is unchanged after a run.
- **B9 Read-only.**
  - **Change detector:** before and after a scan, the fixture tree has identical file
    contents, entry names, sizes, link targets and modification times. The detector
    uses `lstat` and does not follow links.
  - **Only three kinds of file are ever opened:** `libraryfolders.vdf`,
    `appmanifest_*.acf` and `config/config.vdf`.
  - **Allowed imports** in `discover.py`: `__future__`, `argparse`, `json`, `logging`,
    `os`, `stat`, `sys`, `pathlib`, `re`, `fnmatch`, `dataclasses`, `typing`,
    `collections`, and `deckforge.*`.
  - **Banned calls:** no attribute calls named `write`, `write_text`, `write_bytes`,
    `unlink`, `remove`, `rmdir`, `mkdir`, `makedirs`, `rename`, `replace`, `touch`,
    `chmod`, `symlink_to`, `hardlink_to`, `symlink`, `link` or `truncate`, except
    `sys.stdout.write` and `sys.stderr.write`.
  - **`open()` modes:** every `open(...)` call uses a literal mode of `"r"` or `"rb"`.
  - **Listing:** folders are listed with `os.scandir`, so tests can monkeypatch it.

## PR B2 — `deckforge.detect` + card integration

- **C1 Walks.**
  - **Order:** breadth-first from a start folder, each folder's entries sorted by name.
  - **Depth:** the number of path parts relative to the start, so `a/b/c/file` has
    depth 4. The install walk goes to depth 10; prefix walks (C6) go to depth 6.
  - **Cap:** at most 20,000 entries (files, folders and links) per start folder.
  - **Links:** a link found during a walk is matched by its name but never entered. The
    start folder itself may be a link.
  - **Disks:** never descend into a folder on a different device (`st_dev`) than the
    start folder.
  - **Truncation:** the card gets a `scan_truncated` warning (path = the start folder)
    only if the cap was hit, or a folder at the depth limit has contents.
  - **Unreadable folders:** a folder `os.scandir` cannot list adds an `unreadable` card
    warning (path = that folder), and the walk continues.
  - **Non-UTF-8 names:** a name that is not valid UTF-8 appears in evidence via
    `backslashreplace` and adds a `non_utf8_filename` card warning.
  - **Evidence paths** are relative to the start folder, use `/`, and keep the on-disk
    case.
- **C2 Engine.** `engine` is one of `"unreal"`, `"unity"`, `"re_engine"`, `"unknown"` or
  `"ambiguous"`. `engine_evidence` is the sorted list of matched relative paths. All
  names are matched ignoring case.
  - **Unreal:** a file named `*-win64-shipping.exe` or `*-wingdk-shipping.exe`, directly
    inside `Binaries/Win64` or `Binaries/WinGDK`, anywhere within the depth limit.
  - **Unity:** `UnityPlayer.dll` at the install root or one level below; or a folder
    named `*_Data` at the root or one level below that contains `globalgamemanagers` or
    `boot.config` (the evidence is the marker file's path).
  - **RE Engine:** `re_chunk_000.pak` at the install root.
  - No match → `"unknown"`; more than one engine → `"ambiguous"`.
- **C3 Anti-cheat.** `anticheat` is `[{"system": str, "evidence": [str]}]`, one entry per
  system, sorted by system, with sorted evidence. Signatures match file or folder names,
  ignoring case, anywhere in the install walk:
  - `easyanticheat`: a name starting with `easyanticheat`, or `start_protected_game.exe`.
  - `battleye`: a name equal to `battleye`, or starting with `beservice` or `beclient`.
  - `gameguard`: a name equal to `gameguard`.

  The prefix is also walked from `drive_c/Program Files` and
  `drive_c/Program Files (x86)` (depth 6) for the `easyanticheat` and `battleye`
  signatures. Their evidence is written as `pfx/<path relative to the prefix>`, for example
  `pfx/drive_c/Program Files (x86)/EasyAntiCheat`.

  **Curated list:** `CURATED_ANTICHEAT = {2183900: "easyanticheat", 553850: "gameguard"}`
  is a module constant in `detect.py`. Phase 3 reuses it for R16. Each curated entry
  adds the evidence item `"(curated)"` to that system, merged with any file evidence.
  It applies even when the game is not installed.
- **C4 Upscalers.** `upscalers` is `[{"name", "evidence"}]`, sorted. File names match
  ignoring case, anywhere in the install walk:

  | File | Name |
  |---|---|
  | `nvngx_dlss.dll` | `dlss` |
  | `nvngx_dlssg.dll` | `dlss_fg` |
  | `amd_fidelityfx_dx12.dll`, `amd_fidelityfx_vk.dll` | `ffx_sdk` |
  | `ffx_fsr2_api_x64.dll` | `fsr2` |
  | `libxess.dll` | `xess` |

  An empty list means "no DLLs found", not "no upscaler".
- **C5 Injectors.** `injectors` is `[{"name", "evidence"}]`, sorted:
  - `optiscaler`: a file named `OptiScaler.ini`.
  - `reframework`: a folder named `reframework` whose parent folder also contains
    `dinput8.dll`. Names match ignoring case.

  If a card has any injector **and** a non-empty `anticheat`, each injector adds an
  `injector_with_anticheat` card warning (path = its evidence path).
- **C6 Settings files.** `settings_files` is `[{"path": str (absolute), "class": "P" |
  "I", "kind": str}]`, sorted by path. Each engine that matched is searched; an
  `ambiguous` game gets all of them.
  - **RE Engine:** `config.ini` at the install root → class `I`, kind `ini`.
  - **Unity:**
    - `boot.config` inside a `*_Data` folder at the root or one level below → class
      `I`, kind `boot_config`.
    - `<prefix>/user.reg` as a file → class `P`, kind `registry`.
  - **Unreal:** files named `GameUserSettings.ini` or `Engine.ini` (ignoring case) whose
    ancestor folders include `Saved` directly followed by `Config` (ignoring case) →
    class `P`, kind `ini`. The search walks, to depth 6, from
    `<prefix>/drive_c/users/steamuser/AppData/Local`,
    `<prefix>/drive_c/users/steamuser/Documents/My Games` and
    `<prefix>/drive_c/users/steamuser/My Documents/My Games`.
  - A start folder that is a link is used only if its real path is inside the prefix's
    real path. A folder named `dosdevices` is never entered.
  - Entries are de-duplicated by real path (Proton's `My Documents` is a link to
    `Documents`); the first path in sorted order is kept.
  - Only file names are inspected; settings files are never opened.
- **C7 Tier I eligibility.** `tier_i_eligible` is true only if **all** of the following
  hold:
  - `kind == "game"`;
  - the install folder exists;
  - no walk for this card was truncated;
  - no `unreadable` warning;
  - `anticheat` is empty.

  It fails closed: a scan that could not finish never says "eligible". Eligible does not
  mean enabled; Tier I is always a per-game opt-in.
- **C8 Missing install folder.** The card gets `engine: "unknown"`, empty
  `engine_evidence`, `upscalers`, `injectors` and `settings_files`, the curated
  anti-cheat entry if any, and `tier_i_eligible: false`.
- **C9 Purity.** Same import allowlist, banned calls and `os.scandir` rule as B9.
  `detect.py` opens no files at all.

---

## Out of scope

- Writing game cards to disk, which comes with `deckforge.safety`.
- Binary VDF, non-Steam games, Steam Cloud, device and driver versions, and graphics API
  detection.

## Safety

Reads only: no writes, no subprocesses, no network. The CLI requires an explicit root, so
a dev session cannot scan a real install by accident (R7). Fede runs it by hand on the
Deck with no game running and downloads paused.

Data formats come from general knowledge, not a primary source. Before Milestone 1
closes, the fixtures are checked against a sanitized copy of the real files. Fede copies
by hand only `libraryfolders.vdf`, two `.acf` files and the `CompatToolMapping` block,
with Steam IDs replaced. No agent connects to the Deck.

## End-to-end check Fede will run on the Deck

In Desktop Mode, with no game running and downloads paused:

```
mkdir -p ~/deckforge
cd ~/deckforge-repo && git pull
PYTHONPATH=src python3 -B -m deckforge.discover --steam-root ~/.local/share/Steam > ~/deckforge/scan.json; echo "exit $?"
```

(`-B` stops Python writing cache files into the checkout; `python3 --version` must be 3.11 or
newer.)

Expect `exit 0`. Then check:
- Wilds shows `re_engine`, no anti-cheat, and `config.ini` as class `I`.
- Space Marine 2 shows `easyanticheat` and `tier_i_eligible: false`.

"Changes nothing" is proven by the fixture tests. A manual check on a live Steam folder
would raise false alarms, because Steam itself writes there.

## For Fede to confirm (nothing here blocks the overnight work)

| # | Item | Default taken |
|---|---|---|
| F1 | No default Steam root; `--steam-root` is required | Yes |
| F2 | Proton and runtime entries are listed as `kind: "tool"` | Yes |
| F3 | Walk depth 10 (install) and 6 (prefix), with a cap of 20,000 entries per start folder | Yes. The earlier draft said depth 4, which would miss Unreal's DLSS and settings files |
| F4 | Tier I eligibility fails closed, so more games will show "not eligible" | Yes |
| F5 | Anti-cheat detection by name only: EAC, BattlEye and GameGuard, plus a curated list. XIGNCODE3, EQU8, PunkBuster and Denuvo Anti-Cheat are not detected | Yes; add curated entries per game |
| F6 | What does `python3 --version` print on your Deck? (The project targets 3.11+) | Unknown: needed before the Deck check |
| F7 | Do your SD-card games keep their Proton prefix on the card? | Handled either way (B4 `prefix_in_other_library`) |
