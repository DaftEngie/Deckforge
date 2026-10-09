# DeckForge

An open-source (MIT) tool that makes demanding PC games look and run better on the
Steam Deck in handheld mode.

**Goal:** a locked 45 fps with image quality as close as possible to a console
"performance mode", on the Deck's own 7-inch screen. On the OLED model, optional
2x frame generation (Lossless Scaling) can present 90 fps on top of that.

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
