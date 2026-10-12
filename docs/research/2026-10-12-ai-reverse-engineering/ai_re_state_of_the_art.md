# AI reverse engineering of games: hype vs. verified capability (as of 12 Oct 2026)

Labels used on every finding:
- **[M]** Measured: a number with a stated method.
- **[C]** Claimed: an assertion by a creator, vendor or journalist that nobody has independently checked.
- **[R]** Reported: a journalist's account of events.

Inferences are listed separately under each question. I collected no DRM, anti-tamper or anti-cheat bypass steps. The guides I read explicitly exclude those topics.

---

## 1. The viral mashup clips (Elden Ring + Minecraft, CoD + Skate, etc.)

### Takeaway
The September–October 2026 clips are not generative video and not world models. They are real code mods that a human directs and an AI coding agent writes (mostly Claude Opus 5.5, some Codex). Most are "passthrough" mods: two games run at the same time, connected through existing mod loaders and shared memory, and one game's render is composited into the other's frame. Nothing here rebuilds or optimizes a game. A passthrough mod roughly doubles the load, because both games run at once.

### Cited Findings
- **Timeline [R].** Clips began appearing in mid-September 2026, around the release of Claude Opus 5.5 — [Know Your Meme](https://knowyourmeme.com/memes/ai-video-game-merging)
  - 19 Sep: chasm's "rewrote Skate 3 in Rust".
  - 27 Sep: Skate in Modern Warfare 2.
  - 28 Sep: Call of Duty + Minecraft, 619k views.
  - 29 Sep: @TobynJacobs posts Minecraft-in-Elden Ring, 308k likes.
  - 3 Oct: Super Mario 64 + Elden Ring, 2.9M views, taken down after a copyright claim.
  - The entry says Claude Opus 5.5 is usually credited. chasm's Skate 3 post credits Codex for help with the reverse engineering.
- **How the Minecraft/Elden Ring clip was made [R, 8 Oct 2026].** Players used Claude agents to "vibe code" the mods. The method is a "passthrough mod": one game hosts the world and the other supplies movement and combat. The Minecraft/Elden Ring mod also adds Black Ops guns. This is the most likely source of the "Elden Ring + Call of Duty" clips: it is a Black Ops mode inside the same mod, not a separate merge. — [Decrypt](https://decrypt.co/380407/ai-video-game-mod-mashups-are-taking-off-here-are-the-wackiest-examples)
- **Creator status [C].** Toby Jacobs has not released the mod. He says he built it on a Mac and would need a Windows port first — [Decrypt](https://decrypt.co/380407/ai-video-game-mod-mashups-are-taking-off-here-are-the-wackiest-examples)
- **Unverified as of 1 Oct 2026 [R].** There is no public download. After accusations of fakery, the creator posted videos of himself playing it on a laptop. He attributes it only to "AI experiments" — [BisectHosting](https://www.bisecthosting.com/blog/is-the-minecraft-elden-ring-mod-real)
- **Not a world model [R, 6 Oct 2026].** The demo is "not a verified public release, but a compelling proof-of-concept." It is described as code-bridged ("dual-engine or passthrough", IPC syncing inputs, coordinates and hitboxes), as distinct from world models like Genie. — [Stork.ai](https://www.stork.ai/blog/minecraft-just-invaded-elden-ring)
- **How the effect works [R, 5 Oct 2026].** VGC describes it as an "elaborate green-screen": visuals from one game are overlaid on the other, and actions are linked across the two. VGC says modders "decompile two games using Claude Opus 5.5." — [VGC](https://www.videogameschronicle.com/news/ai-game-mashup-videos-on-social-media-spark-debate-and-backlash-among-players-and-modders/)
  - The how-to guide below contradicts this in part. It treats decompiling as a last resort, used only when no mod loader exists.
- **Passthrough architecture, from the community guide [C].**
  - The host game draws the frame. The "gameplay" game runs in a hidden window.
  - State and frames pass between them over shared memory.
  - The heavy lifting is done by existing loaders: SKSE, F4SE, Fabric, BepInEx/MelonLoader, UE4SS.
  - The agent clones a reference project (SkyCraft) and builds the plugin. The human picks the games, playtests and feeds back logs.
  - The guide says it can be "a realistic weekend project" when a loader already exists. Without one, reverse engineering comes first and takes much longer.
  - Performance: "running two games plus a message channel at once is costly." The only figure given is that OWCraft went from 25 to 60 fps after skipping the hidden window's present.
  - Scope: single-player, offline, games you own. It states: "Nothing here covers anti-cheat, DRM, or online play."
  - Source: [ai-game-modding-guides/02](https://github.com/trevaintdead/ai-game-modding-guides/blob/main/guides/02-passthrough-mods.md), [README](https://github.com/trevaintdead/ai-game-modding-guides)
- **Elden Ring + Spider-Man [C].** The same guide says this merge took 3–4 hours and that first results are rough — [Decrypt citing the guide](https://decrypt.co/380407/ai-video-game-mod-mashups-are-taking-off-here-are-the-wackiest-examples)
- **SkyCraft, the reference design [C, repo README].**
  - A Skyrim SKSE C++ plugin and a Minecraft Fabric Java mod talk over a shared-memory protocol. Minecraft runs hidden; Skyrim draws the final frame.
  - It needs about 3 GB of extra RAM and a GPU that can also run Minecraft.
  - It is version-locked to Skyrim 1.6.x/1.7.x and is "early and experimental."
  - The README does not say whether AI was used.
  - Source: [SkyCraft](https://github.com/chasmlol/SkyCraft)
- **Three merge architectures [C, 7 Oct 2026].** A Towards AI article lists content port, passthrough and reimplementation. Its Minecraft×GTA V example uses a WebSocket for state, shared memory for frames, and a ReShade add-on that composites against GTA's depth buffer. It says the agent "doesn't make two engines share a renderer, clock, or coordinate system," and that the link between AI and these mashups "needs care." — [Towards AI](https://pub.towardsai.net/how-does-ai-game-merging-actually-work-043063de3706)
- **Universal Modder [R, 6 Oct 2026].** An MIT-licensed set of Claude Code skills (repo created 30 Sep 2026) with 12 engine playbooks and fal for asset generation. It is "not an app that mods games by itself." Its rules forbid injecting code into anti-cheat games, but these are agent instructions, "not a technical lock." The reviewer did not mod a real game. — [laozhang.ai review](https://blog.laozhang.ai/en/posts/universal-modder)
- **Modder backlash [R].** One modder called it an "AI slop factory." Kran said the mashups need no creative input beyond choosing two games. Others raised maintainability of AI code — [VGC](https://www.videogameschronicle.com/news/ai-game-mashup-videos-on-social-media-spark-debate-and-backlash-among-players-and-modders/)
- **World models are a separate track that cannot reproduce real games:**
  - **Project Genie (Genie 3) [C, 29 Jan 2026].** A research prototype for US AI Ultra subscribers. Generations last 60 seconds. Google says worlds "may not always follow… physics" and that characters can have high control latency — [Google](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/project-genie/)
  - **Microsoft WHAMM/Muse Quake II demo [R, 6 Apr 2025].** Trained on a single level. Enemies are fuzzy and object permanence is lost after about 0.9 s. Austin Walker called the idea that it preserves games "a fundamental misunderstanding of… how games WORK." — [TechCrunch](https://techcrunch.com/2025/04/06/microsoft-releases-ai-generated-quake-ii-demo-but-admits-limitations)
  - **Decart Mirage [R].** Restyles live game footage in real time (for example, Fortnite underwater) at 768×432, 20 fps, about 100 ms latency — [etcentric](https://www.etcentric.org/decart-ais-mirage-transforms-live-stream-video-in-real-time/)

### Inferences
- The "AI reverse-engineered Elden Ring" framing is mostly wrong. The documented method relies on existing community mod loaders, script extenders and IPC glue. The AI writes glue code at high speed. It does not understand or rebuild FromSoftware's engine.
- Passthrough mods are the opposite of a Deck optimization. They add a second game process, extra RAM and GPU work, and frame latency.
- Some mashup clips may have been restyled with tools like Mirage, but I found no documented case among the viral clips. The well-documented ones are code mods.

### Gaps
- I found no first-person build write-up from Toby Jacobs for Minecraft/Elden Ring: no model version, no token cost, no hours spent.
- I found no standalone "Elden Ring + Call of Duty" project. My best match is the Black Ops mode in the Jacobs mod.
- No mashup has published fps or frame-time data on any hardware, let alone a Deck.

---

## 2. State of AI-assisted reverse engineering, 2025–2026

### Takeaway
LLM decompilation works one function at a time on C. It reaches roughly 40–65% "re-executability" on single-function benchmarks, and less on realistic code. A September 2026 study shows that recompiling and passing tests overstate how correct the output is. Day to day, people connect Claude (most often), GPT/Codex, Gemini or local models to IDA, Ghidra or Binary Ninja through MCP.

The strongest real-world results are in console matching decompilation. There a compiler gives a byte-exact yes/no answer, and Claude Opus 4.5 roughly doubled the pace of one N64 project. AI-built "recomps" of console games exist, but they sit on top of human-built recompilers and runtimes and get poor quality reviews.

I found no credible case of AI rebuilding a modern commercial PC game end-to-end.

### Cited Findings

**LLM decompilation research**
- **LLM4Decompile [M].**
  - Re-executability: 1.3B-v1.5 27.3%; 6.7B-v1.5 45.4%; 6.7B-v2 (refining Ghidra output) 52.7%; 9B-v2 64.9%; 22B-v2 63.6%.
  - The benchmarks are single C functions, Linux x86-64, GCC O0–O3. HumanEval-Decompile has 164 functions; ExeBench has 2,621 real-project functions.
  - Source: [LLM4Decompile GitHub](https://github.com/albertan017/LLM4Decompile)
- **Idioms (CMU, early 2025) [M].** Passes 54.4% of ExeBench unit tests, versus 46.3% for LLM4Decompile and 37.5% for Nova.
  - It recovers structurally correct user-defined types only about 15% of the time, and dependency equivalence is about 18%.
  - C only. Performance "drops sharply at O1." Inlining was disabled for evaluation.
  - It works per function, and the neighbouring context it can use is capped by the context window.
  - Source: [arXiv 2502.04536](https://arxiv.org/html/2502.04536v2)
- **DecLLM (ISSTA, June 2025) [M].** An iterative repair loop with GPT-3.5/GPT-4 using recompile and runtime feedback. It makes about 70% of decompiler outputs that did not recompile recompile again. The remaining 30% are hard cases. — [ISSTA 2025](https://conf.researchr.org/details/issta-2025/issta-2025-papers/80/DecLLM-LLM-Augmented-Recompilable-Decompilation-for-Enabling-Programmatic-Use-of-Dec)
- **AutoDecompiler (2026, reinforcement-learning trained) [M].**
  - Average re-executability on HumanEval: 67.4% for the 30B model, against GPT-4o 29.3% and DeepSeek-V3 51.2%.
  - On ExeBench it falls to 46.4%. On HumanEval with pseudo-code input, DecLLM + DeepSeek-V3 scores 80.5%.
  - Stated limits: single function, no interprocedural context, refinement turns capped by context length, untested on obfuscated or packed binaries, and can "hallucinate code that is readable and valid but semantically inconsistent."
  - Source: [arXiv 2606.16162](https://arxiv.org/pdf/2606.16162)
- **DecompileBench (Tsinghua, May 2025) [M].**
  - 23,400 functions from 130 OSS-Fuzz programs.
  - Hex-Rays: about 58.3% recompile success and 41.8% coverage-equivalence. GPT-4o-mini matches Hex-Rays on recompilation (0.582). GPT-4o has the best LLM coverage-equivalence (0.346), still behind Hex-Rays.
  - Claude-3.5-Sonnet was among the models tested.
  - LLMs win on readability but lose on correctness. All tools get worse from O0 to O3. Scope is x86-64 and C.
  - Source: [arXiv 2505.11340](https://arxiv.org/html/2505.11340v1)
- **"When LLM Decompilers Recompile More and Preserve Less" (4 Sep 2026) [M].**
  - Output that passes every shipped test still behaves differently on other inputs: 4.9% overall, up to 13% for one system.
  - On 300 real GitHub functions, the best LLM refinement raised Ghidra's build rate from 75% to 90% but lowered behavioural match from 74% to 62%.
  - Up to 10% of known CVEs (published vulnerabilities) disappeared silently from the output.
  - The authors recommend differential fuzzing (Decompile-Diverge).
  - Source: [arXiv 2609.05370](https://arxiv.org/abs/2609.05370)

**Tooling (MCP and plugins)**
- **IDA Pro MCP (mrexodia) [C].** About 12.1k stars. Offers decompile, xrefs, callgraph, rename, set_type, patch_asm, py_eval and a debugger, and runs headless via idalib.
  - Supported clients include Claude, Claude Code, Codex, Gemini CLI and Cursor.
  - The README warns: "LLMs are prone to hallucinations" and "will not perform well on obfuscated code." It paginates results to avoid token overflow.
  - Source: [GitHub](https://github.com/mrexodia/ida-pro-mcp)
- **ReVa (Ghidra MCP) [C].** Uses many small tools to limit "context rot." It recommends Claude Code as the client, ships Claude Code skills (triage, deep analysis, crypto), and claims to handle large binaries and firmware. Requires Ghidra 12+. — [ReVa README](https://cdn.jsdelivr.net/gh/cyberkaida/reverse-engineering-assistant@main/README.md)
- **Binary Ninja Sidekick 26.0 (15 May 2026) [C].** Agent modes (Research, Transform, Repair Analysis, Debugger), subagents, skills and MCP. Models can be routed to the Sidekick cloud, Ollama/vLLM, or direct Anthropic/OpenAI — [Sidekick blog](https://sidekick.binary.ninja/blog/sidekick-26-0-a-whole-new-experience-in-reversing-with-ai)
- **Claude + GhidraMCP on Atari River Raid (23 Jan 2026) [R].**
  - Claude found the lives-decrement code, giving an infinite-lives patch on an 8 kB ROM.
  - It also confidently misidentified the game as Centipede ("confidence and accuracy are orthogonal").
  - The MCP tools could not rebase or patch. Each tool call took about 30 s. The chain of four components was fragile.
  - Source: [Quesma](https://quesma.com/blog/ghidra-mcp-unlimited-lives/)

**AI in fan decompilation and recompilation**
- **Snowboard Kids 2, N64 matching decomp, Chris Lewis.**
  - Nov 2025 [R]: Claude was found to perform better than Codex, with the caveat "completely unscientific." The author wrote "We're a long way from 'vibe coding' being viable for matching decompilation." Agents "stumble on basic arithmetic and bookkeeping" and "struggle to reproduce the precise control flow that compilers generate for complex functions." — [blog](https://blog.chrislewis.au/using-coding-agents-to-decompile-nintendo-64-games/)
  - 27 Nov 2025 [C]: after switching to Claude Opus 4.5 he made "more progress in three weeks than in the prior three months." He used an unattended `claude -p` loop that fed the easiest functions first. Output is often messy (pointer arithmetic, gotos). He projects about 79% of functions are matchable. Codex did poorly. — [blog](https://blog.chrislewis.au/the-unexpected-effectiveness-of-one-shot-decompilation-with-claude/)
  - [M]: the decomp.dev chart went from about 20% to 25% matched between 3 Sep and 17 Nov 2025, then to about 45% by 2 Dec 2025 — [Simon Willison](https://simonwillison.net/2025/Dec/6/one-shot-decompilation/)
- **Super Smash Bros. Melee, GameCube.**
  - [R, 8 Sep 2026]: 100% decompiled per decomp.dev, 3.88 MB of code. The project started in July 2020. The article does not mention AI. — [Android Authority](https://androidauthority.com/super-smash-bros-melee-decompiled-3708716)
  - [C]: AI sped up the final stretch, and a Claude-made port, melee-pc, runs on Windows, Linux and Android — [Dot Esports, 3 Oct 2026](https://dotesports.com/general/news/ai-vibe-coded-game-recompilations-pc)
  - Conflicting claim: OpenAI "GPT-6 Astra" closed out the last part, and a 120 fps macOS build was produced in about 6 hours. This comes from a single source that cites no primary sources, and I could not verify that the model exists. — [Held Games](https://heldgames.com/guides/melee-decompiled-ai-astra)
- **AI-built recomps [R, 3 Oct 2026].**
  - Wave Race 64: Claude Code wrote "every line," but on top of human-built N64Recomp, N64ModernRuntime and the RT64 renderer.
  - GoldenEye 007 (heavily AI-coded): "critical bugs."
  - Mischief Makers: criticized at launch.
  - Fable 2 (Xbox 360, via the ReXGlue SDK) reportedly used local Qwen. "AI got the game running quickly," but mapping enough functions to finish the game took a lot of trial and error.
  - The N64 Recomp Discord bans showcasing vibe-coded projects.
  - Source: [Dot Esports](https://dotesports.com/general/news/ai-vibe-coded-game-recompilations-pc)
- **Fable 2 Recomp state [R, 22 Sep 2026].** Static recompilation of PowerPC to C++. Early stage; Vulkan renderer incomplete; users must supply their own ISO. The article does not mention AI. — [DSOGaming](https://dsogaming.com/news/fable-2-unofficial-native-pc-port-available-for-download/)
- **Backlash.** DarioSamo (Banjo: Recompiled) on the AI-built Banjo-Tooie recomp: "entirely AI-generated," built on his team's framework, and patching memory "from the wrong side," which makes modding unmaintainable — [Kotaku, 5 Oct 2026](https://kotaku.com/zelda-and-banjo-recompiled-devs-go-to-war-with-ai-vibe-coded-slopcomps-2000739936); [VGC, 3 Oct 2026](https://www.videogameschronicle.com/news/banjo-kazooie-pc-port-decomp-developer-says-ai-generated-pc-ports-are-a-race-to-the-bottom-and-disrespectful/)
- **Mario Kart Wii "Wiicompiled" (Jul 2026) [R].** An AI-agent-coded static recompilation. The developer himself recommends staying on Dolphin for now. PC Gamer's Wes Fenlon: reaching a partially working port is easy, but accurate and crash-free is "a different story." — [Time Extension](https://www.timeextension.com/news/2026/07/this-sucks-ass-mario-kart-wii-is-getting-an-ai-assisted-recomp-and-some-people-arent-happy)

**AI rebuilds of commercial games**
- **Rust rewrites [C].** These rebuild an engine in Rust/Bevy and load assets from the player's own install.
  - hl2-rs (Half-Life 2) is partial: the campaign is not playable.
  - "benilla" (WoW 1.12.1 client) is described as complete after hundreds of commits.
  - The guide treats decompiling as a last resort and recommends documented formats and existing source releases first.
  - Source: [guide 03](https://github.com/trevaintdead/ai-game-modding-guides/blob/main/guides/03-rust-rewrites-and-ports.md)

### Inferences
- The success cases share three conditions:
  - Small binaries from old, fixed hardware (MIPS/PowerPC).
  - A mechanical oracle: byte-matching, or a human-built recompiler.
  - Years of prior human infrastructure.
- Modern PC games meet none of these. They are already native x86-64, they are much larger optimized C++, and they often carry anti-tamper or anti-cheat protection.
- Static recompilation helps console games because it removes emulation overhead. A PC game on the Deck already runs natively through Proton, so there is no equivalent overhead to remove.
- Claude is the most frequently documented model in hobbyist game RE (Snowboard Kids 2, Wave Race 64, melee-pc, the Elden Ring mashup). The evidence is anecdotal; there is no head-to-head benchmark.

### Gaps
- I found no published speed-up figures except the Snowboard Kids 2 chart. I found no cost or token data for any game project.
- I found no academic evaluation of Claude Opus 4.5 or 5.x on decompilation benchmarks. The most recent Claude results I found are 3.5-Sonnet in DecompileBench.
- I did not search PS2/PS3 recomp efforts (PS2Recomp, RPCS3-adjacent work) specifically and have no AI-specific findings for them.
- Primary sources for melee-pc and for Fable 2's Qwen usage were not checked; both come from Dot Esports only.

---

## 3. Limits: what AI RE cannot yet do

### Takeaway
Every published system works one function at a time. Accuracy falls with compiler optimization. None of the papers I read evaluates C++ (templates, virtual dispatch). Obfuscation defeats current LLMs. "It compiles and passes tests" is a measurably unreliable proxy for "it is correct." I found no LLM research at all on decompiling GPU shader bytecode (DXIL/SPIR-V); the closest work is CUDA PTX.

### Cited Findings
- **Whole-program understanding.** Idioms works per function, its neighbouring context is capped by the context window, and the "scattered evidence" problem persists. It does not address whole-program decompilation — [Idioms](https://arxiv.org/html/2502.04536v2)
  - AutoDecompiler: single function, no interprocedural context — [arXiv 2606.16162](https://arxiv.org/pdf/2606.16162)
  - The agent "doesn't make two engines share a renderer, clock, or coordinate system" — [Towards AI](https://pub.towardsai.net/how-does-ai-game-merging-actually-work-043063de3706)
- **Optimized code.** Results fall from O0 to O3 for every tool — [DecompileBench](https://arxiv.org/html/2505.11340v1). Idioms "drops sharply at O1" even with inlining disabled — [Idioms](https://arxiv.org/html/2502.04536v2). Agents struggle with compiler-generated control flow in complex functions — [Chris Lewis](https://blog.chrislewis.au/using-coding-agents-to-decompile-nintendo-64-games/)
- **C++.** None of Idioms, AutoDecompiler, DecompileBench or 2609.05370 reports C++ results. All are C only — [Idioms](https://arxiv.org/html/2502.04536v2); [DecompileBench](https://arxiv.org/html/2505.11340v1); [2609.05370](https://arxiv.org/abs/2609.05370)
- **Obfuscation [M, 2025].** Seven commercial LLMs were tested. Bogus control flow has low resistance, control-flow flattening moderate, instruction substitution high, and combined techniques produced "universal failure." Complex deobfuscation still needs human guidance — [arXiv 2505.19887](https://arxiv.org/abs/2505.19887)
  - VM protection: ShieldedCode (ICLR 2026) reports 26.95% vs GPT-4o's 22.58% Pass@1 on its lowest-difficulty VM code-generation task. That task generates protected code; it does not undo protection — [ICLR](https://iclr.cc/virtual/2026/poster/10011131)
  - IDA Pro MCP: LLMs "will not perform well on obfuscated code" — [README](https://github.com/mrexodia/ida-pro-mcp)
- **GPU shaders.** PtxDec (ASE, Nov 2025) decompiles NVIDIA PTX to CUDA. It reports a 2.3–3.1× functional-accuracy gain over baselines and cites scarce training pairs and heavy unrolling as the obstacles — [ASE 2025](https://conf.researchr.org/details/ase-2025/ase-2025-papers/86/Enhancing-LLM-to-Decompile-Optimized-PTX-to-Readable-CUDA-for-Tensor-Programs)
  - DXIL-to-SPIR-V translation is already done without AI, by vkd3d-proton's dxil-spirv on Proton. Its author documents how hard that translation is — [themaister blog](https://themaister.net/blog/2021/09/05/my-personal-hell-of-translating-dxil-to-spir-v-part-1/)
- **Context window.** Refinement turns are capped by context length — [AutoDecompiler](https://arxiv.org/pdf/2606.16162). Pagination exists to avoid token overflow — [IDA MCP](https://github.com/mrexodia/ida-pro-mcp). Small tools are used to fight "context rot" — [ReVa](https://cdn.jsdelivr.net/gh/cyberkaida/reverse-engineering-assistant@main/README.md). Avoid verbose tool output — [Chris Lewis](https://blog.chrislewis.au/using-coding-agents-to-decompile-nintendo-64-games/)
- **Correctness.** Passing tests is not equivalence: 4.9–13% hidden divergence, and behavioural match fell from 74% to 62% while build rate rose — [2609.05370](https://arxiv.org/abs/2609.05370). LLM coverage-equivalence trails Hex-Rays by up to 52.2% — [DecompileBench](https://arxiv.org/html/2505.11340v1)
  - Matching decomps suit AI because wrong answers are thrown out automatically — [Dot Esports](https://dotesports.com/general/news/ai-vibe-coded-game-recompilations-pc)
  - "Confidence and accuracy are orthogonal" — [Quesma](https://quesma.com/blog/ghidra-mcp-unlimited-lives/)

### Inferences
- "Deconstruct a modern AAA game and rebuild it optimized" fails on every limit at once: whole-program scope, optimized C++, protection layers, no correctness oracle, and context size. This is an inference from the combined evidence; nobody has tested it directly, because nobody has attempted it credibly.
- Shaders are the most tractable layer. DXIL is LLVM-based, SPIR-V has open tooling, and Proton already translates both. But per-game shader rewriting by AI is undocumented, and anything that hooks into a running game is Tier I under DeckForge's own rules.

### Gaps
- I found no measurement of LLM RE on binaries with millions of lines of code, on C++ virtual dispatch or templates, on Denuvo-class protection, or on DXIL/SPIR-V decompilation by LLMs.
- I found no published expert survey. The limits above come from paper limitation sections and practitioners' write-ups.

---

## Summary table

| Claim / approach | What it really is | Evidence quality | Relevance to optimizing a modern PC game for the Deck |
|---|---|---|---|
| "AI reverse-engineered Elden Ring + Minecraft / CoD" | Human-directed Claude (or Codex) agents write passthrough glue: two live games, existing mod loaders, shared memory, render compositing (Sep–Oct 2026) | Medium: press plus guides; the headline mod is unreleased and unverified | **Negative.** Two processes means more CPU, GPU and RAM. Injection makes it Tier I, and it is impossible on anti-cheat titles. |
| World models (Genie 3, WHAMM/Muse, Oasis/Mirage) | Neural video that imitates gameplay. 60 s sessions, weak persistence, low resolution | High (vendor docs and press), and the vendors state the limits themselves | **None.** These do not run the real game, and they cost more compute than the game itself. |
| LLM decompilers (LLM4Decompile, Idioms, DecLLM, AutoDecompiler) | Single-function C decompilation, about 40–67% re-executable on benchmarks, lower on realistic code | High (peer-reviewed, measured) | **Low.** No C++, no whole-program, weak at O2/O3; correctness overstated (2609.05370). |
| MCP + IDA / Ghidra / Binary Ninja (GhidraMCP, IDA Pro MCP, ReVa, Sidekick) | An analyst's assistant: navigate, rename, explain, patch small things. Claude Code is the common client | Medium (tool docs plus anecdotes; River Raid case) | **Low–moderate.** Useful for understanding config or save formats and finding a setting (Tier S). Not for rebuilding an engine. |
| Claude in N64/GameCube matching decomp (Snowboard Kids 2, Melee) | Agent loops checked by a byte-exact compiler oracle on small MIPS/PowerPC binaries | Medium–high (public progress charts); the Melee AI role is disputed | **Low.** No byte-matching oracle exists for modern PC builds, and the binaries are far larger. |
| AI "recomps" (Wave Race 64, GoldenEye, Banjo-Tooie, Fable 2, MKWii) | AI glue on human-built recompilers and runtimes (N64Recomp, RT64, ReXGlue). Quality widely criticized | Medium (press; community bans) | **None directly.** Recomp removes console-emulation overhead; PC games on the Deck already run natively via Proton. |
| AI Rust rewrites (hl2-rs, benilla, Skate 3) | A new engine that reads the player's own assets. Mostly partial | Low–medium (repos, self-reported) | **Very low** for modern AAA. HL2 (2004) is still partial. |
| "AI deconstructs a modern game and rebuilds it optimized for Deck" | No credible example exists | None | **Not feasible today.** It fails on scale, C++, protection, verification, legal terms, and DeckForge's own R7/Tier rules. |

**Note for the main session (possible memory item):** In Oct 2026, Fede asked whether AI could reverse-engineer and rebuild modern games for the Deck, prompted by viral mashup clips. The research verdict: those clips are Claude-coded passthrough mods, not rebuilds. AI RE is credible only for small console binaries that have a compiler oracle. For DeckForge, AI RE is at most an analysis aid for Tier S settings and formats.
