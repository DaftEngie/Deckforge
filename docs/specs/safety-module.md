# Spec: `deckforge.safety`: preview, backup, apply, restore

Status: answers from Fede recorded 2026-10-22; approved for clarifier review.

Every later write DeckForge makes to a user's Deck goes through this module (CLAUDE.md
R10). The first user is `tune`.

## Goal (one sentence, user-visible)

Before DeckForge changes a game's settings file, it shows exactly what will change and
saves a backup. It refuses anything outside its rules, and it can put every file back
byte-for-byte with one command.

## Fede's answers (2026-10-22)

**Q1. Which files may be written?**
- **Allowed now:** the game's own settings file: a non-registry entry in the scan card's
  `settings_files` (Wilds `config.ini`, Unreal `GameUserSettings.ini`). This holds even
  when the file is inside the game's install folder.
- **Allowed only for games whose card lists no anti-cheat:** Unreal `Engine.ini`
  (advanced tweaks).
- **Never:**
  - game program or data files;
  - save files;
  - Wine registry files (`user.reg`, `system.reg`);
  - Steam's own files;
  - anything in SteamOS itself, or the BIOS.
- **Later, separate module (not this spec):** shader-cache housekeeping, such as removing
  caches of uninstalled games with Fede's OK.
- **Experimental and far later (Tier I under CLAUDE.md, never in this module):**
  changing game shaders or code. That is only for games with no anti-cheat and no
  anti-tamper, opt-in per game.

**Q2. Launch options.**
- DeckForge never edits Steam's files.
- `tune`, in a later spec, builds one combined launch-option line (MangoHud, lsfg-vk,
  etc.) to paste.
- The Decky plugin will later set it through Steam's own client interface, saving the old
  line first.

**Q3. File changed since apply.** Restore shows the difference and stops. It overwrites
only with explicit confirmation, after backing up the current version.

**Q4. Game running.** Apply and restore refuse while that game is running. The plugin
will later queue the change until the game quits.

**Q5. File missing.** Refuse: "launch the game once, then retry". Never create a settings
file.

**Q6. Read-only file.** Ask first. With confirmation:
1. temporarily add the owner's write permission;
2. apply;
3. put the file's original permissions back exactly.

A file DeckForge cannot unlock (for example, the immutable attribute) is refused.

**Q7. Steam Cloud.** Detect, warn ("these settings may sync to your other devices"),
and apply only with confirmation.

## Interface (module `src/deckforge/safety.py`, standard library only)

- **`plan(card, target_path, new_bytes) -> Change`**
  - Validates Q1 against the card and returns a frozen dataclass `Change`
    `(appid, path, new_bytes)`.
  - Refusals raise `SafetyError` with a stable `code` attribute.
- **`preview(changes) -> list[dict]`**
  - Per file: `{"path", "diff", "old_sha256", "new_sha256", "warnings"}`, where `diff`
    is a unified diff of the decoded text.
  - Writes nothing.
- **`apply(changes, *, backup_root, confirm=frozenset(), proc_root="/proc", userdata_roots=()) -> str`**
  - Returns the `backup_id`.
  - `confirm` may hold `"locked"` (Q6) and `"cloud"` (Q7).
- **`restore(backup_id, *, backup_root, confirm=frozenset(), proc_root="/proc") -> dict`**
  - `confirm` may hold `"overwrite"` (Q3).
- **`list_backups(backup_root) -> list[dict]`**
- **`class SafetyError(Exception)`**, with `.code: str`.
- **`main(argv=None) -> int`**, with these commands (`apply` is a library call only,
  used by `tune`):
  - `list`
  - `show <backup_id>`
  - `restore <backup_id> [--confirm-overwrite]`
  - Shared flag: `--backup-root` (default `<home>/deckforge/backups`).

## Acceptance criteria

- **AC1 Preview.** Lists each file's diff and hashes, and writes nothing (tree hash
  unchanged).
- **AC2 Backup before write.**
  - Every original is copied to `<backup_root>/<backup_id>/` with a `manifest.json`
    before the first write. The manifest holds: `backup_id`, `created_utc`,
    `deckforge_version`, `appid`, and per file `path`, `size`, `mode`, `sha256_before`,
    `sha256_after`.
  - The backup copy's SHA-256 is verified after writing it.
- **AC3 Atomic write.**
  - Write to a temp file in the same folder, fsync, `os.replace`, then fsync the folder.
  - Each file ends up fully old or fully new.
  - Permissions are kept, and leftover temp files are removed on error.
  - The bytes written are exactly `new_bytes`; encoding, line endings and BOM are the
    caller's responsibility.
- **AC4 Allowlist (Q1).** `plan` refuses before anything is touched, each with its own
  code:
  - a path that is not a non-registry `settings_files` entry of that card
    (`not_a_settings_file`);
  - a registry file (`registry_file`);
  - `Engine.ini` (case-insensitive) on a card with non-empty `anticheat`
    (`engine_ini_anticheat`);
  - a path that is empty, relative or contains `..` (`bad_path`);
  - a target that is a link (`symlink`).
  - Steam's own files (`config/*.vdf`, `userdata/**/localconfig.vdf`) can never appear as
    targets, because they are never in `settings_files`. A test proves it.
- **AC5 Restore.**
  - Every file returns byte-identical to `sha256_before`, with its original mode.
  - The backup is verified against its manifest first.
  - A missing, edited or corrupt manifest or backup copy is refused
    (`backup_corrupt`).
- **AC6 Round trip.** For any change set over the fixture tree, apply then restore gives
  the starting tree hash.
- **AC7 Missing file (Q5).** A target that doesn't exist is refused
  (`file_missing: launch the game once, then retry`). Nothing is ever created.
- **AC8 No silent failure.** On any error during apply (disk full, permission,
  interrupted):
  - stop;
  - roll back files already changed, from the backup;
  - report what happened.
  - If the rollback itself fails, keep the backup and print where the originals are
    (R12).
- **AC9 Game running (Q4).** Apply and restore refuse (`game_running`) when any process
  under `proc_root` has `SteamAppId=<appid>` or `STEAM_COMPAT_APP_ID=<appid>` in its
  environ, or an `exe` link resolving inside the card's `install_path`. If `proc_root`
  can't be read at all, refuse (`cannot_check_running`, fail closed).
- **AC10 Locked file (Q6).**
  - A target without owner-write permission is refused (`file_locked`) unless `"locked"`
    is in `confirm`.
  - With confirmation, the write follows Q6, and the final mode equals the original
    mode.
  - Restore puts back the mode recorded in the manifest.
- **AC11 Steam Cloud (Q7).**
  - If the target's base name appears in any `<userdata_root>/<account>/<appid>/remotecache.vdf`,
    `preview` adds the warning `cloud_synced`.
  - `apply` refuses (`cloud_synced`) unless `"cloud"` is in `confirm`.
  - An unreadable `remotecache.vdf` adds the warning `cloud_unknown` (not a refusal).
- **AC12 Changed since apply (Q3).**
  - If a file's current SHA-256 differs from `sha256_after`, `restore` refuses
    (`changed_since_apply`) and returns the diff, unless `"overwrite"` is in `confirm`.
  - With confirmation, the current version is first saved as a new backup.
- **AC13 One at a time.** A lock file in `backup_root` stops two applies or restores
  running at once (`busy`). A stale lock whose recorded PID no longer exists is taken
  over.
- **AC14 Restore never deletes.** Restore only overwrites files listed in the manifest.
  It never deletes files or folders, and it never deletes recursively (R6).
- **AC15 CLI.** `list`, `show` and `restore` behave as above. Exit codes:
  - 0 on success;
  - 2 on `SafetyError`, with one stderr line containing the code;
  - other exceptions propagate.

## Out of scope

- Deciding what to change (`tune`).
- Building launch-option lines (`tune`).
- Shader-cache housekeeping and storage cleanup (a later module, with its own deletion
  rules).
- The Decky plugin.
- Tier I anything.

## Files and interfaces involved

- New: `src/deckforge/safety.py`, `tests/test_safety_*.py`.
- Reused:
  - discover's card shape;
  - the `snapshot._read_file` pattern (lstat, `O_NOFOLLOW`) for reads (R13);
  - `deckforge.vdf` for `remotecache.vdf`.

## Safety

- **Writes:**
  - only the exact settings file named in a `Change`;
  - its backup under `<backup_root>`;
  - the lock file.
- **Undo:** `python3 -m deckforge.safety restore <backup_id>`.
- **Unusual setups:**
  - SD-card library: allowed, since paths come from the card;
  - SD card missing at restore: refuse (`file_missing`), backup kept;
  - Flatpak Steam: paths come from the card;
  - paths with spaces or non-English characters;
  - full backup disk: refuse before any write.

## End-to-end check Fede will run on the Deck

This waits for `tune`, which is the first caller of `apply`.

1. `python3 -m deckforge.safety list` shows the backups.
2. `python3 -m deckforge.safety restore <id>` puts the file back.
3. The tool prints matching SHA-256 values.

## Clarifier questions and answers (filled before tests are written)
