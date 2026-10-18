# Clean-slate search: research notes (2026-10-17/18)

These are the raw notes behind `docs/design/CLEAN_SLATE_NATIVE.md`. Each note is one agent's final report, saved verbatim, with three changes:
- two lines about session housekeeping were removed;
- one suggestion that crossed a project rule is struck through, and a second is narrowed, each with an inline note;
- headings named "Worth saving to memory" were renamed "Key facts to keep".

The briefs are in the `00_*` files. Agents were not shown each other's reasoning, only the briefs and the earlier rounds' notes.

## Round 1: seven specialists

Brief: `00_brief_round1.md`.

| File | Viewpoint |
|---|---|
| `round1/1_console_port.md` | Console-port graphics engineer |
| `round1/2_neural.md` | Neural rendering / ML systems |
| `round1/3_perception.md` | Perception and display science |
| `round1/4_systems.md` | Kernel, driver and compiler |
| `round1/5_power.md` | Hardware, power and thermal |
| `round1/6_precompute.md` | Offline precomputation |
| `round1/7_outsider.md` | Adjacent fields (emulation, codecs, economics) |

## Round 2: seven sceptics

Each sceptic broke the ideas, then tried to rescue them. The sceptics' brief is `00_brief_round2_sceptics.md`, and the ideas were clustered in `00_round2_clusters.md`.

| File | Scope |
|---|---|
| `round2/A_G_vrs_reprojection.md` | Forced VRS; camera reprojection |
| `round2/B_H_amortization_gi.md` | Pass amortization, Replay Lab, harvested GI |
| `round2/C_sched_power.md` | CPU scheduling and power |
| `round2/D_neural.md` | Neural reconstruction |
| `round2/E_F_search_autotune.md` | Perceptual settings search; driver and compiler autotuning |
| `round2/X_anticheat_legal_maint.md` | Anti-cheat, legal, maintenance, prior art (all clusters) |
| `round2/baselines_stack.md` | Measured Deck baselines and the stacked budget |

## Round 3: four specialists, each aimed at one wall Round 2 exposed

Brief: `00_brief_round3.md`.

| File | Wall |
|---|---|
| `round3/W1_perceived_high.md` | What "looks like High" means on this screen, and how to prove it |
| `round3/W2_W4_gpu_fixed_cost.md` | GPU work that doesn't shrink with resolution; reconstruction |
| `round3/W3_cpu_wall.md` | CPU-bound scenes |
| `round3/W5_ecosystem_upstream.md` | Upstream, publishers, the owner's own PC, hardware |

## Round 4: two fresh sceptics on the Round 3 ideas

| File | Scope |
|---|---|
| `round4/R4_gpu_perception.md` | Round 3 GPU and perception ideas |
| `round4/R4_cpu_ecosystem.md` | Round 3 CPU and ecosystem ideas |

## Verification of the design doc

| File | What it is |
|---|---|
| `verification/verifier_round1.md` | A fresh-context verifier's review of revision 1. Verdict: FAIL, with 13 findings. |
| `verification/verifier_round2.md` | A second fresh-context verifier's review of revision 2. Verdict: FAIL, with 11 new or remaining findings. Revision 3 addresses them; see the design doc's §2 table for the re-check result. |
| `verification/arith.py.txt`, `verification/lock30.py.txt` | The round-1 verifier's scripts. They check revision 1's numbers. |
| `verification/arith2.py.txt`, `verification/newfindings.py.txt` | The round-2 verifier's scripts. They check revision 2's numbers, which revision 3 keeps. |

All four scripts are renamed `.py.txt` so the linter skips them.

## Reading the numbers

- Figures marked "(est.)" are estimates.
- Figures with a link are measurements by others.
- **No High-preset measurement near 800p exists for any of the five target games.**
- Nothing in these notes was measured on a Deck by this project.
