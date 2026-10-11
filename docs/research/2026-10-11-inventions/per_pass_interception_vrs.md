# Generic GPU workload reallocation by Vulkan-layer interception on Steam Deck (RADV, DXVK/vkd3d-proton), with focus on Monster Hunter Wilds

Research date: 2026-10-11. Mesa source was read from a GitHub mirror of Mesa `main` (chaotic-cx/mesa-mirror), fetched 2026-10-11, because the robots rules on gitlab.freedesktop.org blocked direct reads. vkd3d-proton and DXVK source was read from their GitHub `master` branches on the same day. Several sources could not be opened: the Dolphin blog and forums (bot wall or permission timeout), the RPCS3 wiki, the PCSX2 docs site and the archived yuzu blog. Those are listed under Gaps.

## 1. Prior art in emulators: how they choose render targets to scale, and what breaks

### Takeaway
Emulators scale render targets mostly upward and uniformly across the whole frame. Their generic rules are crude: size thresholds, plus blacklisting textures the CPU touches or compute reads. Selective per-pass changes such as "half-res bloom" or "native-res bloom" are almost always hand-written per game: Cemu graphic packs, Dolphin graphics mods, PCSX2 per-game CRC hacks. Emulators have one big advantage a layer lacks. They own the shader translator, so they can patch `texelFetch` and `textureSize` coordinates in place.

### Cited Findings
- **RPCS3 size threshold.** RPCS3's resolution scaling has a "Resolution Scale Threshold" that "will not upscale framebuffers (bitmaps) that are smaller than the selected size." The developers call it "only a temporary workaround" for missing graphics "when write color buffers are used." The blog post is undated, roughly 2017. — [RPCS3 blog](https://rpcs3.net/blog/?p=1015)
- **RPCS3 strict mode.** RPCS3 high-resolution rendering "does not yet work with Strict Rendering Mode" (circa 2017). — [RPCS3 blog](https://rpcs3.net/blog/?p=1015)
- **RPCS3 tooltips (current).**
  - Minimum Scalable Dimension: "Only framebuffers greater than this size will be upscaled. Increasing this value might fix problems with missing graphics when upscaling."
  - Resolution scale: "Values below 100% will usually not improve performance," because the emulator is CPU-bound.
  - [RPCS3 tooltips.cpp](https://raw.githubusercontent.com/RPCS3/rpcs3/master/rpcs3/rpcs3qt/tooltips.cpp)
- **Ryujinx "Zero-Configuration Resolution Scaling"** (riperiperi, PR #1365, 2020-07-07). The commit log lists:
  - "Discount small textures" and "square texture detection".
  - "All CPU modification blacklists scale."
  - Texture2D→Texture3D copies blacklist the texture.
  - A workaround for "random uses of textures in compute" that had been blacklisting textures in some games.
  - "texelFetch scaling on fragment shader (WIP)".
  - [Ryujinx archive commit](https://git.devminer.xyz/archive/Ryujinx/src/commit/484eb645ae0611f60fae845ed011ed6115352e06)
- **yuzu shader patching.** yuzu's "RescalingPass" rewrites shaders:
  - `ImageFetch`/`ImageRead` coordinates are rescaled in fragment shaders. They are multiplied by an up-factor and the fragment's offset inside the down-factor cell is added.
  - Only Color2D and ColorArray2D are handled; other dimensions are marked "Nothing to patch here".
  - `ImageQueryDimensions` (textureSize) is patched only for compute.
  - The scale is selected at runtime by an `is_scaled` flag.
  - Undated commit. — [yuzu commit (OpenPunk mirror)](https://git.openpunk.com/OpenPunk/yuzu/commit/dfa82915262ca26d0884528b7bdae791554332ca)
- **PCSX2 render-target heuristics.** PCSX2's hardware renderer originally assumed "a draw's start address identifies its render target." The "RT in RT" work adds heuristics for offset draws inside an existing target. The risk was misclassification, and the work had to avoid code that "explode[s] on every other game." Per-game CRC hacks remain, for example Hitman Blood Money. Article dated Feb 16, 2025. — [Read Only Memo](https://www.readonlymemo.com/pcsx2-render-target-hdr-performance-graphical-fixes)
- **PCSX2 upscaling fixes.** These are toggles users set per game:
  - "Half Pixel Offset… Might fix some misaligned fog, bloom, or blend effect."
  - "Merge Sprite: Replaces post-processing multiple paving sprites by a single fat sprite."
  - "Unscaled Palette Texture Draws: Forces palette texture draws to render at native resolution."
  - "Native Scaling: Emulates native PS2 coordinate scaling behavior when upscaling to reduce misalignment artifacts."
  - [PCSX2 GraphicsSettingsWidget.cpp](https://raw.githubusercontent.com/PCSX2/pcsx2/master/pcsx2-qt/Settings/GraphicsSettingsWidget.cpp)
- **Cemu graphic packs.** The `[TextureRedefine]` rules match textures by width, height and format filters and overwrite their width, height or format. The rules are applied when the texture is created.
  - Loose filters catch unintended textures: "Some games use background or splash screen textures that have the same resolution."
  - "Cemu resets the contents of a texture if any rule is applied," which can turn an unmatched background black.
  - [Cemu wiki](https://wiki.cemu.info/wiki/Graphic_packs_creation)
- **Dolphin bloom.** Bloom ghosting at high internal resolution was a long-standing known issue. As of June 2026 it is fixed by an opt-in "Bloom Blurred" graphics mod for games such as Metroid Prime, Xenoblade, Mario Galaxy and Okami. Before that, the workarounds were native resolution or mod packs and Gecko codes. — [Notebookcheck, 30 Jun 2026](https://www.notebookcheck.net/Dolphin-Emulator-fixes-high-resolution-Bloom-effects.1330367.0.html)

### Inferences
- **What emulators detect generically:**
  - Size or dimension thresholds (RPCS3, Ryujinx).
  - Format filters (Cemu).
  - Usage blacklists: CPU access, compute use, odd copies (Ryujinx).
  - Shader-side coordinate patching where they own the compiler (yuzu, Ryujinx).
- **What breaks:**
  - Blur and bloom kernels that assume native texel spacing (Dolphin ghosting).
  - Half-pixel or offset alignment (PCSX2).
  - Textures written or read by the CPU or by compute.
  - Accidental matches with same-size unrelated textures (Cemu).
  - Copies between scaled and unscaled resources.
- **What DeckForge should take from this:**
  - Even with full control of the shader compiler, every one of these projects ended up with per-game rules for anything selective.
  - A "generic, automatic" per-pass downscaler is likely to need per-game allowlists.
  - Matching would be by image size, format and usage, or by shader hash, in the style of Special K.
- **The layer's handicap.** DeckForge's layer would sit below DXVK/vkd3d-proton, which already did the translation. Patching `texelFetch`/`textureSize` would mean parsing and rewriting SPIR-V at pipeline creation. That is harder than what emulators do, and a SPIR-V rewriting library would be a new dependency (R8).
- **Direction mismatch.** Emulators scale up to beat the native res. DeckForge would scale selected passes down below what the game asks for. The breakage classes are the same, with one asymmetry: shrinking reduces memory footprint, so aliasing and placement constraints get easier.

### Gaps
- The Dolphin progress report for release-2606 could not be read (bot wall or permission timeout), so how "Bloom Blurred" detects bloom copies is unknown. Dolphin's bug tracker and forum on "what not to scale" were also unreachable.
- The yuzu Resolution Rescaler blog (heuristics write-up) was blocked, and the RPCS3 wiki and PCSX2 docs could not be read. Default threshold values, such as RPCS3's default minimum scalable dimension, were not confirmed.
- No emulator was found that does generic per-pass downscaling below native for performance. RPCS3 says sub-100% scaling usually does not help there.

## 2. Prior art on PC: Special K, ReShade, vkBasalt, DXVK/vkd3d-proton hacks, RADV per-game workarounds

### Takeaway
Pass-level changes by API interception have shipped on PC, but only as per-game mods with hand-identified targets:
- DSfix: D3D9, internal resolution and DoF.
- Kaldaien's TBFix: shadow resolution multipliers plus a "low-precision environmental shadow mode" for performance.
- FAR / Special K for NieR: Automata: reduced GI compute workgroups, plus shader-hash-based disabling of volumetric lighting.

No generic, cross-game downscaler for shadows or volumetrics was found. DXVK, vkd3d-proton and RADV per-game options are correctness or performance workarounds and never lower image quality. ReShade and vkBasalt are post-process injectors and do not resize passes.

### Cited Findings
- **DSfix (Durante).** An "interception DINPUT8.dll" that "intercepts the game's calls to the DirectX 9 API" to raise Dark Souls' internal rendering resolution and improve the DoF effect. It also adds SSAO/SMAA. Uploaded Sept 18, 2012; last updated Jan 28, 2015. — [Nexus Mods DSfix](https://www.nexusmods.com/darksouls/mods/19)
- **TBFix for Tales of Berseria (Kaldaien).** "Up to 8x increase in shadow resolution on character shadows and 4x on environmental." It "Supports low-precision environmental shadow mode to dramatically improve performance at very high resolutions." Uses a `d3d9.ini`; last updated Sept 3, 2018. — [GamePressure TBFix page](https://www.gamepressure.com/download/tales-of-berseria-tales-of-berseria-fix-v01012-mod/z810abd)
- **FAR / Special K for NieR: Automata.**
  - A "Global Illumination Quality" override maps to GI workgroups: Ultra 128, High 64, Medium 32, Low 16, Off 0. "Off" can make dark areas appear red.
  - A `d3d11_shaders.ini` maps pixel-shader hashes to actions, for example `4af66f86=Disable` to disable volumetric lighting and `=HUD` for HUD-less screenshots.
  - [Special K wiki FAR](https://wiki.special-k.info/SpecialK/Custom/FAR)
- **FAR GI tweak reception.** The GI tweak (by DrDaxxy, added to FAR) trades for a "less complex and less accurate Global Illumination solution," with "a lot of reports" of significantly improved performance. No numbers given. The GI value must be a multiple of 16. Mar 23, 2017. — [DSOGaming](https://www.dsogaming.com/news/the-first-global-illumination-performance-mod-for-nier-automata-is-now-available/)
- **ReShade.** The official signed ReShade 5 "will not load add-ons itself." ReShade disables add-on capabilities on network activity, as it already does for depth-buffer access, because of anti-cheat concerns. This is crosire's forum post, roughly four years old, and describes a plan. — [ReShade forum](https://reshade.me/forum/general-discussion/7584-some-concerns-about-reshade-5-0-extended-functionality)
- **DXVK.** It has no render-target or shadow resolution override. Its config has sampler LOD bias, `forceSampleRateShading`, `d3d8.shadowPerspectiveDivide`, and descriptor-model switches (`dxvk.enableDescriptorHeap`, `dxvk.enableDescriptorBuffer`, both Auto). — [dxvk.conf](https://raw.githubusercontent.com/doitsujin/dxvk/master/dxvk.conf)
- **RADV per-game drirc options** are workarounds such as:
  - `radv_disable_dcc`, `radv_disable_aniso_single_level`, `radv_flush_before_timestamp_write`.
  - `radv_app_layer`, a driver-internal per-app entrypoint override for Quantic Dream, UE5, RAGE 2, Metro Exodus, Strange Brigade / Sniper Elite 5, No Man's Sky and GFXBench.
  - No option changes resolution or VRS, and there is no Wilds entry.
  - [00-radv-defaults.conf (mirror)](https://raw.githubusercontent.com/chaotic-cx/mesa-mirror/main/src/amd/vulkan/00-radv-defaults.conf)
- **Valve's only cross-game "render less" hack in RADV is forced VRS** (see section 4). The source says "RADV_FORCE_VRS_CONFIG_FILE is only applied to gfx10.3 APUs and is used by SteamOS." — [radv_device.c (mirror)](https://raw.githubusercontent.com/chaotic-cx/mesa-mirror/main/src/amd/vulkan/radv_device.c)

### Inferences
- **The closest prior art** to "downscale shadow maps or other passes by interception" is TBFix's low-precision shadow mode and FAR's GI workgroup reduction. Both are per-game, built from reverse-engineered knowledge of specific shaders and constant buffers. That fits DeckForge's Tier I "opt-in per game" model better than a "generic, automatic" claim.
- **Special K's shader-hash approach** (disable or replace a known pixel shader) is the most portable pattern for a layer. The layer can hash the SPIR-V that DXVK/vkd3d-proton hand to `vkCreateShaderModule` or pipeline creation. Caveat: hashes from a translator can change across DXVK/vkd3d-proton versions, so original DXBC/DXIL hashes would be more stable. That is speculative and needs checking.
- **Valve has not shipped quality-reducing per-game hacks** in RADV beyond the blanket VRS toggle. That suggests Valve sees per-game quality reduction as out of scope for the driver, which leaves room for a DeckForge-level tool.

### Gaps
- The Special K source for any D3D11/D3D12 shadow-resolution override was not inspected. Its wiki pages found cover only FAR's GI. Whether Special K has a generic render-target override for D3D12 is unconfirmed.
- No vkBasalt or ReShade feature for resizing game passes was found. Both are post-process only, but this is from absence of evidence.

## 3. Technical pitfalls of resizing render targets under the game: what a layer can detect or patch

### Takeaway
A layer sees every Vulkan call that DXVK and vkd3d-proton emit, so on paper it can substitute a smaller image and rescale viewport, scissor, render area and copy regions. Three things make this hard:
- **Descriptors are now written as raw bytes.** Both translators use `VK_EXT_descriptor_buffer` (and optionally `VK_EXT_descriptor_heap`), so a layer can only swap an image at `vkGetDescriptorEXT` time.
- **Shaders carry resolution assumptions** in constant buffers and absolute-coordinate loads. Fixing those means rewriting SPIR-V.
- **Compute passes encode resolution** in dispatch sizes and thread→pixel mapping, which needs shader-aware patching.

Raster depth-only passes (shadow maps) are the most tractable target. Compute-based effects (volumetrics, AO, SSR, GI) are generically intractable without per-shader knowledge.

### Cited Findings
- **vkd3d-proton descriptors.** vkd3d-proton recommends `VK_EXT_mutable_descriptor_type` and `VK_EXT_descriptor_buffer`. It has an `EXT_descriptor_heap` path behind a config flag. — [vkd3d-proton README](https://raw.githubusercontent.com/HansKristian-Work/vkd3d-proton/master/README.md); [device.c](https://raw.githubusercontent.com/HansKristian-Work/vkd3d-proton/master/libs/vkd3d/device.c)
- **DXVK descriptors.** DXVK enables `VK_EXT_descriptor_heap` and `VK_EXT_descriptor_buffer` on "known-good drivers" by default (Auto). The heap takes precedence when supported. — [dxvk.conf](https://raw.githubusercontent.com/doitsujin/dxvk/master/dxvk.conf)
- **yuzu precedent.** yuzu had to patch `ImageFetch`/`ImageRead` coordinates and `ImageQueryDimensions` for rescaled targets, and only for 2D and 2D-array images. — [yuzu commit](https://git.openpunk.com/OpenPunk/yuzu/commit/dfa82915262ca26d0884528b7bdae791554332ca)
- **Ryujinx precedent.** Ryujinx blacklisted scaling on CPU modification, on certain copies (2D→3D), and in some cases on compute use. — [Ryujinx commit](https://git.devminer.xyz/archive/Ryujinx/src/commit/484eb645ae0611f60fae845ed011ed6115352e06)
- **Cemu precedent.** Cemu applies overrides when the texture is created and resets contents. Unintended same-size matches are the main failure. — [Cemu wiki](https://wiki.cemu.info/wiki/Graphic_packs_creation)
- **Depth-only passes don't benefit from VRS.** AMD's guidance is that "depth-only passes… generally don't benefit" from VRS because they have no expensive pixel shader. — [GPUOpen VRS manual](https://gpuopen.com/manuals/fidelityfx_sdk/fidelityfx_sdk-page_techniques_variable-shading/)
- **Wilds shadow caching.** The Wilds Steam Deck config mod's changelog says it "Changed lines to disable shadow caching." So Wilds/RE Engine uses cached shadow maps, which means partial updates and copies. — [Nexus Mods "Little Engine that Shouldn't"](https://nexusmods.com/monsterhunterwilds/mods/183)

### Inferences (pitfall by pitfall, all reasoning, not tested)

**`textureSize` / `GetDimensions` (SPIR-V `OpImageQuerySize[Lod]`)**
- A smaller image returns its true smaller size, so shaders that derive texel size from it adapt by themselves.
- Many engines instead pass resolution or 1/size in constant buffers, which the layer cannot interpret semantically.
- Detect: yes, by scanning SPIR-V.
- Patch: only via SPIR-V rewriting.

**`texelFetch` / `Load` / `imageLoad` / `imageStore` with absolute coordinates (`OpImageFetch`/`OpImageRead`/`OpImageWrite`)**
- These read or write the wrong texels after a resize.
- Detect: yes.
- Patch: requires injecting a scale factor, as yuzu and Ryujinx do, via a push constant or extra binding. Under DXVK/vkd3d-proton that is non-trivial because the layer must preserve their pipeline layouts.

**Compute dispatch sizes**
- `vkCmdDispatch` group counts are sized for full res, and thread ID maps to pixel inside the shader.
- Shrinking the output means shrinking the dispatch and making every consumer agree.
- Constant-buffer-driven bounds checks will still use full-res values.
- Robust buffer/image access may silently drop out-of-bounds writes rather than crash, which turns into silent corruption.
- This is why FAR's GI change was a per-game workgroup knob, not a generic one.
- Detect: the dispatch, yes. The intent, no.

**PCF kernel offsets as constants**
- If offsets are in UV units (for example 1/2048), halving the map makes each offset half a texel.
- The filter footprint in UV and world space stays the same, so it is not broken. You get blockier, more aliased shadows rather than wrong ones.
- If offsets are in texel units via `textureOffset` or `Gather` offsets, the footprint doubles in world space, giving softer shadows.
- Either way it is not catastrophic for shadow maps that are sampled with normalized coordinates and comparison samplers.

**Viewport, scissor and render area**
- All are visible: `vkCmdSetViewport`/`Scissor` (dynamic in both translators), `VkRenderingInfo.renderArea` via dynamic rendering, and pipeline static state.
- Scaling them proportionally is easy, including shadow-atlas or cascade sub-rects, as long as the shader's atlas UV transforms are normalized.
- Depth bias (`vkCmdSetDepthBias`) is also visible. Slope-scaled bias tuned for the original resolution may give acne or peter-panning at lower res, so it may need adjusting.

**Aliased transient memory (D3D12 placed resources → `vkBindImageMemory2` at heap offsets)**
- The layer sees creation and binding.
- A smaller replacement image has a smaller memory requirement, so it can be bound at the same offset, or in layer-owned memory.
- D3D12 aliasing rules already make contents undefined on aliasing switches, so correctness risk is moderate.
- Aliasing barriers and initial layout transitions must be mirrored.

**Descriptor updates**
- With `vkUpdateDescriptorSets` the layer can swap `VkImageView`s.
- With descriptor buffers, the game-side translator calls `vkGetDescriptorEXT` (visible), then memcpys the bytes into mapped memory (invisible).
- So substitution is possible only as a permanent "this image is always the small one" decision at descriptor creation. Per-frame toggling is impractical.
- `VK_EXT_descriptor_heap` would need a separate code path.

**Barriers**
- Straightforward with handle substitution: subresource ranges are unchanged, extents are not part of barriers.

**Copies, blits and resolves between different sizes**
- `vkCmdCopyImage` regions are in texels and must be scaled.
- A copy between a shrunk image and a full-size one becomes a blit (`vkCmdBlitImage`) or a custom shader.
- Depth formats cannot always be blitted with linear filtering.
- Readbacks to buffers or the CPU (`vkCmdCopyImageToBuffer`) must either upscale or disable the substitution, which is Ryujinx's blacklist rule.
- Cached shadow maps (Wilds) imply incremental updates and copies with absolute rects. All must be caught.

**Other traps**
- Hi-Z or depth pyramids built by compute from a resized depth buffer.
- MSAA resolves.
- Images used both as render target and UAV.
- Typeless or format-reinterpreting views.
- Temporal history buffers that mix scaled and unscaled frames when the scale changes at runtime.

**Overall**
- Shadow maps are the best candidate: depth-only render passes into D16/D32 images, often square or atlas-shaped, later sampled with comparison samplers.
- They are identifiable by heuristic: depth-only attachment, not the swapchain size, consumed via a compare sampler.
- Expected gain from shrinking is limited to rasterization, depth bandwidth and ROP cost. Vertex cost is unchanged, and shadow passes are often vertex- or geometry-heavy (speculative).
- **Alternative location (strong inference).** Doing this inside a vkd3d-proton fork, which already owns dxil-spirv translation and descriptor heap emulation, would be far more tractable than an independent layer. The same applies to DXVK for D3D11.

### Gaps
- No public project was found that downscales passes generically below DXVK/vkd3d-proton, so none of the above has field evidence.
- Not verified which descriptor model (buffer or heap) vkd3d-proton and DXVK actually choose on the Deck's current SteamOS RADV.

## 4. Variable rate shading on Van Gogh / GFX10.3 under RADV

### Takeaway
RADV exposes `VK_KHR_fragment_shading_rate` on GFX10.3 (the Deck) with:
- pipeline and primitive rates always;
- attachment rates when HiZ/HTILE is in use, implemented by copying the rate image into the depth buffer's HTILE;
- 8×8 tiles and a maximum rate of 2×2.

Valve already ships a driver-level, UI-aware "force VRS" for the Deck (`RADV_FORCE_VRS_CONFIG_FILE`, enabled by default on Van Gogh and used by SteamOS). SteamOS exposes it as the "Half Rate Shading" toggle; that pairing is a strong inference, not stated by Valve. Measured gains on RDNA2 dGPUs were about 8% average at 4K in 2021, with best cases "upwards of 30%".

VRS cannot help shadow maps (depth-only) or compute passes (most volumetrics, AO, SSR, GI). Content-adaptive VRS in a layer is possible in principle but needs motion vectors and scene color that the layer cannot find generically.

### Cited Findings

**RADV capabilities (current Mesa main)**
- `.KHR_fragment_shading_rate = pdev->info.gfx_level >= GFX10_3`.
- `.pipelineFragmentShadingRate = true`, `.primitiveFragmentShadingRate = true`, `.attachmentFragmentShadingRate = radv_vrs_attachment_enabled(pdev)`, where that function returns `gfx_level >= GFX11 || pdev->use_hiz`.
- Attachment texel size is fixed at 8×8.
- `fragmentShadingRateNonTrivialCombinerOps = true`.
- Supported rates are 1×1, 1×2, 2×1 and 2×2 only. There are no 4×4 rates, and coarse rates are not offered with 8× MSAA.
- [radv_physical_device.c (mirror)](https://raw.githubusercontent.com/chaotic-cx/mesa-mirror/main/src/amd/vulkan/radv_physical_device.c)

**How attachment VRS works on GFX10.3**
- "When we have a VRS attachment and a depth/stencil attachment, we just need to copy the VRS rates to the HTILE buffer."
- Without a depth attachment, RADV binds "our internal depth buffer that contains the VRS data as part of HTILE."
- [radv_cmd_buffer.c (mirror)](https://raw.githubusercontent.com/chaotic-cx/mesa-mirror/main/src/amd/vulkan/radv_cmd_buffer.c)

**Force-VRS heuristics in RADV**
- The per-vertex rate is injected only when the position output's W "can't be determined or if its value is != 1 (typical for non-GUI elements)." In practice: 3D perspective geometry gets VRS, flat 2D/UI does not.
- It is disabled when the fragment shader can discard or reads `gl_FragCoord`: "Do not enable if the PS uses gl_FragCoord because it breaks postprocessing in some games." It is also disabled for sample shading, sample mask and interlock.
- [radv_shader_info.c (mirror)](https://raw.githubusercontent.com/chaotic-cx/mesa-mirror/main/src/amd/vulkan/radv_shader_info.c)
- Force VRS is also skipped:
  - with 8× MSAA or sample shading;
  - when the app already uses static VRS;
  - for mesh shaders;
  - when the shader already writes a primitive shading rate;
  - when there is no pixel shader.
  - [radv_pipeline_graphics.c (mirror)](https://raw.githubusercontent.com/chaotic-cx/mesa-mirror/main/src/amd/vulkan/radv_pipeline_graphics.c)

**The Steam Deck config-file mechanism (Valve)**
- Code comment: "RADV_FORCE_VRS_CONFIG_FILE is only applied to gfx10.3 APUs and is used by SteamOS. RADV_FORCE_VRS is mainly for testing."
- The file is watched with inotify and re-read on change, so the rate can change at runtime without restarting the game.
- [radv_device.c (mirror)](https://raw.githubusercontent.com/chaotic-cx/mesa-mirror/main/src/amd/vulkan/radv_device.c)
- MR 14713 by Samuel Pitoiset (Valve) is described as "For power saving." It is "enabled by default on VanGogh." Pitoiset is "not a real fan of the inotify solution." — [Mesa MR 14713](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/14713)
- Phoronix, Jan 26, 2022: Valve's Pitoiset posted patches so "it's now possible to force per-vertex VRS dynamically by writing eg. 2x2 via RADV_FORCE_VRS_CONFIG_FILE." Previously rates were hardcoded in vertex shaders. Purpose: power savings on Van Gogh. — [Phoronix](https://www.phoronix.com/news/RADV-Dynamic-VRS)
- A draft MR adds `enable_with_discard` and `enable_with_frag_coord` config-file options "to hopefully allow more per-game VRS tuning." Still a draft. — [Mesa MR 16471](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/16471)
- Mesa docs: `RADV_FORCE_VRS` forces "per-pipeline vertex VRS rates on GFX10.3+… Only for testing purposes." `RADV_FORCE_VRS_CONFIG_FILE` "supersedes" it and "only affects GFX10.3 APUs." `RADV_DEBUG=novrsflatshading` disables VRS for flat shading. — [Mesa envvars](https://docs.mesa3d.org/envvars.html)

**Steam Deck "Half Rate Shading" (user-facing)**
- SDHQ (Jan 7, 2023): HRS "will apply a Variable Rate Shading that is designed to save on power" and "will half the shading quality while in-game." — [SDHQ encyclopedia](https://steamdeckhq.com/tips-and-guides/the-sdhq-performance-settings-encyclopedia/)
- overkill.wtf (Aug 20, 2022): "a brute-force method… no matter the content," "meant to save battery life but not necessarily improve performance." — [overkill.wtf](https://overkill.wtf/how-to-graphic-settings-steam-deck)
- A game developer (Jan 22, 2024) warned that HRS "can sometimes lead to some unexpected graphical quirks, such as pixelated texts." — [Steam Community, Against the Storm](https://steamcommunity.com/app/1336490/discussions/0/4137186611109115317/)

**Measured VRS gains on RDNA2 (older, 2021)**
- Phoronix, Apr 12, 2021: RADV VRS 2×2 on RX 6700 XT, 6800 and 6800 XT at 4K (Mesa 21.1-devel). "came out 8% faster overall," with "very sizable" gains in Talos Principle and "minor visual quality loss." — [Phoronix review p1](https://www.phoronix.com/review/radeon-radv-vrs); [p4](https://www.phoronix.com/review/radeon-radv-vrs/4)
- Phoronix news, Apr 10, 2021: "upwards of 30%" performance, RDNA2 only, credited to Bas Nieuwenhuizen. Warns "gamers will likely notice the lower quality visuals." — [Phoronix](https://www.phoronix.com/news/RADV-Render-Less)

**2026 RADV VRS work**
- Marek Olšák (Valve) rewrote RADV VRS state across 22 patches (MR 42242, Mesa 26.2, Aug 2026).
- The VRS flat-shading optimization can now be enabled when VRS is dynamic or static in the pipeline. This "mainly benefits VKD3D," and gains still require flat-shaded fragment shaders.
- July 6, 2026. — [Phoronix](https://phoronix.com/news/Marek-Double-VRS-RADV-Perf)

**vkd3d-proton D3D12 VRS tiers**
- Tier 1 needs `pipelineFragmentShadingRate` plus 2× sample support.
- Tier 2 needs non-trivial combiner ops, attachment FSR, primitive FSR and a tile size of 8, 16 or 32.
- A code comment notes RADV lacks `fragmentShadingRateWithShaderSampleMask`, but "lots of content relies on TIER_2," so vkd3d-proton "just allow[s] non-compliant VRS for now."
- [vkd3d-proton device.c](https://raw.githubusercontent.com/HansKristian-Work/vkd3d-proton/master/libs/vkd3d/device.c)

**AMD FidelityFX Variable Shading**
- Open source, MIT license. "Analyzes luminance variance in the previous frame" and uses motion vectors. RDNA2-optimized, HLSL with SM6 wave ops, D3D12 Ultimate and Vulkan. — [GPUOpen FidelityFX VS](https://gpuopen.com/fidelityfx-variable-shading/)
- Algorithm, per the SDK v1.1.4 source (MIT header):
  1. Read previous-frame luminance, reprojected by motion vector.
  2. Per 2×2 coarse pixel, compute horizontal (2×1), vertical (1×2) and min/max (2×2) luminance deltas.
  3. Subtract `length(motionVector) * MotionFactor` ("reduce variance value for fast moving pixels").
  4. Widen with neighbour min/max.
  5. Take the max over the VRS tile with `WaveActiveMax`/`subgroupMax`.
  6. Choose 2×2 if `delta.z < VarianceCutoff`, else 2×1 or 1×2 per axis, else 1×1. Additional-rates builds go up to 4×4.
  - [ffx_variable_shading.h](https://raw.githubusercontent.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/v1.1.4/sdk/include/FidelityFX/gpu/vrs/ffx_variable_shading.h)
- AMD guidance: "VRS does not reduce the amount of pixels which get written to the rendertargets, fillrate will not get reduced." Depth-only passes generally don't benefit. Decals and soft particles may see larger depth differences. Centroid interpolation is recommended. — [GPUOpen VRS manual](https://gpuopen.com/manuals/fidelityfx_sdk/fidelityfx_sdk-page_techniques_variable-shading/)

**Wilds has its own VRS setting**
- MSI's guide recommends "Variable Rate Shading (Off): only enable if the PC still struggles… makes shading grainy." — [MSI guide](https://www.msi.com/blog/rtx-50-benchmarks-monster-hunter-wilds-best-setting-guide)
- PCOptimizedSettings puts VRS in its "<1.5%" impact band on an RTX 4090 test system. — [PCOptimizedSettings](https://pcoptimizedsettings.com/monster-hunter-wilds-pc-optimization-best-settings-benchmarks/)

### Inferences
- **Support levels on the Deck:**
  - Pipeline: yes.
  - Primitive: yes.
  - Attachment: yes while HiZ is on (the default unless `RADV_DEBUG=nohiz`), emulated through an HTILE copy at the start of each render pass. That copy is extra work per pass. Its cost was not measured anywhere found.
- **Wilds' own VRS on the Deck.** vkd3d-proton's Tier 2 conditions look satisfiable on GFX10.3 with HiZ: attachment, primitive, non-trivial combiners, and an 8-px tile in the valid set. So Wilds' VRS option may work on the Deck.
  - Being game-provided, it is a Tier S lever and should be benchmarked before building anything.
  - With Mesa 26.2's change, game-driven VRS under vkd3d-proton may also get the flat-shading optimization.
  - Both are unverified.
- **Can a layer apply VRS only to 3D scene passes, not UI?** Yes. RADV already does exactly this at driver level with the W≠1 heuristic and the discard/`FragCoord` exclusions.
  - A DeckForge layer could do a stricter version: add `VkPipelineFragmentShadingRateStateCreateInfoKHR` only to pipelines in render passes whose color attachments are not the swapchain or UI-composition targets, or call `vkCmdSetFragmentShadingRateKHR` per render pass.
  - But duplicating the driver's force-VRS gives little new value.
- **Content-adaptive VRS is the real delta.** It needs:
  - an identified motion-vector target (typically R16G16_FLOAT at render res written in the G-buffer pass);
  - previous-frame scene color before UI;
  - per-frame classification compute at render resolution, plus the HTILE copy on GFX10.3.
  - Identifying the motion-vector and color targets generically is heuristic. A per-game allowlist is realistic. Speculative.
- **Expected gain on the Deck is modest:**
  - Wilds is deferred; lighting and many effects are compute.
  - Shadows are depth-only.
  - VRS max is 2×2.
  - At 800p or lower internal resolution, pixel-shading share is smaller than at 4K.
  - Phoronix's 8% average was measured at 4K on dGPUs.
  - A plausible Deck-at-800p range is low single digits to about 10% where G-buffer or forward pixel shading dominates. This is speculative and needs bench data.
- **Valve's experiment:** per-vertex VRS forced at runtime through a watched file, aimed at power savings on Van Gogh, with heuristics to keep UI and post-process sharp. Per-game tuning options (discard/`FragCoord`) were drafted but remain a draft.

### Gaps
- No measured Half Rate Shading fps or power numbers on the Deck were found.
- Not confirmed whether the Half Rate Shading toggle still exists in current SteamOS; a 2024 user could not find it by name.
- No public Deck or RADV measurement of Wilds' own VRS option, and not confirmed that vkd3d-proton reports Tier 2 on the Deck. Needs a `CheckFeatureSupport` trace or vkd3d log.
- Not established which Mesa version SteamOS stable ships as of Oct 2026, so it is unknown whether Marek's Mesa 26.2 VRS changes are on Decks yet.
- Cost of RADV's VRS-image→HTILE copy on GFX10.3 is unmeasured.

## 5. Per-pass GPU cost breakdowns for modern engines, RE Engine and Monster Hunter Wilds

### Takeaway
No public per-pass GPU breakdown of Monster Hunter Wilds was found: no RGP, Nsight or RenderDoc capture with timings, and no Digital Foundry pass analysis. What exists:
- per-setting cost bands on a CPU-bound RTX 4090, where no single setting is above 2%;
- qualitative guides calling volumetric fog a "performance hog";
- Deck reports that at the lowest settings Wilds runs high-teens to about 30 fps and is mainly GPU-bound;
- a Deck mod author reporting that GI and volumetric-fog reductions via REFramework give "significant gains."

Wilds' per-pass costs on Van Gogh have to be measured by DeckForge itself, for example via RGP capture on the bench Deck.

### Cited Findings
- **Per-setting bands (RTX 4090 + i9-12900K).**
  - "1.5–2%" uplift each when set to lowest: shadow quality, volumetric fog, AO, SSR, render distance, ambient light, mesh quality.
  - "<1.5%": distant shadows, sky, grass/tree, sand/snow, fur, VRS, contact shadows.
  - "no single setting affects performance by more than 2%."
  - [PCOptimizedSettings](https://pcoptimizedsettings.com/monster-hunter-wilds-pc-optimization-best-settings-benchmarks/)
- **Qualitative guidance** (MSI, no per-setting numbers): volumetric fog "another performance hog"; AO "a very small performance hit"; sand/snow impact "very noticeable"; lowest shadow setting "doesn't give you much of a performance improvement"; render distance "a great way to get more performance"; VRS makes shading grainy. — [MSI guide](https://www.msi.com/blog/rtx-50-benchmarks-monster-hunter-wilds-best-setting-guide)
- **PC Games Hardware.** Per reader comments quoting the article (the benchmark pages were not in the fetched text): Wilds "fordert die CPU sehr intensiv" (is very CPU-heavy); 10–12 GB VRAM advisable even for reduced 1080p; storm weather affects performance. — [PCGH](https://www.pcgameshardware.de/Monster-Hunter-Wilds-Spiel-74697/Specials/Release-PC-Preload-Review-Benchmark-1466495/)
- **Digital Foundry (via Gameranx, Mar 4, 2025):** very low-quality textures regardless of setting; camera-rotation stutter on high settings; advised 8 GB-VRAM and low-spec owners not to buy yet. — [Gameranx](https://gameranx.com/updates/id/531237/article/digital-foundry-explains-monster-hunter-wilds-pc-performance-issues/)
- **SDHQ on the Deck (Jan 28, 2026, post-1.040 patch), at "the lowest possible settings":**
  - Open areas "sits in the high teens or low 20s".
  - Windward Plains below 20 near the watering hole; Scarlet Forest mid-20s; Oilwell Basin around 30.
  - New GPU options had "almost no effect."
  - "the issue on the Steam Deck is more related to the GPU than the CPU."
  - A Feb 18 patch was expected to bring GPU optimizations.
  - [SDHQ](https://steamdeckhq.com/news/monster-hunter-wilds-1040-performance/)
- **Notebookcheck (Jan 30, 2026):** "roughly playable at ~30 FPS, no Frame Generation needed" with FSR or XeSS. Patch optimized shader compilation and texture streaming; minimum fps up about 8% vs Title Update 4 (per Daniel Owen). — [Notebookcheck](https://www.notebookcheck.net/Monster-Hunter-Wilds-fixes-DLC-bug-greatly-reduces-FPS-drops-and-runs-at-30-FPS-on-Steam-Deck.1215270.0.html)
- **Earlier (Mar 17, 2025):** Deck users reported sub-30 fps. The "Little Engine that Shouldn't" config targets about 30 fps with frame generation, or close to 30 at 1024×640 with Lite Environment and no frame generation. — [Destructoid](https://destructoid.com/steam-deck-users-enjoy-monster-hunter-wilds-at-sub-30-fps)
- **The Wilds Deck mod page.**
  - Config disables shadow caching and reduces texture filtering.
  - With REFramework, "Lite Environment" GI and volumetric fog settings "net significant gains"; disabling wind simulation gives "a few frames"; foliage and leaf LOD bias gives "a couple more frames."
  - The author claims "around 30–45fps" at 1280×800 Quality, 1600×900 Balanced, or 1024×640 native.
  - No per-change numbers.
  - [Nexus Mods #183](https://nexusmods.com/monsterhunterwilds/mods/183)
- **Generic AAA example (Chips and Cheese, Starfield, Sep 14, 2023, 4K):**
  - About 6,800 events per frame.
  - The longest single dispatch is "just over 1.1 ms" and the longest pixel shader 0.93–1.18 ms, against frames of 18.1 ms (4090) and 20.2 ms (7900 XTX).
  - So individual passes are about 5–6% each. Costs are spread across many calls.
  - Profiled with RGP and Nsight.
  - [Chips and Cheese](https://chipsandcheese.com/p/analyzing-starfields-performance-on-nvidias-4090-and-amds-7900-xtx)
- **Van Gogh GPU (Chips and Cheese, LCD-model Deck):**
  - 512 FP32 lanes (4 WGPs) up to 1.6 GHz.
  - 88 GB/s theoretical from LPDDR5-5500, "over 70 GB/s" measured by the GPU.
  - 1 MB L2, no Infinity Cache, very poor GPU DRAM latency.
  - 16 W APU cap shared with the CPU; a GPU-bound sequence can pull over 10 W on the GPU.
  - [Chips and Cheese Van Gogh](https://chipsandcheese.com/p/van-gogh-amds-steam-deck-apu)

### Inferences
- **The 4090 bands understate GPU-side pass costs.** The 4090 test is likely CPU-bound (PCGH says the game is CPU-heavy), so those bands are not usable as GPU per-pass shares on the Deck.
- **On the Deck the game is GPU-bound at the lowest preset.** Remaining costs are what the lowest preset still renders: G-buffer, lighting, residual fog and GI, shadows and upscaling.
- **Volumetric fog and GI are the most likely reallocation targets** for Wilds on the Deck. Two independent signals point there: the REFramework "Lite Environment" GI and fog gains, and fog being "a performance hog". This is indicative, not measured.
- **The 45 fps target is a big ask.** Going from about 20 fps (50 ms) to 45 fps (22.2 ms) needs about 55% less frame time. Going from about 30 fps (33.3 ms) needs about 33% less.
  - Section 3 suggests generic per-pass downscaling cannot reach that for Wilds.
  - Even with the Tier I REFramework tweaks, the mod author claims 30–45 fps, not a locked 45.
  - A locked native 45 fps in Wilds' open areas looks unrealistic on the Deck. A locked 30, or about 40 in lighter areas, is a more honest target. Speculative pending bench data.
- **Bandwidth amplifies the payoff of shrinking targets.** Van Gogh shares 88–102 GB/s with the CPU and has no Infinity Cache, so bandwidth-heavy full-screen passes (fog, SSR, AO at render res) cost relatively more than on dGPUs. Shrinking intermediate targets therefore saves proportionally more there than VRS does, since VRS does not cut render-target writes. Inference.

### Gaps
- No Wilds or RE Engine per-pass timing data (RGP, Nsight, PIX, RenderDoc) found publicly.
- No Capcom RE Engine talk with Wilds pass budgets found (CEDEC or docswell searches returned nothing relevant).
- No Digital Foundry Deck analysis of Wilds found.
- Unknown whether the Feb 18, 2026 patch or later updates materially changed Deck GPU performance.

## 6. Per-pass timing from a layer: timestamps, debug labels, RGP

### Takeaway
Per-render-pass timestamps from a layer are feasible on RADV. `vkCmdWriteTimestamp2` (bottom of pipe) is an end-of-pipe event write that does not force a full pipeline drain by default, but it does flush pending barrier work at that point. Attribution is approximate where work overlaps (async compute, adjacent passes).

Names for passes are not available by default:
- DXVK forwards application markers only with `DXVK_DEBUG=markers`; `DXVK_DEBUG=capture` adds its own internal render-pass and shader names.
- vkd3d-proton emits debug-utils labels (from PIX `BeginEvent` and pipeline state binds) only with its debug-utils config flag.
- Whether Wilds' retail build emits PIX events is unknown.

For offline analysis, RGP capture via `MESA_VK_TRACE=rgp` with a trigger file is the strongest tool. vkd3d-proton also has a per-PSO timestamp profiler, but only in profiling builds.

### Cited Findings
- **RADV `vkCmdWriteTimestamp2`:**
  - Calls `radv_emit_cache_flush`, then writes the timestamp with an end-of-pipe `BOTTOM_OF_PIPE_TS` event, or `COPY_DATA` for `TOP_OF_PIPE`.
  - A per-game drirc option `flush_before_timestamp_write` adds a full VS/PS/CS sync "to make sure previously launched waves have finished."
  - [radv_query.c (mirror)](https://raw.githubusercontent.com/chaotic-cx/mesa-mirror/main/src/amd/vulkan/radv_query.c); [00-radv-defaults.conf](https://raw.githubusercontent.com/chaotic-cx/mesa-mirror/main/src/amd/vulkan/00-radv-defaults.conf)
- **DXVK markers.** `DXVK_DEBUG=capture` "Enables dxvk-internal debug names and debug markers for render passes, shaders, etc." `DXVK_DEBUG=markers` "Uses VK_EXT_debug_utils to forward application-provided resource names and debug markers." — [DXVK README](https://raw.githubusercontent.com/doitsujin/dxvk/master/README.md)
- **DXVK debug utils off by default.** `dxvk.enableDebugUtils = False` by default: "this enables user annotations like BeginEvent()/EndEvent()." — [dxvk.conf](https://raw.githubusercontent.com/doitsujin/dxvk/master/dxvk.conf)
- **vkd3d-proton labels.** It emits `vkCmdBeginDebugUtilsLabelEXT` and decodes PIX event payloads (`ePIXEvent_BeginEvent_*`) only when `VKD3D_CONFIG_FLAG_IS_SET(DEBUG_UTILS)` and `EXT_debug_utils` is available. It also labels pipeline state binds under the same flag. — [vkd3d-proton command.c](https://raw.githubusercontent.com/HansKristian-Work/vkd3d-proton/master/libs/vkd3d/command.c)
- **vkd3d-proton timestamp profiler.**
  - Copyright 2025 Hans-Kristian Arntzen for Valve.
  - Hooks pipeline-state set, pre-command marks, render-pass end, command-buffer end, submit and frame boundary.
  - Compiled only with `VKD3D_ENABLE_PROFILING`, using `-Denable_profiling=true` and `VKD3D_PROFILE_PATH`.
  - [vkd3d_timestamp_profiler.h](https://raw.githubusercontent.com/HansKristian-Work/vkd3d-proton/master/libs/vkd3d/vkd3d_timestamp_profiler.h); [README](https://raw.githubusercontent.com/HansKristian-Work/vkd3d-proton/master/README.md)
- **vkd3d-proton breadcrumbs.** `VKD3D_CONFIG=breadcrumbs` instruments command lists with `VK_AMD_buffer_marker` for crash debugging, in non-release builds. — [vkd3d-proton README](https://raw.githubusercontent.com/HansKristian-Work/vkd3d-proton/master/README.md)
- **RADV RGP/SQTT tooling:**
  - `MESA_VK_TRACE` (trace types including rgp, dumped to /tmp).
  - `MESA_VK_TRACE_TRIGGER` ("Creating the file triggers the capture").
  - `MESA_VK_TRACE_PER_SUBMIT`.
  - `RADV_THREAD_TRACE_BUFFER_SIZE` (default 32 MiB), instruction timing and cache counters.
  - `RADV_PROFILE_PSTATE` (default `peak` clocks during tracing).
  - `RADV_SPM_COUNTERS_CONFIG`.
  - [Mesa envvars](https://docs.mesa3d.org/envvars.html)
- **Scale of attribution.** Chips and Cheese profiled about 6,800 events per Starfield frame with RGP and Nsight, examining only the longest calls because per-event analysis was "impractical." — [Chips and Cheese](https://chipsandcheese.com/p/analyzing-starfields-performance-on-nvidias-4090-and-amds-7900-xtx)

### Inferences
- **Layer design:**
  - Wrap each `vkCmdBeginRendering`/`vkCmdEndRendering` pair, and coalesced runs of `vkCmdDispatch`, with `vkCmdWriteTimestamp2` at `ALL_COMMANDS`/bottom-of-pipe.
  - Use per-frame ring-buffered query pools and read results 2–3 frames later without `WAIT_BIT`, to avoid CPU stalls.
  - Key passes by attachment formats and extents, pipeline or shader hash, and dispatch dims, since names are unavailable.
  - A few hundred timestamps per frame is likely sub-millisecond overhead on RADV, given EOP events and no drain. This is speculative and must be measured on the Deck, and the earlier barrier flush could perturb overlap.
- **Better for discovery:** run a profiling build of vkd3d-proton (per-PSO timestamps) or RGP captures on the bench Deck. Use the in-layer timer only for runtime adaptation, such as toggling a downscale when frame time exceeds budget.
- **Repo-rule constraint.** Both RGP and profiled vkd3d-proton involve the real Deck, so under CLAUDE.md R7 they are bench-runner-phase activities, not dev-session ones.

### Gaps
- No published measurement of timestamp-query overhead on RADV or Van Gogh.
- Unknown whether Wilds' retail D3D12 build emits PIX `BeginEvent` markers that would give pass names via `VKD3D_CONFIG=debug_utils`.
- The exact config-flag spelling for vkd3d-proton debug utils was not confirmed in the README; only the code-level flag `DEBUG_UTILS` was seen.

## 7. Anti-cheat: does a Vulkan layer count as injection?

### Takeaway
No authoritative public statement was found on whether Easy Anti-Cheat or BattlEye on Proton flag third-party Vulkan layers. A Vulkan layer is a native shared library loaded into the game process that can alter rendering, so it is functionally injection. Treating it as Tier I (never for Helldivers 2 / GameGuard or Space Marine 2 / EAC), as DeckForge's CLAUDE.md already does, is the defensible stance. Precedent from ReShade (disables add-ons on network activity) points the same conservative way.

### Cited Findings
- **Valve's Proton anti-cheat guidance.** EAC under Proton ships a Linux library (`libeasyanticheat.so` renamed to `easyanticheat_x64.so`) next to the Windows DLL. "Kernel-space solutions are not currently supported," and user-space components "can typically run in the Wine environment." No mention of overlays or Vulkan layers. — [Steamworks Proton docs](https://partner.steamgames.com/doc/steamdeck/proton)
- **ReShade.** The signed build "will not load add-ons itself" so that add-ons go through the same loading paths anti-cheat already watches. ReShade "completely disables its add-on capabilities" when it detects network traffic, as with depth-buffer access. This is crosire's stated plan, about four years old. — [ReShade forum](https://reshade.me/forum/general-discussion/7584-some-concerns-about-reshade-5-0-extended-functionality)
- **The Deck's own overlay.** The Steam Deck performance overlay is MangoApp, used with gamescope ("any time you see the performance overlay in the corner on a Steam Deck, that's it in action"). Aug 1, 2022. — [GamingOnLinux](https://www.gamingonlinux.com/2022/08/linux-gaming-overlay-mangohud-version-068-out-now/page=1/)

### Inferences
- **Same process as EAC.** Under Proton the game process loads the native Vulkan loader, then layers, then RADV. EAC's Linux component runs in user space in that same process. Whether it inspects loaded `.so` modules or Vulkan layer manifests is undocumented.
- **Valve's own components are no precedent.** Valve-shipped layers and overlays (gamescope's WSI layer, MangoApp) run alongside EAC games on the Deck, but third-party layers that modify rendering are a different risk class.
- **Shader rewriting looks like cheating tools.** A layer that rewrites shaders or substitutes depth or shadow images is technically similar to wallhack tooling, which removes or changes shadow and fog passes. Anti-cheat vendors have strong incentives to flag it. Space Marine 2 (EAC) and similar titles should stay Tier S only.
- **Wilds is not in that class.** Wilds is not known to use kernel or online anti-cheat. REFramework mods are widely used with it, per the Nexus mod. That makes Wilds a reasonable Tier I opt-in candidate, though Capcom's EULA or DRM stance on modification was not researched.

### Gaps
- No primary source (Epic EAC docs, BattlEye, Valve) on Vulkan-layer detection or bans under Proton.
- No reports found, positive or negative, of bans tied to vkBasalt, MangoHud or custom layers in EAC titles.
- Wilds' DRM or anti-tamper posture was not researched.

## 8. Overall feasibility and realistic gains (synthesis across the questions above)

### Takeaway
A fully generic, automatic layer that cheapens shadows, volumetrics, AO, SSR and GI across games is not supported by any prior art. It is technically high-risk:
- compute-based effects need shader rewriting;
- descriptor buffers and heaps limit image substitution;
- every emulator and PC mod that did selective pass scaling fell back to per-game rules.

The realistic path, in order:
1. Tier S game-provided levers, including Wilds' own VRS option and low fog/GI settings, measured on the Deck.
2. Driver-level VRS that already exists (`RADV_FORCE_VRS_CONFIG_FILE`, Half Rate Shading).
3. Per-game Tier I targets: REFramework for Wilds; later a layer with per-game shader-hash and image-signature allowlists, starting with shadow-map resolution.

For Wilds on the Deck, a locked native 45 fps looks out of reach. Public data puts lowest-settings performance at high-teens to about 30 fps in open areas, GPU-bound.

### Cited Findings
- **Wilds on the Deck is GPU-limited at the lowest settings** (high-teens to low-20s fps in open areas, about 30 fps in quiet or interior areas). — [SDHQ](https://steamdeckhq.com/news/monster-hunter-wilds-1040-performance/)
- **Tier I REFramework tweaks** (GI and volumetric fog) give "significant gains"; the author claims 30–45 fps at 1280×800 Quality. — [Nexus Mods #183](https://nexusmods.com/monsterhunterwilds/mods/183)
- **Valve already ships content-blind VRS for Van Gogh** with UI and post-process safeguards. — [radv_device.c](https://raw.githubusercontent.com/chaotic-cx/mesa-mirror/main/src/amd/vulkan/radv_device.c); [radv_shader_info.c](https://raw.githubusercontent.com/chaotic-cx/mesa-mirror/main/src/amd/vulkan/radv_shader_info.c)
- **RDNA2 VRS 2×2 averaged about 8% at 4K** (2021). — [Phoronix](https://www.phoronix.com/review/radeon-radv-vrs/4)
- **Per-pass shrinking precedents are per-game:** FAR GI workgroups, TBFix shadows, Cemu, Dolphin and PCSX2 per-game fixes. — [Special K wiki](https://wiki.special-k.info/SpecialK/Custom/FAR); [GamePressure TBFix](https://www.gamepressure.com/download/tales-of-berseria-tales-of-berseria-fix-v01012-mod/z810abd); [Cemu wiki](https://wiki.cemu.info/wiki/Graphic_packs_creation)

### Inferences
- **Ranked feasibility for a DeckForge layer:**
  1. **Measurement (high feasibility).** Per-render-pass and per-dispatch GPU timestamps keyed by attachment and dispatch signature. Useful on its own for evidence-driven tuning.
  2. **Pipeline-level VRS on scene passes (medium-high feasibility, low gain).** Largely duplicates the driver's force-VRS. The only extra value is per-pass targeting via the frame graph.
  3. **Shadow-map downscale by image substitution, per-game allowlisted (medium feasibility, small-to-moderate gain, Tier I).** Needs viewport, scissor, render-area, copy-region and depth-bias rescaling, plus substitution at `vkGetDescriptorEXT` time. Wilds' shadow caching adds copy-tracking complexity.
  4. **Content-adaptive VRS, FidelityFX-style (medium-low feasibility).** Needs per-game identification of the motion-vector and scene-color targets. MIT-licensed reference code exists.
  5. **Compute-effect downscale for fog, AO, SSR or GI (low feasibility generically).** Requires SPIR-V rewriting of thread→pixel mapping and consumer coordinate scaling. Only realistic per shader hash, like FAR. Better done inside a vkd3d-proton fork, or via REFramework for RE Engine games.
- **Rough per-technique gain guesses for Wilds on the Deck, all speculative pending RGP data:**

  | Technique | Guessed frame-time reduction |
  |---|---|
  | VRS | 0–8% |
  | Shadow-map halving beyond the lowest preset | 2–8% |
  | Fog/GI reductions (REFramework-type, already partly available as a mod) | 5–20% |

  Combined, these probably cannot close the 33–55% frame-time gap to a locked native 45 fps in open areas.
- **What to keep at 800p.** Intuitively, keep budget on what survives the final 1280×800 output: upscaler input resolution, texture and material detail, and geometry or LOD in the near field. Cut low-frequency, temporally accumulated effects: fog, GI, AO, distant shadows. This is design reasoning; no source measured perceptual impact on the Deck's 7.4" OLED.

### Gaps
- No measured per-pass Deck data for Wilds. The first concrete next step is a bench-phase RGP capture at the lowest preset in Windward Plains, to replace the speculative gain table above.
- Untested: whether Wilds' in-game VRS works under vkd3d-proton on the Deck, and what it gains.
- No field test of any third-party layer doing image substitution under vkd3d-proton's descriptor-buffer or descriptor-heap model.
