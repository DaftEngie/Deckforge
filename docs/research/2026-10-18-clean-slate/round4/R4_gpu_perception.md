# Round 3 red-team: W1 and W2/W4 ideas (UE5 rendering plus perceptual metrics)

**Sources I read myself:**
- REFramework at upstream HEAD `d052e8f` (2026-10-10). I fetched it again today and nothing has changed.
- vkd3d-proton `0bb64c5`.
- Mesa main, through the GitHub mirror: `radv_pipeline_graphics.c` and `docs/envvars.rst`.
- The Intel XeSS UE plugin v3.0.5 source, from the UE5.0 and UE5.5 release zips.
- Epic's 5.8 docs.
- The W1 simulation scripts, which I re-ran, plus two simulations of my own run inline. I wrote no files.

## Verification points

**TSR "2.63 ms on a Deck": [checked, with caveats].** ([forum](https://forums.unrealengine.com/t/understanding-tsr-rejectshading-gpu-cost/2598124), 15 May 2025)
- The poster is a developer doing "optimizations for Steam Deck" on "our game", running "through Proton". It is UE 5.5, captured with `profilegpu` in sync mode, 640×360 → 1280×720, `sg.AntiAliasingQuality=1`.
- In a later post they write "r.TSR.ShadingRejection.Flickering is responsible for ~0.58ms (on steam deck)".
- Not stated: the Deck model, TDP, clocks, or the game's name.
- Epic's reply says async compute can hide about 0.46 ms.
- The 5.8 TSR doc says the flicker heuristic is on by default only at the High, Epic and Cinematic AA levels. So a default Medium-AA configuration wouldn't pay the 0.58 ms.
- **Revised TSR cost at 800p: about 2.0–2.9 ms (est.), not a flat 2.9.**

**REFramework bypasses integrity checks: [checked], and it is stronger than W2 claimed.**
- It isn't an optional module.
  - `Mods.cpp:30–33` registers `IntegrityCheckBypass` for every RE Engine game flagged as anti-tamper, and `GameIdentity.cpp` flags MHWILDS as anti-tamper (`m_reengine_at = true`).
  - `REFramework.cpp:565–567` runs `immediate_patch_dd2` on these titles. Its comment says it deals with "the scans that are done every frame on the game's memory… the crash will be avoided" (`IntegrityCheckBypass.cpp:1299–1306`).
  - That function then calls `restore_unencrypted_paks` (`:1435`). This NOPs the branch that rejects a pak whose RSA-signed SHA3-256 hash doesn't match (`:1211–1235`).
- Line `:1131` is the fallback search pattern for Wilds v1.041.
- **So every Wilds route that depends on REFramework, including OptiScaler, crosses the "no circumventing anti-tamper" line. It is dead under the project rules.**

## 1. Display-matched mip bias

**Already done? Partly, by the engine itself.**
- The cvars exist, but their effect is unverified.
  - `r.ViewTextureMipBias.Offset` and `.Min` appear in users' ini files for a UE5 game ([Oblivion Remastered, Nexus 2642](https://www.nexusmods.com/oblivionremastered/mods/2642?tab=posts)).
  - A UE4 game guide lists their defaults as −0.3 and −2 ([Gundam Breaker 4](https://medium.com/@appleDODO/gundam-breaker4-max-graphics-setting-3167e95d3cb2)).
  - Neither source says whether they visibly did anything.
- The engine formula, log2(render/display) + Offset clamped at Min: [could not verify] in source.
- XeSS's own guidance is exactly display-matched: "−1 for 2.0x" (`xess_guide.md:502`). So under TSR or XeSS the headroom is only about 0.3 mip, not the ~1 mip implied by FSR2's −2.0 (`fsr2_readme.md:431–445`).

**What the upscaler plugins do:**
- **XeSS plugin:** it contains no bias code at all and outputs at `GetSecondaryViewRectSize()` (`XeSSUpscaler.cpp:96`). So the engine's bias and the ini Offset apply [checked].
- **FSR3 plugin:** it has `r.FidelityFX.FSR3.AdjustMipBias` (default 1, "Applies negative MipBias to material textures") [checked, [GPUOpen](https://gpuopen.com/learn/ue-fsr3/)].
  - Whether it overwrites `r.ViewTextureMipBias.*` so that an ini line loses: [could not verify].
  - The plugin needs UE 5.1.1 or later. If Wukong really is UE 5.0 [could not verify: an unsupported forum claim], its FSR is a custom integration.

**Budget (est.):**

| Upscaler | Pessimistic | Central | Optimistic |
|---|---|---|---|
| TSR or XeSS | 0.05 ms | 0.2 ms | 0.6 ms |
| FSR | 0.1 ms | 0.4 ms | 1.0 ms |

This sits under the price-list (E) umbrella; don't add it on top.

**Verdict: SURVIVES WITH CHANGES.** It is one E knob, not a new idea.
- Test Offset at {−0.3, 0, +0.5}. The Offset is absolute, so W1's "+1" is 1.3 mip blurrier than the default.
- Before trusting any result, confirm the ini is honoured: at Offset +3 textures must be visibly blurry.
- With FSR, also run with `AdjustMipBias=0`.
- Pass: ≥2% GPU time saved with ΔJOD ≥ −0.05, or ≥+0.1 JOD on the foliage and fur clips.
- Drop the vkd3d-proton upstream proposal unless this test passes.

## 2. Effect-density pinning

**Facts:**
- `DownsampleFactor` and the VSM `ResolutionLodBias` cvars exist in the docs [checked].
- `r.VolumetricFog.GridPixelSize`: [could not verify in Epic's doc].
- "Any process before TAAU will use a lower resolution" [checked].
- Whether UE already compensates these effects for screen percentage: [could not verify].
- Whether `DownsampleFactor` accepts a non-power-of-two value like 12 (W1's 16→12 step): [could not verify].

**The catch:** pinning *raises* effect cost compared with scaling everything uniformly. It is a trade, and in practice a structured prior for E's search.

**Budget:** 0 / 0.8 / 2.5 ms at equal JOD (est.), entirely inside E.

**Verdict: SURVIVES WITH CHANGES, as a prior for E.**
- Add a day-0 check: do non-power-of-two factors render correctly?
- Identify passes by timing regression (see idea 9).
- Keep W1's pass and kill thresholds.

## 3. Viewing-condition-indexed profiles

**Facts:**
- The SteamOS kernel builds the LTR-F216A light-sensor driver (`config-neptune:69`, next to the `MFD_STEAMDECK` options) [checked].
- The sensor's sysfs path on the OLED: [could not verify].
- The reflected-light arithmetic (0.48 / 1.6 / 6.4 nit) [checked].
- CVVDP takes `E_ambient` and `k_refl` (`README:97–102`) [checked].

**Failure modes:**
- Adaptive brightness raises the screen's luminance as ambient light rises, which partly undoes the masking the idea relies on.
- The profile is chosen only at launch.
- Most play is probably indoors at 50–300 lux (est.), so the buckets may collapse into one.

**Budget:** 0 / 1 / 3 ms in the matched bucket. Weighted across real sessions, about half that.

**Verdict: SURVIVES WITH CHANGES, lowest priority.**
- Run only the offline metric stage until the 2-week sensor log shows ≥20% of play time outside the default bucket.
- Never use it as a headline result.

## 4. "Lumen Lite by ini"

**Facts:**
- 5.8 Medium GI is "Irradiance Final Gather, enabled by `r.Lumen.FinalGatherMethod 0`", aimed at Switch 2 including handheld. Each GI level costs "approximately half" of the level above it [checked, [Epic Lumen guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine)].
- The 5.4 failure was an assert: "FDiffuseIndirectCompositePS's required shader parameter … DiffuseIndirect_Lumen_2 was not set" [checked, [forum](https://forums.unrealengine.com/t/how-to-enable-irradiance-field-gather-for-lumen/1945758)].
- **Stalker 2 evidence: [contradicted].** The dtf.ru preset only sets `…IrradianceFieldGather.NumProbesToTraceBudget=128`. It never enables the gather and reports no result. UE stores unknown cvars from an ini without complaint, so that line proves nothing.
- The 5.8 gather is described as "new" in ue5-main testing (Mar 2026): 60 → 85 fps on an RTX 3080 at 4K, worse occlusion in detailed areas ([video](https://www.youtube.com/watch?v=KRo9OAVa0hE)). So the 5.0–5.5 prototype is not the algorithm Epic shipped.

**Key risk (my inference):** that assert is a validation check that shipping builds compile out. In a 5.4+ shipping build you would most likely get an unbound texture and wrong or black indirect lighting, not a clean crash. So the kill test must compare the image against High, not just check that the game launches.

**Budget (est.):**
- Wukong: 0 / 1.0 / 3 ms.
- Stalker 2 on 5.5.4: 0 / 0 / 1.5 ms.
- It removes the per-pixel screen-probe work, which is already small at 50–67% internal resolution. The fixed radiance cache stays.

**Verdict: SURVIVES, as a 10-minute probe with low expected value.**
- First confirm the cvar is live: an extreme value of a sub-cvar must visibly change the image.
- Then run W2's thresholds.

## 5. Split reconstruction (`r.SecondaryScreenPercentage.GameViewport`)

**Facts:** The [Epic doc](https://dev.epicgames.com/documentation/en-us/unreal-engine/screen-percentage-with-temporal-upscale-in-unreal-engine) says [checked]:
- "a Secondary Spatial Upscale runs after the TAAU pass";
- "Spatial Scaling happens before the UI";
- it is static, set in ini or a device profile, and Fortnite used it on Xbox One at 83.33%.

That device-profile example implies it works in shipping builds; the doc never says "shipping". Plugins:
- **XeSS:** follows the secondary resolution [checked].
- **FSR3:** [could not verify]. Its quality mode overrides `r.ScreenPercentage` [checked].

**The catch:** the primary percentage applies on top of the secondary one.
- 75% secondary with Performance drops the internal resolution from 640×400 to 480×300.
- Holding 640×400 needs Quality at 960×600. That is just the gamescope 960×600 path, with a native HUD added.

**Budget:** 0.3 / 0.6 / 1.1 ms (est.).

**Check first:** if the game's AA level keeps TSR history at 200% (range 100–200 [checked], TSR doc), then `r.TSR.History.ScreenPercentage=100` is the bigger output-resolution saving. It is an E knob.

**Verdict: SURVIVES WITH CHANGES.**
- Compare at equal internal resolution and at equal milliseconds.
- Keep W2's pass threshold (≥0.7 ms saved at 75%) and kill thresholds.

## 6. Lock-in ablation and the intercept governor (Tier I)

**UE4SS compatibility:**
- Wukong: yes ([RE-UE4SS packaged Aug 2024](https://www.gamepressure.com/download/black-myth-wukong-re-ue4ss-mod-loader-and-debug-tool-v11-mod/z014ed2)).
- Stalker 2 v1.x: yes ([Steam, Dec 2024](https://steamcommunity.com/app/1643320/discussions/0/4626981776940665420)).
- Stalker 2 v2.0 on UE 5.5.4 (released 20 Aug 2026, [playnews](https://www.playnews.gg/en/guides/stalker-2-update-2-0-mods-zone-kit-unreal-engine)): [could not verify].

**The statistics are optimistic.**
- I simulated frame times whose scene-driven content is correlated over 1–3 s (SD 2–3 ms, plus 1 ms jitter), for 3 minutes with a 2 s ABBA square wave.
- The true standard error is **0.31–0.40 ms**, against W2's 0.055 ms. That is 4–6× optimistic.
- Rescue: measure from static viewpoints, or run phase-reversed repeats on the deterministic benchmark. Compute the SE from ABBA-cycle differences, not from individual frames.

**Cache settling:**
- Budgeted systems (probe and surface-cache budgets) settle in cost almost at once, though the image settles more slowly.
- Knobs that reallocate memory, invalidate the VSM cache or switch shader permutations cause pipeline compiles on the first toggle and hitches when render state is recreated. Exclude those, or use long half-periods.

**Stage 2 (the governor):**
- Many spikes are CPU-side (streaming, pipeline compiles, garbage collection).
- It detects overload 0.5 s late, so it only acts on sustained load.
- It overlaps UE's dynamic resolution and Round 2's A2 load gate.

**Verdict:**
- **Stage 1 SURVIVES WITH CHANGES** (bench only). Validity test: bias ≤0.2 ms against a 10-run relaunch A/B.
- **Stage 2 SURVIVES WITH CHANGES** as research only: Wukong on the bench; Stalker 2 only after UE4SS is confirmed on 2.0. Pass: 1% lows +6%.

## 7. The measurement protocol

**Analysis problems:**
- W1's own script (`power2.py`) at 24×16×1 gives power 0.95–0.98, but **8.6–13.6% false passes** at the 0.5 JOD margin. The per-clip t-test ignores the observer variance that is shared across all clips.
- My simulation with crossed observer and clip random effects:

  | Design | Power (true difference 0) | False passes (true 0.5 JOD) |
  |---|---|---|
  | 24 observers × 16 clips × 1 trial | 0.91–0.97 | 6.3–6.9% |
  | 12 observers × 16 clips × 2 trials | 0.81–0.95 | 5.8–6.6% |

- The "no clip above 1.0 JOD" rule, applied to point estimates, cuts power to 0.66–0.79. Use a per-clip lower bound instead.

**Fact checks:**
- **P.913 wording [checked]:** "24 or more … controlled environment", increasing "to 35 … public environment or a narrow range of audiovisual quality" ([Pinson & Janowski](https://its.ntia.gov/publications/download/Pinson2014eLetter.pdf)). It is a rule of thumb for mean-opinion-score tests. The power should come from simulation, not from the standard.
- **CGVQM [contradicted, in part]:** the 0.871 score belongs to CGVQM-5; CGVQM-2 scores 0.855. Either way it is in-distribution: its dataset is 20 remote participants and XeSS-only upscaling with synthetically boosted ghosting ([arXiv](https://arxiv.org/html/2506.11546v1)). That is weak support for making it "the artifact detector".

**Other design flaws:**
- The reference doesn't match: W1 uses High at native 100%, the baselines use High at 67%.
- "Which looks better?" rewards sharpening, so force identical sharpening on both sides.
- ρ ≥ 0.6 across 8 conditions is not significant (the one-sided critical value is about 0.64).
- Matching content across clips needs a deterministic camera, so only the frozen benchmark tool works.
- Capture judder confounds the test unless duplicate frames are checked.

**Cheapest defensible version:**
- Wukong benchmark, one candidate.
- 12 observers × 16 clips × 2 trials, plus 4 High-vs-Low and 4 High-vs-High pairs.
- About 20 minutes per person.
- Crossed analysis, pre-registered. No colorimeter is needed for the human verdict.
- The claim is limited to that panel, that room and that distance.

**Target wording:** use "not reliably preferred over High (upper bound ≤ 63%)" rather than "perceived within X JOD". Define the frame-time test as ≤1% missed presents at a 30 cap, or uncapped p99 ≤ 31.7 ms. Keep the 45 fps track.

**Verdict: SURVIVES WITH CHANGES.**

## 8. Alan Wake 2 non-mesh-shader path

**Facts [checked]:**
- vkd3d-proton side:
  - The env var is documented (`README.md:219`) and honoured (`device.c:198–215`).
  - The reported mesh-shader tier is derived from the Vulkan feature (`device.c:9143–9151`).
  - Feature level 12_2 requires mesh shaders (`device.c:9666–9677`).
  - AW2 has a workaround entry that enables mesh shaders without barycentrics (`device_workarounds.c:159`). So it runs the mesh path on the Deck today (inference).
- The game:
  - Patch 1.0.16.1 (6 Mar 2024) "optimizes rendering for GPUs that don't support mesh shaders".
  - Its minimum spec dropped to the RX 5600 XT, which has no mesh shaders ([DSOGaming](https://www.dsogaming.com/patches/alan-wake-2-patch-1-0-16-1-released-optimizing-rendering-for-older-gpus/)). So starting at feature level 12_1 should work (inference).
- RADV's forced VRS skips mesh shaders (`radv_pipeline_graphics.c:1948–1950`).

**Prior report is mixed** ([lemmy](https://lemmy.imagisphe.re/post/656911/2028793)): one user went 12 → 45/51 fps; the original poster saw "reduced performance significantly". The "Mesa 24.1" detail W2 cites: [could not verify].

**Budget:** −3 / 0 / +2 ms. VRS reaches little, because the forced rate skips alpha-tested foliage.

**Verdict: SURVIVES, as a one-evening probe.**
- Pass: ≥5% GPU time saved.
- Kill: a launch failure or any regression.

## 9. Three-axis fixed-share fit

**Facts:** `MESA_VK_TRACE=rgp`, with `_TRIGGER` and `_FRAME` [checked, `envvars.rst:382–430`]. The F1 trigger is X11-only, so use the trigger file under gamescope.

**Flaw in the classification:** classifying passes by grid size fails for indirect dispatches (Nanite, VSM, Lumen compacted tiles) and for draws.

**Rescue:**
- Match passes across captures by pipeline hash and order, then regress each one's duration on internal and output pixels.
- For non-UE games, hold the internal resolution at 640×400 by comparing 1280×800 Performance (2×) with 960×600 Quality (1.5×).
- Pin the CPU clock as well as the GPU clock, and confirm the GPU clock holds at 15 W.

**Verdict: SURVIVES WITH CHANGES.** Keep W2's threshold: a scene-fixed share ≥40% means W2 is large, under 25% means small.

## Double counting

Ideas 1, 2, 3, 4 and 5 are all Engine.ini knobs under E's umbrella; never sum them. Idea 4 overlaps Round 2's Lumen temporal knobs. Idea 5 overlaps the gamescope 960×600 path and the TSR history knob.

## Verdict table

| Idea | Verdict |
|---|---|
| 1. Mip bias | SURVIVES WITH CHANGES (an E knob, about 0.2 ms) |
| 2. Effect pinning | SURVIVES WITH CHANGES (a prior for E) |
| 3. Viewing-condition profiles | SURVIVES WITH CHANGES (lowest priority) |
| 4. Lumen Lite by ini | SURVIVES (10-minute probe, low expected value) |
| 5. Split reconstruction | SURVIVES WITH CHANGES (check TSR history first) |
| 6. Lock-in and governor | SURVIVES WITH CHANGES (fix the statistics; stage 2 research only) |
| 7. Protocol | SURVIVES WITH CHANGES (crossed analysis; 12×16×2) |
| 8. AW2 non-mesh path | SURVIVES (one-evening probe) |
| 9. Three-axis fit | SURVIVES WITH CHANGES (per-pipeline regression) |

## What would change my mind

1. FSR plugin source showing that it leaves an ini `r.ViewTextureMipBias.Offset` in force, plus a measured gain of ≥2%.
2. Evidence that UE already scales probe or froxel density with screen percentage. That kills idea 2.
3. A sensor log showing ≥30% of play time in a second bucket.
4. A correct image from the irradiance-field gather in a 5.5.4 shipping build.
5. FSR3 plugin source that ignores the secondary rect. That would kill idea 5 for FSR.
6. Measured content-driven frame-time correlation under 0.5 s, which would make the iid standard error valid.
7. A pilot showing observer SD under 0.2 JOD, which would allow 8 observers.
8. Measured faster non-mesh rendering on RDNA2 under RADV.
9. RGP exposing the dimensions of indirect dispatches.

## Key facts to keep

- REFramework's anti-tamper bypass is mandatory on Wilds, so every Wilds Tier I route is dead.
- Under TSR or XeSS, UE's default mip bias is only about 0.3 mip below display-matched. The XeSS UE plugin sets no bias.
- The primary screen percentage applies on top of the secondary one.
- The lock-in standard error is about 0.3 ms at 3 minutes, not 0.055.
- Use a crossed random-effects analysis; 12 observers × 16 clips × 2 trials is the cheap design.
- The TSR forum numbers are from a sync-mode profile of an unnamed game, with the Deck model unstated.

The GPUOpen FSR2 guide page timed out on a permission prompt and was not read.
