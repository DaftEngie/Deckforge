# Progress log (append-only; newest at the bottom)

## 2026-10-08 — Phase 0 skeleton
- Repo skeleton created: CLAUDE.md, agents, hooks, CI, tamper check, docs.
- Decisions: handheld-first, 45 fps target, subscription-only budget (docs/decisions/0001).
- Next: Deck setup (deck/README.md), first Wilds MangoHud baseline, RGP capture (E1).

## 2026-10-22 — settings-read implementation (BLOCKED on one test)
- deckforge.settings + 3 maps implemented; 1523 tests pass, ruff clean, tamper check OK.
- BLOCKED: tests/test_settings_report.py::test_s5_report_names_the_card fails with
  TypeError before any settings code runs: it calls one_file(..., GUS, name="REMATCH"),
  but one_file's 4th positional parameter is also called `name` (the file name), so
  Python gets two values for `name`. Test bug; R5 forbids editing it. Fix for the test
  author: rename one_file's parameter (e.g. file_name) or pass the card name another way.

## 2026-10-23 — safety implementation (BLOCKED on one test; 5 more fail only as root here)
- deckforge.safety implemented (plan, preview, apply, restore, list_backups, CLI). ruff
  clean, tamper check OK. Locally 1785 pass, 6 fail.
- BLOCKED: tests/test_safety_guards.py::test_a14_backup_room_one_byte_short_of_the_originals_is_no_space
  fails on its own line 443, before any safety code runs: it asserts
  len(CONFIG_INI)+len(GUS_INI) != len(CONFIG_NEW)+len(GUS_NEW), but both are 126 bytes.
  Test bug; R5 forbids editing it. Fix for the test author: pick fixture bytes whose sums
  differ, or drop that line. The behavior it targets was checked by hand (needed-1 bytes
  free -> no_space, exactly needed -> accepted, original sizes used).
- UNSURE (environment): 5 tests in test_safety_cli.py that restore through the real /proc
  return cannot_check_running here, because this sandbox runs tests as root and its pid 1
  (process_api) has an environ that even root cannot read. A16 says an unreadable process
  of the current user fails closed, so this is the specified behavior. Run as a non-root
  user (like CI and the Deck), all 234 safety tests but the one above pass. CI run decides.

## 2026-10-23 — safety spec item 22 (cmdline-based running check)
- _check_running now reads each process's cmdline (AppId=<appid> argument, or an absolute
  path inside install_path, compared as written and after realpath) before environ.
  Only both-unreadable same-user processes give cannot_check_running; ENOENT/ESRCH skip.
- 1830 tests pass locally (as root), ruff clean. The earlier root-only /proc failures are
  gone: pid 1's cmdline is readable here.
- Decided (spec silent): a readable cmdline/environ of another user's process still counts
  (as environ already did); the cmdline-path signal also runs in restore, using the
  manifest's install_path (like the exe signal).

## 2026-10-23 — safety spec item 23 (Ctrl-C, non-ini restore records, group kept)
- Ctrl-C in apply: own temp file removed, answer-7 rollback, SafetyError("interrupted")
  naming the backup folder and the files rolled back; lock freed. Ctrl-C while the backup
  is built -> interrupted, nothing changed. Ctrl-C in restore: stops, files whole,
  message names files already restored and every backup kept (incl. a new overwrite one).
- Restore refuses any manifest record whose base name is not *.ini (any case), is
  user/system/userdef.reg, or whose path ends in .vdf (not_a_settings_file), before any write.
- Manifest records gid; temp files get it via os.fchown(fd, -1, gid) before fchmod and
  rename; EPERM -> write proceeds, WARNING log "group_not_kept: <path> ...".
- Decided (spec silent): a record without gid (made before A23) is accepted and its
  group is left as the temp file gets it.
- 1866 tests pass locally (as root), ruff clean, tamper check OK.

## 2026-10-23 — safety spec item 24 (double Ctrl-C, final-step Ctrl-C, gid range)
- A Ctrl-C during rollback is a failed rollback for that file (not retried): apply raises
  rollback_failed naming the backup folder, the files that still hold the new content,
  and that the old (original) content is in that folder. A file found back to its
  original after the interrupt (e.g. Ctrl-C at the folder fsync) counts as rolled back.
- The lock is released explicitly (flock LOCK_UN, then os.close); a Ctrl-C there is logged
  as a warning and not re-raised, so apply/restore/CLI restore return their result.
- A manifest gid must be an int (not bool) with 0 <= gid < 2**32 - 1, else backup_corrupt
  before any write. A record without gid (pre-A23) is still accepted, as decided in A23.
- 1903 tests pass locally (as root), ruff clean, tamper check OK.
