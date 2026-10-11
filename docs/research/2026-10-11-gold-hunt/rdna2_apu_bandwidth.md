# Memory-bandwidth and GPU-architecture levers on the Steam Deck OLED (Van Gogh/Sephiroth, RDNA2, RADV, vkd3d-proton)

Scope and labels used below. **[measured]** means a third party ran the test. **[claimed]** means a vendor, author or guide said so without data. **[code]** means I read it in source; line numbers are from today (2026-10-11). The Mesa source comes from the `chaotic-cx/mesa-mirror` main branch, which may be newer than the Mesa 26.1.2 that SteamOS 3.8.28 reportedly ships. vkd3d-proton source is from `master`, which is past the 3.0.1 tag. **[doc]** means official documentation. **[inference]** is my own reasoning or arithmetic.

Overall verdict: on the Deck, memory-bandwidth and compression levers are worth low single-digit percentages each, if anything. Wilds runs at about 30 fps on the Deck with upscaling. A locked 40 fps needs about +33%, and none of these levers delivers that alone. They are A/B candidates to stack on top of settings and resolution changes. The cheap, reversible ones are env vars and drirc entries, which fit Tier S via launch options. The large-gain ideas (format demotion, forcing DCC) carry high risk and belong in a vkd3d-proton fork with a per-game allowlist, if anywhere.

---

## 1. How bandwidth-bound is Van Gogh in games?

### Takeaway
The only hard GPU bandwidth figure comes from the LCD Deck in 2023: over 70 GB/s achieved out of 88 GB/s theoretical. I found no RGP/per-pass, L2 hit-rate or CPU-to-GPU contention measurements for any game on the Deck. The best indirect evidence is a natural experiment: the OLED has 16.3% more bandwidth and measured only 2–9% faster than the LCD. So the GPU is partly bandwidth-sensitive, not fully bandwidth-bound.

### Cited Findings
- **[measured, older, Mar 2023, LCD Deck]** GPU bandwidth test: "over 70 GB/s"; theoretical 88 GB/s (LPDDR5-5500, 4×32-bit). The author says LPDDR5 bandwidth is "close to what it should be capable of on paper." — [Chips and Cheese, Van Gogh](https://chipsandcheese.com/p/van-gogh-amds-steam-deck-apu) ([dated URL](https://old.chipsandcheese.com/2023/03/05/van-gogh-amds-steam-deck-apu/))
- **[measured, 2023]** Cache sizes:
  - L0 vector and scalar caches: 16 KB each. L1: 128 KB. L2: 1 MB, which the author calls "disproportionately large" (desktop RDNA2 scaled to 4 WGPs would be under 512 KB).
  - No Infinity Cache.
  - Van Gogh's L2 is faster than desktop RDNA2's at matched clocks. DRAM latency is "poor."
  - The article gives no ns values for the GPU caches. CPU DRAM latency is about 150 ns, and CPU-side bandwidth is only about 25 GB/s.
  - Source: [Chips and Cheese](https://chipsandcheese.com/p/van-gogh-amds-steam-deck-apu)
- **[claimed/predicted, not measured]** C&C says the CPU and GPU compete for memory bandwidth and predicts the GPU still has plenty when sharing, but it did not measure contention. Its Cyberpunk profiling used CPU-side counters and gives no GPU-side bandwidth figure. — [Chips and Cheese](https://chipsandcheese.com/p/van-gogh-amds-steam-deck-apu)
- **[measured, Nov 2023]** OLED memory is LPDDR5-6400 vs 5500 on the LCD, "16.3% more memory bandwidth." Digital Foundry measured the OLED at 2–9% faster than the LCD. The coverage names no games or fps. — [OC3D](https://overclock3d.net/news/systems/valves-steam-deck-oled-isnt-just-a-screen-upgrade-its-faster-and-kills-input-lag-too/)
- **[measured, 2023]** In a GPU-bound sequence the GPU draws over 10 W while the CPU drops below base clock at 2–3 W, inside an APU cap of about 16 W. — [Chips and Cheese](https://chipsandcheese.com/p/van-gogh-amds-steam-deck-apu)
- **[measured, third-party via outlet, Jan 2026]** After the January 2026 PC patch, Wilds is "roughly playable at ~30 FPS" on the Deck without frame generation, with FSR/XeSS upscaling. These numbers come from Daniel Owen and Deck Wizard; Notebookcheck did not measure them. The patch also lowered CPU load and VRAM demand (no figures). — [Notebookcheck](https://www.notebookcheck.net/Monster-Hunter-Wilds-fixes-DLC-bug-greatly-reduces-FPS-drops-and-runs-at-30-FPS-on-Steam-Deck.1215270.0.html)

### Inferences
- If the OLED keeps the LCD's roughly 80% efficiency, achievable GPU bandwidth is about 80–85 GB/s. At 40 fps (25 ms) that is roughly 2 GB of DRAM traffic per frame.
- The OLED-vs-LCD result (+16% bandwidth → +2–9% fps) implies an elasticity of about 0.1–0.55. A lever that cuts DRAM traffic by X% should yield at most about 0.1–0.55·X% fps. Caveat: the OLED's 6 nm APU also changes power behaviour, so not all of that gain comes from memory.
- Wilds at about 30 fps needs +33% for a locked 40, which is far beyond what traffic-reduction levers can supply.

### Gaps
- No RGP captures of Wilds (or any RE Engine title) on the Deck showing memory-bound passes.
- No GPU L2 hit-rate data for Van Gogh in games.
- No measured CPU-to-GPU bandwidth contention on the Deck.
- No OLED-specific microbenchmark (C&C tested the LCD model).

---

## 2. Render-target formats (RGBA16F vs R11G11B10F vs RGB10A2) and format demotion

### Takeaway
RGBA16F is 8 B/px; R11G11B10F and RGB10A2 are 4 B/px. At 800p a full-surface access is about 8.2 MB vs 4.1 MB, so each demoted read or write saves around 0.05 ms at about 80 GB/s. That is small at Deck resolutions, and smaller again behind FSR. The precedent is old (ATI's 2010 "FP16 Demotion"). A layer-level demotion has many correctness traps.

### Cited Findings
- **[measured by outlet, older ~2010]** ATI/AMD Catalyst A.I. "FP16 Demotion" was an optional driver setting.
  - Measured about 17% faster at high resolution and about 10% at lower resolution, in 2 of 4 games.
  - Only 1 of 4 games showed "any real visible influence."
  - NVIDIA called it cheating.
  - Source: [Legit Reviews](https://legitreviews.com/?p=9031)
  - AMD later exposed a "Surface Format Optimization" driver toggle (thread title only): [AMD community](https://community.amd.com/t5/pc-drivers-software/surface-format-optimization/m-p/632368)
- **[doc, 2023]** GPUOpen's RDNA guide:
  - Write all colour channels, because partial writes disable compression.
  - Avoid TYPELESS/MUTABLE formats on render targets, depth targets and UAVs.
  - Minimize the data a pixel shader writes.
  - Avoid RGB32.
  - It gives no per-format export-rate table.
  - Source: [GPUOpen RDNA Performance Guide](https://gpuopen.com/learn/rdna-performance-guide/)
- **[code]** RADV's DCC compatibility needs a view-format list. If an image is MUTABLE with no format list, DCC is disabled on GFX10.3. A demoted format must therefore stay DCC-compatible with every view format. — [radv_image.c L150–186](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/radv_image.c)

### Inferences
- Budget arithmetic: one 800p RGBA16F full read+write is about 16 MB, roughly 0.8% of a 25 ms frame's DRAM capacity. Demoting ten such accesses saves at most about 4% of bandwidth. That becomes about 0.4–2% fps after the elasticity above, and less with DCC already compressing render targets or FSR running at 50–59% scale.
- A Vulkan layer that demotes formats would have to verify all of the following:
  - **Alpha unused:** no blend state reads destination alpha; no shader reads `.a` (needs SPIR-V analysis of every pipeline that samples or loads the image).
  - **No negative values:** R11G11B10F is unsigned, and engines with sharpening or TAA can produce negatives.
  - **No reinterpreting views:** no RGBA16_UINT/R32G32 views, no size-compatible copies, no buffer↔image copies or readbacks.
  - **No memory aliasing:** vkd3d-proton places D3D12 placed resources at heap offsets, and the game may alias them.
  - **Precision:** 6/6/5-bit mantissas cause banding and a blue-channel shift.
  - **MSAA and storage writes:** vkd3d-proton writes storage images without a declared format, so the store path may work, but this is unverified.
- Doing this per game, by shader hash, in a vkd3d-proton fork is much safer than a generic layer, because vkd3d-proton knows the D3D12 TYPELESS families and heap placement.
- Expected value is low. Risk is high.

### Gaps
- No RDNA2 export (ROP) rate per format from AMD.
- No precedent found for format demotion in Mesa drirc or in Deck mods.
- Which formats Wilds' intermediates use is unknown; it needs a RenderDoc/RGP capture.

---

## 3. Compression: DCC and HTILE on GFX10.3 under RADV

### Takeaway
DCC is on by default in RADV, but only for colour-attachment images larger than 512×512. Storage (UAV) images that are also render targets keep DCC on GFX10.3 unless their format allows atomics. Compute-only UAVs, which have no colour-attachment usage, never get DCC. HTILE/HiZ is on for depth attachments, including mips on GFX10+. No measured RDNA2 DCC savings were found.

### Cited Findings
- **[code]** DCC is only used when fast-clear is allowed. That requires `COLOR_ATTACHMENT` usage, and single-sample images up to 512×512 are excluded ("cost of the eliminate pass can be higher than the benefit"). — [radv_image.c L135–147, L254](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/radv_image.c)
- **[code]** Storage usage disables DCC on GFX9 and earlier. It also disables DCC whenever the format or view list allows atomics ("atomics will always decompress"). Mipmapped arrays get no DCC ("performance is worse"). — [radv_image.c L219–286](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/radv_image.c)
- **[code]** DCC image stores on GFX10.3 need 128B independent blocks with a 128B max compressed block, or the GFX10.3-only 64B mode. Otherwise DCC on a storage image is dropped late. — [ac_surface.c L217–257](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/common/ac_surface.c); [radv_image.c L289–299](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/radv_image.c)
- **[code]** HTILE is used for depth/stencil attachments. Mips are allowed on GFX10+. Images under 8×8 are skipped unless VRS attachments are in use on GFX10.3. — [radv_image.c L320–352](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/radv_image.c)
- **[code]** vkd3d-proton comment: "On AMD native drivers, UAV + RTV usage tends to disable compression, but RADV tends to enable it. This is another source of application bugs." Escape hatches:
  - `disable_uav_compression`, `disable_color_compression`, `disable_depth_compression`, `disable_simultaneous_uav_compression`.
  - SIMULTANEOUS_ACCESS + UAV can disable compression through full-mutable format or `image_compression_control`.
  - Source: [resource.c L781–815](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d/resource.c); [config_flag_decl.h](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/include/private/config_flag_decl.h)
- **[code]** Per-game compression *disables* (all for correctness, none for speed):
  - RADV drirc `radv_disable_dcc`: DOOM 2016, Wolfenstein II, WWE 2K23.
  - `radv_disable_dcc_stores`: Indiana Jones TGC, DOOM: The Dark Ages.
  - `radv_disable_dcc_mips`: RDR2.
  - Source: [00-radv-defaults.conf](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/00-radv-defaults.conf)
  - vkd3d-proton: `DISABLE_UAV_COMPRESSION` for Spider-Man and SCPSL; `DISABLE_COLOR_COMPRESSION` for ROTTR. Source: [device_workarounds.c L71–206](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d/device_workarounds.c)
  - The vkd3d-proton 3.0 notes confirm the Spider-Man (RT issues on RDNA2) and ROTTR cases: [GamingOnLinux, 17 Nov 2025](https://www.gamingonlinux.com/2025/11/vkd3d-proton-3-0-brings-fsr4-support-shader-backend-rewrite-lots-of-bug-fixes-and-performance-upgrades/page=1/)
  - **No Wilds entry disables compression.**
- **[doc]** `RADV_DEBUG=nodcc`, `nohiz` and `nodisplaydcc` exist for debugging only. — [Mesa envvars](https://github.com/chaotic-cx/mesa-mirror/blob/main/docs/envvars.rst)
- **[doc, older 2016, updated note for RDNA]** GPUOpen DCC guidance:
  - DCC needs no setup.
  - UAV writability historically disabled DCC; RDNA differs on when decompression happens, so check RGP.
  - Fast-clear values are 0/1 combinations.
  - The article quotes no bandwidth savings.
  - Source: [GPUOpen DCC overview](https://gpuopen.com/dcc-overview/)

### Inferences
- **Enable-compression lever:** a Vulkan layer or vkd3d-proton fork could add `COLOR_ATTACHMENT` usage to large storage-only images, so RADV gives them DCC with image stores. Problems:
  - It changes memory requirements and swizzle mode. That breaks vkd3d-proton heap placement and aliasing assumptions.
  - It is excluded for atomic-capable formats.
  - On GFX10.3, compute-written DCC uses smaller independent blocks, so the compression ratio is lower.
  - The net effect is unknown and could be negative.
  - It is only plausible in a vkd3d-proton fork with a per-resource allowlist validated in RGP.
- **Nothing to disable:** for Wilds no compression is turned off by default, so there is no "re-enable" win from removing a workaround.

### Gaps
- No measured DCC bandwidth saving on RDNA2 or Van Gogh.
- No data on how many of Wilds' UAVs are compute-only (and so uncompressed).
- Whether RADV's DCC defaults differ in 26.1.2 vs main is not verified.

---

## 4. Textures: anisotropic filtering, formats and mip caps, VRAM budget on 16 GB UMA

### Takeaway
RADV can force anisotropy globally (`RADV_TEX_ANISO`), but it overrides *every* sampler, including ones the game left non-anisotropic. On APUs, RADV reports two-thirds of (GTT + carveout) as the VRAM heap and one-third as GTT. A per-game drirc can merge them into one heap. The 1 GB vs 4 GB UMA question has guide recommendations but no controlled benchmark. SteamOS 3.8.28's "VRAM management" work mainly targets discrete GPUs.

### Cited Findings
- **[code/doc]** `RADV_TEX_ANISO` is documented as "force anisotropy filter (up to 16)." In code, when it is ≥0 it replaces the sampler's anisotropy, including samplers with anisotropy disabled.
  - Source: [radv_sampler.c L134–144](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/radv_sampler.c); [envvars](https://github.com/chaotic-cx/mesa-mirror/blob/main/docs/envvars.rst)
  - vkd3d and DXVK set `radv_disable_aniso_single_level=true` for D3D-correct behaviour: [00-radv-defaults.conf L15–27](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/00-radv-defaults.conf)
- **[code]** APU heaps:
  - By default the VRAM heap is 2/3 of (GTT + visible VRAM) and GTT is 1/3, "because the carveout is usually too small."
  - `radv_enable_unified_heap_on_apu` exposes one DEVICE_LOCAL heap with everything.
  - Source: [radv_physical_device.c L459–472, L3302–3316](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/radv_physical_device.c)
  - The option is currently enabled only for RDR2, listed in [01-radv-performance.conf](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/01-radv-performance.conf), with its origin in [MR 18884](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/18884).
- **[doc]** `RADV_PERFTEST=nogttspill` "disable GTT spilling when allocating memory." `sam`/`nosam` toggle "all VRAM CPU-visible" optimizations. — [envvars](https://github.com/chaotic-cx/mesa-mirror/blob/main/docs/envvars.rst)
- **[code]** vkd3d-proton's Wilds profile:
  - `SKIP_NULL_SPARSE_TILES` + `NO_UPLOAD_HVV`, with the comment "impossible amdgpu bug with PRT sparse… No upload HVV as a performance opt since it's very CPU intensive, and there's no obvious GPU uplift."
  - Plus a descriptor-heap-robustness shader quirk for all Wilds shaders (bogus bindless indices loaded from sparse pages).
  - `VKD3D_CONFIG=log_memory_budget` exists for diagnosing budget.
  - Source: [device_workarounds.c L160–164, L659–667](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d/device_workarounds.c); [config_flag_decl.h](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/include/private/config_flag_decl.h)
  - The 3.0 notes add: "A proper hardware workaround in RADV is still pending." Source: [GamingOnLinux](https://www.gamingonlinux.com/2025/11/vkd3d-proton-3-0-brings-fsr4-support-shader-backend-rewrite-lots-of-bug-fixes-and-performance-upgrades/page=1/)
- **[claimed, no test data]** A Wilds 40 fps Deck guide says "Always set your UMA Buffer Size to 4GB," with Medium textures only when using 4 GB, otherwise mostly Low, at 1280×800 with FSR Balanced/Performance. Its FAQ contradicts its body. — [Evetech, Feb 2026](https://evezone.evetech.co.za/performance-pulse/steam-deck-40fps-settings-mh-wilds)
- **[anecdotal, older Apr 2024]** Steam Deck HQ needed 4 GB UMA in *No Rest for the Wicked* to reduce freezes and crashes; it ran no 1 GB vs 4 GB fps comparison. — [Steam Deck HQ](https://steamdeckhq.com/?p=17670)
- **[changelog/claimed]** SteamOS 3.8.28 (stable, 25 Sep 2026):
  - "Greatly improved VRAM management" and a new Mesa major release with RT gains.
  - Kernel 6.18.50.
  - Source: [GamingOnLinux](https://www.gamingonlinux.com/2026/09/steamos-3-8-28-stable-released-with-big-improvements-for-steam-deck-steam-machine-and-more-hardware-support/)
  - NerdZap ties the VRAM work to Natalie Vock's foreground-priority eviction patches aimed at 8 GB dGPUs. It says Valve published no benchmarks and expects small Deck gains at most. Source: [NerdZap](https://nerdzap.com/news/steamos-3-8-28-steam-deck-what-changed/)

### Inferences
- **Aniso:** capping anisotropy (e.g. `RADV_TEX_ANISO=4`) also *raises* samplers the game left at 1×, and may touch shadow or point samplers. It is not a clean "cap." A clean cap needs a layer or fork that clamps `maxAnisotropy` only where it is >N. AF mostly costs texture-unit throughput and L1/L2 traffic; DRAM cost is modest because neighbouring texels are cache-resident.
- **Texture formats and mip caps:** the BC formats are fixed by the game's assets and a tool cannot change them. A mip-LOD bias or min-LOD clamp through a layer (`VK_EXT_image_view_min_lod` / sampler `minLod`) is possible but visibly blurs textures. The Wilds in-game texture setting is the Tier S equivalent.
- **UMA:** the carveout does not change physical bandwidth. It changes what heap size RADV reports, and therefore Wilds' streaming budget and OOM behaviour, and it takes RAM from the OS. Expect stability and texture-quality effects, not fps.

### Gaps
- No controlled 1 GB vs 4 GB UMA benchmark in Wilds (or any title) on SteamOS 3.8.
- No measurement of GTT vs carveout access speed on Van Gogh.
- I did not read how vkd3d-proton computes the DXGI budget from `VK_EXT_memory_budget`.
- No measured AF cost on RDNA2 APUs; search returned only 2002–2003 desktop results.

---

## 5. Async compute on the Deck (vkd3d-proton + RADV)

### Takeaway
By default vkd3d-proton maps D3D12 compute queues to a dedicated Vulkan compute-only family when one exists, which RADV provides. D3D12 copy queues fall back to that compute family, because RADV's SDMA transfer queue is off by default. `single_queue` collapses everything onto graphics; `RADV_QUEUE_DISABLE=compute` hides the compute family and has the same effect. I found no measured Deck results either way.

### Cited Findings
- **[code]** Queue mapping in vkd3d-proton:
  - COMPUTE goes to a compute-only family, or falls back to graphics.
  - TRANSFER goes to a transfer-only family, or falls back to COMPUTE.
  - `single_queue` forces both onto GRAPHICS.
  - Source: [device.c L3014–3061](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d/device.c)
  - README: `single_queue` = "Do not use asynchronous compute or transfer queues." Source: [vkd3d-proton README](https://github.com/HansKristian-Work/vkd3d-proton)
- **[code/doc]** RADV options:
  - `RADV_QUEUE_DISABLE` accepts gfx, compute, transfer and others.
  - The SDMA transfer queue is experimental (`RADV_EXPERIMENTAL=transfer_queue`, "not yet spec compliant") or per-game via drirc `radv_enable_transfer_queue` (used for Ghost Recon Breakpoint "to offload the compute queue").
  - Source: [radv_instance.c](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/radv_instance.c); [envvars](https://github.com/chaotic-cx/mesa-mirror/blob/main/docs/envvars.rst); [01-radv-performance.conf](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/01-radv-performance.conf)
- **[code + claimed]** vkd3d-proton "staggered submissions":
  - Software scheduling on single-graphics-queue implementations.
  - The 2.14 notes say it "may regress GPU performance in some other cases" and claim "almost doubled performance in some cases" (FF XVI with FSR3 FG on RADV).
  - `no_staggered_submit` disables it, and it is the default for all Unreal titles.
  - Source: [GamingOnLinux 2.14, Dec 2024](https://www.gamingonlinux.com/2024/12/direct3d-12-to-vulkan-project-vkd3d-proton-v2-14-out-now-with-various-performance-improvements/comment_id=274050); [device_workarounds.c L810–820](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d/device_workarounds.c); [command.c ~L24342, L25279](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d/command.c)
- **[doc, 2023]** AMD: async compute helps "when graphics can't produce enough work to fill the GPU" and "performs poorly when executed in parallel with export bound shaders." — [GPUOpen RDNA guide](https://gpuopen.com/learn/rdna-performance-guide/)

### Inferences
- On an 8-CU, bandwidth-limited APU there is little idle-unit headroom for async overlap, and overlap adds cache and DRAM contention. The gain is likely small and could be negative.
- `VKD3D_CONFIG=single_queue` and `VKD3D_CONFIG=no_staggered_submit` are zero-image-cost, reversible launch-option A/B tests (Tier S). They are worth benchmarking on Wilds.
- RDNA2 hardware runs the graphics and compute (ACE) rings concurrently. I did not find a RADV-specific citation confirming concurrent execution on GFX10.3.

### Gaps
- No measured single_queue vs default numbers on the Deck or for Wilds.
- No source on RADV queue priorities or pre-emption behaviour (`VK_EXT_global_priority`, gamescope's queue priority) on Van Gogh.

---

## 6. Wave32 vs wave64 under ACO on RDNA2

### Takeaway
Current RADV defaults on GFX10.3:
- Compute: wave64, but wave32 for workgroups of 32 invocations or fewer.
- Pixel shaders: wave64 ("wave64 is recommended").
- Vertex/geometry (NGG): wave64.
- Legacy GS: always wave64.
- Ray tracing: wave32.

App-required subgroup sizes win. The `cswave32`, `pswave32` and `gewave32` perftest flags still exist. I found no measured results.

### Cited Findings
- **[code]** Defaults: `cs/ps/ge/rt_wave_size = 64`, then on GFX10+ each switches to 32 only via `RADV_PERFTEST`, except RT, which defaults to 32 ("better perf due to less issues with divergence"). Comment: "For pixel shaders, wave64 is recommended." — [radv_physical_device.c L2836–2860](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/radv_physical_device.c)
- **[code]** Per-shader selection:
  - Workgroups of 32 or fewer → wave32.
  - Wide-subgroup or cooperative-matrix shaders → forced full wave64 when cswave32 is on, because "Games don't always request full subgroups when they should, which can cause bugs if cswave32 is enabled."
  - Legacy GS on GFX10–10.3 → wave64.
  - Source: [radv_shader.c L385–431](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/radv_shader.c)
- **[doc]** `cswave32`, `pswave32`, `gewave32`: "enable wave32 for compute / pixel / vertex-tess-geometry shaders (GFX10+)." — [envvars](https://github.com/chaotic-cx/mesa-mirror/blob/main/docs/envvars.rst)
- **[doc]** AMD: RDNA natively runs wave32, and workgroups that are multiples of 64 perform best across generations. — [GPUOpen RDNA guide](https://gpuopen.com/learn/rdna-performance-guide/)

### Inferences
- `RADV_PERFTEST=cswave32` is a plausible A/B for Wilds' compute-heavy passes: less divergence waste, at the cost of more instruction-issue overhead.
- Correctness risk: shaders using subgroup ops that assume 64 lanes without requesting full subgroups can break.
- `pswave32` goes against RADV's own recommendation.

### Gaps
- No measured cswave32/pswave32/gewave32 results on any RDNA2 APU found.
- I did not determine which DXIL WaveSize requests vkd3d-proton passes through for RE Engine.

---

## 7. Recent RADV/ACO and vkd3d-proton work (2025–2026) and SteamOS 3.8 Mesa version

### Takeaway
SteamOS 3.8.28 (stable, 25 Sep 2026) reportedly ships Mesa 26.1.2 and kernel 6.18.50; Valve's notes do not state the Mesa version. The headline 2025–26 gains are ray tracing (irrelevant to Wilds on Deck) and descriptor heaps. Descriptor heaps are opt-in in Mesa 26.1, default only from 26.2, and opt-in in vkd3d-proton master, with no published numbers. A Deck-relevant perf-only drirc for 3D storage images now exists.

### Cited Findings
- **[secondary report]** SteamOS 3.8.28 ships Mesa 26.1.2 (up from 25.3.0) and kernel 6.18.50. BornCity cites no primary source. — [BornCity](https://borncity.com/news/steamos-3-8-28-valve-erweitert-handheld-support-und-aktualisiert-firmware/); kernel confirmed by [GamingOnLinux](https://www.gamingonlinux.com/2026/09/steamos-3-8-28-stable-released-with-big-improvements-for-steam-deck-steam-machine-and-more-hardware-support/)
- **[news, Apr 2026]** RADV descriptor heap was merged in Mesa 26.1 but not enabled by default (`RADV_EXPERIMENTAL=heap`). No benchmarks. — [Phoronix](https://www.phoronix.com/news/RADV-Merges-Descriptor-Heap)
- **[news, Jun 2026]** Descriptor heap is exposed by default in Mesa 26.2-devel. No performance numbers; GPU generations not named. — [Phoronix](https://phoronix.com/news/RADV-Descriptor-Heap-Default)
  - Consistent with this, `heap` no longer appears in RADV_EXPERIMENTAL on main: [radv_instance.c](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/radv_instance.c)
- **[news, May 2026]** vkd3d-proton merged descriptor heap support, opt-in via `VKD3D_CONFIG=descriptor_heap`, on master and not in a tagged release. It claims "more predictable performance characteristics," with no numbers. — [Phoronix](https://phoronix.com/news/VKD3D-Proton-Descriptor-Heaps)
  - 3.0.1 (6 May 2026) added present timing and unspecified "optimizations especially for mobile/laptop hardware": [Phoronix](https://www.phoronix.com/news/VKD3D-Proton-3.0.1)
- **[release notes, Nov 2025]** vkd3d-proton 3.0:
  - Texture-copy batching overhaul, `VK_KHR_unified_image_layouts` to avoid barriers, `VK_EXT_zero_initialize_device_memory` to avoid manual clears.
  - Removal of the AMD manual-clear workaround on kernel 6.15.9+.
  - TLOU1 "prefer 2D tiling on 3D images" (requires a Mesa update).
  - Wilds sparse SMEM workarounds.
  - Source: [GamingOnLinux](https://www.gamingonlinux.com/2025/11/vkd3d-proton-3-0-brings-fsr4-support-shader-backend-rewrite-lots-of-bug-fixes-and-performance-upgrades/page=1/)
- **[code]** Mesa now has `01-radv-performance.conf` ("Options in this file must only affect performance, never correctness"). `radv_prefer_2d_swizzle_for_3d_storage` is set for Ghost Recon Breakpoint (fog pass), TLOU1, and Total War ROME (comment: a 3D swizzle "wrecks L2 locality… (+15% FPS)"). — [01-radv-performance.conf](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/01-radv-performance.conf); option list in [radv_drirc_gen.py](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/radv_drirc_gen.py)
- **[older, date not verified]** VRS 2x2 for flat shading on GFX10.3+ is a default RADV optimization and can be disabled with `RADV_DEBUG=novrsflatshading`. — [MR 9515](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/9515); [envvars](https://github.com/chaotic-cx/mesa-mirror/blob/main/docs/envvars.rst)
- **[older, Phoronix headlines; dates/numbers not fetched]** Valve's "dynamic VRS" for Deck power savings is reflected in `RADV_FORCE_VRS_CONFIG_FILE` ("This only affects GFX10.3 APUs"). — [Phoronix: RADV Dynamic VRS Lands](https://www.phoronix.com/news/RADV-Dynamic-VRS-Lands); [envvars](https://github.com/chaotic-cx/mesa-mirror/blob/main/docs/envvars.rst)
- **[measured, older Apr 2021, desktop RDNA2]** Phoronix benchmarked `RADV_FORCE_VRS=2x2` on RX 6700 XT/6800/6800 XT at 4K and reported "little quality loss." I did not retrieve the fps tables. — [Phoronix VRS review](https://www.phoronix.com/review/radeon-radv-vrs)

### Inferences
- **2D swizzle for 3D storage:** this is the most interesting new "free" lever. Wilds' volumetric fog or froxel passes may use 3D storage images read with 2D patterns. A user drirc entry `radv_prefer_2d_swizzle_for_3d_storage` for `MonsterHunterWilds.exe` is a perf-only, Tier S-style experiment. It needs verification that the option exists in 26.1.2. vkd3d-proton 3.0's TLOU1 note implies the Mesa side landed around late 2025, so it is probably present.
- **Descriptor heaps:** these mainly reduce CPU overhead. On the Deck they are not available by default in 26.1.2 and need a newer vkd3d-proton build. Low priority, high uncertainty.

### Gaps
- Mesa 26.1.2 is unconfirmed by Valve.
- No ExecuteIndirect/DGC batching changes relevant to RADV were found for 2025–26.
- No ACO compiler improvement with Deck-measured gains found.
- I could not confirm whether user `~/.drirc` is read inside Proton's pressure-vessel runtime; this needs a bench test.

---

## 8. Clocks, power and memory-clock control

### Takeaway
The GPU peaks at about 1.6 GHz inside an APU budget of about 15–16 W. Memory clock (MCLK) is bonded to FCLK on Van Gogh, and the PMFW allows setting only FCLK manually. Reducing CPU power and traffic most plausibly helps by freeing *power* for GPU clocks, not bandwidth; no contention measurement exists.

### Cited Findings
- **[measured, 2023]** GPU up to 1.6 GHz; APU capped at about 16 W; GPU over 10 W while the CPU drops to 2–3 W when GPU-bound. — [Chips and Cheese](https://chipsandcheese.com/p/van-gogh-amds-steam-deck-apu)
- **[kernel patch, older Apr 2021]** "For vangogh, mclk bonds with fclk… only fclk is allowed to set value manually," so the `pp_dpm_mclk` setter was removed. — [amd-gfx patch](https://yhbt.net/lore/all/BN6PR12MB112431A20309BCCCBC4BD7F8F14E9@BN6PR12MB1124.namprd12.prod.outlook.com/T)
  - Related: GFXCLK/CCLK fine-grain tuning for vangogh, the basis of manual GPU clock control: [commit c98ee89736b8](https://upd.dev/kernel/linux/commit/c98ee89736b8)

### Inferences
- Per CLAUDE.md R7, a tool must not drive FCLK through sysfs on a real Deck outside the bench runner. It is also SMU-level and risky.
- The Tier S equivalents are the TDP limit, CPU frequency cap, fps cap and GPU clock floor, which shift power to the GPU.
- Whether SteamOS lowers FCLK/MCLK dynamically during games is not established.

### Gaps
- No source on runtime FCLK/MCLK behaviour under SteamOS power profiles.
- No measurement of GPU throughput vs CPU memory traffic on the Deck.
- No Deck BIOS memory-timing options documented beyond the UMA frame buffer.

---

## 9. Other "free" or APU-specific knobs

### Takeaway
The real knobs are:
- `RADV_PERFTEST` (wave32 variants, `nogttspill`, `sam`/`nosam`).
- `RADV_FORCE_VRS` / `RADV_FORCE_VRS_CONFIG_FILE`, which trade image quality for pixel-shader cost.
- drirc perf options: 2D swizzle for 3D storage, unified heap, transfer queue.
- `VKD3D_CONFIG` queue options.

`RADV_DEBUG` flags are debug tools that mostly slow things down. `mesa_glthread` is OpenGL-only and irrelevant to D3D12 via vkd3d-proton.

### Cited Findings
- **[doc]** `RADV_FORCE_VRS` takes 2x2, 1x2, 2x1 or 1x1. It applies to "pipelines that don't explicitly use VRS or flat shading" and is "Only for testing purposes." — [envvars](https://github.com/chaotic-cx/mesa-mirror/blob/main/docs/envvars.rst)
- **[code]** The full current `VKD3D_CONFIG` list includes: `single_queue`, `no_staggered_submit`, `small_vram_rebar`, `no_upload_hvv`, `disable_{uav,color,depth}_compression`, `prefer_thin_uav_tiling`, `descriptor_heap`, `log_memory_budget`, `debug_wave64_simulation`, `skip_application_workarounds`, among others. — [config_flag_decl.h](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/include/private/config_flag_decl.h)
- **[code]** Full RADV drirc option list (including `radv_enable_unified_heap_on_apu`, `radv_prefer_2d_swizzle_for_3d_storage`, `radv_enable_transfer_queue` and `radv_force_exclusive_image`): [radv_drirc_gen.py](https://github.com/chaotic-cx/mesa-mirror/blob/main/src/amd/vulkan/radv_drirc_gen.py)

### Inferences
- **Forced VRS:** `RADV_FORCE_VRS=2x2` is the only knob here with plausible large gains on pixel-shader-bound passes. However:
  - It blurs the whole image, including UI and text drawn by non-VRS pipelines.
  - RE Engine does much of its work in compute, which VRS does not touch.
  - It conflicts with the "best image quality" goal; treat it as a last resort.
- **Skipping app workarounds:** `skip_application_workarounds` would drop Wilds' sparse and robustness workarounds and risks GPU faults. Do not use it.

### Gaps
- No Deck or Wilds measurements for any of these knobs.
- `RADV_FORCE_VRS` interaction with FSR and TAA upscaling in Wilds is unknown.

---

## Lever summary

| Lever | Route | Expected gain | Image cost | Risk |
|---|---|---|---|---|
| `VKD3D_CONFIG=single_queue` (or `RADV_QUEUE_DISABLE=compute`) | env var / launch option (Tier S) | Unknown; estimate ±0–5%, could be negative (no measurements found) | None | Low (reversible A/B) |
| `VKD3D_CONFIG=no_staggered_submit` | env var | Unknown for Wilds; claimed it can regress or help (2.14 notes) | None | Low |
| `radv_prefer_2d_swizzle_for_3d_storage` for MonsterHunterWilds.exe | user drirc (`~/.drirc`) or env-equivalent | Claimed +15% in Total War ROME (driver comment); unknown for Wilds; estimate 0–5% if Wilds has 3D storage passes | None (perf-only option) | Low–medium (availability in 26.1.2 and drirc visibility inside pressure-vessel unverified) |
| `RADV_PERFTEST=cswave32` | env var | Unknown; estimate ±0–5% | None | Medium (driver comment: can break games without full subgroups) |
| `RADV_PERFTEST=pswave32` / `gewave32` | env var | Unknown; RADV recommends wave64 for PS | None | Low–medium |
| `RADV_FORCE_VRS=2x2` / `RADV_FORCE_VRS_CONFIG_FILE` | env var | Measured on desktop RDNA2 in 2021 (numbers not retrieved); estimate 0–10% in PS-bound passes only | High (whole-frame and UI softening) | Medium ("testing purposes" flag) |
| `RADV_TEX_ANISO=N` | env var | Estimate 0–3% | Moderate (blurrier oblique surfaces; also forces AF on samplers that had none) | Medium |
| Clean AF clamp (only where maxAniso > N) | Vulkan layer | Estimate 0–3% | Moderate | Medium (Tier I) |
| `radv_enable_unified_heap_on_apu` for Wilds | drirc | Unknown; changes the game's VRAM budget heuristic, not bandwidth | None / maybe better textures | Medium (overcommit or stutter risk) |
| UMA frame buffer 4 GB | BIOS (user action) | Claimed by guides for stability; no controlled fps data | None | Low–medium (takes 3 GB from OS RAM; DeckForge cannot set it under R7) |
| CPU power cap / fps cap / GPU clock floor | OS / Steam QAM (Tier S) | Estimate: meaningful when GPU-bound at 15 W (CPU can drop to 2–3 W, measured 2023) | None | Low |
| MCLK/FCLK control | kernel sysfs / SMU | n/a: MCLK not settable; FCLK only | None | High (R7; firmware-level) |
| Descriptor heaps (Mesa ≥26.2 or `RADV_EXPERIMENTAL=heap` + `VKD3D_CONFIG=descriptor_heap`) | env + newer vkd3d-proton build | No published numbers; mostly CPU overhead | None | Medium–high (opt-in; vkd3d-proton support untagged; GFX10.3 support unverified) |
| `radv_enable_transfer_queue` / `RADV_EXPERIMENTAL=transfer_queue` | drirc / env | Unknown; may offload streaming copies | None | Medium–high ("not yet spec compliant") |
| Force DCC on storage-only images (add COLOR_ATTACHMENT usage) | vkd3d-proton fork (a layer is impractical) | Unknown sign; estimate −3% to +3% | None if correct | High (memory requirements, aliasing, swizzle change, atomics) |
| RGBA16F → R11G11B10F demotion (alpha unused) | vkd3d-proton fork with per-game allowlist (generic layer very hard) | Estimate ≤0.5–2% at 800p behind FSR; measured 10–17% in 2010 desktop high-res games | Low–moderate (banding, blue shift, no negatives) | High (views, copies, aliasing, shader analysis) |
| Remove Wilds heap-robustness quirk / `skip_application_workarounds` | vkd3d-proton fork / env | Estimate small (a few % ALU at most) | None | Very high (GPU page faults or hangs; Valve added it for a reason) |
| `RADV_DEBUG=nodcc/nohiz` etc. | env var | Negative (more bandwidth); correctness-only | n/a | Do not use for performance |

Notes for the main session:
- **Repo constraint:** I followed the hook and wrote no files to the repo or project. Downloaded source copies sit only in the session scratchpad, used for grep.
- **Possible memory note:** SteamOS 3.8.28 (Sep 2026) reportedly ships Mesa 26.1.2 and kernel 6.18.50. Descriptor heaps are not default there.
- **Possible memory note:** vkd3d-proton's Wilds profile sets `SKIP_NULL_SPARSE_TILES` + `NO_UPLOAD_HVV` plus a heap-robustness shader quirk, and does not disable compression.
