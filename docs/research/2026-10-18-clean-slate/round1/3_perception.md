## Vision-science brief: how perceived quality and smoothness can beat the Deck OLED's limits

**What the eye can resolve on this screen.** Geometry comes from the spec. The other numbers come from published vision models I ran myself, so treat them as estimates (est.).
- 7.4" 1280×800 works out to 204 ppi and 0.1245 mm pixels. At 30/35/40 cm that is **42/49/56 pixels per degree (ppd)**, which puts the screen's finest displayable detail (Nyquist) at 21/24.5/28 cycles per degree (cpd).
  - At 35 cm the screen spans 25.7°×16.2°. The corners are only about 15° from the centre.
  - 20/20 vision needs about 60 ppd, so at the screen centre the display is slightly *below* what the eye can resolve. Any resolution lost in the centre is visible.
- **Fine detail versus mid-scale detail.** I used Barten's contrast-sensitivity model and his SQRI image-quality integral ([Barten 1990](https://www.doi.org/10.1364/JOSAA.7.002024)). At 100 cd/m²:
  - the finest octave (12–24.5 cpd), which is what upscaling gives up, carries about 10% of perceived quality;
  - the 2–8 cpd band carries about 42%.
- **Darkness.** Sensitivity at 20 cpd falls **6.6×** from 100 to 1 cd/m² (107 → 16). This agrees with [castleCSF](https://pmc.ncbi.nlm.nih.gov/articles/PMC10996938/).
- **Motion.** The Kelly–Daly motion-sensitivity model ([Kelly 1979](https://www.doi.org/10.1364/JOSA.69.001340), [Daly 1998](https://opticalengineering.spiedigitallibrary.org/conference-proceedings-of-spie/3299/0000/Engineering-observations-from-spatiovelocity-and-spatiotemporal-visual-models/10.1117/12.320110.full)) gives:
  - the finest visible detail drops to about 11 cpd when the image slides across the retina at 2°/s, and about 3 cpd at 10°/s;
  - at 45 fps each frame is held on screen for 22.2 ms, so an eye following motion sees it smeared by speed × 22.2 ms. That is 0.22° at 10°/s and 2° at 90°/s.
- **Where players look.**
  - In first-person shooters, 88% of fixations land in the central 25% of the screen area ([Kenny et al. 2005](https://mural.maynoothuniversity.ie/id/eprint/282/1/Paper04_ECMS_2005.pdf)). Third-person over-the-shoulder play is probably similar (est.).
  - In orbit cameras the character the player watches stays *still on screen*, so during a camera turn the eye is not following the background. That makes judder (stepping) the main artifact, not blur.
  - [Johnson et al. 2015](https://escholarship.org/content/qt7vc8b2tx/qt7vc8b2tx.pdf) found motion artifacts visible from about 10–20°/s at 60 fps, and a fixed gaze is more sensitive than a following one.

**Bottom line:** the cheap wins are in time (motion, latency, judder) and in luminance, not in lower peripheral resolution.

---

### 1. Stick-latched reprojection to 90 Hz in gamescope
**Pitch:** every 11.1 ms refresh shows the camera angle implied by the *latest* right-stick reading, instead of repeating a frame that is 22 ms old.

**Mechanism:**
- Gamescope reads the Steam virtual gamepad's input device, read-only.
- It measures low-resolution (320×200) optical flow, i.e. how each part of the image moved, between the last two game frames. The open-source FidelityFX optical-flow pass (MIT licence) can do this. lsfg-vk's shaders are proprietary, so they can't be reused.
- At each vblank, it shifts the newest frame by flow × (ω_now / ω_frame). ω is the camera turn speed that a given stick position produces in this game (deadzone, response curve, smoothing). That stick-to-camera-speed curve is fitted offline per game and shipped as data.
- No depth buffer is needed: the measured flow already contains the orbit parallax (the character barely moves, the sky moves fully), and the HUD has zero flow so it stays put.
- First-person games (Stalker 2) use a pure rotation warp with masks for the weapon model and HUD.
- Newly exposed background beside the character gets a soft, low-detail fill. That strip moves across the retina at full pan speed, where the eye can't see detail above about 1–3 cpd anyway.
- Missed frames are covered the same way (the original job of VR spacewarp), so hitches during camera turns disappear.

**Why it beats the wall:**
- Extrapolating forward *removes* latency. Interpolating frame generation adds it.
- Camera turns are the main whole-screen motion in action games.
- [TRM (Denes et al.)](https://www.cl.cam.ac.uk/~rkm38/pdfs/denes2019trm.pdf) showed that at 90 Hz and above, alternating full-quality and degraded frames looks close to full quality. Frames at 0.4–0.5× resolution were indistinguishable.

**Budget (est.):**
- GPU: flow about 0.4 ms plus two warps at about 0.25 ms each, so **about 0.9 ms per 22.2 ms (about 4%)**.
- Memory: about 10 MB.
- Power: gamescope has to composite on every refresh instead of passing frames straight to the display, about +0.2–0.5 W.
- Latency: camera-turn motion-to-photon goes from about 70–90 ms to **about 10–15 ms**. This applies to camera rotation only, not to attacks or other game actions.
- Persistence: each image is held 11.1 ms instead of 22.2 ms, and the speed at which judder becomes visible roughly doubles.

**Tools:** gamescope already creates a REALTIME-priority compute queue (`src/rendervulkan.cpp:542-545`, `VK_QUEUE_GLOBAL_PRIORITY_REALTIME_EXT`).

**Prior art:**
- [Kim et al., HPG 2020](https://research.nvidia.com/sites/default/files/pubs/2020-07_Post-Render-Warp-with/HPG_2020_Latewarp_AuthorVersion_0.pdf): a rotation-only late warp removed about 81% of an 80 ms aiming penalty. The black screen-edge gaps were noticed but did not hurt performance.
- [Reflex 2 Frame Warp](https://www.nvidia.com/en-au/geforce/news/reflex-2-even-lower-latency-gameplay-with-frame-warp/): 27 → 14 ms in THE FINALS.
- VR runtimes: [ASW 2.0](https://www.meta.com/blog/introducing-asw-2-point-0-better-accuracy-lower-latency/) and [async reprojection](https://developers.google.com/vr/discover/async-reprojection).

**Tier:** S (compositor only), so it also works for anti-cheat games. It raises *presented* fps only and does not count toward the native target.

**Falsification (2 weeks or less):**
- Offline: capture 90 fps on a PC with scripted stick input, drop to 45 fps, synthesize the missing frames, and score with FovVideoVDP (gaze on the character) against true 90 fps and against plain frame-doubling. Kill it if it isn't at least 0.3 JOD better than doubling on pans.
- Bench Deck: measure stick-to-photon latency with injected input and a photodiode. Kill it if the gain is under 30 ms.

**Biggest risk:** silhouette tearing around the character the player is looking at during fast pans (the exposed strip is about 49 px at 90°/s), and semi-transparent HUD where the flow is mixed.

### 2. Pan-locked anisotropic VRS through RADV's own runtime switch
**Pitch:** while the camera turns, shade 3D passes at half rate *along the motion direction*. RADV already exposes a runtime knob for this, so nothing is injected into the game.

**Mechanism:**
- A launch option sets `RADV_FORCE_VRS_CONFIG_FILE`. Per the [Mesa docs](https://docs.mesa3d.org/envvars.html): "supported values are 2x2, 1x2, 2x1 and 1x1 … only affects GFX10.3 APUs". The file is watched with inotify and changes apply immediately ([MR 14713](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/14713)).
- A small daemon writes the rate (on above 15°/s, off below 10°/s, held at least 100 ms):
  - **2x1** when camera yaw exceeds about 15°/s, judged from the stick or gamescope's flow;
  - **1x2** for pitch;
  - **2x2** for fast flicks;
  - **2x2** for about 130 ms after a detected camera cut. Visual masking right after scene cuts hides it ([SPIE 5292](https://neurophotonics.spiedigitallibrary.org/conference-proceedings-of-spie/5292/0000/Temporal-masking-effect-on-dropped-frames-at-video-scene-cuts/10.1117/12.526648.full)).
- The forced path skips 2D (UI and full-screen) draws and shaders that discard pixels ([Nieuwenhuizen](https://www.basnieuwenhuizen.nl/a-first-foray-into-rendering-less/)), so the HUD and post-processing stay at full rate.

**Why it should be invisible:** motion only destroys detail *along* the motion direction.
- At a 67% render scale, 2x1 shading keeps about 8 cpd horizontally.
- At 15°/s an eye following the motion gets a smear of 0.33° (no detail survives at 3 cpd) and its tracking slip limits it to about 9 cpd.
- An eye fixed on the character sees the background with a cutoff of about 2 cpd.
- Vertical detail is not touched.

**Budget:**
- Pixel-shader work halves in 3D passes. If those take 25–45% of the frame (est.; measure per game), that saves **about 2.8–5 ms of the 22.2 ms frame during pans**.
- Forced VRS has been reported to give "30%+" in some games and nothing in others.
- Memory zero, CPU negligible.

**Prior art:**
- NVIDIA Adaptive Shading shipped in Wolfenstein: Youngblood: +6–17% in stationary-scene tests with "hardly any perceptible quality loss" ([NVIDIA](https://www.nvidia.com/en-us/geforce/news/nvidia-adaptive-shading-a-deep-dive)).
- [Jindal et al. 2021](https://www.cl.cam.ac.uk/research/rainbow/projects/alsarr/) and [Denes et al. 2020](https://www.cl.cam.ac.uk/research/rainbow/projects/motion_quality_model/).

**Tier:** S (driver environment variable). Applies to any DXVK, vkd3d-proton or native Vulkan game, including Helldivers 2 and Space Marine 2.

**Falsification:**
- Scripted pans in three games on the bench, with per-pass GPU timing at 1x1 versus 2x1. Kill it if GPU savings during pans are under 8%.
- On a Deck: two-alternative forced-choice test with 20 people × 40 trials at 20 and 60°/s. Kill it if people detect the change more than 75% of the time.

**Biggest risk:**
- The rate is frame-wide, so the static character the player is watching also gets 2x1 (fixing that needs idea 3).
- The option is labelled "for testing purposes" and could be removed upstream.
- Mesh-shader paths (Alan Wake 2) may not pick up the forced rate; verify.
- Compute-heavy UE5 frames may see small gains.

### 3. Shading-rate map driven by displayed brightness and predicted gaze
**Pitch:** a per-8×8-tile shading-rate map driven by how bright each tile actually is on the panel (in nits), its contrast, and its distance from the centre/character.

**Mechanism:**
- A Vulkan layer attaches a `VkFragmentShadingRateAttachmentInfoKHR` image to the scene passes. RADV supports VRS on RDNA2 ([Phoronix](https://www.phoronix.com/news/RADV-fragment-shading-rate)); confirm the supported tile size with vulkaninfo.
- The map is built from the previous frame, shifted by the global flow. Displayed brightness = pixel value × the nits set by the brightness slider, compared against the contrast-sensitivity model at the Deck's ppd.
- Rules: tiles under about 3 nits → 2x2; low-contrast tiles more than 10° from centre → 2x2; a protected ellipse covers the centre and the character.
- Rates must be "sticky" (slow to change). Sensitivity to flicker *peaks* at 10–30° from the gaze point ([Krajancich 2021](https://ar5iv.labs.arxiv.org/html/2104.13514)), so shimmer, not blur, is what gives foveation away.
- Later, ship it as a RADV patch (driver-level).

**Why:** at 20 cpd, the smallest visible error contrast rises from 0.9% at 100 nits to 6% at 1 nit. Alan Wake 2, Stalker 2 at night and Wukong's caves are mostly dark.

**Budget:**
- Honest foveation ceiling: 32% of pixels are more than 10° from centre, so at most 0.32 × 0.75 = **24% of pixel-shader work**.
- [Guenter 2012](https://www.microsoft.com/en-us/research/publication/foveated-3d-graphics) got a 5–6× speedup, but with an eye tracker. Without one, 12% of fixations land off-centre (Kenny).
- Dark scenes with half the tiles at 2x2: about 37% less pixel-shader work, about 9–17% of GPU time (est.).
- Building the map costs under 0.05 ms.

**Way around the missing eye tracker:** a clip-on IR tracker (**accessory**). Total system latency of 50–70 ms is tolerable ([Albert 2017](https://research.nvidia.com/publication/2017-09_latency-requirements-foveated-rendering-virtual-reality)).

**Prior art:** NVIDIA Content Adaptive Shading (uses relative luminance), AMD FidelityFX VRS (uses luminance variance), [Patney 2016](https://research.nvidia.com/labs/rtr/publication/patney2016towards) (up to 70% fewer shading operations).

**Tier:** I (in-process layer), or S if shipped as a driver patch.

**Falsification:** collect tile-brightness histograms from 10-minute captures per game, then run ColorVideoVDP with a **Deck display model** (1280×800, 7.4", 0.35 m, measured nits). Kill it if quality drops by more than 0.25 JOD for less than 10% savings.

**Biggest risk:** the gain only shows up in dark games, and noisy dark regions may interact badly with TAA and the upscaler.

### 4. Judder-matched motion blur at 45 fps on OLED
**Pitch:** turn the game's motion blur *on*, at roughly a 180° shutter. That is the opposite of common PC advice.

**Mechanism and why:**
- An OLED switches pixels in about 0.1 ms (typical figure), so there is no smearing between frames to hide judder.
- At 45 fps, a 90°/s orbit makes the background the eye isn't following jump **2° (98 px) per frame**. That reads as strobing and a "phantom array" of repeated images.
- Blurring each pixel over half that jump (1°) fills the gaps. The background's detail at those speeds is already invisible (cutoff 0.4–0.8 cpd at 40–80°/s).
- The character at the orbit pivot barely moves on screen, so it stays sharp.

**Budget:** about 0.3–0.8 ms for the blur pass (est.). Halve the shutter if idea 1 is running.

**Prior art:** the cinema 180°-shutter rule; [Johnson et al. 2015](https://escholarship.org/content/qt7vc8b2tx/qt7vc8b2tx.pdf).

**Tier:** S (settings and ini files, e.g. UE's `r.MotionBlur.Amount`). Applies to all games.

**Falsification:** record pans at 30/90/150°/s with blur off, 90°, 180° and 360° and show them on a Deck. Measure forced-choice "which is smoother" and whether blur is detected *on the character*. Kill it if 180° isn't preferred at 90°/s and above.

**Biggest risk:** player preference splits, and blur hurts when the eye *follows* a fast enemy.

### 5. OLED/HDR "richness" pass in the compositor
**Pitch:** spend display watts instead of APU watts on what the eye weights most: mid-scale contrast and dynamic range.

**Mechanism:**
- Gamescope already has `--hdr-itm-enabled`, `--hdr-itm-sdr-nits` and `--hdr-itm-target-nits` (`src/main.cpp:148-150`) and `--reshade-effect` (`main.cpp:155`).
- **Highlight expansion:** inverse tone mapping pushes highlights only into the 600 → 1000-nit HDR headroom ([Gigazine](https://www.gigazine.net/gsc_news/en/20240117-steam-deck-oled-review)). This relies on two known effects: perceived contrast and perceived colourfulness both rise with luminance (Stevens and Hunt effects).
- **Mid-scale contrast boost:** a local-contrast gain at 2–6 cpd (σ ≈ 4–12 px), kept inside the halo-visibility limits from [Trentacoste et al. 2012](https://www.cs.ubc.ca/labs/imager/tr/2012/Countershading).

**Why:** the 2–8 cpd band carries about 4× the perceived-quality weight of the fine octave that upscaling removes. Panel power comes from the battery, outside the APU's 15 W limit.

**Budget:** about 0.2–0.4 ms inside the existing composite pass (est.). Because only highlights brighten, average picture level barely changes: about +0.1–0.5 W from the battery (est.).

**Prior art:** gamescope's existing inverse tone mapping and its ReShade support.

**Tier:** S. Applies to all games.

**Falsification:** blind preference test of the Medium preset plus this pass against the High preset without it. Kill it if preference is 50% or less (95% CI), or if halos are reported in more than 25% of trials. **FLIP and ColorVideoVDP will score this pass as error, because they measure fidelity to the reference, so only a preference test can judge it.**

**Biggest risk:** inverse tone mapping can look garish, and a static HUD at high nits risks burn-in ([Notebookcheck](https://www.notebookcheck.net/Steam-Deck-OLED-Burn-in-stress-test-reveals-the-disadvantages-of-a-1000-nit-bright-OLED-panel.798272.0.html)).

---

### Unknown unknowns
1. **The scoring metric can't see where these ideas operate.**
   - ColorVideoVDP's documentation mentions neither foveation nor eye pursuit. It effectively treats every pixel as looked at directly and the eye as stationary. It will over-penalize idea 3 and mis-score ideas 1, 2 and 4.
   - It also needs a Deck display entry (peak nits set by the brightness slider, ambient lux). The stock presets such as `standard_4k` are wrong for this screen.
   - Use FovVideoVDP with gaze traces, and resample along the motion path to model an eye following motion.
2. **Persistence changes with the brightness slider and between panel units.** OLED dimming (PWM duty cycle, if the panel uses it) changes hold blur and the speed at which judder appears. Measure with a photodiode at every brightness step on several Decks. The thresholds in ideas 2 and 4 should be lookup tables, not constants.
3. **The stick is not the camera.** Games smooth the stick input, add acceleration, and override it during lock-on or auto-centring. Fit the stick-to-camera curve per game, and when stick and image motion stop agreeing, fall back to repeating the frame.
4. **The 1TB model's etched anti-glare glass adds haze** ([Reviewed](https://reviewed.com/gaming/content/steam-deck-oled-review)). That lowers both effective sharpness and black level. Measure sharpness (MTF, slanted-edge test) and reflectance: part of the fine detail you pay GPU time for may already be erased by the glass on those units.
5. **Room light moves every threshold.** Screen reflections raise the effective black level, so the dark-scene savings and the HDR gain both depend on ambient light. Read the Deck's ambient light sensor and feed it into ideas 3 and 5.

**Key facts to keep:** RADV's `RADV_FORCE_VRS_CONFIG_FILE` is a Tier S lever. It is a runtime-switchable, Deck-only (GFX10.3 APU) VRS control that injects nothing into the game. Also, gamescope already has a realtime-priority compute queue plus inverse-tone-mapping and ReShade hooks, which are natural host points for ideas 1 and 5.
