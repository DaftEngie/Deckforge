# Spec: `deckforge.snapshot` — read-only Deck snapshot for remote analysis

## Goal (one sentence, user-visible)

Fede runs one command on his Deck. It writes a single zip file he can upload to Claude, containing what DeckForge needs to write profiles and plan cleanup: games, settings files, cache sizes, Decky plugins, frame-time logs and system facts. It changes nothing else on the Deck.

## Delivery

One PR, stacked on `feat/discover-detect` (PR #5), because it reuses `deckforge.discover.scan`, which already includes the `deckforge.detect` card fields.

## Interface

- `build_snapshot(steam_root, home, out_dir, *, now) -> str`
  - Writes the zip and returns its path.
  - `now` is a `datetime`, injected so tests are deterministic.
- `class SnapshotError(Exception)`
- `main(argv: list[str] | None = None) -> int`
  - Flags: `--steam-root` (required), `--home` (default `os.path.expanduser("~")`), `--out-dir` (default `<home>/deckforge/snapshots`).
- `__main__` guard: `raise SystemExit(main())`.

## Acceptance criteria

**S1 Scan.**
- The zip contains `scan.json`: the result of `deckforge.discover.scan(steam_root)`, serialized like B8 (`indent=2, sort_keys=True, ensure_ascii=True`).
- `DiscoverError` → `SnapshotError`, and no zip is written.

**S2 Settings files.** For every card with `installed: true`, each entry in its `settings_files` is copied into the zip at `settings/<appid>/<n>_<basename>`. `n` is the entry's index in the list.
- **Not copied:** files that are not regular files (checked with `lstat`, so a link is skipped), files larger than 1 MiB, and entries whose `kind` is `reg` (Wine registry files can hold personal data).
- Each skip is recorded in `manifest.json` with a reason:

  | Reason | When |
  |---|---|
  | `not_regular` | Not a regular file, including a link |
  | `too_large` | Larger than 1 MiB |
  | `excluded_kind` | `kind` is `reg` |
  | `unreadable` | An OS error while reading |

**S3 Sizes and orphans.**
- `sizes.json` gives each card's total byte size of `shadercache_path` and of its compatdata folder (`<library>/steamapps/compatdata/<appid>`), or `null` if absent.
- Sizes are summed with `os.scandir` and `lstat` (`follow_symlinks=False`); links are never followed.
- It also lists **orphans**: every all-digit entry under each available library's `steamapps/shadercache` and `steamapps/compatdata` whose appid has no card in `scan.json`. For each it gives the path and byte size.
- Folder errors while sizing become `{"code": "size_unreadable", "path": ...}` issues in `sizes.json`. They are never silent (R12).

**S4 Decky plugins.**
- For each folder in `<home>/homebrew/plugins`, read `plugin.json` (the `name` key) and `package.json` (the `version` key): regular files of 1 MiB or less, UTF-8 JSON.
- Output is `plugins.json` as a list of `{"folder", "name", "version"}`, sorted by folder. A missing or invalid file gives `null` for that field, plus an issue.
- A missing `homebrew/plugins` folder gives an empty list and a `decky_not_found` issue.

**S5 Frame-time logs.**
- Copies the 5 newest regular files matching `*.csv` in `<home>/deckforge/logs`, newest first by mtime, into `logs/`.
- Files larger than 20 MiB are skipped, with a `too_large` entry in the manifest.
- A missing folder gives no logs, and the manifest notes `logs_not_found`.

**S6 System facts.** `system.json` contains:
- `os_release`: the `/etc/os-release` key/value pairs. Only these keys are kept: `NAME`, `PRETTY_NAME`, `VERSION_ID`, `BUILD_ID`, `VARIANT_ID`.
- `kernel`: from `os.uname().release`.
- `board`: from `/sys/devices/virtual/dmi/id/board_name`. `Galileo` means OLED and `Jupiter` means LCD. Unreadable gives `null`.
- `disk`: `shutil.disk_usage` (total, used, free) for `home` and for each available library.

The file paths are read through module-level constants, so tests can redirect them.

**S7 Manifest.**
- `manifest.json` lists every file added (zip name, source path, size) and every skip (source path, reason).
- It records `snapshot_version: 1` and `created_utc` (from `now`, ISO 8601).

**S8 Output safety.**
- The zip path is `<out_dir>/deckforge-snapshot-<YYYYmmdd-HHMMSS>Z.zip`.
- `out_dir` is created with `os.makedirs(exist_ok=True)`.
- If the target file already exists, `SnapshotError` is raised and nothing is written or changed.
- The zip is written to `<target>.partial`, then `os.replace`d into place. On any error the partial file is removed and the error re-raised. No partial zip is left behind.
- `out_dir` must not be inside `steam_root`, or any library, or `<home>/homebrew`, after `realpath` on both sides. Otherwise `SnapshotError`.

**S9 Read-only everywhere else.**
- **Change detector:** the B9 change detector, run over the Steam tree, `<home>/homebrew` and `<home>/deckforge/logs`, shows no change.
- **Allowed writes:** the only writes are inside `out_dir`. No other file or folder is created or changed.
- **Never opened:** `config/config.vdf` contents beyond what `scan` reads, save files, `user.reg` and `system.reg`.

**S10 CLI.**
- On success, prints the zip path and the counts of settings files copied, logs copied and orphans found. Returns 0.
- `SnapshotError` → a one-line message on stderr, and returns 2.
- Other exceptions propagate (R12).

## Out of scope

- Any change to games, settings, caches or plugins. That comes later and goes through `deckforge.safety`.
- Uploading anywhere. Fede uploads the zip by hand.
- Measuring frame times. This module only collects existing logs.

## Files and interfaces involved

- New: `src/deckforge/snapshot.py`, `tests/test_snapshot_*.py`.
- Reused: `deckforge.discover.scan`.
- Imports: stdlib only (R8), namely `json`, `os`, `stat`, `shutil`, `zipfile`, `datetime`, `argparse`, `logging`, `pathlib`, `sys`, `typing`, `dataclasses`.

## Safety

- **Reads:** the Steam library tree (scan), detected settings files, cache folder sizes, the Decky plugin manifests, `~/deckforge/logs`, `/etc/os-release` and the board name.
- **Writes:** one new zip in `~/deckforge/snapshots/`. It never overwrites.
- **Undo:** delete the zip.
- **Unusual setups:**
  - an SD-card library is scanned like any other library;
  - Flatpak Steam: pass `--steam-root` explicitly;
  - Steam running: fine, because everything is read-only;
  - a full disk: the partial file is removed and the error is reported.
- **Privacy:** no saves, no registry files, no `config.vdf` contents. Settings files and logs hold no account data.

## End-to-end check Fede will run on the Deck

1. Desktop mode → Konsole.
2. `cd ~/deckforge-repo && git pull`.
3. `PYTHONPATH=src python3 -m deckforge.snapshot --steam-root ~/.local/share/Steam`.
4. Upload the printed zip to Claude.

## Clarifier questions and answers

1. Should the default cover all installed games or only chosen ones? **Default: all installed games.** Settings files are small; the scan already covers everything.
2. Should Wine `user.reg` be included for games that keep settings there? **No, by default** (privacy). Revisit per game if a profile needs it.
