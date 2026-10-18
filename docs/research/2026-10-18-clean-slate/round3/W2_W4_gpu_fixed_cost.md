# Round 3: walls W2 (fixed-cost GPU work) and W4 (reconstruction)

Read: `round3_brief.md`, `brief.md`, `round2/{B_H, A_G, D_neural, baselines_stack, X_anticheat, E_F}`.

Local sources checked:
- REFramework at commit `d052e8f` (2026-10-10), cloned to `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/reframework.biwy/repo`.
- vkd3d-proton at `0bb64c5` (2026-10-14).

I had no access to Epic's source. Cvar names I could not confirm in a document or a shipping-game ini are marked [unverified].

## 0. Two corrections to Round 2

1. **TSR on the Deck is measured, and it costs about twice Round 2's estimate.**
   - An Epic forum thread (UE 5.5, May 2025, `profilegpu` in sync mode, 640×360 → 1280×720, `sg.AntiAliasingQuality=1`) gives a TSR total of **2.63 ms**. ([forum](https://forums.unrealengine.com/t/understanding-tsr-rejectshading-gpu-cost/2598124))
   - Per pass:

     | Pass | Runs at | ms |
     |---|---|---|
     | RejectShading | input resolution | 1.35 |
     | UpdateHistory | output resolution | 0.82 |
     | DecimateHistory | input | 0.26 |
     | DilateVelocity | input | 0.20 |

   - Two heuristics inside that: the anti-flicker heuristic costs 0.58 ms and Resurrection costs 0.1 ms.
   - The shader labels read "VALU=16bit, WaveSize=32", and forcing wave64 was slower. **So the "run the upscaler at lower precision" idea is already done.**
   - `r.TSR.History.ScreenPercentage` supports only 100–200 ([TSR doc](https://dev.epicgames.com/documentation/en-us/unreal-engine/temporal-super-resolution-in-unreal-engine)), so TSR history cannot be stored below the output resolution.
   - Round 2 assumed TSR ≈1.2 ms (est.). At 800p it is more like **~2.9 ms (est.), about 13% of the 22.2 ms budget**, and about 0.9 ms of that is tied to the output resolution.
2. **REFramework on Wilds bypasses integrity checks.**
   - `src/mods/IntegrityCheckBypass.cpp:1131` scans for the pak SHA3/RSA check on "MHWILDS v1.041".
   - `:61–80` patches checksum-check jumps in RE8's "protected sections" (obfuscated code).
   - This runs into the brief's "no circumventing anti-tamper" line. Round 2's Wilds Tier I path ("OptiScaler … needs REFramework") inherits the problem.

## 1. Where the resolution-independent milliseconds are (Q1)

| Cost | Why it doesn't shrink with internal pixels | Lever beyond the menu (S1) | In UE 5.0–5.5 shipping builds? |
|---|---|---|---|
| Upscaler output passes and the post-processing after TSR | UpdateHistory runs at output resolution. Motion blur and tonemapping "run at display resolution unless a secondary screen percentage is set" (TSR doc). | `r.SecondaryScreenPercentage.GameViewport` (ini only, static, applied before the UI is drawn) ([doc](https://dev.epicgames.com/documentation/en-us/unreal-engine/screen-percentage-with-temporal-upscale-in-unreal-engine)). AA scalability at Medium or below turns off `r.TSR.ShadingRejection.Flickering`. | Yes |
| Lumen final gather and radiance cache | World-space probe budgets are fixed per frame | `…RadianceCache.NumProbesToTraceBudget/ProbeResolution/GridResolution` ([Epic guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine)); **`r.Lumen.IrradianceFieldGather 1`** (Idea 1) | The budget cvars, yes. The IFG cvar exists but crashed in 5.4. `r.Lumen.FinalGatherMethod` is 5.8-only. |
| Lumen surface cache | Fixed texel budgets | UpdateFactor cvars (already in Round 2) | Yes |
| Lumen reflections | Per pixel, but trace length is fixed | `r.Lumen.Reflections.Allow 0` falls back to SSR (about 1 ms on Series S, Epic) | Yes |
| Virtual shadow maps | Page count does scale with pixels ("lowered by reducing screen resolution"). Invalidation from WPO and skeletal animation, and far clipmaps, do not. | `r.Shadow.Virtual.ResolutionLodBias{Directional,Local}{,Moving}`, `Clipmap.LastLevel`, `MarkCoarsePages*`, `MaxPhysicalPages`, SMRT ray and sample counts ([VSM doc](https://dev.epicgames.com/documentation/en-us/unreal-engine/virtual-shadow-maps-in-unreal-engine)). WPO disable distance is a per-primitive property; no cvar is documented. | Yes. Which version added the *Moving* variants: [could not verify] |
| Nanite culling and rasterisation | Scales with instance and cluster counts, at a fixed triangle density | `r.Nanite.MaxPixelsPerEdge` (on Arm Mali, UE 5.5.2, going 1→3 took frames from 45.7 to 29.6 ms ([Arm](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/mori-to-nanite-billions-of-triangles-on-mobile)); a different architecture, order of magnitude only); `MinPixelsPerEdgeHW` (about 1 ms); `r.Nanite.ViewMeshLODBias.Min` (seen in an [Oblivion Remastered ini mod](https://www.nexusmods.com/oblivionremastered/mods/5276); semantics [unverified]) | Yes |
| Foliage with WPO, skinning, Niagara simulation | Scales with instances, vertices and particles | `r.ViewDistanceScale`, `r.SkeletalMeshLODBias` (seen in the same mod); `foliage.DensityScale`, `grass.DensityScale`, `fx.Niagara.QualityLevel` [unverified] | Yes |
| GPU scene update, HZB, instance culling, global distance field updates | Scale with how much the scene changes | No user lever | — |
| **Wilds** (RE Engine) | No public profile | `config.ini` holds only menu settings, and the game resets non-menu keys at launch ([Steam](https://steamcommunity.com/app/2246340/discussions/0/596268134575464734)). Going beyond the menu needs REFramework (correction 2). | — |
| **Alan Wake 2** (Northlight) | Mesh-shader geometry, distance-field GI | `renderer.ini` in `%LOCALAPPDATA%\Remedy\AlanWake2` (`m_*` keys) mostly mirrors the menu; whether it holds anything beyond: [could not verify]. See unknown unknown 3. | — |

**Epic's low-end guidance as it applies to 5.1–5.5 builds:**
- UE 5.8 (June 2026) "Lumen Lite" uses Irradiance Field Gather through `r.Lumen.FinalGatherMethod 0` and is described as "twice as fast as Lumen High". It is Beta and 5.8-only ([Tom Looman](https://tomlooman.com/unreal-engine-5-8-performance-highlights/), [TheSixthAxis, 18 Jun 2026](https://www.thesixthaxis.com/2026/06/18/unreal-engine-5-8-just-got-a-faster-lumen-for-nintendo-switch-2/)).
- Low GI = unshadowed skylight with `r.SkylightIntensityMultiplier=0.7` [whether that cvar exists in old builds: unverified].
- Stock UE5 ships no Steam Deck device profile. Under Proton the Windows profile is used ([forum, Dec 2023](https://forums.unrealengine.com/t/how-can-i-add-a-steamdeck-device-profile/1516709)).
- UE's dynamic resolution moves only the primary screen percentage ([doc](https://dev.epicgames.com/documentation/en-us/unreal-engine/dynamic-resolution-in-unreal-engine)). Nothing in the engine flexes the fixed cost.

## 2. Ideas (Q2)

### Idea 1: "Lumen Lite by ini" (switch on the irradiance-field gather prototype)

1. **Pitch.** Turn on the GI algorithm Epic just shipped for Switch 2 handheld, through the experimental cvar that older builds already compile.
2. **Already done?**
   - Epic only productised it in 5.8.
   - In older builds, a UE 5.4 user who set `r.Lumen.IrradianceFieldGather=1` got a crash ("FDiffuseIndirectCompositePS's required shader parameter") ([forum, Jul 2024](https://forums.unrealengine.com/t/how-to-enable-irradiance-field-gather-for-lumen/1945758)).
   - A Stalker 2 preset (v1.0, which shipped on UE 5.1) touches `r.Lumen.IrradianceFieldGather.NumProbesToTraceBudget` ([dtf.ru](https://dtf.ru/3212779-razbor-parametrov-ue5-ili-lite-preset-dlya-stalker-2)), so the cvar family exists in a shipping build.
   - I found no Deck guide or measurement that uses it, and it is not in any Round 2 list.
3. **Mechanism.** It replaces the screen-probe gather, which works at internal resolution with probes every 16 px, octahedral traces and filters. Instead it pre-integrates world-space radiance-cache probes to irradiance, applies probe occlusion, and interpolates per pixel. That gives a fixed probe budget plus a cheap per-pixel apply. The surface cache and reflections stay as they are.
4. **Tier:** S1 (Engine.ini `[SystemSettings]`). Targets Wukong (UE 5.0.0, according to a [Nexus forum claim](https://forums.nexusmods.com/topic/13497522-ue50-black-myth-wukong-modding-repack-problem/)) and Stalker 2 (UE 5.5.4).
5. **Budget (est.).**
   - Lumen GI at High on the Deck is about 6–10 ms. That comes from Oblivion Remastered with Lumen off (5–11 ms) and from PC data where Wukong's GI levels cost 18–44% of fps.
   - The gather plus radiance cache is about 65% of that.
   - Pessimistic: **0** (it crashes, as in 5.4).
   - Central: 0.5 × 0.65 × 6.5 ≈ **2.1 ms**.
   - Optimistic: 0.6 × 0.7 × 10 ≈ **4.2 ms**.
   - Wukong High-like goes from 54 to ~52 ms (central).
   - It overlaps Round 2's Lumen temporal knobs, which tune the very gather it replaces. Count the larger of the two, not the sum.
6. **Self-red-team.** "It's a 2021 prototype Epic shelved for four years. In 5.0 it will leak, be unfiltered, or crash." That is probably true in at least one of the two games. But the test takes minutes and has a hard kill. It is also the only S1 lever that changes the GI *algorithm* rather than its budget, so its gain isn't capped by the temporal knobs' 0.5/2/4 ms.
7. **Maintenance.** One ini line. The bench runner re-checks it after each patch. If a game moves to 5.8 or later, switch to `FinalGatherMethod 0`.
8. **Falsification experiment.**
   - Day 1 (owner, 10 min per game): write the line through `deckforge.safety`. **Kill for that game** on a crash, or on visible corruption at 3 checkpoints.
   - Days 2–7: Wukong Benchmark Tool plus a fixed Stalker 2 route. OLED at 15 W, first with the GPU pinned at 1.6 GHz, then at default, 5 runs each. Configurations: High GI, High GI + IFG, Medium GI; everything else High-like at 67% → 800p.
   - Quality captured on the PC at 1280×800, scored with ColorVideoVDP (Deck display model) and CGVQM.
   - **Pass:** saves ≥2.0 ms against High GI, is ≤0.3 JOD below High GI, and is ≥0.3 JOD above Medium GI.
   - **Kill:** saves <1.0 ms, or is no better than Medium GI at equal ms.

### Idea 2: Split reconstruction (secondary screen percentage)

1. **Pitch.** Let TSR (or an FSR/XeSS plugin) finish at ~75% of the panel, then let UE's own spatial upscale do the last 1.33× *before* the HUD. This takes the output-resolution share of the upscaler, and all post-TSR passes, out of the fixed cost. HUD text stays at native resolution.
2. **Already done?**
   - The cvar is documented. I found no Deck guide that uses it.
   - The closest common practice is gamescope's 960×600 game resolution with FSR1. It gives the same post-processing saving, but the HUD is rendered at 960×600.
   - TSR's other levers are already in use or capped (see correction 1), so this is the only TSR-side lever not already on.
3. **Mechanism.** At 75%, the history update and post-processing (motion blur, bloom, tonemapping) run on 0.5625× as many pixels.
4. **Tier:** S1, UE titles only.
5. **Budget.** Measured: UpdateHistory at 800p ≈ 0.91 ms. Estimated: post after TSR 0.8–2.0 ms; the extra spatial upscale pass +0.1–0.15 ms.

   | Secondary % | Arithmetic | Saving |
   |---|---|---|
   | 83% (pessimistic) | 0.31 × (0.91 + 0.8) − 0.15 | **0.4 ms** |
   | 75% (central) | 0.44 × (0.91 + 1.4) − 0.12 | **0.9 ms** |
   | 67% (optimistic) | 0.56 × (0.91 + 2.0) − 0.1 | **1.5 ms** |

   - If FSR/XeSS plugins also stop at the secondary resolution, their output-bound share (≈1 ms, est.) shrinks too [inference].
   - Against the gamescope 960×600 path the saving is ≈0 ms; the gain there is HUD legibility.
6. **Self-red-team.** "That's just render scale plus a blur, i.e. the price list." The answer: output resolution is the one axis the price list lacks, and the intercept fit over internal resolution cannot see it. The fair comparison is at equal ms: 0.9 ms spent here, or spent on internal resolution instead. At Wukong's measured 17.5 ms per full pixel fraction, 0.9 ms buys +0.05 of the pixel fraction (640×400 → ~700×437).
7. **Maintenance.** One static ini line, stable across patches.
8. **Falsification experiment (1 week).**
   - Games: Wukong and Stalker 2. Secondary % ∈ {100, 83, 75, 67}, 5 runs each, plus the equal-ms internal-resolution alternative.
   - Judges: ColorVideoVDP on stills and on a 10 s lossless motion clip, plus FLIP inside a HUD mask.
   - **Pass:** saves ≥0.7 ms at 75%, scores ≥ (the equal-ms alternative − 0.05 JOD), and has better HUD FLIP than gamescope 960×600.
   - **Kill:** saves <0.4 ms at 75%, or scores ≥0.15 JOD below the equal-ms alternative.

### Idea 3: Lock-in cvar ablation (bench instrument), with an optional closed-loop "intercept governor"

1. **Pitch.** Toggle each fixed-cost knob as a square wave during live gameplay and demodulate frame time. That prices each knob to about ±0.1 ms. Doing it at two resolutions splits every subsystem into a fixed part and a per-pixel part. Stage 2 closes the loop so the fixed cost can flex.
2. **Already done?**
   - UE4SS mods already cycle cvars at runtime, but by hotkey ([Silent Hill f mod 97](https://www.nexusmods.com/silenthillf/mods/97)).
   - Round 2's F1 relaunches the game per configuration, with 1–3% run-to-run noise (0.5–1.6 ms at 54 ms).
   - I found no demodulated or two-resolution profiler, and no closed-loop governor for fixed costs; UE's dynamic resolution only moves the per-pixel part.
3. **Mechanism.**
   - A UE4SS Lua script flips cvar X every 2 s, in ABBA order to cancel drift.
   - It drops the first 0.5 s after each flip (VSM and Lumen cache transients) and logs that separately as the switch cost.
   - Phases are aligned to the MangoHud log with a marker pulse. Δ = mean(on) − mean(off).
   - Repeating at `r.ScreenPercentage` 50 and 70 gives Δ(p) = a + b·p per knob.
   - Standard error: with σ ≈ 2 ms (est.) and ~2,700 kept frames in 3 minutes, SE ≈ 2/√1350 ≈ **0.055 ms**.
   - Stage 2: when GPU frame time stays above 21 ms for 0.5 s, step down only knobs that don't invalidate a cache (Lumen probe budgets, SMRT ray count, Niagara quality), with hysteresis. Never change the VSM LOD bias at runtime; that is what causes a spike.
4. **Tier:** I (UE4SS DLL injection).
   - Stalker 2 is the primary target, because GSC's official Zone Kit mod SDK is a permissive signal.
   - Wukong only on the bench, because of its EULA §2.2(1) and §8.3.
   - No anti-cheat titles.
5. **Budget.**
   - Stage 1 saves 0 ms by itself. It cuts the price list's search from ~55 Deck-hours to ~10 (100 knobs × 2 resolutions × 3 min).
   - Stage 2, on frames over budget, can flex 0.5 / 1.5 / 3 ms (est.). Central case: a 25 ms 1% low becomes 23.5 ms, about **+6% on 1% lows**. It does nothing when the spike is CPU-bound.
6. **Self-red-team.**
   - "Caches converge over many frames, so the on-phase isn't the steady-state cost." Answer: measure the settling curve first, use a half-period of at least 3× the settling time, and validate against relaunch A/B.
   - Stage 2 is the same controller pattern as Round 2's A2 load gate, with a different actuator. Don't stack both on one game without measuring.
7. **Maintenance.** The UE4SS community maintains the per-patch signatures, and DeckForge's script is about 100 lines. Stage 1 never ships. Stage 2 would be opt-in Tier I and will break on each game patch until UE4SS catches up.
8. **Falsification experiment.**
   - Days 1–3 (validity), on a fixed Stalker 2 route: compare lock-in Δ against a 10-run relaunch A/B for `r.ScreenPercentage` 50↔55, `r.Lumen.Reflections.Allow`, and `SMRT.RayCountDirectional 8↔0`.
   - **Pass:** bias ≤0.2 ms and SE ≤0.1 ms. **Kill:** SE or bias >0.3 ms.
   - Days 4–10: build a 20-knob, two-resolution table (this feeds Q3).
   - Days 11–14 (stage 2): 10 randomised runs with the governor on or off.
   - **Pass:** 1% lows improve ≥6%, average fps drops ≤1%, and viewers detect it in <60% of 160 2AFC trials. **Kill:** 1% lows improve <3%.

## 3. Settling the 34–66% fixed-share question (Q3)

**What I found.** I searched Deck, ROG Ally, 680M/780M and Switch 2 sources, Epic, and Arm. **No full-frame per-pass profile of a UE5 game on small RDNA hardware is public.** The partial evidence:
- The Deck TSR trace above.
- Arm Mali sensitivity to `MaxPixelsPerEdge`.
- Digital Foundry on Switch 2 (Sep 2025): Cronos ships at near-lowest PC settings with Lumen removed for 30 fps handheld, and Fortnite drops UE5's distinctive features. They give no per-pass numbers ([vgtimes summary](https://vgtimes.ru/tech-and-hardware/133427-lumen-i-nanite-ostalis-za-bortom-analiz-pokazal-realnye-vozmozhnosti-switch-2-na-unreal-engine-5.html)).
- Epic gives "2× faster" for Lumen Lite with no milliseconds.

**What this means for the Wukong 64% figure.**
- Round 2's intercept (15.2 ms at Low with FSR) must contain about 2.5–3.5 ms of upscaler and post work tied to output resolution (est., scaled from the TSR trace). That leaves ≤~12 ms that is scene-fixed or CPU.
- It was measured at **Low, where Lumen is off**. The share at High is a different number, because both the fixed and the per-pixel terms grow.

**How to settle it on the bench (S1, about 4 days).** Fit along three axes:
- **Internal resolution** (4 levels).
- **Output resolution:** the secondary screen percentage in UE titles, or gamescope's output resolution in any game, including Wilds, Alan Wake 2 and Space Marine 2.
- **GPU clock** pinned at 1.0 vs 1.6 GHz. CPU-bound and bandwidth-bound time doesn't scale with core clock.

Add RGP via `MESA_VK_TRACE=rgp`, and classify passes **without needing their names**: a dispatch's grid size shows which resolution it runs at (the forum trace shows 80×45 groups at 360p input vs 160×90 at 720p output). Passes whose grid follows internal resolution are per-pixel, those that follow output resolution are output-bound, and constant-grid passes are scene-fixed.

**Thresholds:** W2 is "large" if the scene-fixed share is ≥40% of the frame at 960×600 High, and "small" if it is under 25%.

## 4. Unknown unknowns

1. **REFramework's integrity bypass** (correction 2). Check whether REFramework runs on Wilds with that module removed. If the game refuses, every Tier I route on Wilds is dead under the project's rules.
2. **Detail deliberately tied to output resolution.**
   - UE's "Automatic View Mip Bias" samples textures at mip levels for the output resolution when upscaling (documented).
   - `r.Nanite.ViewMeshLODBias.*` may do the same for Nanite triangles [semantics unverified].
   - If so, part of the "fixed" share is there by design and costs bandwidth on a 102 GB/s bus. Lock-in toggle `r.Nanite.ViewMeshLODBias.Min 0` to check.
3. **Alan Wake 2's non-mesh-shader path.**
   - `VKD3D_DISABLE_EXTENSIONS=VK_EXT_mesh_shader` makes the mesh shader tier report as unsupported (`README.md:219`, `device.c:198–206, 9143–9151`), which should push the game onto its March 2024 fallback path (patch 1.0.16.1).
   - Prior report: it "reduced performance significantly" on an RX 7800 XT with Mesa 24.1 ([lemmy](https://lemmy.imagisphe.re/post/656911/2028793)).
   - On the Deck it would also let Valve's Half Rate Shading reach AW2's raster passes, which the forced rate skips under mesh shaders.
   - Caveats: the feature level drops below 12_2 (`device.c:9670–9677`), so the game may refuse to start. vkd3d-proton already carries an AW2 mesh-shader workaround (`device_workarounds.c:159`).
   - Costs one evening to check.

**Key facts to keep:**
- Measured TSR on the Deck: 2.63 ms at 360p → 720p.
- REFramework bypasses RE Engine integrity checks.
- UE 5.8 Lumen Lite = Irradiance Field Gather; the old cvar crashed in 5.4.
- Stock UE5 has no Steam Deck device profile.
- UE dynamic resolution flexes only the per-pixel cost, never the fixed cost.
