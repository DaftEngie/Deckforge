# Rule enforcement map

Prose rules are advisory; these mechanisms are what actually enforce them. When a
rule is broken twice, the fix is a new mechanism (hook, lint rule, CI check), not
another sentence in CLAUDE.md.

| Rule | Local (Claude Code) | CI (GitHub, required) |
|---|---|---|
| R2 done = green CI | Stop hook runs tests, blocks finishing on failure (max 2 blocks) | `tests` job |
| R5 protected paths | settings.json deny rules; `protect_paths.py` hook (existing tests/ files read-only, new test files allowed); sandbox denyWrite | `tamper` job: deleted/modified tests, test-count drop, new skip/suppression markers |
| R6 destructive commands | `protect_paths.py` blocks recursive rm outside /tmp, $HOME/~ in rm/mv | — |
| R8 dependencies | hook blocks pip/uv/poetry/npm installs; pyproject.toml protected | `dependency-review` job |
| R9 no merges/settings | hook blocks `git push` to main, `gh pr merge` | branch protection, no bypass |
| R11-R12 security/hidden errors | PostToolUse runs ruff on edited files | `lint` (ruff incl. bandit "S" and blind-except rules), CodeQL default setup |
| Secrets | — | `gitleaks` job; GitHub secret scanning + push protection |
| Gate health | — | `gate-selftest` (every PR + weekly): known-bad commits built in a throwaway clone must be rejected by the tamper check, and a clean commit must pass |

Overrides: a PR that legitimately changes existing tests needs the label
`test-change-approved`, which only Fede applies.
