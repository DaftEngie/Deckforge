# Strategy options: is DeckForge's approach the right one?

Status: **PROPOSED**, 2026-10-11. Decisions D1–D8 below are Fede's to make. Until he
does, `CLAUDE.md` and `docs/QUALITY_TARGET.md` stay as they are.
Evidence: [the overnight report](../research/2026-10-11-overnight/REPORT.md) and its seven
source notes. How the tool would work end to end: [LAUNCH_FLOW.md](LAUNCH_FLOW.md).

## Short answer

**Partly.** The core idea holds; three bets do not.

**What holds:** a tool that measures the game on your own Deck, tries settings, scores
smoothness *and* image quality, applies changes reversibly, and re-checks after
updates. The research found no tool that does this today: not from NVIDIA, AMD or Valve,
nor in the Deck community [prior art §5]. A targeted GitHub search and a check of
Handheld Daemon and Handheld Companion are still open.

**What does not hold:**

1. **"Locked 45 fps native" in the test games.** The best reports put Wilds at about
   30 fps on the Deck after its January 2026 patch, and Space Marine 2 at 20–30 fps
   (author-tested, no data published). No *measured* source shows either near 45, even
   with mods.
2. **"60 with frame generation is ideal"** (your stated ideal when we set the target; the
   written plan already keeps frame generation as a separate track).
   Near a 45 fps base, frame generation adds roughly 40–75 ms of input delay compared
   with native play using latency reduction, and at least 22 ms even in the best
   comparison. The Deck's whole measured button-to-screen time is 51–65 ms on the OLED.
   Frame generation cannot meet your "no added latency" goal.
3. **Shader rewriting as a core feature.** The hooks are debug-only, there are no
   published gains on the Deck's driver, and every game or Proton update breaks the
   work. Realistic "shader optimization" on the Deck means stutter control and variable
   rate shading.

**What the evidence points to instead:**

- **Latency** is the lever most under the user's control. The frame limiter you choose
  may add 44–87 ms (a 2022 measurement that has never been redone).
- **FSR 4** is the biggest image-quality lever: about 4.5 ms per frame at 800p by one
  user's measurement, possibly around 6 ms. It is only worth it in GPU-bound games.
- **Cloud (GeForce NOW)** may be the better answer for PS5-era games like Wilds, if its
  latency from Mexico City holds up.

## The options compared

| # | Option | What you get | Cost and risk | Verdict |
|---|---|---|---|---|
| A | **Current plan** (locked 45 native in every test game; your stated ideal of 60 with frame gen) | Clear target | Unreachable in both test games; frame gen breaks the latency goal | **Revise** (D1, D2) |
| B | **Native-first optimizer with honest verdicts** | Best measured native lock per game (45@90 → 40@80 → 30@90), or a clear "BLOCKED, here's why" | Same engineering as A, more honest | **Recommended core** |
| C | **Latency-first:** measure and fix limiter and queue | Possibly the largest felt improvement, in every game including anti-cheat ones (Tier S) | A phone camera and an evening | **Do first, inside B** (E8) |
| D | **Reconstruction-first:** best upscaler + mip bias + sharpening per game | Biggest visual gain at 800p | FSR 4 needs injection (Tier I) in most games today; about 20–27% of the frame budget | **Main visual lever inside B** (E9) |
| E | **Cloud hybrid:** GeForce NOW for PS5-era games, plus a "route to cloud" verdict | High render settings at 60–90 fps, about double the battery life; anti-cheat stops being a Deck problem | US$9.99–19.99/month (Ultimate MXN 439/month in Mexico); 100 h cap; Helldivers 2 not listed; **end-to-end latency and stream quality from Mexico City unmeasured** | **Test with a US$7.99 day pass** (E11, D6) |
| F | **Local streaming from your own PC** | Best stream quality, any game | No host today; Steam Machine from US$1,049, used PC about US$600–900 (estimate) | **Not now** |
| G | **Deep tech:** Vulkan-layer per-pass budget changes, AI shader rewriting | Possibly gains settings can't reach | Months of work, debug-only hooks, update churn | **Research track**, gated on E1 and E7 data |
| H | **Hardware hacks:** overclock, RAM overclock, Windows on the Deck | Little: GPU OC is capped near 1600 MHz, RAM OC showed nothing, SteamOS often beats Windows | Brick and warranty risk; loses the Linux toolchain | **No.** LAVD and TDP become search knobs inside B; undervolting stays a manual BIOS step for you |

**Where Lossless Scaling fits:**
- On SteamOS it exists only as lsfg-vk frame generation. Its upscaler is not documented
  on Linux.
- It works as a labeled "motion smoothing" option with its latency cost shown, never as
  part of "native".
- It loads into the game as a Vulkan layer, so by DeckForge's own rules it is Tier I.
- Its CC BY-NC-ND licence means DeckForge can launch your installed copy but never
  bundle it.

## Recommended path

**B as the product, C first, D as the main visual lever, E as the escape hatch.**

1. **Measure latency before anything else (E8).** It needs only your phone, it decides
   how DeckForge locks frame rates, and nobody has published it for the current OLED.
2. **Build Phase 1 around a safe, reversible core:** read-only discovery, the safety
   module, and the `df-run` launcher.
3. **Add one "winnable" test game (D5)** alongside Wilds, so the loop can show a real
   win. Wilds and Space Marine 2 become the "BLOCKED, with evidence" test cases.
4. **Measure FSR 4 on your Deck (E9), then try the GeForce NOW day pass (E11).** Use the
   same camera and image-quality tests for both, so local and cloud are compared fairly.
5. **Keep shader rewriting and the Vulkan layer as research** until E1 (a GPU profile of
   Wilds) shows a single pass worth attacking.

## Techniques nobody has published for the Deck (candidate wins)

1. **Measured latency for every way to lock 45 fps** on a current OLED: Steam cap vs
   in-game cap vs MangoHud, with and without `maxFrameLatency=1`.
2. **Moving power from CPU to GPU** (lower CPU boost; SMT off if root is approved) for
   GPU-bound games inside the shared 15 W budget. Plausible, unmeasured.
3. **Two-stage upscaling:** the game's temporal upscaler to an in-between size, then
   gamescope's near-free spatial filter to 800p. Untested anywhere on the Deck.
4. **Mip bias and sharpening tuned per game** against a temporal quality score, instead
   of AMD's desktop formula.
5. **The rc9 integer-optimized FSR 4 build on the Deck.** If its gains on similar AMD
   hardware carry over, FSR 4 would cost about 2.5 ms instead of about 4.5 ms.
6. **Scoring a cloud stream and a local configuration with the same latency and
   image-quality harness.** No public source has done it.
7. **An open data set of settings → frame time → image quality,** tagged by game build
   and versions. Valve's new frame-rate data records at most a coarse setting level and
   render resolution, never individual settings or image quality.

## Experiments backlog (continues the compendium's E1–E7)

| ID | Experiment | Needs | Decides |
|---|---|---|---|
| **E8** | Latency of each way to cap at 45 (Steam per-game cap, in-game cap, MangoHud, uncapped) and of `maxFrameLatency=1`. 240 fps phone camera, 10–20 presses each | Phone slow-motion at 240 fps, a stand, an evening | Default limiter policy |
| **E9** | Real FSR 4 INT8 cost on the Deck at 800p vs FSR 3.1, in the **Wilds Benchmark app or offline mode only**, via Decky Framegen or OptiScaler. If it needs a different Proton, first check whether the game uses Denuvo (a lockout was reported after Proton changes) | Tier I opt-in (D7) | Whether FSR 4 fits the 45/40/30 budgets; settles the 4.5 vs ~6 ms question |
| E10 | rc9 integer-optimized FSR 4 build on the Deck | Only if E9 shows ≥4 ms | Whether FSR 4 gets cheap enough for Quality-mode inputs |
| **E11** | GeForce NOW day pass from home in Mexico City: built-in network test, the E8 camera test, image check in Wilds and Space Marine 2 | US$7.99 (D6) | The "route to cloud" verdict |
| E12 | Power: CPU boost limit in a GPU-bound scene; LAVD vs default scheduler in a CPU-heavy Wilds scene | `steamosctl` (E16) | Whether power-shifting is a real lever |
| E13 | Two-stage scaling vs single-stage | A game with an in-game upscaler | Whether to add it to the search |
| E14 | `dxvk.numCompilerThreads` cap vs default: hitch count on a cold run | A DirectX 11 game (Wilds is believed to be DirectX 12) | Stutter lever for DirectX 11 titles |
| E15 | Does Wilds' `config.ini` survive a Steam verify and a game update? Does Steam Cloud sync it? | A test copy of the file | Safety rules for install-folder settings (D3) |
| E16 | Does `steamosctl` work as the `deck` user without a password? Does Steam's per-game profile override it at launch? | Deck, Desktop Mode | Whether DeckForge can set TDP, boost and scheduler itself or only recommend them |
| E17 | Can Steam's performance overlay (mangoapp) log per-frame times without loading anything into the game? | Deck, any game | Whether anti-cheat games can be measured without an in-process layer (D8) |

## Decisions for Fede

| # | Decision | Recommendation | Why |
|---|---|---|---|
| D1 | Replace "locked 45 everywhere" with a per-game ladder: 45@90 → 40@80 → 30@90, then BLOCKED or route to cloud. **And set the floor:** is 30@90 acceptable, or should anything under 40 suggest the cloud? | **Yes to the ladder; the floor is your call** | All three rungs pace evenly on the OLED. The floor decides whether Wilds (~30 fps) gets "30@90" or "try cloud" |
| D2 | Frame generation only as opt-in "motion smoothing", with its measured latency shown; never the default, never "native" | **Yes** | Adds roughly 40–75 ms near a 45 base (at least 22 ms in the best case) |
| D3 | Split Tier S: files in the Proton prefix = Tier S; files in the install folder (like Wilds' `config.ini`) = Tier I unless proven safe for that game. Let DeckForge edit Wilds' `config.ini` as a Tier I opt-in, with drift detection | **Yes** | Otherwise DeckForge cannot touch Wilds' settings file at all under safety-spec Q1 |
| D4 | One launch option per game, pasted once (`~/deckforge/bin/df-run %command%`). After that DeckForge changes only its own files, never Steam's `localconfig.vdf`. This needs one lint exception for the launcher module (ruff S606, for starting the game without a shell) in `pyproject.toml`, which only you can approve | **Yes** | The pattern Decky Framegen and lsfg-vk already use; it also answers safety-spec Q2 |
| D5 | Add a "winnable" test game: one you own that runs at about 35–40 fps on the Deck untuned, ideally without online anti-cheat | **Pick one** | The loop needs a game where a real win is possible |
| D6 | Spend US$7.99 on a GeForce NOW Ultimate day pass for E11 | **Your call** (recommended) | The cheapest way to settle the cloud question |
| D7 | Allow the Tier I FSR 4 test on Wilds (E9), **in the Benchmark app or offline mode only**, never while connected online | **Yes, as an experiment only** | OptiScaler's own README warns against online use; playing solo while connected still counts as online |
| D8 | May MangoHud (an in-process layer) run on anti-cheat games for measurement? | **No, until E17 shows an outside-the-game alternative or you accept the risk** | No ban was found, but "not found" is not proof of safety |

Still open from the safety spec: Q1–Q7. D3 and D4 change the recommended answers to Q1
and Q2.
