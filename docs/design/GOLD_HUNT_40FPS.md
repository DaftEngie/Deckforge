# Gold hunt: what could get Wilds and Space Marine 2 to 40 fps

Status: **PROPOSED**, 2026-10-11. This is a catalog of techniques, not a plan of record.
It answers Fede's question: *"The target I want is 40 fps. What other techniques can better
distribute resources to gain a couple more frames while keeping image quality good? Can we
really not optimize the shaders? Look at the device, at modern games, at how developers
optimize for weak hardware. There might be gold hiding somewhere."*

**Evidence.** Four research notes in `docs/research/2026-10-11-gold-hunt/`:

| Cited as | File | Question |
|---|---|---|
| [ports] | `impossible_ports.md` | What did Switch, Switch 2, iPhone and Series S ports cut, and what can an outside tool copy? |
| [engines] | `re_engine_swarm_low_end.md` | Hidden or low-end paths in RE Engine (Wilds) and Swarm (Space Marine 2) |
| [shaders] | `shader_optimization_outside.md` | Can shaders be optimized from outside a shipped game? |
| [bandwidth] | `rdna2_apu_bandwidth.md` | Memory-bandwidth and chip-level levers on the Deck's APU |

Earlier work this builds on: `INVENTIONS.md` (PR #6, branch `design/native-inventions`) and
`STRATEGY_OPTIONS.md` / `LAUNCH_FLOW.md` (PR #2, branch `design/overnight-rethink`).

**Labels:**
- **(est.)**: my estimate or inference, not a measurement.
- **UNPROVEN**: nobody has shown it working.
- **[checked]**: I confirmed it myself in source code or on the primary page (section 12 lists
  what and where).
- "none found": the research found no example. That is not proof that none exists.

---

## 1. The short answer

**What 40 fps means on the Deck.** 40 fps is 25 ms per frame. It only paces evenly at **80 Hz**
(each frame shown for exactly two refreshes). At 90 Hz it judders, because 90 ÷ 40 is not a whole
number. The OLED panel runs 45–90 Hz, so 80 Hz is available. Optional 2× frame generation would
present 80 fps at 80 Hz.

**The baseline moved since INVENTIONS was written.** Capcom's 2026 patches added a CPU tab, three
new fog levels below the old Low, and mesh LODs [engines §5, checked]. Wilds then became **Steam
Deck Verified on 20–21 August 2026**, holding "30 FPS and above most of the time" at default
settings, with visuals that look "pixelated and blurry" [engines §5, checked]. INVENTIONS used
January 2026 numbers (high teens to low 20s in open areas). Those are probably stale, and **the
first test is to re-measure** (Y0, section 10).

**Honest verdicts (est., to be tested):**

| Scene | Today (best evidence) | 40 fps? |
|---|---|---|
| Wilds, field and combat (mostly GPU-bound) | ~30 fps, about 33 ms | **Plausible, unproven.** Needs Tier I levers. Tier S alone very unlikely (section 8) |
| Wilds, hubs such as the Grand Hub (CPU-bound) | No Deck number. An 8-core Zen 4 handheld drops to ~30 there [engines §5, checked] | **Very unlikely.** The Deck's CPU is much weaker |
| Space Marine 2, interiors and quiet sections | 20–30 fps on 2024 builds; no recent Deck numbers [engines §11]. INVENTIONS cited 14–24 fps from another source | **Maybe**, using the game's own dynamic-resolution target |
| Space Marine 2, hordes (CPU-bound) | Low 20s on 2024 builds; 8-core consoles fall below 40 [engines §8, §11] | **No** with Tier S tools |

Per rule R1, "40 in the field, 30 in hubs and hordes" is a better result to promise than a
40 everywhere that we can't deliver.

**Can we really optimize the shaders? Yes, and the hook already exists.** Proton's D3D12
translator (vkd3d-proton) can load our own version of any game shader, keyed by a fingerprint of
the original. A second switch changes how individual shaders are compiled, with no shader writing
at all. Both are plain launch options [checked]. Nobody has published a *performance* use of
them in a shipped game. That is the main gold here (section 3). It is Wilds-only (Tier I), and a
realistic gain is 5–10%, not 30% (est.).

## 2. How "impossible ports" are made, and what we can copy

Port teams follow the same three steps [ports §1]:
1. render at roughly 25–45% of the output's pixels and reconstruct the image;
2. remove "second-order" lighting: AO, GI, volumetrics, reflections, depth of field;
3. trim shadows, foliage, draw distance and textures.

Their biggest single wins were not settings. They were **algorithm rewrites** (Saber rewrote
Witcher 3's grass and sun shadows to go from 10 to 30 fps on Switch) and **quarter-resolution
transparency** (Doom 2016 on Switch) [ports §1, §2].

| Port trick | Precedent | What DeckForge can do from outside | Tier |
|---|---|---|---|
| Very low internal resolution plus strong reconstruction | RE Engine on Switch 2 handheld at **360p** with DLSS (Street Fighter 6, RE Requiem); RE4 on iPhone at ~360p with MetalFX [ports §1, engines §6] | The Deck has neither DLSS nor MetalFX. FSR from below ~540p looks much worse. Better reconstruction is the open research track (QUALITY_TARGET lever 1, DeckSR, X7) | S (game upscaler) / I (OptiScaler) |
| Remove second-order lighting | Street Fighter 6 handheld drops AO, volumetrics, SSR, DoF [ports §1] | Wilds menu; REFramework for GI (DPGI) and below-menu cuts [engines §3] | S / I |
| Distant characters animate less often | Hogwarts on Switch; SF6 animates distant characters at ~20 fps [ports §4, engines §6] | **Wilds now has this officially**: the CPU tab reportedly includes "frame skips" for distant animation (option names unconfirmed) [engines §5] | S |
| Cap the number of small creatures | Witcher 3 tried −30% NPCs, then **reverted it because the world felt empty** [ports §1] | Wilds CPU tab reportedly caps small creatures [engines §5]. Use as a last resort | S |
| Dynamic resolution to hold the frame rate | Every Switch port; Wilds on consoles [ports §1, engines §1] | Space Marine 2 has a "Dynamic Resolution FPS Target" [engines §9]. Wilds on PC has none we know of; see the dormant-feature check (section 5) | S / I |
| Quarter-resolution particles and depth of field | Doom 2016 on Switch [ports §5] | **No external precedent found.** Per-pass VRS (INVENTIONS) is the nearest stand-in | I |
| Algorithm rewrites | Witcher 3 grass and sun shadows [ports §1] | Only through shader surgery (section 3), and only for loops and constants, not whole new algorithms | I |
| Cutscenes at a lower frame rate for higher resolution | Doom Eternal on Switch: cutscenes at 20 fps [ports §1] | Scene-aware targets (section 6) | S |

## 3. Gold nugget 1: shader surgery without forking Proton

INVENTIONS assumed port surgery would need our own fork of vkd3d-proton (decision N3). It doesn't,
at least for the first experiments. Released vkd3d-proton already has three switches, read from
environment variables (so they can go in a Steam launch option):

| Switch | What it does | Checked |
|---|---|---|
| `VKD3D_SHADER_DUMP_PATH` | Saves every shader the game creates, named by a 64-bit fingerprint of its original bytecode | [checked] master; [shaders §1] |
| `VKD3D_SHADER_OVERRIDE` | If a file named after a shader's fingerprint exists in that folder, loads it instead of the game's shader | [checked] master, v3.0, v3.0.1 |
| `VKD3D_SHADER_QUIRKS` | A text file mapping fingerprints (or ranges) to compile options: wave size (`FORCE_MAX_WAVE32`, `FORCE_MIN_WAVE32`, `DEBUG_FORCE_MIN_WAVE64`), tessellation caps (`LIMIT_TESS_FACTORS_4…32`), and more. No shader writing needed | [checked] master, v3.0, v3.0.1 |

**Why this matters.** It turns "AI writes cheaper shaders" into a concrete, measurable loop:
1. **Capture** a fixed scene on the Deck: an RGP GPU profile (`MESA_VK_TRACE=rgp` with a file
   trigger, so no keyboard press is needed mid-game), a shader dump, and per-shader register
   statistics (`RADV_DEBUG=shaderstats`) [shaders §4].
2. **Rank** the passes by GPU time and label each one: memory-bound, ALU-bound, latency-bound or
   output-bound.
3. **Try the cheap switches first**: wave size or tessellation caps through the quirks file.
4. **Then edit constants** in the hottest shaders: sample counts (AO, blur, shadow filtering),
   ray-march steps (fog), loop bounds. Edit by decompiling to GLSL, changing the number,
   recompiling and validating, with every binding kept identical [shaders §8].
5. **Score every variant automatically**: per-frame and temporal image metrics over several
   scenes, plus frame time measured on the Deck at the real power limit. Fede's blind A/B makes
   the final call (QUALITY_TARGET.md).
6. **Pin** each recipe to the game build, the Proton version and the shader fingerprint. If any of
   them changes, the recipe switches itself off and reports "dropped", never "passed".

**What the research says about gains:**
- Classic automatic shader simplification: 1.6–2.5× on complex shaders, in lab conditions with
  full source code [shaders §5].
- AMD on 16-bit math (FP16): about 10% on Vega when the engine was written for it [shaders §3].
  vkd3d-proton already uses native 16-bit wherever the game asks for it, so there is little left
  to take for free.
- Halving a sample or step count saves roughly 30–50% of that one pass when the pass is
  memory-bound (est.) [shaders §8].
- **Frame-level math (est.):** cutting 40% from a 3 ms pass saves 1.2 ms, about 5% of a 25 ms
  frame. Doing that to two or three hot passes gives roughly 5–10%.

**AI's role, honestly.** Recent results shrink a lot under strict checking.
- KernelBench-Verified (2026): the best model's speedup fell from 1.43× to 0.88× once realistic
  baselines and hidden inputs were used. Some "speedups" returned the input unchanged
  [shaders §5].
- In a rendering-kernel study, a model deleted a loop it judged redundant and broke the image
  [shaders §5].

So the AI proposes *which constants to try*, and the harness decides. That matches rule R2.

**Caveats:**
- The vkd3d-proton README calls these switches "only meant to be used by vkd3d-proton
  developers". They could change without notice [shaders §1].
- A replacement can break silently in two ways [shaders §6]:
  - A game patch recompiles a shader. Its fingerprint changes, and our version simply stops
    applying. Safe, just lost gain.
  - A Proton update changes how shaders are wired. Our old version still loads but may be bound
    wrong. Unsafe: corruption or a GPU hang. This is why recipes pin the Proton version.
- Using the override or dump switch makes vkd3d-proton ignore the game's own cached shader
  translations [checked]. Expect extra compiling on the first run.
- RE Engine keeps its own `shader.cache2`, which a RenoDX mod tells users to delete when
  installing [shaders §6]. Needs checking for Wilds.
- **Tier I, Wilds only.** These switches don't inject anything into the game, but they change
  the code the GPU runs. That is exactly what anti-cheat watches for. Never for Space Marine 2
  or Helldivers 2 (decision T3).

**Prior art:** none found for performance. RenoDX and 3DMigoto replace shaders by fingerprint for
HDR and fixes. RenoDX added an AI-agent bridge (MCP) for inspecting and hot-loading shaders in
2026 [shaders §2]. DeckForge would be first-of-kind for **measured performance** recipes under
Proton (est.).

## 4. Gold nugget 2: driver switches that cost no image quality

These change how the GPU driver lays out memory or schedules work, never what is drawn. Each is a
launch option, so it is free to try and free to undo.

| Switch (launch option) | What it changes | Evidence | Expected (est.) |
|---|---|---|---|
| `radv_prefer_2d_swizzle_for_3d_storage=true` | Stores 3D compute textures (typical for volumetric fog) in a 2D memory layout | Mesa's own per-game tuning: "+15% FPS" in Total War: ROME and a "much faster" fog pass in Ghost Recon Breakpoint. In Mesa 26.0 and 26.1, and any Mesa option can be set by an environment variable of the same name [checked]. Mesa's comment calls it "really just a heuristic" that depends on how the game reads the texture [checked] | 0–5%, could be slower. Only matters if Wilds' fog uses 3D storage textures (likely, unproven) |
| `RADV_PERFTEST=cswave32` | Runs compute shaders 32 threads wide instead of 64 | Wave32 gave +12.5% for ray tracing on desktop RDNA2 [shaders §3]. No game numbers for compute | ±5%. Can break shaders that assume 64-wide groups [bandwidth §6] |
| `VKD3D_CONFIG=single_queue` | Turns off async compute and puts all work on one queue | No Deck measurements. On an 8-unit, bandwidth-limited GPU, overlap may not help [bandwidth §5] | ±5% |
| `VKD3D_CONFIG=no_staggered_submit` | Turns off a software scheduling trick that "may regress GPU performance in some cases" | vkd3d-proton 2.14 notes [bandwidth §5] | ±5% |
| `radv_enable_unified_heap_on_apu=true` | Reports all shared memory as one GPU heap, which changes the game's texture budget | Enabled for one game (RDR2) [bandwidth §4] | Texture quality and stutter, not fps |

**An upstream gift.** If any of these clearly helps Wilds, the same setting can be proposed to
Mesa as a built-in Wilds profile. Every Deck owner would then get it automatically, with credit to
DeckForge. This posts publicly, so it needs Fede's yes (decision T5).

**Bandwidth tricks: fool's gold** [bandwidth §1–§4]. The OLED has 16% more memory bandwidth than
the LCD model, and it measured only 2–9% faster. So the GPU is only partly bandwidth-limited, and
cutting memory traffic buys a fraction of the saving. At 800p, demoting render-target formats or
forcing compression is worth about 0–2% for high risk. See section 9.

## 5. Gold nugget 3: what Wilds itself now offers, and what may be dormant inside it

**New official levers (Tier S)** [engines §5, checked]:
- **Volumetric fog: five levels.** The old Low became High, and Medium, Low and Lowest are new.
- **CPU tab.** Capcom says it adjusts "settings related to CPU load". Community reports name frame
  skips and a small-creature cap; not confirmed officially.
- **Mesh LODs and spawn optimizations** (Ver.1.041, February 2026).

**One lever closed.** Capcom now forces Wilds' own variable-rate shading **off whenever an
upscaler is on**, "to maintain proper effect visuals" [checked]. Two consequences:
- INVENTIONS test X4 ("Wilds' own VRS setting") only applies at native resolution now.
- The driver can still force coarse shading (`RADV_FORCE_VRS`). Capcom's reason is a warning
  that it may look bad with upscaling.

**Below-menu values (Tier I, REFramework)** [engines §3]. Mods expose values the menu doesn't:
- shadow resolution below the lowest preset;
- clutter culling;
- mesh, foliage and texture LOD bias;
- particle density;
- turning ambient GI (DPGI) off.

The gains are claimed as "significant" but nobody measured them. The image cost is real: pop-in,
missing clutter, flat lighting.

**Dormant console features: a hypothesis (UNPROVEN).** Wilds on consoles uses dynamic resolution
[engines §1]. Fog levels below the PC menu existed in the PC build before Capcom exposed them
[engines §3, §7]. If the console dynamic-resolution code also ships in the PC build, a
REFramework script could switch it on. That would give Wilds the single most common port trick:
resolution drops only in heavy moments, so quiet scenes stay sharp. **Checking costs about 30
minutes** with REFramework's object explorer (Y3). None found so far.

**Texture pre-decompression (Tier I).** Wilds decompresses textures on the GPU. A community tool
stores them uncompressed instead (+17 GB on disk). It removed camera-pan micro-stutter on an
RTX 4060 [engines §4]. On the Deck's 8 compute units, that decompression competes directly with
rendering. Expect better 1% lows rather than a higher average (est.). This is INVENTIONS'
"decompression routing" add-on (X8) in a simpler form.

## 6. CPU-bound scenes: hubs and hordes

GPU tricks do nothing when the CPU is the limit. The Deck has 4 Zen 2 cores sharing a 15 W budget
with the GPU. The levers that remain:

| Lever | Tier | Game | Evidence |
|---|---|---|---|
| CPU tab (distant-animation frame skip, small-creature cap) | S | Wilds | Official tab; option effects unmeasured [engines §5, §13] |
| `ParallelBuildProcessorCount` 4–8 in `config.ini` | S | Wilds | "Same or slightly smoother, lower CPU load" at 4 on a Deck (claimed). Values above 8 hurt some users [engines §2] |
| Newer Proton (less translation overhead) | S | Both | Valve recommends Proton Experimental for Wilds [engines §5]. Newer vkd3d-proton builds reduce CPU overhead, but no numbers are published [bandwidth §7] |
| Power steering: cap the GPU clock so the CPU gets more of the 15 W | S | Both | INVENTIONS invention 3, test X3. In GPU-heavy scenes the CPU drops to 2–3 W [bandwidth §8] |

**Scene-aware targets.** Doom Eternal on Switch ran cutscenes at 20 fps to look better [ports §1].
The DeckForge version: **40 fps in the field, 30 fps in hubs**. The catch is pacing:

| Frame rate | Paces evenly at | Shares a refresh rate with |
|---|---|---|
| 45 fps | 90 Hz | 30 fps |
| 40 fps | 80 Hz | nothing useful in 45–90 Hz (the next step down is 26.7 fps) |
| 30 fps | 90 Hz (or 60 Hz) | 45 fps |

So switching between 40 and 30 means switching the panel between 80 and 90 Hz. Whether that
blinks on the OLED is unknown; test Y4 checks it in five minutes. If it blinks, the choice is:
- 40 at 80 Hz with uneven hubs;
- or 45/30 at 90 Hz.

## 7. Space Marine 2 (Tier S only, Easy Anti-Cheat)

- **The settings files are reportedly encrypted** and keyed to each other. Editing or restoring
  one file fails, and Steam Cloud reverts changes [engines §9]. Only user reports; not confirmed.
  **Impact on Phase 1:** the scanner may find these files, but DeckForge must treat them as
  back-up-only, never edit them (a spec amendment for later).
- **`SteamDeck=1`** (set automatically on a Deck) only selects a Low preset and a 30 fps cap. No
  hidden Deck tier was found [engines §10, ports §3].
- **Usable levers:**
  - the in-game menu, especially the **Dynamic Resolution FPS Target**, which could hold 40 in
    GPU-bound scenes;
  - FSR 3.1;
  - Cloth Simulation Low;
  - SSR off;
  - frame cap and refresh rate;
  - power steering.
- **Hordes** are limited by enemy count on the CPU. An 8-core PS5 drops below 40, and no setting
  changes enemy count [engines §8, §13].
- The driver switches in section 4 are launch options, which CLAUDE.md lists as Tier S. Whether
  they are allowed for an anti-cheat game is decision T3. Shader replacement never is.

## 8. Budget math to 25 ms

All gains below are **(est.)**, made up from the evidence ranges above. They multiply rather than
add. Example: two 10% cuts give 1 − 0.9 × 0.9 = 19%, not 20%.

**Wilds field (GPU-bound). Start ~33 ms (30 fps); need ~25% off for 40 fps:**

| Lever | Tier | Low | Mid | High |
|---|---|---|---|---|
| New official settings beyond the Verified defaults (fog Lowest, shadow-cache A/B, filtering) | S | 0% | 4% | 10% |
| Driver switches (section 4) | S | 0% | 3% | 8% |
| Power steering (watts to the GPU) | S | 0% | 2% | 5% |
| REFramework below-menu cuts | I | 3% | 8% | 15% |
| Shader surgery on 2–3 hot passes | I | 0% | 5% | 10% |
| **Tier S only, combined** | | 0% | **9% → ~33 fps** | 21% → ~38 fps |
| **Tier S + I, combined** | | 3% → ~31 fps | **20% → ~38 fps** | 40% → ~50 fps |

Reading: with Tier S alone, 40 in the field looks out of reach. With Tier I the middle case lands
just short, at about 38 fps. Reaching 40 needs better-than-middle results, or a small resolution
drop, which is where image quality starts to suffer.

**Wilds hubs (CPU-bound).** There is no Deck measurement. The available evidence points to 30
fps or below: the 8-core handheld result and a January 2026 Deck report of large areas at ~25 or
lower [engines §5]. Getting to 25 ms needs 25–40% off the CPU's time. The CPU levers in section 6
add up to about 15% in the middle case (est.). **40 in hubs: very unlikely.**

**Space Marine 2.** Interiors: the dynamic-resolution target may hold 40 by trading resolution.
Hordes: no.

## 9. Fool's gold: ruled out or pushed down the list

| Idea | Why not (for now) |
|---|---|
| Render-target format demotion (16-bit → 11/10-bit colour) | ~0.5–2% at 800p behind FSR. High risk: banding, no negative values, aliased memory [bandwidth §2] |
| Forcing memory compression (DCC) on more textures | Unknown sign (−3% to +3%). Changes memory layout under the game [bandwidth §3] |
| `RADV_TEX_ANISO` to cap texture filtering | Also *raises* filtering on samplers the game set to none. Not a clean cap [bandwidth §4] |
| UMA frame buffer 4 GB | Stability and texture budget, not fps. It is a BIOS setting the user changes, not DeckForge (R7) [bandwidth §4] |
| Memory or fabric clock control | Memory clock can't be set on this chip. Fabric clock is firmware-level and off-limits (R7) [bandwidth §8] |
| Skipping Wilds' safety workarounds in vkd3d-proton | Risks GPU page faults or hangs. Valve added them for a reason [bandwidth §9] |
| Free-form AI shader rewrites | 0.88× under strict checking; known image-breaking edits [shaders §5] |
| Generic "half-resolution particles" layer | No precedent. Breaks on depth, blending and memory aliasing [ports §5] |
| Cutting crowds or monsters hard | Witcher 3's port reverted it because the world felt empty [ports §1] |
| Old Deck config packs ("Little Engine that Shouldn't") | Marked obsolete by its author after the 2026 patches [engines §2] |

## 10. Tests

These extend the X-tests in INVENTIONS section 7. Under rule R7, every Deck test is run by Fede
by hand, or later by the bench runner, never from a dev session.

| # | Test | Where | Time | Decides |
|---|---|---|---|---|
| **Y0** | Re-baseline Wilds on the current build: Verified defaults and the 2026 Lowest preset; field, combat and Grand Hub; uncapped frame time | Deck | One evening | Every number in section 8. Should run before X1 |
| **Y1** | The section 4 driver switches, one at a time, in the same field scene | Deck | One evening | Free zero-image-cost gains (extends X8) |
| **Y2** | New official levers one at a time: fog Lowest, each CPU-tab option, `ParallelBuildProcessorCount` 4/6/8, shadow cache on/off; field and hub | Deck | One evening | Best Tier S baseline for Wilds |
| **Y3** | Search REFramework's object explorer for a dynamic-resolution component in Wilds | Deck | ~30 min | Whether external dynamic resolution is possible |
| **Y4** | Switch the refresh rate 80 ↔ 90 Hz while playing; does the screen blink? | Deck | 5 min | Whether scene-aware 40/30 targets are viable |
| **Y5** | Shader-hook smoke test: (a) shader dump works for Wilds under the Deck's Proton; (b) a no-op override (the dumped shader fed back unchanged) loads and runs; (c) an RGP capture works on the Deck's chip | Deck | One evening | Whether X1 and shader surgery can start without a fork |
| **Y6** | Space Marine 2: dynamic-resolution target 40 + FSR 3.1 at 80 Hz, interior vs horde; power steering in a horde | Deck | One evening | Realistic Space Marine 2 target |

## 11. Decisions for Fede

| # | Decision | Recommendation |
|---|---|---|
| **T1** | Change the native target from a locked 45 fps (22.2 ms, 90 Hz) to a locked **40 fps (25 ms, 80 Hz)**. That means amending decision 0001, QUALITY_TARGET.md and CLAUDE.md, in a small separate PR | Yes, you asked for it. I'll prepare that PR once you confirm |
| **T2** | Allow **scene-aware targets**: 40 where the GPU is the limit, 30 accepted where the CPU is (hubs, hordes) | Yes, subject to Y4. It is honest (R1) and copies a real port trick |
| **T3** | Classify launch-option switches: switches that only change driver performance (section 4) are **Tier S**, allowed for Space Marine 2. Shader dump, override or quirk files are **Tier I**, never for anti-cheat games | Yes. Nothing is injected and nothing drawn changes. The anti-cheat risk is unknown but low (est.) |
| **T4** | Run port-surgery experiments on stock vkd3d-proton switches first. Decide on a fork (N3) only if they hit a limit | Yes. This defers the fork's maintenance cost |
| **T5** | If a driver switch clearly helps Wilds, propose it to Mesa as a built-in Wilds profile (a public contribution) | Yes, after Y1 shows a repeatable gain |

## 12. What I checked myself, and what this makes stale

**Checked (2026-10-11):**

| Claim | Where |
|---|---|
| Override, dump and quirk switches exist; the quirk list | vkd3d-proton master `2230755`, `libs/vkd3d-shader/vkd3d_shader_main.c` lines 87–122 and 380–470. Override and quirks also present in tags v3.0 and v3.0.1 |
| Override or dump makes vkd3d-proton ignore cached SPIR-V | `libs/vkd3d/device_workarounds.c` lines 876–880 |
| vkd3d-proton has a Wilds profile (sparse-tile and heap-robustness fixes; no compression changes) | `libs/vkd3d/device_workarounds.c` lines 160–164 and 659–667 |
| `radv_prefer_2d_swizzle_for_3d_storage` exists in Mesa 26.0 and 26.1 (not 25.3) | Mesa 26.1 `src/amd/vulkan/radv_instance.c` lines 289–290; effect and "heuristic" comment in `radv_image.c` lines 642–656 |
| Any Mesa option can be overridden by an environment variable of the same name | Mesa 26.1 `src/util/xmlconfig.c` lines 422–443 |
| Mesa's per-game use: Ghost Recon Breakpoint (fog pass), The Last of Us Part I, Total War: ROME (+15%) | Mesa main `src/amd/vulkan/01-radv-performance.conf` |
| Wilds Ver.1.040.03.01: CPU tab, fog 2 → 5 levels, VRS forced off during upscaling | [Capcom patch notes](https://info.monsterhunter.com/wilds/update/en-us/Ver.1.040.03.01.html) |
| Wilds Verified on 21 Aug 2026, "30 FPS and above most of the time", poor visuals | [Steam Deck HQ](https://steamdeckhq.com/news/monster-hunter-wilds-gets-steam-deck-verified/) |
| Legion Go S (Z1 Extreme): ~40 fps exploring and fighting, ~30 in CPU-heavy areas such as the Grand Hub (29 Jan 2026) | [TechRadar](https://www.techradar.com/gaming/pc-gaming/its-not-a-myth-capcom-has-fixed-monster-hunter-wilds-and-i-even-tested-it-to-find-out) |

Mesa code was read from the GitHub mirror `chaotic-cx/mesa-mirror`, branches 26.0, 26.1 and main.
SteamOS 3.8.28 reportedly ships Mesa 26.1.2, but Valve's notes don't say so [bandwidth §7].

**Made stale by this research:**
- INVENTIONS sections 1 and 8 baseline numbers (January 2026) predate Ver.1.041 and the Verified
  badge. Refresh them after Y0.
- INVENTIONS test X4's "Wilds' own VRS setting" now applies only without upscaling.
- INVENTIONS section 4 "where to build: a fork of vkd3d-proton". Stock switches come first (T4).
- QUALITY_TARGET.md, decision 0001 and CLAUDE.md say 45 fps. Pending T1.
- The discover spec's settings-file handling for Space Marine 2: back-up-only (section 7).

**Gaps:**
- PCGamingWiki was unreachable from this environment.
- Digital Foundry pages were read only through secondary summaries.
- No per-pass GPU profile of Wilds on any RDNA2 device exists publicly. Y5 and X1 produce the
  first one.
