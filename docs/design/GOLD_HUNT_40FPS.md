# Gold hunt: what could get Wilds and Space Marine 2 to 40 fps

Status: **PROPOSED**, 2026-10-11. This is a catalog of techniques, not a plan of record. An
independent verifier raised 22 findings. Its re-check found 20 fixed and 2 partly fixed; the
remaining wording issues were then corrected.

It answers Fede's question: *"The target I want is 40 fps. What other techniques can better
distribute resources to gain a couple more frames while keeping image quality good? Can we
really not optimize the shaders? Look at the device, at modern games, at how developers
optimize for weak hardware. There might be gold hiding somewhere."*

**Evidence.** Four new research notes in `docs/research/2026-10-11-gold-hunt/`, plus one earlier
note:

| Cited as | File | Question |
|---|---|---|
| [ports] | `impossible_ports.md` | What did Switch, Switch 2, iPhone and Series S ports cut, and what can an outside tool copy? |
| [engines] | `re_engine_swarm_low_end.md` | Hidden or low-end paths in RE Engine (Wilds) and Swarm (Space Marine 2) |
| [shaders] | `shader_optimization_outside.md` | Can shaders be optimized from outside a shipped game? |
| [bandwidth] | `rdna2_apu_bandwidth.md` | Memory-bandwidth and chip-level levers on the Deck's APU |
| [inv-cpu] | `docs/research/2026-10-11-inventions/cpu_power_io_levers.md` on branch `design/native-inventions` | Earlier note: Deck baselines for both games |

Earlier work this builds on: `INVENTIONS.md` (PR #6, branch `design/native-inventions`) and
`STRATEGY_OPTIONS.md` / `LAUNCH_FLOW.md` (PR #2, branch `design/overnight-rethink`).

**Labels:**
- **(est.)**: my estimate or inference, not a measurement.
- **UNPROVEN**: nobody has shown it working.
- **[checked]**: I confirmed it myself in source code or on the primary page. Section 12 lists
  what and where.
- "none found": the research found no example. That is not proof that none exists.

---

## 1. The short answer

**What 40 fps means on the Deck.**
- 40 fps is 25 ms per frame. It only paces evenly at **80 Hz**, where each frame is shown for
  exactly two refreshes. At 90 Hz it judders, because 90 ÷ 40 = 2.25.
- The OLED panel runs 45–90 Hz, so 80 Hz is available.
- Optional 2× frame generation would present 80 fps at 80 Hz.
- "Locked" means what QUALITY_TARGET.md says: median frame time ≤ 25 ms, plus a 99th-percentile
  guard. An *average* of 38–40 fps is not a lock.

**Where Wilds starts today: better than January in places, unknown in others.**
- **28 January 2026.** Steam Deck HQ, lowest settings, measured *after* the patch that added the
  CPU tab and the new fog levels. They found that patch's new GPU options had "almost no effect"
  [inv-cpu §1]. Results:
  - quieter areas: about 30 fps;
  - large open areas: high teens to low 20s;
  - Windward Plains watering hole: below 20;
  - Scarlet Forest: mid-20s.
- **18 February 2026.** Ver.1.041 added mesh LODs and cut CPU load [engines §5].
- **July 2026.** A 9-minute Scarlet Forest hunt averaged just above 30 at the lowest settings, with
  poor 1% and 0.1% lows [checked]. The same area went from mid-20s to 30+. That hints
  at a 15–25% improvement, though it is one test each (est.).
- **21 August 2026.** Steam Deck Verified: "30 FPS and above most of the time" at default
  settings, with no area named and visuals that look "pixelated and blurry" [checked].
- **Best guess (est.):** about 30 fps in quieter areas, low-to-mid 20s in large open areas.
  Unknown until we re-measure (test Y0).

**Honest verdicts (est., to be tested):**

| Scene | Starting point | Locked 40 fps? |
|---|---|---|
| Wilds, quieter field areas (mostly GPU-bound per Steam Deck HQ) | ~30 fps | **Possible only with Tier I levers *and* better-than-middle results** (section 8). Tier S alone: unlikely without lowering image quality |
| Wilds, large open areas | Low-to-mid 20s (est.) | **Unlikely.** Needs 37–50% off the frame time |
| Wilds, hubs such as the Grand Hub (CPU-bound) | No Deck number. An 8-core Zen 4 handheld drops to ~30 there [checked] | **Very unlikely.** The Deck's CPU is much weaker |
| Space Marine 2, interiors and quiet sections | 20–30 fps on 2024 builds [engines §11]; ~24 dropping to 19 at the lowest settings with FSR 2 Ultra Performance, not interior-specific; interiors were "higher" [inv-cpu §2] | **Unlikely.** A forced 640×400 still couldn't hold 30 [inv-cpu §2], so resolution isn't the limit. Evidence supports 30 with dynamic resolution as the ceiling [engines §11]. Test Y6 decides |
| Space Marine 2, hordes (CPU-bound) | As low as 14 fps [inv-cpu §2]; 8-core consoles fall below 40 [engines §8] | **No** with Tier S tools |

Per rule R1, the honest promise is narrower than "40 everywhere": aim for 40 in the quieter
parts of Wilds, and accept 30 in hubs, large open areas and Space Marine 2.

**Can we really optimize the shaders? Yes, and the hook already exists.**
- Proton's D3D12 translator, vkd3d-proton, can load our own version of any game shader, keyed by a
  fingerprint of the original.
- A second switch changes how individual shaders are compiled, with no shader writing at all.
- Both are plain launch options [checked].
- Nobody has published a *performance* use of them in a shipped game. That is the main gold here
  (section 3).
- Limits: Wilds-only (Tier I), and a realistic gain is single digits to about 10%, not 30%
  (est.).

## 2. How "impossible ports" are made, and what we can copy

Port teams follow the same three steps [ports §1]:
1. render at roughly 25–45% of the output's pixels and reconstruct the image;
2. remove "second-order" lighting: AO, GI, volumetrics, reflections, depth of field;
3. trim shadows, foliage, draw distance and textures.

Their biggest single wins were not settings changes:
- Saber says it took Witcher 3 on Switch from 10 to 30 fps by rewriting the grass and sun-shadow
  systems, plus memory and storage work [ports §2, claimed].
- Doom 2016 on Switch rendered transparency and depth of field at **quarter resolution**
  [ports §1].

| Port trick | Precedent | What DeckForge can do from outside | Tier |
|---|---|---|---|
| Very low internal resolution plus strong reconstruction | RE Engine on Switch 2 handheld at **360p** with DLSS (Street Fighter 6, RE Requiem); RE4 on iPhone at ~360p with MetalFX [ports §1, engines §6] | The Deck has neither DLSS nor MetalFX, and FSR from below ~540p looks much worse. Better reconstruction is the open research track (QUALITY_TARGET lever 1, DeckSR, X7) | S (game upscaler) / I (OptiScaler) |
| Remove second-order lighting | Street Fighter 6 handheld drops AO, volumetrics, SSR, DoF [ports §1] | Wilds menu; REFramework for GI (DPGI) and below-menu cuts [engines §3] | S / I |
| Distant characters animate less often | Hogwarts on Switch; SF6 animates distant characters at ~20 fps [ports §4, engines §6] | Wilds' official CPU tab reportedly has a "frame skip" option. What it skips is unconfirmed [engines §5] | S |
| Cap the number of small creatures | Witcher 3 tried −30% NPCs, then **reverted it because the world felt empty** [ports §1] | Wilds' CPU tab reportedly caps small creatures [engines §5]. Use as a last resort | S |
| Dynamic resolution to hold the frame rate | Most Switch ports; Wilds on consoles [ports §1, engines §1] | Space Marine 2 has a "Dynamic Resolution FPS Target" [engines §9]. Wilds on PC has none we know of; see the dormant-feature check (section 5) | S / I |
| Quarter-resolution particles and depth of field | Doom 2016 on Switch [ports §5] | **No external precedent found.** Per-pass VRS (INVENTIONS) is the nearest stand-in | I |
| Algorithm rewrites | Witcher 3 grass and sun shadows [ports §1] | Only through shader surgery (section 3), and only for loops and constants, not whole new algorithms | I |
| Cutscenes at a lower frame rate for higher resolution | Doom Eternal on Switch: cutscenes at 20 fps [ports §1] | Scene-aware targets (section 6) | S |

## 3. Gold nugget 1: shader surgery without forking Proton

INVENTIONS assumed port surgery would need our own fork of vkd3d-proton (decision N3). The first
experiments don't. Released vkd3d-proton already has three switches, read from environment
variables, so they can go in a Steam launch option:

| Switch | What it does | Checked |
|---|---|---|
| `VKD3D_SHADER_DUMP_PATH` | Saves every shader the game creates, named by a 64-bit fingerprint of its original bytecode | [checked] master, v3.0, v3.0.1 |
| `VKD3D_SHADER_OVERRIDE` | If a file named after a shader's fingerprint exists in that folder, loads it instead of the game's shader | [checked] master, v3.0, v3.0.1 |
| `VKD3D_SHADER_QUIRKS` | A text file mapping fingerprints (or ranges) to compile options, with no shader writing needed. In released v3.0/v3.0.1: wave size `FORCE_MAX_WAVE32` / `FORCE_MIN_WAVE32`, and tessellation caps `LIMIT_TESS_FACTORS_4…32`. Master only (not released): `DEBUG_FORCE_MIN_WAVE64`, `CLAMP_WAVE_SIZE_TO_THREAD_GROUP32` | [checked] master, v3.0, v3.0.1 |

A user quirk file adds to vkd3d-proton's own built-in Wilds safety quirk and does not replace it
(`vkd3d_shader_main.c` lines ~495–515).

**Why this matters.** It turns "AI writes cheaper shaders" into a concrete, measurable loop:
1. **Capture** a fixed scene on the Deck:
   - an RGP GPU profile (`MESA_VK_TRACE=rgp` with a file trigger, so no keyboard press is needed
     mid-game);
   - a shader dump;
   - per-shader register statistics (`RADV_DEBUG=shaderstats`) [shaders §4].
2. **Rank** the passes by GPU time. Label each one memory-bound, ALU-bound, latency-bound or
   output-bound.
3. **Map** each hot pass in the profile to its shader fingerprint. **This step is a risk:** no
   documented way to do it was found [shaders §4]. Test Y5(d) checks it first.
4. **Try the cheap switches first:** wave size or tessellation caps through the quirks file.
5. **Then edit constants** in the hottest shaders: sample counts (AO, blur, shadow filtering),
   ray-march steps (fog), loop bounds. Decompile to GLSL, change the number, recompile and
   validate, keeping every binding identical [shaders §8].
6. **Score every variant automatically:**
   - per-frame and temporal image metrics over several scenes;
   - frame time measured on the Deck at the real power limit;
   - Fede's blind A/B for the final call (QUALITY_TARGET.md).
7. **Pin** each recipe to the game build, the Proton version and the shader fingerprint. If any
   of them changes, the recipe switches itself off and reports "dropped", never "passed".

**What the research says about gains:**
- Classic automatic shader simplification: 1.6–2.5× on complex shaders, in lab conditions with
  full source code [shaders §5].
- AMD on 16-bit math (FP16): about 10% on Vega when the engine was written for it [shaders §3].
  vkd3d-proton already uses native 16-bit wherever the game asks for it, so there is little left
  to take for free.
- Halving a sample or step count saves roughly 30–50% of that one pass when the pass is
  memory-bound (est.) [shaders §8].
- **Frame-level math (est.).** Cutting 40% from a 3 ms pass saves 1.2 ms. *If* Wilds has two or
  three hot passes of about that size (unknown until X1), that is 2.4–3.6 ms: about 7–11% of
  today's ~33 ms frame.

**AI's role, honestly.** Recent results shrink a lot under strict checking.
- KernelBench-Verified (2026), on CUDA/ML kernels rather than shaders: the best model's speedup
  fell from 1.43× to 0.88× once realistic baselines and hidden inputs were used. Some "speedups"
  returned the input unchanged [shaders §5].
- In a rendering-kernel study, a model deleted a loop it judged redundant and broke the image
  [shaders §5].

So the AI proposes *which constants to try*, and the harness decides. That matches rule R2.

**Caveats:**
- The vkd3d-proton README calls these switches "only meant to be used by vkd3d-proton
  developers". They could change without notice [shaders §1].
- A replacement can break in two ways [shaders §6]:
  - **A game patch recompiles a shader.** Its fingerprint changes and our version silently stops
    applying. Safe; we only lose the gain.
  - **A Proton update changes how shaders are wired.** Our old version still loads but may be
    bound wrong. Unsafe: corruption or a GPU hang. This is why recipes pin the Proton version.
- Using the override or dump switch makes vkd3d-proton ignore the game's own cached shader
  translations [checked]. Expect extra compiling on the first run.
- RE Engine keeps its own `shader.cache2`. A RenoDX mod tells users to delete it when installing
  [shaders §6]. This needs checking for Wilds.
- **Tier I, Wilds only.** These switches inject nothing into the game, but they change the code
  the GPU runs, which is the kind of change cheats rely on (for example, see-through walls).
  Whether Easy Anti-Cheat on Proton would notice is unknown (no source), so we treat them as
  Tier I either way. Never for Space Marine 2 or Helldivers 2 (decision T3).
- **Prerequisite still open.** INVENTIONS section 4 lists Wilds as a Tier I candidate *pending a
  check of its anti-tamper and EULA*, which hasn't been done. Capcom has an anti-mod stance for
  ranked play [engines §5]. Desk task Y7 does this check before any Tier I test.

**Prior art: none found for performance.** RenoDX and 3DMigoto replace shaders by fingerprint for
HDR and fixes. RenoDX added an AI-agent bridge (MCP) for inspecting and hot-loading shaders in
2026 [shaders §2]. DeckForge would be first-of-kind for **measured performance** recipes under
Proton (est.).

## 4. Gold nugget 2: driver switches meant not to change the image

These change how the GPU driver lays out memory or schedules work, not the game's shader code
(except `cswave32`, which is why it is Tier I). All but one are meant to leave the image
unchanged. The unified-heap switch deliberately changes the game's texture budget. Y1 includes
an image check anyway, because driver-level changes can expose game bugs. Each is a launch option, so it is free to try and free
to undo.

| Switch (launch option) | What it changes | Evidence | Expected (est.) |
|---|---|---|---|
| `radv_prefer_2d_swizzle_for_3d_storage=true` | Stores 3D compute textures (typical for volumetric fog) in a 2D memory layout | Option ships in Mesa 26.0 and 26.1. Any Mesa option can be set by an environment variable of the same name [checked]. Mesa's own code calls it "really just a heuristic" that depends on how the game reads the texture [checked]. Per-game uses: The Last of Us Part I (Mesa 26.2, `00-radv-defaults.conf` lines 269–271). Only on unreleased Mesa main: Ghost Recon Breakpoint's fog pass ("much faster") and Total War: ROME (+15%, a native Linux port, not a Proton game) [checked; verifier] | 0–5%, could be slower. Only matters if Wilds' fog uses 3D storage textures (likely, unproven) |
| `VKD3D_CONFIG=single_queue` | Turns off async compute and puts all work on one queue | No Deck measurements. On an 8-unit, bandwidth-limited GPU, overlap may not help [bandwidth §5] | ±5% |
| `VKD3D_CONFIG=no_staggered_submit` | Turns off a software scheduling trick that "may regress GPU performance in some cases" [bandwidth §5] | The code says staggering only happens with a single queue family or `single_queue`, so on a default Deck it probably does nothing (`libs/vkd3d/command.c` lines 25310–25312) | Test only together with `single_queue` |
| `radv_enable_unified_heap_on_apu=true` | Reports all shared memory as one GPU heap. That changes the game's texture budget, so textures may look different | Enabled for one game (RDR2) [bandwidth §4] | Texture quality and stutter, not fps |
| `RADV_PERFTEST=cswave32` | Compiles every compute shader 32 threads wide instead of 64 | Wave32 gave +12.5% for ray tracing on desktop RDNA2 [shaders §3]. No game numbers for compute. Can break shaders that assume 64-wide groups [bandwidth §6] | ±5%. **Changes how shader code is compiled**, the same class as the quirk `FORCE_MAX_WAVE32`, so treated as **Tier I** (T3) |

**An upstream gift.** If a switch clearly helps Wilds, propose it as a built-in Wilds profile to
the project that owns it:
- Mesa, for the `radv_…` options;
- vkd3d-proton, for the `VKD3D_CONFIG` flags.

Every Deck owner would then get it automatically, with credit to DeckForge. This posts publicly,
so it needs Fede's yes (decision T5).

**Bandwidth tricks are fool's gold** [bandwidth §1–§4]. The OLED has 16% more memory bandwidth
than the LCD model and measured only 2–9% faster. So the GPU is only partly bandwidth-limited,
and cutting memory traffic buys only a fraction of the saving.
- Demoting render-target formats at 800p: about 0.5–2%, for high risk.
- Forcing memory compression: anywhere from −3% to +3%.

See section 9.

## 5. Gold nugget 3: what Wilds itself now offers, and what may be dormant inside it

**Official levers (Tier S)** [engines §5, checked]:
- **Volumetric fog: five levels.** The old Low became High, and Medium, Low and Lowest are new.
- **CPU tab.** Capcom says it adjusts "settings related to CPU load". Community reports mention a
  "frame skip" option and a small-creature cap; neither is officially confirmed.
- **Mesh LODs and spawn optimizations** (Ver.1.041, February 2026).

Steam Deck HQ found the January patch's new GPU options had "almost no effect" on the Deck
[inv-cpu §1]. Don't expect much from the fog levels alone.

**One lever closed.** Capcom now forces Wilds' own variable-rate shading **off whenever an
upscaler is on**, "to maintain proper effect visuals" [checked]. Two consequences:
- INVENTIONS test X4 ("Wilds' own VRS setting") only applies at native resolution now.
- The driver can still force coarse shading (`RADV_FORCE_VRS`). Capcom's reason is a warning that
  it may look bad with upscaling.

**Below-menu values (Tier I, REFramework)** [engines §3]. Mods expose values the menu doesn't:
- shadow resolution below the lowest preset;
- clutter culling;
- mesh, foliage and texture LOD bias;
- particle density;
- turning ambient GI (DPGI) off.

The gains are claimed as "significant" but nobody measured them. The image cost is real: pop-in,
missing clutter, flat lighting. The author of a fog mod expects it "probably not" to improve fps
significantly [engines §3].

**Dormant console features: a hypothesis (UNPROVEN).**
- Wilds on consoles uses dynamic resolution [engines §1].
- Fog levels below the PC menu existed in the PC build before Capcom exposed them [engines §3, §7].
- If the console dynamic-resolution code also ships in the PC build, a REFramework script could
  switch it on. Wilds would then get the most common port trick: resolution drops only in heavy
  moments, so quiet scenes stay sharp.
- **A 30-minute search** with REFramework's object explorer (Y3) can find it. It can't prove it's
  absent.

**Texture pre-decompression (Tier I).**
- **What it does.** Community tools store Wilds' textures uncompressed, so nothing has to
  decompress them while you play. One removed camera-pan micro-stutter on an RTX 4060
  [engines §4].
- **Which chip benefits is unknown.** Nobody has established whether Wilds decompresses on the
  CPU or the GPU by default; one community claim says CPU [inv-cpu §3]. Either way the work
  disappears: CPU relief in hubs, or GPU relief in the field.
- **Expected effect:** better 1% lows rather than a higher average (est.).
- **Cost and safety.** It writes roughly 17–37 GB of extra files into the game's install folder,
  depending on the tool [engines §4, inv-cpu §3]. That is a user-file write under R10; the undo is
  Steam's "Verify integrity of game files". That probably restores replaced files but may not
  delete added patch files, so freeing the disk space may need a manual step (unconfirmed).
- This is INVENTIONS' "decompression routing" add-on (X8) in a simpler form.

## 6. CPU-bound scenes: hubs and hordes

GPU tricks do nothing when the CPU is the limit. The Deck has 4 Zen 2 cores sharing a 15 W budget
with the GPU. The levers that remain:

| Lever | Tier | Game | Evidence |
|---|---|---|---|
| CPU tab ("frame skip" and small-creature cap, per community reports) | S | Wilds | Official tab; what each option does is unconfirmed and unmeasured [engines §5, §13] |
| `ParallelBuildProcessorCount` 4–8 in `config.ini` | S | Wilds | "Same or slightly smoother, lower CPU load" at 4 on a Deck (claimed). Values above 8 hurt some users [engines §2] |
| Newer Proton | S | Both | Proton Experimental is recommended for Wilds on the Deck [engines §5]. Newer vkd3d-proton *may* cut CPU overhead through opt-in descriptor heaps; no numbers are published [bandwidth §7]. If Y0 already runs on Proton Experimental, part of this gain is already in the baseline |
| Power steering: cap the GPU clock so the CPU gets more of the 15 W | S | Both | INVENTIONS invention 3, test X3. In GPU-heavy scenes the CPU drops to 2–3 W [bandwidth §8]. Moving watts to the GPU in the field takes them away from the CPU, so the two directions conflict |

**Scene-aware targets.** Doom Eternal on Switch ran cutscenes at 20 fps to look better
[ports §1]. The DeckForge version is **40 fps where possible, 30 fps where not**. The catch is
pacing:

| Frame rate | Paces evenly at | Shares a refresh rate with |
|---|---|---|
| 45 fps | 90 Hz | 30 fps |
| 40 fps | 80 Hz | nothing useful in 45–90 Hz (the next step down at 80 Hz is 26.7 fps) |
| 30 fps | 90 Hz (or 60 Hz) | 45 fps |

So switching between 40 and 30 means switching the panel between 80 and 90 Hz. Nobody knows yet
whether that blinks on the OLED; test Y4 checks it in five minutes. If it blinks, the choice is
between:
- 40 at 80 Hz with uneven hubs;
- or 45/30 at 90 Hz.

## 7. Space Marine 2 (Tier S only, Easy Anti-Cheat)

- **The settings files are reportedly encrypted** and keyed to each other. Editing or restoring a
  single file fails, and Steam Cloud reverts changes [engines §9]. Only user reports; not
  confirmed.
  - **Impact on Phase 1:** DeckForge must never edit these files. Even a backup may not be
    restorable, so it cannot promise an undo for them. This needs a spec amendment later.
- **`SteamDeck=1`** (set automatically on a Deck) is only known to select a Low preset and a 30
  fps cap. Whether it changes anything else is unknown [engines §10, ports §3].
- **Usable levers:**
  - the in-game menu, including the **Dynamic Resolution FPS Target**;
  - FSR 3.1;
  - Cloth Simulation Low;
  - SSR off;
  - frame cap and refresh rate;
  - power steering, towards the CPU [inv-cpu §2].
- **Hordes** are limited by enemy count on the CPU. An 8-core PS5 drops below 40, and no setting
  changes enemy count [engines §8, §13].
- **No evidence that interiors are GPU-bound.** The dynamic-resolution target only helps if they
  are.
- **Launch-option driver switches** (section 4) are Tier S under today's CLAUDE.md. Whether to
  keep allowing them for an anti-cheat game is decision T3. Shader replacement never is.

## 8. Budget math to 25 ms

All gains below are **(est.)**, made up from the evidence ranges above. They are combined by
multiplying: two 10% cuts give 1 − 0.9 × 0.9 = 19%, not 20%.

**Read the combined rows as upper bounds.** Several levers cut the same passes: fog Lowest,
REFramework fog/GI cuts, and shader surgery on fog or AO. Once a pass is cut, the next lever on
it gains less.

**Wilds field (GPU-bound). The levers:**

| Lever | Tier | Low | Mid | High |
|---|---|---|---|---|
| Official settings beyond the defaults (fog Lowest, shadow-cache A/B, filtering). January's GPU options had "almost no effect" [inv-cpu §1] | S | 0% | 2% | 6% |
| Driver switches (section 4, Tier S ones) | S | 0% | 3% | 8% |
| Power steering (watts to the GPU) | S | 0% | 2% | 5% |
| REFramework below-menu cuts | I | 3% | 8% | 15% |
| Shader surgery on 2–3 hot passes | I | 0% | 5% | 10% |
| **Tier S only, combined (upper bound)** | | 0% | 7% | 18% |
| **Tier S + I, combined (upper bound)** | | 3% | 19% | 37% |

**What that gives, from two starting points:**

| Start | Needs off for 40 | Tier S mid | Tier S high | S + I mid | S + I high |
|---|---|---|---|---|---|
| 30 fps (33.3 ms), quieter areas | 25% | 32.2 fps | 36.5 fps | 36.8 fps | 47.7 fps |
| 22 fps (45.5 ms), large open areas (est.) | 45% | 23.6 fps | 26.8 fps | 27.0 fps | 35.0 fps |

**Reading the tables:**
- **Quieter areas.** The middle case lands around 37 fps on average, short of 40 and well short
  of a *lock*. Reaching a lock needs high-end results on several levers at once.
- **Large open areas.** Even the best case stays in the mid-30s.
- **What "Tier S only" leaves out.** Two Tier S levers are excluded because they cost image
  quality: forced coarse shading (`RADV_FORCE_VRS`) and lower resolution. They are the remaining
  swing levers if Fede accepts a softer image.
- **The bottleneck can move.** As GPU time falls toward 25 ms, the CPU may become the limit even
  in the field, and steering watts to the GPU makes that worse.

**Wilds hubs (CPU-bound).**
- **Starting point:** no Deck measurement. The evidence points to 30 fps or below: a much faster
  handheld CPU drops to ~30 there [checked]. (A January Deck report puts *large open areas* at
  ~25 or lower [engines §5], but those are not hubs.)
- **What 40 needs:** 25–40% off the CPU's time.
- **What the levers might give:** four CPU levers (section 6), guessed at 5–10% each (none is
  measured), would give about 19–34% together.
- **Verdict:** only the optimistic end reaches the easiest case. **40 in hubs: very unlikely.**

**Space Marine 2.** 30 with dynamic resolution is the evidence-backed ceiling (section 1). Y6
tests whether interiors can do better.

## 9. Fool's gold: ruled out or pushed down the list

| Idea | Why not (for now) |
|---|---|
| Render-target format demotion (16-bit → 11/10-bit colour) | ~0.5–2% at 800p behind FSR. High risk: banding, no negative values, aliased memory [bandwidth §2] |
| Forcing memory compression (DCC) on more textures | Could go either way (−3% to +3%). Changes memory layout under the game [bandwidth §3] |
| `RADV_TEX_ANISO` to cap texture filtering | Also *raises* filtering on samplers the game set to none, so it is not a clean cap [bandwidth §4] |
| UMA frame buffer 4 GB | Affects stability and texture budget, not fps. It is a BIOS setting the user changes, not DeckForge (R7) [bandwidth §4] |
| Memory or fabric clock control | Memory clock can't be set on this chip. Fabric clock is firmware-level and off-limits (R7) [bandwidth §8] |
| Skipping Wilds' safety workarounds in vkd3d-proton | Risks GPU page faults or hangs. Valve added them for a reason [bandwidth §9] |
| Free-form AI shader rewrites | Speedup fell to 0.88× under strict checking (measured on CUDA/ML kernels, not shaders). Known image-breaking edits [shaders §5] |
| Generic "half-resolution particles" layer | No precedent. Breaks on depth, blending and memory aliasing [ports §5] |
| Cutting crowds or monsters hard | Witcher 3's port reverted it because the world felt empty [ports §1] |
| Old Deck config packs ("Little Engine that Shouldn't") | Marked obsolete by its author after the 2026 patches [engines §2] |

## 10. Tests

These extend the X-tests in INVENTIONS section 7. Under rule R7, every Deck test is run by Fede
by hand, or later by the bench runner, never from a dev session.

| # | Test | Where | Time | Decides |
|---|---|---|---|---|
| **Y0** | Re-baseline Wilds on the current build, at the Verified defaults and the 2026 Lowest preset. Scenes: a quieter field area, Windward Plains, combat, Grand Hub. Measure uncapped median and 99th-percentile frame time | Deck | One evening | Every number in section 8. Should run before X1 |
| **Y1** | The Tier S driver switches from section 4, one at a time, in the same field scene, each with a screenshot comparison. `no_staggered_submit` only together with `single_queue` | Deck | One evening | Driver gains with no intended image cost (extends X8) |
| **Y2** | Official levers one at a time: fog Lowest, each CPU-tab option, `ParallelBuildProcessorCount` 4/6/8, shadow cache on/off. In the field and in a hub | Deck | One evening | Best Tier S baseline for Wilds |
| **Y3** | Search REFramework's object explorer for a dynamic-resolution component in Wilds. Needs Y7 first | Deck | ~30 min | Whether external dynamic resolution is possible (finding it proves it; not finding it doesn't disprove it) |
| **Y4** | Switch the refresh rate 80 ↔ 90 Hz while playing. Does the screen blink? | Deck | 5 min | Whether scene-aware 40/30 targets are viable |
| **Y5** | Shader-hook smoke test. Needs Y7 first. Four checks: (a) the shader dump works for Wilds under the Deck's Proton; (b) a no-op override (the dumped shader fed back unchanged) loads and runs; (c) an RGP capture works on the Deck's chip; (d) one hot event in the profile can be mapped to its shader fingerprint | Deck | One evening | Whether X1 and shader surgery can start without a fork |
| **Y6** | Space Marine 2: dynamic-resolution target 40 + FSR 3.1 at 80 Hz, interior vs horde; power steering towards the CPU in a horde | Deck | One evening | Realistic Space Marine 2 target |
| **Y7** | Desk check of Wilds' anti-tamper and EULA for Tier I tools (the check INVENTIONS section 4 left open) | Desk | ~1 hour | Whether any Tier I test (Y3, Y5, X1, REFramework) may run |

## 11. Decisions for Fede

| # | Decision | Recommendation |
|---|---|---|
| **T1** | Change the native target from a locked 45 fps (22.2 ms, 90 Hz) to a locked **40 fps (25 ms, 80 Hz)**. This amends decision 0001, QUALITY_TARGET.md and CLAUDE.md, in a small separate PR | Yes, you asked for it. I'll prepare that PR once you confirm |
| **T2** | Allow **scene-aware targets**: 40 where reachable, 30 accepted elsewhere (hubs, large open areas, Space Marine 2) | Yes, subject to Y4. It is honest (R1) and copies a real port trick |
| **T3** | Today CLAUDE.md lists all Steam launch options as Tier S. That technically includes shader dump, override and quirk files, even for anti-cheat games. Proposal: **narrow it.** Keep as Tier S only the switches that change driver memory layout or scheduling (`radv_prefer_2d_swizzle_for_3d_storage`, `VKD3D_CONFIG=single_queue` / `no_staggered_submit`, `radv_enable_unified_heap_on_apu`). Move anything that changes or recompiles shader code (shader dump/override/quirks, `RADV_PERFTEST=cswave32`) to **Tier I**, never for anti-cheat games | Yes to narrowing. Whether Easy Anti-Cheat reacts to *any* launch-option switch is **unknown (no source either way)**. A more cautious alternative is no driver switches at all for Space Marine 2 |
| **T4** | Run port-surgery experiments on the stock vkd3d-proton switches first. Decide on a fork (N3) only if they hit a limit | Yes. This defers the fork's maintenance cost |
| **T5** | If a driver switch clearly helps Wilds, propose it upstream (Mesa or vkd3d-proton) as a built-in Wilds profile. This is a public contribution | Yes, after Y1 shows a repeatable gain |

## 12. What I checked myself, and what this makes stale

**Checked on 2026-10-11:**

| Claim | Where |
|---|---|
| Override, dump and quirk switches exist | vkd3d-proton master `2230755`, `libs/vkd3d-shader/vkd3d_shader_main.c` lines 87–175 (override and dump) and 380–470 (quirks). All three are also present in tags v3.0 and v3.0.1 |
| Quirks available in released builds vs master only | Tag v3.0/v3.0.1 quirk table ends at `FIXUP_RSQRT_INF_NAN`. `DEBUG_FORCE_MIN_WAVE64`, `CLAMP_WAVE_SIZE_TO_THREAD_GROUP32`, `PRECISE_FMA` and `IGNORE_PRIMITIVE_SHADING_RATE` are master only |
| Override or dump makes vkd3d-proton ignore cached SPIR-V | `libs/vkd3d/device_workarounds.c` lines 876–880 |
| vkd3d-proton has a Wilds profile (sparse-tile and heap-robustness fixes; no compression changes) | `libs/vkd3d/device_workarounds.c` lines 160–164 and 659–667 |
| `radv_prefer_2d_swizzle_for_3d_storage` exists in Mesa 26.0 and 26.1, not in 25.3 | Mesa 26.1 `src/amd/vulkan/radv_instance.c` lines 289–290. Effect and "heuristic" comment in `radv_image.c` lines 642–656 |
| Any Mesa option can be overridden by an environment variable of the same name, even over drirc files | Mesa 26.1 `src/util/xmlconfig.c` lines 422–443 and 876 |
| Mesa's per-game uses of the swizzle option | Mesa main `src/amd/vulkan/01-radv-performance.conf`: Ghost Recon Breakpoint (fog pass), Total War: ROME (+15%). TLOU1 in Mesa 26.2 `src/amd/vulkan/00-radv-defaults.conf` lines 269–271 |
| Wilds Ver.1.040.03.01: CPU tab, fog 2 → 5 levels, VRS forced off during upscaling | [Capcom patch notes](https://info.monsterhunter.com/wilds/update/en-us/Ver.1.040.03.01.html) |
| Wilds got Valve's Playable badge in July 2026 (Steam Deck HQ headline: "technically playable"; a 9-minute Scarlet Forest hunt averaged above 30 at lowest settings), then Verified on 21 Aug 2026 with "30 FPS and above most of the time" | [Steam Deck HQ, July](https://steamdeckhq.com/news/monster-hunter-wilds-is-technically-playable/); [Steam Deck HQ, August](https://steamdeckhq.com/news/monster-hunter-wilds-gets-steam-deck-verified/) |
| Legion Go S (Z1 Extreme), 29 Jan 2026: ~40 fps exploring and fighting, ~30 in CPU-heavy areas such as the Grand Hub | [TechRadar](https://www.techradar.com/gaming/pc-gaming/its-not-a-myth-capcom-has-fixed-monster-hunter-wilds-and-i-even-tested-it-to-find-out) |

**Notes on the checks:**
- Mesa code was read from the GitHub mirror `chaotic-cx/mesa-mirror`, branches 26.0, 26.1 and
  main.
- SteamOS 3.8.28 reportedly ships Mesa 26.1.2, but Valve's notes don't say so [bandwidth §7].
- The verifier could not reach the three web pages above from its environment. I read them
  directly.

**Made stale by this research:**
- **INVENTIONS sections 1 and 8, baseline numbers.** These are from 28 January 2026 and are still
  the best per-area data. They predate Ver.1.041, and July's Scarlet Forest result suggests some
  areas improved. Refresh them after Y0.
- **INVENTIONS test X4.** "Wilds' own VRS setting" now applies only without upscaling.
- **INVENTIONS section 4, "where to build: a fork of vkd3d-proton."** Stock switches come first
  (T4).
- **QUALITY_TARGET.md, decision 0001 and CLAUDE.md.** They say 45 fps. Pending T1.
- **The discover spec's settings-file handling for Space Marine 2.** It becomes never-edit, with
  no promised undo (section 7).

**Gaps:**
- PCGamingWiki was unreachable from this environment.
- Digital Foundry pages were read only through secondary summaries.
- No per-pass GPU profile of Wilds on any RDNA2 device exists publicly. Y5 and X1 would produce
  the first one.
