# Round 3 (W1 + W4 perception): what "High-like" means, how to prove it, and whether to change the target

## Bottom line
- **High-like is testable, and nobody has tested it.** Nobody has published a High-vs-Medium panel on a handheld, and no High-preset run near 800p exists (Round 2 baselines). Round 2's E1 plan (4 observers × 40 trials) is too small. Once scene-to-scene and observer-to-observer variation is modelled, it has only a 0.40–0.58 chance of passing a candidate that truly equals High (my simulation, below).
- **Recommended instrument:**
  - ColorVideoVDP (CVVDP) with a *measured* Deck display model screens the candidates.
  - CGVQM runs alongside as a check for ghosting and flicker artifacts.
  - The human judge is a no-reference paired comparison on the Deck, scaled to JOD with pwcmp: 24–35 observers, 16 clips per game, clips analysed as a random factor.
- **Three new Tier S ideas:** a display-matched mip bias, effect resolution pinned to display pixels, and viewing-condition-indexed profiles. Each is worth about 0.5–3 ms (est.). None of them closes the gap alone.
- **Wukong Medium/50% FSR (32 avg / 28 at the 5th percentile)** is about 15% short of a clean 30 lock. That is within reach of the central Tier S stack. **The open question is the look, not the fps.**

---

## Q1. Definition and measurement

**Definition.** A candidate C is "High-like" for a pre-registered clip set and viewing condition if both hold:
- In no-reference viewing, the pooled preference for High over C is **≤63.2%**, which is ≤0.5 JOD on pwcmp's scale (1 JOD = 75%). This is judged on the 95% upper bound, with clips treated as random.
- **No single clip** has a point estimate above 1.0 JOD, so a bad cave scene can't hide behind good field scenes.

"Indistinguishable" is a separate, stronger claim: in a 2AFC test ("which one is High?") after a labelled training block, the upper bound on the correct rate is below 60%. That needs about 155 trials for 80% power (my simulation).

| Element | Design |
|---|---|
| **Metric** | **CVVDP** (v0.5.7, which runs on Apple Silicon by default, so on the owner's M3 Max) is the primary screen, because it is the only candidate that models nits, ambient light, reflection and distance (README:89–106,146–158). **CGVQM-2** is the artifact detector: it scores 0.871 against CVVDP's 0.744 on rendering artifacts, but it "does not account for viewing conditions and display parameters", and its dataset was remote viewers on ≥FHD monitors with 1024² crops at 30 fps ([arXiv 2506.11546](https://arxiv.org/html/2506.11546v1)). If the two disagree by more than 0.3 JOD, the clip goes to humans. FovVideoVDP adds nothing at a 26° field of view. FLIP is for per-frame debugging only; `QUALITY_TARGET.md` currently screens with FLIP and should change. Score CVVDP twice: raw, and after a per-clip global tone match, because full-reference metrics punish exposure shifts that a no-reference viewer never sees. |
| **Display model** | Custom JSON entry: 1280×800, 7.4", `viewing_distance_meters` 0.30 (worst case) and the observers' measured median. Use `max_luminance` and black level measured with a **colorimeter** at the owner's slider positions (accessory; a phone lux app measures illuminance at the phone, not screen luminance, so Round 2's step is wrong). Measure `k_refl` with a gray-card photo of the switched-off screen, **separately for glossy and etched glass**. `E_ambient` is pre-registered at 5 and 150 lux. Use the PQ colorspace for HDR titles. |
| **Reference** | R_High is the High preset at 100% render scale (native 1280×800) with the game's default anti-aliasing. R_max (max settings at 200%, downscaled) is an anchor. The Deck cannot show High at 30 fps live, so **every condition is pre-rendered video played on the Deck**. Render both sides on the bench PC. For UE titles use `-BENCHMARK` ("fixed-step… without skipping any frames"), `-FPS=30` and `FIXEDSEED` ([UE docs](https://dev.epicgames.com/documentation/en-us/unreal-engine/command-line-arguments?application_version=4.27)); whether shipping Wukong and Stalker 2 honour these is [could not verify]. Capture losslessly (FFV1) with the real frame rate capped at 30. Gate each clip at ≥9.5 JOD reference-vs-reference. Clips below the gate go to humans only: **human no-reference comparisons don't need pixel alignment**, so alignment failures limit the metric, not the judge. Once per game, spot-check PC-rendered against Deck-rendered candidate frames at ≥9.5 JOD. |
| **Stimuli** | 16 clips × 8 s per game: 8 scene classes × 2 (foliage pan, dark interior/cave, night, ≥90°/s orbit, fur/hair close-up, combat effects, sky edges, HDR highlights). Spread them by spatial/temporal complexity (P.910 SI/TI). HUD off, which is stricter. 4 clips are held out from all tuning. |
| **Playback** | Frame-exact lossless playback at 30 fps on the 90 Hz panel. Verify zero dropped frames with a 240 fps phone video of a frame-counter clip. |
| **Protocol** | Sequential A / grey / B, "which looks better?". Conditions per clip: High, candidates, stock Medium at the same render scale, Low, R_max, and a High-vs-High null pair. Exploratory scaling uses ASAP active sampling ([Mikhailiuk et al.](https://arxiv.org/pdf/2004.05691)) and pwcmp (Thurstone Case V, bootstrapped over observers). The **confirmatory High-vs-candidate pair gets a fixed, pre-registered allocation**, not an adaptive one. Sessions ≤30 min. |
| **Observers** | ITU-T P.913 recommends ≥24 subjects in a controlled environment, "increas[ing] to 35 … [for] a narrow range of … quality" ([Pinson 2014](https://its.ntia.gov/publications/download/Pinson2014eLetter.pdf)). High vs Medium-plus is a narrow range, so 35 is standards-compliant and 24 is the floor. Screen observers for acuity and colour vision. The owner and anyone who watched the clips during tuning are excluded from the confirmatory data. |
| **Trials (my simulation)** | Assumes observer SD 0.3–0.5 JOD and clip SD 0.3–0.4 JOD. **24 observers × 16 clips × 1 trial on the critical pair** gives 0.95–0.98 power. With 8 clips it drops to 0.76–0.83. **Treating clips as fixed inflates false passes to 13–15%.** |
| **Validity guards** | High vs Low ≥2 JOD. Null pair within 42–58%. Spearman ρ(CVVDP, human) ≥0.6 across ≥8 conditions. Held-out clips must pass. If High vs stock Medium is itself <0.5 JOD, report "the preset ladder is invisible on this screen". That is a finding, not a pass. |

**Two-week pilot on Wukong (owner-run, never a dev session):**
- Days 1–2: display characterisation.
- Days 3–4: reference repeatability.
- Days 5–7: capture High, Medium, Low, Medium/50% FSR and Medium/50% XeSS.
- Days 8–12: 8 observers (P.913 allows pilots "to find trending").
- **Instrument kill:** High vs Low <1 JOD, or the null pair outside 40–60%.
- **Output:** the first estimate of the observer and clip variances, and of the High-vs-Medium/50% gap.

---

## Q2. New ideas

### A. Display-matched mip bias
1. **Pitch.** Upscaler guidance pushes texture detail beyond what this screen can show. On a 42–56 pixels-per-degree OLED that buys shimmer and memory bandwidth. Bring the bias back to display-matched, or +0.5 above it.
2. **Already done?**
   - FSR2 recommends `log2(render/display) − 1.0`, which is −2.0 at 50% (`dl/fsr2_readme.md:429–445`).
   - XeSS asks for −1 at 2× and warns that more negative values cost "memory bandwidth" and cause "flickering and moire" (`skD/xess_guide.md:495–508`).
   - DXVK has `d3d11.samplerLodBias`, but only for D3D11 linear-filtered samplers (`dxvk.conf:302–318`, `d3d11_sampler.cpp:25–33`).
   - vkd3d-proton passes `MipLODBias` through untouched, with no override (`resource.c:8537`, commit 0bb64c5).
   - So no S1 lever exists for the five D3D12 targets outside UE cvars. A quick search found no Deck guide that sets it, and it is not on E's menu.
3. **Mechanism.** UE: `r.ViewTextureMipBias.Offset` in Engine.ini (name recalled, [could not verify]; confirm by visible blur at +1). Non-UE: upstream a vkd3d-proton option that mirrors DXVK's, including its linear-filter guard. The detail it removes sits in the finest octave (about 10% of SQRI), while the shimmer it causes is temporal and spans all bands.
4. **Tier.** S1: ini now, vkd3d-proton after an upstream merge.
5. **Budget (est.).** Texture sampling is about 10–20% of the GPU frame, so the saving is 0.5 / 2 / 5% of GPU time. On Wukong Medium/50% (31.25 ms) that is **0.16 / 0.6 / 1.6 ms**. Quality: −0.1 / +0.05 / +0.2 JOD.
6. **Red-team.** "Upscalers need the bias to rebuild texture detail, and 0.6 ms is noise." Answer: it is a continuous knob, judged on the close-up clip class. Its main value may be in stability, not ms. Below the 3% noise floor it must be pooled with other changes or killed.
7. **Maintenance.** One ini line per UE game. The vkd3d-proton path lives upstream if it is merged; if not, the idea is dead for non-UE games.
8. **Falsification (3 days).** Wukong benchmark, Medium/50% with FSR and XeSS, offsets {0, +0.5, +1}, 5 runs each, scored with CVVDP and CGVQM on 16 clips.
   - **Pass:** ≥2% GPU ms saved with ΔJOD ≥ −0.05, or ≥+0.1 JOD at equal ms.
   - **Kill:** <1% saved and no JOD gain, or no visible change at +1.

### B. Display-referenced effect density ("pin the 2–8 cpd band")
1. **Pitch.** Lowering render scale also coarsens every effect computed before the upscaler, measured in display degrees. That removes detail in the 2–8 cpd band, which carries about 42% of SQRI. Scale those effects' pixel-size cvars with render scale so they stay fixed in display cycles per degree, while primary visibility drops.
2. **Already done?** Epic: "any process before TAAU will use a lower resolution" ([screen-percentage doc](https://dev.epicgames.com/documentation/en-us/unreal-engine/screen-percentage-with-temporal-upscale-in-unreal-engine)). E's main-effects screening cannot see a render-scale × effect interaction. I found no preset or guide that couples the two. What is new is a rule from the contrast-sensitivity model that turns a 2-D search into a 1-D one.
3. **Mechanism.** A per-game table: render scale s → `r.Lumen.ScreenProbeGather.DownsampleFactor` ∝ s (16 → 12 going from 67% to 50%), `r.VolumetricFog.GridPixelSize` ∝ s, AO and contact shadows at full resolution, and a VSM resolution LOD bias of −log2(s/s_ref). Names recalled; verify per engine version.
4. **Tier.** S1 (Engine.ini).
5. **Budget (est.).**
   - Wukong High-like is 54 ms at 67%. The resolution-dependent 36% is 19.4 ms, of which the effects are 40–60%.
   - Dropping only primary visibility to 50% saves 3.5–5.2 ms. A uniform drop to 50% saves 8.6 ms but loses the mid-band effects.
   - At equal JOD against the best uniform scale: **0 / 1.5 / 3 ms**.
6. **Red-team.** "Wukong's frame is 64% resolution-independent, so the effects may not scale and there is nothing to pin." Answer: then pinning costs nothing and gains nothing, and step 1 below kills it in a day.
7. **Maintenance.** 3–5 cvars per game, re-checked with a 30-minute timing run after each engine-version patch. Expect names to differ between Wukong's older UE5 and Stalker 2's 5.5.4.
8. **Falsification (5 days).** Wukong and Stalker 2.
   - Step 1: an RGP trace at 50/58/67%. **Kill** if the target passes change by less than 15% between 67% and 50%.
   - Step 2: a grid of {50, 58, 67}% × {pinned, unpinned}.
   - **Pass:** the pinned curve beats the unpinned one by ≥0.15 JOD at equal ms, or ≥1 ms at equal JOD, in ≥60% of clips.
   - **Kill:** <0.05 JOD or <0.3 ms.

### C. Viewing-condition-indexed profiles
1. **Pitch.** How much shadow, GI and fine detail is visible depends on room light and the brightness slider. The OLED has a "dual ambient light sensor" ([spec list](https://mp1st.com/?p=243098)). Choose one of 2–3 pre-validated profiles at launch.
2. **Already done?** SteamOS uses the light sensor only for adaptive brightness. Round 1 fed it into a Tier I VRS map; Round 2's E prices a single display model. I found no tool that picks render settings by viewing condition. Patents on light-sensor-driven display control exist (e.g. [US 8,734,247](https://patents.justia.com/patent/8734247)); I have not cleared the patent landscape.
3. **Mechanism.**
   - **Bright room:** reflected light (k·E/π) at k_refl 0.01 is 0.48 / 1.6 / 6.4 nit at 150 / 500 / 2000 lux. That raises the floor under the 0.5–5 nit shadows where High's GI and AO differ, so the bright profile cuts GI and shadows.
   - **Dark room, low slider:** fine-detail sensitivity drops (6.6× at 20 cpd going from 100 to 1 cd/m²), so the night profile cuts render scale instead.
   - **How it runs:** the sensor and backlight are read only (S0; sysfs path [could not verify]) and the profile is written through `deckforge.safety` **before launch only**.
4. **Tier.** S0 read + S1 write. Allowed for anti-cheat titles. Flag a small Wukong EULA §8.3 risk anyway.
5. **Budget (est., per condition bucket, not averaged over sessions).**
   - Bright: one GI step down, 1–4 ms.
   - Night: 50% → 42% render scale saves 3.3 ms (11.25 ms × (1 − 0.176/0.25)).
   - Overall: **0 / 2 / 4 ms** in the matched bucket.
6. **Red-team.** "This moves the goalpost room by room." Answer: claims are reported per pre-registered bucket, the strict bucket is the default and the headline, and profiles switch only at launch.
7. **Maintenance.** The profiles are extra outputs of the E pipeline. Fall back to the backlight value if the sensor path moves.
8. **Falsification (≤2 weeks, mostly offline).**
   - Day 1: re-score the Q1 clips at E_ambient {5, 150, 500, 2000}, measured k_refl, and peaks {40, 150, 600}. Continue only if ΔJOD falls ≥0.3 across the realistic range.
   - Then a 12-observer panel in a dark room and under a 500-lux lamp. **Pass:** the interaction is ≥0.3 JOD with the CI excluding 0.
   - **Kill:** either stage fails, or a 2-week sensor log of real play shows more than 80% of play time in one bucket.

---

## Q3. Should the target change?

**Possible wording (Fede decides).** "p99 frame time ≤33.3 ms on the pre-registered worst scene, and High-like per Q1 at 30 cm in the strict bucket. Label it 'Medium-plus, perceived within X JOD of High', never 'High'." For reference, the repo today says median ≤22.2 ms with max settings as the reference.

**Evidence that would justify the change:**
- The pilot shows High vs stock Medium is ≤1 JOD on this screen, i.e. the preset label is a poor stand-in for the look.
- A blind *play* panel prefers 30 fps Medium-plus over 40 fps/80 Hz or 45 fps Low-plus. It can only compare configurations the Deck runs live. Use [Denes et al. 2020](https://www.cl.cam.ac.uk/research/rainbow/projects/motion_quality_model/) to predict the result in advance.
- Keeping High as the anchor keeps the *look* target honest. **Dropping from 45 to 30 is a real concession**, and it stays one unless that play panel favours it.

**How to keep it honest:**
- Commit the thresholds, clips, conditions and analysis method before any candidate data exists.
- Hold out clips, report every anchor, and exclude the experimenter from the panel.
- A sceptic writes the kill thresholds.
- Keep reporting the 45 fps track.

**Is Wukong close?**
- 32 fps average = 31.25 ms. The 5th percentile of 28 fps = 35.7 ms, so at least 5% of frames miss 33.3 ms. At a 30 cap on the 90 Hz panel those frames slip to 44.4 ms: about 1.5 hitches per second.
- Gameplay 1% lows run 0.75–0.85× the average, so a clean lock needs about a 37.5 fps average (26.7 ms). That is a 4.6 ms (15%) cut.
- The plausible Tier S pieces are temporal cvars (~2 ms), mip bias (~0.6 ms) and Round 2's driver/translation-layer sweep (cluster F, ~0.5 ms), for a total of 3–4 ms. That reaches roughly 35–37 fps: **borderline**.
- The look is unmeasured. My prior (est.) is that FSR at 640×400 fails the 1-JOD worst-clip rule on fur and foliage; XeSS has a better chance but costs more ms. The benchmark tool is also a frozen pre-release build.

---

## Unknown unknowns
1. **Near-black on this panel.** If the slider crushes the lowest code values, High's deep-shadow GI is never displayed, and CVVDP's display model will mispredict it. Measure a 0–10% grey ramp with the colorimeter at 3 slider positions.
2. **There are two different "JOD"s.** CVVDP predicts fidelity against a reference; pwcmp scales no-reference preference. Averaging per-observer JODs and pooling answers give different pass rates: in my simulation, 7–15% false passes against a nominal 5%. Pre-register the method and calibrate the metric against humans per game.
3. **Who sits on the panel.** Testers from a QA background see TAA ghosting that casual players miss. Recruit them as a separate group and name the population in every claim. Passive viewing without a HUD is stricter than playing, so a pass is conservative, but a fail may be invisible in play.

## Questions for Fede (rule R4)
1. Is the reference the **High preset** (brief) or **max settings** (`QUALITY_TARGET.md`)?
2. Is the frame target a **45 fps median** (repo) or a **locked 30 floor** (brief)?
3. Is showing captures to friends on the bench Deck acceptable under the capture rules? (Not legal advice.)

## Claims dated after June 2026
- CVVDP v0.5.6 (Apple Silicon by default) and v0.5.7: checked in the local README.
- vkd3d-proton 0bb64c5 (14 Oct 2026): checked in the local clone.

## Key facts to keep
- P.913: 24 observers minimum, 35 for a narrow quality range.
- CGVQM has no display model.
- The High reference must be shown on the Deck as pre-rendered video.
- Clips must be analysed as a random factor; 16 clips × 24 observers is the floor.
- vkd3d-proton has no sampler mip-bias override (`resource.c:8537`).

Scripts used for the simulation: `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/r3psy/power.py` and `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/r3psy/power2.py`.

**Sources:** [CGVQM paper](https://arxiv.org/html/2506.11546v1) · [CGVQM repo](https://github.com/IntelLabs/CGVQM) · [ASAP](https://arxiv.org/pdf/2004.05691) · [Pinson 2014, P.913 observers](https://its.ntia.gov/publications/download/Pinson2014eLetter.pdf) · [UE command-line arguments](https://dev.epicgames.com/documentation/en-us/unreal-engine/command-line-arguments?application_version=4.27) · [UE screen percentage](https://dev.epicgames.com/documentation/en-us/unreal-engine/screen-percentage-with-temporal-upscale-in-unreal-engine) · [Deck OLED spec list](https://mp1st.com/?p=243098) · [Gigazine OLED review](https://www.gigazine.net/gsc_news/en/20240117-steam-deck-oled-review) · [US 8,734,247](https://patents.justia.com/patent/8734247) · [Denes 2020 motion-quality model](https://www.cl.cam.ac.uk/research/rainbow/projects/motion_quality_model/)
