# Spec: `deckforge.safety` — preview, backup, apply, restore

Status: DRAFT — waiting for Fede's answers to the clarifier questions.
Milestone 1 (apply/restore tested profiles) depends on this module. Every later write
DeckForge makes to a user's Deck goes through it (CLAUDE.md R10).

## Goal (one sentence, user-visible)
Before DeckForge changes any game file, it shows exactly what will change, saves a
backup, and can put every file back byte-for-byte with one command.

## Acceptance criteria
- AC1 Preview: Given a planned change set (file → new content), when preview runs, then it
  lists each file with before/after differences and writes nothing (directory tree hash
  unchanged).
- AC2 Backup before write: Given a change set, when apply runs, then every original file
  is copied into a DeckForge-owned backup folder with a manifest (path, size, SHA-256,
  timestamp, DeckForge version) before the first write happens.
- AC3 Atomic write: Given apply is interrupted mid-write, then each target file is either
  fully old or fully new, never partial (write to temp file in the same folder, then rename).
- AC4 Allowlist: Given a target path outside the allowed roots, or a path that is empty,
  relative, contains "..", or resolves through a symlink to outside the allowed roots,
  then apply refuses before touching anything.
- AC5 Restore: Given a completed apply, when restore runs, then every file is
  byte-identical to the original (SHA-256 match), and files that did not exist before
  are removed only if DeckForge created them.
- AC6 Round trip: For any change set over the fixture tree, apply then restore gives a
  tree hash identical to the starting hash.
- AC7 Steam running: Given Steam is running, when apply targets Steam-managed files
  (e.g. localconfig.vdf for launch options), then it refuses with a clear message.
  (Game config files such as config.ini are not Steam-managed.)
- AC8 No silent failure: Given any error (disk full, read-only file, permission denied),
  apply stops, restores anything already changed, and reports what happened.

## Out of scope
UI/Decky plugin, deciding what to change (that's profiles/search), anti-cheat detection,
the Vulkan layer.

## Files and interfaces involved
- `src/deckforge/safety/` (new package): `plan`, `preview`, `apply`, `restore`.
- `tests/fixtures/steam_tree/` (new): a fake Steam/Proton directory tree.
- No dependencies beyond the Python standard library.

## Safety
- Reads/writes only inside allowed roots (to confirm in Q1). Backups live in
  `~/deckforge/backups/` — never inside a folder DeckForge edits.
- Undo: `restore <backup-id>` (and "restore everything" later in the UI).
- Unusual setups to handle or refuse: SD-card library, non-default library path, Flatpak
  Steam, missing config file, Steam running, read-only file, full disk, symlinks.

## End-to-end check Fede will run on the Deck
Apply a harmless test change to a copy of a game config, look at the preview, apply,
confirm the change in a text editor, run restore, and confirm the file matches the
original (the tool prints matching SHA-256 values).

## Clarifier questions and answers
Clarifier review 2026-10-09. Answers pending from Fede; recommended defaults shown.

| # | Question | Recommended default | Answer |
|---|---|---|---|
| Q1 | Which folders may DeckForge ever write to? | Only each game's settings folder inside its Proton prefix (`steamapps/compatdata/<id>/pfx/...`, internal or SD card, roots taken from Steam's library list). Never `steamapps/common` (game installs), never save files. | |
| Q2 | Steam is always running on a Deck, and it rewrites `localconfig.vdf` on exit. How to handle launch options? | Don't edit Steam's file in Milestone 1; print the launch-option text for Fede to paste into Properties. | |
| Q3 | If the game or Fede changed the file after apply, what does restore do? | Show the difference and stop; overwrite only on confirmation, after backing up the current version. | |
| Q4 | Refuse apply while the target game is running? | Yes. | |
| Q5 | Config file doesn't exist yet (game never launched)? | Refuse: "launch the game once, then retry". Never create it from scratch. | |
| Q6 | Config file is read-only (player locked it)? | Refuse and explain; never change permissions. | |
| Q7 | Settings file synced by Steam Cloud? | Detect and warn/refuse in Milestone 1. | |

### Additions to acceptance criteria if defaults are accepted
- AC3 also requires fsync before rename, cleanup of leftover temp files, and keeping
  permissions, symlinks, encoding, line endings and BOM unchanged.
- AC2/AC5: verify the backup's own SHA-256 after writing it and before restoring from it;
  refuse if the manifest is missing, edited or corrupted.
- New: a lock so only one DeckForge apply runs at a time.
- New: restore never deletes folders and never deletes recursively; it removes only exact
  files the manifest says DeckForge created, matched by hash.
- New: if rollback itself fails, keep the backup and print where the originals are.
- New fixtures: second library on SD card (and card missing at restore), Flatpak Steam
  (refuse), multiple Steam accounts, paths with spaces/non-English characters,
  binary/UTF-16/CRLF config files, read-only folder, full backup disk vs full SD card.
- Symlinks that resolve inside allowed roots (e.g. `~/.steam/steam`) must work.
