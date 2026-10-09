# DeckForge — agent map

DeckForge tunes demanding PC games for the Steam Deck **in handheld mode**.
Target: a locked 45 fps (22.2 ms frame time) with the best image quality that fits
in that budget. Frame generation (Lossless Scaling / lsfg-vk) is tracked separately
and never counts toward the native target. Owner: Fede (not a software engineer;
he reviews evidence and behavior, not code).

Read first, every session: `state/progress.md` (tail), the active spec in `docs/specs/`.
Background: `docs/ARCHITECTURE.md`, `docs/QUALITY_TARGET.md`.

## Commands
- Lint/format: `ruff check . && ruff format --check .`
- Tests: `python -m pytest -q`
- Tamper check (what CI runs): `python ci/tamper_check.py --base origin/main`

## Non-negotiables (how each is enforced: docs/ENFORCEMENT.md)
R1  BLOCKED or UNSURE with a reason is a good result. A wrong "done" is the worst result.
    Partial-and-labeled beats complete-and-wrong.
R2  Your statement that something works is not evidence. Done = CI is green. Link the run.
R3  In every PR, mark each acceptance criterion MET (test name), NOT MET or CHANGED.
    Name anything you simplified, skipped, or solved differently from the spec.
R4  If the spec is ambiguous, stop and list assumptions and questions before writing code.
R5  Never modify or delete existing files in tests/. Never edit evals/, bench/, ci/,
    .github/, .claude/, pyproject.toml. If a test looks wrong, report BLOCKED.
    You may ADD new test files.
R6  Never delete recursively except inside a directory you created this session with
    mktemp. Never put $HOME, ~, or an unchecked variable in a delete/move/overwrite target.
R7  Never touch a real Steam install or a real Deck from a dev session. Use
    tests/fixtures/. The Deck is driven only by the bench runner (later phase).
R8  Never add, install or upgrade a dependency. Propose it in the PR under
    "New dependencies" with the PyPI link and why the standard library can't do it.
R9  Never push to main, merge, or change labels, branch rules or repository settings.
R10 Every write to a user file goes through `deckforge.safety` (backup, atomic write,
    manifest, verify) once it exists. No direct writes outside the repo or fixtures.
R11 No shell=True, no string-built shell commands, no eval/exec, no unsafe YAML/pickle,
    no code downloaded at runtime.
R12 No catch-all exception handlers that hide errors. Log with context, then handle or re-raise.
R13 Search for an existing helper before writing a new one. No copy-pasted blocks.
R14 Before calling a library function not yet used in this repo, confirm it exists in the
    installed version; cite the doc URL or file:line in the PR.
R15 One behavior change per PR. Refactors in separate PRs. Keep diffs under ~400 lines.
R16 (Phase 3) Vulkan layer: clean under the Khronos validation layer, off by default,
    never loads for a game on the anti-cheat denylist.

## Safety tiers for games (product rule)
- Tier S (safe everywhere): in-game settings files, Steam launch options, TDP/fps cap,
  refresh rate, game-provided upscalers.
- Tier I (injection): OptiScaler, DLL swaps, REFramework, the DeckForge Vulkan layer.
  Only for games with no online anti-cheat, opt-in per game, never global.
- Games with kernel/online anti-cheat (e.g. Helldivers 2 = GameGuard,
  Space Marine 2 = Easy Anti-Cheat) get Tier S only.

## Roles
Defined in `.claude/agents/`. One implementer writes code; everyone else reads or
verifies. The verifier never sees the implementer's reasoning.
