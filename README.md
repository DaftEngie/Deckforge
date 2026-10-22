# DeckForge

An open-source (MIT) tool that makes demanding PC games look and run better on the
Steam Deck in handheld mode.

**Goal:** a steady, good-looking picture on the Deck's own 7-inch screen. The gold
standard is a locked 35 fps at 70 Hz. Steady 30-35 fps with 1% lows of at least 28
is good enough. Frame generation is allowed, and real (native) fps is always
reported separately (docs/decisions/0002-experience-target.md).

**How:** DeckForge measures where each game spends its frame time, then searches
safely through settings, upscalers and system knobs to find the best-looking setup
that holds the frame budget. Every change it makes is previewed, backed up, and
reversible with one tap.

**Status:** Phase 0 — project setup. Nothing here modifies a game yet.

| Phase | What | Status |
|---|---|---|
| 0 | Guardrails, CI, Deck bench setup, first measurements | in progress |
| 1 | Apply/restore tested profiles (preview, backup, restore) | planned |
| 2 | Diagnose: where does the frame time go? | planned |
| 3 | Search: automated overnight experiments on the Deck | planned |
| 4 | Per-pass Vulkan layer | later |

Test games: Monster Hunter Wilds (full stack), Warhammer 40,000: Space Marine 2
(safe tier only, Easy Anti-Cheat).

See `docs/` for architecture, quality target and enforcement rules.
