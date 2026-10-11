# Strategy options: is DeckForge's approach the right one?

Status: **PROPOSED**, 2026-10-11. Decisions D1–D7 below are Fede's to make. Until he
does, `CLAUDE.md` and `docs/QUALITY_TARGET.md` stay as they are.
Evidence: [the overnight report](../research/2026-10-11-overnight/REPORT.md) and its seven
source notes. How the tool would work end to end: [LAUNCH_FLOW.md](LAUNCH_FLOW.md).

## Short answer

**Partly.** The core idea holds, and three bets do not.

**What holds:** a tool that measures the game on your own Deck, tries settings, scores
smoothness *and* image quality, applies changes reversibly, and re-checks after updates.
Nobody does this today: not NVIDIA, AMD, Valve or the Deck community [prior art §5].

**What does not hold:**

1. **"Locked 45 fps native" in the test games.** The best evidence puts Wilds at about
   30 fps on the Deck after its 2026 patches, and Space Marine 2 at 20–30 fps. No source
   shows either near 45, even with mods.
2. **"60/90 fps with frame generation" as the ideal.** Frame generation from a 45 fps base
   adds an estimated 22–65 ms of input delay. That is close to the Deck's whole measured
   button-to-screen time (51–65 ms on the OLED). It cannot meet your "no added latency"
   goal by construction.
3. **Shader rewriting as a core feature.** The hooks are debug-only, there are no
   published gains on the Deck's driver, and every game or Proton update breaks the
   work. Realistic "shader optimization" on the Deck means stutter control and variable
   rate shading.

**What the evidence points to instead:**

- **Latency** is the lever most under the user's control. The frame limiter you pick
  may add 44–87 ms (2022 measurement, never redone).
- **FSR 4** is the biggest image-quality lever: about 4.5 ms per frame at 800p, and only
  worth it in GPU-bound games.
- **Cloud (GeForce NOW)** may simply be the better answer for PS5-era games like Wilds.

## The options compared

| # | Option | What you get | Cost and risk | Verdict |
|---|---|---|---|---|
| A | **Current plan as written** (45 native everywhere, frame gen to 90 as the ideal) | Clear target | Unreachable in both test games; frame gen breaks the latency goal | **Revise** (D1, D2) |
| B | **Native-first optimizer with honest verdicts** | Best measured native lock per game (45@90 → 40@80 → 30@90) or a clear "BLOCKED, here's why" | Same engineering as A, but more honest | **Recommended core** |
| C | **Latency-first:** measure and fix limiter and queue | Possibly the largest felt improvement, in every game including anti-cheat ones (Tier S) | A phone camera and an evening | **Do first, inside B** (E8) |
| D | **Reconstruction-first:** best upscaler + mip bias + sharpening per game | Biggest visual gain at 800p | FSR 4 needs injection (Tier I) in most games today; about 20% of the frame budget | **Main visual lever inside B** (E9) |
| E | **Cloud hybrid:** GeForce NOW for PS5-era games, plus a "route to cloud" verdict | High settings at 60–90 fps, about double the battery life, anti-cheat stops mattering | US$9.99–19.99 a month (Ultimate is MXN 439 in Mexico); 100 h cap; no Helldivers 2; **latency from Mexico City unknown** | **Test with a US$7.99 day pass** (E11, D6) |
| F | **Local streaming from your own PC** | Best stream quality, any game | No host today; Steam Machine from US$1,049, used PC about US$600–900 (estimate) | **Not now** |
| G | **Deep tech:** Vulkan-layer per-pass budget changes, AI shader rewriting | Possibly gains settings can't reach | Months of work, debug-only hooks, update churn | **Research track**, gated on E1 and E7 data |
| H | **Hardware hacks:** overclock, RAM overclock, Windows on the Deck | Little: GPU OC is capped near 1600 MHz, RAM OC showed nothing, SteamOS often beats Windows | Brick and warranty risk; loses the Linux toolchain | **No.** Undervolt, LAVD and TDP become search knobs inside B |

**Where Lossless Scaling fits.** On SteamOS it exists only as lsfg-vk frame generation;
its upscaler is not documented on Linux. It works as a labeled "motion smoothing" option
with its latency cost shown, never as part of "native". It loads into the game as a
Vulkan layer, so by DeckForge's own rules it is Tier I. Its CC BY-NC-ND licence means
DeckForge can launch your installed copy but never bundle it.

## Recommended path

**B as the product, C first, D as the main visual lever, E as the escape hatch.**

1. **Measure latency before anything else (E8).** It needs only your phone. The result
   decides how DeckForge locks frame rates, and nobody has published it for the current
   OLED.
2. **Build Phase 1 around a safe, reversible core:** read-only discovery, the safety
   module, and the `df-run` launcher.
3. **Add one "winnable" test game (D5)** alongside Wilds, so the loop can show a real
   win. Wilds and Space Marine 2 become the "BLOCKED, with evidence" test cases.
4. **Measure FSR 4 on your Deck (E9), then test the GeForce NOW day pass (E11).** Run both
   with the same camera and image-quality tests, so local and cloud are compared fairly.
5. **Keep shader rewriting and the Vulkan layer as research,** until E1 (a GPU profile of
   Wilds) shows a single pass worth attacking.

## Techniques nobody has published for the Deck (candidate wins)

1. **Measured latency for every way to lock 45 fps** (Steam cap vs in-game cap vs
   MangoHud, with and without `maxFrameLatency=1`) on a current OLED.
2. **Moving power from CPU to GPU** (SMT off, lower CPU boost) for GPU-bound games inside
   the shared 15 W budget. Plausible, unmeasured.
3. **Two-stage upscaling:** the game's temporal upscaler to an in-between size, then
   gamescope's near-free spatial filter to 800p. Untested anywhere on the Deck.
4. **Mip bias and sharpening tuned per game against a temporal quality score,** instead
   of AMD's desktop formula.
5. **The rc9 integer-optimized FSR 4 build on the Deck.** If its gains on similar AMD
   hardware carry over, FSR 4 would cost about 2.5 ms instead of about 4.5 ms.
6. **Scoring a cloud stream and a local configuration with the same latency and
   image-quality harness.** No public source has done it.
7. **An open data set of settings → frame-time → image-quality results,** tagged by game
   build and versions. Valve's new frame-rate data does not record settings.

## Experiments backlog (continues the compendium's E1–E7)

| ID | Experiment | Needs | Decides |
|---|---|---|---|
| **E8** | Latency of each way to cap at 45 (Steam per-game cap, in-game cap, MangoHud, uncapped) and `maxFrameLatency=1`, measured by a 240 fps phone camera with 10–20 presses each | Phone slow-motion at 240 fps, a stand, an evening | Default limiter policy |
| **E9** | FSR 4 INT8 real cost on the Deck at 800p vs FSR 3.1 (Wilds, via Decky Framegen or OptiScaler) | Tier I opt-in (D7); play offline or solo | Whether FSR 4 fits 45/40/30 budgets; settles the 4.5 vs 6–11 ms conflict |
| E10 | rc9 integer-optimized FSR 4 build on the Deck | Only if E9 shows ≥4 ms | Whether FSR 4 becomes cheap enough for Quality-mode inputs |
| **E11** | GeForce NOW day pass from home in Mexico City: built-in network test, E8 camera test, image check in Wilds and Space Marine 2 | US$7.99 (D6) | The "route to cloud" verdict |
| E12 | Power: SMT off / CPU boost limit in a GPU-bound scene; LAVD vs default scheduler in a CPU-heavy Wilds scene | Root for SMT (see E16) | Whether power-shifting is a real lever |
| E13 | Two-stage scaling vs single-stage | A game with an in-game upscaler | Whether to add it to the search |
| E14 | `dxvk.numCompilerThreads` cap vs default: hitch count on a cold run | A DirectX 11 game (Wilds is DirectX 12) | Stutter lever for DirectX 11 titles |
| E15 | Does Wilds' `config.ini` survive a Steam verify and a game update? Does Steam Cloud sync it? | A test copy of the file | Safety rules for install-folder settings (D3) |
| E16 | Does `steamosctl` work as the `deck` user without a password? Does Steam's per-game profile override it at launch? | Deck, Desktop Mode | Whether DeckForge can set TDP and scheduler itself or only recommend |

## Decisions for Fede

| # | Decision | Recommendation | Why |
|---|---|---|---|
| D1 | Replace "locked 45 everywhere" with a per-game ladder: 45@90 → 40@80 → 30@90, then BLOCKED / route to cloud | **Yes** | All three lock evenly on the OLED; 45 stays the first goal; nothing in the evidence gets Wilds to 45 |
| D2 | Frame generation only as opt-in "motion smoothing", with its measured latency shown; never the default, never "native" | **Yes** | Adds an estimated 22–65 ms at a 45 base |
| D3 | Split Tier S: files in the Proton prefix = Tier S; files in the install folder (like Wilds' `config.ini`) = Tier I unless proven safe for that game. Let DeckForge edit Wilds' `config.ini` as a Tier I opt-in, with drift detection | **Yes** | Otherwise DeckForge cannot touch Wilds' settings file at all under safety-spec Q1 |
| D4 | One launch option per game, pasted once (`~/deckforge/bin/df-run %command%`); after that DeckForge changes only its own files, never Steam's `localconfig.vdf` | **Yes** | The pattern Decky Framegen and lsfg-vk already use; also answers safety-spec Q2 |
| D5 | Add a "winnable" test game: one you own that runs at about 30–40 fps on the Deck untuned, ideally without online anti-cheat | **Pick one** | The loop needs a game where a real win is possible |
| D6 | Spend US$7.99 on a GeForce NOW Ultimate day pass for E11 | **Your call** (recommended) | Cheapest way to settle the cloud question |
| D7 | Allow the Tier I FSR 4 test on Wilds (E9), played offline or solo | **Yes, as an experiment only** | OptiScaler's own README warns against online use |

Still open from the safety spec: Q1–Q7. D3 and D4 above change the recommended answers
to Q1 and Q2.
