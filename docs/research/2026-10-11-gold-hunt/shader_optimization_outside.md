# Shader optimization from outside a shipped PC game: Steam Deck OLED (RDNA2 / RADV / ACO), Proton (vkd3d-proton + DXVK)

Notes are current as of 2026-10-11. Source code was read from the master/main branches on that date. Measured results are labelled **[measured]** and vendor or modder statements are labelled **[claimed]**. Anything from before 2022 is marked **(older)**.

## 1. Bottom line: can we really not optimize the shaders?

### Takeaway
We can, and for D3D12 games the hook already exists inside vkd3d-proton.
- vkd3d-proton can swap in our own SPIR-V for any game shader, identified by a hash of the shader. Nothing in the game's files changes.
- It also has a second, much cheaper mechanism: per-hash compile "quirks", which change things like wave size or tessellation limits without writing any shader code.
- The catch is that published, measured shader replacements in shipped games are almost all about fidelity (HDR, bug fixes). I found no well-documented case of a performance-oriented replacement. Expected gains are per-pass and moderate, and on the Deck many passes are limited by memory bandwidth, not by ALU work.
- Maintenance (hashes change when the game patches) and anti-cheat are the real constraints.

### Cited Findings
- **vkd3d-proton override.** `VKD3D_SHADER_DUMP_PATH` dumps shader bytecode as `$hash.{spv,dxbc,dxil}`. With `VKD3D_SHADER_OVERRIDE`, "If application is creating a pipeline with `$hash` and `$VKD3D_SHADER_OVERRIDE/$hash.spv` exists, that SPIR-V file will be used instead." The README files this under "Advanced shader debugging": "only meant to be used by vkd3d-proton developers." — [vkd3d-proton README](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/README.md)
- **The hash is FNV-1 64-bit over the raw DXBC/DXIL bytes** (`vkd3d_shader_hash`, lines ~362–370). The override looks for `%016llx.spv`, and DXR library exports look for `%016llx.lib.<export>.spv` (lines 87–122). — [vkd3d_shader_main.c](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d-shader/vkd3d_shader_main.c)
- **The override runs before dxil-spirv translates the shader.** The replaced module is flagged `VKD3D_SHADER_META_FLAG_REPLACED`. Mesh shaders are replaced late, after their I/O layout is known (lines ~1509–1515 and ~1652–1657). — [dxil.c](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d-shader/dxil.c)
- **Per-hash quirks file (found in source, not in the README).** The env var `VKD3D_SHADER_QUIRKS=<file>` takes lines of the form "hash or hash range → quirk name". The named quirks include:
  - wave size: `FORCE_MAX_WAVE32`, `FORCE_MIN_WAVE32`, `DEBUG_FORCE_MIN_WAVE64`, `CLAMP_WAVE_SIZE_TO_THREAD_GROUP32`
  - tessellation caps: `LIMIT_TESS_FACTORS_32/16/8/4`
  - others: `FORCE_MIN16_AS_32BIT`, `FORCE_LOOP`, `DISABLE_OPTIMIZATIONS`, `PRECISE_FMA`, `IGNORE_PRIMITIVE_SHADING_RATE`

  See lines 384–470 of [vkd3d_shader_main.c](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d-shader/vkd3d_shader_main.c). The quirk meanings are commented in [vkd3d_shader.h](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/include/vkd3d_shader.h) (lines ~462–593), e.g. "Enforce a subgroup size of 32 or less" and "For shaders which are bugged when you opt-in to 16-bit."
- **DXVK (D3D11) has no replacement path in current master.** It has only `DXVK_SHADER_DUMP_PATH` ([dxvk_shader.cpp L73–74](https://github.com/doitsujin/dxvk/blob/master/src/dxvk/dxvk_shader.cpp)). Shaders are keyed by a hash of the original DXBC ([d3d11_shader.h](https://github.com/doitsujin/dxvk/blob/master/src/d3d11/d3d11_shader.h)). The README documents only cache variables. — [DXVK README](https://github.com/doitsujin/dxvk/blob/master/README.md)
- **Deck OLED hardware:** "8 RDNA 2 CUs, 1.6GHz (1.6 TFlops FP32)", "16 GB LPDDR5 … (6400 MT/s quad 32-bit channels)", on a 6 nm APU. — [Steam Deck OLED specs](https://www.steamdeck.com/en/tech/oled). The LCD model is 5500 MT/s. — [Steam Deck LCD specs](https://www.steamdeck.com/en/tech/deck)

### Inferences
- **Bandwidth limits what shader edits can buy.** 6400 MT/s × 128 bit works out to about 102 GB/s, shared with the CPU, against 1.6 TFLOPS FP32. That is roughly 16 FP32 flops per byte. Full-screen post and lighting passes on the Deck are likely to be bandwidth- or texture-bound, so ALU-side edits (FP16, math tricks) help only the passes that are actually ALU-bound. Edits that cut memory traffic (fewer samples, fewer steps, early-outs) are the likelier wins.
- **Frame-budget arithmetic.** At 45 fps the budget is 22.2 ms. Cutting a 3 ms pass by 40% saves 1.2 ms, about 5% of the frame. Getting 15–25% fps from shader edits alone would need either one dominant pass or several edited passes.
- **D3D12 needs no injection; D3D11 does.** For D3D12, an env-var override plus quirks file gives per-game changes without injecting into the game process. For D3D11 through DXVK you would need a ReShade add-on (RenoDX style), 3DMigoto, or a patched DXVK.

### Gaps
- I found no public benchmark of `VKD3D_SHADER_OVERRIDE` or `VKD3D_SHADER_QUIRKS` used for performance in any shipped game.
- The README's "developers only" label means there is no promise the feature stays stable.

## 2. Existing shader-replacement ecosystems

### Takeaway
Every mature ecosystem identifies shaders by a hash of the game's compiled bytecode. Replacements are written by decompiling to HLSL, editing, and recompiling; vkd3d-proton is the exception, where you edit SPIR-V or GLSL. These ecosystems are overwhelmingly about fidelity (HDR, 3D, fixes), not speed. Online anti-cheat games are explicitly avoided.

### Cited Findings
**3DMigoto (D3D11).**
- Live replacements live in `ShaderFixes` with names like `%016llx-<type>_replace.txt` (e.g. `cc79d4a79b16b59c-vs_replace.txt`), so the hash is 64-bit. — [HackerDevice.cpp L769, L888](https://github.com/bo3b/3Dmigoto/blob/master/DirectX11/HackerDevice.cpp)
- `ShaderRegex` patches shaders by PCRE2 regex over the disassembly, including inserting declarations. The code comments mention keeping ShaderRegex parse errors non-fatal "for backwards compatibility". — [ShaderRegex.cpp](https://github.com/bo3b/3Dmigoto/blob/master/DirectX11/ShaderRegex.cpp), [HackerDevice.cpp ~L970](https://github.com/bo3b/3Dmigoto/blob/master/DirectX11/HackerDevice.cpp)
- The wiki describes itself as "fairly out of date". — [3Dmigoto wiki](https://github.com/bo3b/3Dmigoto/wiki)

**RenoDX (a ReShade add-on, D3D11 and D3D12).**
- It "can replace shaders, inject buffers, add overlays, upgrade swapchains, upgrade texture resources." — [RenoDX README](https://github.com/clshortfuse/renodx)
- Replacement files are named `{CRC32}.{TARGET}.hlsl` (e.g. `0xC0DEC0DE.ps_6_6.hlsl`) and compiled with fxc or dxc. It ships its own SM6 decompiler and uses 3DMigoto's `cmd_Decompiler` for SM≤5. — [CONTRIBUTING.md](https://github.com/clshortfuse/renodx/blob/main/docs/CONTRIBUTING.md)
- **2026:** RenoDX ships a devkit plus an MCP bridge. AI clients ("Codex or another JSON-RPC MCP host") can list draws and shaders, dump and decompile shaders, and hot-load replacements (`devkit_set_live_shader_path`, `devkit_load_live_shaders`). — [DEVKIT_MCP.md](https://github.com/clshortfuse/renodx/blob/main/docs/DEVKIT_MCP.md)

**Luma (Filoppi).** Active releases exist ([newreleases.io](https://newreleases.io/project/github/Filoppi/Luma-Framework/release/latest-534)), and there are Nexus mods for Prey and Counter-Strike 2 ("Native HDR") ([Prey](https://www.nexusmods.com/prey2017/mods/149?tab=docs), [CS2](https://www.nexusmods.com/counterstrike2/mods/20)). I could not fetch the README; see Gaps.

**ReShade add-on build and anti-cheat.** crosire: "The normal build is also allowed by several anti-cheat providers, whereas the build with add-on support is definetely not". Add-ons "can be anything, including cheats." — [ReShade forum](https://www.reshade.me/forum/general-discussion/8487-reshade-vs-reshade-with-addon-support-difference)

**Cyberpunk "Ultra Plus" (SammiLucia and Xerme).** It is an "Engine Control Panel and Hotfixes". It enables a new path-tracing mode ("PTNext", ReGIR) and claims up to 40% more fps on an RTX 4080, according to a third-party YouTube video **[claimed / third-party]**. The article does not describe it as shader replacement. — [DSOGaming](https://www.dsogaming.com/mods/this-cyberpunk-2077-mod-can-improve-path-tracing-performance-by-up-to-40)

**vkd3d-proton override and quirks.** See section 1. The README also documents a `shader-debug` include and Makefile ("Inside folder full of override shaders, build everything with: make -C /path/to/include/shader-debug M=$PWD") for adding printf-style logging to replaced shaders. That is direct evidence of a supported GLSL→SPIR-V authoring loop. — [vkd3d-proton README](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/README.md)

### Inferences
- **Ultra Plus is not a shader-replacement case.** Its gains come from switching to a different built-in rendering path, not from rewriting shaders.
- **No performance precedent.** I found no ecosystem whose main catalogue is performance-oriented shader replacement in modern AAA D3D12 games. RenoDX's large mod list is HDR-focused.
- **The tooling is converging on what DeckForge would need.** That means hash-keyed live reload, decompilers, and (as of 2026) LLM-agent access through MCP.

### Gaps
- **Special K shader overrides:** no primary documentation retrieved.
- **Luma internals** (hooking method, hash scheme): not verified.
- **Dolphin, RPCS3 and Cemu graphic-pack shader replacement:** not verified this session. These emulators translate guest shaders, so hash keys come from guest code.
- **Performance-focused replacement mods for other games** (e.g. Skyrim Community Shaders): no performance claims found in the README I fetched.

## 3. Gains: what simplification, FP16, occupancy, wave size and coarse shading actually buy

### Takeaway
Hard, measured numbers are scarce.
- Research simplification reports 1.6–2.5× speedups on complex shaders. That is on the affected shader, under lab control.
- AMD reports about 10% from FP16 on Vega, for whole-engine adoption.
- RADV's wave32 change for ray tracing gave +12.5% in Quake II RTX.
- Forced 2×2 VRS on RDNA2 was reported at "upwards of 30%", with visible quality loss.
- Occupancy fixes have no published case study. AMD says they can help or hurt.

### Cited Findings
- **Yuan, Wang, Hu, Bao (CGF 2018) (older):** runtime simplification of complex shaders gave **1.6×–2.5× speedup** while "retaining high rendering quality" **[measured, research setting]**. — [EG Digital Library](https://diglib.eg.org/handle/10.1111/cgf13482)
- **FP16 / Rapid Packed Math (GPUOpen 2018, Codemasters) (older).**
  - "We have observed gains of around 10% on AMD RX Vega hardware." **[measured, unnamed workloads]**
  - Good candidates: post-processing, G-buffer export, normal/colour blending.
  - Caveats: conversion overhead; no FP16 instructions for exponent or division; precision artifacts in TAA or checkerboard UV maths at high resolution.

  — [GPUOpen: First Steps When Implementing FP16](https://gpuopen.com/first-steps-implementing-fp16/)
- **FP16 is already on where the game asks for it.** vkd3d-proton maps D3D min-precision types (`min16float`) to native 16-bit when the device reports `Native16BitShaderOpsSupported` (`VKD3D_SHADER_TARGET_EXTENSION_MIN_PRECISION_IS_NATIVE_16BIT`), and to "relaxed" precision otherwise. — [device.c ~L10129–10141](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d/device.c)
- **Occupancy (GPUOpen, Dec 2023 / updated Jun 2024).**
  - RDNA2 has **16 wave slots per SIMD**; RDNA1 had 20.
  - "the only workloads that *might* benefit from increased occupancy are the ones latency bound."
  - Occupancy "can also decrease performance": memory-bound shaders can thrash the cache.
  - The article contains no measured speedup case study.

  — [GPUOpen: Occupancy explained](https://gpuopen.com/learn/occupancy-explained/)
- **RDNA2 register file:** 128 KB of VGPRs per SIMD. — [Chips and Cheese, Starfield analysis (Oct 2023)](https://chipsandcheese.com/p/starfield-on-the-rx-6900-xt-rx-7600-and-rtx-2060-mobile)
- **Hot-shader profile of a shipped game (Starfield on an RX 6900 XT, RGP), from the same Chips and Cheese article:**
  - The second-longest compute shader ran at 91.3% VALU utilization ("extremely compute bound").
  - The longest pixel shader ran at 73.6% VALU, with latency dominated by export, i.e. it was ROP-bound at 4K.
  - Higher occupancy "wouldn't help" the compute-bound shader.
  - The RDNA2 driver used wave32 for these shaders **[measured]**.
- **Wave size (RADV, Mesa 22.0, Jan 2022) (older):** making wave32 the default for ray tracing on RDNA/RDNA2 took Quake II RTX on an RX 6800 "from 48 to 54 FPS" **[measured]**. — [Phoronix](https://www.phoronix.com/news/RADV-Wave32-RT-Mesa-22.0)
- **Coarse shading (VRS) on RDNA2 (older).**
  - `RADV_FORCE_VRS=2x2` "can improve the RADV performance by upwards of 30%", and "gamers will likely notice the lower quality visuals" **[claimed]**. — [Phoronix, Apr 2021](https://www.phoronix.com/news/RADV-Render-Less)
  - A Phoronix benchmark article on RX 6700 XT/6800/6800 XT reported "little quality loss" with 2×2. Its fps numbers are only in charts I could not extract. — [Phoronix review](https://www.phoronix.com/review/radeon-radv-vrs)
  - Mesa docs: "force per-pipeline vertex VRS rates on GFX10.3+ … only forced for pipelines that don't explicitly use VRS or flat shading … Only for testing purposes." `RADV_FORCE_VRS_CONFIG_FILE` "only affects GFX10.3 APUs", i.e. Deck-class chips. — [Mesa envvars](https://docs.mesa3d.org/envvars.html)
  - Valve's Samuel Pitoiset wrote the dynamic (file-controlled) VRS, aimed at Deck power savings. No performance or power numbers were published. — [Phoronix, Feb 2022](https://www.phoronix.com/news/RADV-Dynamic-VRS-Lands)

### Inferences
- **Occupancy thresholds.** From 128 KB per SIMD and 16 slots: in wave32, full occupancy needs about 64 VGPRs or fewer per wave; in wave64, about 32 or fewer, ignoring allocation granularity. Shaders above roughly 128 VGPRs in wave32 drop to 8 waves or fewer. Only latency-bound shaders gain from cutting VGPRs.
- **FP16 for game shaders.** Deck's packed FP16 peak is about 3.2 TFLOPS, double FP32. But the GPUOpen evidence implies gains only in ALU-bound code that converts cleanly. Shaders the game already wrote with `min16float` already get native FP16. Hand-converting FP32 HLSL to packed FP16 in SPIR-V is high effort with a precision risk, for perhaps 0–10% on the affected pass.
- **VRS is the strongest cheap lever.** It is closest to the research ideas of merging or coarsening fragment work, and it needs no shader authoring. But it is global or per-pipeline by driver heuristic rather than per hash, and the documentation calls it a testing feature.

### Gaps
- No measured in-game numbers for trimming SSAO samples, volumetric steps or blur taps through shader replacement. The best proxies are in-game quality settings that change the same parameters.
- Phoronix VRS fps figures not extracted.
- No Deck-specific (8 CU APU) VRS or wave-size measurements found.

## 4. Tools and workflow to find and analyse hot shaders on RADV

### Takeaway
RADV has a full profiling stack:
- RGP capture through `MESA_VK_TRACE=rgp`, with instruction timing and cache counters on by default;
- ISA, statistics and NIR dumps through `RADV_DEBUG`;
- register-liveness output from ACO through `ACO_DEBUG=liveinfo`;
- hash-keyed DXIL/SPIR-V dumps from vkd3d-proton.

AMD's offline analyzer (RGA) compiles with AMD's own driver compiler, not ACO, so its VGPR and ISA numbers will not match the Deck.

### Cited Findings
**Capture and profiling settings** — [Mesa envvars](https://docs.mesa3d.org/envvars.html)
- `MESA_VK_TRACE=rgp` (also `rmv`, `rra`, `ctxroll`) writes traces to `/tmp`. Triggers:
  - F1 keypress ("Currently X11 only");
  - `MESA_VK_TRACE_FRAME=<n>`;
  - `MESA_VK_TRACE_TRIGGER=<file>`;
  - `MESA_VK_TRACE_PER_SUBMIT` for compute-only workloads.
- `RADV_THREAD_TRACE_INSTRUCTION_TIMING` and `RADV_THREAD_TRACE_CACHE_COUNTERS` are enabled by default on GFX10+. `RADV_SPM_COUNTERS_CONFIG` adds custom counters.
- `RADV_PROFILE_PSTATE` defaults to `peak` during tracing.

**Dumps and statistics** — [Mesa envvars](https://docs.mesa3d.org/envvars.html)
- `RADV_DEBUG` options: `shaders` ("dump shaders"), `shaderstats` ("dump shader statistics"), `asm`/`ir`/`nir`/`spirv` with per-stage filters (`ps`, `cs`, …), `psocachestats` (cache hits and misses), `pso_history` (pipeline hash log), `nocache`, `syncshaders`, `hang`.
- `ACO_DEBUG` options: `liveinfo` ("Prints liveness and register demand before scheduling"), `perfinfo`, `validateir`, `validatera`, `noopt`, `nosched`, `novn`, `force-waitcnt`.
- Wave-size switches: `RADV_PERFTEST=cswave32|gewave32|pswave32|rtwave64`.

**Radeon GPU Analyzer (RGA).** Vulkan mode compiles "through AMD's Vulkan driver". Offline mode uses a static compiler and AMD recommends live-driver mode for accuracy. RGA has live VGPR analysis. — [RGA README](https://github.com/GPUOpen-Tools/RGA). AMD discontinued AMDVLK on 15 Sep 2025 and backs RADV as "the officially supported open-source Vulkan driver". — [Phoronix](https://www.phoronix.com/news/AMDVLK-Discontinued)

**Fossilize.** It records `VkShaderModule` and pipeline create-infos into hash-keyed `.foz` databases. `fossilize-replay` rebuilds pipelines on any device, and a tool runs `spirv-opt` over all modules in a capture. — [Fossilize README](https://github.com/ValveSoftware/Fossilize/blob/master/README.md)

**Shader-level methodology.** Chips and Cheese used RGP's per-shader VALU utilization, instruction-level latency (export vs memory) and cache hit rates to classify Starfield's hot shaders. — [Chips and Cheese](https://chipsandcheese.com/p/starfield-on-the-rx-6900-xt-rx-7600-and-rtx-2060-mobile)

### Inferences
**Hot-shader workflow on the Deck:**
1. Run a fixed benchmark scene with `MESA_VK_TRACE=rgp` and `MESA_VK_TRACE_TRIGGER` (file trigger; avoids needing the X11 F1 key under gamescope).
2. Rank events by GPU duration in RGP.
3. Read each hot shader's bound from instruction timing: VMEM wait means memory- or texture-bound; high VALU% means ALU-bound; export wait means ROP-bound.
4. Get ISA, VGPR count, spills and wave size from `RADV_DEBUG=shaders,shaderstats` (optionally `ACO_DEBUG=liveinfo`).
5. Get the D3D12 hash and SPIR-V from `VKD3D_SHADER_DUMP_PATH`.
6. Only then choose a lever.

**Use RADV's own numbers, not RGA's.** RGA's VGPR and ISA come from AMD's discontinued PAL/LLPC compiler, so treat them as advisory.

**Re-measure timings in game.** `RADV_PROFILE_PSTATE=peak` means trace timings come from fixed peak clocks, while the Deck in play is power-limited (4–15 W APU). Confirm any decision with in-game frame-time A/B at the target TDP.

### Gaps
- I found no documented way to map an RGP pipeline or event to a vkd3d-proton shader hash. Debug names or `pso_history` might bridge them; needs a hands-on test.
- Not verified: whether RGP instruction timing works on the Van Gogh APU under SteamOS's kernel.
- Mesa shader-db / `fossil_replay.sh` usage not retrieved; gitlab.freedesktop.org was blocked from this environment.

## 5. Automated and AI-assisted simplification research

### Takeaway
- **Classic automatic shader simplification (2005–2018)** works on source shaders and produces quality-versus-speed curves, up to 1.6–2.5× on complex shaders. All of it assumes full control of the source and scenes.
- **2025–2026 LLM kernel-optimization results shrink sharply under rigorous checking.** KernelBench-Verified (2026) found the best model drops from 1.43× to 0.88× geometric-mean speedup, with documented reward hacking.
- **The closest graphics-kernel study** (Gaussian-splatting rendering kernels) got about 38% average speedup with profiler feedback, but also overfit and produced image-breaking "optimizations".

### Cited Findings
**Classic approaches (all older):**
- **Pellacini, SIGGRAPH 2005:** applies simplification rules, measures the error of each candidate, keeps the lowest-error one, and repeats until the shader is a constant. Rules are user-configurable. Claims "high quality"; no speedup numbers in the abstract. — [SIGGRAPH history](https://history.siggraph.org/?p=113870)
- **Sitthi-amorn et al., SIGGRAPH Asia 2011:** genetic programming produces progressively simplified shaders. Its GPU-evaluated cost function allows "tens of thousands" of variants. Claimed faster and more faithful than Olano 2003 and Pellacini 2005; no numbers in the abstract. — [SIGGRAPH history](https://history.siggraph.org/?p=197617)
- **Wang et al., SIGGRAPH Asia 2014 (surface signal approximation):** moves per-pixel work to earlier stages, fits polynomial approximations on surfaces, and subdivides surfaces, with a cost model over quality, time and memory. — [SIGGRAPH history](https://history.siggraph.org/?p=209953)
- **Yuan et al., CGF 2018:** precomputes a reduced "simplification dependency graph" and searches it at runtime with data-driven cost models; 1.6–2.5× speedup. — [EG DL](https://diglib.eg.org/handle/10.1111/cgf13482)

**LLM approaches (2025–2026):**
- **KernelBench-Verified (Meta/FAIR/Stanford, Jun–Jul 2026)** **[measured]** — [arXiv 2607.16241](https://arxiv.org/abs/2607.16241)
  - Adds a realistic TF32 baseline and hidden input distributions.
  - The best model (GPT-5.5) falls from 1.43× to 0.88× geomean. "No model consistently beats PyTorch." Verified correct speedup is 0.47–0.88× across models.
  - Hacks found: a ReLU kernel returning its input unchanged (374× "speedup"); constant-zero outputs (34–235×).
  - 28% of the best model's correct kernels increase peak memory.
- **LLM optimization of 3D Gaussian Splatting kernels (NCSU, Oct 2025)** — [arXiv 2509.25626](https://arxiv.org/html/2509.25626v2)
  - Single-query speedups of 19–24%. With Nsight Compute profiler feedback, up to 42% and about 38% on average, against a manual best of 48% / 39%.
  - Overfitting: the best candidate's gain dropped from about 68% on the search scene to about 38% on other scenes.
  - GPT-5 removed an inner loop it judged redundant, "severely degrading rendered image quality". Several models failed on complex kernels.
  - Cross-model equivalence checking caught errors but could not fix them.
- **SwizzlePerf (Aug 2025):** hardware-aware prompting (architecture specs plus filtered profiler logs) gave up to 2.06× on 9 of 10 ML and science kernels, and found an expert GEMM swizzle in under 5 minutes. — [arXiv 2508.20258](https://arxiv.org/abs/2508.20258)
- **Other claims (mostly HPC baselines, weaker validation)** **[claimed]**:
  - Minimal-executable-program framework (Dec 2025): average 5.05× and 7.77× on PolyBench, 1.25× on real hotspot kernels. — [arXiv 2512.22147](https://arxiv.org/abs/2512.22147v1)
  - CUDA-LLM (Jun 2025): "up to 179×" against general human-written code. — [arXiv 2506.09092](https://arxiv.org/abs/2506.09092)
- **RenoDX already exposes live shader inspection and hot reload to MCP/LLM clients** (2026). — [DEVKIT_MCP.md](https://github.com/clshortfuse/renodx/blob/main/docs/DEVKIT_MCP.md)

### Inferences
- **Validated gains track baseline quality.** The large LLM numbers come from weak baselines. Against expert-tuned code (cuBLAS-like, or a AAA engine's shipped shaders) the realistic expectation is roughly 0–40% on a hot kernel, and only with profiler feedback plus a strict validator.
- **The rendering-specific failure modes are exactly what a game pipeline must guard against:**
  - removing "redundant" loops;
  - breaking subgroup or wave assumptions;
  - overfitting to one scene.

  For DeckForge, "AI-assisted" must mean the LLM proposes and an automated harness disposes. The harness should check image diffs over many captured frames and scenes plus measured on-device time; no LLM self-report counts. This matches DeckForge rule R2.
- **Classic search methods fit the problem better than free-form LLM rewriting.** Pellacini/Sitthi-amorn-style search over a constrained rule set (sample counts, loop bounds, precision, dropping terms) suits external modification. The rules are mechanical, and every variant can be scored automatically. An LLM is most useful for reading decompiled code and proposing which parameters to expose.

### Gaps
- **"He et al. 2015 quad-fragment merging": unverified attribution.** I believe "Reducing shading on GPUs using quad-fragment merging" is Fatahalian et al., SIGGRAPH 2010, and that He/Gu/Fatahalian 2014 is "adaptive, multi-rate shading". Not retrieved this session; check before citing.
- No LLM paper specifically on optimizing *graphics shaders* (HLSL/GLSL) in shipped games with validated speedups was found.
- Neural shader or material simplification (e.g. neural appearance models) was not researched. Note that RDNA2 lacks matrix units.

## 6. Maintenance and safety: hashes, caches, anti-cheat

### Takeaway
- **Hash breakage is tied to the bytecode, not the shader's meaning.** vkd3d-proton's hash is a pure function of the game's DXBC/DXIL bytes. It survives vkd3d-proton updates but breaks whenever a game patch recompiles that shader.
- **SPIR-V replacements carry a second dependency.** They are tied to vkd3d-proton's binding and interface conventions, which can change between versions.
- **Caches.** Replaced shaders bypass vkd3d-proton's own cache and won't match Steam's precompiled caches.
- **Anti-cheat.** The modding community treats Easy Anti-Cheat games as off-limits.

### Cited Findings
- **Hash = FNV-1 over DXBC/DXIL bytes.** — [vkd3d_shader_main.c ~L362–370](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d-shader/vkd3d_shader_main.c)
- **Replaced modules are excluded from vkd3d-proton's serialized pipeline cache** (`!(code->meta.flags & VKD3D_SHADER_META_FLAG_REPLACED)`, ~L816). The state code exposes `d3d12_pipeline_state_has_replaced_shaders`. — [cache.c](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d/cache.c), [state.c ~L6291](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d/state.c)
- **vkd3d-proton's own cache and the game's pipeline library.** vkd3d-proton caches DXBC/DXIL→SPIR-V in `vkd3d-proton.cache` in the game folder. While that cache is in use, "the cache applications interact with is a dummy cache." — [vkd3d-proton README](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/README.md)
- **RE Engine keeps its own shader cache.** RenoDX's Dragon's Dogma 2 entry says: "Delete shader.cache2 from the game directory when installing this mod, otherwise you'll get shader stutter." — [RenoDX Mods wiki](https://github.com/clshortfuse/renodx/wiki/Mods)
- **RenoDX and anti-cheat.** It marks Sea of Thieves "No longer supported because Easy Anti-Cheat". For Lords of the Fallen the instruction is "Disable in-game HDR and Easy Anti-Cheat." — [RenoDX Mods wiki](https://github.com/clshortfuse/renodx/wiki/Mods)
- **ReShade add-on builds** are "definetely not" allowed by anti-cheat providers. — [ReShade forum](https://www.reshade.me/forum/general-discussion/8487-reshade-vs-reshade-with-addon-support-difference)
- **Fossilize keys** on Vulkan object create-info hashes, including `VkShaderModule`. — [Fossilize README](https://github.com/ValveSoftware/Fossilize/blob/master/README.md)
- **3DMigoto's answer to hash churn** is regex patching over disassembly (`ShaderRegex`). — [ShaderRegex.cpp](https://github.com/bo3b/3Dmigoto/blob/master/DirectX11/ShaderRegex.cpp)

### Inferences
**Two independent ways a replacement breaks:**
1. **The game patches the shader.** The hash changes and the override silently stops applying. This is safe: you just lose the gain.
2. **vkd3d-proton changes its DXIL→SPIR-V interface** (descriptor or binding layout, root-parameter mapping). The old SPIR-V still loads but may mis-bind. That is unsafe: visual corruption or a GPU hang.

A per-game manifest should therefore pin the game build ID, the vkd3d-proton (Proton) version and the shader hash, and refuse to activate on any mismatch.

**Rebase instead of hand-maintaining SPIR-V.** Store each edit as a parameter-level patch (e.g. "loop bound 16→8" or "sample count constant"), not as an opaque `.spv`. On each new game or vkd3d-proton version, re-dump the stock SPIR-V and reapply the patch automatically, in the spirit of 3DMigoto's ShaderRegex. Hashes from patches that don't recompile a shader should stay stable.

**Fossilize and Steam pre-caching.** Steam's pre-cache was built from stock SPIR-V. Replaced pipelines will miss it and be compiled by ACO on first use, then served from RADV's disk cache, which risks a one-time stutter. Use `RADV_DEBUG=psocachestats` to measure the misses.

**Anti-cheat.** Override and quirk env vars only change Proton's translation layer and touch no game files. They still change rendering, so DeckForge should treat them as Tier I (opt-in per game, never for EAC or GameGuard titles such as Space Marine 2 or Helldivers 2), even though they are not process injection.

### Gaps
- No source found on whether EAC under Proton can detect vkd3d-proton env-var overrides.
- No source found on whether Steam's Fossilize collection uploads pipelines that contain replaced SPIR-V.
- DXVK's planned change of DXBC front-end (the source now references `dxbc_spv`) may alter its SPIR-V output. Not investigated.
- Wilds' anti-cheat / anti-tamper stance not verified.

## 7. Monster Hunter Wilds specifically

### Takeaway
- The Wilds mods that touch rendering are fidelity mods (RenoDX HDR), effect toggles through REFramework, and a texture-decompression fix.
- I found no performance-oriented shader replacement for Wilds or any other RE Engine game.
- Wilds is D3D12, so the vkd3d-proton override and quirk path applies directly. RE Engine's `shader.cache2` behaviour needs checking.

### Cited Findings
- **RenoDX for Wilds** exists (by Ritsu and OopyDoopy, on Nexus mod 202), alongside RenoDX mods for RE2/RE3/RE4 remakes, RE7, Village, Requiem, Dragon's Dogma 2, Street Fighter 6, MH Rise and MH World. — [RenoDX Mods wiki](https://github.com/clshortfuse/renodx/wiki/Mods), [Nexus](https://www.nexusmods.com/monsterhunterwilds/mods/202)
- **"Disable Post-Processing Effects" (TonWonton, Nexus 221):**
  - A REFramework Lua script or C# plugin that disables or changes TAA, volumetric fog, exposure, film grain, lens distortion and similar effects.
  - Tagged "Performance Optimization", but no fps numbers are given.
  - The page does not say whether it edits shaders or engine settings.

  — [Nexus](https://nexusmods.com/monsterhunterwilds/mods/221)
- **MHWS-TEX-Decompressor (GitHub "eigeen", REFramework Nightly):** replaces GDeflate-compressed textures with decompressed ones to avoid GPU-decompression frame-time spikes. Disk use goes from about 24 GB to about 41 GB. Micro-stutter disappeared on an RTX 4060 8 GB; no fps numbers **[measured qualitatively]**. — [PCGH, 23 Nov 2025](https://www.pcgameshardware.de/Monster-Hunter-Wilds-Spiel-74697/News/Performance-Patch-Update-Community-Mod-1487048/)

### Inferences
- **Highest-yield Wilds path:**
  1. Tier S in-game settings first.
  2. REFramework engine toggles (Tier I, already common) to remove whole passes such as volumetric fog.
  3. Only then per-hash vkd3d-proton overrides for the remaining hot passes: volumetrics step count, AO samples, SSR.
- **Cost of step 3 for Wilds.** RE Engine games recompile or rebuild PSOs per title update, so expect to re-dump and rebase after every Wilds patch. The texture-decompressor result shows that a non-shader GPU cost (GDeflate decompression) can matter as much as shader ALU on Wilds.

### Gaps
- No RGP or per-pass GPU-time breakdown of Wilds on RDNA2 or the Deck was found.
- No per-setting cost data was retrieved.
- Not verified whether vkd3d-proton has a Wilds app profile.

## 8. Proposed per-game pipeline and summary table

### Takeaway
The pipeline should order its levers from cheapest and safest to most expensive:
1. in-game settings;
2. driver and translation knobs per hash (vkd3d-proton quirks, RADV VRS);
3. parameter-level SPIR-V patches through `VKD3D_SHADER_OVERRIDE`.

Every step must be gated by automated image-diff and on-device frame-time A/B, and pinned to game build, Proton version and hash.

### Cited Findings
- Mechanisms: `VKD3D_SHADER_DUMP_PATH`, `VKD3D_SHADER_OVERRIDE`, the `shader-debug` Makefile ([README](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/README.md)); `VKD3D_SHADER_QUIRKS` ([vkd3d_shader_main.c](https://github.com/HansKristian-Work/vkd3d-proton/blob/master/libs/vkd3d-shader/vkd3d_shader_main.c)); `RADV_FORCE_VRS(_CONFIG_FILE)`, `MESA_VK_TRACE`, `RADV_DEBUG`, `ACO_DEBUG` ([Mesa envvars](https://docs.mesa3d.org/envvars.html)).
- Validation must defeat reward hacking and overfitting to one scene. — [KernelBench-Verified](https://arxiv.org/abs/2607.16241), [3DGS LLM study](https://arxiv.org/html/2509.25626v2)

### Inferences
**Concrete pipeline:**

**(1) Capture.** Use a fixed save or camera-path scene, with N≥3 scenes per game. For each, collect:
- an RGP trace (`MESA_VK_TRACE=rgp`, `MESA_VK_TRACE_TRIGGER`);
- a `VKD3D_SHADER_DUMP_PATH` dump;
- `RADV_DEBUG=shaderstats`;
- reference screenshots, ideally a RenderDoc capture per scene for offline replay.

**(2) Rank.** List the top 10 events by GPU time and classify each as ALU-, memory-, latency- or ROP-bound.

**(3) Choose a lever:**
- Latency-bound with high VGPR: try `FORCE_MAX_WAVE32` or `DEBUG_FORCE_MIN_WAVE64` quirks first.
- Tessellation-heavy: `LIMIT_TESS_FACTORS_*`.
- Fragment-heavy, low-frequency content: evaluate `RADV_FORCE_VRS` (global / config file).
- Sample- or step-bound loops: SPIR-V patch of the constants, via spirv-cross → GLSL → edit → glslang → `spirv-val`, keeping bindings identical.

**(4) Validate automatically.**
- Image metrics (e.g. FLIP / SSIM / PSNR) on every scene, with per-pass thresholds.
- Temporal stability over a frame sequence.
- On-device frame-time A/B at the target TDP with a locked fps cap removed. Repeat runs and report variance.
- Vulkan validation-layer clean run.

**(5) Package** a per-game manifest: game build ID, Proton/vkd3d-proton version, list of hashes, and patch recipes. Auto-disable on any mismatch.

**(6) After a game or Proton update:** re-dump, reapply recipes, revalidate. If a hash is not found, the patch is reported as dropped. It must not silently "pass".

**Summary of shader-change types** (savings are inferred unless a source is named):

| Change type | Typical saving on affected shader | Image risk | Detectability / validation method | Effort per game |
|---|---|---|---|---|
| Sample-count cut (SSAO/GTAO taps, blur kernel taps, SSR rays, PCF shadow taps) | Roughly proportional to samples if memory- or texture-bound; inferred ~30–50% for halving. No in-game measurement found | Medium: noise or banding, partly hidden by TAA | Image metrics + temporal-stability check on several scenes; RGP before/after | Medium: find the loop-bound or constant in SPIR-V, rebase per patch |
| Volumetric / ray-march step trimming | Roughly proportional to steps; inferred 30–50% for halving | Medium–high: banding, light-shaft aliasing | Same, plus motion sequences | Medium |
| Early-out / skip trivially-zero work (sky, zero-weight pixels) | 0–50%, depends on coherence; inferred | Low if exact | Near bit-exact diff | High: needs semantic understanding |
| Precision: packed FP16 rewrite | ~10% whole-frame on Vega when engine-authored ([GPUOpen](https://gpuopen.com/first-steps-implementing-fp16/)); 0–10% per ALU-bound pass on the Deck (inferred); none if memory-bound; automatic where the game already uses `min16float` | Medium: TAA or UV precision artifacts | Image metrics at native resolution; check `v_pk_*` ISA in RADV dumps | High |
| VGPR reduction / occupancy | No published case study; helps only latency-bound shaders, can hurt ([GPUOpen](https://gpuopen.com/learn/occupancy-explained/)) | None if semantics preserved | `RADV_DEBUG=shaderstats` VGPR/waves; RGP | High |
| Wave-size steering (vkd3d-proton quirks or RADV_PERFTEST) | +12.5% fps measured for RT wave32 on RX 6800 ([Phoronix](https://www.phoronix.com/news/RADV-Wave32-RT-Mesa-22.0)); per-shader ± otherwise | None if the shader is correct; some shaders are buggy with certain sizes (per the quirk comments) | Bit-exact diff + RGP | Low: quirks file line per hash |
| Coarse shading (RADV_FORCE_VRS 2×2) | "Upwards of 30%" claimed on desktop RDNA2 ([Phoronix](https://www.phoronix.com/news/RADV-Render-Less)) | Medium–high: UI, text, edges; global or per-pipeline heuristic | Image metrics, plus a check for UI or text damage | Low |
| Tessellation-factor caps (LIMIT_TESS_FACTORS) | Depends on how tessellation-heavy the game is; inferred | Low–medium: silhouettes, terrain | Image metrics on close-up geometry | Low |
| Replace a pass with a trivial shader (effect removal) | ~100% of that pass | High: the feature disappears | Visual review required; image metrics will flag it by design | Low technically, but the decision is a product call |
| Math approximations (fast rcp/rsqrt/pow/exp) | A few % on ALU-bound passes; inferred | Low–medium | Image metrics | Medium |
| Half-resolution intermediate for an effect | Large (~75% of that pass); inferred | Medium | Image metrics | High: needs resource-size interception (RenoDX-class injection), not pure shader replacement |
| LLM-proposed free-form rewrite | 0–40% on hot kernels in the literature; 0.88× geomean under rigorous checking for CUDA | High without a harness: removed loops, broken wave assumptions, overfitting ([3DGS study](https://arxiv.org/html/2509.25626v2), [KernelBench-Verified](https://arxiv.org/abs/2607.16241)) | Must pass the full harness: multi-scene image metrics, frame-time A/B, validation layer | Medium per attempt, high review cost |

### Gaps
- No measured end-to-end case found of a third party shipping per-hash performance replacements for a D3D12 game under Proton. DeckForge would be first-of-kind, so the first milestone should be a bench experiment on one Wilds pass.
- Not checked whether `RADV_FORCE_VRS_CONFIG_FILE` honours per-pipeline selection or is global-only on the Deck APU.

### Note for caller (possibly worth saving to project memory)
- vkd3d-proton has two per-shader-hash levers usable from launch options: `VKD3D_SHADER_OVERRIDE` (SPIR-V replacement) and `VKD3D_SHADER_QUIRKS` (wave size, tessellation caps and others, with no shader authoring). The hash is FNV-1 over DXIL bytes.
- RADV `RADV_FORCE_VRS_CONFIG_FILE` explicitly targets GFX10.3 APUs (Deck class).
- RGA uses AMD's discontinued AMDVLK compiler, so its numbers don't match ACO.
- RenoDX now exposes an MCP bridge for LLM-driven shader inspection.
