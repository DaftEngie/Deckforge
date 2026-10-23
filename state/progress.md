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
