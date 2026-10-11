# Past the settings menu: what DeckForge could invent

Status: **PROPOSED**, 2026-10-11. This answers Fede's challenge: *"invent something new, something
which by code alone can enhance the experience natively on the Deck. Don't dismiss it because
GeForce NOW or FSR exist."*

Evidence: four research notes in `docs/research/2026-10-11-inventions/`:
- [reprojection], i.e. `reprojection_frame_warp.md`
- [passes], i.e. `per_pass_interception_vrs.md`
- [cpu], i.e. `cpu_power_io_levers.md`
- [recon], i.e. `reconstruction_amortization.md`

Plus last night's notes in `docs/research/2026-10-11-overnight/` (cited as [overnight …]). They
live on branch `design/overnight-rethink`, PR #2. The notes carry every source link.

Labels used below:
- **(est.)** marks an estimate or inference. Everything else is sourced.
- **UNPROVEN** marks an idea that nobody has demonstrated. It is not a claim.

---

## 1. The honest answer first

**Can code alone make Monster Hunter Wilds run at a locked native 45 fps with console image
quality on the Deck?** Nothing found says so.
- At the lowest settings, Wilds sits in the **high teens to low 20s fps in open areas** and about
  **30 fps in quieter areas**. Steam Deck HQ calls the Deck's problem "more related to the GPU
  than the CPU" (Jan 2026) [cpu §1].
- Space Marine 2 measured **14–24 fps**, and **still couldn't hold 30 at a forced 640×400**. That
  points to a CPU and simulation bottleneck that resolution can't fix [cpu §2].

**Can code alone make Wilds *feel* native and *look* clean on the Deck?** Plausibly yes, but not by
searching harder through the settings menu. That approach has hit its ceiling. The remaining
headroom sits in five places, and DeckForge could be the first tool to go after all five on
purpose:

| Where free performance hides | What DeckForge would do | New? |
|---|---|---|
| **Frames the camera needs vs frames the game needs** | Show 90 Hz camera motion from a 30–45 fps game, using your *latest* stick input (invention 1) | Never shipped outside VR. NVIDIA's version is still unreleased |
| **Pixels a 7" screen can't show** | Retrofit the game the way a console port team would: cheaper shadows, fog and GI, full detail where it's visible (invention 2) | Done only by hand, one game at a time. Never as a pipeline |
| **Watts in the wrong chip** | Move power between CPU and GPU every few frames, based on which one is the bottleneck (invention 3) | Not on the Deck. Android has it |
| **CPU work that could run elsewhere** | Route texture decompression to the CPU or GPU per scene, and use a better scheduler (part of invention 3) | Not as an adaptive system |
| **Image quality per millisecond** | Our own reconstruction model, sized for 800p (research track) | Possible with Arm's retrainable model |

None of these needs GeForce NOW or someone else's upscaler. All of them are UNPROVEN on the Deck,
and each has a cheap test that can kill it within weeks (section 7).

## 2. Why the Deck runs some heavy games well and not Wilds

The Deck is a **PS4-class GPU with a much better CPU** in a 15 W envelope:
- **GPU:** 8 RDNA2 compute units at 1.6 GHz, about 1.6 TFLOPS [overnight platform §1].
- **Memory:** 88–102 GB/s shared between CPU and GPU [overnight platform §1].
- **CPU:** a 4-core Zen 2 with only 4 MB of L3, and about 25 GB/s of memory bandwidth on the CPU
  side [cpu §1].

Games authored for PS4-era budgets fit it. Wilds and Space Marine 2 were authored for the PS5
generation. By public spec sheets (est.), that is roughly 6× the GPU throughput, 4–5× the memory
bandwidth, and twice the CPU cores.

A console port team closing a gap like that rewrites systems with source code: it bakes lighting,
cuts crowd density and simplifies effects. From outside the game, DeckForge can only change
three things:
1. what the engine exposes (settings files, REFramework scripts);
2. what the GPU command stream reveals (passes, shaders, render targets);
3. how frames are presented and how the chip is powered.

The inventions below use all three.

---

## 3. Invention 1 — DeckWarp: 90 Hz camera motion from a 30–45 fps game

**What it does.** The game keeps rendering real frames at 30–45 fps. Between them, DeckWarp
re-projects the last real frame using the **newest stick input**, at every 90 Hz refresh. Turning
the camera then responds at 90 Hz. VR headsets have relied on this for a decade (asynchronous
timewarp) [reprojection §2].

**Why it's the opposite of frame generation.** Interpolation waits for the *next* frame before
showing an in-between one, which adds about 40–75 ms of lag [overnight report]. Reprojection
uses input that is *newer* than the frame, so it **removes** camera latency:
- NVIDIA's version, Reflex 2 Frame Warp, cut THE FINALS from 27 ms to 14 ms of PC latency
  [reprojection §3].
- NVIDIA Research found a rotation-only late warp removed **81%** of the aiming penalty of an
  80 ms-old frame [reprojection §1].

This fits your "no latency compromise" rule better than anything else on the table.

**Why nobody has done it on the Deck.** Gamescope (the SteamOS compositor) has no warp code
[reprojection §6]. NVIDIA's Frame Warp was still "coming soon" in August 2026 [reprojection §3].
Every working version so far gets the camera pose from the engine; none is game-agnostic
[reprojection §4]. A game-agnostic DeckWarp would be **first of its kind**.

### Two forms

| | DeckWarp-C (compositor) | DeckWarp-D (in-game, with depth) |
|---|---|---|
| Where | A fork of gamescope (BSD-2 licensed). It already composites on a realtime-priority queue just before each refresh [reprojection §7] | A Vulkan layer or vkd3d-proton fork that captures the depth buffer and the image before the HUD is drawn |
| Inputs | Final image only (HUD baked in), plus stick or gyro read from the Deck's controller device, which the user can access [reprojection §9] | Depth, so it can do a positional warp. Also the chance to redraw the HUD after warping |
| Anti-cheat games (Space Marine 2) | **Possible.** Nothing is injected into the game | No (Tier I) |
| Quality ceiling | Lower | Higher |

### The hard problems (all real, in order of danger)

1. **Third-person orbit cameras.** Both test games orbit the camera around your character.
   A rotation-only warp slides *everything*, the character included, about 22 px per warped frame
   at a 180°/s turn. The next real frame snaps it back, so the character judders (est.)
   [reprojection §11]. DeckWarp-D can fix this with depth. DeckWarp-C would need a trick.
   UNPROVEN idea: keep the screen centre pinned and warp only the periphery.
2. **Predicting the camera from the stick.** Games turn the camera with acceleration curves,
   dead zones and smoothing. A wrong prediction overshoots, then snaps back. Proposed approach:
   **auto-calibrate each game** by correlating recorded stick input with the measured image
   motion. No published method exists [reprojection §10].
3. **HUD baked into the image.** Static HUD pieces (health bars, minimap) can be detected because
   they don't move when the camera does. Qualcomm patented one such method, which constrains
   copying it exactly [reprojection §12]. Moving markers (lock-on, damage numbers) stay a problem.
4. **Getting the warp on time while the game saturates the GPU.** This needs high-priority GPU
   queues. Linux SteamVR had years of trouble with exactly this on AMD [reprojection §2, §7].
5. **Low frame rates look worse.** A community Frame Warp demo showed "major visual issues" at
   30–60 fps caps [reprojection §3]. 45 fps is the friendlier case: one warped frame per real
   frame.

**Cost.** The warp itself is tiny: about 0.1–0.3 ms per refresh at 800p (est.) [reprojection §13].
The real costs are forcing a full composite every refresh and contention with the game.
Learned inpainting like PatchEX is out of budget (3 ms at 360p on an RTX 4080-class GPU)
[reprojection §5].

**How it would ship without touching SteamOS.** Launch a **nested** forked gamescope per game
through the same "paste a launch option once" pattern as `df-run`. The nesting overhead and
latency are UNVERIFIED (est.).

**Kill test first, on the Mac, before any Deck code (X2 in section 7).** Record third-person
footage at 90 fps. Simulate the warp from every second frame, assuming perfect knowledge of the
camera. Compare against the real in-between frames, both with a temporal image metric and blind,
by you. If even this best case shows visible character judder, DeckWarp-C is dead for
third-person games and only DeckWarp-D continues.

---

## 4. Invention 2 — Port surgery: automating what a console port team does

**What it does.** For each heavy game, DeckForge would do three things:
1. Profile **every GPU pass on the Deck**.
2. Find the expensive passes a 7" screen barely shows: volumetric fog, global illumination,
   shadow resolution, ambient occlusion, reflections.
3. Apply targeted cuts to those passes, re-measure, and score image quality with temporal
   metrics.

The result is a shareable **"port profile"** per game and per patch.

**Why "pipeline" is the invention.** People have done each piece by hand for single games:
- FAR for NieR: Automata cut its global-illumination workgroups and disabled volumetric light by
  shader fingerprint.
- TBFix had a "low-precision shadow mode" for performance [passes §2].
- Emulators scale render targets, but every selective change ended up as a per-game rule
  [passes §1].

**Nobody has made the process fast and repeatable.** The steps would be:
1. measure;
2. shortlist candidates;
3. generate cheaper variants: smaller targets, fewer workgroups, or simplified shaders written
   with AI help;
4. A/B them automatically on the Deck;
5. publish the profile with its evidence.

The original "AI writes cheaper shaders" idea fits here, as **one candidate generator inside a
measured, validated pipeline**. It is never trusted on its own.

**Why it might work for Wilds.** Two independent signals point at fog and global illumination:
- The Deck community's REFramework "Lite Environment" GI and fog cuts give "significant gains".
  That mod claims 30–45 fps with heavy cuts [passes §5].
- Guides call volumetric fog a "performance hog" [passes §5].
- Wilds also has its own variable-rate-shading setting, which may work on the Deck. That is
  untested [passes §4].

**Where to build it.** Inside a fork of vkd3d-proton (the D3D12→Vulkan translator), not as a
separate layer. vkd3d-proton already owns shader translation, so it can patch shaders and resize
targets far more easily than a layer underneath it [passes §3, §8]. The cost is maintaining a
fork. **Tier I only**: Wilds yes, Space Marine 2 never.

**Realistic gain, speculative until profiled** [passes §8]:

| Cut | Frame-time saved |
|---|---|
| Fog/GI reductions | 5–20% |
| Halving shadow maps | 2–8% |
| VRS | 0–8% |

**Kill test (X1).** An RGP GPU profile of Wilds on your Deck at the lowest preset in Windward
Plains. If fog, GI, shadows and AO together are under ~20% of GPU frame time, port surgery can't
move Wilds enough and drops to "nice to have".

---

## 5. Invention 3 — Power steering: put the watts where the bottleneck is

**What it does.** A small controller watches each frame. When the GPU is the bottleneck, it caps
CPU boost and frequency so the shared 15 W goes to the GPU. When the CPU is the bottleneck
(camps, hordes), it does the reverse. It uses Valve's own `steamosctl` controls and kernel
interfaces, with no injection [cpu §4].

**Why one fixed setting is wrong.** The best split changes *within* a game:
- **Wilds:** GPU-bound in the open field, CPU-heavy in camps and hubs.
- **Space Marine 2:** CPU-bound in hordes [cpu §1, §2].

A per-game static profile is wrong part of the time. A frame-aware controller isn't.

**Why it's new here.** AMD's SmartShift is designed for laptops with a separate GPU [cpu §4]. On
Android, frame-aware power control (ADPF hint sessions, research such as Co-Cap) has measured:
- about **10% energy per frame** saved at ~1% fps loss;
- one vendor case study of **+11% to +50% fps** [cpu §5].

**No one has published a Deck test, even of a static CPU cap** [cpu §4]. DeckForge's bench runner
would be first.

**Honest size.** The Deck's power controller already favours the GPU: the CPU drops to about
2–3 W in GPU-bound scenes [cpu §4]. Expect **a few percent and steadier lows**, not a
transformation (est.).

**This is the one invention that helps Space Marine 2.** It is Tier S and anti-cheat safe.

**Same module, your original "reroute work" idea.** Wilds ships Microsoft DirectStorage. A mod
already exposes switching texture decompression between CPU and GPU: "GPU mode will decrease CPU
load at a price of GPU load increase" [cpu §3]. Routing that work per scene is the
"reroute CPU work to the GPU" idea in its realistic form:
- GPU decompression in CPU-bound hubs;
- CPU decompression in GPU-bound fields.

Untested; it needs REFramework, so it is Tier I.

Cheap extras in the same module, all measured elsewhere but never on the Deck [cpu §5, §6]:
- the LAVD scheduler;
- low swappiness, which measured **10–21% better lows** on the Deck in other games;
- transparent huge pages.

---

## 6. Research track — DeckSR: our own reconstruction model

**Why it's possible now.** Arm's Neural Super Sampling ships weights that may be **retrained on
your own content**, with Apache-2.0 code and published training tools [recon §1, §3]. A model we
train is a model we own. That avoids NVIDIA's license, the problem with HelixSR, and AMD's
timeline.

**Why it's hard:**
- **Training data.** Good training pairs need supersampled "ground truth" frames, which commercial
  games can't give us [recon §3].
- **Cost.** A network small enough for 1–2 ms at 800p is about 4–8 tiny layers (est.)
  [recon §2]. Arm's own model would cost about 2.5–3.5 ms on the Deck (est.), about the same as
  HelixSR.
- **Competition.** AMD promised a "lightweight" FSR 4 for integrated graphics by the end of 2026
  [recon §2].

**Kill test (X7).** Before any training, microbenchmark a 6-layer INT8 network at 640×400 on the
Deck's GPU. If it's over 2.5 ms, stop.

---

## 7. Validation plan: cheap tests that can kill each idea fast

| # | Test | Where | Needs | Kills or confirms |
|---|---|---|---|---|
| **X1** | RGP GPU profile of Wilds, lowest preset, Windward Plains (compendium E1) | Deck + you, together | One evening | Port surgery: is ≥20% of GPU time in fog/GI/shadows/AO? |
| **X2** | Offline warp simulation on 90 fps third-person footage, best case, scored and blind-tested by you | **Mac only** | Footage of a third-person game the Deck runs at 90 fps | DeckWarp-C for third-person games |
| **X3** | Power A/B: CPU boost off / frequency caps vs GPU clock and fps. Wilds field vs hub; Space Marine 2 horde vs interior | Deck bench | `steamosctl` (E16) | Power steering |
| **X4** | Wilds' own VRS setting, Half Rate Shading, REFramework Lite Environment, each measured alone | Deck | 30 min | Quick Tier S/I wins; feeds X1 |
| **X5** | Limiter latency (E8, already planned) | Deck + phone | One evening | Latency baseline that DeckWarp must beat |
| **X6** | DeckWarp-D prototype in the in-game layer, Wilds only | Deck | Only if X2 passes | In-game warp quality |
| **X7** | INT8 network microbenchmark | Deck | After X1 | DeckSR |

X2 needs no Deck time and no risk, so it can start this week. X1 and X5 need one evening with the
Deck plugged in.

---

## 8. What this could add up to (speculative until X1–X3)

| | Wilds (Tier S + I) | Space Marine 2 (Tier S only) |
|---|---|---|
| Today, lowest settings | High teens–30 fps | 14–24 fps |
| + port surgery (fog/GI/shadows), VRS, power steering | Plausibly **30–38 fps**, a locked 30 everywhere, 40@80 Hz in lighter areas (est.) | Power steering and scheduler only: single digits; hordes stay CPU-bound (est.) |
| + DeckWarp | 90 Hz camera motion with *lower* camera latency than native, **if** the orbit-camera problem is solved (DeckWarp-D) | Only DeckWarp-C applies, the hardest case (third person, no depth) |
| Locked native 45 in open areas | Still unlikely | No |

**Your goal reframed, not dropped.** "Native 45" was a stand-in for *responsive and smooth*.
DeckWarp is the only idea here that could deliver smooth and responsive camera motion without
the hardware reaching 45. That is why it's the headline invention, and why its kill test runs
first.

## 9. What changes in DeckForge

DeckForge stops being only a **settings optimizer**. It becomes an **automated Deck port team**
with three modules, matched to the safety tiers:

| Module | What | Tier | Works with anti-cheat |
|---|---|---|---|
| Steering (Python, userspace) | Power steering, limiter, scheduler, settings, `df-run` | S | Yes |
| Presenter (gamescope fork, nested) | DeckWarp-C | S (no injection; a platform risk) | Yes |
| Retrofit (vkd3d-proton fork) | Port surgery, DeckWarp-D, DeckSR | I | No |

The existing Phase 1 work (discover, safety, `df-run`) feeds all three unchanged.

## 10. Income: possible, with care (brief)

What other tools don't have:
- per-game port profiles backed by evidence;
- DeckWarp.

A model that respects the licences (est.): an open-source core plus profiles as data, funded
through donations, Patreon or a paid convenience app. The constraints:
- OptiScaler is GPL;
- lsfg-vk is non-commercial;
- DLSS weights can't be redistributed;
- shipping modified copies of a game's shaders is legally different from shipping instructions
  that transform them on the user's machine.

Legal review comes before any paid offering. Not a decision for now.

## 11. Ruled out (and why)

- **Skipping passes from outside the game** to reuse last frame's shadows or fog: no prior art.
  It breaks on memory aliasing, stale camera matrices and history buffers [recon §5]. Allowed only
  inside port surgery, per game, if a pass is proven persistent.
- **Mobile upscalers (Arm ASR, Qualcomm GSR) as quality upgrades.** They are cheaper versions of
  FSR 2, not better ones [recon §1].
- **A generic "make every game cheaper" layer.** Every precedent ended up per-game [passes §1, §8].
- **HelixSR / DLSS weights.** Licensing [recon §2].

## 12. Decisions for Fede

| # | Decision | Recommendation |
|---|---|---|
| N1 | Adopt the "automated Deck port team" direction (sections 3–6, 9) next to Phase 1 | **Yes** |
| N2 | Run X2 (Mac, offline) now, and X1 + X5 at the next Deck evening | **Yes** |
| N3 | Accept that port surgery means maintaining a vkd3d-proton fork (Tier I games only) | Decide after X1 |
| N4 | Income model | Later, after a working prototype and legal review |
