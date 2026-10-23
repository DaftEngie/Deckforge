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
Clarifier review, 2026-10-22. These answers are binding and override the ACs where they
differ. All of them take the conservative option.

1. **Only kind `ini` may be written.** Unity `boot.config` (kind `boot_config`) is
   refused (`kind_not_writable`) until Fede approves it.
2. **`Engine.ini` needs proof of no anti-cheat.** It requires the card's
   `tier_i_eligible is True`, not merely an empty `anticheat` list. Otherwise it is
   refused with `engine_ini_anticheat`.
3. **Path checks.** The target must equal a card entry's `path` exactly, as a string.
   - The last part must be a regular file and not a link (`symlink`).
   - `realpath(target)` must lie inside `realpath(install_path)` or
     `realpath(prefix_path)` (`outside_game`). Links in parent folders are allowed.
   - `apply` re-checks all of this on disk.
4. **Changed since preview.** `Change` gains `old_sha256`, set by `plan` from the file at
   that moment. `apply` refuses (`changed_since_preview`) if the file no longer matches.
   Interface: `plan(card, target_path, new_bytes)` returns
   `Change(appid, path, old_sha256, new_bytes)`.
5. **Crash safety.**
   - The backup is built in `<backup_root>/.tmp-<id>/`: copies first, each one fsynced,
     then `manifest.json` written last and fsynced.
   - The folder is renamed to `<backup_root>/<id>/`, and the parent folder fsynced.
   - All of this finishes before the first target write.
   - **Restore decides per file:**
     - current matches `sha256_before`: skip, and list it as `skipped`;
     - current matches `sha256_after`: restore;
     - otherwise: `changed_since_apply` (AC12).
   - `list` shows `.tmp-*` folders and folders without a manifest as `incomplete`, and
     never deletes them.
6. **Duplicate targets.**
   - Two Changes that resolve to the same file (same `st_dev` and `st_ino`) → refused
     (`duplicate_target`).
   - A target with a link count above 1 → refused (`hard_link`).
7. **Rollback** after a later file fails rewrites only files whose current hash equals
   our `sha256_after`. Any other file is reported in the error, never overwritten.
8. **Read-only files (Q6), restated.** With temp-file-plus-rename, the target's own mode
   never blocks the write.
   - Q6 therefore means "ask first": a target without owner-write is refused
     (`file_locked`) unless `"locked"` is in `confirm`.
   - The temp file gets the target's original mode (`chmod` on the temp file) before
     the rename, so the lock stays exactly as it was.
   - Refused: targets not owned by the current user (`not_owner`), and folders the user
     can't write to (`folder_locked`).
   - Folder permissions are never changed.
9. **Immutable or otherwise unwritable.** If `os.replace` fails with `EPERM` or
   `EACCES`, the result is `file_locked`, with the temp file cleaned up. A test fakes
   this error. There is no attempt to read the immutable attribute.
10. **Size and text.**
    - Targets and new contents are limited to 1 MiB each (`too_large`).
    - The diff decodes using the BOM (UTF-8 or UTF-16), otherwise strict UTF-8.
    - If decoding fails, the diff is `null` and the warning `not_text` is added.
11. **`backup_id`** is `<YYYYmmdd-HHMMSS>-<appid>-<8 hex from secrets.token_hex(4)>`.
    It is created with `os.mkdir`; if the id exists, a new one is drawn. A folder is
    never reused.
12. **Clock.** `created_utc` is informational only. `list` sorts by `backup_id` and
    labels the time as "Deck clock".
13. **Lock.** The lock is `fcntl.flock(LOCK_EX | LOCK_NB)` on `<backup_root>/.lock`,
    held from the first check to the last write. If the lock is held → `busy`. A lock
    left by a dead process is free automatically; there is no PID logic.
14. **Free space.** Before writing anything, `os.statvfs` must show enough room:
    - on the backup filesystem, the sum of the original sizes;
    - on each target's filesystem, its new size.

    Otherwise the result is `no_space`. Tests fake `statvfs`. AC8 still covers running
    out of space later.
15. **SD card missing.** If the target's folder (or the library root) is missing at
    apply or restore → `target_unavailable: insert the SD card or check the library`.
    Restore never creates folders.
16. **Game-running check (AC9), restated.**
    - Scan `proc_root/<pid>/environ` for `SteamAppId=<appid>` or
      `STEAM_COMPAT_APP_ID=<appid>`.
    - Processes owned by other users and unreadable are skipped.
    - An unreadable process owned by the current user → `cannot_check_running`.
    - The `exe` link is an extra signal only.
    - The check runs while holding the lock, and again just before each rename.
    - The docs say plainly that games started outside Steam are not detected.
17. **Steam Cloud, restated.**
    - `userdata_roots` is required: an empty sequence → `SafetyError("no_userdata")`.
    - Every account folder is checked.
    - If the target's base name appears as the last path part of any key in
      `remotecache.vdf`, that is a match.
    - Either `cloud_synced` or `cloud_unknown` (unreadable or unparsable file) requires
      `"cloud"` in `confirm`; the default is to ask.
    - A missing `remotecache.vdf` means "not synced".
    - The text tells Fede that Cloud may push the old file back.
18. **Backup root.** It must be absolute, existing and a folder, and it must not be
    inside any Steam library or Proton prefix the card names (`bad_backup_root`). The
    default is `Path.home()/deckforge/backups`, created with `mkdir(parents=True,
    exist_ok=True)` only under the home folder.
19. **Restore result:** `{"backup_id", "restored": [paths], "skipped": [paths],
    "new_backup_id": str | None}`. With `"overwrite"`, the current versions are first
    saved as a new backup, whose id is returned.
20. **Steam updates.** When restore finds a file changed since apply, the message says:
    "changed since DeckForge applied it (you, the game, or a Steam update/verify may have
    changed it)".
21. **Confirmed after the tests were written, 2026-10-22.** The test author's
    assumptions are adopted as spec:
    - `preview(changes, *, userdata_roots)` takes `userdata_roots` so that it can warn
      about cloud sync.
    - An unreadable cloud file in `apply` without `"cloud"` → `cloud_unknown`.
    - Every refusal in `apply` happens before any backup folder is created.
    - A changed file (`changed_since_apply`) without `"overwrite"` stops the whole restore,
      so nothing is restored. The message names the file and includes the answer-20
      sentence.
    - A settings file deleted after apply: restore → `file_missing`, with or without
      `"overwrite"`. It is never recreated.
    - CLI flags come after the command. After an overwrite, the CLI prints the new
      `backup_id`.
    - The CLI's `restore` reads the real `/proc`, read-only.
    - **Known limit:** edits to a manifest's `mode` or `path` fields can't be detected,
      because the manifest has no checksum of its own. Restore still re-checks Q1 path
      rules on disk (answer 3) before writing, so an edited path can't point outside the
      game's folders.
22. **Decided after the first CI run, 2026-10-23: the game-running check must work with
    hidden processes.**
    - **The problem.**
      - Processes that mark themselves non-dumpable (`prctl(PR_SET_DUMPABLE, 0)`) have an
        unreadable `environ` and `exe`, even for their own user. Reproduced in the
        sandbox: environ unreadable, cmdline readable.
      - Chromium-based helpers such as Steam's `steamwebhelper`, and agents like
        `ssh-agent`, do this. A real Deck almost certainly has some running.
      - Under answer 16, every apply would then be refused (`cannot_check_running`).
    - **New rule, replacing answer 16's handling of unreadable processes.** For every
      process owned by the current user:
      1. Read `cmdline`, which stays readable for non-dumpable processes. It is
         split on NUL.
      2. Mark the process "running the game" if any argument equals `AppId=<appid>`
         (Steam's launcher runs `reaper SteamLaunch AppId=<appid> -- …`), or if any
         argument is a path inside the card's `install_path`.
      3. Also read `environ` when readable, and match `SteamAppId=<appid>` /
         `STEAM_COMPAT_APP_ID=<appid>` as before.
      4. Handle unreadable fields:
         - An unreadable `environ` with a readable `cmdline` is **not** a refusal; the
           cmdline result decides.
         - Only a same-user process whose `cmdline` **and** `environ` are both
           unreadable gives `cannot_check_running`. Processes that vanish while being
           read (ENOENT/ESRCH) are skipped.
    - **Unchanged:** other users' processes are skipped, and `exe` is an extra signal
      only.
    - **To confirm on the Deck:** that the `reaper SteamLaunch AppId=` form appears
      while a game runs. The CLI's `restore` will report which signal matched.
