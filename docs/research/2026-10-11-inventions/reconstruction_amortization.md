# Cheap image reconstruction and temporal amortization for Steam Deck OLED (research notes, current to 2026-10-11)

Labels used below: **[measured]** means someone reported a timing they took themselves (usually a community measurement, not independently verified). **[claimed]** means a vendor or author statement with no published numbers. **(older, YYYY)** marks findings from before 2025. Frame budget reference: 45 fps = 22.2 ms.

## 1. Mobile-oriented temporal upscalers (Arm ASR, Qualcomm GSR, Arm NSS): license, cost, injectability

### Takeaway
None of the mobile upscalers would give better image quality per millisecond on the Deck than what we can already run.
- **Arm ASR** is FSR 2.2.2 tuned for cost. Its Quality preset is designed to match FSR2 image quality, not beat it.
- **Qualcomm GSR 2** is a simpler TAAU (convert pass, Lanczos upscale, optional sharpen) aimed at about 1–2 ms on phones.
- **Arm NSS** is the only new learned design. It needs Vulkan ML extensions that the Deck's driver does not have, and Arm's own cost target is about 4 ms on future phone neural accelerators.

ASR and GSR are permissively licensed (MIT and BSD-3), so we could legally use them. OptiScaler does not ship either as a backend today. I found no measurements of any of the three on RDNA2 or the Deck.

### Cited Findings
- **Arm ASR origin and license.** Derived from AMD FidelityFX Super Resolution 2 v2.2.2 with Arm-specific mobile optimizations; MIT license; released 10 Jul 2024 (older, 2024). — [GitHub arm/accuracy-super-resolution](https://github.com/arm/accuracy-super-resolution); [Arm blog, Introducing Arm ASR](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/introducing-arm-accuracy-super-resolution)
- **ASR presets and design.**
  - The Quality preset is described as "ultra-optimized FSR2 with ~100% image-quality match."
  - There are three shader-quality presets (Quality, Balanced, Performance), set independently of the upscale ratio.
  - Explicit FP16 covers about 77.67% of shaders, and all register spilling was removed.
  - Inputs are jittered color, depth, motion vectors and an optional reactive mask, the same as FSR2.
  - Source: [Vulkanised 2025, Sergio Alapont (Arm)](https://vulkan.org/user/pages/09.events/vulkanised-2025/T24-Sergio-Alapont-Arm-ArmASR.pdf)
- **ASR cost.** The FSR2-vs-ASR timing and bandwidth comparisons (Immortalis-G720, 2400×1080 and 1600×720 targets) exist only as charts. The text gives no ms values. — [Vulkanised 2025 slides](https://vulkan.org/user/pages/09.events/vulkanised-2025/T24-Sergio-Alapont-Arm-ArmASR.pdf); [Arm blog](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/introducing-arm-accuracy-super-resolution)
- **ASR integration paths.** Unreal Engine 5.3–5.5 plugin and a generic library; "upscale ratio 50.0 = 2×". — [Arm Learning Path](https://learn.arm.com/learning-paths/mobile-graphics-and-gaming/get-started-with-arm-asr/01-what-is-arm-asr/)
- **Snapdragon GSR license and versions.**
  - BSD 3-Clause.
  - SGSR 1 is a single spatial pass: a 12-tap Lanczos-like filter plus adaptive sharpening, taking one input texture.
  - SGSR 2 is temporal, aimed at Adreno GPUs.
  - Releases: 1.0.0 (2023-06-29), 1.1.0 (2024-01-29), 2.0.0 (2024-10-21).
  - Source: [GitHub SnapdragonGameStudios/snapdragon-gsr](https://github.com/SnapdragonGameStudios/snapdragon-gsr)
- **GSR 2 design and cost [claimed].**
  - Passes: a convert pass (motion and depth-clip buffers), a "highly optimized Lanczos upscale", and an optional sharpen pass.
  - Inputs: low-resolution color, depth and motion vectors.
  - A fragment-shader variant runs at about 1 ms on Adreno after optimization.
  - Target is under 2 ms on Snapdragon 8 Gen 3 at maximum GPU clock at 1260×2800, and up to about 8 ms at the lowest GPU clock.
  - No comparison with FSR2 is given.
  - Source: [ProAndroidDev, Jan 2025](https://proandroiddev.com/enhance-your-game-graphics-with-snapdragon-game-super-resolution-2-8484598b1391)
- **Qualcomm Adreno Neural Fusion SDK (Sep 2026).** Announced as "AI-powered super resolution and frame generation on Snapdragon." The page gave no license, cost or architecture details. — [Qualcomm blog, 2026/09](https://www.qualcomm.com/developer/blog/2026/09/introducing-adreno-neural-fusion-sdk-for-snapdragon-mobile-platforms)
- **Arm NSS architecture (Aug 2025).**
  - Parameter-prediction network on a 4-level UNet. Per pixel it outputs a 4×4 filter kernel, temporal accumulation and rectification coefficients, and a recurrent hidden state.
  - Inputs: color, motion vectors, depth, jitter, camera matrices, luma derivative, disocclusion mask, and reprojected hidden features.
  - About 10 GOPs per inference.
  - Target is 4 ms or less per frame. Pre- and post-processing shaders take about 1.4 ms on a low-frequency GPU.
  - In simulation it ran at about 75% of ASR's runtime at 1.5× upscale.
  - It handles particles without a reactive mask.
  - It runs on the GPU through Vulkan ML extensions. Arm GPUs with neural accelerators are planned for 2026.
  - Source: [Arm blog, How Arm NSS works](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/how-arm-neural-super-sampling-works)
- **Arm NSS weights, license and tooling.**
  - Weights are under the Arm AI Model Community License v1.0, described as permissive and as allowing NSS "to be retrained on datasets captured from your own content." Model source code is Apache-2.0.
  - Shipped as VGF models in three modes (high, mid, low). Example configs are 540p→1080p, and input dimensions must be padded to multiples of 8.
  - It can run on desktop through Arm's "ML Emulation Layer for Vulkan," which supplies the ML extensions where the driver lacks them.
  - Training code is published as the "Neural Graphics Model Gym," with an Unreal Engine capture plugin.
  - Source: [Hugging Face Arm/neural-super-sampling](https://huggingface.co/Arm/neural-super-sampling)
- **OptiScaler (GPL-3.0).**
  - Inputs it accepts: DLSS2+, XeSS and FSR2+ calls.
  - Backends: XeSS, FSR 2.1.2/2.2.1, FSR 3.x, FSR 4.x and DLSS on DX12; FSR 4.x, FSR 2.x/3.1, DLSS and XeSS 2.x on Vulkan.
  - It also offers RCAS/MAS sharpening and output scaling.
  - ASR and GSR are not listed as backends.
  - Source: [GitHub optiscaler/OptiScaler](https://github.com/optiscaler/OptiScaler)

### Inferences
- **ASR and GSR are cost tools, not quality tools.** ASR's top preset is designed to match FSR2. FSR 3.1 already costs about 1 ms on the Deck and is the shimmer baseline we want to beat. So ASR at best trades a little more quality for a few tenths of a millisecond. GSR 2 is a cheaper TAAU (Lanczos-based) and would probably be less stable than FSR 3.1.
- **ASR would be the easiest third-party temporal upscaler to add to OptiScaler.** Its API and inputs mirror FSR2's, and OptiScaler already has FSR2 backends. Both are permissively licensed, though OptiScaler itself is GPL-3.0, which constrains how DeckForge can modify and distribute it. The value for Deck players would be low.
- **Rough NSS estimate for the Deck (my arithmetic, unverified):**
  - Arm's 10 GOPs figure is for 540p→1080p. Scaled to a 640×400 input it is about 5 GOPs.
  - Deck INT8 peak, assuming full-rate dot4: 8 CUs × 64 lanes × 1.6 GHz × 8 ops ≈ 6.5 TOPS.
  - At Arm's assumed 40% efficiency, inference is about 2 ms, plus pre/post shaders. That suggests roughly 2.5–3.5 ms in total, similar to HelixSR.
  - In practice it would have to go through Arm's ML emulation layer on RADV, whose performance on AMD is unknown and probably not tuned for production.
  - NSS is the most plausible openly licensed, retrainable neural candidate. It is not a proven fast path.

### Gaps
- I found no numeric ms comparison of ASR and FSR2 (only charts), and no ASR or GSR measurement on any RDNA2 GPU or the Deck.
- I could not read the GSR 2 source directory (robots-blocked), so its exact pass structure and inputs are taken from a secondary article.
- I found no implementation of ASR, GSR or NSS inside OptiScaler or a Vulkan layer, and no Deck test of the NSS emulation layer.
- I found no evidence that the Adreno Neural Fusion SDK is open or portable.

## 2. Small learned upscalers: literature, HelixSR, BC-250 "rc9", AMD's lighter FSR 4, XeSS

### Takeaway
The Deck's realistic learned-upscaler range today is about 3.5–4.5 ms at 800p output: HelixSR at about 3.5 ms and FSR 4 INT8 at about 4.5 ms. Both are early community measurements. That is 16–20% of a 45 fps frame.
- **HelixSR** runs NVIDIA's DLSS 3.7 CNN weights in DX12 compute shaders. Its speed is attributed to the older, cheaper CNN model rather than a disclosed trick. It carries clear licensing risk.
- **The BC-250 rc9 speedup** (about 45–53% less upscaler time) mostly fixes a weakness specific to that board's gfx1013 GPU in FSR 4's packed INT8 dot-product path. It also adds Winograd convolution. Most of it probably would not carry over to the Deck's RDNA2 GPU.
- **AMD** has promised a "lightweight" FSR 4 for integrated graphics by the end of 2026. It has not shipped as of these sources, and the Deck is not named.
- **Literature:** published "tiny" temporal networks run at about 1–1.5 ms at 1080p on an RTX 3090. A network that fits 1–2 ms on the Deck at 800p would need to be at the very small end, a few 16-channel convolution layers at input resolution.

### Cited Findings
- **HelixSR [measured, community, early].**
  - Made by community developer lonewolf0622.
  - Replaces FSR 3.1 in D3D12 games and "runs the neural network from DLSS 3.7 Preset E through ordinary DirectX 12 compute shaders." Needs no NVIDIA driver, CUDA or ROCm. Works on Linux through Proton and vkd3d-proton. Games without FSR 3.1 need OptiScaler. Vulkan games are not supported.
  - Steam Deck 800p: about 3.5 ms vs about 4.5 ms for FSR 4. Steam Deck 1080p: about 7 ms vs about 11 ms at 1400 MHz GPU clock.
  - Quality: some testers rate it slightly behind FSR 4 and clearly ahead of FSR 3.
  - The article attributes the speed to the older CNN model needing less compute than transformer models. It names no precision or other optimization.
  - Article dated 9 Oct 2026. Source: [Digital Citizen](https://www.digitalcitizen.life/helixsr-brings-dlss-3-7-to-steam-deck-and-amd-handhelds-beating-fsr-4-in-early-tests/)
- **DLSS license (2020 version; older).**
  - §2.1: "You may not reverse engineer, decompile or disassemble."
  - §2.2: no modifying or creating derivative works of any portion of the SDK. Models are listed among SDK assets.
  - The RTX Supplement requires interoperability with NVIDIA hardware and distribution only for "authorized platforms."
  - Source: [NVIDIA DLSS License Agreement 06.26.2020](https://developer.download.nvidia.com/gameworks/dlss/NVIDIA_DLSS_License_Agreement-(06.26.2020).pdf)
- **FSR 4 INT8 on the Deck [measured, anecdotal].** Spider-Man Remastered at Ultra Performance: FSR 3 about 90 fps, FSR 4 about 70 fps. Several games showed higher battery drain. A reader commenter called the piece "purely anecdotal." Dated 16 Sep 2025. — [SteamDeckHQ](https://steamdeckhq.com/news/we-can-now-use-fsr-4-on-the-steam-deck-for-better-visuals-with-a-power-tradeoff/)
- **FSR 4 INT8 on the Deck, quality.** PCGH (via Deck Wizzard and Wccftech) reports cleaner, sharper distant detail than FSR 3.1, with no numbers. — [PCGH, 20 Sep 2025](https://www.pcgameshardware.de/FidelityFX-Super-Resolution-Software-277617/News/FSR-4-auf-dem-Steam-Deck-1482538/)
- **BC-250 rc9 [measured by the fork author; synthetic].**
  - Isolated upscaler GPU cost, before → after:

    | Output | Before | After rc9 |
    |---|---|---|
    | 1080p | 7.13 ms | 3.93 ms |
    | 1440p (1706×960 input) | 11.51 ms | 5.92 ms |
    | 4K | 25.72 ms | 12.08 ms |

  - The article says the optimization "targets INT8 packed signed integer dot-product operations used by FSR 4. The GFX1013 GPU in the BC-250 handles this path poorly."
  - An earlier fix replaced that path in a device-ID-specific experimental Mesa (RADV) build. rc9 moves it into a portable DLL.
  - The article itself says generalizing to RDNA 2 or the Steam Deck is uncertain.
  - Source: [remio.ai](https://www.remio.ai/pl/post/amd-bc-250-fsr-4-mod-halves-upscaling-time-but-the-real-test-is-gameplay-pl); same timings in [Guru3D, 14 Sep 2026](https://www.guru3d.com/story/optimized-fsr-4-nearly-halves-upscaling-time-on-amd-repurposed-bc250-mining-board/)
- **rc9 release notes.**
  - Single Windows x64 DLL, "4.1.1r9", carrying the FSR 4.1.1 INT8 shader checkpoint.
  - Adds "exact Winograd convolution and bounded packed arithmetic."
  - 348 shaders; 220 tests pass. Measured with GE-Proton and standard Mesa as medians of four 600-frame runs.
  - Windows, other GPUs and frame generation are "unqualified." No license is named.
  - Source: [GitHub daniel-h-0/bc250-fsr4-fork v4.0.0-rc9](https://github.com/daniel-h-0/bc250-fsr4-fork/releases/tag/v4.0.0-rc9)
- **BC-250 hardware.** Cut-down PS5 "Oberon" silicon, RDNA 2 family, 24 CUs enabled as standard (40 unlockable). — [TechSpot, 16 Sep 2026](https://techspot.com/news/113859-modders-turn-amd-abandoned-ps5-based-mining-gpu.html)
- **Steam Deck GPU instruction set.** The "GFX10 RDNA2 family includes gfx1030 … gfx1036." LLVM's instruction listing for that family includes `v_dot4c_i32_i8` and `v_dot2c_f32_f16`. — [LLVM/ROCm AMDGPU GFX1030 syntax](https://rocm.docs.amd.com/projects/llvm-project/en/docs-6.4.1/LLVM/llvm/html/AMDGPU/AMDGPUAsmGFX1030.html)
- **Lighter FSR 4 for handhelds [claimed].**
  - AMD's Jack Huynh told Korean media (via The Elec) that a special lightweight FSR 4 for integrated graphics is coming "by the end of this year."
  - Current APUs such as the Z2 Extreme reportedly cannot run standard FSR 4.
  - No architectures named, no Deck mention, no technical details.
  - Article dated about 7 Oct 2026. Source: [Notebookcheck](https://www.notebookcheck.net/FSR-4-special-version-to-boost-gaming-performance-on-handhelds-coming-this-year.1418417.0.html)
- **FSR 4.1 on RDNA 3 and RDNA 2 [claimed].**
  - AMD told TechPowerUp that RDNA 3 gets a separately requantized INT8 model because it lacks FP8. Converting FP8 straight to INT8 causes artifacts.
  - RDNA 2 support is delayed to early 2027, because without AI accelerators the model runs entirely on shader ALUs and needs significant optimization.
  - Article dated 16 Jun 2026. Source: [Wccftech](https://wccftech.com/amd-confirms-different-fsr-4-1-models-for-rdna-3-and-rdna-2-gpus/amp/)
- **FSR 4 INT8 on desktop RDNA2/3 [measured, ComputerBase via TweakTown].** 9–13% performance drop relative to the RDNA 4 path. +23% over native at 1440p Quality on RX 6800 XT and RX 7800 XT. Dated Oct 2025. — [TweakTown](https://www.tweaktown.com/news/108225/amds-fsr-4-running-on-rdna-2-and-3-gpus-shows-a-23-percent-performance-improvement-over-native/index.html)
- **XeSS, another INT8 learned upscaler [measured; Legion Go Z1E is RDNA3, not the Deck].**
  - Cyberpunk at 1440×900 output:

    | Setting | fps |
    |---|---|
    | Native | 47 |
    | FSR 4 INT8 Balanced | 56 |
    | XeSS 2 Balanced | 57 |
    | FSR 3 Balanced | 59 |
    | FSR 4 Performance | 60 |
    | FSR 3 Performance | 62 |

  - Quality ranking: FSR 4 > XeSS > FSR 3. FSR 3 showed moiré and poor transparency handling.
  - Dated 23 Apr 2026. Source: [TechSpot](https://www.techspot.com/article/3096-handheld-gaming-holy-grail-dll-upscaling/)
- **Tiny-network literature (Qualcomm AI Research, ICCV 2023; older).**
  - Design: warping module plus a small 3×3 Conv-ReLU reconstruction network with depth-to-space upsampling.
  - Measured on RTX 3090 at 1080p, 2× upscale, TensorRT FP16:

    | Model | Time | PSNR |
    |---|---|---|
    | Ours-S (f16-m1) | 1.08 ms | 31.18 dB |
    | Ours-M | 1.53 ms | n/a |
    | Ours-L | 3.52 ms | 32.21 dB |
    | Xiao et al. 2020 | 13.93 ms | 31.89 dB |
    | DLSS 2.2 | n/a | 30.21 dB |

  - The paper says DLSS 2.2 shows more ghosting. No FLOPs or parameter counts are given.
  - Source: [arXiv 2308.01483](https://arxiv.org/abs/2308.01483)
- **Facebook neural supersampling (2020; older).** 16× supersampling (960×540 → 3840×2160) from color, depth and motion vectors over multiple frames. The blog gives no timing figures. — [Meta Research blog](https://research.facebook.com/blog/2020/7/introducing-neural-supersampling-for-real-time-rendering/)
- **Mobile-focused 2025 paper.** "Lightweight, Edge-Aware, and Temporally Consistent Supersampling for Mobile Real-Time Rendering" (ACM TOG 44(6), 2025). Uses edge-coverage estimation, gradient-guided upsampling and temporal accumulation. Claims real-time on mobile GPUs but gives no figures in the abstract. — [MBZUAI repository](https://irep.mbzuai.ac.ae/items/62a245db-f057-456a-8728-766397b51e1b)

### Inferences
- **FSR 4 INT8 cost on the Deck.** The SteamDeckHQ figures (90 → 70 fps, about 11.1 → 14.3 ms) imply FSR 4 INT8 costs about 3.2 ms more than FSR 3 in that game. With FSR 3 at about 1 ms, that is about 4.2 ms, consistent with the ~4.5 ms figure we were given.
- **When FSR 4 pays for itself.** At a 45 fps target, the extra ~3.5 ms over FSR 3.1 only pays off if FSR 4 lets the game render at about 9–15% lower resolution per axis at equal perceived quality. The 9% figure assumes the whole frame scales with pixel count; 15% assumes about 60% does. Dropping from Quality (1.5×) to Balanced (1.7×) is about a 12% per-axis drop. The TechSpot and SteamDeckHQ reports suggest FSR 4 Performance is acceptable where FSR 3 Performance is not, which would be roughly a 25% drop.
- **rc9 is probably a BC-250-specific fix (my arithmetic; clocks unknown).**
  - Per output megapixel, rc9 on the BC-250 is about 1.9 ms/MP (1080p), and pre-rc9 was about 3.4 ms/MP.
  - The Deck's FSR 4 at 800p is about 4.4 ms/MP. HelixSR's article implies about 5.3 ms/MP at 1080p and 1400 MHz.
  - The BC-250 has 3× the CUs. Before rc9 it was far below per-CU parity with the Deck; after rc9 it is roughly at or a bit below parity.
  - That is consistent with rc9 mainly fixing a gfx1013 weakness in the dot4 path. The Deck's gfx103x family does have `v_dot4c_i32_i8` per LLVM.
  - The Winograd part (fewer multiplies for 3×3 convolutions) is algorithmic and might help the Deck modestly. That has not been tested.
- **What makes HelixSR fast.** Probably a smaller or cheaper model, the 2023–24 DLSS CNN rather than a transformer, plus compute-shader execution. The weights are almost certainly extracted from NVIDIA's DLL, which conflicts with the DLSS license terms on reverse engineering and derivative works (§2.1–2.2). DeckForge should not bundle, download or automate HelixSR. At most it could detect it and report it as a user-installed component.
- **How small a network fits 1–2 ms at 800p.** One 3×3 convolution with 16 input and 16 output channels at 640×400 is about 1.2 GOPs. At an effective ~2.6 TOPS INT8 (40% of a 6.5 TOPS peak, assuming full-rate dot4) that is about 0.45 ms per layer, or about 0.2 ms with Winograd. So a 1–2 ms network has to be roughly 4–8 such layers plus warping. That is the size class of Qualcomm's "Ours-S (f16-m1)". It is feasible on paper but leaves little room for quality.

### Gaps
- I could not find HelixSR's source repository, its license, the precision it uses (FP16, INT8 or FP32), or independent image-quality comparisons. All HelixSR timings come from one secondary article.
- I found no rc9 or BC-250-fork measurement on a Steam Deck, and no explicit statement of whether gfx1013 lacks dot4. The causal claim rests on the remio article.
- The licensing status of the community FSR 4 INT8 builds (shaders from AMD's SDK leak or release) is unresolved.
- AMD has published no release, design details or Deck eligibility for the lighter FSR 4.
- I could not open the Mob-FGSR (SIGGRAPH 2024) PDF, so I have no numbers for it.
- I did not find a source for the Deck's actual dot4 issue rate (full or half rate).

## 3. Building a Deck-specific reconstruction model we own (data, compute, licensing)

### Takeaway
It is technically possible, but the hard part is training data, not compute.
- **Arm's NSS stack** is the most practical open base. Weights are under a permissive community license that explicitly allows retraining on your own captured content, code is Apache-2.0, and Arm publishes training tooling, a sample dataset and an Unreal capture plugin.
- **Running it on the Deck** would still need our own RADV-friendly inference path, either compute shaders using INT8 dot4 or Arm's emulation layer.
- **Open game super-resolution datasets** are small (Arm: about 35 GB of the Bistro scene; Qualcomm QRISP: 8,760 frames from 13 Unity scenes). Their licenses need legal reading before commercial or distribution use.

### Cited Findings
- **Arm sample dataset.**
  - Arm/neural-graphics-dataset is under the Arm AI Model Community License v1.0.
  - Contents: Amazon Lumberyard Bistro scene rendered in Unreal Engine; low- and high-resolution color, depth, motion vectors, jitter and exposure; 35.3 GB.
  - Described as "a small, practical example dataset for tutorials." Arm recommends a much larger, more varied set for production training.
  - NSS itself was trained on more than 50,000 frames.
  - Source: [Hugging Face Arm/neural-graphics-dataset](https://huggingface.co/datasets/Arm/neural-graphics-dataset)
- **NSS license and tooling.** Weights are retrainable on your own content under the Arm AI Model Community License; code is Apache-2.0; Model Gym and an Unreal capture plugin are available. — [Hugging Face Arm/neural-super-sampling](https://huggingface.co/Arm/neural-super-sampling)
- **NSS training recipe.**
  - About 100-frame sequences, 540p 1 spp inputs, 1080p 16 spp ground truth.
  - Recurrent spatiotemporal loss, built in PyTorch.
  - Quantization-aware training via ExecuTorch; pre- and post-processing written in Slang.
  - Source: [Arm blog](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/how-arm-neural-super-sampling-works)
- **QRISP dataset (2023; older).**
  - 8,760 frames from 13 Unity scenes (7,260 train / 1,500 test), captured at 60 fps.
  - Resolutions: 270p, 360p, 540p, 1080p, plus a 1080p "Enhanced" target (2160p with 8× MSAA, downsampled).
  - Buffers: color, depth, motion vectors, with jittered and mip-biased variants. Includes DLSS 2.2 and FSR 1.2 baseline outputs.
  - The paper states no license.
  - Source: [arXiv 2308.01483](https://arxiv.org/abs/2308.01483)
- **QRISP license page.** Qualcomm's dataset page exists but needed JavaScript, so the license terms could not be read. — [Qualcomm Rasterized Images Dataset](https://www.qualcomm.com/developer/software/qualcomm-rasterized-images-dataset)
- **Model compression is achievable.** Qualcomm's small model was about 13× faster than Xiao et al. (1.08 vs 13.93 ms) on the same GPU at higher PSNR. — [arXiv 2308.01483](https://arxiv.org/abs/2308.01483)

### Inferences
- **Data is the bottleneck.**
  - Good training pairs need engine-side jitter, motion vectors and depth at low resolution, plus heavily supersampled high-resolution ground truth from the same frame.
  - From unmodified commercial games, OptiScaler-style interception can capture the low-resolution inputs, because games that support DLSS or FSR2+ already hand them to the upscaler. Matched 16 spp ground truth is not obtainable without engine control or a deterministic replay.
  - The realistic path is training on content we render ourselves (Unreal or other open scenes via Arm's capture plugin, plus Arm and QRISP data if their licenses permit), then fine-tuning and validating on captured game inputs using no-reference or temporal metrics.
  - Copyright and EULA questions around frames captured from commercial games are unresolved.
- **Compute.** The networks in this size class are small (Qualcomm's S/M models; NSS at about 10 GOPs per 1080p frame). Training is probably feasible on a single modern GPU or modest cloud budget. I found no published training-cost figure, so this is an estimate.
- **Weights we own.** Training from scratch, or retraining NSS under Arm's license, avoids NVIDIA and AMD weight licensing. Using HelixSR (DLSS) weights or leaked FSR 4 weights as a base would not.
- **Deployment.** We would need our own Vulkan compute or HLSL implementation of INT8 inference, ideally with Winograd 3×3 and dot4 paths. It would be injected the way HelixSR and the BC-250 fork do it: replacing the FSR 3.1 or FidelityFX upscaler DLL behind OptiScaler. Under DeckForge's own rules this is Tier I (injection), so it is only allowed in games without online anti-cheat.

### Gaps
- QRISP license terms.
- The exact text of the Arm AI Model Community License v1.0 (for example any field-of-use or attribution clauses). I did not open the PDF.
- Published training-compute budgets for models in this size class.
- Any precedent for legally training on frames captured from commercial games.

## 4. Temporal amortization in engines and research

### Takeaway
"Render less often" is widely used inside engines:
- caching static shadow geometry, scrolling cascaded shadow maps, refreshing distant shadow cascades every few seconds;
- updating 1/16 of cloud pixels per frame with reprojection;
- temporally reprojected volumetrics;
- checkerboard rendering, which saves roughly 12–30% when pixel shading dominates.

Every one of these is designed together with the engine's culling, matrices, motion vectors and resource lifetimes. Render-graph engines skip passes deliberately, for example shadow maps rendered only when something changed, and keep history resources out of memory aliasing.

### Cited Findings
- **Horizon Zero Dawn clouds (older, 2015, PS4).** Each frame updates 1 of every 16 pixels per 4×4 block in a quarter-resolution buffer and reprojects the previous frame, falling back to a low-resolution buffer where reprojection fails (e.g. screen edges). Cost went from about 20 ms to a target of about 2 ms ("10x faster or more"). — [Schneider, Advances 2015](https://www.advances.realtimerendering.com/s2015/The%20Real-time%20Volumetric%20Cloudscapes%20of%20Horizon%20-%20Zero%20Dawn%20-%20ARTR.pdf)
- **Cyberpunk 2077 (2021).**
  - Near cascades (up to 4) render every frame.
  - Distant shadows (up to 4 levels, the last covering the whole 256 km² map) take several frames to render, so they are "refreshed every few seconds."
  - Local shadow updates are capped per frame, with a static/dynamic split per map.
  - Unused shadow-map memory is aliased with HUD and post-process passes.
  - No ms figures.
  - Source: [Dybisz, SIGGRAPH 2021 talk](https://history.siggraph.org/wp-content/uploads/2022/06/2021-Talks-Dybisz_Shadows-Optimizations-in-Cyberpunk-2077.pdf)
- **Call of Duty: Infinite Warfare (older, 2017).**
  - Local shadow maps are reused unless the light moved or something moved inside their frustum.
  - A static cache holds static-geometry D16 maps, copied in on a hit; dynamic geometry is re-rendered every time.
  - Volumetrics use temporal reprojection to stabilize, at "2x memory & bandwidth."
  - No ms savings given for caching.
  - Source: [Activision, Rendering of COD IW](https://www.activision.com/cdn/research/2017_DD_Rendering_of_COD_IW.pdf)
- **Insomniac CSM caching and scrolling (older, 2012, PS3/X360).**
  - Static geometry (unmoved for about 5 s) is cached.
  - As the camera moves, the cached map is scrolled; only newly exposed edge slabs and newly static geometry are rendered, then dynamic geometry is added on top.
  - Claims it avoids rendering about 70% of static geometry.
  - Assumes a stable light direction.
  - Source: [Day/Hastings/Acton, SIGGRAPH 2012](https://advances.realtimerendering.com/s2012/insomniac/Acton-CSM_Scrolling(Siggraph2012).pdf)
- **Unity HDRP.** The maintainer disabled mixed-cached directional shadows, calling it "the least useful case anyway (since directional light shadows need frequent re-updates)." — [Unity Graphics PR #1559](https://github.com/Unity-Technologies/Graphics/pull/1559)
- **Assassin's Creed IV volumetric fog (older, 2014, Xbox One).** About 1.1 ms total on a 160×90×64 froxel volume, broken down as: shadow downsample 0.163 ms, blur 0.177 ms, lighting 0.43 ms, scattering 0.116 ms, apply 0.247 ms. No temporal reprojection in this version. — [Wronski, GDC 2014](https://bartwronski.com/wp-content/uploads/2014/03/ac4_gdc.pdf)
- **Checkerboard rendering on Intel iGPU (older, 2018).**
  - Method: quarter-resolution 2× MSAA with per-sample shading, a one-pixel viewport jitter on alternate frames, and a reconstruction pass that reads frames N and N-1.
  - Speedup: 1.14–1.2× on average, up to 1.4× when pixel-shader bound (about 30% lower frame time).
  - Requires engine motion vectors for dynamic objects, previous-frame vectors, and changes to deferred G-buffer, resolve and forward passes.
  - Artifacts: edge crawl and disocclusion ghosting.
  - Notes the PS4 Pro used an object-ID buffer that Intel hardware lacks.
  - Source: [Intel, McFerron & Lake](https://intel.com/content/dam/develop/external/us/en/documents/checkerboard-rendering-for-real-time-upscaling-on-intel-integrated-graphics.pdf)
- **Checkerboard background.** Renders about 50% of pixels and reconstructs the rest. PS4 Pro had dedicated hardware support. Rainbow Six Siege used it mainly as anti-aliasing. — [Wikipedia](https://en.wikipedia.org/wiki/Checkerboard_rendering); [GDC 2016 Rendering Rainbow Six Siege](https://gdcvault.com/play/1022990/Rendering-Rainbow-Six-Siege)
- **Render-graph pass skipping (Granite, older, 2017).**
  - Each pass has a callback that can mark it as not executed for the frame; the example is shadow maps that only render when something changes.
  - Aliased resources hand off with their layout forced to UNDEFINED.
  - History/feedback images keep two instances and "should never alias with anything else."
  - Write-only passes may discard prior contents.
  - Source: [Themaister, Render graphs and Vulkan — a deep dive](http://themaister.net/blog/2017/08/15/render-graphs-and-vulkan-a-deep-dive/)
- **Frame graphs in general.** They exist to handle "barriers, queue synchronization and memory aliasing in the background." References Frostbite FrameGraph (GDC 2017). — [gfx-rs wiki](https://github.com/gfx-rs/gfx/wiki/Frame-graphs)

### Inferences
- **What engines actually amortize.** The robust targets are static geometry in shadow maps (with invalidation on light or object movement), very distant cascades on multi-second refreshes, and low-frequency effects (clouds, fog, GI) that have reprojection and fallbacks.
- **Directional (sun) cascades** need frequent updates as the camera moves (Unity's comment). Engines solve this by scrolling, snapping or caching only static geometry, not by naively reusing last frame's map.
- **Checkerboard** needs deep renderer changes (MSAA targets, jitter, ID or motion data). It is not something to retrofit from outside a game. A temporal upscaler at a lower render resolution has largely replaced it.

### Gaps
- I found no ms-quantified source for "update far cascade N every K frames" in a specific shipped title (Cyberpunk gives "every few seconds" with no numbers). Far Cry, Decima and Call of Duty sun-shadow cascade schedules were not found.
- I found no information on whether Monster Hunter Wilds' RE Engine already caches shadows or amortizes volumetrics, or whether REFramework exposes such settings.
- Half-rate GI timings (e.g. Lumen) were not collected.

## 5. Could an external layer force amortization on an unmodified game? Safety and prior attempts

### Takeaway
Forcing pass skipping from a Vulkan layer or vkd3d-proton (e.g. reusing last frame's far cascade on alternate frames) is high-risk and has no public prior art I could find.
- The layer cannot reliably tell which commands are "far cascade N."
- The shadow map's memory may be aliased and overwritten later in the same frame.
- The game recomputes cascade matrices every frame, so a stale map is sampled with a new projection.
- Render-pass load/store semantics allow drivers to discard contents.

The closest existing tools (ReShade ShaderToggler) hide shaders for visual purposes, not to save time. A narrow, verifiable subset might be possible per game. It belongs in Tier I (injection, opt-in, no anti-cheat) and would need per-game, per-patch validation.

### Cited Findings
- **Vulkan load-op semantics.** `VK_ATTACHMENT_LOAD_OP_DONT_CARE`: "the previous contents within the area need not be preserved … contents … will be undefined"; LOAD preserves; CLEAR overwrites. — [Vulkan refpage VkAttachmentLoadOp](https://docs.vulkan.org/refpages/latest/refpages/source/VkAttachmentLoadOp.html)
- **Aliasing and history resources.** Aliased resources hand off with layout forced to UNDEFINED. History resources never alias. Engines can mark a shadow pass not-executed only because the graph knows the resource is persistent. — [Themaister](http://themaister.net/blog/2017/08/15/render-graphs-and-vulkan-a-deep-dive/)
- **Shipped example of aliasing shadow memory.** Cyberpunk 2077 aliases unused shadow-map memory with HUD and post-process passes. — [Dybisz 2021](https://history.siggraph.org/wp-content/uploads/2022/06/2021-Talks-Dybisz_Shadows-Optimizations-in-Cyberpunk-2077.pdf)
- **Prior art for external shader toggling.**
  - ShaderToggler (ReShade add-on) toggles a game's shaders on or off in groups, found by browsing pixel, vertex and compute shaders in-game, e.g. to hide HUD, menus or effects. It makes no performance or amortization claims.
  - A fork applies ReShade effects at user-chosen points in the pipeline rather than skipping work.
  - Sources: [GitHub FransBouma/ShaderToggler](https://github.com/FransBouma/ShaderToggler); [GitHub akrieger/reshadeeffectshadertoggler](https://github.com/akrieger/reshadeeffectshadertoggler)
- **Engine-side shadow-cache invalidation** depends on game-side knowledge (light moved, object moved in frustum, static vs dynamic geometry). — [Activision COD IW](https://www.activision.com/cdn/research/2017_DD_Rendering_of_COD_IW.pdf); [Insomniac 2012](https://advances.realtimerendering.com/s2012/insomniac/Acton-CSM_Scrolling(Siggraph2012).pdf)

### Inferences
- **Specific failure modes for a layer that skips a pass:**
  - **Aliasing.** Under D3D12 to vkd3d-proton, games use placed resources and aliasing barriers. A skipped cascade's memory may hold another pass's data by the time it is sampled. A layer would have to prove the image has a dedicated, non-overlapping memory binding, e.g. by tracking `vkBindImageMemory` offsets.
  - **Discard semantics.** A pass with DONT_CARE load/store, or a transition from UNDEFINED, can lose contents across frames.
  - **Projection mismatch.** Cascade matrices live in game constant buffers the layer cannot interpret. Reusing the map while the game samples with this frame's matrix causes shadow swimming or detachment.
  - **Dynamic objects.** Moving objects would lag or vanish from far shadows.
  - **Stale history.** The game's own temporal history buffers (TAA/upscaler) will accept the stale data and smear it.
  - **Brittle identification.** Matching draws by shader hash, render-target format or draw count breaks with game patches and settings changes.
- **A safer variant.** Use only games that already expose a frame-persistent distant-shadow or volumetric target. Verify per game in the bench runner with image-diff and frame-time evidence. Ship as opt-in Tier I. The more reliable route is engine-level knobs (REFramework or ini or console variables) where the engine itself already supports caching or update rates, which is Tier S/I depending on the method.
- **Reality check.** Shadows are often a small share of frame time on the Deck compared with GI, volumetrics and post-processing. Without a per-pass GPU profile of the target game (e.g. Monster Hunter Wilds via RGP or RenderDoc captures, which this research did not obtain), the potential saving is unknown.

### Gaps
- I found no public attempt (layer, DXVK/vkd3d patch, or mod) that forces alternate-frame pass skipping for performance in unmodified games. The absence of evidence is itself a signal, not proof.
- I found no per-pass GPU timing breakdown for Monster Hunter Wilds on the Deck.

## 6. Spatial post-filters and perception on a 7.4" 800p screen at handheld distance

### Takeaway
- **Pixel density.** The Deck OLED is about 204 PPI. At typical handheld distances of 12–16 inches (my assumption) that is roughly 43–57 pixels per degree, well under the eye's measured foveal limit of about 94. Individual pixels and aliasing are resolvable.
- **Temporal stability matters most.** Shimmer and moiré are the dominant visible defects. That argues for spending budget on temporal reconstruction quality over raw resolution.
- **Sharpening** (CAS/RCAS) helps restore TAA blur but cannot fix temporal instability. Over-sharpening amplifies shimmer.

### Cited Findings
- **Deck OLED specs.**
  - Display: 7.4-inch HDR OLED, 1280×800, up to 90 Hz.
  - GPU: 8 RDNA 2 CUs at 1.6 GHz, about 1.6 TFLOPS FP32.
  - Memory: LPDDR5-6400 on quad 32-bit channels (about 102 GB/s by calculation).
  - Source: [Steam Deck tech specs](https://www.steamdeck.com/en/tech)
- **Eye resolution limit.** Measured foveal limits are 94 ppd achromatic, 89 red-green and 53 yellow-violet, with individuals up to 120. The authors call the 60 ppd "20/20 = retinal" assumption a historical misconception. Dated 10 Oct 2024. — [Ashraf, Chapiro, Mantiuk, arXiv 2410.06068](https://arxiv.org/abs/2410.06068)
- **CAS.** Designed to improve existing TAA, which "can add variable blur through temporal feedback." It sharpens adaptively (less where already sharp) and is applied after TAA. Its optional scaling can handle dynamic-resolution changes before UI compositing. — [GPUOpen FidelityFX CAS](https://gpuopen.com/fidelityfx-cas/)
- **RCAS.** Supported in Arm ASR as in FSR1/FSR2. — [Arm blog](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/introducing-arm-accuracy-super-resolution)
- **FSR1 (EASU+RCAS) license.** MIT. — [GitHub GPUOpen-Effects/FidelityFX-FSR](https://github.com/GPUOpen-Effects/FidelityFX-FSR)
- **Upscaler quality metrics.** Arm evaluates with PSNR, SSIM, tPSNR (temporal stability and ghosting) and STRRED (temporal instability and shimmer). — [Vulkanised 2025](https://vulkan.org/user/pages/09.events/vulkanised-2025/T24-Sergio-Alapont-Arm-ArmASR.pdf)
- **Resolution vs frame rate in motion (older, 2020; LCD, small samples).**
  - The best split depends on object velocity: as velocity rises, the model shifts budget to frame rate at the cost of resolution.
  - Judder was not detectable above 60 Hz; quality gains slow above about 100 Hz.
  - Calibrated on LCDs with 5–11 participants; flicker and ghosting were not modeled.
  - Source: [Denes et al., ACM TOG 39(4), 2020](https://www.cl.cam.ac.uk/~gd355/publications/sg20_paper.pdf)
- **Handheld FSR 3 artifacts.** At 900p output on a handheld, FSR 3 showed visible moiré and poor transparency handling, "usable only when little is moving." FSR 4 INT8 Balanced was "close to native 900p." — [TechSpot, Apr 2026](https://www.techspot.com/article/3096-handheld-gaming-holy-grail-dll-upscaling/)

### Inferences
- **Pixel-density arithmetic (mine).**
  - PPI = √(1280² + 800²) / 7.4 ≈ 204 (the LCD Deck is about 216).
  - PPD ≈ PPI × distance (inches) × tan 1°: about 43 at 12 in, 50 at 14 in, 57 at 16 in.
  - Even at 60 ppd, aliasing and moiré remain visible to most people per Ashraf et al. So the Deck sits where both blur and shimmer are perceptible. Temporal shimmer is especially noticeable because it draws the eye in an otherwise static scene. The 2020 motion model also suggests that in fast motion, extra frame rate beats extra resolution.
- **Practical post-filter guidance.**
  - Use moderate RCAS/CAS after a good temporal resolve. RCAS has tunable strength through OptiScaler.
  - Prefer a better TAA/upscaler (FSR 4, HelixSR-class, or future AMD lite) over a higher render scale with FSR 3.1 when the cost difference fits.
  - Do not use sharpening to compensate for FSR 3.1 shimmer: it increases high-frequency flicker.
  - FSR1/SGSR1-style spatial upscaling only makes sense where a game has no temporal path. It cannot remove temporal aliasing.
- **Metrics for DeckForge's own quality comparisons.** Include temporal-stability metrics (tPSNR/STRRED or a flicker measure on a fixed camera path), not just single-frame PSNR or SSIM. That matches Arm's method and the visible defect we care about.

### Gaps
- I found no study specific to handheld viewing distances or the Deck OLED's subpixel layout and how they affect perceived sharpness or shimmer.
- I did not find a perceptual study directly ranking temporal flicker against spatial blur for upscalers. The 2020 study excludes flicker and ghosting.
- I found no measured ms cost of RCAS or CAS on the Deck (generally assumed to be well under 0.2 ms, but unverified here).
