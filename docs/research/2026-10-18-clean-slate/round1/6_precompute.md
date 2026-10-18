# Offline precomputation for DeckForge: "do it once, ship the result"

**The core asymmetry.** Every Steam Deck OLED has the same silicon, the same driver stack and the same 1280×800 panel, held at roughly the same distance. That is about 43 px/deg at 30 cm (est., my arithmetic: a 15.9 cm wide panel spans 29.8°). So one offline measurement holds for millions of devices. A PC vendor can't do this because its hardware varies too much. Consoles do it, but by hand.

**Legal rule I applied throughout: ship recipes and measurements, never derivatives of code or assets.**
- Fossilize databases contain the game's own SPIR-V shader code. The [Fossilize README](https://github.com/ValveSoftware/Fossilize) says they hold "deflated varint-encoded SPIR-V".
- So DeckForge must not redistribute `.foz` files or compiled caches. Valve ships them under its Steam agreements; we have no such agreement.
- What DeckForge ships is keyed by hashes. Any transform is applied on the Deck, to the user's own installed copy.

---

## 1. Shader recipes tuned on fixed silicon (Tier S)
**Pitch:** Valve's pre-caching for speed instead of stutter. We tune the hot shaders once on a farm of Decks, then ship a small table of hashes and transforms.

**Mechanism:**
1. Take an RGP capture on a Deck (Mesa supports this) and rank pipelines by GPU time. The top ~30 are likely about 80% of the frame (est.).
2. Search offline, on 2–4 Decks replaying GFXReconstruct captures, over these transforms:
   - wave32 vs wave64 per shader;
   - loop unrolling and spirv-opt passes;
   - **specialising on uniforms that never change:** constant-buffer values that crowd telemetry shows are the same in every session (quality flags, feature toggles) get folded into the shader as constants, behind a guard branch.
3. Ship each result as a pair: (BLAKE3 hash of the shader, list of transforms).
4. On the Deck, set `MESA_SPIRV_DUMP_PATH` to dump the user's own shaders, apply the recipe locally, and load the result with `MESA_SPIRV_READ_PATH`. Mesa 25.3+ supports this, matched by BLAKE3 hash ([Mesa docs](https://docs.mesa3d.org/spirv/index.html), [Phoronix](https://www.phoronix.com/news/Mesa-SPIR-V-Shader-Replacement)).

**Why it beats the wall:** PC drivers can't afford a per-shader search for every GPU model. The Deck is one GPU model.

**Budget:**
- Savings: 3–8% of GPU time (est.), which is 0.7–1.8 ms of a 22.2 ms frame.
- Data: about 500 entries × 64 B ≈ 32 KB per game per build.
- Compute: 30 shaders × 20 variants × 3 scenes × 30 s ≈ 15 Deck-hours per build.

**Prior art:**
- Valve and RADV developers have discussed per-game performance profiles and driver-side shader replacement, comparing it to what Windows vendors do ([Phoronix](https://phoronix.com/news/Mesa-RADV-More-Per-Game-Tuning)).
- RADV's wave32 switches today are global environment variables only ([Phoronix](https://www.phoronix.com/news/RADV-Vulkan-More-Wave32-Shaders)).
- Google's MLGO uses machine learning for compiler decisions ([arXiv](https://arxiv.org/abs/2101.04808)).

**Tier:** S. It is a launch-option environment variable at driver level and loads nothing into the game. For anti-cheat games, use only exact transforms that don't change the image. No FP16 demotion.

**Patches:** Shaders are matched by hash. A changed shader misses and gets the stock compile, which is safe.

**Falsification (≤2 weeks):** Stalker 2 plus one RE Engine game, top 20 pipelines, brute-force search with clocks locked. **Kill if** median whole-frame GPU time improves by less than 2% across 3 scenes.

**Biggest risk:** Mesa's docs say replacement needs `MESA_SHADER_CACHE_DISABLE=1`, which brings back stutter. A possible workaround is to pre-warm a separate `MESA_SHADER_CACHE_DIR` by running `fossilize_replay` with the replacements switched on. This is untested.

## 2. Perceptual knob atlas: a learned "skip map" (Tier S, plus a Tier I variant)
**Pitch:** A machine-searched Pareto front over hundreds of hidden engine variables and individual render passes, scored against the Deck's own display. It is not a settings guide.

**Mechanism:**
1. For each UE5 `r.*` variable (set in Engine.ini `[SystemSettings]`) and each render pass, try it off, at half resolution and at half rate.
2. Score each change with [ColorVideoVDP](https://github.com/gfxdisp/ColorVideoVDP), configured for a 7.4" 1280×800 OLED at 30 cm, against a max-settings reference.
3. Measure the milliseconds saved on the Deck farm.
4. Use Bayesian optimisation to find the best combinations.
5. Ship the result in one of two forms:
   - **Tier S:** a per-game ini profile.
   - **Tier I:** a per-pass schedule run by a Vulkan layer. The layer either skips a dispatch and writes a neutral value, or runs the pass every second frame and reprojects using the game's motion vectors, like a video codec's P-frames.

**Why it beats the wall:** Menu presets bundle passes with very different costs and are tuned for TVs. The Deck's display and viewing geometry are the same for every player, so one perceptual model fits everyone.

**Budget:**
- Savings: 2–6 ms (est.).
- Data: 2–20 KB per game.
- Compute: 500 knobs × 3 levels × 5 scenes × 60 s ≈ 125 Deck-hours for the first pass.

**Prior art:** NVIDIA GeForce Experience computed "optimal settings" per hardware configuration in its lab, but without perceptual metrics ([PCWorld](https://www.pcworld.com/article/456298/nvidia-s-audacious-attempt-to-make-life-easier-for-pc-gamers.html)).

**Tier:** S for config files (allowed for anti-cheat games). I for the pass schedule.

**Falsification:** Black Myth: Wukong with 150 variables. **Kill if** the best profile doesn't beat the best menu preset by at least 0.5 JOD at equal milliseconds, or by at least 2 ms at equal JOD.

**Biggest risk:** Shipping builds that ignore variables, and ColorVideoVDP disagreeing with human judgement on stylised content.

## 3. Per-game distilled reconstruction network (Tier I; weaker Tier S variant)
**Pitch:** A specialist upscaler trained on a single game, about 3× cheaper than a generalist for the same in-game quality.

**Mechanism:**
- Distil a teacher (FSR4/DLSS-class output, or a 64-frame jittered accumulation) into a ~150k-parameter INT8 student that uses the Deck's dot4 instructions. Optional small per-biome heads.
- **Tier I:** the inputs (colour, depth, motion vectors, jitter) come through [OptiScaler](https://github.com/optiscaler/OptiScaler), with the student added as a new backend.
- **Tier S, for anti-cheat games:** a spatial-only network running in gamescope on the final frame. It is weaker without depth and motion vectors.

**Budget:**
- **FSR2 on the Deck:** about 2 ms (est.). Scaled from 1.3 ms at 1080p Quality on an RX 590 ([FSR2 README](https://github.com/GPUOpen-Effects/FidelityFX-FSR2)).
- **FSR4 INT8 on the Deck:** about 5.5–7 ms (est.).
  - Scaled from 3.93 ms at 1080p on a 24-CU BC-250 ([Guru3D](https://www.guru3d.com/story/optimized-fsr-4-nearly-halves-upscaling-time-on-amd-repurposed-bc250-mining-board/)).
  - Consistent with the ~10 fps loss reported on the Deck ([Club386](https://www.club386.com/?p=117457)).
- **INT8 peak:** 8 CUs × 64 lanes × 4 MACs × 1.6 GHz = 3.3 TMAC/s (est.).
  - At 35% utilisation for 2 ms, that is about 2,250 MAC per output pixel.
  - FSR4's implied cost is about 7,000, so the student must be roughly 3× cheaper.
- **Payoff:** suppose the student at 50% render scale (0.256 Mpx) matches FSR2 at 67% (0.455 Mpx).
  - Resolution-dependent work drops 44%.
  - If that work is 15 ms of the frame, the saving is ~6.6 ms. The upscaler cost is about the same, so net ~6 ms (est.).
- **Data:** about 150 KB per game.

**Prior art:**
- DLSS 1.0 was trained per game and was dropped for a generalised DLSS 2 ([AnandTech](https://www.anandtech.com/show/15648)). The trade-off differs here because compute is the binding constraint on the Deck.
- NAS shipped per-video super-resolution models over a CDN and reported +43% QoE ([OSDI'18](https://www.usenix.org/conference/osdi18/presentation/yeo)).
- Intel trained a network on G-buffers harvested from GTA V without source code ([arXiv](https://arxiv.org/abs/2105.04619)).

**Legal:** A 150 KB set of weights can't contain gigabytes of textures. A UK court held that model weights are not an "infringing copy" ([Mayer Brown](https://www.mayerbrown.com/insights/publications/2025/11/getty-images-v-stability-ai-what-the-high-courts-decision-means-for-rights-holders-and-ai-developers)). US law is unsettled and EULAs add risk, so get publisher non-objection before distributing.

**Patches:** Retrain only when the game's look changes. Run a ColorVideoVDP regression on a fixed clip set for each new build.

**Falsification:** One game, 10 held-out clips. **Kill if** the student at 50% scores below FSR2 at 67%, or costs more than 2.5 ms on the Deck.

**Biggest risk:** Ghosting on content the student never saw.

## 4. Harvested GI: "photogrammetry of light" (Tier I, UE5)
**Pitch:** Turn Lumen off on the Deck and replace it with irradiance harvested from the game's own max-settings output.

**Mechanism:**
1. **Capture**, on contributors' PCs and only for games without anti-cheat:
   - A capture layer reads Lumen's diffuse-indirect buffer, plus depth, normals and the view matrices, with free-camera fly-throughs via [UE4SS](https://github.com/UE4SS-RE/RE-UE4SS).
   - The irradiance is splatted into sparse world-space probe bricks, DDGI-style ([JCGT](https://jcgt.org/published/0008/02/01/)).
2. **Time of day:** GI is linear in its light sources. So we capture a basis (sky plus the sun at K points along its arc) and blend at runtime, as in precomputed radiance transfer ([Sloan 2002](https://dl.acm.org/doi/10.1145/566654.566612)).
3. **On the Deck:**
   - Disable Lumen with `r.DynamicGlobalIlluminationMethod=0` in Engine.ini (this part is Tier S).
   - A layer adds one compute pass after the G-buffer: albedo × the probe's spherical-harmonics value, added to scene colour, plus cheap SSAO.

**Budget:**
- **Lumen's stated budget:** 4 ms at 1080p for 60 fps on consoles ([Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine)).
- **Scaled to the Deck:** 6.3× less compute and 4.4× less bandwidth, at 0.28× the pixels (960×600). That gives 4.9–7.1 ms, plus fixed costs, so ~5–9 ms (est.).
- **Lookup cost:** about 28 B/px × 0.58 Mpx = 16 MB, which is 0.16 ms at peak bandwidth; 0.3–0.7 ms including SSAO. Net saving 4.5–8 ms (est.).
- **Data:**
  - Open world: 1.2e7 probes × 12 B = 144 MB per basis element; 13 elements, compressed to 4 with PCA, is about 0.6 GB.
  - Linear games: 0.1–0.3 GB.
  - Streamed, with about 10–30 MB resident.

**Prior art:**
- ReShade RTGI injects GI after the fact from the depth buffer ([ReShade](https://reshade.me/forum/shader-discussion/5450-guide-to-ray-tracing-with-reshade)).
- "Playing for Data" intercepted GTA V's buffers ([arXiv](https://arxiv.org/abs/1608.02192)).

**Patches:** Data is keyed by Steam build ID. Each brick stores depth moments; if what the Deck sees doesn't match, it falls back to SSGI and reports the mismatch.

**Legal:** We ship lighting measurements, not meshes or textures. Never decrypt pak files. Ask the publisher before distributing.

**Falsification:**
- **Day 1:** measure Deck frame time with Lumen on and off. **Kill if** the difference is under 3 ms.
- **Week 2:** harvest one Wukong area. **Kill if** harvested GI scores less than 0.5 JOD above "Lumen off + SSAO".

**Biggest risk:** Dynamic lights, losing Lumen reflections (they would need SSR instead), and per-version matrix extraction.

## 5. Shadow PVS (Tier I, non-GPU-driven engines)
**Mechanism:**
- Offline, for each 10 m camera cell and each sun-angle bin, record which shadow-pass draws produce at least one visible shadow texel at 800p, using receiver masks ([Bittner 2011](https://dcgi.fel.cvut.cz/en/publications/2011/bittner-i3d-scc/)).
- Ship compressed bitsets, as Quake did with its PVS.
- A layer skips draws in that set, taking the union with neighbouring cells to stay conservative.

**Budget:**
- Shadow passes cost 2–4 ms (est.). Culling 20–40% of them saves 0.4–1.6 ms, plus vkd3d-proton CPU time.
- Data: 40k cells × 8 bins × 20k draws = 800 MB raw. With 20–50× RLE compression, 16–40 MB (est.).

**Falsification:** RenderDoc captures at 20 locations. **Kill if** casters that never contribute account for less than 15% of shadow-pass time.

**Biggest risk:** Instancing and indirect draws make draw identity unstable; Nanite and virtual shadow maps make this not applicable.

---

## Candidates I rejected
- **Precompiled shaders:** Valve already ships Deck caches, and DeckForge cannot legally ship `.foz` files.
- **Precomputed LODs and re-encoded textures:** these are derived assets. LOD bias is already a variable in idea 2's search space.
- **Offloading CPU work:**
  - The CPU work that is the same for every player (shader compiles, decompression) is either already done by Valve or locked inside files protected by anti-tamper.
  - AI, physics and animation differ per player, so they can't be precomputed.
  - CPU-bound titles need something else.

## Unknown unknowns
1. **Custom drivers lose Valve's cache.** A custom Mesa build or separate cache directory forfeits Valve's pre-cache, which is keyed by driver build. The cost is first-run stutter in every game.
2. **Proton updates break shader hashes.** vkd3d-proton updates change the SPIR-V it emits, so hashes churn with Proton versions, not just game patches. Key recipes on the DXIL hash as well.
3. **The two OLED models differ optically.** The etched anti-glare glass and the glossy glass may need different perceptual profiles. Measure MTF with a camera.
4. **Hand-held distance is not fixed.** At 30 cm vs 40 cm the Deck is 43 vs 57 px/deg. Both are below the eye's limits of 94 px/deg for achromatic and 53 for yellow-violet detail ([arXiv](https://arxiv.org/abs/2410.06068)). So "the small screen hides it" is weaker than intuition suggests; measure real viewing distances.
5. **At the 15 W cap, saved GPU time may not become fps.** The power controller may hand the saved GPU power to the CPU. Measure fps at a fixed TDP, and measure watts.
   - Separately, server-side hotfixes that don't change the build ID can make harvested data stale.
