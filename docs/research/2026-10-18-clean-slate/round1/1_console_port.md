# Console-port lens: what a port team does, done from the API stream

## Budget frame: why port teams cut fixed budgets, not pixels (all est.)
- **Hardware ratio.** PS5 is 10.28 TF against the Deck's 1.64 TF, so **6.3×** more compute. Bandwidth is 448 GB/s against ~80 GB/s achievable on the Deck, so **5.6×** more. The ~80 figure comes from Chips and Cheese, who measured >70 GB/s on the LCD Deck's 88 GB/s bus, scaled up to the OLED's 6400 MT/s. ([C&C](https://chipsandcheese.com/p/van-gogh-amds-steam-deck-apu))
- **Reference frame.** A PS5 60 fps UE5 frame is 16.6 ms at 1080p internal. Known pieces of it:
  - Lumen GI + reflections + fog: **4 ms** ([Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine))
  - Nanite VisBuffer **~2.5 ms** and materials **~2.1 ms** at ~1404p ([Karis 2021](https://advances.realtimerendering.com/s2021/Karis_Nanite_SIGGRAPH_Advances_2021_final.pdf))
  - TSR: **1.5 ms** ([Epic](https://dev.epicgames.com/documentation/en-us/unreal-engine/temporal-super-resolution-in-unreal-engine))
- **Scaling to the Deck.** Rendering at 960×600 means 3.6× fewer pixels than 1080p. Pixel-proportional work therefore costs 6.3/3.6 ≈ 1.75× its PS5 time. Resolution-independent work still costs the full 6.3×. That covers surface-cache texel budgets, culling and shadow geometry.
- **Result.** If 25–35% of the PS5 frame is resolution-independent:
  - 25%: 12.45×1.75 + 4.15×6.3 ≈ **48 ms**
  - 35%: 10.8×1.75 + 5.8×6.3 ≈ **55 ms**
  - In both cases **54–66% of the Deck frame is work that does not shrink when you lower resolution.** Port teams fix exactly that, by changing how often things update. From outside the game, the only generic way to cut a fixed budget is to run the pass less often.
- **What the ideas below add up to.** About 9–14 ms (est., not fully additive). That turns "High at ~19 fps" into roughly 28–33 fps at a High-like look. Getting a native 45 fps at High is beyond pass-level tricks alone.

---

## 0. Foundation (not ranked): Replay Lab
- **Pitch:** Capture 10 s of real gameplay once. Replay it deterministically on the Deck thousands of times with different per-pass policies, score each one, and ship only the winning policy (hashes and rules, no assets).
- **Mechanism:**
  - Capture with GFXReconstruct below vkd3d-proton/DXVK. Replay with `gfxrecon-replay -m rebind`, which handles buffer-device-address rebinding ([LunarG 2025](https://www.lunarg.com/improving-replay-portability-initial-support-for-buffer-device-address-rebinding-in-gfxreconstruct/)).
  - A thin DeckForge layer applies the policy during replay. Per-pass timestamps measure the cost; RADV's Radeon GPU Profiler support gives deeper traces ([MR 3900](https://gitlab.freedesktop.org/mesa/mesa/merge_requests/3900)).
  - Each pass is identified by its shader hash, the same key Mesa 25.3 SPIR-V replacement uses ([BLAKE3](https://www.phoronix.com/news/Mesa-SPIR-V-Shader-Replacement)) and the one vkd3d-proton's `VKD3D_SHADER_OVERRIDE` uses ([README](https://github.com/HansKristian-Work/vkd3d-proton)). Dispatch size and image formats are added to the key.
- **Why it matters:** Live games are not deterministic. A 0.3 ms gain only becomes measurable above the noise on a deterministic replay.
- **Cost:** No runtime cost. Captures are several GB and contain game assets, so they stay local and are never uploaded.
- **Tier:** I during capture, so only non-anti-cheat games can be captured. Policies for anti-cheat games can only be checked by live A/B.
- **Falsify:** Capture 300 frames from two D3D12 titles. Pass if two replays are pixel-identical and replay GPU ms is within ±5% of live.
- **Biggest risk:** vkd3d-proton streams (sparse resources, descriptor buffers) may not replay.

---

## 1. Pass Interleaver: rate-divide the fixed-budget passes
- **Pitch:** Run expensive, temporally filtered passes every 2nd or 3rd frame, interleaved so frame time stays flat. This is the port team's "update fraction" knob applied from the command stream.
- **Mechanism:**
  - The layer rebuilds each frame's pass graph (dispatch groups between barriers, inputs and outputs from descriptor writes).
  - **Candidates:** compute passes whose outputs are images (never buffers or indirect arguments) and whose consumers also read an image written in the previous frame, which marks them as history accumulators.
  - **On "off" frames:** the layer drops those dispatches, keeps the barriers, and leaves the outputs intact.
  - **Guard (a), un-aliasing:** vkd3d-proton's placed resources share device memory, so the layer detects overlapping memory binds and gives pinned outputs their own memory.
  - **Guard (b), knapsack scheduling:** candidates are split into groups A/B (or A/B/C) of equal milliseconds, so even and odd frames cost the same.
  - **Exact-memo mode:** if push constants, uniform-buffer bytes and inputs hash the same as last frame, the pass is skipped with no quality loss. Typical hits are sky/atmosphere lookup tables and static probes.
- **Why it beats the wall:**
  - The budgets are sized for a 10 TF GPU and are fixed per frame. Lumen captures 512² card texels and lights 1024² direct-lighting texels every frame.
  - The results are already accumulated over at least 4 frames, and Lumen caps probe accumulation at 4 ([SIGGRAPH 2022](https://advances.realtimerendering.com/s2022/SIGGRAPH2022-Advances-Lumen-Wright%20et%20al.pdf)).
  - So the signal changes far more slowly than 22.5 Hz, and sampling it at half rate loses little.
- **Budget (est.):**
  - Candidate set ≈ 10–14 ms. Lumen's resolution-independent part is ~1.2×6.3 ≈ 7.6 ms; volumetrics, AO, SSR and clouds add 2–4 ms.
  - Half rate saves **5–7 ms**; one-third rate saves 6.7–9 ms.
  - Costs: 0.1–0.3 ms of CPU for stream filtering and +10–40 MB of memory for un-aliased outputs.
  - Fewer GPU-busy milliseconds lets the GPU clock down or frees watts for the CPU. The 16 W budget is shared, and the GPU can draw >10 W (C&C).
- **Prior art:**
  - Horizon Zero Dawn clouds went from 20 ms to ~2 ms by updating 1/16 of pixels per frame ([Schneider 2015](https://www.advances.realtimerendering.com/s2015/The%20Real-time%20Volumetric%20Cloudscapes%20of%20Horizon%20-%20Zero%20Dawn%20-%20ARTR.pdf)).
  - Reverse reprojection caching ([Nehab 2007](https://gfx.cs.princeton.edu/pubs/Nehab_2007_ARS/NehEtAl07.pdf)).
  - GTAO reaches 0.5 ms on console by spreading work spatially and temporally ([Activision](https://research.activision.com/publications/archives/atvi-tr-16-01practical-realtime-strategies-for-accurate-indirect-occlusion)).
  - I know of no one doing this from outside the engine. It is novel and unproven.
- **Tier:** I. Applies to Wilds, Stalker 2, Wukong, AW2. For UE5, the same knob already exists as Engine.ini cvars (`r.LumenScene.Radiosity.UpdateFactor` etc.), which are Tier S. Use those first.
- **Falsify:** In the Lab, take the top-15 compute passes in Wilds and Stalker 2 and replay candidate sets at half rate. Measure ms saved and ColorVideoVDP (CVVDP) JOD on walking and fast-pan clips. **Kill** if no set gives ≥3 ms at ≤0.25 JOD loss in both titles.
- **Biggest risk:** Some outputs are not truly temporal and get corrupted. View-relative froxel fog smears on fast pans.

---

## 2. Shading-rate governor inside RADV
- **Pitch:** Turn Valve's existing Van Gogh forced-VRS plumbing, already on by default, into a per-pipeline-class, content-aware and motion-aware policy. Effectively Radeon Boost VRS, open source, in the driver.
- **Mechanism:**
  - **Already there:** RADV loads a forced VRS rate dynamically in every vertex shader on Van Gogh, controlled through `RADV_FORCE_VRS_CONFIG_FILE` ([MR 14713](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/14713), [envvars](https://docs.mesa3d.org/envvars.html)).
  - **Class rules, set at pipeline creation:**
    - blended pipelines with no depth write (particles) → 2×2
    - full-screen-triangle blur chains → 2×2
    - the final pass and UI → 1×1
    - opaque materials → attachment-image rate
  - **Attachment VRS:** on GFX10.3 RADV implements it by copying into the depth buffer's HTILE ([MR 10187](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/10187), [MR 26025](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/26025)). The rate image is built from the previous frame's luma contrast, following [VALAR](https://intel.com/content/www/us/en/developer/articles/technical/velocity-luminance-adaptive-rasterization-vrs-tier.html) or [FidelityFX VS](https://gpuopen.com/manuals/fidelityfx_sdk/techniques/variable-shading/).
  - **Motion gate:** a daemon reads stick/gyro magnitude and writes the config file.
  - **New (unproven) temporal dither:** alternate 1×1 and 2×2 per tile per frame, so the game's TAA/FSR builds back near-full detail on static content.
- **Why it beats the wall:**
  - One Deck pixel is 0.125 mm, or 1.43 arcmin at 30 cm. That is 42 px/deg, with a Nyquist limit of 21 cycles/deg, where contrast sensitivity is ~10× below its peak (est.).
  - VRS keeps edges at full rate and coarsens only interior shading.
  - In a 20°/s pan on a 45 Hz OLED that holds each frame, eye-tracking smear is 20×0.022 = 0.44° ≈ 18 px, so 2×2 is invisible in motion.
- **Budget (est.):** Pixel-shader-bound work ≈ 5–7 ms.
  - Static scenes: 0.4×1.5 (translucency) + 0.3×2.2 (materials) + 0.5×1 (post) ≈ **1.8 ms** saved.
  - Pans: 0.45×6 ≈ **2.7 ms** saved.
  - Costs: rate image 0.1–0.2 ms. No memory.
- **Prior art:**
  - Blanket `RADV_FORCE_VRS=2x2` gave +8% overall on desktop RDNA2 at 4K ([Phoronix](https://www.phoronix.com/review/radeon-radv-vrs)).
  - AMD Radeon Boost VRS is input-gated and driver-level on RX 6000, covering 28 titles. AMD claims +27% in Fortnite and +49% in BL3 ([AMD](https://www.amd.com/en/products/software/adrenalin/radeon-boost.html)).
  - VALAR: up to 1.12× at 4K, evaluated with FLIP.
  - The Coalition's Gears games moved to Tier 2 VRS ([blog](https://devblogs.microsoft.com/directx/gears-vrs-tier2/)).
  - Marek Olšák's VRS fixes land in Mesa 26.2 ([Phoronix](https://phoronix.com/news/Marek-Double-VRS-RADV-Perf)).
- **Tier:** S through env var/driconf today, and through upstream Mesa that Valve ships later. A side-loaded custom driver is in-process, so treat it as Tier I for anti-cheat titles until it is upstream. Works for raster-heavy games and is weak for compute-shaded ones.
- **Falsify (1 day, no code):** In 5 games, toggle the config file between 1x1 and 2x2 and read GPU ms. Blanket 2×2 is the ceiling for any governor. **Kill** if it saves <1.5 ms in ≥4 of 5 games.
- **Biggest risk:** The ceiling is low on compute-heavy renderers such as Nanite.

---

## 3. Far-cascade rate division plus exact shadow memo
- **Pitch:** Re-render the near shadow cascades every frame and the far ones every 2nd or 4th frame. Skip local shadow maps whose inputs are byte-identical to last frame.
- **Mechanism:**
  - A shadow pass is a depth-only render pass whose image is later sampled with a compare-enabled sampler, so it is easy to identify.
  - Cascades are successive layers or viewports of the same image.
  - Schedule: C0 and C1 every frame; C2 on even frames; C3 on frame 1 mod 4, interleaved so they don't land on the same frame.
- **Why it beats the wall:** Engines use stable cascades: fitted to a sphere and snapped to texels ([MS](https://learn.microsoft.com/en-us/windows/win32/dxtecharticles/cascaded-shadow-maps)). Rotating the camera doesn't change them, and moving shifts them in whole texels. A far-cascade texel (~10 cm, est.) projects to less than one pixel at 800p, so a cascade 1–3 frames stale is invisible.
- **Budget (est.):** Cascaded shadows cost 4–6 ms on the Deck reference. With 6 ms split 20/25/25/30%: 1.5×½ + 1.8×¾ ≈ **2.1 ms**, plus 0–1 ms from the memo.
- **Prior art:**
  - Cyberpunk 2077 refreshes distant shadows "every few seconds", spread across frames, and throttles local shadow refreshes ([SIGGRAPH 2021](https://history.siggraph.org/wp-content/uploads/2022/06/2021-Talks-Dybisz_Shadows-Optimizations-in-Cyberpunk-2077.pdf)).
  - Insomniac's CSM scrolling ([Acton 2012](https://advances.realtimerendering.com/s2012/insomniac/Acton-CSM_Scrolling(Siggraph2012).pdf)).
  - UE5's virtual shadow maps already cache, so little to gain there.
- **Tier:** I. Applies to cascaded-shadow engines such as RE Engine. Not Space Marine 2 (Easy Anti-Cheat).
- **Falsify:** In the Lab, test walking, mounted and time-of-day clips. **Kill** if it saves <1 ms or JOD drops by more than 0.2.
- **Biggest risk:** Engines that re-fit cascades every frame (not stable) will show swimming far shadows.

---

## 4. Per-shader FP16 demotion found by search
- **Pitch:** The driver compiles chosen hot shaders with 16-bit math, picked per shader hash by measurement rather than by hand.
- **Mechanism:**
  - RDNA2 runs packed FP16 at 2× rate and halves register use for 16-bit values.
  - A RADV compiler pass, enabled per shader hash, demotes float math to 16-bit. It excludes anything that flows into positions, depth or large-texture UVs, found by tracing data flow back from those outputs.
  - ACO, RADV's shader compiler, already emits packed instructions.
  - Targets: tonemap, bloom, DOF, TAA and lighting shaders, chosen from GPU-profiler data.
- **Why it beats the wall:** Color shown on an 8–10-bit 800p panel doesn't need 23-bit mantissas.
- **Budget (est.):** About 4 ms of ALU-bound shaders made 20–25% faster saves **~0.8–1 ms**, up to ~2 ms where register pressure limits occupancy.
- **Prior art:**
  - AMD reported 20–25% on converted rendering steps ([AnandTech](https://at-web1.www.anandtech.com/show/11717/the-amd-radeon-rx-vega-64-and-56-review/4)).
  - Frostbite's FP16 shader work ([GDC 2024](https://gdcvault.com/play/1034306/FP16-Shaders-in)).
  - Mesa's Freedreno driver already lowers reduced-precision math to fp16 by default (its `nofp16` flag is in the envvars doc).
- **Tier:** S as a driver build, with the same caveat as idea 2.
- **Falsify (3 days):** Profile the top-20 shaders. **Kill** if most show <50% ALU busy, i.e. they are memory-bound. Otherwise hand-convert three via `MESA_SPIRV_READ_PATH` and measure.
- **Biggest risk:** Most shaders may be memory-bound on a 1 MB L2. Banding near black, which the OLED's true blacks make more visible.

---

## 5. Bandwidth diet: format demotion and off-screen transparency
- **Pitch:** Cut bytes, not pixels.
- **Mechanism:**
  - **(a) Format demotion:** RGBA16F intermediates whose alpha is never read (checked by SPIR-V reflection) are created as B10G11R11 instead. Each one is validated in the Lab.
  - **(b) Off-screen particles:** blended draws after the lighting pass go to a half-res target with a max-depth downsample, then get a bilateral composite ([GPU Gems 3 ch. 23](https://developer.nvidia.com/gpugems/gpugems3/part-iv-image-effects/chapter-23-high-speed-screen-particles)).
- **Why it beats the wall:** The GPU has ~80 GB/s. The CPU gets only ~25 GB/s on the same shared bus (C&C), so bytes saved on the GPU may also help CPU-bound games.
- **Budget (est.):**
  - One full-screen RGBA16F read+write = 1.024M px × 16 B = 16.4 MB ≈ 0.2 ms. 8–12 such passes cost 1.6–2.5 ms; demotion saves **0.8–1.2 ms**.
  - 8 layers of particle overdraw ≈ 131 MB ≈ 1.6 ms. Half-res plus composite ≈ 0.6 ms, saving **~1 ms** in heavy-VFX scenes.
- **Tier:** I.
- **Falsify:** **Kill** if the Lab shows <0.7 ms saved or a JOD drop >0.2.
- **Biggest risk:** B10G11R11 has no sign bit and a 6-bit mantissa, which can shift hues. Soft-particle shaders that rely on screen position break at half res.

---

## Unknown unknowns
1. **Where the anti-cheat line really is.** Gamescope's WSI is already an implicit Vulkan layer in every game ([VK_LAYER_FROG_gamescope_wsi](https://deepwiki.com/ValveSoftware/gamescope/4.1-vulkan-wsi-layer)), and Mesa itself runs in-process. Find out what Easy Anti-Cheat and BattlEye on Proton actually check by asking the vendors, never by probing.
2. **Shader pre-cache misses.** Driver-side policy, and possibly the env vars themselves, may change RADV's pipeline cache keys. That would make Steam's precompiled Deck shaders miss, causing compile stutter that ruins 1% lows. Measure on a first boot.
3. **Single-frame metrics are misleading for temporal tricks.** TAA clamping turns stale data into flicker, not blur. Use CVVDP on sequences with fast pans, not FLIP on stills.
4. **OLED near-black.** Coarse shading and FP16 banding show up more in dark scenes (AW2, Wilds caves) on this panel than on LCD benches. Test on the Deck screen itself.
5. **Named passes might be free.** Check with the profiler whether shipping builds still carry debug markers that vkd3d-proton forwards (unverified). If they do, passes come with names like "Lumen.ScreenProbeGather" and hash heuristics become unnecessary.
