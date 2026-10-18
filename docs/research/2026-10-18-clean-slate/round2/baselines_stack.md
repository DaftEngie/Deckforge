# DeckForge Round 2: measured baselines and the honest stacked budget

**How numbers are labelled.** A number with a link is measured. Everything marked "est." is my estimate. I found no measured High-preset run near 800p on any Deck for any of the five games. Every "High-like" figure below is therefore an estimate: measured Deck Low/Medium points multiplied by measured PC preset-scaling ratios.

## Bottom line

- **Central stack** (all applicable clusters, no frame generation, est.):
  - Wukong ~29 fps
  - Stalker 2 ~30 in the wilderness, ~28 in settlements
  - Wilds ~21
  - Space Marine 2 ~25 average, ~15 in hordes
  - Alan Wake 2 ~17
- **≥30 fps with good 1% lows, natively:** plausible only for Wukong and Stalker 2 in the wilderness, and only if the stack lands above central.
- **45 fps:** no game at central. Only Wukong gets there, and only if every idea delivers its claim.
- **What carries the gain:** D1, B and E deliver about 80% of the savings wherever they apply. A and F are worth 1–2 ms each. C only matters in CPU-bound scenes: Space Marine 2 hordes, Stalker 2 settlements, Wilds plains.

---

## 1. Measured baselines

| Game | Device | Settings | Frame gen | fps | Source |
|---|---|---|---|---|---|
| Wilds | LCD | Benchmark tool, all Lowest, FSR Ultra Perf | off | **27.1 avg**; grass ~14 | [Steam thread](https://steamcommunity.com/app/2246340/discussions/0/597391898829653004) |
| Wilds | OLED | Benchmark tool, Lowest + tweaks, 800p, 60 cap | **on** | 41.7 avg (not native) | same |
| Wilds | LCD | Lowest, no upscaler / FSR Ultra Perf | off | ~20, dips ≤10 / "constantly under 30" | [GOL Feb 2025](https://gamingonlinux.com/2025/02/monster-hunter-wilds-looks-unplayable-on-steam-deck-but-good-on-desktop-linux) |
| Wilds | Deck (model not stated) | Lowest, Title Update 1.040 | n/a | Windward Plains <20, Scarlet Forest mid-20s, Oilwell ~30 | [SDHQ](https://steamdeckhq.com/news/monster-hunter-wilds-1040-performance/) |
| Wilds | Deck | Lowest, 9-minute Scarlet Forest hunt | n/a | avg >30; 1% lows "much lower" | [SDHQ 8 Jul 2026](https://steamdeckhq.com/monster-hunter-wilds-is-technically-playable/) |
| Wilds | Deck | Default (Verified) settings | n/a | "30 and above most of the time" | [SDHQ 21 Aug 2026](https://steamdeckhq.com/news/monster-hunter-wilds-gets-steam-deck-verified/) |
| Wukong | **OLED** | Benchmark tool, Low, FSR 70 / Low, FSR 50 / Medium, FSR 50 | off | **42/38**, **51/46**, **32/28** (avg / 5th-percentile low) | [Steam thread](https://steamcommunity.com/app/2358720/discussions/0/6149188575101206698) |
| Wukong | OLED | Gameplay, Low, TSR 45% | off | 40–50 early game, ~22 W system draw | [TouchArcade](https://toucharcade.com/2024/08/16/black-myth-wukong-steam-deck-review-settings-pc-port-options/) |
| Alan Wake 2 | Deck (Windows) | Lowest, FSR Performance | off | 19–45; "tanks" in combat | [Notebookcheck 2023](https://www.notebookcheck.net/Alan-Wake-2-works-on-the-Steam-Deck-but-only-with-user-assistance.763177.0.html) |
| Alan Wake 2 | Deck (SteamOS 3.5.1) | Lowest | off | "regularly below 30" | [SDHQ 2023](https://steamdeckhq.com/tips-and-guides/alan-wake-2-on-steam-deck/) |
| Space Marine 2 | Deck, 21–24 W system | Low, FSR2 Ultra Perf, 24 cap | off | ~24; 19 on explosions; **14 in hordes**; **forced 640×400 still <30** | [SDHQ](https://steamdeckhq.com/game-reviews/warhammer-40000-space-marine-2/) |
| Stalker 2 (v1.x) | **OLED** | Lowest native / Low + FSR Ultra Perf | off | **~15 / 23** | [GOL](https://www.gamingonlinux.com/2024/11/stalker-2-heart-of-chornobyl-review-works-on-linux-desktop-with-proton-but-poorly-on-steam-deck/page=1/) |
| Stalker 2 (v2.0) | Deck | "Aggressive FSR" | ? | "~30 avg" | [TweakTown, citing RPS](https://www.tweaktown.com/news/113170/stalker-2-receives-massive-performance-boost-with-new-2-0-update-game-gets-upgraded-to-unreal-engine-5-5-4/index.html). Second-hand; I could not find the original, so treat as **unverified** |

No source gave TDP; all ran at stock 15 W unless noted.

**PC preset-scaling ratios** (measured), used to estimate High:
- **Wilds** ([Notebookcheck](https://www.notebookcheck.net/Monster-Hunter-Wilds-Benchmark-Demanding-action-role-playing-game-hit-needs-a-dGPU.975933.0.html)):
  - RX 6600 XT, Low → High: 62.1 → 35.8 fps, so frame time ×1.73.
  - RTX 3060: ×1.61.
  - Radeon 680M, Low: 18.3 fps.
- **Stalker 2** ([Notebookcheck](https://www.notebookcheck.net/S-T-A-L-K-E-R-2-benchmark-test-Significant-potential-but-performance-challenges-remain.925699.0.html)):
  - RX 6600: Low/Medium/High = 56.8/48.6/40.6 fps, so ×1.40 from Low to High.
  - Radeon 780M: 16.9 → 13.0 fps.
- **Wukong** ([TechSpot](https://www.techspot.com/review/2883-black-myth-wukong-benchmark/)):
  - RX 6600 Medium = 50 fps; High ≈ 41 fps via Arc proxies, so ×~1.2.
  - Shadows and GI are its two most expensive settings ([TechSpot guide](https://www.techspot.com/guides/2884-wukong-optimization/)).

**Resolution-independent share, derived from the measured pairs (est.).** Only the Wukong figure comes from a clean pair (one device, only the scale changed); the other three mix scenes, devices or patch versions:
- **Wukong:** Low at 70% is 23.8 ms and at 50% is 19.6 ms. That fits 15.2 ms fixed plus 17.5 ms × pixel fraction, so **64% of the frame is resolution-independent**. This confirms Round 1's 54–66% estimate.
- **Stalker 2 v1.x:** 66.7 ms native vs 43.5 ms at 11% of the pixels, so the floor is **≥40 ms**.
- **Wilds at launch:** ~35 ms floor.
- **Space Marine 2:** 640×400 is still below 30 fps, so the CPU floor is **>33 ms**, and ~71 ms in hordes.

### Per-game answers

| Game | Gap to a High-like look (High preset, 67% scale → 800p, est.) | Bottleneck | Anti-cheat / tier | Engine hooks |
|---|---|---|---|---|
| **Wilds** | Best today ~30 fps at Deck defaults. High-like **~15 fps (67 ms)**; gap ≈ +35 ms | CPU in plains/camps at low settings (patch with a CPU focus "doesn't really help"; resolution drop gives little). GPU-bound at High | None; Denuvo Anti-tamper ([store](https://store.steampowered.com/app/2246340/)) → **Tier I** (watch Capcom anti-tamper) | RE Engine; ini holds only menu settings. OptiScaler works but needs REFramework ([wiki](https://github.com/optiscaler/OptiScaler/wiki/Monster-Hunter-Wilds)) |
| **Wukong** | Best today: Low 50%, ~45–51 fps. High-like **~18.5 fps (54 ms)**; gap ≈ +33 ms (2.6×) | GPU (benchmark fps scales with both resolution and preset) | Single-player, no anti-cheat → **Tier I** | UE5 with software Lumen. OptiScaler "officially supported" ([list](https://github-wiki-see.page/m/TheRazerMD/OptiScaler/wiki/FSR4-Compatibility-List)). Engine.ini honoured: likely, **unverified** |
| **Alan Wake 2** | Best today: lowest + FSR Perf, ~25 fps (est.). High-like **~11 fps (91 ms)**; gap ≈ +55 ms | GPU (Northlight engine, mesh shaders) | Epic Games Store only ([Sweeney](https://3dnews.ru/1117324/gendirektor-epic-games-podtverdil-chto-alan-wake-2-ne-viydet-v-steam)), so no Valve rating. No anti-cheat → **Tier I** | OptiScaler works on Linux with DLSS input + fakenvapi (same list) |
| **Space Marine 2** | Best today ~24 fps, 14 in hordes. High-like **~22 fps (est.)**: the CPU caps it, so High costs only ~3 ms more | **CPU** (proven by the 640×400 test) | **Easy Anti-Cheat** ([GOL Sep 2026](https://www.gamingonlinux.com/2026/09/warhammer-40-000-space-marine-2-update-is-causing-issues-for-steamos-linux-players/)), Deck "Playable" → **Tier S** | Swarm engine. `SteamDeck=1` applies Low + 30 cap ([GOL](https://www.gamingonlinux.com/2024/12/space-marine-2-adds-dlss3-fsr3-and-frame-generation-more-playable-on-steam-deck-needs-launch-option-for-desktop-linux/page=1/)) |
| **Stalker 2** | Best today (v2.0) ~30 fps with aggressive FSR (unverified). High-like **~18.7 fps (53.5 ms)**; gap ≈ +20 ms | CPU in settlements (v2.0 on PC, CPU-limited: 84.6→120.1 avg, 49→81.3 1% low ([OC3D](https://overclock3d.net/reviews/software/stalker-2-patch-2-0-tested-huge-improvements/))). GPU at High | Single-player; store lists no DRM or anti-cheat ([store](https://store.steampowered.com/app/1643320/)) → **Tier I** | UE 5.5.4. Engine.ini cvars: est. yes |

**Free win for Space Marine 2 (est.).** Because the CPU binds at ~42 ms, GPU settings can be raised to near-High for about 0–3 ms. The price list (E) should do this first.

---

## 2. Which ideas apply to which game (Y = applies, P = partly, N = no)

| Cluster | Wilds | Wukong | Alan Wake 2 | Space Marine 2 | Stalker 2 |
|---|---|---|---|---|---|
| **A** Driver-forced VRS (S) | P: raster-heavy, but CPU-bound at low settings | P: Lumen is compute and unaffected | P: forced rate may not reach mesh-shader pipelines | P: GPU-bound scenes only | P: compute-heavy UE5.5 |
| **B** Pass amortization | P: Tier I layer only, unproven | **Y**: Tier S Lumen/shadow cvars; shadows and GI are the top costs | P: Tier I layer, unproven | N: anti-cheat, no cvars | **Y**: Tier S cvars |
| **C** CPU/power scheduling (S) | **Y**: plains | P: watt arbitrage only | P | **Y**: the only lever in hordes | **Y**: settlements |
| **D1** Neural upscaler (I) | P: needs REFramework | **Y** | **Y**: pixel-bound (73%) | N: anti-cheat | **Y** |
| **D2** Compositor filter (S) | Y, small | Y, small | Y, small | **Y**: the only image-quality lever | Y, small |
| **E** Perceptual price list (S) | Y | Y | Y | **Y**: raise GPU settings to the CPU line | Y |
| **F** Driver/compiler autotune (S) | Y, small | Y, small | Y, small | Y, but custom builds are risky with anti-cheat | Y, small |
| **G** Reprojection (presented fps only) | P: orbit camera | P | P | P | **Y**: first-person |
| **H** Harvested GI (I) | N | P: mostly static levels; legal question | N | N | P: dynamic time of day and weather |

---

## 3. The honest stacked budget

### Method (all est.)

- **Baseline.** GPU frame at High, 67% internal → 800p, split into slices:
  - B-eligible (Lumen, GI, shadows, volumetrics);
  - pixel-proportional work, which D1 shrinks;
  - pixel-shader raster, which A acts on (a subset of the pixel-proportional slice);
  - everything else.
- **Order of application, each on its own slice:**
  1. B on its slice: pessimistic/central/optimistic = 10/30/50% (Tier S) or 0/25/50% (Tier I).
  2. D1 by cutting internal scale at equal quality: none / 67→57% / 67→50%, net of +0.3 ms network cost. This shrinks A's slice too.
  3. A on what remains of its slice: 5/20/40%.
  4. F: 0/3/7% of the remaining GPU frame.
  5. E: 3/10/18% of the remaining GPU frame.
  6. C: +0/3/6% fps when GPU-bound (only if the power cap binds), or −0/5/12% CPU frame time when CPU-bound.
- **Frame time** = max(GPU, CPU); fps = 1000 / frame time.
- **1% lows.** On the Deck these run ~0.75–0.85× the average in gameplay (est.). The benchmark-tool ratio of 0.90 is optimistic. "Good lows at 30" therefore needs a ~36–40 fps average.
- **Cut needed for 30 fps:** Wukong 38%, Stalker 2 38%, Wilds 50%, Alan Wake 2 63%. Space Marine 2's GPU needs 26%, but its CPU is the real limit.

### Results: High-like look, before → after (est.)

| Game | Before | Pessimistic | **Central** | Optimistic | Main carriers (central ms) |
|---|---|---|---|---|---|
| Wilds | 14.9 | 13.9 | **21.4** | 35.5 field / 32.5 plains (CPU) | D1 7.1, E 5.3, B 3.0 |
| Wukong | 18.5 | 17.9 | **29.2** | 50.0 | D1 7.3, B 4.5, E 3.9 |
| Alan Wake 2 | 11.0 | 10.4 | **17.0** | 32.7 | D1 18.0, E 6.7 |
| Space Marine 2 | 22.2 / 14 hordes | 21 / 13 | **25.3 / 15.0** | 30.8 / 18.0 | E 4.1, A 3.0, then CPU-bound |
| Stalker 2 | 18.7 | 17.2 | **30.0 wild / 28.0 settlements** | 43.4 / 33.5 (CPU) | D1 8.7, B 4.2, E 3.8 |

**Tier S only (no D1), central:** Wukong falls to ~25 fps (est.). D1 is both the biggest lever and the least proven: no per-game INT8 network on RDNA2 exists yet.

**Verdict on the two targets:**
- **≥30 fps with good lows:** Wukong and Stalker 2 wilderness need results above central. Wilds and Alan Wake 2 need near-optimistic results. Space Marine 2 does not get there: hordes stay CPU-bound at 15–18 fps in every case.
- **45 fps:** Wukong only, with everything working as claimed. That outcome has a low joint probability. Stalker 2 is CPU-capped at ~43 fps.

---

## 4. The portfolio

**Portfolio: B + D1 + E on Black Myth: Wukong.**

1. **B, Tier S.** Engine.ini Lumen update-factor cvars plus shadow refresh cvars. They hit Wukong's two most expensive settings.
2. **D1, Tier I via OptiScaler.** Same perceived quality at 50% internal instead of 67%.
   - Stand-in today: FSR 4 INT8 or XeSS. FSR 4 INT8 costs about +3.2 ms vs FSR 3 on the Deck ([SDHQ, anecdotal](https://steamdeckhq.com/news/we-can-now-use-fsr-4-on-the-steam-deck-for-better-visuals-with-a-power-tradeoff/)). It would still net ~9 ms (est.) if its quality at 50% matches TSR at 67%.
   - Shippable path: AMD says official FSR 4.1 for RDNA2 arrives "early 2027"; the Deck is not named ([GOL, 14 May 2026](https://gamingonlinux.com/2026/05/amd-announce-fsr-upscaling-4-1-officially-coming-to-rdna-3-and-rdna-2)).
   - Build a custom per-game network only if both fall short.
3. **E.** A price list scored at the Deck's own viewing geometry. It also re-tunes render scale, shadows and GI.

**Expected effect (est.):** 18.5 → **26.4 fps central** (pessimistic 17.7, optimistic 40.5). Crossing 30 needs each of the three to land around its 60th–70th percentile, or adding A + C + F (central 29.2).

I chose this over a C-led portfolio because the targets are GPU-bound at High. At High, C only helps Space Marine 2 and Stalker 2 settlements, and neither crosses 30 that way.

**Cheapest decisive experiment: 2–3 days, run by Fede or the bench runner, never a dev session (rule R7).** Use Wukong's free, deterministic [Benchmark Tool](https://store.steampowered.com/app/3132990/) on the OLED at 15 W, with MangoHud frame-time logs and 3 runs each:
1. High at 67% TSR. This is the first-ever measurement of a High-like look at ~800p; my estimate is ~49 ms in the benchmark.
2. Run 1 plus the Lumen/shadow cvars.
3. Run 2 with FSR 4 INT8 or XeSS at 50% replacing TSR at 67%. FSR 4 INT8 comes from a leaked SDK, so it is for measurement only; never ship it.
4. Capture matched frames and score them with ColorVideoVDP using the Deck display model.

**Pass / kill:**
- **Pass** if runs 2+3 reach ≤33 ms (≥30 fps) at ≤0.25 JOD below High at 67%.
- **Kill D1+B** if together they save less than 8 ms at that quality.
- Run 1 alone also recalibrates every estimate in this report.

---

## Caveats

- **Post-June-2026 claims I checked:**
  - Wilds Verified (Aug 2026): SDHQ plus [Digital Citizen](https://www.digitalcitizen.life/monster-hunter-wilds-is-now-steam-deck-verified-but-visual-quality-remains-a-major-compromise/). Verified.
  - Stalker 2 moving to UE 5.5.4: OC3D, DSOGaming and TweakTown. Verified.
  - Stalker 2 at "~30 fps on the Deck": a single secondary source. **Unverified.**
  - Space Marine 2's anti-cheat crash on Proton: GOL. Verified.
- **Sources I couldn't use:**
  - Steam's Deck-compatibility endpoint was blocked by the proxy, so Wukong's and Stalker 2's current Valve rating is unknown.
- Alan Wake 2 has no Deck measurement newer than 2023.

**Key facts to keep:**
- No public High-preset measurement near 800p exists on a Deck for any of the five games.
- The Wukong benchmark-tool data confirms a ~64% resolution-independent frame.
- Space Marine 2 is CPU-bound below 640×400, so it should get higher GPU settings for free, not more speed.
- B + D1 + E on Wukong is the portfolio to test first.
