# Progress log (append-only; newest at the bottom)

## 2026-10-08 — Phase 0 skeleton
- Repo skeleton created: CLAUDE.md, agents, hooks, CI, tamper check, docs.
- Decisions: handheld-first, 45 fps target, subscription-only budget (docs/decisions/0001).
- Next: Deck setup (deck/README.md), first Wilds MangoHud baseline, RGP capture (E1).

## 2026-10-11 — Overnight session (unattended): research rethink + Phase 1 read-only scanner
Reading taken: Fede asked for study + critical rethink + "start Phase 1 if you can" while asleep.
Phase 1 work limited to modules that only READ (safety module still waits on Q1-Q7).
- Research: 7 notes + report (docs/research/2026-10-11-overnight/). Verdict: 45 native not
  credible in Wilds (~30) or SM2 (20-30); frame gen at a 45 base adds ~40-75 ms (not native);
  shader rewriting = research track; biggest levers = limiter/queue latency (unmeasured since
  2022), FSR 4 INT8 (~4.5 ms, one user's figure), cloud (GFN) for PS5-era games.
- Design: docs/design/LAUNCH_FLOW.md, STRATEGY_OPTIONS.md (decisions D1-D8, experiments E8-E17).
  PR #2. Verifier: FAIL x2 -> all findings fixed.
- Phase 1 code (stacked PRs, all verified, CI green except dependency-review):
  #3 deckforge.vdf (parser) -> #4 deckforge.discover (libraries/manifests/prefixes) ->
  #5 deckforge.detect (engine/anti-cheat/upscalers/settings files, fail-closed Tier I).
  798 tests. Verifier caught: regex memory blow-up (vdf), silent folder errors (discover),
  four fail-open eligibility paths (detect). All fixed before PR.
- One test edited after commit with Fede's approval in chat (R5): relative link typo.
- Harness issues found (need Fede, .claude/ is protected):
  1. implementer `isolation: worktree` creates worktrees under .claude/worktrees/, which
     protect_paths.py denies -> implementers ran on the branch without worktrees.
  2. protect_paths.py blocks Write outside the repo, incl. the session scratchpad ->
     researchers could not save notes; test authors used .pytest_cache/ as scratch, and
     recursive delete there is blocked (leftover gitignored dirs).
  3. Stop hook runs the full suite, so test-first commits always "fail" until code lands.
  4. `ruff check .` skips extensionless scripts; keep Python logic in .py files.
- Waiting on Fede: decisions D1-D8 (STRATEGY_OPTIONS.md), safety Q1-Q7, spec items F1-F7
  (discover.md), GitHub settings (Dependency graph etc.), Deck check of the scanner.
