# Architecture

## Two machines
- **Mac (development):** Claude Code, the repo, analysis. Agents run here only.
- **Steam Deck (bench):** a small deterministic runner (later phase) pulls
  schema-checked trial specs, runs them with nothing else active, and returns raw
  logs plus environment metadata. No agent or LLM runs on the Deck during measurement.

## Layers (planned)
| Package | Purpose | Phase |
|---|---|---|
| `deckforge.safety` | Preview, backup + manifest, atomic writes, allowlisted paths, verified restore | 1 |
| `deckforge.profiles` | Apply/restore per-game profiles (config.ini, launch options, upscaler) | 1 |
| `deckforge.diagnose` | Parse MangoHud CSVs and RGP captures; CPU/GPU/bandwidth-bound verdict | 2 |
| `bench/` (protected) | Deck runner, measurement protocol, statistics | 2-3 |
| `deckforge.search` | Optuna search scored by frame time + image quality | 3 |
| `layer/` (C++, vkroots) | Per-pass timing, then interventions | 4 |

## Measurement rules (summary)
Warm-up run discarded, 60 s captures, interleaved A/B ordering, >=10 runs per arm
for confirmation, Mann-Whitney / bootstrap CI, minimum effect size, held-out scene,
weekly A/A self-test. Full protocol: project doc "Harness engineering for agent teams".

## Out of scope for now
Docked/TV mode, Windows, online anti-cheat games beyond Tier S.
