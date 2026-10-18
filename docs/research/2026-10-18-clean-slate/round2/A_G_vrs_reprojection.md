# Round 2 sceptic review: Clusters A (forced VRS) and G (gamescope reprojection)

I read RADV's code from current Mesa main (27.0-devel, through the GitHub mirror chaotic-cx/mesa-mirror, because gitlab.freedesktop.org is blocked by the proxy), gamescope at commit 6867f50 (27 Sep 2026), vkd3d-proton, and the session scripts. Unless marked otherwise, Mesa line numbers are in `src/amd/vulkan/`.

## A. Driver-forced, motion-aware VRS

### What the code does
- **It is already on in every game on a stock Deck.**
  - Mesa says so: "RADV_FORCE_VRS_CONFIG_FILE is only applied to gfx10.3 APUs and is used by SteamOS" (`radv_device.c:1513-1528`). The condition is `GFX10_3 && !has_dedicated_vram`.
  - The session exports the file and writes `1x1` into it (ChimeraOS's copy of the Deck session, `gamescope-session-plus:62,96-99`, https://github.com/ChimeraOS/gamescope-session). It also sets `STEAM_USE_DYNAMIC_VRS=1` (`sessions.d/steam:29`), and gamescope `main.cpp:648` refers to that variable.
  - The user-facing control is the Quick Access Menu's **"Half Rate Shading"** toggle, which can be set per game. Users report it makes UI text unreadable in some games and does nothing in others (https://steamcommunity.com/app/1675200/discussions/0/4139438126592899261). [checked plumbing. The toggle → file link is inferred.]
- **`RADV_FORCE_VRS=2x2 %command%` does nothing on SteamOS.** The config-file variable takes precedence (`radv_device.c:1517-1534`). Round 1's one-evening test (7_outsider #2) would have measured nothing. Use the Steam toggle, or point the config-file variable at your own file per game.
- **Which pipelines it skips:**
  - mesh-shader pipelines: "Mesh shaders aren't considered" (`radv_pipeline_graphics.c:1948-1950`);
  - pipelines with no pixel shader (`:1956`);
  - pipelines that set their own primitive shading rate (`:1952`);
  - 8× MSAA or sample shading (`:1766-1770`);
  - draws whose vertex position has a constant W of 1.0, i.e. 2D, full-screen post and UI passes (`radv_shader_info.c:157-166`);
  - pixel shaders that can discard (alpha-tested foliage);
  - pixel shaders that read FragCoord. That is any HLSL shader that uses SV_Position, such as deferred lighting, soft particles, depth-fade translucency and dithered fades: "breaks postprocessing in some games" (`radv_shader_info.c:923-929`);
  - shaders using sample mask or interlock (`:917-921`);
  - any draw where the game sets its own VRS rate (`radv_cmd_buffer.c:4719-4723`);
  - all compute work. [checked]
- **How the rate is applied.** It is a user SGPR (a shader constant register) written when the command buffer is recorded (`radv_cmd_buffer.c:13103-13141`, made dirty when a shader is bound, `:9248`).
  - The pipeline key holds only a yes/no flag (`radv_pipeline_graphics.c:1770`), and SteamOS already sets that flag for every game. **Changing the rate causes no recompiles and no pipeline-cache misses.** [checked]
  - Caveat: if the variable is *unset*, the key flips and Valve's precompiled cache misses. Never unset it.
- **Switch latency.** Round 1 said changes "apply immediately". [contradicted]
  - The notifier thread polls a non-blocking inotify handle every 100 ms, then sleeps another 100 ms before re-reading the file (`radv_device.c:395-430`). Command buffers already recorded keep the old rate.
  - Total delay: **~120–250 ms**.
  - Gotcha: `fread(buf,4,1)` needs 4 bytes, so writing `2x1` with no newline silently means 1x1 (`:382-385`).
- **Marek Olšák's Mesa 26.2 VRS work.** [checked: Phoronix, 6 Jul 2026, MR 42242, https://phoronix.com/news/Marek-Double-VRS-RADV-Perf]
  - It rewrites the VRS state handling for VRS the game requests itself: flat shading under dynamic VRS (mainly vkd3d-proton) and an RB+ edge case.
  - "Double performance" applies only to those cases. Nothing says it changes the forced path. **Irrelevant to A's budget.**
- **No controlled measurement on a Deck exists** that I could find, after four years of the toggle shipping: only anecdotes ("helped" in the Wilds benchmark, with no before/after numbers, https://steamcommunity.com/app/2246340/discussions/0/597391898829653004). The desktop "+8% at 4K" figure: [could not verify]. The "30%+ in some games, nothing in others" claim: [checked, no titles named, https://www.basnieuwenhuizen.nl/a-first-foray-into-rendering-less/]. The "power saving" intent: [checked, MR 14713 per WebFetch].

### What the exclusions do to the budget (est.)
The Round 1 budgets (1.8–5 ms) counted translucency, Nanite materials and post. Each of these is excluded or is compute work:
- UE5 Nanite hardware rasterization runs as mesh shaders or reads FragCoord.
- Nanite materials and Lumen are compute, or are FragCoord-reading quads.
- Post is compute or a W=1 full-screen pass.
- Foliage discards.

Eligible work = opaque, non-discarding, non-FragCoord raster pixel shaders. 2x2 saves ~40–50% of that, because helper lanes and render-output/bandwidth costs don't shrink.

| Engine | Eligible share | Saved at 2x2 (pess / central / opt) |
|---|---|---|
| UE5 Nanite + Lumen (Wukong, Stalker 2) | 0–6% of ~50 ms | **0 / 0.4 / 1.4 ms** |
| RE Engine (Wilds) | 5–25% | **0.9 / 2.4 / 5 ms** |
| Alan Wake 2 (mesh shaders) | — | **0** |
| Raster-heavy engines (Space Marine 2) | 10–30% (est.) | 1.5 / 3 / 5 ms |

- **Wilds already ships its own "Variable Rate Shading" option** (https://www.pcgamesn.com/monster-hunter-wilds/settings). When the game's VRS is on, the forced rate is bypassed.
- vkd3d-proton reports VRS Tier 2 when RADV offers shading-rate attachments (`libs/vkd3d/device.c:1007-1026`). RADV offers them on GFX10.3 with 8×8 tiles (`radv_physical_device.c:168-171,1251,1799`). So the game-side option should be available on the Deck [not device-verified].
- **Double-counting:**
  - Lowering internal resolution (D1, render-scale items in E) shrinks the same pixel-shader milliseconds.
  - Watts freed at the 15 W cap are already counted in C.

### A correction that hits A and G
Round 1 treated **game-camera degrees as retinal degrees**.
- At 35 cm the screen spans 25.7°, against a ~90° game field of view. One game-degree is about 14 px, not 49.
- A 20°/s camera pan is therefore ~5.8°/s on the retina, not 20°/s. The 18 px smear in 1_console_port's "invisible 2×2" claim is really about 6 px. The 98 px judder step in 3_perception's motion-blur idea is really about 28 px.
- Motion masking is about 3–3.5× weaker than Round 1 assumed.

### How A fails
- In orbit cameras the eye fixates on the character, which is **stationary on screen** during pans. A frame-wide rate coarsens exactly what is being looked at.
- A 120–250 ms lag means coarse shading **persists after the camera stops**, which is when acuity comes back.
- **A pan-only saving does not help a locked 45 fps.** The static frames still have to fit the budget.
- Visible artifacts:
  - UI drawn with non-constant W (3D/world-space UI) gets blurred;
  - coarse shading on a 640×400 internal image feeds the upscaler 320×200-equivalent interiors;
  - banding near black on the OLED.

### Tier
The environment variable and Steam toggle are Tier S, including for anti-cheat games. A patched Mesa counts as Tier I until it is upstream.

### Verdicts
- **A1, blanket 2x2: SURVIVES WITH CHANGES.** It already ships as Half Rate Shading. DeckForge's only gain is *measuring* per game where it pays: fold it into E's perceptual price list as one menu item.
- **A2, motion-gated daemon: SURVIVES WITH CHANGES.**
  1. Gate on GPU load first (go 2x1 when GPU frame time stays above 21 ms for 300 ms or more). That serves the 45 fps lock, and the 200 ms lag is fine for sustained load.
  2. Use motion only as a preference, triggered by stick deflection rather than image motion; the stick leads the camera by ~45–70 ms.
  3. First-person games only.
  4. One file per game via a launch option, so it doesn't fight Steam's toggle.
  5. Write `"2x1\n"`.
- **A3, per-pipeline-class policy: DEAD as Tier S.**
  - The targets it names (post, particles) are deliberately excluded for correctness.
  - Rescue tried: a per-pipeline-hash allowlist in a Mesa patch. That makes it Tier I, worth ≤0.8 ms in VFX-heavy scenes (est.). Parked.
- **A4, per-tile rate image: SURVIVES WITH CHANGES.**
  - The Tier S route is the engines' own VRS: Wilds' option, and UE5's `r.VRS.Enable`/`r.VRS.EnableImage` cvars plus its ContrastAdaptiveShading source, applied to the base and transparency passes (https://dev.epicgames.com/documentation/unreal-engine/xr-performance-features-in-unreal-engine, https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/Renderer/FVariableRateShadingImageManager/EVRSSourceType). Whether 5.0/5.1 titles have these: [could not verify].
  - The darkness/gaze map stays a Tier I layer idea for later.

### Falsification experiment for A (≤2 weeks)
**Week 1: the owner does it by hand, no code.**
- Setup: bench Deck OLED. GPU clock pinned at 1600 MHz from the Quick Access Menu for the cost pass, then a second pass at the default 15 W.
- Games:
  - Wukong benchmark and Wilds benchmark (both free);
  - Space Marine 2 and Stalker 2;
  - Alan Wake 2 as the control, which should show no gain.
- Runs: 3× Half Rate Shading off, 3× on. For Wilds, also a run with the game's own VRS on and the Steam toggle off.
- Logging: MangoHud frame-time log. Lossless screenshots at 3 fixed benchmark timestamps (turn on Steam's uncompressed-screenshot option).
- **Pass:** saves ≥2.0 ms in at least 2 of the 4 test games.
- **Kill A2/A3:** saves <1.0 ms in at least 3 of 4. Blanket 2x2 is the ceiling for any governor.
- **Sanity check:** if Alan Wake 2 gains ≥0.3 ms, my source reading is wrong; re-examine.
- **Quality:** ColorVideoVDP with a custom Deck display model, compared against "one upscaler-quality step lower" at equal milliseconds. **Kill A1** if VRS loses more quality (JOD) per ms saved than lowering render scale.

**Week 2, only if Week 1 passes:**
- The A2 daemon runs on a first-person game. It logs its own write times and RADV's "Updated the per-vertex VRS rate" stderr line, which gives the switch latency.
- Blind test: gating on or off at random in 60 s blocks, ≥5 viewers × 20 blocks.
- **Kill** if detection is above 75%, or the measured gain under load is below 8%.

## G. Stick/gyro-latched reprojection in gamescope

### Facts
- **gamescope has no reprojection, warp or extrapolation code.** It paints only when there is a new frame or an overlay change (`steamcompmgr.cpp:10606-10617`); otherwise the display controller **holds** the last buffer. A missed frame at a 45 fps cap is held for 33 ms. The cap releases frames every Nth vblank (`:6828-6833`). [checked]
- gamescope does have a REALTIME-priority queue (`rendervulkan.cpp:540-545`). [checked]
- **Input.**
  - gamescope reads only seat0 keyboard, mouse and touch through libinput. No gamepad, joystick or raw HID code exists in `src/`. [checked by grep]
  - Reading Steam's virtual-pad input device read-only, without grabbing it, doesn't steal events. That is standard Linux input semantics; [not verified on a Deck]. It gives post-Steam-Input values, which is what the game sees.
  - The Deck's motion sensors are a separate input device since the hid-steam patch (https://phoronix.com/news/Steam-Deck-IMU-For-HID-Driver). Whether that device stays live while Steam holds the raw controller: [could not verify].
  - Gyro-as-mouse already reaches gamescope's own pointer path [inference].
- **Measured latency on the Deck OLED.** Digital Foundry with NVIDIA LDAT: Crysis 3 Remastered 65.2 ms at 90 Hz, Doom Eternal 51.1 ms (https://www.pcgamesn.com/steam-deck/oled-input-lag) [checked; frame rate not stated]. The 2022 camera tests (75–146 ms with caps, https://www.tomshardware.com/news/steam-deck-framerate-limiter-egregiously-raises-input-latency) predate later limiter work. A heavy game at a 45 fps lock: ~70–100 ms (est.).
- **lsfg-vk is a Vulkan layer that "hooks into Vulkan applications"** (https://lsfg-vk.dev). That is in-process, so **Tier I** under project rules.
  - It generates intermediate frames (Lossless Scaling Frame Generation 3.1). No extrapolation mode is mentioned anywhere.
  - Version 2.0 added FP16. The August 2026 experimental build fixed small-object ghosting but not latency (https://windowsforum.com/windows-news.4/steam-deck-lsfg-vk-experimental-fixes-ghosting-not-latency.442030/).
  - No measured Deck latency has been published.
  - **G's real niche: anti-cheat games, and smoothing that adds no latency.**
- **Prior-art warning.** A demo of NVIDIA's Frame Warp, which has depth and inpainting, still showed visible edge artifacts at 90 fps (https://tech.yahoo.com/computing/articles/intrepid-modder-builds-frame-warp-100200888.html). G has no depth and a horizon up to twice as long.

### Is 320×200 optical flow good enough for orbit cameras?
- After the field-of-view correction, the strip uncovered next to the character at 90°/s and an 11.1 ms horizon is **~14 px**, not 49.
- Flow at 320×200 is in 4 px blocks, and its edges smear over 1–3 blocks, so 4–12 px.
- The silhouette error is therefore about as big as the strip itself. It sits **at the fixation point** and alternates at 45 Hz.
- The TRM result (alternating degraded frames look fine at 90 Hz) was shown for blur, not for misplaced edges. It doesn't transfer.
- Expected outcome: visible halo shimmer around the character [est.; needs the test below].

### "50–90 → 10–20 ms" latency claim
Overstated. Without the game's actual camera transform (the input NVIDIA Reflex 2 receives), the warp must predict the game's own stick smoothing and acceleration. Errors show up as a snap-back on every real frame: a 20% error in angular speed at a 45 ms horizon is ~11 px of jitter.

### Budget (est., nothing measured)
- **GPU per real frame:**
  - optical flow 0.3 / 0.5 / 0.8 ms;
  - warp plus composite per synthetic vblank 0.15 / 0.25 / 0.4 ms;
  - losing direct scanout 0.1 / 0.15 / 0.25 ms.
- **Total 0.55 / 0.9 / 1.45 ms per 22.2 ms frame**, so **−2.5 / −4 / −6.5% native fps** when GPU-bound. Rotation-only skips the flow: 0.25–0.65 ms.
- This cost comes *out of* the native target. Power adds +0.2–0.5 W at 90 Hz.
- **Onset latency gain:**
  - constant-velocity mode 0 / 3 / 6 ms;
  - stick-latched mode 10 / 30 / 50 ms, and only if the per-game curve error is under ~10%.

### How G fails
- silhouette tearing;
- semi-transparent HUD;
- viewmodel and HUD shifting under the rotation warp;
- an overshoot when the stick is released;
- missed composites under GPU saturation, giving an irregular cadence that is worse than steady judder.

SteamOS's read-only root filesystem and its updates replace gamescope. So the experiment must run a user-built gamescope **nested** through a launch option (+0–11 ms, est.), and shipping it needs an upstream change at Valve.

### Verdicts
- **G2, first-person rotation warp: SURVIVES WITH CHANGES.**
  - v1 is constant-velocity extrapolation for the in-between vblank only, stopped when the stick is released or reversed, with screen-locked pixels (zero flow) masked. Judge it on smoothness.
  - v2 adds stick latching, judged on latency.
  - Report presented fps separately from native fps.
- **G1, orbit flow warp: SURVIVES WITH CHANGES, provisionally.**
  - The rescue is a rotation-model warp of the background only, leaving pixels that disagree with the model (the character) unwarped, with a feathered seam.
  - **DEAD if the offline silhouette test fails.**

### Falsification experiment for G (≤2 weeks)
**Week 1: offline on a PC, an engineer, no Deck.**
- Record lossless 90 fps at 1280×800 with scripted pans from a virtual gamepad at 30, 90 and 180°/s. One first-person game (Stalker 2) and one orbit-camera game (Wilds).
- Decimate to 45 fps. Synthesize the in-between frames with:
  - (a) frame repeat;
  - (b) rotation warp;
  - (c) 320×200 flow warp (OpenCV DIS as a proxy).
- Score against the true 90 fps frames: ColorVideoVDP on the Deck display model, plus FLIP inside a 24 px band around a segmented character mask.
- **Pass:** (b) or (c) beats repeat by ≥0.3 JOD on pans.
- **Kill G1:** band FLIP above 0.15 in more than 25% of synthetic frames.

**Week 2: bench Deck.**
- The owner pastes a launch option that runs the nested build.
- Measure native fps at 15 W with the warp on vs the nested build with the warp off. **Kill** if the cost exceeds 3%.
- Latency: the owner films the stick and screen with a 240 fps phone, 20 flicks per configuration. Stick-latched mode **passes** at a ≥20 ms median onset gain and is **killed** below 10 ms.
- Blind two-choice "which is smoother": ≥5 people × 20 trials. **Pass** at ≥70% preferring the warp with artifacts reported in <20% of trials; **kill** below 60%.
- Also compare against lsfg-vk on a game without anti-cheat.

## Verdict table
| Idea | Verdict |
|---|---|
| A1 blanket forced VRS | SURVIVES WITH CHANGES (already ships as Half Rate Shading; becomes an E menu item) |
| A2 motion-gated daemon | SURVIVES WITH CHANGES (gate on load, stick-predicted, first-person only) |
| A3 per-class policy | DEAD as Tier S (Tier I allowlist parked) |
| A4 per-tile map | SURVIVES WITH CHANGES (use the engine's own VRS first) |
| G1 orbit flow warp | SURVIVES WITH CHANGES, provisional; dies if the silhouette test fails |
| G2 first-person rotation warp | SURVIVES WITH CHANGES |

## What would change my mind
- **A1:** a controlled Deck run where the toggle saves ≥3 ms in a UE5 Nanite title, which would mean my exclusion analysis is wrong.
- **A2:** a 2-line Mesa change upstream (blocking `poll`, no 100 ms sleep), making switching per pan feasible.
- **A3:** evidence that FragCoord-reading particle shaders coarsen cleanly, plus RADV maintainers accepting a hash allowlist upstream.
- **A4:** RGP captures showing UE5's base and transparency passes are ≥15% of a Deck frame.
- **G1:** band errors under 10% of synthetic frames at 90°/s with 320×200 flow.
- **G2:** a measured onset gain under 10 ms, or a native-fps cost above 3%, would kill it.

**Key facts to keep:**
- SteamOS already enables RADV's forced VRS for every game (Half Rate Shading). `RADV_FORCE_VRS` is ignored there.
- A rate switch takes 120–250 ms, and the file needs a 4-byte write including the newline.
- Forced VRS skips mesh shaders, FragCoord-reading shaders, discarding shaders and constant-W (full-screen and UI) draws.
- lsfg-vk is an in-process Vulkan layer (Tier I) and only interpolates.
- Digital Foundry measured 51–65 ms button-to-photon on the Deck OLED.
