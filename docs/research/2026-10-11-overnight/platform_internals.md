# Steam Deck OLED platform internals: what a third-party optimization tool can control (as of 2026-10-11)

*Scope note: this covers what the 2026-09-28 compendium (`deckforge-research.md`) does not: hardware power and clock mechanics, the SteamOS/gamescope/Proton stack as of October 2026, every userspace control point, Steam data layout, Decky internals, and 2026 platform changes. "Primary" means vendor docs, source code or official changelogs. "Community" means forum posts, plugin READMEs or user measurements. Source code was read directly from GitHub `master`/`main` on 2026-10-11, so treat line numbers as a snapshot of that day.*

## 1. Hardware: Van Gogh/Sephiroth APU, memory, power budget, clocks, thermals, display

### Takeaway
The OLED Deck has the same 4C/8T Zen 2 + 8 CU RDNA2 APU as the LCD model, moved from 7 nm to 6 nm. Memory goes from 5500 to 6400 MT/s (about 88 to 102.4 GB/s), and the APU power envelope is still 15 W, shared between CPU and GPU. The OLED's 15 W draws less real power than the LCD's 15 W. Its panel runs at 90 Hz with a 45–90 Hz range and no VRR on the internal display. At 45 fps, every frame is shown on exactly two 90 Hz refreshes.

### Cited Findings
**APU and clocks**
- OLED APU: 6 nm (LCD: 7 nm). Zen 2 4C/8T at 2.4–3.5 GHz; RDNA 2 with 8 CUs at 1.0–1.6 GHz (1.6 TFLOPS FP32); APU power 4–15 W, "same as original". Valve said clocks and core/CU counts are unchanged and that there should be no change to gaming performance. GN had not verified Valve's claims — [GamersNexus, 2023-11-09](https://gamersnexus.net/news/valve-announces-steam-deck-oled-deck-2-works)
- Codenames: LCD = Aerith (TSMC N7), OLED = Sephiroth (TSMC N6). Wikipedia gives the APU power range as **3–15 W**, which conflicts with GN's 4–15 W — [Wikipedia: Steam Deck, accessed 2026-10-11](https://en.wikipedia.org/wiki/Steam_Deck)
- Manual GPU clock range used by tooling: SimpleDeckyTDP hard-codes `GPU_FREQUENCY_RANGE = [200, 1600]` MHz, with the comment "Steam Deck pp_od_clk_voltage is empty, so min/max values can't be automatically detected" — [SimpleDeckyTDP `py_modules/devices/steam_deck.py`, main branch, read 2026-10-11](https://github.com/aarron-lee/SimpleDeckyTDP)

**Memory**
- OLED: "16GB LPDDR5 at 6400 MT/s, 4x 32-bit" (LCD: 5500 MT/s). Capacity and channel configuration are unchanged — [GamersNexus, 2023-11-09](https://gamersnexus.net/news/valve-announces-steam-deck-oled-deck-2-works)
- Bandwidth: 88 GB/s (LCD) vs 102.4 GB/s (OLED). Wikipedia's table also labels the OLED RAM "LPDDR5X-8533 (6400 MT/s)", which contradicts GN and Valve's "LPDDR5" and is probably a table error — [Wikipedia: Steam Deck](https://en.wikipedia.org/wiki/Steam_Deck)
- Measured: stock OLED vs LCD is "a couple of percent better" in most tests, which the author attributes mainly to memory bandwidth — [willett.io "What's In A Watt", published 2024-05-06, revised 2026-09-02](https://www.willett.io/posts/watts/). Eurogamer measured the OLED 2–9% faster depending on content — [Eurogamer review via Overclockers.ru translation, undated (late 2023)](https://overclockers.ru/blog/NOVO_GEEK/show/158278/Moe-mnenie-o-Steam-Deck-OLED-Eurogamer)

**Shared power budget, TDP, PPT**
- TDP is "an average" the device only tries to hit over time, so instantaneous draw fluctuates. PPT is "the maximum wattage that the processor will try to consume". The largest gains from more power come in workloads that load the CPU and GPU at once, "where there aren't enough watts to go around" (example: Elden Ring) — [willett.io, 2024-05-06](https://www.willett.io/posts/watts/)
- Measured whole-system draw at full load: LCD about 27 W; OLED about 23 W at 15 W TDP; OLED with PPT raised to 18 W (via a UEFI patch) about 27 W. To match the LCD's real draw at a 5 W cap, an OLED needs roughly a 7 W cap. The author saw at most about 80 °C at 18 W PPT — [willett.io](https://www.willett.io/posts/watts/) (community measurement)
- amdgpu hwmon: `power1_cap` is the "selected power cap in microWatts", bounded by `power1_cap_min`/`power1_cap_max`. On APUs, `power1_average`/`power1_input` "includes the CPU" — [Linux kernel docs, amdgpu thermal, v7.2](https://kernel.org/doc/html/v7.2/gpu/amdgpu/thermal.html)
- On the Deck, `power1_cap` and `power2_cap` (under `/sys/class/hwmon/hwmon4/` on the reporter's unit) change with Steam's TDP slider. A user reported that values above 15 set the fast and slow limits to the same number — [PowerTools issue #88, undated](https://github.com/NGnius/PowerTools/issues/88) (community observation)

**Thermals**
- OLED cooling: fan impeller 14% thicker, fan body 15% thicker, fins 12% thicker, larger heatpipe. Valve's goal was a steadier fan curve with less ramping — [GamersNexus, 2023-11-09](https://gamersnexus.net/news/valve-announces-steam-deck-oled-deck-2-works)
- Fan control can be switched between BIOS and OS (`steamosctl set-fan-control-state <bios|os>`) — [steamosctl man page summary, accessed 2026-10-11](https://linuxcommandlibrary.com/man/steamosctl). SteamOS 3.8.28 fixed "a rare case where fan speed reverted to BIOS control until reboot, causing higher-than-normal fan speeds" — [GamingOnLinux, 2026-09-25](https://www.gamingonlinux.com/2026/09/steamos-3-8-28-stable-released-with-big-improvements-for-steam-deck-steam-machine-and-more-hardware-support/)
- `gpu_metrics` (amdgpu sysfs) reports temperature, frequency, utilization, power, **throttler status**, fan speed and, on APUs only, CPU core statistics — [kernel docs v7.2](https://kernel.org/doc/html/v7.2/gpu/amdgpu/thermal.html)

**Display**
- OLED panel: 7.4" HDR OLED, 1280×800, 90 Hz, 1000 nits peak HDR / 600 nits SDR, 110% P3, over 1,000,000:1 contrast, under 0.1 ms response (Valve claim), 180 Hz touch polling — [GamersNexus, 2023-11-09](https://gamersnexus.net/news/valve-announces-steam-deck-oled-deck-2-works)
- Refresh/frame-limit slider runs 45–90. VRR is "not yet available" on the internal panel. At a 30 fps cap the panel stays at 90 Hz and shows each frame 3 times; at a 40 fps cap it drops to 80 Hz and shows each frame twice — [Eurogamer review via Overclockers.ru, late 2023](https://overclockers.ru/blog/NOVO_GEEK/show/158278/Moe-mnenie-o-Steam-Deck-OLED-Eurogamer)
- The only VRR Wikipedia records is for docked external monitors (SteamOS 3.5.5) — [Wikipedia: Steam Deck](https://en.wikipedia.org/wiki/Steam_Deck). SteamOS 3.8 added "preliminary HDMI VRR support" and "Improved VRR frame pacing", which concern external displays — [GamingOnLinux, 2026-06-18](https://www.gamingonlinux.com/2026/06/steamos-3-8-is-out-with-initial-steam-machine-support-desktop-mode-upgrades-new-graphics-drivers/page=1/)
- gamescope exposes HDR controls as X atoms: `GAMESCOPE_DISPLAY_HDR_ENABLED`, `GAMESCOPE_HDR_ITM_ENABLE` (inverse tone mapping for SDR content), `GAMESCOPE_HDR_TONEMAP_OPERATOR`, `GAMESCOPE_SDR_ON_HDR_CONTENT_BRIGHTNESS`, plus OLED-relevant `GAMESCOPE_COLOR_MURA_CORRECTION_*` atoms — [gamescope `src/steamcompmgr.cpp`, master, read 2026-10-11](https://github.com/ValveSoftware/gamescope)

**Market context**
- Valve said in Nov 2025 that no available SoC would deliver a next-gen Deck, and in 2026 that a successor depends on "a very delineated performance improvement". OLED stock ran out around 2026-02-17. On 2026-05-27 Valve raised OLED prices to $789 (512 GB) and $949 (1 TB) — [Wikipedia: Steam Deck](https://en.wikipedia.org/wiki/Steam_Deck)

### Inferences
- **45 fps is a natural target on the OLED.** 90/45 = 2, so the gamescope limiter can pace with an exact 2-vblank divisor (see section 2). The 22.2 ms budget lines up with two 11.1 ms refreshes, with no judder. On the LCD (40–60 Hz panel), 45 fps needs the panel set to 45 Hz.
- **The CPU and GPU share one budget.** In CPU-heavy scenes, lowering CPU load (for example through engine settings) can free watts for the GPU. That makes "CPU-bound vs GPU-bound vs power-bound" a needed third diagnostic class beyond the compendium's CPU/GPU/bandwidth split. `power1_average` includes the CPU, so it is the right signal for "power-bound".
- **TDP numbers don't transfer between models.** Real power at the same nominal TDP differs between OLED and LCD, so crowd data must be keyed by model and never mixed.
- **Bandwidth is about 16% higher on the OLED,** so bandwidth-bound passes should see the largest OLED-vs-LCD gains. That is a cheap way to classify passes if LCD data is ever collected.

### Gaps
- I found no Valve-documented thermal throttle threshold (Tjmax or skin-temperature limit) for Sephiroth, or how throttling interacts with the TDP limit. `gpu_metrics` throttler status is the measurable proxy.
- Valve's official tech-specs page (steamdeck.com/en/tech/deck) could not be fetched (permission timeout). Specs above come from GN and Wikipedia, and the 3 W vs 4 W minimum TDP conflict is unresolved.
- I found no 2026 source confirming or ruling out internal-panel VRR on the OLED. The 2023 review says "not yet", and nothing since shows it added.
- I found no source for the BIOS UMA frame-buffer options on the OLED (the commonly cited 1 GB default and 4 GB option are community lore here).

## 2. Software stack as of October 2026: SteamOS, gamescope, Proton/DXVK/vkd3d-proton, Mesa, kernel, immutability

### Takeaway
Stable is **SteamOS 3.8.28** (released 2026-09-24/25) with kernel 6.18.50 and a new major Mesa (reported as 26.1.2, not confirmed by Valve). SteamOS 3.9 is in beta/preview, rebased on Linux 7.2. Proton 11 is stable (11.0-2, Aug 2026), DXVK is at 3.0.x, and Proton bundles Git snapshots of DXVK and vkd3d-proton. gamescope's frame limiter is a vblank-divisor limiter that holds back the game's frame callbacks. Its controls are X atoms on the root window that any X client can set. The root filesystem is read-only and replaced wholesale on update. Only `/home` is guaranteed to persist.

### Cited Findings
**SteamOS versions and timeline (2026)**
- **SteamOS 3.8.10 stable, 2026-06-18:** kernel 6.16, KDE Plasma 6.4, Wayland default in Desktop Mode, LAVD scheduler support, initial Steam Machine support, preliminary HDMI VRR, improved VRR frame pacing — [Phoronix, 2026-06-18](https://phoronix.com/news/SteamOS-3.8.10-Stable)
- The 3.8 notes include several performance-relevant fixes. "Fixed a case where per-app performance settings would intermittently fail to apply when launching a game". "Fixed a case where FPS limits would fail to apply when downscaling games from a higher resolution". "Fixed 'Allow Tearing' in some configurations". "Fixes several cases of reduced performance in Desktop Mode compared to Game Mode". It also shipped OLED BIOS v114, and LCD BIOS v133 with a "Memory Power Down" option and preliminary hibernation — [GamingOnLinux, 2026-06-18](https://www.gamingonlinux.com/2026/06/steamos-3-8-is-out-with-initial-steam-machine-support-desktop-mode-upgrades-new-graphics-drivers/page=1/)
- **3.8.16 stable** was still on Linux 6.16. **3.9.0 preview, 2026-08-30:** Linux 7.2, Plasma 6.7.3, wpa_supplicant replaces iwd on fresh installs, hibernation present but not exposed in the Game Mode UI, `steamos-` packages renamed to `holo-`, VM guest support (virtio-gpu/Venus). Linux 7.2's Cache Aware Scheduling is of little use on the Deck's single-LLC 4-core CPU — [PC Games Hardware, 2026-08-30](https://www.pcgameshardware.de/SteamOS-Software-258049/News/Version-3-9-Vorschau-Linux-7-2-Plasma-6-7-3-1552419/)
- **3.8.20 beta** (late June) brought improved VRAM management, which reached stable in **3.8.28 (2026-09-24)**. Boiling Steam says games can now use "pretty much every last byte of VRAM" and that BIOS graphics-memory tweaks may be unnecessary. PC Gamer expects "minor at best" gains on iGPUs. Valve published no benchmarks — [NerdZap, 2026-10-07](https://nerdzap.com/news/steamos-3-8-28-steam-deck-what-changed/)
- **3.8.28:** kernel 6.18.50. Mesa is a "new major release" with ray-tracing gains (no version given by Valve). Also fixed the fan-reverting-to-BIOS bug — [GamingOnLinux, 2026-09-25](https://www.gamingonlinux.com/2026/09/steamos-3-8-28-stable-released-with-big-improvements-for-steam-deck-steam-machine-and-more-hardware-support/); kernel also confirmed by [comss.ru, 2026-09-25](https://www.comss.ru/page.php?id=22156)
- Mesa **26.1.2** in 3.8.28, replacing **25.3.0** in 3.8.16. BornCity is the only source and cites no Valve notes — [BornCity, 2026-09-29](https://borncity.com/news/steamos-3-8-28-valve-erweitert-handheld-support-und-aktualisiert-firmware/). A GOL commenter gives the same numbers, also unverified.
- **3.9.1 preview** (2026-09-14) and **3.8.27 beta** (fan fix) — [warp2search, 2026-09-15](https://www.warp2search.net/story/steamos-391-preview-and-3827-beta-everything-new-in-the-latest-update/). **3.9.2 beta** (2026-09-26) "bundles all changes since the stable 3.8 release". SteamOS **0.4.1 beta** is a separate branch for the Steam Frame — [warp2search, 2026-09-26](https://www.warp2search.net/story/valve-ships-steamos-392-and-041-betas-for-steam-deck-machine-and-frame/)

**Proton / DXVK / vkd3d-proton**
- Proton 11.0 Beta 1 was built "against Wine 11.0"; Beta 2 (tag `proton-11.0-1-beta2`) updated vkd3d-proton to a newer Git state — [Phoronix, 2026-04-28](https://www.phoronix.com/news/Proton-11.0-Beta-2)
- **Proton 11.0-2** (2026-08-21) is a Wine 11.0 downstream with **DXVK Git and VKD3D-Proton Git** (no tagged versions), VKD3D 2.0, DXVK-NVAPI 0.9.2, Wine Mono 11.2 and FEX 2607 for AArch64 — [Phoronix, 2026-08-21](https://phoronix.com/news/Proton-11.0-2). Proton 11 first went stable around 2026-07-08, per search-result headlines from [10jqka, 2026-07-08](https://news.10jqka.com.cn/20260708/c678034089.shtml) and [PCGH](https://www.pcgameshardware.de/Linux-Software-26761/News/Valve-Proton-11-final-erschienen-1547589/) (not fetched).
- **DXVK 3.0.2** (2026-07-17) adds `DXVK_DEBUG=hang` and fixes a performance regression when FSR is enabled, among others — [Phoronix, 2026-07-17](https://phoronix.com/news/DXVK-3.0.2-Released). The DXVK 3.0 release date and headline changes were not found.
- vkd3d-proton 3.0.1 (May 2026) is covered in the compendium.
- Proton's documented runtime switches include `PROTON_LOG` (writes `$PROTON_LOG_DIR/steam-$APPID.log`), `PROTON_LOG_DIR` and `PROTON_NO_ESYNC`. Advanced users can create `user_settings.py` from `user_settings.sample.py` — [Proton README, branch proton_10.0, read 2026-10-11](https://github.com/ValveSoftware/Proton)

**gamescope (session compositor) — read from source**
- Design: per the README, there are fewer copies and less latency than a traditional compositor. Game frames can be flipped straight to the display via DRM/KMS ("direct scanout"), even when stretching or showing notifications. Composition uses **async Vulkan compute**, so a frame can be shown even while the game keeps the GPU busy. ReShade effects **add latency** because they run on the general queue; LUTs/CTMs applied in AMDGPU Display Core are preferred for simple transforms — [gamescope README, read 2026-10-11](https://github.com/ValveSoftware/gamescope)
- CLI: `-F fsr` / `-F nis`, `-S integer|stretch`, `-r` (fps limit), `-o` (unfocused fps limit), `-w/-h` (game resolution), `-W/-H` (output), `--reshade-effect`, `--reshade-technique-idx` — [gamescope README](https://github.com/ValveSoftware/gamescope)
- Upscale filters in code: `LINEAR, NEAREST, FSR, NIS, PIXEL, SGSR`. Scalers: `AUTO, INTEGER, FIT, FILL, STRETCH` — [gamescope `src/main.hpp` lines 40–87, master, read 2026-10-11](https://github.com/ValveSoftware/gamescope)
- **Runtime control atoms** (read from the root window on PropertyNotify): `GAMESCOPE_FPS_LIMIT`, `GAMESCOPE_DYNAMIC_REFRESH` (+`_EXTERNAL`), `GAMESCOPE_LOW_LATENCY`, `GAMESCOPE_SCALING_FILTER`, `GAMESCOPE_NEW_SCALING_FILTER`, `GAMESCOPE_NEW_SCALING_SCALER`, `GAMESCOPE_FSR_SHARPNESS`, `GAMESCOPE_SHARPNESS`, `GAMESCOPE_ALLOW_TEARING`, `GAMESCOPE_COMPOSITE_FORCE`, `GAMESCOPE_VRR_ENABLED`, `GAMESCOPE_RESHADE_EFFECT`, `GAMESCOPE_RESHADE_TECHNIQUE_IDX`, `GAMESCOPE_DISPLAY_REFRESH_RATE_FEEDBACK`, `GAMESCOPE_LIMITER_FEEDBACK`, `GAMESCOPE_FSR_FEEDBACK`, plus focus, HDR and color atoms. Example handler: `g_nSteamCompMgrTargetFPS = get_prop(ctx, ctx->root, ctx->atoms.gamescopeFPSLimit, 0)` — [gamescope `src/steamcompmgr.cpp` lines ~7200–7360 and 9135–9171](https://github.com/ValveSoftware/gamescope)
- **How the limiter works** (`steamcompmgr_should_vblank_window`, ~line 6812). On a non-VRR display, when the target is below refresh, gamescope computes `nVblankDivisor = nRefreshHz / nTargetFPS` (integer division). It **withholds the game window's frame-done callback** until the next divisor boundary. On VRR it schedules from `last_commit_first_latch_time + g_SteamCompMgrLimitedAppRefreshCycle` instead — [gamescope source](https://github.com/ValveSoftware/gamescope)
- **Refresh doubling** (`_update_app_target_refresh_cycle`, ~line 1222). When Steam sets a combined app refresh cycle, gamescope picks "the highest mode to do refresh doubling with", meaning the highest valid dynamic refresh rate that is an exact multiple of the target fps — [gamescope source](https://github.com/ValveSoftware/gamescope)
- Steam merged the refresh-rate and framerate-limit sliders into one "unified" slider in SteamOS 3.5 (Nov 2023). It can be turned off under Settings → Display → Advanced — [GamingOnLinux, 2023-11-07](https://gamingonlinux.com/2023/11/steam-deck-preview-update-has-a-unified-refresh-rate-and-framerate-limit-slider)
- **Latency of the system limiter (2022):** a Reddit user measured with a 240 fps camera and found Steam's limiter "adds an unacceptable amount of input latency", about the same as VSync. An in-game 40 fps cap in Rocket League added no perceptible lag. No Valve response was reported — [HotHardware, 2022-05-04](https://hothardware.com/news/steam-deck-fps-limit-adds-input-latency) (community measurement on LCD; predates the unified slider, the OLED and the `GAMESCOPE_LOW_LATENCY` atom)

**Immutability and persistence**
- The root filesystem is read-only by default except `/home`, a separate, always-writable partition. Updates replace the system area wholesale (`/usr` etc.), so pacman installs are lost at the next update. `sudo steamos-readonly disable` unlocks root. Valve "aggressively reduce[s] the size of the OS partition" — [heguro Scrapbox notes, circa 2022-12](https://scrapbox.io/heguro/Steam_Deck%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6%E3%82%8BSteamOS_3%E7%92%B0%E5%A2%83%E3%81%AE%E4%BB%95%E6%A7%98) (community; old)
- SteamOS 3.8 added a `custom-update` verb in `atomupd-manager` for testing specific builds. Rolling back to an older version is "considerably more involved" — [GamingOnLinux, 2026-06-18](https://www.gamingonlinux.com/2026/06/steamos-3-8-is-out-with-initial-steam-machine-support-desktop-mode-upgrades-new-graphics-drivers/page=1/); [PCGH, 2026-08-30](https://www.pcgameshardware.de/SteamOS-Software-258049/News/Version-3-9-Vorschau-Linux-7-2-Plasma-6-7-3-1552419/)
- Decky installs to `~/homebrew` but registers `/etc/systemd/system/plugin_loader.service`. "A major OS update will occasionally remove Decky entirely"; plugins and settings persist, and rerunning the installer restores it. Major updates may also reset the `deck` password to blank — [tech-insider.org, 2026-06-16 (updated 2026-08-17)](https://tech-insider.org/decky-loader-setup-2026/) (aggregator of uncertain quality)

### Inferences
- **At 45 fps on the OLED, gamescope's limiter is clean.** With unified mode the panel goes to 90 Hz (highest multiple of 45), divisor = 2, and frames land on alternate vblanks. With unified mode **off** and the panel left at 60 Hz, `60/45 = 1` in integer math, so the limiter does nothing. A tool must set refresh and fps limit together.
- **The limiter's latency cost is unmeasured on current software.** It works by delaying the app's frame callback, so the game blocks in present instead of before input sampling. That is the classic source of added latency, and it matches the 2022 report. DeckForge's "no added input latency" goal means it must either (a) prefer an in-game cap or a latency-aware limiter at the game level, or (b) measure gamescope's limiter with and without `GAMESCOPE_LOW_LATENCY`. This should be an explicit experiment, not an assumption.
- **The atoms are a real control surface, but Steam owns them.** Any X client on gamescope's Xwayland display can set `GAMESCOPE_FPS_LIMIT`, `GAMESCOPE_DYNAMIC_REFRESH`, `GAMESCOPE_NEW_SCALING_FILTER` or `GAMESCOPE_RESHADE_EFFECT`. Steam's client also writes them, so the last writer wins, and Steam rewrites them on game switch or QAM changes. The gamescope ReShade atom is notable: compositor-level post-processing (for example sharpening) without injecting into the game process, which fits Tier S. It costs latency per the README.
- **Proton bundles Git snapshots** of DXVK and vkd3d-proton, so "which vkd3d-proton fix is in my Proton" can only be answered from Proton's submodule commit, not a version number. DeckForge's crowd data should record the Proton build string and Mesa version per run.
- **Persistence rules for DeckForge.** Everything DeckForge installs (Python venv, Vulkan layer manifest in `~/.local/share/vulkan/implicit_layer.d/`, configs) must live under `/home/deck` to survive updates. Anything in `/etc` or `/usr` is at risk, and Decky itself can be dropped by updates.
- **Measure in Game Mode only.** Desktop Mode had known performance gaps (fixed only "in several cases" in 3.8).

### Gaps
- The exact gamescope version or commit shipped in SteamOS 3.8.28 was not found (GitHub API access was blocked; release notes don't list it).
- Valve has not published the Mesa version for 3.8.28. 26.1.2 comes from one secondary source.
- I found no post-2023 measurement of gamescope limiter latency on the OLED, and no documentation of what `GAMESCOPE_LOW_LATENCY` changes.
- I found no primary source for the A/B rootfs partition layout or for whether `/etc` overlays and `/var` (Flatpaks) persist across updates. Commonly believed (rootfs-A/B, var-A/B, home), but not confirmed here.
- `SGSR` appears in gamescope's filter enum. Whether Steam's QAM exposes it on the Deck was not found. The name suggests Qualcomm's Snapdragon Game Super Resolution, but that is unverified.

## 3. Control points from userspace: QAM settings, programmatic control, SMU/sysfs, CPU, schedulers, memory

### Takeaway
A tool can reach every QAM knob through one of four layers, from most to least "official":
1. Steam's own per-game profile (protobuf in `config.vdf`, or the undocumented `SteamClient.System.Perf` JS API reachable from a Decky frontend).
2. **steamos-manager** over D-Bus / `steamosctl`: TDP, GPU performance level, manual GPU clock, CPU governor, boost, scheduler (LAVD).
3. Raw sysfs as root: hwmon `power*_cap`, `pp_od_clk_voltage`, SMT, EPP.
4. gamescope X atoms: fps limit, refresh, filter, sharpness.

Steam re-applies its per-game profile at game launch, so layers 2–4 can be silently overwritten. ryzenadj is not needed on the Deck.

### Cited Findings
**Steam per-game performance profiles (QAM)**
- Steam stores per-AppID Performance settings as hex strings in `config.vdf` under `Software/Valve/Steam/Perf/GameProfiles`. A contributor identified the format as a Steam client protobuf. NGnius (PowerTools maintainer) pointed to a frontend API, `SteamClient.System.Perf` (base64-encoded). He declined to modify Steam settings because the binary format could change and "the frontend API has no stability guarantee" — [PowerTools issue #88, undated](https://github.com/NGnius/PowerTools/issues/88)
- Steam applies per-app settings at game launch. SteamOS 3.8 fixed "a case where per-app performance settings would intermittently fail to apply when launching a game" — [GamingOnLinux, 2026-06-18](https://www.gamingonlinux.com/2026/06/steamos-3-8-is-out-with-initial-steam-machine-support-desktop-mode-upgrades-new-graphics-drivers/page=1/)

**steamos-manager / steamosctl (Valve's OS abstraction daemon)**
- Valve's MIT-licensed daemon, open-sourced after SteamOS 3.7 (May 2025) at `gitlab.steamos.cloud/holo/steamos-manager`. It is "a system daemon that aims to abstract Steam's interactions with the operating system": GPU clock management, TDP management, BIOS/dock updates, storage maintenance, max battery charge, and `EnterDownloadMode` — [GamingOnLinux, 2025-05-27](https://gamingonlinux.com/2025/05/steamos-manager-for-bios-updates-tdp-and-gpu-clock-controls-now-open-source)
- `steamosctl` talks to steamos-manager over D-Bus. There is a **user daemon on the session bus** and a **root daemon on the system bus** for privileged operations. Firmware updates and factory resets need elevated privileges. Written in Rust with contributions from Collabora and Igalia. Commands include:
  - TDP: `get/set-tdp-limit <watts>`, `get-tdp-limit-min`, `get-tdp-limit-max`
  - GPU: `get/set-gpu-performance-level <auto|low|high|manual|profile_peak>`, `get/set-manual-gpu-clock <MHz>`, `get/set-gpu-power-profile`
  - CPU: `get/set-cpu-scaling-governor`, `get/set-cpu-boost-state`
  - Other: `get/set-performance-profile`, `get/set-fan-control-state <bios|os>`, `get/set-max-charge-level`, `get-all-properties`, `get-device-model`
  - Source: [linuxcommandlibrary steamosctl, accessed 2026-10-11](https://linuxcommandlibrary.com/man/steamosctl)
- SteamOS 3.8: "Initial support for LAVD CPU scheduler via `steamosctl set-cpu-scheduler lavd`" (no device scope or default stated). Also "Steam uses steamos-manager to query and switch desktop sessions" — [GamingOnLinux, 2026-06-18](https://www.gamingonlinux.com/2026/06/steamos-3-8-is-out-with-initial-steam-machine-support-desktop-mode-upgrades-new-graphics-drivers/page=1/)

**Raw sysfs (root) — what plugins actually write on the Deck**
- TDP: SimpleDeckyTDP writes microwatts to `STEAM_DECK_TDP_PATH="/sys/class/hwmon/hwmon*/power*_cap"`, setting both power1 and power2 caps. It uses `subprocess.run(f"echo '{tdp_microwatts}' | tee {tdp_path}", shell=True, ...)` — [SimpleDeckyTDP `py_modules/devices/steam_deck.py`, main, read 2026-10-11](https://github.com/aarron-lee/SimpleDeckyTDP)
- GPU clock: SimpleDeckyTDP sets `/sys/class/drm/card?/device/power_dpm_force_performance_level` to `manual`, then writes `s 0 <min>`, `s 1 <max>`, `c` to `/sys/class/drm/card?/device/pp_od_clk_voltage`. Preset modes map to `auto`/`high`/`low` — [SimpleDeckyTDP `py_modules/gpu_utils.py` lines 18–19, 146–180](https://github.com/aarron-lee/SimpleDeckyTDP)
- Kernel doc: on VanGogh, select `manual` first; CPU core clocks use `p core index clock` (e.g. `p 2 0 800`), commit with `c`, reset with `r`. On APUs, reading `pp_od_clk_voltage` shows `OD_SCLK` and `OD_RANGE`. `pp_dpm_sclk` level masking and `pp_power_profile_mode` also require `manual` — [kernel docs v7.2](https://kernel.org/doc/html/v7.2/gpu/amdgpu/thermal.html)
- CPU paths used by SimpleDeckyTDP:
  - SMT: `/sys/devices/system/cpu/smt/control`
  - per-policy boost: `/sys/devices/system/cpu/cpufreq/policy*/boost`
  - EPP: `/sys/devices/system/cpu/cpu*/cpufreq/energy_performance_preference` and `energy_performance_available_preferences`
  - driver: `/sys/devices/system/cpu/amd_pstate/status`
  - Source: [SimpleDeckyTDP `py_modules/cpu_utils.py`](https://github.com/aarron-lee/SimpleDeckyTDP)
- SteamOS 3.7.5 reportedly changed the scaling driver from `acpi-cpufreq` to `amd-pstate-epp`, breaking EPP and boost controls on existing plugin installs — [SimpleDeckyTDP README](https://github.com/aarron-lee/SimpleDeckyTDP) ("reportedly")
- PowerTools (Decky) offers "Enable & disable CPU threads & SMT" — [PowerTools README](https://github.com/NGnius/PowerTools)

**ryzenadj / SMU**
- SimpleDeckyTDP lists the Steam Deck among devices that **don't need ryzenadj** for TDP control. It bundles ryzenadj for other AMD handhelds — [SimpleDeckyTDP README](https://github.com/aarron-lee/SimpleDeckyTDP)
- Stock RyzenAdj does not support Curve Optimizer on Van Gogh (`set_coall` returns "unsupported"); a fork by JamesCJ60 adds it. NGnius prefers the amdgpu `pp_od_clk_voltage` interface and avoids RyzenAdj on the Deck — [PowerTools issue #84, undated](https://github.com/NGnius/PowerTools/issues/84)

**Memory: zram, swap, UMA**
- zram "appeared in update 3.6". A user's config showed `zram-size = ram/2`, `compression-algorithm = zstd`, `swap-priority = 100`, plus a swap file (16 GB in that user's case, enlarged by CryoUtilities). The user reported more stutter in Hogwarts Legacy with zram disabled. Another user suggested a 2 GiB UMA frame buffer — [Steam Community thread, 2025-01-11 to 2025-02-05](https://steamcommunity.com/app/1675200/discussions/0/599641410463908507) (community; no Valve staff)
- After 3.8.20/3.8.28's VRAM-management rework, Boiling Steam argues BIOS UMA tweaks may be unnecessary, while PC Gamer expects minor iGPU gains — [NerdZap, 2026-10-07](https://nerdzap.com/news/steamos-3-8-28-steam-deck-what-changed/)

**Schedulers**
- LAVD (sched_ext) is opt-in on SteamOS 3.8+ via `steamosctl set-cpu-scheduler lavd` — [GamingOnLinux, 2026-06-18](https://www.gamingonlinux.com/2026/06/steamos-3-8-is-out-with-initial-steam-machine-support-desktop-mode-upgrades-new-graphics-drivers/page=1/); Phoronix also lists "Support for the LAVD CPU scheduler" in 3.8.10 — [Phoronix, 2026-06-18](https://phoronix.com/news/SteamOS-3.8.10-Stable)

### Inferences
- **Recommended control path for DeckForge Phase 1 (Tier S):** use `steamosctl` / the steamos-manager D-Bus API for TDP, GPU clock and governor. The user daemon means no root is likely needed, though this is unverified. It is Valve's own path, so values stay within Valve's limits (`get-tdp-limit-min/max`). Raw sysfs writes need root, bypass Valve's clamps, and conflict with Steam.
- **The real conflict is Steam's per-game profile.** It is applied at launch and stored in an undocumented protobuf, so a DeckForge-set TDP can be reverted when a game launches or the QAM is touched. Options:
  - (a) Instruct the user to apply DeckForge's recommendation in the QAM per-game profile. Safest; matches "Fede reviews evidence".
  - (b) Drive `SteamClient.System.Perf` from a Decky frontend. Unstable API.
  - (c) Re-assert after launch. Fragile, and fights Steam.

  Editing `config.vdf` protobuf directly is what the PowerTools maintainer refused to do, and DeckForge rule R10 (safety writes) and R7 (no real Steam install in dev) argue against it too.
- **Don't copy plugin code verbatim.** SimpleDeckyTDP's `shell=True` + `tee` pattern violates DeckForge rule R11. Equivalent writes should be direct file writes (or go through steamosctl) with argument lists.
- **LAVD is a cheap per-game experiment knob** (one `steamosctl` call, reversible) for CPU-bound titles. Its effect on frame-time percentiles on the Deck is unmeasured in sources found.
- **SMT off and lower CPU boost** are classic ways to shift watts from CPU to GPU inside the shared 15 W budget. They belong in the search space for GPU-bound titles.

### Gaps
- Whether `steamosctl set-tdp-limit` from the `deck` user session works without a password prompt, and whether Steam overrides it, was not found in documentation. This needs a bench test.
- The full list of QAM performance controls in the October 2026 Steam client was not found. Known from older sources: frame limit/refresh, allow tearing, half-rate shading, TDP limit, manual GPU clock, scaling filter. Whether an SMT/thread toggle still exists in the QAM was not confirmed.
- The half-rate shading implementation was not confirmed. RADV's dynamic VRS (`RADV_FORCE_VRS_CONFIG_FILE`, values `2x2/2x1/1x2/1x1`, on by default on Van Gogh) was built by Valve for power savings — [Phoronix, 2022-01-26](https://www.phoronix.com/news/RADV-Dynamic-VRS). But no source here ties the QAM toggle to it.
- ryzenadj's root and `iomem` requirements on SteamOS were not sourced (moot, since it isn't needed for TDP on the Deck).
- No source documented the protobuf schema of `Perf/GameProfiles` or the method names on `SteamClient.System.Perf`.

## 4. Steam data layout on SteamOS: libraries, Proton prefixes, launch options, shader cache, cloud

### Takeaway
Game settings for Proton titles live inside `steamapps/compatdata/<appid>/pfx/drive_c/users/steamuser/` (AppData/Local, AppData/Roaming, Documents), in the library where the game is installed (internal or SD card). Launch options live in `userdata/<id>/config/localconfig.vdf` and should only be edited with Steam closed. Steam Cloud can overwrite a settings file that is cloud-synced, even though Valve tells developers not to sync graphics settings.

### Cited Findings
- Paths (Steam Deck internal storage):
  - compatdata root: `/home/deck/.local/share/Steam/steamapps/compatdata/APPID/`
  - virtual C: drive: `.../pfx/drive_c/` (Program Files, users, windows)
  - Windows user dir: `.../pfx/drive_c/users/steamuser/` with `AppData/Local/`, `AppData/Roaming/`, `Documents/`
  - secondary libraries: each library has its own `steamapps/compatdata/APPID/pfx/`
  - microSD example mount: `/run/media/deck/SR256`
  - Flatpak Steam (non-Deck): `~/.var/app/com.valvesoftware.Steam/data/Steam/...`
  - Source: [GamingOnLinux guide, 2026-09-24](https://www.gamingonlinux.com/guides/view/how-to-find-where-steam-stores-proton-game-files/)
- Launch options are stored in `~/.local/share/Steam/userdata/<user-id>/config/localconfig.vdf` (as a `"LaunchOptions"` key inside the app's block). A CLI tool for editing them aborts if `steamwebhelper` is running, "Otherwise, launch options would not be accepted by the client". It has no backup step — [steam-launchoptions script (Fincer), originally 2018](https://fjordtek.com/git/Fincer/steam-launchoptions/blame/branch/master/steam_launchoptions.sh)
- Per-game performance (QAM) profiles live in `config.vdf` → `Software/Valve/Steam/Perf/GameProfiles` (protobuf hex) — [PowerTools issue #88](https://github.com/NGnius/PowerTools/issues/88)
- Valve guidance to developers: graphics settings "should be set and saved on a per-device basis" and kept out of cloud saves. Default graphics options for specific hardware are acceptable. Valve recommends "against restricting access to settings based on specific hardware" and "targeting Vulkan as your primary graphics API" — [Steamworks: Steam Hardware recommendations, undated, accessed 2026-10-11](https://partner.steamgames.com/doc/steamhardware/recommendations)
- SD-card libraries can live at the card root (`steamapps/`, `libraryfolder.vdf`) or under `SteamLibrary/`. Users reported Steam re-creating the library path after updates — [Steam Community thread, 2022-09-19](https://steamcommunity.com/app/1675200/discussions/0/5057002258672548404) (community)
- RADV on the Deck uses single-file pipeline caches. Mesa 23.1 cut that disk cache about 60% and enabled Graphics Pipeline Library by default (helps D3D11 and older, not vkd3d D3D12) — [Steam Deck HQ, ~spring 2023](https://steamdeckhq.com/ja/news/mesa-driver-pipeline-and-reduced-shader-cache-size/)

### Inferences
- **DeckForge's settings-file writer needs a resolver:** (library path from `libraryfolders.vdf`) + `compatdata/<appid>/pfx/drive_c/users/steamuser/` + an engine-specific relative path. It also needs a cloud-sync check: does the file sit under a Steam Auto-Cloud root? If so, a newer cloud copy can silently revert DeckForge's change. Snapshot before and after each launch to detect it.
- **Treat launch-option edits as Steam-closed-only operations,** or route them through the Steam client (Decky frontend API). The existing Decky plugins (lsfg-vk, Framegen) use a "copy launch option to clipboard" button rather than writing `localconfig.vdf`, which suggests the ecosystem avoids editing it live.
- Changing graphics settings or the driver changes pipelines. After any setting change, the first run has cold-cache stutter, so benchmarks should discard a warm-up pass.

### Gaps
- No primary source fetched for `libraryfolders.vdf` (commonly `~/.local/share/Steam/steamapps/libraryfolders.vdf`), `userdata/<id>/<appid>/remote` (Steam Cloud), the `steamapps/shadercache/<appid>/` layout (Fossilize `.foz`, Mesa cache, DXVK/vkd3d caches), or `user.reg`/`system.reg` in the prefix root. All are commonly known but unsourced here.
- I found no source on how Steam behaves if `config.vdf`/`localconfig.vdf` is edited while Steam runs (overwrite on exit vs ignore). The only evidence is the script's warning.
- "Documents/My Games" as a common location (e.g. Bethesda/UE titles) was not confirmed by the fetched guide, which only says "some games will use Documents instead".

## 5. Decky Loader plugin architecture and how existing plugins apply settings

### Takeaway
Decky runs as a root systemd service and injects into Steam's CEF UI through the remote-debugging endpoint at `localhost:8080`. Each plugin's Python backend drops to the `deck` user unless `plugin.json` has `"flags": ["root"]`. TDP plugins (SimpleDeckyTDP, PowerTools) are root plugins that write sysfs directly. Graphics plugins (Decky Framegen, decky-lsfg-vk) install files under `$HOME` and rely on the user pasting a wrapper launch option (`~/fgmod/fgmod %command%`, `~/lsfg %command%`).

### Cited Findings
- **Privilege model:** in `sandboxed_plugin.py`, each plugin process calls `setgid`/`setuid(UserType.EFFECTIVE_USER if "root" in self.flags else UserType.HOST_USER)` and sets `HOME`/`USER` to match. So root plugins run as root, and all others as the host user — [decky-loader `backend/decky_loader/plugin/sandboxed_plugin.py` lines 72–76, main, read 2026-10-11](https://github.com/SteamDeckHomebrew/decky-loader)
- **Injection:** `BASE_ADDRESS = "http://localhost:8080"`; the injector polls `{BASE_ADDRESS}/json` (CEF DevTools target list) — [decky-loader `backend/decky_loader/injector.py` line 12, ~377](https://github.com/SteamDeckHomebrew/decky-loader). Backend requires Python `>=3.10,<3.15` — [decky-loader `backend/pyproject.toml`](https://github.com/SteamDeckHomebrew/decky-loader)
- `plugin.json` `flags`: `"debug"` (auto reload), `"root"` ("ONLY DO THIS WHEN ACTUALLY REQUIRED"). The backend is a `main.py` `Plugin` class with async methods callable from the frontend, plus `_main` (long-running) and `_unload`. `package.json` `remote_binary` entries need `sha256hash`, and non-FOSS binaries need Loader team approval — [Decky wiki: getting started, accessed 2026-10-11](https://wiki.deckbrew.xyz/plugin-dev/getting-started)
- **Backend environment variables:** `DECKY_USER`, `DECKY_USER_HOME` (e.g. `/home/deck`), `DECKY_HOME` (`/home/deck/homebrew`), `DECKY_PLUGIN_SETTINGS_DIR` (`.../homebrew/settings/<plugin>`), `DECKY_PLUGIN_RUNTIME_DIR` (`.../homebrew/data/<plugin>`), `DECKY_PLUGIN_LOG_DIR` (`.../homebrew/logs/<plugin>`), `DECKY_PLUGIN_DIR`, `DECKY_VERSION`. `USER`/`HOME` reflect the effective user (`root`/`/root` for root plugins) — [Decky wiki: env vars](https://wiki.deckbrew.xyz/plugin-dev/env-vars)
- Decky stable was reportedly v3.2.6 (2026-06-24). Maintainers "routinely patch stable within days of a Valve-side beta change" (e.g. v3.2.3 on 2026-03-31 for the 2026-03-19 client beta) — [tech-insider.org, 2026-06-16](https://tech-insider.org/decky-loader-setup-2026/) (aggregator; unverified)
- **SimpleDeckyTDP:** `"flags": ["root"]`. Settings live at `$HOME/homebrew/settings/SimpleDeckyTDP/settings.json`. Supports per-game TDP profiles with optional AC profiles, and writes sysfs as listed in section 3 — [SimpleDeckyTDP `plugin.json` and README](https://github.com/aarron-lee/SimpleDeckyTDP)
- **Decky Framegen:** downloads OptiScaler into `~/fgmod`, then the user pastes `~/fgmod/fgmod %command%` and uninstalls with `~/fgmod/fgmod-uninstaller.sh %command%`. Since v0.15.1, environment variables in the launch option override `OptiScaler.ini` on each launch (e.g. `Dx12Upscaler=fsr31 ~/fgmod/fgmod %command%`). It bundles **OptiScaler 0.9.4** (FFX 2.3 SDK / FSR 4.1.1), offers `FSR_Fsr4ForceEnableInt8=true`, and has a "4.1.1 Valve RDNA2 Compatibility" mode that uses Valve's `amdxcffx64.dll`/`amdxc64.dll` — [Decky-Framegen README, main, read 2026-10-11](https://github.com/xXJSONDeruloXx/Decky-Framegen)
- **decky-lsfg-vk:** installs the layer library to `~/.local/lib/`, the implicit-layer manifest to `~/.local/share/vulkan/implicit_layer.d/`, and config to `~/.config/lsfg-vk/conf.toml`. Config changes "apply immediately without restarting games". Per-game enable is the `~/lsfg %command%` launch option, offered via a "Launch Option Clipboard" button. It requires the purchased Lossless Scaling DLL (auto-detected). The release list showed v0.12.1 (2025-10-22) as latest, which may be stale; the compendium notes lsfg-vk core v2.0 in Sep 2026 — [decky-lsfg-vk GitHub, accessed 2026-10-11](https://github.com/xXJSONDeruloXx/decky-lsfg-vk)
- PowerTools' maintainer deliberately avoids editing Steam's settings and prioritizes them over the plugin's own — [PowerTools issue #88](https://github.com/NGnius/PowerTools/issues/88)

### Inferences
- **A DeckForge Decky plugin would be two halves.**
  - The **frontend** (runs inside Steam's CEF) is the only sanctioned way to call Steam's internal JS (`SteamClient.*`): per-game Perf profile, launch options, current running appid.
  - The **backend** (Python, non-root by default) runs the DeckForge engine.

  Root should be avoided if steamosctl suffices, which fits CLAUDE.md's principle of least privilege.
- **The "wrapper launch option" pattern** (`~/x %command%`) is the ecosystem's de-facto per-game opt-in. It is also exactly CLAUDE.md's planned per-game enable for Tier I. DeckForge's Vulkan layer can follow lsfg-vk: implicit layer in `~/.local/share/vulkan/implicit_layer.d/` with an `enable_environment` gate set by the wrapper.
- **Hot-reload works:** lsfg-vk proves a config file can be re-read by a running layer. That is a precedent for DeckForge's live VRS/LOD-bias experiments without game restarts.
- **Decky is fragile across SteamOS updates and Steam client betas,** so DeckForge's core should work without Decky (Python CLI + steamosctl). Decky should be the UX layer only.

### Gaps
- The `@decky/api` / `@decky/ui` frontend packages, the `callable` API and the `decky` Python module (`decky.emit`, `decky.logger`) were not covered by the fetched wiki page.
- I found no documentation of which `SteamClient.Apps.*` methods (e.g. setting launch options) exist or are stable.
- I found no source on how SimpleDeckyTDP detects the running game for per-game profiles.

## 6. 2026 platform changes: SteamOS 3.8/3.9, Steam Machine/Frame, Valve per-game settings and performance data, new APIs

### Takeaway
2026 shifted SteamOS from "Deck OS" to a multi-device platform (Steam Machine, Steam Frame, third-party handhelds). Valve also built **official per-device default-settings and performance-telemetry plumbing** into Steamworks: SDK 1.65 adds `GetSteamHardwareDefaultConfig`, plus fps reports that carry the graphics setting and render resolution, and developers receive opt-in framerate data from Deck users. This is the closest thing to "per-game recommended settings from Valve", and it is developer-driven, not user-tunable.

### Cited Findings
- **Steamworks SDK 1.65 (2026-07-24):**
  - `IsRunningOnSteamHardware` (replaces `IsRunningOnSteamDeck`; Valve says "should mainly be used for analytics, technical support and diagnostics")
  - `GetSteamHardwareDefaultConfig` (loads developer-prepared defaults for specific Valve hardware; Valve can update them for future devices without a game rebuild)
  - `IsRunningUnderProton`, `SetGamePerformanceSetting`, `SetGameRenderResolution`
  - Anonymous fps reports can now include the game's relative graphics setting and render resolution, sent only if the player opts in
  - Source: [Digital Citizen, 2026-07-24](https://www.digitalcitizen.life/steamworks-sdk-1-65-helps-developers-optimise-games-for-steam-deck-steam-machine-and-steam-frame/)
- **Developer framerate data (2026-04-23):** Valve gives developers a trailing 30-day daily-average framerate chart from opt-in Deck players, with per-date variance "planned", plus a post-play survey on whether players agree with the Verified rating (>95% agree). A February 2026 Steam update added an opt-in to send anonymous performance data — [GamingOnLinux, 2026-04-23](https://www.gamingonlinux.com/2026/04/valve-make-steps-to-improve-steam-deck-verification-giving-developers-more-performance-data/page=1/)
- Steam is reportedly testing store-page FPS estimates from crowd data (April 2026) — search-result headlines only, not fetched: [TechSpot](https://www.techspot.com/news/111951-steam-could-soon-show-estimated-fps-based-crowd.html), [Godisageek, 2026-04](https://godisageek.com/2026/04/steam-fps-estimator-game-performance-pc/)
- Valve says it is "currently working on updated APIs to help game developers detect the type of hardware their game is running on" — [Steamworks: Steam Hardware recommendations](https://partner.steamgames.com/doc/steamhardware/recommendations)
- **Steam Machine:**
  - Announced 2025-11-12 with a semi-custom 6-core Zen 4 (up to 4.8 GHz), semi-custom RDNA3, 16 GB DDR + 8 GB GDDR6, 512 GB / 2 TB
  - Delayed in Feb 2026 over RAM/storage shortages and pricing — [Engadget, 2026-02-05 (updated 2026-03-11)](https://www.engadget.com/gaming/pc/everything-we-know-about-valves-new-steam-machine-200458817.html)
  - Wikipedia states a 2026-06-29 release — [Wikipedia: Steam Machine](https://en.wikipedia.org/wiki/Steam_Machine) (not independently confirmed)
  - SteamOS 3.8.28 ships fixes for "Steam Machine (Firmware 108)", implying units are in users' hands — [GamingOnLinux, 2026-09-25](https://www.gamingonlinux.com/2026/09/steamos-3-8-28-stable-released-with-big-improvements-for-steam-deck-steam-machine-and-more-hardware-support/)
- **Steam Frame** (VR) runs a separate SteamOS 0.4.x branch (0.4.1 beta on 2026-09-26) — [warp2search, 2026-09-26](https://www.warp2search.net/story/valve-ships-steamos-392-and-041-betas-for-steam-deck-machine-and-frame/). The 2026 Steam Controller is supported by the in-kernel `hid_steam` driver as of 3.8.28 — [GamingOnLinux, 2026-09-25](https://www.gamingonlinux.com/2026/09/steamos-3-8-28-stable-released-with-big-improvements-for-steam-deck-steam-machine-and-more-hardware-support/)
- **Third-party handhelds on SteamOS 3.8:** TDP control for the ASUS ROG Xbox Ally series; controller support for Legion Go 2, OneXPlayer, MSI Claw and others; charge limiting for Legion Go/Go S/Go 2 — [GamingOnLinux, 2026-06-18](https://www.gamingonlinux.com/2026/06/steamos-3-8-is-out-with-initial-steam-machine-support-desktop-mode-upgrades-new-graphics-drivers/page=1/). In May 2025 Valve added a compatibility rating for "any device that's not a Steam Deck" — [Wikipedia: Steam Deck](https://en.wikipedia.org/wiki/Steam_Deck)

### Inferences
- **Valve now collects the same tuple DeckForge plans to crowdsource** (game, setting level, render resolution, fps), but only for developers, coarse (relative setting level), and opt-in. DeckForge's differentiators remain: (a) per-knob granularity, (b) frame-time percentiles and image-quality scores rather than averages, and (c) user-side application.
- **`GetSteamHardwareDefaultConfig` means some games will ship Valve-hardware-specific defaults.** DeckForge's search should treat the game's own "Deck default" as the baseline to beat, and should detect when a game patch changes it.
- **Multi-device SteamOS raises the value of the steamos-manager abstraction:** it exposes the same TDP and GPU knobs across Deck, Ally and Legion. A DeckForge that targets steamosctl rather than Deck-specific sysfs paths could later run on other SteamOS handhelds. Crowd data must then be keyed by device model.
- The Deck has no successor in sight and prices are rising, which supports the compendium's market thesis.

### Gaps
- The exact semantics and payload of `GetSteamHardwareDefaultConfig` (developer-authored key/values? Valve-curated?) were not found in primary Steamworks docs; there was only a secondary article.
- The Steam Machine release date and price could not be confirmed from a primary source; the web search budget ran out before verification.
- I found no evidence that Valve exposes per-game recommended settings to users or third-party tools, or a public API for the opt-in framerate dataset.
