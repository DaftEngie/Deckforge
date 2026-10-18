# Round 2 sceptic review: Cluster B, Replay Lab, Cluster H

**Short answer:** UE5 already does most of Cluster B inside the engine, and exposes it as cvars. A blind Vulkan layer under vkd3d-proton can't safely recover the dataflow it would need. The Replay Lab works only same-device, and the next Proton release will probably break it. Harvested GI is a research spike, not something to ship.

**Sources I read:**
- vkd3d-proton `0bb64c56` (2026-10-14), local copy at `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/src/vkd3d-proton`.
- GFXReconstruct `280a0ac` (2026-10-14), cloned to `/tmp/claude-0/-home-claude/bafac712-f1ea-5f41-b2ba-592b27d3cd05/scratchpad/gfxr.7O2E/gfxr`.

## B-S: UE5 temporal cvars in Engine.ini (Tier S)

### Is it already done? Mostly yes, inside the engine
- **Lumen surface cache.** It already runs on fixed per-frame budgets: 512² card-capture texels, 1024² direct-lighting texels and 512² radiosity texels per frame, with accumulation capped at 4 frames ([SIGGRAPH 2022](https://advances.realtimerendering.com/s2022/SIGGRAPH2022-Advances-Lumen-Wright%20et%20al.pdf)) [checked]. So it is already rate-divided.
- **The knobs exist** [checked, [Epic Lumen guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine)]:
  - `r.LumenScene.DirectLighting.UpdateFactor`
  - `r.LumenScene.Radiosity.UpdateFactor`
  - `r.Lumen.ScreenProbeGather.RadianceCache.NumProbesToTraceBudget`
  - `r.Lumen.ScreenProbeGather.DownsampleFactor` and `…IntegrateDownsampleFactor`
  - Whether they exist under these names in Wukong's and Stalker 2's older engine builds: [could not verify].
- **Virtual shadow maps.** Caching is on by default. The cost is dominated by pages that get invalidated. Skeletal animation, world-position-offset and pixel-depth-offset materials "always invalidate cached pages every frame" ([VSM doc](https://dev.epicgames.com/documentation/en-us/unreal-engine/virtual-shadow-maps-in-unreal-engine)) [checked]. So UE5 has no cascades to rate-divide. The real lever is foliage animated with world-position offset.
- **Clouds.** `r.VolumetricRenderTarget.Mode 2` traces 1 in 16 pixels per frame with temporal reprojection. That is the Horizon Zero Dawn trick, as a cvar ([Hillaire, Epic forum](https://forums.unrealengine.com/t/volumetriccloud/688516)) [checked].
- **Fog.** `r.VolumetricFog.HistoryWeight` defaults to 0.9 [forum-level only].

### Do the target games honour Engine.ini?
- **Wukong:** yes. `%LOCALAPPDATA%\b1\Saved\Config\Windows\Engine.ini`, users confirm their edits work ([Steam](https://steamcommunity.com/app/2358720/discussions/0/6149189044493378916)) [checked].
- **Oblivion Remastered:** turning Lumen off through the ini works ([overkill.wtf](https://overkill.wtf/elder-scrolls-oblivion-remastered-best-settings-steam-deck)) [checked].
- **Stalker 2:** the path is known and ini tools exist, but nobody confirms a cvar actually took effect [could not verify].
- **Lock-down pattern:** Silent Hill 2 rewrites Engine.ini unless the file is read-only ([Steam](https://steamcommunity.com/app/2124490/discussions/0/4700161008286832258)).
- I found no evidence that Wukong or Stalker 2 lock it down.

### The "54–66% resolution-independent" claim
- It is arithmetic on an assumption, not a measurement (1_console_port.md:9–13). I reproduce 54.6% and 66% from the assumed 25–35% fixed share.
- The assumption is weak for UE5:
  - Nanite targets about one triangle per pixel.
  - VSM chooses shadow resolution from "the resolution implied by the camera's perspective projection" (VSM doc).
  - Screen probes are placed per pixel.
  - So much of what Round 1 called "culling and shadow geometry" shrinks with resolution.
- If half of the assumed fixed work actually scales with resolution, the fixed share is 34–43% (est.).
- I found no public per-pass profile of a UE5 game on the Deck or a similar small RDNA2 GPU [could not verify].
- The only Deck data point: Oblivion Remastered with Lumen diffuse GI off gained +5–10 fps (author-reported, no frame-time log). At a 25–30 fps base that is about 5–11 ms (my arithmetic).

### Budget (est., temporal knobs only)
- **Pessimistic 0.5 / central 2 / optimistic 4 ms.** Round 1 claimed 5–7 ms.
- This is the same search space as Cluster E, so count it once.
- It drops to zero if H turns Lumen off.

### Ways it fails
- GI lagging behind doors opening and torches.
- Lighting pops on fast camera turns.
- Patches renaming cvars, or the game overwriting the ini.
- CPU-bound scenes, where GPU savings don't become fps.

**Verdict: SURVIVES WITH CHANGES.** Merge it into E as the "temporal" axis, and tie its claims to the intercept measurement in F1.

## B-I: the Vulkan-layer Pass Interleaver and related ideas (Tier I)

### What vkd3d-proton actually gives a layer [checked in source]
- **Barriers carry almost no dataflow.** UAV barriers collapse into one global memory barrier with no resource attached (`libs/vkd3d/command.c:14147–14192`). Transitions that don't change layout are global too (`command.c:14137`).
- **Descriptor copies are invisible.** `CopyDescriptorsSimple` is a CPU `memcpy` into mapped descriptor buffers (`device.c:6021–6067`). No Vulkan call happens.
  - To recover what a dispatch reads and writes, the layer would have to hook `vkGetDescriptorEXT` to build a bytes-to-view map, read heap memory at submit time, and reflect the SPIR-V for static indices.
  - Shader Model 6.6 dynamic heap indexing defeats all of that.
  - My CPU cost estimate on the Zen 2 is 0.5–2 ms per frame (est.). Round 1 assumed 0.1–0.3 ms.
- **Placed buffers are slices of one heap allocation** (`resource.c:4782`), addressed by GPU virtual address. Un-aliasing outputs means tracking address ranges, not handles.
- **Debug markers reach Vulkan only with `VKD3D_CONFIG=debug_utils`** (`device.c:63`, `command.c:17870`). Whether shipping builds emit them at all: [could not verify].

### Skipping a dispatch but keeping its barriers corrupts state
- **Stale producer outputs.** A skipped pass may have written indirect arguments, tile lists or counters that a kept pass reads.
- **Re-allocated persistent memory.** Kept passes re-allocate surface-cache pages and VSM page tables, so stale writes land in reassigned pages. The result is corruption, not just staleness.
- **Misregistered screen-space outputs.** A screen-space result reused without reprojection is one frame out of place: about 19 px during a 20°/s pan at 45 fps.
- **Consequence:** only whole subgraphs (from the clear to the final write) of world-space caches can be skipped. In UE5 those are exactly what the budget cvars already control, with the engine's priority logic intact. **For UE5 the layer is strictly dominated by Tier S.**

### Precedent
- Skipping by shader hash from outside the engine exists: 3DMigoto's `handling = skip` ([guide](https://github.com/rayshire/3dmigoto/blob/main/Guides/UsageInstructions.md)), and ReShade draw-skip add-ons ([ShaderToggler](https://github.com/FransBouma/ShaderToggler/wiki)).
- Both remove passes outright. I found no precedent for rate-dividing a pass from outside an engine.

### The other ideas in the cluster
- **Far-cascade rate division:** UE5 uses VSM, so there are no cascades to divide. Monster Hunter Wilds already has an in-game "Distant Shadow Quality" setting, which is Tier S ([deltiasgaming](https://deltiasgaming.com/monster-hunter-wilds-best-settings-for-1440p)).
- **Exact memo:** proving inputs are unchanged means hashing everything the pass reads, which costs about as much as the tiny passes it would skip (≤0.3 ms est.).
- **Learned pass skipping:** in UE5, the screen-probe downsample cvars dominate it. Elsewhere it hits the same identification wall, plus 0.4 ms for the correction network.
- **Async history refinement:** it saves no milliseconds. At the 15 W cap, "idle" ALUs aren't free. It belongs with Cluster D.

### Rescue tried
I tried two rescues: engine-aware hooks (REFramework for RE Engine, UE4SS for UE) instead of a blind layer, and hand-curating one world-space subgraph per game, located with a Radeon GPU Profiler (RGP) trace. The only thing that survives is a gated research spike on one non-UE game with no anti-cheat (Alan Wake 2 or Monster Hunter Wilds).

**Verdicts:**
- Pass Interleaver: SURVIVES WITH CHANGES (non-UE only, curated subgraphs, gated by F3).
- Far-cascade division: DEAD.
- Exact memo: DEAD.
- Learned pass skipping: DEAD for UE5; folded into F3 elsewhere.
- Async history refinement: defer to D.

## Replay Lab

### What works and what doesn't
- **Round 1's plan to replay with `-m rebind` is [contradicted].**
  - GFXReconstruct handles VK_EXT_descriptor_buffer only non-portably, through opaque capture data (`framework/encode/vulkan_capture_manager.cpp:912–975`).
  - It warns that `-m rebind` "[is] currently not supported for VK_EXT_descriptor_buffer → Replay is likely going to fail" (`framework/decode/vulkan_replay_consumer_base.cpp:14276`).
  - So capture and replay must happen on the same Deck with the same Mesa build.
- **The next Proton release probably breaks capture.**
  - RADV enables VK_EXT_descriptor_heap by default from Mesa 26.2 ([Phoronix, 2026-08-05](https://phoronix.com/news/Mesa-26.2-Released)) [checked].
  - vkd3d-proton's CHANGELOG.md:5 says 3.0.1 is "likely the last release before VK_EXT_descriptor_heap lands". Today it is opt-in (`device.c:144`) or switched on per game (`device_workarounds.c:134,225`).
  - GFXReconstruct has no descriptor-heap entry points in its generated code.
  - Captures could fail silently. **Pin the Proton/vkd3d-proton version for the Lab.**
- **Wine and the default memory tracker clash.** Wine owns the SIGSEGV signal, which GFXReconstruct's default `page_guard` mode also uses. Use `userfaultfd` mode instead. It uses `UFFD_USER_MODE_ONLY` (`page_guard_manager_uffd.cpp:529`), so no system setting needs changing.
- **Capture size and the 16 GB of RAM (est.):**
  - A trimmed capture's starting snapshot is roughly the game's resident GPU memory, 3–6 GB, plus 20–80 MB of changes per frame. 300 frames would be 9–30 GB.
  - Shadow copies of mapped memory push the Deck toward swap.
  - Use 60–120-frame trims, `GFXRECON_CAPTURE_USE_ASSET_FILE`, and an external SSD.
- **Fidelity limit:** replay freezes the engine's CPU-side feedback decisions, such as Lumen card requests and VSM page requests. The Lab will therefore be optimistic about any skip policy, and results must be confirmed live.

### Cheaper default for timing (Tier S)
- Wukong's standalone Benchmark Tool, which should be deterministic enough; whether it honours Engine.ini: [could not verify].
- `MESA_VK_TRACE=rgp` with `MESA_VK_TRACE_TRIGGER` ([Mesa docs](https://docs.mesa3d.org/envvars.html)) gives per-dispatch timing with no capture layer, including for anti-cheat games.

**Verdict: SURVIVES WITH CHANGES.** Same device, no rebind, pinned Proton, userfaultfd, short trims. RGP plus benchmark tools are the default; use GFXReconstruct only where determinism is needed.

## H: Harvested GI

### What the game looks like with Lumen off
- Epic: at Low, Lumen is off and "only unshadowed skylight is used", at 0.7× intensity [checked].
- In Wukong, Low GI makes "a dimly fire-lit cave look like an overcast outdoor scene" ([TechSpot](https://www.techspot.com/guides/2884-wukong-optimization/)) [checked].
- So interiors are not pitch black. They are leaky and flat.
- **Design consequence:** H must also remove the unshadowed sky lighting, or it double-counts. It must also replace Lumen's reflections, which fall back to the sky cubemap.
  - Doing that needs the composite pass identified, which is the same wall as B-I.
  - Or it needs a sky-light cvar that may not exist in UE 5.0/5.1 [could not verify].

### Can Lumen's diffuse indirect buffer be isolated?
- Not by name in shipping builds.
- It can be done on a PC with RenderDoc by hand: find the G-buffer, depth and diffuse-indirect targets, and pull the camera matrices from the view constant buffer.
- That is manual reverse engineering, repeated for every patch.

### What Lumen costs on low-end RDNA2
No per-pass measurement found. The only data point is the Oblivion Remastered anecdote above.

### Do the data sizes make sense?
- The spherical-harmonics payload is plausible: 1.2e7 probes × 12 B = 144 MB per basis element.
- The leak prevention the design depends on ("depth moments") is not budgeted. DDGI-style visibility at ≥144 B per probe (est.) gives 1.7–12 GB, which is 3–20× the 0.6 GB claimed.
- Rescue: 8-bit per-octant visibility masks plus a coarse harvested occupancy grid (≤50 MB est.). This accepts some leaking through thin walls.

### Already done elsewhere
Current Unreal ships "Irradiance Field Gather" for Medium GI (Epic guide), which is engine-native probe GI for low-end hardware. It isn't in Wukong's or Stalker 2's engine versions [version not stated in the doc].

### Budget (est.)
- Saves Lumen's cost (5–11 ms, from the anecdote), minus 0.3–0.7 ms to apply the probes, minus 0.5–1 ms for the reflection and sky fix.
- Net 3–9 ms against Lumen at High. Against Medium GI the gain may be less than half of that.

### Legal (I am not a lawyer; this is a cautious reading)
- Probe data is a fixed, concrete encoding of part of the game's displayed lighting, built to recreate it when combined with the game.
- That is closer to *Micro Star v. FormGen* than to *Galoob*. In *Micro Star*, level files that described the game's audiovisual displays were held to be derivative works ([154 F.3d 1107](https://law.resource.org/pub/us/case/reporter/F3/154/154.F3d.1107.html)).
- "Facts" about a fictional world can still infringe (*Castle Rock*, [150 F.3d 132](https://law.resource.org/pub/us/case/reporter/F3/150/150.F3d.132.97-7992.html)).
- Game EULAs add contract risk on top.
- Distributing the data needs publisher permission. Having each user harvest locally carries less risk but needs a high-end PC per user.

### Tier
Capture is Tier I (on a PC). Applying the probes on the Deck is Tier I (a layer pass). Only turning Lumen off in the ini is Tier S.

**Verdict: SURVIVES WITH CHANGES.** Research only. Compare against Medium GI, not Low. Budget the visibility data. No distribution without a licence.

## Claims dated after June 2026
- RADV enabling VK_EXT_descriptor_heap by default in Mesa 26.2: [checked]. Whether SteamOS 3.8 ships Mesa 26.2 or later: [could not verify].
- vkd3d-proton descriptor heaps opt-in as of 2026-10-14: [checked in source].
- GFXReconstruct has no descriptor-heap support as of 2026-10-14: [checked].
- Epic's guide mentioning Switch 2 and Irradiance Field Gather: [checked the text; it doesn't state the engine version].
- No other post-June claims fall in my clusters.

## Falsification experiments
All on the bench Deck OLED at 15 W, GPU clock pinned, 5 runs per setting, 95% confidence intervals.

**F1. Fixed-cost intercept plus Tier S temporal knobs (5 days)**
- Games: Wukong Benchmark Tool, and Stalker 2 on a fixed save and route. DeckForge writes Engine.ini through `deckforge.safety`.
- Steps:
  1. Run at four render scales (50/60/70/85%) and fit GPU ms against pixel count. The intercept is the resolution-independent cost.
  2. Compare Lumen GI and reflections off vs on.
  3. Try each temporal knob alone, then combined.
- Quality: lossless 1280×800 capture, scored with ColorVideoVDP using the Deck display model, against Cinematic.
- **Pass:** the combined knobs save ≥2.0 ms at ≤0.25 JOD loss.
- **Kill:** <1.0 ms saved, or GPU busy below 90% (the scene is CPU-bound).
- The "54–66%" figure is killed if intercept/total at 960×600 is below 40%.
- Owner by hand: install the games and the benchmark tool, start the runs, and confirm the ini took effect with an `r.ScreenPercentage` change he can see.

**F2. Replay Lab viability (5 days)**
- Setup: Proton 11 pinned with vkd3d-proton 3.0.x, `userfaultfd` mode, 120-frame trimmed captures of the Wukong benchmark and Alan Wake 2.
- **Pass:** three replays produce identical frame hashes, and replay GPU ms per frame is within ±5% of a live RGP trace of the same frames, with no out-of-memory.
- **Kill:** both titles fail.
- Owner by hand: press the capture trigger and plug in an external SSD.

**F3. Tier I subgraph gate (10 days, after F2)**
- In Alan Wake 2 or Wilds, use RGP to find one world-space-cache subgraph.
- Skip it on odd frames during replay, under the Khronos validation and synchronization validation layers.
- Then run a 10-minute live soak.
- **Pass:** ≥1.5 ms saved, ≤0.25 JOD loss on pan clips, zero validation errors, zero hangs, and layer CPU overhead ≤0.5 ms.
- **Kill:** anything short of that.
- Owner by hand: start the soak and report any crash.

**F4. Harvested GI (10 days)**
- Days 1–2, on the Deck: measure frame-time differences between GI High, Medium and Low.
  - **Kill:** High minus Low is under 3 ms, or Medium is within 1.5 ms of Low.
- Days 3–10, on a PC only:
  1. Take a RenderDoc capture of one Wukong cave.
  2. Build probes with visibility masks.
  3. Composite offline at 960×600 upscaled to 800p.
  - **Pass:** at least +0.5 JOD over Medium GI, at no more than Low's cost plus 1 ms (the apply shader timed on the Deck).
  - **Kill:** anything short of that, or extrapolated data over 2 GB per game.
- Owner by hand: nothing on the Deck after day 2.

## Verdict table
| Idea | Verdict |
|---|---|
| B-S: UE5 temporal cvars | SURVIVES WITH CHANGES (merge into E; 0.5 / 2 / 4 ms) |
| Pass Interleaver (layer) | SURVIVES WITH CHANGES (non-UE, curated subgraphs, F3 gate) |
| Far-cascade rate division | DEAD |
| Exact memo | DEAD |
| Learned pass skipping | DEAD for UE5; folded into F3 elsewhere |
| Async history refinement | Not a frame-time saver; defer to D |
| Replay Lab | SURVIVES WITH CHANGES |
| H: harvested GI | SURVIVES WITH CHANGES (research only, no distribution) |

## What would change my mind
- **B-S:** F1 shows an intercept of at least 55% and the knobs save at least 3 ms at ≤0.25 JOD.
- **Pass Interleaver:** a clean ≥1.5 ms UE5 subgraph that no cvar reaches, or shipping builds turning out to carry debug markers (RGP showing pass names with `VKD3D_CONFIG=debug_utils`).
- **Far-cascade division:** a target game with stable cascaded shadows, far cascades costing at least 1.5 ms, and no in-game setting for them.
- **Exact memo:** an RGP trace showing at least 1 ms per frame of byte-identical passes.
- **Learned pass skipping:** a non-UE pass of at least 3 ms that can be skipped with a correction costing no more than 0.4 ms.
- **Async refinement:** at least 1 ms of idle ALU time at 15 W with no clock drop.
- **Replay Lab:** GFXReconstruct adding descriptor-heap support and a portable rebind for descriptor buffers.
- **H:** written publisher permission plus an F4 pass.

**Worth saving to the project:** GFXReconstruct can't do portable (`-m rebind`) replay with descriptor buffers and has no descriptor-heap support. The next vkd3d-proton release will likely switch to descriptor heaps, so the Replay Lab must pin the Proton version.
