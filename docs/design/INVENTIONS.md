# Past the settings menu: what DeckForge could invent

Status: **PROPOSED**, 2026-10-11, revised after an independent verifier review (FAIL → fixed).
It answers Fede's challenge: *"invent something new, something which by code alone can enhance
the experience natively on the Deck. Don't dismiss it because GeForce NOW or FSR exist."*

**Evidence.** Four research notes in `docs/research/2026-10-11-inventions/`:

| Cited as | File |
|---|---|
| [reprojection] | `reprojection_frame_warp.md` |
| [passes] | `per_pass_interception_vrs.md` |
| [cpu] | `cpu_power_io_levers.md` |
| [recon] | `reconstruction_amortization.md` |

Last night's notes and report, cited as [overnight …], live on branch `design/overnight-rethink`
(PR #2). E-numbered experiments (E1, E8, E16) are defined in that PR's `STRATEGY_OPTIONS.md` and
in the research compendium. The notes carry every source link.

**Labels:**
- **(est.)**: estimate or inference.
- **UNPROVEN**: nobody has demonstrated it.
- "none found": the research found no example. GitHub code search was blocked for part of this
  research, so treat these as "not found", not "doesn't exist".

---

## 1. The honest answer first

**Can code alone make Monster Hunter Wilds run at a locked native 45 fps with console image
quality on the Deck?** Nothing found supports it.
- **Wilds**, at the lowest settings: high teens to low 20s fps in open areas, below 20 near the
  Windward Plains watering hole, about 30 in quieter areas. Steam Deck HQ calls the problem "more
  related to the GPU than the CPU" (Jan 2026) [cpu §1].
- **Space Marine 2**: 14–24 fps, and it still couldn't hold 30 at a forced 640×400. That points
  to a bottleneck resolution can't fix, probably CPU or simulation [cpu §2].

**Can code alone make these games noticeably better on the Deck?** Probably by some margin, and
possibly by more in one specific way (camera motion). But not by searching harder through the
settings menu: for these two games that approach is close to its limit (est.). The remaining
headroom sits in five places. DeckForge could be the first tool *we know of* to go after all five
deliberately:

| Where performance hides | What DeckForge would try | Prior art found |
|---|---|---|
| Frames the camera needs vs frames the game needs | Show 90 Hz *camera* motion from a 30–45 fps game using your newest stick input (invention 1) | VR runtimes; engine-side flat-screen mods and demos. NVIDIA's game version was unreleased as of Aug 2026. No game-agnostic version found |
| Pixels a 7" screen can't show | Retrofit a game the way a console port team would: cheaper fog, GI, shadows (invention 2) | Hand-made per-game mods. No repeatable pipeline found |
| Watts in the wrong chip | Shift power between CPU and GPU frame by frame (invention 3) | Android and phones. No Deck test found |
| CPU work that could run elsewhere | Choose CPU or GPU texture decompression per scene in Wilds (add-on to invention 2) | A manual mod toggle exists |
| Image quality per millisecond | Our own small reconstruction model (research track) | Arm publishes a retrainable model |

All of this is UNPROVEN on the Deck, and some of it may fail. Each item has a test that can rule
it out early (section 7).

## 2. Why the Deck runs some heavy games well and not Wilds

**The Deck OLED:**
- GPU: 8 RDNA2 compute units at 1.6 GHz, about 1.6 TFLOPS [overnight platform §1].
- Memory: about 102 GB/s shared between CPU and GPU (88 GB/s on the LCD model) [overnight
  platform §1].
- CPU: a 4-core Zen 2 with only 4 MB of L3 and about 25 GB/s of CPU-side memory bandwidth
  [cpu §1].

By public spec sheets (est.) that is roughly a PS4-class GPU with a stronger CPU. Games authored
for that era fit. Wilds and Space Marine 2 were authored for the PS5 generation, which by the
same public specs has several times the GPU throughput and memory bandwidth, and twice the CPU
cores (est.).

A console port team closing that gap rewrites systems with source code. From outside the game,
DeckForge can change only three things:
1. what the engine exposes: settings files, REFramework scripts;
2. what the GPU command stream reveals: passes, shaders, render targets;
3. how frames are presented and how the chip is powered.

---

## 3. Invention 1 — DeckWarp: faster camera response between real frames

**What it does.** The game keeps rendering real frames at 30–45 fps. At each 90 Hz refresh in
between, DeckWarp re-projects the last real frame using your newest stick input, so turning the
camera responds faster. VR headsets have done this for years (asynchronous timewarp)
[reprojection §2].

**What it improves, and what it doesn't.**
- **Improves:** camera-rotation latency. Interpolation frame generation waits for the next frame
  and adds lag. On desktop measurements that is roughly 40–75 ms compared with native play using
  latency reduction, and at least 22 ms even in the best case [overnight report]. Reprojection
  uses input newer than the frame instead. NVIDIA's Reflex 2 Frame Warp cut THE FINALS from
  27 ms to 14 ms PC latency [reprojection §3]. NVIDIA Research found a rotation-only warp removed
  81% of the aiming penalty of an 80 ms-old frame, in a mouse-driven, first-person, 9-person
  study [reprojection §1].
- **Does not improve:** game-state latency, meaning hits, enemy movement and animation. Moving
  monsters and your character's animation still update at the real frame rate [reprojection §1,
  §2].

**Prior art found.**
- Gamescope (the SteamOS compositor) has no warp code [reprojection §6].
- Reflex 2 Frame Warp was "coming soon" as of August 2026; later status unconfirmed
  [reprojection §3].
- Flat-screen versions found are engine-side: the Comrade Stinger Unity demo, and the Minecraft
  mod `mc-ar-mod`, which is based on it [reprojection §4].
- None found works on arbitrary games. A game-agnostic DeckWarp would be the first *we know of*.

**Researcher's verdict: an R&D prototype with a high risk of a negative result**
[reprojection §1].

### Two forms

| | DeckWarp-C (compositor) | DeckWarp-D (inside the game process) |
|---|---|---|
| Where | A fork of gamescope (BSD-2 licensed). SteamOS's *session* gamescope composites on a realtime-priority queue just before each refresh. Whether a nested, user-installed fork gets that priority (it needs CAP_SYS_NICE) is UNVERIFIED [reprojection §7] | A Vulkan layer or vkd3d-proton fork capturing depth and the pre-HUD image |
| Inputs | Final image only (HUD baked in), plus stick or gyro from the Deck controller's hidraw device, which the logged-in user can access [reprojection §9] | Depth, for a positional warp. Possibly the HUD redrawn after warping, but recovering the game's camera matrix and UI pass is per-game reverse engineering, with no game-agnostic method found [reprojection §8] |
| Anti-cheat games (Space Marine 2) | **UNVERIFIED, decision N5.** No DeckForge code would run inside the game, but gamescope's own WSI layer already loads into game processes. NVIDIA's own paper notes that multiplayer late-warp may raise cheating concerns [reprojection §3, §7] | No (Tier I) |
| Quality ceiling | Lower | Higher |

### The hard problems, most dangerous first

1. **Low frame rates looked bad in the only public test.** A community Reflex 2 demo showed
   "major visual issues" at 30 *and* 60 fps caps, and that demo had engine camera data plus extra
   rendered border area. It looked fine at 100 fps [reprojection §3]. DeckWarp would start below
   60.
2. **Third-person orbit cameras.** Both test games orbit the camera around your character.
   A rotation-only warp slides everything, the character included: about 22 px per warped frame
   at a 180°/s turn. The next real frame then snaps it back (est.) [reprojection §11].
   - DeckWarp-D could correct this *if* the camera matrix can be recovered per game (UNPROVEN).
   - DeckWarp-C would need a trick, such as pinning the screen centre and warping only the
     periphery (UNPROVEN).
3. **Black or smeared screen edges.** Turning exposes 22–44 px per warped frame that was never
   rendered. Every subject in NVIDIA's study noticed the black edges. The best fix, rendering
   extra border area, is realistic only inside the game [reprojection §3, §8, §11].
4. **Predicting the camera from the stick.**
   - Games turn the camera with acceleration curves, dead zones and smoothing.
   - Steam Input layouts change what the stick even does (stick, mouse, flick stick).
   - A wrong prediction overshoots and snaps back.
   - Proposed fix: auto-calibrate per game by correlating recorded stick input with measured image
     motion. No published method found [reprojection §9, §10].
5. **HUD baked into the image.** Static HUD pieces can be detected because they don't move with
   the camera. Qualcomm patented one such method, which may constrain copying it exactly.
   Moving markers such as lock-on and damage numbers remain unsolved [reprojection §12].
6. **Getting the warp done in time while the game saturates the GPU.** This needs high-priority
   GPU queues. Linux SteamVR had years of trouble with exactly this on AMD [reprojection §2, §7].

**Cost.** The warp maths is tiny: about 0.1–0.3 ms per refresh at 800p (est.)
[reprojection §13]. The real costs are forcing a full composite every refresh, and contention
with the game. Learned inpainting is out of budget: PatchEX takes about 3 ms at 360p on an RTX
4080-class GPU [reprojection §5].

**Shipping without touching SteamOS.** Launch a nested, forked gamescope per game through a
launch option. Overhead, priority and latency are all UNVERIFIED [reprojection §7].

**Kill test X2, on the Mac, before any Deck code.**
1. Take 90 fps (or faster) third-person footage from any source.
2. Simulate the warp from every second frame. Estimate camera rotation from far-background motion,
   which approximates a good prediction.
3. Compare against the real in-between frames with a temporal image metric, and in a blind
   A/B by you.

If this optimistic case already shows visible character judder or edge artifacts, DeckWarp-C is
dropped for third-person games. DeckWarp-D (X6) is still evaluated separately.

---

## 4. Invention 2 — Port surgery: a repeatable retrofit pipeline

**What it does.** For one heavy game at a time:
1. Profile every GPU pass on the Deck.
2. Find the expensive passes a 7" screen barely shows: volumetric fog, GI, shadow resolution, AO,
   reflections.
3. Generate cheaper variants: smaller targets, fewer compute workgroups, or simplified shaders
   written with AI help.
4. A/B the variants automatically on the Deck with temporal image metrics.
5. Publish an evidence-backed **"port profile"** for that game and patch.

**Why the pipeline is the new part.** People have done single pieces by hand:
- NieR: Automata's FAR cut GI workgroups and disabled volumetric light by shader fingerprint.
- TBFix offered a "low-precision shadow mode".
- Emulators scale render targets, but every selective change ended up as a per-game rule
  [passes §1, §2].

None found makes this fast and repeatable. The original "AI writes cheaper shaders" idea fits
here as one candidate generator inside a measured, validated loop, never trusted on its own.

**Signals that it could matter for Wilds, with caveats:**
- The Deck community's REFramework "Lite Environment" GI and fog cuts "net significant gains"
  [passes §5]. But the guide is now marked outdated after Capcom's patches [cpu §1], and its
  no-frame-generation result was "close to 30 at 1024×640" [passes §5].
- Disabling GI and fog broke cutscenes until the mod re-enabled them [overnight game_file_levers].
- Wilds has its own VRS setting, which may work on the Deck. Untested [passes §4].
- Patched shaders miss Steam's precompiled shader cache, so the first run stutters. They also
  break whenever a game patch changes shader fingerprints [overnight report].

**Where to build it.** A fork of vkd3d-proton (the D3D12-to-Vulkan translator) rather than a
separate layer. It already owns shader translation [passes §3, §8].
- Tier I only.
- Wilds is a candidate pending a check of its anti-tamper and EULA, which hasn't been done
  [passes §7].
- Space Marine 2 never.

**Rough guesses for Wilds, speculative until profiled** [passes §8]:

| Cut | Frame-time saved |
|---|---|
| Fog/GI reductions | 5–20% |
| Shadow-map halving beyond the lowest preset | 2–8% |
| VRS | 0–8% |

The researcher's own conclusion: combined, these probably cannot close the 33–55% gap to a
locked 45.

**Add-on, Wilds only, Tier I: decompression routing.** Wilds ships Microsoft DirectStorage. A
REFramework mod already switches texture decompression between CPU and GPU: "GPU mode will
decrease CPU load at a price of GPU load increase" [cpu §3]. Choosing per scene would put
Fede's original "reroute CPU work to the GPU" idea in realistic form: GPU decompression in
CPU-bound hubs, CPU decompression in GPU-bound fields. Untested (X8).

**Kill test X1.** Take an RGP GPU profile of Wilds at the lowest preset in Windward Plains. Then
look at the share of GPU frame time in fog, GI, shadows, AO and reflections:

| Share | Verdict |
|---|---|
| ≥ ~40% | **Go.** A locked 30 in open areas becomes plausible |
| 20–40% | **Partial.** Helps quieter areas only |
| < 20% | **Stop** for Wilds |

---

## 5. Invention 3 — Power steering: put the watts where the bottleneck is

**What it does.** A small controller watches frame times. Where the GPU is the bottleneck, it
limits CPU boost or frequency so more of the shared 15 W can go to the GPU. Where the CPU is the
bottleneck, it does the reverse. It uses Valve's `steamosctl` controls and kernel interfaces, with
no injection [cpu §4].

**Why one fixed setting is probably wrong.** The notes suggest the bottleneck changes *within* a
game:
- Wilds is likely GPU-bound in open fields and CPU-heavy in camps and hubs.
- Space Marine 2 is likely CPU-bound in hordes [cpu §1, §2].

**Evidence from elsewhere:**
- AMD SmartShift targets laptops with a separate GPU [cpu §4].
- Phone research (Co-Cap) measured about 10% energy per frame saved at about 1% fps loss.
- An Android vendor case study (ADPF) reported +11% to +50% fps, but power also rose up to 9.9%
  [cpu §5].
- No Deck test was found, not even of a static CPU cap [cpu §4]. DeckForge's bench would produce
  the first numbers we know of.

**Honest size.** The Deck's power controller already favours the GPU: the CPU drops to about
2–3 W in GPU-bound scenes. Expect a few percent and steadier lows at best (est.) [cpu §4].

**Known obstacles:**
- **Steam's per-game performance profile** is re-applied at launch and can override
  DeckForge's settings. Re-asserting after launch "fights Steam" [overnight platform §3].
- **Permissions.** Whether `steamosctl` works for a third-party process without a password is
  unconfirmed. SMT and CPU frequency caps probably need root or a policy rule [cpu §4].

**Space Marine 2.** This is the only proposal for it that needs no new tier decision (Tier S).

**Cheap extras in the same module.** These are measured elsewhere, not on these games
[cpu §5, §6], and are tested in X8:
- the LAVD scheduler;
- low swappiness, which improved lows 10–21% on a Deck in other games, though SteamOS's current
  default is unknown, so the gain may be zero;
- transparent huge pages.

---

## 6. Research track — DeckSR: our own reconstruction model

**Why it's possible now.** Arm's Neural Super Sampling (NSS) ships weights that may be retrained
on your own content, with Apache-2.0 code and published training tools [recon §1, §3]. On the
licence:
- A model trained from scratch is ours.
- A retrained NSS stays under Arm's community licence, whose full text hasn't been read yet.
- Either route avoids NVIDIA's DLSS licence, the problem with HelixSR [recon §2].

**Why it's hard:**
- **No ML extensions on the Deck.** NSS needs Vulkan ML extensions the Deck's driver doesn't
  have, and Arm's emulation layer is untested on AMD. We would write our own INT8 compute shaders
  [recon §1, §3].
- **Training data.** Good training pairs need supersampled "ground truth" frames that commercial
  games can't give us. Copyright on captured game frames is unresolved [recon §3].
- **Training costs money.** It needs a modern GPU or a modest cloud budget [recon §3]. Fede owns
  no gaming PC, and decision 0001 limits spend to the Claude subscription [overnight
  alternative_approaches].
- **Cost on the Deck.** A network small enough for 1–2 ms at 800p is about 4–8 tiny layers
  [recon §2]. Arm's model would be about 2.5–3.5 ms on the Deck, similar to HelixSR [recon §1].
  Both are estimates.
- **Competition.** AMD promised a "lightweight" FSR 4 for integrated graphics by the end of 2026
  [recon §2].

**Kill test X7.** Benchmark a 6-layer INT8 network at 640×400 on the Deck's GPU. If it costs more
than 2.5 ms, stop. If it passes, budget decisions come next (N7).

---

## 7. Validation plan: tests that can rule each idea out early

| # | Test | Where | Needs | Decides |
|---|---|---|---|---|
| **X1** | RGP GPU profile of Wilds, lowest preset, Windward Plains (E1) | Deck + Fede, together | One evening | Port surgery: go / partial / stop (section 4 thresholds) |
| **X2** | Offline warp simulation on 90+ fps third-person footage, scored and blind-tested | Mac | Footage from any source | DeckWarp-C for third-person games |
| **X3** | Power A/B: CPU boost off / frequency caps vs GPU clock and fps; Wilds field vs hub, Space Marine 2 horde vs interior | Deck bench | `steamosctl` access (E16) | Power steering |
| **X4** | Wilds' own VRS setting, Half Rate Shading, REFramework Lite Environment, each alone | Deck | 30 min | Quick wins; feeds X1 |
| **X5** | Frame-limiter latency (E8) | Deck + phone | One evening | Latency baseline any warp must beat |
| **X6** | DeckWarp-D prototype in the in-game layer, Wilds only | Deck | After X2, whatever its result | In-game warp quality |
| **X7** | INT8 network microbenchmark | Deck | After X1 | DeckSR |
| **X8** | LAVD, swappiness, THP, and Wilds CPU/GPU decompression, each A/B | Deck bench | One evening | The cheap extras |

X2 can start this week without the Deck. X1, X4 and X5 fit in one Deck evening.

---

## 8. What this could add up to (speculative until X1–X3)

| | Wilds (Tier S + I) | Space Marine 2 (Tier S only) |
|---|---|---|
| Today, lowest settings | Below 20 in the worst open areas, about 30 in quieter ones | 14–24 fps |
| + port surgery, VRS, power steering | Roughly 21–31 fps in the worst open areas and 32–45 in quieter ones (est., from the ranges in section 4). A locked 30 everywhere only if X1 finds about 40% or more of GPU time in cuttable passes | Single-digit gains; hordes stay CPU-bound (est.) |
| + DeckWarp, if it survives X2/X6 | Faster camera response between real frames; game state still at the real frame rate | Only DeckWarp-C could apply, the hardest case, and only after decision N5 |
| Locked native 45 in open areas | Very unlikely | No |

**How DeckWarp relates to your target (decision N6).** Under decision 0001, the target is a locked
45 *native*. Generated frames count only as "presented fps" (QUALITY_TARGET.md). DeckWarp's warped
frames are generated frames, so under the current rule they would be reported as presented fps,
never as native. Counting "faster camera response" toward the target would mean changing 0001.
That is your call; this document doesn't make it.

## 9. What changes in DeckForge (if N1 is accepted)

DeckForge grows from a **settings optimizer** into an **automated Deck port team**, with three
modules matched to the safety tiers:

| Module | What | Tier | Anti-cheat games |
|---|---|---|---|
| Steering (Python, userspace) | Power steering, limiter, scheduler, settings, launcher | S | Yes |
| Presenter (nested gamescope fork) | DeckWarp-C | **Undecided (N5)** | **Unverified** |
| Retrofit (vkd3d-proton fork) | Port surgery, decompression routing, DeckWarp-D, DeckSR | I | No |

The Phase 1 scanner (PRs #3–#5) feeds all three. The `df-run` launcher exists only as a design
(LAUNCH_FLOW.md, PR #2), and launching a nested compositor would change what it starts.

## 10. Income: possible, with care

**What would be distinctive:** evidence-backed per-game port profiles, and DeckWarp if it works.

**A plausible model (est.):** an open-source core plus profiles shipped as data, funded by
donations, Patreon or a paid convenience app.

**Open legal questions, not researched or not resolved:**
- Arm's model licence text (unread).
- Qualcomm's HUD-mask patent.
- Copyright on captured game frames.
- Capcom's EULA on modification.
- Distributing modified game shaders versus distributing instructions that transform them on
  your machine (my guess, not legal advice).
- OptiScaler is GPL.
- lsfg-vk is non-commercial and no-derivatives.
- DLSS weights can't be redistributed.

Legal review comes before any paid offering.

## 11. Ruled out (and why)

- **Skipping passes from outside the game** to reuse last frame's shadows or fog. None found that
  does it, and it breaks on memory aliasing, stale camera matrices and history buffers
  [recon §5]. It is allowed only inside port surgery, per game, if a pass is proven persistent.
- **Mobile upscalers as quality upgrades.** Arm ASR is an optimized FSR 2. Qualcomm GSR 2 is a
  simpler Lanczos-based temporal upscaler. Both are cost tools, not quality upgrades over FSR 3.1
  [recon §1].
- **A generic "make every game cheaper" layer.** Every precedent found ended up per-game
  [passes §1, §8].
- **HelixSR / DLSS weights.** Licensing [recon §2].

## 12. Decisions for Fede

| # | Decision | Recommendation |
|---|---|---|
| N1 | Adopt the "automated Deck port team" direction alongside Phase 1 | Yes, as experiments first (section 7) |
| N2 | Run X2 (Mac) now, and X1 + X4 + X5 at the next Deck evening | Yes |
| N3 | Accept maintaining a vkd3d-proton fork for port surgery (Tier I games only) | Decide after X1 |
| N4 | Income model | Later, after a working prototype and legal review |
| N5 | Treat a nested, forked compositor (DeckWarp-C) as Tier S, i.e. allowed for anti-cheat games? Only defensible if no DeckForge or modified layer ever loads into the game | Undecided. Not before X2 passes and the anti-cheat question is researched |
| N6 | Should "faster camera response" from DeckWarp count toward your target, or stay "presented fps" as decision 0001 says today? | Keep 0001 as is until DeckWarp is proven |
| N7 | Spend money on training hardware or cloud for DeckSR (outside the subscription-only budget)? | Only if X7 passes |
