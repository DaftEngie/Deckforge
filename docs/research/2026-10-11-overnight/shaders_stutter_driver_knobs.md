# Shader compilation, stutter, and driver/translation-layer tuning knobs on Steam Deck (as of Oct 2026)

Snapshot of primary sources read for these notes, all pinned to commits from the last few weeks: Mesa main (26.3.0-devel, commit bffd919, 2026-10-10, via the chaotic-cx GitHub mirror of upstream; rendered docs at https://docs.mesa3d.org/envvars.html), DXVK master (meson version 3.1.1, commit 71ec7b5, 2026-10-10), vkd3d-proton master (meson version 3.1.0, commit 2230755, 2026-10-06), Proton `proton_11.0` branch (tag proton-11.0-2e, commit bc89621, 2026-10-09), Fossilize (commit 556da9f, 2026-09-24), MangoHud (commit e5d3111, 2026-10-09). The earlier compendium (`deckforge-research.md`) already covers RADV forced/dynamic VRS, GFXReconstruct, RenderDoc, and the basic vkd3d-proton dump/override. This file adds to it and does not repeat it.

## Q1. How does shader-related stutter arise on Deck, how do the caches work (Steam/Fossilize, DXVK, vkd3d-proton, Mesa), and how can a tool trigger, verify, and measure pre-warming?

### Takeaway
On Deck there are four cache layers:
1. Steam's Fossilize pre-caching: pipeline state plus SPIR-V, replayed in the background into the driver cache.
2. The translation-layer caches: DXVK's new internal IR shader cache and vkd3d-proton's DXBC/DXIL→SPIR-V cache.
3. Mesa/RADV's on-disk cache of compiled GPU binaries.
4. The driver's graphics pipeline library (GPL) fast-link path.

Residual stutter comes from pipelines first seen at draw time (typical of UE4/5), from cache-key changes after driver or knob changes, from fast-linked pipelines that run less optimized until the background compile finishes, and from non-shader traversal hitches. A tool can verify a warm cache with `RADV_DEBUG=psocachestats` and `MESA_SHADER_CACHE_SHOW_STATS`. It should measure stutter as per-frame frame-time spikes from MangoHud logs, comparing a cold run against a warm run.

### Cited Findings
**Steam pre-caching and Fossilize**
- Steam's "Allow background processing of Vulkan shaders" setting (Steam Beta, May 2020) works as follows:
  - It processes shaders in the background, including during downloads. If processing isn't finished when you press Play, Steam finishes it before the game loads.
  - It applies to native and Proton titles and is built on the Fossilize library and Vulkan layer.
  - Thread count is set by `unShaderBackgroundProcessingThreads` via `steam://open/console`; the article flags this as at your own risk.
  — [GamingOnLinux, ~May 2020](https://www.gamingonlinux.com/articles/16761/); [Khronos news repost](https://www.khronos.org/news/permalink/steam-beta-adds-vulkan-shader-processing)
- Per-game caches live in `steamapps/shadercache/<appid>/`. A 2020 example (Halo, 976730) contained:
  - `DXVK_state_cache`
  - `fozpipelinesv4/steamapp_pipeline_cache.foz` (~51 MB) and `steam_pipeline_cache.foz` (~285 MB)
  - `nvidiav1/GLCache`
  - `swarm/steam_shader_cache/*.swarc` (~313 MB); its purpose was the author's speculation.
  — [GamingOnLinux 2020](https://www.gamingonlinux.com/articles/16761/). Current folder names (e.g. "fozpipelinesv6") are only in community posts, not verified (see Gaps).
- Fossilize records VkPipeline/VkShaderModule create-infos in hashmaps so they can be replayed. One stated use case is "Serialize state in application once, replay on N devices to build up VkPipelineCache objects without having to run application." — [Fossilize README](https://github.com/ValveSoftware/Fossilize/blob/556da9ff7d7616704dda515756219ab1dab693ec/README.md)
- The Fossilize layer is an implicit layer enabled by `FOSSILIZE=1`. It dumps to `$FOSSILIZE_DUMP_PATH.$hash.$index.foz`, and `FOSSILIZE_DUMP_SIGSEGV` and `FOSSILIZE_DUMP_SYNC` handle crashy drivers. — [Fossilize README](https://github.com/ValveSoftware/Fossilize/blob/556da9ff7d7616704dda515756219ab1dab693ec/README.md)
- The Fossilize command-line tools:
  - `fossilize-replay` "serves as the main 'repro' tool as well as a pipeline driver cache warming tool". `--graphics-pipeline-range` and `--compute-pipeline-range` limit which pipelines compile.
  - `fossilize-merge-db` merges databases.
  - `fossilize-convert-db` converts a database to human-readable form and back.
  - `fossilize-disasm` (SPIR-V asm, GLSL, or AMD ISA via VK_AMD_shader_info) and `fossilize-opt` (runs spirv-opt over all modules) are both marked "hasn't been updated since the change to the new database format".
  — [Fossilize README](https://github.com/ValveSoftware/Fossilize/blob/556da9ff7d7616704dda515756219ab1dab693ec/README.md)
- Valve's Samuel Pitoiset (Nov 2023): "On Steam Deck, shaders are pre-compiled for better performance (less stuttering, less CPU usage, etc)." RADV added the drirc options `radv_override_graphics_shader_version`, `radv_override_compute_shader_version` and `radv_override_ray_tracing_shader_version`, which change the pipeline key so a game's pipelines recompile once when a compiler fix is backported. — [Phoronix, 13 Nov 2023](https://www.phoronix.com/news/RADV-Force-Shader-Re-Comp). These options take values 0–7 ("Override the shader version of graphics pipelines to force re-compilation"). — [radv_drirc_gen.py](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/src/amd/vulkan/radv_drirc_gen.py#L169-L171)
- Mesa's RADV drirc file carries this note: "`executable` shouldn't be used for shader based drirc workarounds because they aren't applied when replaying with Fossilize for precompilation." Shader-affecting per-game options must match on engine or application name instead. — [00-radv-defaults.conf L10-11](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/src/amd/vulkan/00-radv-defaults.conf)

**Mesa disk cache**
- Default implementation and size:
  - Multi-file is the default (`MESA_DISK_CACHE_MULTI_FILE=1`).
  - `MESA_SHADER_CACHE_MAX_SIZE` defaults to 1 GB, possibly one cache per installed architecture.
  - `MESA_SHADER_CACHE_DIR` sets the location; otherwise `$XDG_CACHE_HOME/mesa_shader_cache` or `~/.cache/mesa_shader_cache`.
  — [Mesa envvars.rst L194-309](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/docs/envvars.rst)
- `MESA_DISK_CACHE_SINGLE_FILE=1` (the single-file Fossilize DB, stored in `.../mesa_shader_cache_sf`):
  - Enables loading precompiled read-only DBs via `MESA_DISK_CACHE_READ_ONLY_FOZ_DBS`, or via `..._DYNAMIC_LIST`, a list file that can be modified at runtime.
  - At most 8 read-only DBs can be loaded.
  - It "does not support cache size limits".
  — [Mesa envvars.rst](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/docs/envvars.rst)
- Related cache variables:
  - `MESA_DISK_CACHE_COMBINE_RW_WITH_RO_FOZ=1` reads the read-only Fossilize cache first, then the read-write cache.
  - `MESA_DISK_CACHE_DATABASE=1` (Mesa-DB) supports size limits; eviction weighting doubles monthly.
  - `MESA_SHADER_CACHE_SHOW_STATS=true` prints hit/miss statistics at app exit.
  — [Mesa envvars.rst](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/docs/envvars.rst)
- The single-file cache was built by Valve contractor Timothy Arceri (Mesa 21.1). It uses about one-third of the multi-file layout's disk space and is meant for redistributing caches, e.g. Steam's pre-compiled shaders through `MESA_DISK_CACHE_READ_ONLY_FOZ_DBS`. — [Phoronix, 21 Feb 2021](https://www.phoronix.com/news/Mesa-Single-File-Cache)
- "The Steam Deck uses single-file caches." A RADV pipeline-cache rework was expected to cut that cache by about 60% (Mesa 23.1). — [Steam Deck HQ, 11 Apr 2023](https://steamdeckhq.com/news/mesa-driver-pipeline-and-reduced-shader-cache-size/)

**Graphics pipeline library (GPL)**
- RADV enabled `VK_EXT_graphics_pipeline_library` by default in Mesa 23.1; before that it needed `RADV_PERFTEST=gpl`. — [Phoronix, 10 Apr 2023](https://www.phoronix.com/news/RADV-GPL-Mesa-23.1-Default). GPL is now disabled only by the debug flag `RADV_DEBUG=nogpl`. — [Mesa envvars.rst](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/docs/envvars.rst)
- Steam Deck HQ (2023) stated GPL "does not help DirectX 12 games, because GPL is not included in vkd3d." — [Steam Deck HQ 2023](https://steamdeckhq.com/news/mesa-driver-pipeline-and-reduced-shader-cache-size/). Whether that is still true for vkd3d-proton 3.x is unverified.

**DXVK caches**
- With GPL, Vulkan shaders compile when the game loads its D3D shaders rather than at draw time. Loading screens can see "prolonged periods of very high CPU utilization, especially on weaker CPUs", and you should "wait for shader compilation to finish before starting the game". `DXVK_HUD=compiler` shows compile activity. "Games which only load their D3D shaders at draw time (e.g. most Unreal Engine games) will still exhibit some stutter." — [DXVK README L100-105](https://github.com/doitsujin/dxvk/blob/71ec7b5be6c517db39bcca4d38f38a63f6ddbc56/README.md)
- `dxvk.enableGraphicsPipelineLibrary` values:
  - `Auto` (default): "Enable if supported, and compile optimized pipelines in the background".
  - `True`: "do not compile optimized pipelines".
  - `False`: disable.
  The option is labeled a debugging knob that "will likely result in increased stutter or degraded performance". — [dxvk.conf L456-467](https://github.com/doitsujin/dxvk/blob/71ec7b5be6c517db39bcca4d38f38a63f6ddbc56/dxvk.conf)
- DXVK 2.7 (July 2025) removed the state cache, which had been "largely unused since the introduction of VK_EXT_graphics_pipeline_library in DXVK 2.0". — [DXVK v2.7 release](https://github.com/doitsujin/dxvk/releases/tag/v2.7)
- Current DXVK has a new internal shader cache:
  - It is an "On-disk cache for shaders using the internal IR": two append-only files, a binary blob and a lookup table. — [dxvk_shader_cache.h](https://github.com/doitsujin/dxvk/blob/71ec7b5be6c517db39bcca4d38f38a63f6ddbc56/src/dxvk/dxvk_shader_cache.h)
  - `DXVK_SHADER_CACHE=0` disables it. `DXVK_SHADER_CACHE_PATH` relocates it; the default is `%LOCALAPPDATA%/dxvk` under Wine. — [DXVK README L96-98](https://github.com/doitsujin/dxvk/blob/71ec7b5be6c517db39bcca4d38f38a63f6ddbc56/README.md)
  - It is skipped when `DXVK_SHADER_DUMP_PATH` is set. — [dxvk_device.cpp L41](https://github.com/doitsujin/dxvk/blob/71ec7b5be6c517db39bcca4d38f38a63f6ddbc56/src/dxvk/dxvk_device.cpp#L41)
- `dxvk.numCompilerThreads` defaults to 0, meaning all cores; some threads are reserved for high-priority work. — [dxvk.conf L428-438](https://github.com/doitsujin/dxvk/blob/71ec7b5be6c517db39bcca4d38f38a63f6ddbc56/dxvk.conf)

**vkd3d-proton cache**
- vkd3d-proton "manages its own driver cache" of DXBC/DXIL→SPIR-V conversion. Its behavior is "designed to be close to DXVK state cache":
  - `vkd3d-proton.cache` and `.cache.write` go in the working directory, which is generally the game install folder under Steam.
  - `VKD3D_SHADER_CACHE_PATH` relocates the cache, and `VKD3D_SHADER_CACHE_PATH=0` disables it.
  - `VKD3D_CONFIG=pipeline_library_app_cache` hands caching to the game's `ID3D12PipelineLibrary` instead.
  — [vkd3d-proton README L246-276](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/README.md)

**Unreal Engine PSO precaching (Epic, 4 Feb 2025)**
- UE 5.2 added PSO precaching. It computes a candidate PSO subset at object load time; objects loaded during map loading precache behind the loading screen, and streamed objects wait a few frames or use a default material. — [Epic tech blog](https://www.unrealengine.com/en-US/tech-blog/game-engines-and-shader-stuttering-unreal-engines-solution-to-the-problem)
- Known gaps in precaching:
  - Precached PSOs are discarded and rely on the driver cache, so "this can lead to micro-stutters the first time a material is rendered."
  - As of UE 5.5 it "doesn't handle global graphics shaders".
  - Material changes on visible meshes are a hard case.
  - Keeping PSOs alive "can increase memory usage by more than 1 GB".
  - "Traversal stuttering" (synchronous loads, spawning, stream-in) is a separate, non-PSO hitch source.
  — [Epic tech blog](https://www.unrealengine.com/en-US/tech-blog/game-engines-and-shader-stuttering-unreal-engines-solution-to-the-problem)
- RADV's drirc applies `radv_app_layer=ue5` to engines matching `UnrealEngine5.*` (engine versions 0:8). The UE4/5 Vulkan RHI also gets flush-before-query-copy and flush-before-timestamp workarounds. — [00-radv-defaults.conf L36-45](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/src/amd/vulkan/00-radv-defaults.conf)
- A 2026 Unreal forum thread reports a UE 5.8.2 Vulkan compute PSO precaching crash on RADV/ACO on Steam Deck. I only have the search snippet, not the thread. — [Unreal forums](https://forums.unrealengine.com/t/ue-5-8-2-steam-deck-linux-vulkan-compute-pso-precaching-crashes-radv-aco-store-deref/2771073)

**Verification and measurement tools**
- `RADV_DEBUG=psocachestats` dumps "PSO cache stats (hits/misses) to verify precompilation of shaders". `RADV_DEBUG=pso_history` logs pipeline hash plus shader VA to `/tmp/radv_pso_history.log` ("Useful for debugging GPU hangs with UMR and Fossilize"). — [Mesa envvars.rst RADV section](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/docs/envvars.rst)
- MangoHud's `log_interval` defaults to 0 (log every frame). `benchmark_percentiles` defaults to `97,AVG,1,0.1`. `output_folder` is required for logging. `autostart_log` and `log_duration` script the capture window. — [MangoHud README](https://github.com/flightlessmango/MangoHud/blob/e5d31119b521775de01ec41154c3ddb0a4c8c0cb/README.md)

### Inferences
- **Pre-warming check.** The cleanest automated check is to run a scripted segment twice (cold, then warm) with `RADV_DEBUG=psocachestats` and `DXVK_HUD=compiler`, or with vkd3d-proton logging, while MangoHud logs per-frame times. Frame-time spikes that disappear on the warm run are compile stutter; spikes that persist are traversal, streaming, or CPU stutter.
- **Stutter metric.** Against the 45 fps target (22.2 ms), the shader-stutter metric should count frames over 2× budget (~44 ms) per minute and the worst frame, not just 1%/0.1% lows. Percentile lows blur a few 200 ms hitches into a small number.
- **Shader-affecting knobs invalidate Steam's cache.** Steam's Deck pre-compiled caches are replayed with default driver settings. So any DeckForge knob that changes RADV shader compilation will likely change the pipeline key and miss the downloaded cache, causing first-run compile stutter after DeckForge changes settings. Examples are wave32 PERFTEST flags, `nonggc`, and shader-affecting drirc options; forced VRS is unverified. This is supported by the Fossilize note in the drirc file and by the existence of `radv_override_*_shader_version`. Search results for shader-affecting knobs must therefore be scored on a warm second run, and the first-run cost reported separately.
- **Single-file cache size.** Single-file caches have no size limit, so on Deck cache eviction is unlikely to cause stutter. Multi-file cache eviction at 1 GB only matters if a user or tool switches cache modes.
- **Compile threads vs. game threads.** With 4 cores and 8 threads, DXVK's default of all-cores compiler threads competes with game threads during in-gameplay compilation. Capping `dxvk.numCompilerThreads` is a plausible but untested lever for hitch severity, trading against longer time to optimized pipelines.
- **Triggering pre-warm.** DeckForge can most reliably trigger pre-warming by asking the user to let Steam's shader processing finish (UI), or by doing a scripted warm-up run of the game. Running `fossilize-replay` against Steam's .foz manually is possible in principle. But it must reproduce Steam's exact environment and paths, and it touches the real Steam install, which is forbidden for dev sessions under DeckForge rule R7.

### Gaps
- I found no primary source for the exact environment variables the current Steam client sets for Proton games on Deck (e.g. whether it sets `MESA_SHADER_CACHE_DIR`, `MESA_DISK_CACHE_SINGLE_FILE`, `..._READ_ONLY_FOZ_DBS_DYNAMIC_LIST`, `VKD3D_SHADER_CACHE_PATH` or `DXVK_SHADER_CACHE_PATH` to `steamapps/shadercache/<appid>`). The Proton 11 launcher script itself sets none of these, so the Steam client must. Checking `/proc/<pid>/environ` of a running game on a real Deck would answer it (bench-phase task).
- Current shadercache subfolder names and versions (fozpipelinesv6, fozmediav1, mesa_shader_cache_sf, replay caches) are unverified. Only the 2020 v4 layout is sourced.
- I found no documented Steam command, URL or CLI to trigger shader processing for a single appid.
- When DXVK's new internal IR shader cache shipped (2.7 vs 3.x) and whether Steam relocates it into shadercache are unverified.
- Whether vkd3d-proton 3.x now uses GPL on RADV is unconfirmed; the "GPL not in vkd3d" claim is from 2023.
- I have no measured data on how much stutter remains on Deck with full Steam pre-caching for specific UE5 titles.

## Q2. What "shader optimization" is realistically possible without game source code?

### Takeaway
Replacing shaders by hash is officially possible only in vkd3d-proton (D3D12), and only as a developer-debug feature. DXVK (D3D9/10/11) has dump but no override. A Vulkan layer or GFXReconstruct replay is the general path. Generic SPIR-V optimization (spirv-opt) is unlikely to beat RADV's own NIR and ACO pipeline. Real gains need semantic simplification (lower precision, fewer samples, cheaper math), which then has to be verified per game version. Maintenance cost is dominated by hash churn across game patches and translation-layer updates.

### Cited Findings
**vkd3d-proton dump and override**
- `VKD3D_SHADER_DUMP_PATH` dumps `$hash.{spv,dxbc,dxil}`. `VKD3D_SHADER_OVERRIDE`: "If application is creating a pipeline with `$hash` and `$VKD3D_SHADER_OVERRIDE/$hash.spv` exists, that SPIR-V file will be used instead." — [vkd3d-proton README L287-297](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/README.md)
- These sit under "Advanced shader debugging", which says "These features are only meant to be used by vkd3d-proton developers." — [vkd3d-proton README](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/README.md)
- The dump directory should be cleared first, because "existing files are not overwritten". — [vkd3d-proton README](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/README.md)
- `VKD3D_AUTO_CAPTURE_SHADER=<hash>` (with the RenderDoc layer) captures automatically when a given shader is first used. `VKD3D_AUTO_CAPTURE_COUNTS` selects which submissions to capture. — [vkd3d-proton README](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/README.md)

**DXVK**
- DXVK has no override. Its source reads only these `DXVK_*` env vars: CAPTURE_FRAMES, CONFIG, CONFIG_FILE, DEBUG, ENABLE_NVAPI, FILTER_DEVICE_NAME/UUID, FORCE_WINDOWED, HDR, HUD, LOG_LEVEL, LOG_PATH, NO_VR, SHADER_CACHE, SHADER_CACHE_PATH, SHADER_DUMP_PATH, WSI_DRIVER. There is a dump path but no read or replace path. — [DXVK source, grep of getEnvVar at 71ec7b5](https://github.com/doitsujin/dxvk/tree/71ec7b5be6c517db39bcca4d38f38a63f6ddbc56/src)
- vkd3d-proton 3.0 (Nov 2025) replaced its DXBC backend: "DXVK and vkd3d-proton now share the same DXBC frontend", and dxil-spirv gained DXBC support. — [GamingOnLinux, 17 Nov 2025](https://www.gamingonlinux.com/2025/11/vkd3d-proton-3-0-brings-fsr4-support-shader-backend-rewrite-lots-of-bug-fixes-and-performance-upgrades/page=1/)
- The compendium already records that vkd3d-proton 3.0.1 moved some workarounds from shader hashes to entry-point names because hashes churn with patches. — [compendium §4, citing GamingOnLinux May 2026](https://www.gamingonlinux.com/2026/05/vkd3d-proton-3-0-1-brings-many-linux-gaming-enhancements-for-direct3d-12-via-vulkan/)

**Inspecting compiled shaders on RADV**
- RADV can dump compiled code per stage without any capture tool: `RADV_DEBUG=shaders,shaderstats,asm,ir,nir,spirv` plus per-stage filters `vs,tcs,tes,gs,ps,cs,task,mesh`. `preoptir` dumps backend IR before optimization. — [Mesa envvars.rst RADV_DEBUG](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/docs/envvars.rst)
- `RADV_SPM_COUNTERS_CONFIG` (new) lets you define custom SPM hardware counter groups collected in RGP captures (`MESA_VK_TRACE=rgp`), up to 8 groups and 48 items. — [Mesa envvars.rst](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/docs/envvars.rst)

**ACO and LLVM**
- ACO is the only compiler on production RADV: `RADV_DEBUG=llvm` "enable LLVM compiler backend. Only available in debug builds." — [Mesa envvars.rst](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/docs/envvars.rst)
- Every `ACO_DEBUG` option is validation or debug: validateir, novalidate, validatera, force-waitcnt, force-waitdeps, novn, noopt, nosched, nosched-ilp, nosched-vopd, perfinfo, liveinfo. None is a performance-improving option. — [Mesa envvars.rst ACO_DEBUG](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/docs/envvars.rst)

**Fossilize and driver-side replacement**
- Fossilize databases already hold every pipeline's SPIR-V plus state, and `fossilize-convert-db` round-trips them to a human-readable form. `fossilize-opt` (spirv-opt over a capture) exists but is stale for the new DB format. — [Fossilize README](https://github.com/ValveSoftware/Fossilize/blob/556da9ff7d7616704dda515756219ab1dab693ec/README.md)
- Valve/RADV developers (March 2026) are discussing per-game performance tuning and "drivers doing more shader replacement and tuning", as Windows vendors do. These are "just ideas being tossed around" (Mesa issue 15028). — [Phoronix, 10 Mar 2026](https://phoronix.com/news/Mesa-RADV-More-Per-Game-Tuning)

### Inferences
- **Offline pipeline for D3D12 games.** Use `VKD3D_SHADER_DUMP_PATH` (or Steam's .foz) to get SPIR-V, edit or optimize it, check it with `RADV_DEBUG=shaderstats` (VGPRs, SGPRs, instruction count, spills) and GFXReconstruct replay timing, then deploy with `VKD3D_SHADER_OVERRIDE`. This works for D3D12 only. D3D11 games would need a DeckForge Vulkan layer hooking `vkCreateShaderModule` or pipeline creation and keyed on DXVK's SPIR-V hashes. DXVK offers no hook.
- **Overrides are tied to the vkd3d-proton version.** An override replaces the translator's SPIR-V output, which embeds that version's binding and resource interface. A Proton update that changes dxil-spirv codegen (as 3.0 did for DXBC) could make an old override silently wrong or invalid even if the input hash still matches. Each override should be stored with (game build, Proton/vkd3d-proton version, Mesa version) and re-validated whenever any of them changes.
- **spirv-opt alone won't help.** Generic spirv-opt `-O` passes (DCE, constant folding, inlining) largely duplicate NIR and ACO optimizations, so expect little gain from them alone. This is my reasoning, not a measured result. Wins would come from semantic changes the compiler can't prove safe: precision reduction to fp16 (RDNA2 has packed fp16), sample-count reduction in blurs, SSAO and volumetrics, loop trimming. These are exactly the changes that need image and temporal validation.
- **Override files change compilation.** Override files change shader compilation, so they also miss Steam's pre-compiled cache (Q1). The first run after installing an override will stutter.
- **Driver-side replacement may arrive upstream.** If RADV gains driver-side shader replacement (still only discussed), the upstream path for DeckForge's validated rewrites could become drirc or app_layer entries rather than user-side overrides.

### Gaps
- I found no published measurements of frame-time gains from hand- or AI-replaced shaders on Deck or RADV for any commercial game, and no measurements of spirv-opt gains on RADV.
- vkd3d-proton's exact hash algorithm and whether it covers DXIL bytecode only or also the root signature are unverified from source. I didn't read `vkd3d_shader` hashing code.
- The legal and EULA posture of distributing replaced shaders is unaddressed (also open in the compendium).

## Q3. Which Mesa RADV / ACO / AMD driver knobs matter for performance or quality on Van Gogh (GFX10.3), and which are safe vs debug-only?

### Takeaway
On current Mesa, most historically "perftest" features are now defaults on GFX10.3: GPL, NGG culling, and RT pipelines. LLVM exists only in debug builds. What remains in `RADV_PERFTEST` is mostly wave-size and memory-placement experiments of uncertain value on an APU. The real user-facing levers on Deck are:
- `RADV_FORCE_VRS` / `RADV_FORCE_VRS_CONFIG_FILE` (the config file now documented as GFX10.3-APU-only).
- `RADV_TEX_ANISO` (quality).
- A handful of drirc options settable as environment variables (e.g. `radv_enable_unified_heap_on_apu`).

Everything in `RADV_DEBUG` and `ACO_DEBUG` is diagnostic and should never be a shipped tuning knob.

### Cited Findings
All findings below are from [Mesa main envvars.rst, 2026-10-10](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/docs/envvars.rst), unless another source is given.

**Variable rate shading (VRS)**
- `RADV_FORCE_VRS` forces per-pipeline vertex VRS rates on GFX10.3+ (2x2, 1x2, 2x1, 1x1), "only forced for pipelines that don't explicitly use VRS or flat shading. ... Only for testing purposes."
- `RADV_FORCE_VRS_CONFIG_FILE` does the same from a file, supersedes the env var, and "only affects GFX10.3 APUs". In practice that means Van Gogh/Deck-class chips.
- `RADV_DEBUG=novrsflatshading` disables VRS for flat shading on GFX10.3+.

**Current `RADV_PERFTEST` list (GFX10.3-relevant entries marked)**
- `cswave32`, `gewave32`, `pswave32`: wave32 for compute, geometry, or pixel stages (GFX10+). Relevant.
- `dccmsaa`: DCC on MSAA images.
- `dmashaders`: upload shaders to invisible VRAM, "for non-resizable BAR systems". Not relevant to the APU.
- `localbos`
- `nggc`: NGG culling, **GFX11+ only**.
- `nircache`: cache per-stage NIR for graphics pipelines.
- `nogttspill`
- `nosam`: disable optimizations active when all VRAM is CPU-visible.
- `sam`: move more driver-internal objects to VRAM.
- `rtcps`, `rtwave64`: ray tracing.
- `lowlatencydec`, `lowlatencyenc`: video.
- NGG culling is default-on for GFX10/10.3: the only control there is `RADV_DEBUG=nonggc`, "disable NGG culling for GFX10 and GFX10.3".
- An older Mesa doc listed `nggc` as opt-in for GFX10.1 and `gpl` and `rt` as experimental perftests. — [older envvars copy (NeroReflex Mesa fork)](https://gitlab.neroreflex.duckdns.org/NeroReflex/mesa/src/commit/a327ff90d260b0ab9b7dd461461e0e932e828362/docs/envvars.rst). Those flags are gone from the current list.

**`RADV_EXPERIMENTAL` (separate from PERFTEST)**
- Entries: `transfer_queue` ("experimental transfer queue support (GFX9+, not yet spec compliant)"), `emulate_rt`, `hic` (host image copy, GFX10), `msrtss`, `sparse`, `video_decode`, `video_encode`, `bfloat16`, `elf`.
- Mesa 26.1 also gated `VK_EXT_descriptor_heap` behind `RADV_EXPERIMENTAL=heap`. — [Phoronix, Mesa 26.1 released 6 May 2026](https://phoronix.com/news/mesa-26.1-released)
- Conflict: a Phoronix headline says "Mesa 26.0 RADV Lands Dedicated Transfer-Only Queue Using SDMA". — [Phoronix](https://www.phoronix.com/news/Mesa-26.0-RADV-Transfer-SDMA). Current docs still list `transfer_queue` as experimental, and a `radv_enable_transfer_queue` drirc option exists. — [radv_drirc_gen.py](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/src/amd/vulkan/radv_drirc_gen.py). Which is right for GFX10.3 is unresolved.

**`RADV_DEBUG` (all debug or diagnostic)**
- Performance-negative switches useful only for A/B diagnosis: `nodcc`, `nodisplaydcc`, `nohiz`, `nofastclears`, `nobinning`, `nofmask`, `nongg`, `nonggc`, `nogpl`, `noeso`, `nocache` (disables the shader cache, so stutter), `syncshaders`, `fullsync`.
- Diagnostics: `hang`, `info`, `startup`, `psocachestats`, `pso_history`, `shaders`, `shaderstats`, `asm`, `spirv`, `nir`, `ir`.
- `zerovram` is deprecated.
- `nort` skips executing ray tracing while still advertising RT extensions, so RT games won't crash but won't render RT either.
- `nocachecompat` disables "changes to code generation which increases shader cache compatibility between devices".

**Other variables**
- `RADV_TEX_ANISO` forces anisotropic filtering up to 16.
- `RADV_PROFILE_PSTATE` (standard, min_sclk, min_mclk, peak; default peak) applies only during thread tracing or profiling-lock perf queries.
- `MESA_VK_TRACE=rgp` (with `MESA_VK_TRACE_FRAME` / `_TRIGGER`) captures RGP traces to `/tmp`.
- `RADV_QUEUE_DISABLE=gfx|compute|vdec|venc|transfer|sparse` is "for testing purposes".

**Drirc options**
- Exposed RADV drirc options include: `radv_enable_unified_heap_on_apu` ("Enable an unified heap with DEVICE_LOCAL on integrated GPUs"), `radv_disable_ngg_gs` ("Disable NGG GS on GFX10/GFX10.3"), `radv_clear_lds` ("Might decrease performance"), `radv_disable_dcc`, `radv_tex_non_uniform`, `radv_rt_wave64`, `radv_disable_aniso_single_level`, `radv_disable_trunc_coord`, `radv_override_*_shader_version`, `override_vram_size`, `radv_app_layer`, and others. — [radv_drirc_gen.py](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/src/amd/vulkan/radv_drirc_gen.py)
- Mesa defaults apply `radv_disable_aniso_single_level=true` and `radv_disable_trunc_coord=true` to every game whose engine name matches `vkd3d` or `DXVK`. — [00-radv-defaults.conf L14-26](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/src/amd/vulkan/00-radv-defaults.conf)

**`AMD_DEBUG`**
- `AMD_DEBUG` is the RadeonSI (OpenGL) and common-AMD variable. The current docs list RADV-specific debugging under `RADV_DEBUG` and `ACO_DEBUG`. — [Mesa envvars.rst, section ordering RADV → RadeonSI](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/docs/envvars.rst)

### Inferences
**Safe for DeckForge's search space (Tier S, launch-option environment only, reversible):**
- `RADV_FORCE_VRS` / `RADV_FORCE_VRS_CONFIG_FILE`. These are Valve-built for Deck and documented as testing-only, so treat them as "supported but at your own risk" and validate image quality.
- `RADV_TEX_ANISO` (a quality lever with a bandwidth cost).

**Experimental, A/B only, never a default:**
- `RADV_PERFTEST=pswave32,cswave32,gewave32`. Wave size trades occupancy against per-wave efficiency per shader. No Deck numbers were found, and the flags change shader compilation, so they miss Steam's pre-compiled cache.
- `sam` and `nosam`. On an APU all VRAM is likely CPU-visible already, so "SAM" optimizations are probably already active and `sam` may do little. Unverified.
- `nircache` (compile-time only).
- `RADV_EXPERIMENTAL=transfer_queue` ("not yet spec compliant").
- `radv_enable_unified_heap_on_apu` (possibly interesting for UMA frame-buffer-limited games, which ties into compendium experiment E4; untested).

**Never ship:** everything in `RADV_DEBUG` and `ACO_DEBUG` (diagnostic, often performance-negative or stutter-inducing, e.g. `nocache`). `RADV_DEBUG=psocachestats` is acceptable only as a measurement-time probe.

**Not useful on Deck:** ray tracing knobs. The vkd3d-proton evidence in Q4 shows Valve itself disables default RT on Deck for some titles.

### Gaps
- I found no Deck benchmarks for wave32 flags, `sam`, or `radv_enable_unified_heap_on_apu`.
- I don't know which Mesa version the current stable SteamOS (3.7/3.8) ships, so some flags above may not exist yet on users' Decks. The tool should detect the Mesa version (e.g. from `vulkaninfo` driverInfo) before offering a knob.
- Whether `RADV_FORCE_VRS` and the config file change pipeline cache keys (cache invalidation) wasn't verified in source.
- `AMD_DEBUG` options weren't extracted. They are not relevant to Vulkan/RADV on Deck beyond shared debugging.

## Q4. Which dxvk.conf options and VKD3D_CONFIG flags have real performance or quality impact, and how do they behave on AMD/RADV?

### Takeaway
DXVK exposes a compact set of real levers:
- Sampler anisotropy and LOD bias, including clamping negative bias: quality versus bandwidth.
- Tessellation factor cap.
- Relaxed UAV barriers.
- Frame latency, frame rate and present controls.
- Compiler thread count.

All are settable per game through the `DXVK_CONFIG` env var with no file writes. vkd3d-proton's documented `VKD3D_CONFIG` flags are mostly debug or NVIDIA-specific. The flags that matter for performance (`no_staggered_submit`, `small_vram_rebar`, `retain_psos`, etc.) are undocumented and used by Valve's per-app profiles. vkd3d-proton also has Deck-specific logic that turns off default ray tracing in some titles.

### Cited Findings
**DXVK (all from [dxvk.conf @71ec7b5](https://github.com/doitsujin/dxvk/blob/71ec7b5be6c517db39bcca4d38f38a63f6ddbc56/dxvk.conf), unless another source is given)**

Quality levers:
- `d3d11.samplerAnisotropy` / `d3d9.samplerAnisotropy` (0–16): forces anisotropic filtering on all samplers. "Forcing anisotropy is known to break passes that rely on bilinear filtering ... Please do not report bugs with this option enabled."
- `d3d11.samplerLodBias` / `d3d9.samplerLodBias` (−2.0 to 1.0): added to the app's bias. "Positive values will reduce texture detail, while negative values may increase sharpness at the cost of shimmer."
- `d3d11.clampNegativeLodBias` / `d3d9.clampNegativeLodBias`: clamps negative bias to 0 after `samplerLodBias`. "May help with games that use a high negative LOD bias by default."
- `d3d11.forceSampleRateShading`: per-sample shading under MSAA, at "a significant performance cost".
- `d3d11.disableMsaa`: forces sample count 1 with resolve fixups.

Performance levers:
- `d3d11.maxTessFactor` (8–64): "can be used to improve performance in titles which overuse tessellation."
- `d3d11.relaxedBarriers`: ignores write-after-write UAV hazards in compute and all UAV hazards in graphics. "May improve performance ... but may also introduce rendering issues". `d3d11.relaxedGraphicsBarriers` is the graphics-only variant. Both say "don't report bugs".
- `dxvk.useRawSsbo`: on by default on hardware with 4-byte SSBO alignment "(e.g. AMD)", so it is already active on Deck.
- `d3d9.floatEmulation`: True (faster, less accurate), Strict (slower, correct) or Auto.
- `d3d9.deviceLocalConstantBuffers`: `Auto` enables streaming "only on discrete GPUs", so it is off on Deck by default.
- `dxvk.tilerMode`: "only intended to be changed for performance testing and debugging".
- `dxvk.maxMemoryBudget`: "only intended to be a debug option, expect severe performance degradation".
- `dxgi.maxDeviceMemory` / `dxgi.maxSharedMemory`: override reported memory to fix texture streaming in games that mis-handle VRAM size ("not a hard cap").

Latency and pacing levers:
- `dxgi.maxFrameLatency` / `d3d9.maxFrameLatency` (0–16): enforce a stricter maximum frame latency.
- `dxgi.maxFrameRate` / `d3d9.maxFrameRate` / `dxvk.maxFrameRate`: "DO NOT USE THIS IF EXTERNAL LIMITERS ARE AVAILABLE. Limiters from Mangohud or Gamescope WILL provide a significantly better experience."
- `dxvk.latencySleep`: `True` enables built-in latency reduction, which "may reduce performance or lead to less consistent frame pacing" and has no effect with external limiters such as MangoHud.
- `dxgi.syncInterval` / `d3d9.presentInterval`: override vsync.
- `dxvk.tearFree`: mailbox vs relaxed FIFO ("Please do not report issues").
- `dxvk.enablePresentTiming`: improves pacing when emulating non-native modes, "Only works on VRR setups, not recommended otherwise."

Per-game configuration:
- `DXVK_CONFIG="opt = val; opt2 = val2"` sets any dxvk.conf option from the environment. `DXVK_CONFIG_FILE` points to a config file. — [DXVK README L94-95](https://github.com/doitsujin/dxvk/blob/71ec7b5be6c517db39bcca4d38f38a63f6ddbc56/README.md)
- DXVK 2.7 enabled `VK_EXT_descriptor_buffer` by default on newer GPUs. It "significantly reduces CPU overhead", and "RADV is unaffected" by the regressions that kept it off on older GPUs with AMDVLK or Windows drivers. — [DXVK v2.7 release](https://github.com/doitsujin/dxvk/releases/tag/v2.7). Current dxvk.conf also has `dxvk.enableDescriptorHeap` (Auto = "known-good drivers"). — [dxvk.conf](https://github.com/doitsujin/dxvk/blob/71ec7b5be6c517db39bcca4d38f38a63f6ddbc56/dxvk.conf)

**vkd3d-proton**

Documented `VKD3D_CONFIG` flags — [vkd3d-proton README L196-210](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/README.md):
- `vk_debug`, `skip_application_workarounds` (debugging), `nodxr`, `dxr`, `dxr12`.
- `force_static_cbv`: "Unsafe speed hack on NVIDIA".
- `single_queue`: "Do not use asynchronous compute or transfer queues".
- `no_upload_hvv`: blocks host-visible VRAM (ReBAR) for the UPLOAD heap. "May free up vital VRAM ... at cost of lower GPU performance".
- `force_host_cached` (accelerates captures), `no_invariant_position`.

Other knobs:
- `VKD3D_SWAPCHAIN_PRESENT_MODE` (IMMEDIATE, MAILBOX, FIFO, FIFO_RELAXED, FIFO_LATEST_READY) and the `VKD3D_FRAME_RATE` limiter. — [vkd3d-proton README](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/README.md)
- vkd3d-proton 3.0 removed `DXVK_FRAME_RATE` handling "to align with DXVK's removal". `VKD3D_FRAME_RATE` remains. — [GamingOnLinux, Nov 2025](https://www.gamingonlinux.com/2025/11/vkd3d-proton-3-0-brings-fsr4-support-shader-backend-rewrite-lots-of-bug-fixes-and-performance-upgrades/page=1/)

The full flag list in source has about 65 flags. Beyond the documented ones it includes: `no_staggered_submit`, `small_vram_rebar`, `retain_psos`, `global_pipeline_cache`, `shader_cache_sync`, `pipeline_library_app_cache`, `force_raw_va_cbv`, `disable_uav_compression`, `disable_depth_compression`, `disable_color_compression`, `disable_simultaneous_uav_compression`, `prefer_thin_uav_tiling`, `force_dynamic_msaa`, `one_time_submit`, `no_gpu_upload_heap`, `descriptor_heap`, `recycle_command_pools`, `memory_allocator_skip_clear`, `defer_resource_destruction`, `skip_driver_workarounds`, `enable_experimental_features`. — [config_flag_decl.h](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/include/private/config_flag_decl.h)

How Valve's built-in per-app table (110 string-match entries) uses the performance flags — [device_workarounds.c](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/libs/vkd3d/device_workarounds.c):

| Flag | Entries using it | Example |
|---|---|---|
| `no_staggered_submit` | 9 | `GoWEDay-Steam.exe` |
| `no_upload_hvv` | 6 | |
| `small_vram_rebar` | 5 | `Paranoid-Win64-Shipping.exe` (with `no_staggered_submit`) |
| `force_raw_va_cbv` | 4 | |
| `disable_uav_compression` | 3 | |
| `retain_psos` | 3 | |
| `force_dynamic_msaa` | 2 | |
| `one_time_submit` | 2 | |
| `disable_color_compression` | 1 | |
| `prefer_thin_uav_tiling` | 1 | |

- `no_staggered_submit` makes `d3d12_command_queue_needs_cpu_waits()` return false, i.e. it disables a CPU-wait submission heuristic. — [command.c L24342](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/libs/vkd3d/command.c#L24342)
- Deck-specific behavior:
  - vkd3d-proton detects Deck as RADV with AMD device ID 0x163f or 0x1435. — [device_workarounds.c L1000-1006](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/libs/vkd3d/device_workarounds.c#L1000-L1006)
  - It applies `NO_DEFAULT_DXR_ON_DECK_AND_FRAME` "For games which automatically enable RT even on Deck or Frame, leading to very poor performance by default". Examples:
    - Hellblade (RT on by default "particularly jarring on Deck")
    - PARANOID
    - Tracing Decay
    - Persona 3 Reload ("does not run acceptably for a verified title")
    — [device_workarounds.c L97-125, L1024-1027](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/libs/vkd3d/device_workarounds.c)

### Inferences
**DXVK levers to put in DeckForge's Tier S search space (D3D9/10/11):**
- `d3d11.samplerLodBias` with positive values for bandwidth-bound games. The Deck's ~88 GB/s shared memory makes this a real lever.
- `clampNegativeLodBias`, useful when games apply a negative bias tuned for high resolution or upscaling.
- `samplerAnisotropy` (quality up, at a bandwidth cost).
- `maxTessFactor`.
- `numCompilerThreads`.
- `relaxedGraphicsBarriers` only behind image-quality validation, since it can cause rendering errors.
- Apply them through `DXVK_CONFIG` in launch options rather than writing dxvk.conf into game folders. That respects R10 (no direct writes to user files outside deckforge.safety) and is trivially reversible.

**Avoid as DeckForge defaults:**
- DXVK's own frame limiter (DXVK says use gamescope or MangoHud).
- `dxvk.enablePresentTiming`. It is VRR-only, and as far as I know the Deck's internal panel has no VRR; that is my assumption, not verified.
- `enableGraphicsPipelineLibrary` overrides.
- `maxMemoryBudget`, `tilerMode`.

**vkd3d-proton (D3D12):** the only documented flag plausibly useful on Deck is `single_queue`, as an A/B test for async-compute problems. The undocumented flags are Valve's per-game fixes. Using them outside their intended titles is unsupported and may break rendering. DeckForge should at most record which Valve profile is active, not reimplement it.

**Ray tracing auto-enabled on Deck:** Valve's Deck-specific DXR suppression shows that "game auto-enables RT on Deck" is a recognized failure mode. DeckForge's settings search should check in-game RT defaults first (Tier S), and `VKD3D_CONFIG=nodxr` is a blunt, documented fallback.

### Gaps
- I found no Deck benchmarks for any dxvk.conf or VKD3D_CONFIG option.
- The precise semantics of `small_vram_rebar`, `retain_psos`, `global_pipeline_cache` and `shader_cache_sync` weren't read in source beyond the flag names and usage counts.
- Whether `no_upload_hvv` has any effect on Deck's APU memory model is unverified.

## Q5. How does Valve apply per-game workarounds (Proton, Mesa drirc, DXVK, vkd3d-proton), and can a userspace tool add per-game driver configs via environment variables or launch options?

### Takeaway
Valve's per-game fixes live in four places, each keyed differently:
- Proton's `default_compat_config()`, keyed by Steam appid.
- Mesa's `00-radv-defaults.conf` drirc, keyed by engine name, application name or executable.
- DXVK's built-in profiles, keyed by executable.
- vkd3d-proton's `application_override` table, keyed by executable.

Every layer has a userspace override that needs no root:
- Proton: `PROTON_*` environment variables.
- Mesa: driconf options can be set as environment variables of the same name, or in `~/.drirc`.
- DXVK: `DXVK_CONFIG` / `DXVK_CONFIG_FILE`.
- vkd3d-proton: `VKD3D_CONFIG`.

All of these can be passed per game via Steam launch options.

### Cited Findings
**Proton**
- The Proton 11 launcher (`proton-11.0-2e`, 2026-10-09) builds a compat-config set in `default_compat_config()` from `SteamAppId` / `STEAM_COMPAT_APP_ID` lists. Examples include `noxalia`, `nohardwarescheduling` (No Man's Sky, Portal with RTX) and `hidevggpu` (Serious Sam 4, Ara: History Untold), which sets `WINE_HIDE_VANGOGH_GPU=1`. — [Proton `proton` script L1288-1350, L1910-1911](https://github.com/ValveSoftware/Proton/blob/bc896217ffcd67f892f952b010f898fe7bd0f0a1/proton)
- Users toggle the same flags through environment variables mapped by `check_environment`, e.g. `PROTON_HIDE_VANGOGH_GPU` → `hidevggpu`, `PROTON_HEAP_DELAY_FREE`, `PROTON_FORCE_LARGE_ADDRESS_AWARE`. — [proton L1767-1775](https://github.com/ValveSoftware/Proton/blob/bc896217ffcd67f892f952b010f898fe7bd0f0a1/proton)
- A `user_settings.py` in the Proton directory can inject environment variables (used for debug logging). — [proton L42-43, L1727-1739](https://github.com/ValveSoftware/Proton/blob/bc896217ffcd67f892f952b010f898fe7bd0f0a1/proton)
- Proton defaults `DXVK_LOG_LEVEL=none`, `VKD3D_DEBUG=none` and `WINEDEBUG=-all` "for performance". — [proton L1752-1756](https://github.com/ValveSoftware/Proton/blob/bc896217ffcd67f892f952b010f898fe7bd0f0a1/proton)
- The Proton launcher does not itself set the shader cache path variables; grep for `SHADER_CACHE`, `MESA_SHADER` and `STATE_CACHE` found none. — [proton script](https://github.com/ValveSoftware/Proton/blob/bc896217ffcd67f892f952b010f898fe7bd0f0a1/proton)

**Mesa drirc**
- `00-radv-defaults.conf` (199 lines) matches by `engine_name_match` (vkd3d, DXVK, `^UnrealEngine`, `UnrealEngine5.*` with engine_versions, Quantic Dream Engine, DXVK_NvRemix), by `application_name_match`, or by `executable`. It uses 31 distinct options:
  - `radv_app_layer` (8 entries: ue5, quanticdream, rage2, metroexodus, strange_brigade, no_mans_sky, gfxbench5)
  - `radv_disable_aniso_single_level` (4)
  - `radv_disable_dcc` (3)
  - `radv_disable_trunc_coord`
  - `radv_ssbo_non_uniform`
  - `radv_emulate_rt`
  - and others
  — [00-radv-defaults.conf](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/src/amd/vulkan/00-radv-defaults.conf)
- Mesa reads driconf from `$DRIRC_CONFIGDIR` or `$datadir/drirc.d`, then `$SYSCONFDIR/drirc`, then `$HOME/.drirc`. — [xmlconfig.c L1504-1522](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/src/util/xmlconfig.c#L1504-L1522)
- Any driconf option's default is overridden by an environment variable with the option's exact name, via `os_get_option(name)`. Invalid values print "illegal environment value ... Ignoring." — [xmlconfig.c L430-448](https://github.com/chaotic-cx/mesa-mirror/blob/bffd91947efc1932da99aca69fc540d6d4201b0c/src/util/xmlconfig.c#L430-L448)
- Drirc has "mostly been used for correctness workarounds". RADV developers hope to add per-game performance tuning; DriConf would need extending for per-GPU-generation options. Still at the idea stage as of March 2026 (Mesa issue 15028). — [Phoronix, 10 Mar 2026](https://phoronix.com/news/Mesa-RADV-More-Per-Game-Tuning)
- Earlier per-game work: a draft MR adding "new FORCE_VRS options for more per-game tuning". — [Mesa MR 16471](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/16471) (title only; not read).

**DXVK**
- DXVK's built-in app profiles live in `src/util/config/config.cpp`, with 263 profile entries. Option frequency:
  - `d3d9.maxFrameRate`: 40
  - `d3d11.cachedDynamicResources`: 23
  - `d3d9.floatEmulation`: 17
  - `dxgi.syncInterval`: 5
  - `dxgi.maxFrameLatency`: 3
  - `d3d11.relaxedBarriers`: 3 (e.g. "Resident Evil 2/3: Ignore WaW hazards", Devil May Cry 5)
  - Never used by a profile: `samplerLodBias`, `maxTessFactor`, `enableGraphicsPipelineLibrary`.
  — [config.cpp](https://github.com/doitsujin/dxvk/blob/71ec7b5be6c517db39bcca4d38f38a63f6ddbc56/src/util/config/config.cpp)
- Users override profiles via `DXVK_CONFIG` or `DXVK_CONFIG_FILE`. — [DXVK README](https://github.com/doitsujin/dxvk/blob/71ec7b5be6c517db39bcca4d38f38a63f6ddbc56/README.md)

**vkd3d-proton**
- vkd3d-proton's `application_override[]` table matches executable names, and `VKD3D_CONFIG=skip_application_workarounds` disables it for debugging. — [device_workarounds.c L53](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/libs/vkd3d/device_workarounds.c#L53); [README](https://github.com/HansKristian-Work/vkd3d-proton/blob/2230755878b01993b4b82d0ac0c0624f3ab4d333/README.md)

### Inferences
- **One mechanism covers every layer.** Since all four layers accept environment variables, DeckForge can express every per-game driver or translation-layer setting as a Steam launch-option string (`VAR=value ... %command%`), e.g.:
  - `RADV_*`
  - `radv_<drirc option>` / `vk_<drirc option>`
  - `DXVK_CONFIG`
  - `VKD3D_CONFIG`
  - `PROTON_*`
  - `MESA_*`
  This is Tier S, reversible, touches no system files, and needs no root (`/usr` is read-only on SteamOS). Writing `~/.drirc` is an alternative but is a user-file write that must go through `deckforge.safety` (R10) and applies by application or engine name instead of per Steam appid.
- **Keep shader-affecting drirc options keyed by engine or app name.** Valve's Fossilize note means DeckForge should not invent executable-matched shader-affecting drirc entries. Launch-option environment variables also aren't seen by Steam's background Fossilize replay, so the first run will compile locally (Q1).
- **Stacking on Valve's profiles.** DeckForge's settings should layer on top of Valve's built-in profiles, not fight them. DXVK and vkd3d-proton apply profiles first, and user `DXVK_CONFIG` / `VKD3D_CONFIG` flags add to them. `VKD3D_CONFIG` is appended to by Proton itself in some cases (proton L1904), so DeckForge should append rather than overwrite.
- **Anti-cheat.** For anti-cheat titles (Tier S only per CLAUDE.md), env-var driver knobs are not injection, but some knobs (e.g. hiding the GPU, changing feature levels) could alter game behavior. Keep anti-cheat titles to well-understood, documented knobs.

### Gaps
- I didn't confirm how the Steam client composes launch-option environment variables with its own injected variables (precedence when both set `VKD3D_CONFIG` or `DXVK_CONFIG`).
- I didn't verify whether SteamOS ships additional Valve-only drirc files beyond upstream Mesa defaults (e.g. in `/usr/share/drirc.d`). That needs a look on a real Deck (bench phase).
- I didn't read the content of `radv_app_layer=ue5` (what the UE5 app layer actually changes).
