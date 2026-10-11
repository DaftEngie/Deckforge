Notes for caller: research was done 11 Oct 2026. Gamescope findings come from a shallow clone of ValveSoftware/gamescope at HEAD 81146cab (10 Oct 2026), which I grepped but did not build or run. I couldn't reach these sources: GitHub code and issue search (blocked for this session), sites.cs.ucsb.edu (blocked by the proxy, so no GFFE or Mob-FGSR PDFs), and the Comrade Stinger and 2kliksphilip primary pages (not indexed by the search tool). No files were written. Possible memory item for the DeckForge project: "Reprojection research (Oct 2026): gamescope has no warp code and no gamepad path; Reflex 2 Frame Warp still unshipped as of Aug 2026; the community Frame Warp demo showed major artifacts at 30–60 fps."

# Input-driven reprojection ("async timewarp" / "frame warp") for flat-screen games on Steam Deck OLED

## 1. Overall feasibility: can a tool render at 30–45 real fps and present 90 Hz camera motion by warping with the newest stick input?

### Takeaway
A rotation-only warp at 800p is technically buildable and cheap in raw GPU terms on the Deck. Nobody has shipped one outside VR, though, and every documented system that works gets the new camera pose from the engine, not from raw controller input. The best public flat-screen data point is the closest analogue to our range: a community Reflex 2 demo showed "major visual issues" at 30 and 60 fps caps. Treat this as an R&D prototype with a high risk of a negative result, not as a product feature.

### Cited Findings
- Reflex 2 Frame Warp has the CPU compute the camera position for the next frame from the newest input. It then warps the frame the GPU just rendered to that position right before display, and fills disocclusions from "camera, color, and depth data from prior frames". — [NVIDIA](https://www.nvidia.com/en-us/geforce/news/reflex-2-even-lower-latency-gameplay-with-frame-warp/)
- PureDark's unofficial Frame Warp demo (Oct 2025) showed "major visual issues" when moving the camera at 30 and 60 fps caps. There were no major issues at 100 fps, and 120 fps looked better still. — [DSOGaming](https://www.dsogaming.com/news/first-nvidia-reflex-2-tech-demo-available-for-download/)
- As of 16 Aug 2026, NVIDIA's page still said Frame Warp was "coming soon". Neither launch title (THE FINALS, VALORANT) had a public implementation, and NVIDIA had not explained the delay. — [gaming-st.com](https://gaming-st.com/news/nvidia-reflex-2-frame-warp-not-released-2026/); this matches headlines at [itc.ua](https://itc.ua/news/nvidia-reklamyruet-funktsyyu-reflex-2-kotoruyu-do-syh-por-ne-vypustyla-spustya-18-mesyatsev-posle-anonsa/amp/) ("still not released 18 months after announcement") and [PCGH](https://www.pcgameshardware.de/Grafikkarten-Grafikkarte-97980/News/Nvidia-Reflex-2-Frame-Warp-1463017/).
- NVIDIA Research (HPG 2020, older): a rotation-only late warp of an 80 ms-old frame at 60 Hz removed 81.3% of the aiming-time penalty from the added latency. This was for mouse input, first person, an abstract scene and 9 subjects. — [Kim et al., NVIDIA](https://research.nvidia.com/sites/default/files/pubs/2020-07_Post-Render-Warp-with/HPG_2020_Latewarp_AuthorVersion_0.pdf)
- Oculus guidance (2015, older): ATW is "pothole insurance", not a substitute for a sustained 90 Hz. It should run at a fixed fraction of the refresh rate ("hit 90Hz or fall down to the half-rate of 45Hz with ATW"), because intermediate rates are a worse artifact. — [Meta/Oculus, ATW Examined](https://developers.meta.com/horizon/blog/asynchronous-timewarp-examined/)
- Deck OLED hardware: 8 RDNA2 CUs at 1.6 GHz (1.6 TFLOPS FP32), LPDDR5 at 6400 MT/s on quad 32-bit channels, 1280×800 HDR OLED up to 90 Hz, 6 nm APU. — [steamdeck.com/tech](https://www.steamdeck.com/en/tech)

### Inferences
- At a locked 45 fps on 90 Hz, every real frame is followed by one warped frame about 11.1 ms later. At 30 fps there are two (about 11.1 and 22.2 ms). That cadence fits the Oculus "fixed fraction" advice. 30 fps is the region where the community Frame Warp demo looked bad, and it was at least rendering extra off-screen area (overscan) and had engine camera data.
- The decisive difference from Reflex 2 and the HPG paper is that they know the exact new camera pose: the engine computes it, or mouse counts map one-to-one to an angle. A tool outside the game has to *predict* what the game's camera will do from raw stick deflection. The prediction has to cover per-game response curves, acceleration and smoothing (see Q10). A wrong prediction produces overshoot and snap-back when the real frame arrives, which may look worse than no warp.
- The warp only lowers *camera-rotation* latency. Game-state latency (enemy motion, hits, animation) is unchanged. In the HPG study, predictable-target conditions still lagged the true low-latency condition by about 72–98 ms.

### Gaps
- No public measurement exists of flat-screen reprojection at 30–45 fps on a handheld or a mobile-class GPU.
- I couldn't confirm whether Reflex 2 shipped anywhere between August and October 2026.

## 2. VR prior art: ATW, ASW/AppSW, SteamVR Motion Smoothing (cost and artifacts)

### Takeaway
VR runtimes prove that rotation-only reprojection is cheap and robust for *rotation*. They also document its standard failures: positional judder on near objects, moving objects frozen at the real frame rate, specular judder, black edges. Depth-based "positional" warps need app-supplied depth and motion vectors, cost more, and still guess at disocclusions. None of these sources publishes per-frame millisecond costs on mobile GPUs.

### Cited Findings
- Orientation-only timewarp is a cheap 2D warp. Positional warp needs depth and produces disocclusion artifacts at object edges. — [ATW Examined (2015, older)](https://developers.meta.com/horizon/blog/asynchronous-timewarp-examined/)
- ATW artifacts — [ATW Examined (2015, older)](https://developers.meta.com/horizon/blog/asynchronous-timewarp-examined/):
  - Positional judder on near-field objects when the head translates.
  - Moving objects are "effectively frozen in time" between real frames.
  - Specular, reflection and parallax-mapping judder.
- Requirements and failure mode — [same](https://developers.meta.com/horizon/blog/asynchronous-timewarp-examined/):
  - ATW needs GPU preemption at about 2 ms granularity or better, because "a single large draw call with a complex shader can easily take 10 ms".
  - If preemption is too slow, the warped frame misses vsync and the old frame repeats (judder).
- Gear VR used rotation-only ATW. The post gives no millisecond cost. — [same](https://developers.meta.com/horizon/blog/asynchronous-timewarp-examined/)
- Meta OS compositor: "Pure camera rotation introduces no parallax", so rotational timewarp is cheap. — [Meta OS compositor docs](https://developers.meta.com/horizon/documentation/native/android/os-compositor)
  - Positional timewarp is "a more expensive algorithm". It uses app-submitted depth, fills exposed pixels with guesses from neighbours, and is enabled only together with AppSW.
  - Black bars appear at the edges when rotation exposes the frame border.
- Quest Application SpaceWarp needs an app-rendered motion-vector texture (opaque objects only) plus depth. It gave apps "up to 70 percent additional compute". Unmodified materials produce artifacts. — [Meta AppSW docs](https://developers.meta.com/horizon/documentation/native/android/mobile-asw/)
- History (older) — [Wikipedia, citing Valve/Oculus posts](https://en.wikipedia.org/wiki/Asynchronous_reprojection):
  - Valve's interleaved reprojection ran apps at half rate and reprojected every other frame (2016).
  - ASW (2016) uses depth to extrapolate.
  - ASW 2.0 (2019) added positional timewarp.
  - SteamVR Motion Smoothing (Nov 2018) can synthesize two frames instead of one.
- SteamVR async reprojection on Linux has been fragile — [GamingOnLinux 2021](https://gamingonlinux.com/2021/08/having-vr-issues-on-linux-you-should-look-to-disable-async-reprojection); [GamingOnLinux 2024](https://www.gamingonlinux.com/2024/05/steamvr-for-linux-gets-experimental-improvements-to-async-support/):
  - In 2021 it caused jitter and "-203" crashes on AMD and NVIDIA. The workaround was disabling `enableLinuxVulkanAsync`.
  - In May 2024 SteamVR beta 2.6.2 listed "Experimental improvements to async support".
  - A reader reported a fix for the compositor failing to get permission to create a high-priority queue.

### Inferences
- The GPU-scheduling problem (a warp must finish before vblank while the game saturates the GPU) is the same one Linux SteamVR struggled with on AMD for years. Expect this to be a large share of the engineering risk, more than the shader itself.

### Gaps
- No published millisecond cost for ATW or positional timewarp on Adreno, Mali or other mobile GPUs.
- No primary Valve technical write-up of Motion Smoothing was retrievable; the announcement page body didn't load.

## 3. NVIDIA Reflex 2 Frame Warp: mechanism, measured results, status

### Takeaway
Frame Warp is in-engine. It takes a CPU-computed late camera pose and warps with color and depth, plus history-based "predictive" inpainting of disocclusions. NVIDIA's one headline number is 27 → 14 ms PC latency in THE FINALS on an RTX 5070. It was still unreleased as of August 2026. The community demo needed overscan to fix edges and looked bad at 30–60 fps.

### Cited Findings
- THE FINALS, 4K max settings, RTX 5070 — [NVIDIA](https://www.nvidia.com/en-us/geforce/news/reflex-2-even-lower-latency-gameplay-with-frame-warp/):
  - No Reflex: 56 ms
  - Reflex Low Latency: 27 ms
  - Reflex 2 with Frame Warp: 14 ms
- Other NVIDIA claims — [same](https://www.nvidia.com/en-us/geforce/news/reflex-2-even-lower-latency-gameplay-with-frame-warp/):
  - VALORANT on an RTX 5090: under 3 ms.
  - Frame Warp cuts "nearly an entire frametime".
  - Launches on RTX 50 first; other RTX GPUs later.
  - No per-warp cost and no HUD handling are described.
- NVIDIA reportedly told developers integration takes about half a day. It said Frame Warp would expand to DLSS Frame Generation titles, with no dates. — [gaming-st.com](https://gaming-st.com/news/nvidia-reflex-2-frame-warp-not-released-2026/)
- PureDark's first demo was rebuilt from ARC Raiders playtest data and ran on RTX 20 and 30 series cards. — [gaming-st.com](https://gaming-st.com/news/nvidia-reflex-2-frame-warp-not-released-2026/); [DSOGaming](https://www.dsogaming.com/news/first-nvidia-reflex-2-tech-demo-available-for-download/)
- PureDark's v2 (Oct 2025) — [DSOGaming v2](https://www.dsogaming.com/pc-performance-analyses/puredark-has-released-a-new-version-of-his-nvidia-reflex-2-tech-demo-that-fixes-the-visual-border-issues/):
  - Renders 25% extra off-screen area per side, at a 4×4 variable-rate-shading rate (about 1/16 of the pixels), to fix the edge artifacts.
  - Reported as "a slight performance hit", with no numbers.
- Predecessor research: Kim et al. (HPG 2020, older) — [NVIDIA Research](https://research.nvidia.com/publication/2020-07_Post-Render-Warp-with); [PDF](https://research.nvidia.com/sites/default/files/pubs/2020-07_Post-Render-Warp-with/HPG_2020_Latewarp_AuthorVersion_0.pdf):
  - The rotation-only warp had no guard band, so missing pixels showed black. Every subject noticed, but performance was not significantly hurt.
  - Translation needs depth and/or velocity.
  - The HUD and weapon model should be composited after the warp.
  - Multiplayer late-warp may raise cheating concerns.

### Inferences
- NVIDIA's numbers come from high-fps desktop games, not 30–45 fps rendering. The only low-fps evidence (PureDark) is negative.

### Gaps
- The Frame Warp inpainting algorithm, HUD/UI handling, cost in ms and any SDK documentation are not public in the sources I found.

## 4. Flat-screen async reprojection demos and open implementations (Comrade Stinger, 2kliksphilip, follow-ups)

### Takeaway
The Comrade Stinger Unity demo is confirmed to exist and seeded at least one open-source port: the Minecraft mod `mc-ar-mod` (LGPL-3.0, latest release January 2024, 22 stars). I couldn't retrieve primary pages for the demo or the 2kliksphilip video. No follow-up targets arbitrary games, Linux compositors or the Deck.

### Cited Findings
- `mt1006/mc-ar-mod` — [GitHub](https://github.com/mt1006/mc-ar-mod):
  - Asynchronous reprojection for Minecraft via a second rendering context, reprojecting with the new camera rotation and player position.
  - Fabric build on Windows and Linux. Says it "greatly reduces performance of main rendering thread (even when disabled)".
  - Glitches include the camera rotating when GUIs open or close, and random crashes.
  - Shader code is "based on Comrade Stinger's demo".
- `viitana/projector` is a WIP "highly experimental asynchronous reprojection demo application built on Vulkan". It has its own first-person scene and needs Vulkan 1.3 plus variable rate shading support (RDNA2 or newer listed). — [GitHub README](https://github.com/viitana/projector)
- An Elite Dangerous forum thread cites the videos "Async Reprojection outside of VR" and an LTT "asynchronous reprojection test". — [Frontier forums](https://forums.frontier.co.uk/threads/elite-dangerous-performance-asynchronous-reprojection-for-non-vr.611900)
  - A moderator there notes reprojection comes from headset runtimes, not games.

### Inferences
- All known flat-screen implementations are engine-side (own scene, or a modded engine with camera access). None is game-agnostic, so a compositor-level tool would be first-of-kind. That is novel, but it also means no evidence it looks acceptable.

### Gaps
- Primary sources are missing for the Comrade Stinger demo (host page, date, features such as overscan, depth or HUD handling) and the 2kliksphilip video (date, claims).
- My unverified recollection is that the video dates from late 2022 and LTT covered it in early 2023. Treat this as unconfirmed.

## 5. Frame extrapolation research vs interpolation (ExtraSS, GFFE, PatchEX, others)

### Takeaway
The academic line is ExtraNet (2021) → ExtraSS (SIGGRAPH Asia 2023) → GFFE (2024) → PatchEX (2024). All of it aims at zero-added-latency extrapolation using neural refinement or inpainting on desktop GPUs. The one paper with published timings (PatchEX) needs about 3 ms at 360p and about 8.6 ms at 1080p on an RTX 4080-class GPU. That rules out learned inpainting on an 8 CU Deck at 90 Hz.

### Cited Findings
- ExtraSS: Wu, Kim, Zeng, Vembar, Jha, Kaplanyan, Yan (Intel/UCSB). DOI 10.1145/3610548.3618224, posted December 2023. Joint super-sampling plus extrapolation using lightweight warping modules plus "ExtraSSNet" refinement. No timings on Intel's page. — [Intel](https://www.intel.com/content/www/us/en/developer/articles/technical/extrass-a-framework-for-joint-spatial.html); venue from the [SIGGRAPH Asia 2023 program listing](https://asia.siggraph.org/2023/index.html%3Fpost_type=page&p=14494&id=papers_744&sess=sess155.html)
- GFFE (Wu, Vembar, Sochenov, Panneer, Kim, Kaplanyan, Yan) — [Intel](https://www.intel.com/content/www/us/en/developer/articles/technical/gffe-g-buffer-free-frame-extrapolation.html); [arXiv 2406.18551](https://arxiv.org/abs/2406.18551):
  - Needs no G-buffers. Has dedicated modules for moving fragments and disocclusion types, plus a lightweight shading-correction network.
  - Claims no added latency "as opposed to … DLSS 3 and FSR 3".
  - DOI 10.1145/3687923; arXiv submission 23 May 2024. No numbers on the landing pages.
- PatchEX (Dixit & Sarangi, IIT Delhi, 2024) — [arXiv 2407.17501](https://arxiv.org/abs/2407.17501):
  - G-buffer-guided warping plus patch-based inpainting (foreground, near and far background) plus shadow prediction.
  - Per-step timings (Table 12): 360p ≈ 3.0 ms total, 720p ≈ 6.8 ms, 1080p ≈ 8.6 ms. The warp step alone is 0.75 ms at 360p and 1.58 ms at 720p.
  - GPU is listed as RTX 4080 in one place and RTX 4090 in another; the paper is inconsistent.
  - Its model gives interpolation 11.11–22.22 ms added presentation latency at 90 Hz, versus 0 for extrapolation.
- Mob-FGSR (SIGGRAPH 2024) is a "lightweight" frame generation plus super-resolution method for mobile. The archive page gives no timings and doesn't say whether it extrapolates or interpolates. — [SIGGRAPH History](https://history.siggraph.org/?p=164259)

### Inferences
- PatchEX's warp step alone, on a desktop GPU many times faster than the Deck (exact ratio not sourced here), costs about 1–1.6 ms at 360–720p. A Deck version would have to use a hand-written, non-ML warp with simple edge fill.
- These methods also assume engine G-buffers or depth, which only the in-process path could supply.

### Gaps
- No ms numbers for ExtraSS, GFFE or Mob-FGSR: the PDFs were blocked by the proxy.
- No 2025–2026 extrapolation papers were surveyed.

## 6. Prior art on Linux, Vulkan, gamescope or the Deck; Steam Frame

### Takeaway
I found no shipped or prototype flat-screen reprojection on Linux, gamescope or the Deck. Gamescope (Oct 2026 HEAD) contains no reprojection or warp code. Its OpenVR backend presents windows as SteamVR overlays, so any head-pose reprojection there belongs to SteamVR, not gamescope. Steam Frame shows flat games on a virtual screen; no source describes camera warp for flat content.

### Cited Findings
- Grepping gamescope for reproject, timewarp or warp finds only mouse-pointer warps (`wlserver_mousewarp`, pointer-constraint warps). — [gamescope @81146ca](https://github.com/ValveSoftware/gamescope/tree/81146cab9bb79aae5254633f60caedf25c16c3b4/src)
- Its compute shaders are composite, blur, RCAS, EASU (FSR1), NIS, SGSR, RGB→NV12 and gaussian blur, with no warp shader. — [src/shaders](https://github.com/ValveSoftware/gamescope/tree/81146cab9bb79aae5254633f60caedf25c16c3b4/src/shaders)
- `--backend openvr` is described as "use OpenVR backend (outputs as a VR overlay)". The backend is 2,525 lines of overlay management (`vr::VROverlay`, `WaitFrameSync`, overlay keys, a `-vrgamepadui` mode). — [main.cpp L195](https://github.com/ValveSoftware/gamescope/blob/81146cab9bb79aae5254633f60caedf25c16c3b4/src/main.cpp#L195); [OpenVRBackend.cpp](https://github.com/ValveSoftware/gamescope/blob/81146cab9bb79aae5254633f60caedf25c16c3b4/src/Backends/OpenVRBackend.cpp)
- Steam Frame — [vr.org (secondary, updated 7 Oct 2026)](https://vr.org/steam-frame-games):
  - Flat Steam games run on the headset (Snapdragon 8 Gen 3, Proton plus FEX) on a "virtual screen".
  - Flat certification requires "720p at 30fps".
  - The article says the headset launched 14 September 2026.
- heise headline: "Steam Frame: No 3D conversion of flatscreen games planned". I saw the headline only. — [heise](https://heise.de/-11104961)

### Inferences
- Valve's VR work hasn't produced reusable flat-screen warp code in gamescope. A fork would add the warp from scratch, with gamescope's async compute composite path as the hook point.

### Gaps
- I couldn't search gamescope issues or PRs (GitHub search blocked) for reprojection feature requests or Valve comments.
- I didn't read the Steamworks Steam Frame performance criteria page.

## 7. Path A: compositor-level warp in a gamescope fork (no depth, rotation-only)

### Takeaway
Gamescope is BSD-2-Clause, so it can be forked and redistributed. It already composites on a realtime-priority async compute queue just before vblank, and it keeps overlays (Steam UI, MangoHud) on separate planes that could stay unwarped. The available inputs are only the final color buffer (with HUD baked in), present timing, and mouse/keyboard events. There is no depth, no motion vectors, no camera matrices and no gamepad state. Warping would also force a GPU composite every vblank instead of direct scanout.

### Cited Findings
- License is BSD 2-Clause (Valve 2013–2022, NVIDIA 2022). — [LICENSE](https://github.com/ValveSoftware/gamescope/blob/81146cab9bb79aae5254633f60caedf25c16c3b4/LICENSE)
- Gamescope creates its queue with `VK_QUEUE_GLOBAL_PRIORITY_REALTIME_EXT`. Without CAP_SYS_NICE it falls back to "regular-priority compute and threads. Performance will be affected." — [rendervulkan.cpp L543–545](https://github.com/ValveSoftware/gamescope/blob/81146cab9bb79aae5254633f60caedf25c16c3b4/src/rendervulkan.cpp#L543); [main.cpp L890](https://github.com/ValveSoftware/gamescope/blob/81146cab9bb79aae5254633f60caedf25c16c3b4/src/main.cpp#L890)
- The README says the "realtime async compute queue … can run in tandem with the game's gfx work". Reshade effects on the general queue "will increase latency". — [README L90](https://github.com/ValveSoftware/gamescope/blob/81146cab9bb79aae5254633f60caedf25c16c3b4/README.md)
- The DRM backend takes a full GPU composite only when needed: `bNeedsFullComposite` is set by FSR, NIS, SGSR, blur, filters, fades, Reshade, HDR or rotation. Otherwise it scans the app buffer out directly. — [DRMBackend.cpp L3921–3957](https://github.com/ValveSoftware/gamescope/blob/81146cab9bb79aae5254633f60caedf25c16c3b4/src/Backends/DRMBackend.cpp#L3921)
- Vblank scheduling constants — [vblankmanager.hpp L25–32](https://github.com/ValveSoftware/gamescope/blob/81146cab9bb79aae5254633f60caedf25c16c3b4/src/vblankmanager.hpp#L25):
  - Starting draw time 3.0 ms.
  - Minimum draw time while compositing 2.4 ms.
  - Default red zone 1.65 ms.
  - Gamescope wakes up draw time plus red zone before vblank ([vblankmanager.cpp L110–124](https://github.com/ValveSoftware/gamescope/blob/81146cab9bb79aae5254633f60caedf25c16c3b4/src/vblankmanager.cpp#L110)).
- Gamescope tracks base-plane and non-base-plane repaints separately (`hasRepaintNonBasePlane`). — [steamcompmgr.cpp L1116](https://github.com/ValveSoftware/gamescope/blob/81146cab9bb79aae5254633f60caedf25c16c3b4/src/steamcompmgr.cpp#L1116)
- Gamescope's input paths are wlroots/libinput (`LibInputHandler.cpp`, touch via libinput/udev) and a libeis input-emulation server (`InputEmulation.cpp`). No gamepad or evdev joystick handling exists in `src/` outside the VR backend. — [LibInputHandler.cpp](https://github.com/ValveSoftware/gamescope/blob/81146cab9bb79aae5254633f60caedf25c16c3b4/src/LibInputHandler.cpp); [InputEmulation.cpp](https://github.com/ValveSoftware/gamescope/blob/81146cab9bb79aae5254633f60caedf25c16c3b4/src/InputEmulation.cpp)
- Gamescope already loads its own Vulkan layer (`VkLayer_FROG_gamescope_wsi`) into game processes, for frame-limiter and present-timing protocol work. — [layer/](https://github.com/ValveSoftware/gamescope/tree/81146cab9bb79aae5254633f60caedf25c16c3b4/layer)

### Inferences
- **Input sampling point.** Input would be sampled at gamescope's wake-up, about 4 ms or more before vblank (2.4 ms + 1.65 ms). OLED scan-out adds roughly half a refresh on average. So warp sample-to-photon would be around 10 ms, against tens of ms for the game's own input path at 45 fps. The latency headroom is real.
- **Rotation as a homography.** A rotation-only warp is a homography H = K·R·K⁻¹, which needs the game's FOV (K). Neither FOV nor the game's render-time camera pose is visible to gamescope. Both must be calibrated or estimated (Q10). The tool also has to estimate *which* input sample each real frame reflects (the game's input-to-present delay), or warps will be offset.
- **Anti-cheat compatibility.** This path injects nothing new into the game. That matches the project's Tier S spirit and works with Easy Anti-Cheat titles such as Space Marine 2. Note that gamescope's stock WSI layer is already in-process regardless.
- **Overlays.** Keeping Steam overlay and MangoHud planes unwarped is a structural advantage. The game's own HUD is still baked into the base plane (Q9).
- **Cost of forcing composition.** Forcing full composition every vblank removes the direct-scanout saving and adds a GPU pass at 90 Hz that competes with a GPU-bound game. Whether the realtime compute queue actually lands on time while the game saturates all 8 CUs on RADV is unproven. Linux SteamVR's history (Q2) suggests it's fragile.
- **Distribution on SteamOS.** SteamOS ships its own gamescope as the session compositor. Replacing it needs a way to run a forked binary in Game Mode. I have no source on how practical or durable that is across SteamOS updates.

### Gaps
- No measurement of RADV realtime-compute preemption latency while a game saturates the GPU on Van Gogh (the Deck's APU).
- No source on how to ship or launch a forked gamescope in SteamOS Game Mode, or how SteamOS 3.8 updates treat it.

## 8. Path B: in-process Vulkan layer (depth, positional warp, HUD separation)

### Takeaway
An in-process layer under DXVK or vkd3d-proton could in principle intercept depth and the pre-UI color target, enabling positional warp and HUD replay. Every documented system that does this has engine cooperation (motion vectors, depth, a HUD-less buffer, camera pose). I found no published, game-agnostic method for recovering camera matrices or the UI pass from intercepted Vulkan calls. Per project rules this is Tier I: no anti-cheat games, opt-in per game.

### Cited Findings
- Positional timewarp needs the app's depth. AppSW additionally needs an app-rendered motion-vector pass with opaque objects only. — [Meta OS compositor](https://developers.meta.com/horizon/documentation/native/android/os-compositor); [Meta AppSW](https://developers.meta.com/horizon/documentation/native/android/mobile-asw/)
- FSR 3 frame interpolation takes an optional `currentBackBuffer_HUDLess` ("The current presentation color buffer without HUD content"). If absent, it uses the regular back buffer, i.e. the game must supply the separation. — [GPUOpen FidelityFX docs](https://gpuopen.com/manuals/fidelityfx_sdk/techniques/frame-interpolation/)
- The HPG 2020 paper rendered 2D UI after the warp. It calls semitransparent HUD and lit view models "non-trivial". — [Kim et al.](https://research.nvidia.com/sites/default/files/pubs/2020-07_Post-Render-Warp-with/HPG_2020_Latewarp_AuthorVersion_0.pdf)
- PureDark's demo rendered 25% overscan per side at a 4×4 VRS rate, which needs control of the game's projection. — [DSOGaming v2](https://www.dsogaming.com/pc-performance-analyses/puredark-has-released-a-new-version-of-his-nvidia-reflex-2-tech-demo-that-fixes-the-visual-border-issues/)

### Inferences
- A layer can see depth attachments and render passes. Deciding which depth buffer is the main scene, which pass is UI, and what the camera matrix is (to warp in 3D) is game-specific reverse engineering, the way per-engine mods do it.
- Overscan (the best fix for edge disocclusion) needs the game to render a wider FOV, so it's realistic only in-process or through a per-game FOV setting plus crop.
- Replaying UI draws onto a warped frame means recording and re-issuing command-buffer contents. That is high-risk under the project's R16 rule (Khronos-validation-clean, off by default).

### Gaps
- No open-source, game-agnostic Vulkan or DXVK layer doing reprojection was found.
- No source on whether DXVK or vkd3d-proton expose stable hooks or markers for the UI pass.

## 9. Reading controller input: Steam Input, hidraw, evdev permissions

### Takeaway
On SteamOS, Steam owns the Deck controller through hidraw. While Steam runs, the kernel's own evdev gamepad for the Deck is deliberately removed, and games see Steam's virtual devices created via uinput. A warp tool can read raw stick and gyro from the Deck's hidraw node (user-accessible via Steam's udev uaccess rules), or read Steam's virtual pad. Gamescope itself never sees gamepad input.

### Cited Findings
- The `hid-steam` driver says that when a user-space client such as Steam opens the layered hidraw device, the driver sends no commands and removes its own input device "to avoid double input". The device is recreated when the client closes. — [hid-steam.c header](https://github.com/torvalds/linux/blob/master/drivers/hid/hid-steam.c)
- Deck specifics in the driver — [hid-steam.c](https://github.com/torvalds/linux/blob/master/drivers/hid/hid-steam.c):
  - Sticks are reported as ABS_X/Y/RX/RY with range ±32767.
  - Joystick resolution constant is 6553.
  - The IMU can stream raw accelerometer and gyro (`SETTING_IMU_MODE_SEND_RAW_ACCEL | SEND_RAW_GYRO`).
  - Lizard mode is toggled manually on the Deck.
- Steam's udev rules (Debian `steam-devices`) — [Debian README](https://metadata.ftp-master.debian.org/changelogs/main/s/steam-installer/stable_steam-devices.README.Debian):
  - Grant `/dev/uinput` and `/dev/hidraw*` for known pads, explicitly including "the Steam Deck's built-in gamepad", to the logged-in user via uaccess.
  - Steam Input uses uinput to create a virtual keyboard, mouse and Xbox 360 controller.
  - The README notes a background process holding hidraw open behaves like a "mouse logger".
- hidraw passes raw, unparsed reports, and `read()` returns queued reports. — [kernel hidraw docs](https://github.com/torvalds/linux/blob/master/Documentation/hid/hidraw.rst)
- Gamescope has no gamepad handling. It does take mouse input via libinput and an EIS input-emulation server. — [gamescope src](https://github.com/ValveSoftware/gamescope/tree/81146cab9bb79aae5254633f60caedf25c16c3b4/src)

### Inferences
- **Recommended source.** Read the Deck hidraw directly, in parallel with Steam, for the earliest stick and gyro samples. The cost is parsing Valve's report format; SDL and hid-steam contain parsers.
- **Mapping problem.** What the game receives depends on the per-game Steam Input layout. The stick may be a stick, mouse-joystick, flick stick or gyro-to-mouse. The warp predictor needs the *effective* mapping, not just raw deflection.
- **Mouse-style layouts are easier.** For layouts that emit mouse motion (gyro or trackpad to mouse), the deltas pass through uinput, libinput or EIS where a gamescope fork could observe them. Mouse deltas map linearly to camera angle, which makes the warp much easier than for rate-controlled sticks. I did not verify which injection path Steam uses in Game Mode.

### Gaps
- Whether several processes can read the same hidraw node at once without starving Steam: I believe each open gets its own report queue, but the docs I fetched don't state it.
- The Deck controller's report rate.
- Whether Steam in Game Mode injects mouse events through gamescope's EIS socket or through uinput or XTest.

## 10. Mapping stick input to camera rotation; automatic per-game calibration

### Takeaway
No literature turned up on automatically calibrating game camera response from stick input against measured image motion. The closest established practice is JoyShockMapper's manual "real world calibration": units per full in-game turn. Auto-calibration is plausible: inject or record stick input, estimate global image rotation, fit gain, curve, deadzone, acceleration and smoothing. It is unproven.

### Cited Findings
- JoyShockMapper's `REAL_WORLD_CALIBRATION` maps controller rotation to in-game rotation — [JoyShockMapper README §5.2–5.3](https://github.com/Electronicks/JoyShockMapper):
  - The user flicks to complete a full in-game turn and runs `CALCULATE_REAL_WORLD_CALIBRATION [n turns]` to get the factor.
  - The game's `IN_GAME_SENS` must be cancelled out, and OS mouse acceleration interacts with it.
- NVIDIA's late-warp study used mouse rotation, a direct angle per count, not rate-controlled stick input. — [Kim et al.](https://research.nvidia.com/sites/default/files/pubs/2020-07_Post-Render-Warp-with/HPG_2020_Latewarp_AuthorVersion_0.pdf)

### Inferences
- **Stick cameras are rate-controlled.** Deflection maps to angular velocity through per-game curves, deadzones, acceleration ramps and often smoothing. The warp needs a dynamic model ω(t) = f(stick history), not a gain.
- **A proposed calibration procedure (unvalidated):**
  1. Capture frames plus hidraw stick samples in a calibration scene.
  2. Estimate per-frame global yaw and pitch from image motion, e.g. phase correlation or optical flow on the center region with HUD masked.
  3. Fit FOV-scaled gain, response exponent, deadzone, ramp time constant and input-to-display delay.
- **Calibration failure modes:**
  - Parallax and moving objects bias global-motion estimates.
  - Third-person orbit cameras (Q11).
  - Games that change sensitivity or FOV when aiming down sights.
  - Camera auto-centering and lock-on.

### Gaps
- No published method or tool for automatic per-game stick→camera transfer-function identification was found.

## 11. Third-person orbit cameras (Monster Hunter Wilds, Space Marine 2)

### Takeaway
Rotation-only warp models a camera rotating in place. An orbit camera rotates *and translates* around a pivot near the character. A compositor warp would therefore slide the character, the thing the player watches, across the screen, and it would snap back at each real frame. No published measurement exists. This is a first-principles risk that should be prototyped before any commitment.

### Cited Findings
- "Pure camera rotation introduces no parallax". Translation needs depth, and positional timewarp guesses at exposed pixels. — [Meta OS compositor](https://developers.meta.com/horizon/documentation/native/android/os-compositor)
- Rotation-only warp causes positional judder on near-field objects during translation, and moving objects are frozen between real frames. — [ATW Examined (older)](https://developers.meta.com/horizon/blog/asynchronous-timewarp-examined/)
- HPG 2020 tested only first-person aiming and egomotion. — [Kim et al.](https://research.nvidia.com/sites/default/files/pubs/2020-07_Post-Render-Warp-with/HPG_2020_Latewarp_AuthorVersion_0.pdf)

### Inferences (geometry, my own calculation)
- **Pixel shift per warped frame.** Assume a 90° horizontal FOV at 1280 px wide, so focal length ≈ 640 px and 1° ≈ 11 px near the center. A 180°/s stick turn moves the view about 2° per 11.1 ms refresh, about 22 px.
  - In a true orbit render, the character at the pivot stays nearly fixed and the background moves.
  - A rotation-only warp moves *everything* about 22 px, the character included, then the next real frame snaps it back.
  - Result: the character judders at the real frame rate. At 30 fps it's up to about 44 px on the second warped frame.
- **What would fix it:**
  - Depth-aware warp around the orbit pivot (in-process).
  - Masking a character region the compositor would have to segment without depth.
- **Other artifacts:**
  - Far background is mostly right with rotation-only warp.
  - Moving monsters and enemies keep real-fps animation judder.
  - Screen edges expose unrendered areas at about 22–44 px per warped frame at that turn rate.
- **Anti-cheat constraint.** Space Marine 2 is an Easy Anti-Cheat title per the project rules, so it can only use the compositor path, the one hit hardest by this artifact.

### Gaps
- No user study or video analysis of rotation-only warp on third-person orbit cameras exists in the sources found.
- The actual FOVs and camera pivot distances for MH Wilds and Space Marine 2 are unknown.

## 12. HUD and overlay handling without game cooperation

### Takeaway
The only published game-agnostic method found is Qualcomm's patent on static-region detection for frame extrapolation. Shipping vendor frame-gen (FSR 3) relies on the game supplying a HUD-less buffer. A compositor tool would need static-pixel masks, hand-authored per-game masks, or both. Semi-transparent and dynamic HUD elements remain unsolved.

### Cited Findings
- Qualcomm US 11,587,208, "High quality UI elements with frame extrapolation" (filed May 2021, granted Feb 2023) — [Justia](https://patents.justia.com/patent/11587208):
  - Compares pixels pairwise across several previous frames, possibly non-sequential (example spacing 50 frames), to find unchanged pixels.
  - Merges the masks with a median, expands and blurs the result into an alpha mask.
  - Overlays masked regions from the latest real frame on the extrapolated frame.
  - Describes UI and background arriving as one frame, implying no game cooperation.
- FSR 3 uses an optional game-provided `currentBackBuffer_HUDLess`. — [GPUOpen](https://gpuopen.com/manuals/fidelityfx_sdk/techniques/frame-interpolation/)
- In HPG 2020, UI composited after the warp was artifact-free. Semi-transparent HUD is described as non-trivial. — [Kim et al.](https://research.nvidia.com/sites/default/files/pubs/2020-07_Post-Render-Warp-with/HPG_2020_Latewarp_AuthorVersion_0.pdf)

### Inferences
- **What works.** Static-region detection fits fixed HUD elements: health bars, minimaps, ammo counters. It fails on reticles in third-person games that track targets, damage numbers, lock-on markers and HUD elements that animate.
- **Fallback.** Pinning those areas, by keeping the masked region from the real frame, is safe but creates seams where warped background meets the pinned HUD.
- **Gamescope-level overlays.** Steam's quick-access menu, MangoHud and notifications can stay unwarped on non-base planes (Q7).
- **Patent constraint.** Qualcomm's patent (US 11,587,208, granted 2023) may constrain copying its exact median-mask method in an open-source tool. Legal review is out of scope.

### Gaps
- No academic paper on HUD detection for reprojection or extrapolation without engine data was found.
- Reflex 2's HUD handling is undocumented publicly.

## 13. Cost on an 8 CU RDNA2 at 800p, and how to measure the latency effect

### Takeaway
A rotation-only warp plus a simple edge fill and mask blend at 1280×800 is tiny in raw arithmetic and bandwidth terms: well under 0.2 ms by back-of-envelope estimate. The real costs are:
- forcing a GPU composite every 11.1 ms instead of direct scanout,
- contention with a GPU-bound game,
- on-time scheduling of the realtime compute queue.

Learned inpainting (PatchEX-class) is out of budget. Latency should be measured with a 240 fps camera filming stick motion and the screen together, but the stick-to-first-camera-motion setup needs designing.

### Cited Findings
- Deck OLED: 1.6 TFLOPS FP32, LPDDR5 6400 MT/s quad 32-bit channels, 1280×800 up to 90 Hz. — [steamdeck.com/tech](https://www.steamdeck.com/en/tech)
- PatchEX warp step: 0.75 ms (360p) to 1.58 ms (720p). Full extrapolation is about 3–8.6 ms on an RTX 4080-class GPU. — [arXiv 2407.17501](https://arxiv.org/abs/2407.17501)
- Gamescope's default minimum draw time while compositing is 2.4 ms, plus a 1.65 ms red zone. — [vblankmanager.hpp](https://github.com/ValveSoftware/gamescope/blob/81146cab9bb79aae5254633f60caedf25c16c3b4/src/vblankmanager.hpp#L25)
- Example measurement method (2022, older): the iOS app "Is It Snappy?" filmed at 240 fps, five runs per setting, ±4 ms stated error, button-press to screen-change. — [Tom's Hardware](https://www.tomshardware.com/uk/news/steam-deck-framerate-limiter-egregiously-raises-input-latency)
  - Deck results: 31.8 ms uncapped, 75.8 ms at a 60 fps cap, 145.9 ms at a 30 fps cap. These predate later SteamOS limiter changes.
- The Oculus 2015 guidance gives ≤2 ms preemption granularity as the requirement for on-time warps. — [ATW Examined](https://developers.meta.com/horizon/blog/asynchronous-timewarp-examined/)

### Inferences (my arithmetic, not measured)
- **Bandwidth.** 6400 MT/s × 16 bytes ≈ 102.4 GB/s peak, shared with the CPU. One warp pass reads and writes about 1.02 MP × 8 B ≈ 8 MB, about 0.08 ms at peak. At 90 Hz that's about 0.7 GB/s, under 1% of peak.
- **Compute.** Even 100 FLOP per pixel is about 0.1 GFLOP per frame, about 0.06 ms at 1.6 TFLOPS.
- **Realistic estimate.** With dispatch overhead plus mask and edge-fill passes, about 0.1–0.3 ms per warp. That's plausible but must be measured on hardware.
- **Measuring stick latency.** The 240 fps method has about 4.2 ms quantization, so 10+ trials are needed to resolve differences of about 10 ms. For sticks, film the thumbstick and screen in the same frame, or drive a scripted input with a visible marker. The metric is "first frame of stick motion → first frame of image rotation", warp on versus off, at locked 45 and 30 fps.
- **Second metric.** Also measure prediction error: overshoot and snap-back amplitude in pixels, taken from the same video.
- **Project constraint.** Under the project's R7 rule, any on-Deck measurement must go through the bench runner.

### Gaps
- No measured cost exists for gamescope's existing composite passes (FSR1, NIS) on the Deck, which would be the closest calibration point.
- The open-source tools [inputLagTimer](https://github.com/stenyak/inputLagTimer) and [YALMD (Univ. Regensburg)](https://hci.uni-regensburg.de/publications/yet_another_latency_measuring_device) turned up in search, but I didn't retrieve their docs.
- No source on RADV queue-priority behavior while the game saturates the GPU on Van Gogh (the Deck's APU).
