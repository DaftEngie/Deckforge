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
