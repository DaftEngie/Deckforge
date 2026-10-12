# Can AI reverse engineer a modern game and rebuild it for the Steam Deck?

Status: **ASSESSMENT**, 2026-10-12.

It answers Fede's proposal:

> *"People have been using AI to reverse engineer games… mixing Elden Ring and Minecraft or Elden
> Ring and Call of Duty… the tool takes in the game, reverse engineers it, understands it, and
> then changes the code to optimize it for Steam Deck… make PS5-era games PS4-era games…
> Can we do some research on how it's done, what AI models are used, and if we can achieve it
> using Claude or Claude Code?"*

**Evidence.** Four research notes in `docs/research/2026-10-12-ai-reverse-engineering/`:

| Cited as | File | Question |
|---|---|---|
| [state] | `ai_re_state_of_the_art.md` | What the viral mashups really are; what AI reverse engineering can do today, with which models |
| [precedents] | `precedents.md` | Fan decompilations, recompiled ports, performance patches, "potato" mods, official downports |
| [legal] | `legal_and_policy.md` | Copyright, anti-circumvention law in the US and Mexico, game licences, anti-cheat, Anthropic's policy |
| [aaa] | `modern_aaa_feasibility.md` | Whether a modern AAA game can be understood and made 1.5–3× cheaper this way |

**Labels:**
- **(est.)**: my estimate or inference.
- **[checked]**: I confirmed it myself on the primary page.

This is not legal advice.

---

## 1. The short answer

**No, not for modern games. The viral clips aren't doing what they appear to do.**

1. **The mashups are not rebuilds** [state §1, checked].
   - People direct Claude agents (and some Codex) to write "passthrough" mods. Both games run at
     the same time, linked through existing community mod loaders and shared memory.
   - One game's picture is laid over the other's. VGC calls it "an elaborate green-screen".
   - Nothing is optimized. Running two games at once roughly doubles the load.
   - The famous Elden Ring + Minecraft mod hasn't been released.
2. **Where AI reverse engineering really works, it works on small, old games with an automatic
   answer-checker** [state §2, precedents Q1–Q2]:
   - It works on N64 and GameCube games, where a compiler confirms every recovered function byte
     for byte.
   - There, Claude Opus 4.5 roughly doubled one project's pace.
   - Even so, that project took almost two years, and humans finished it.
   - Nobody has done this for a PS5-era game, with or without AI.
3. **A modern AAA game is a different scale of problem** [aaa §1–§2, §4]:
   - **Code size:** hundreds of megabytes of protected code, about 100,000–200,000 functions (est.).
   - **Protection:** Monster Hunter Wilds ships Denuvo [checked], which is woven through the code.
   - **No checker:** nothing tells you an answer is right.
   - **Patches:** a new game version every few weeks. Wilds had 28 updates in 16 months.
4. **The big gains need source code** [aaa §3, precedents Q5].
   - Real "PS5-to-weaker-hardware" ports got their 2–3× by rewriting algorithms and restructuring
     the game's content.
   - With full source code, that took a studio about a year. Witcher 3 on Switch, for example,
     started at 10 fps.
   - Without source code, the reachable ceiling in Wilds is about 1.2–1.5× in the field, at a
     "potato" look. CPU-limited hubs gain about 1.0–1.15× (est.).
5. **The rebuild-and-repackage version is the legally riskiest form of the idea** [legal §1–§3, §6]:
   - Getting at Wilds' code means getting past Denuvo and Capcom's anti-tamper. In the US that is
     a separate offence even when studying your own copy is fair use.
   - In Mexico, decompiling is a right reserved to the copyright owner. Circumventing protection
     is a crime there when done knowingly and for profit (6 months to 6 years).
   - Redistributing rebuilt game code is plain infringement.
   - This is also where I stop: I won't help defeat DRM, anti-tamper or anti-cheat, or rebuild and
     redistribute a game's code.

## 2. What the viral mashups really are

| What people think | What is happening | Source |
|---|---|---|
| "AI reverse-engineered Elden Ring and merged it with Minecraft" | A Claude-coded "passthrough" mod. Minecraft runs hidden, sends its state and picture over shared memory, and Elden Ring draws the final frame | [Decrypt, 8 Oct 2026, checked](https://decrypt.co/380407/ai-video-game-mod-mashups-are-taking-off-here-are-the-wackiest-examples); [VGC, 5 Oct 2026, checked](https://videogameschronicle.com/news/ai-game-mashup-videos-on-social-media-spark-debate-and-backlash-among-players-and-modders/) |
| "Elden Ring + Call of Duty" | Most likely a Black Ops gun mode inside the same mod, not a separate merge [state §1] | Decrypt |
| "The AI understood the whole game" | The heavy lifting is existing mod loaders (Skyrim's SKSE, Minecraft's Fabric, Unreal's UE4SS). The AI writes the glue between them. A community guide calls decompiling a "last resort" [state §1] | [AI game modding guide](https://github.com/trevaintdead/ai-game-modding-guides/blob/main/guides/02-passthrough-mods.md) |
| "AI world models can recreate games" | A separate track (Google Genie 3, Microsoft's Quake II demo). Sessions last 60 seconds, objects vanish within about a second, and the image is low-resolution. They don't run the real game | [state §1] |

**What it means for the Deck:** a passthrough mod adds a second game, extra memory and extra
frame delay. It is the opposite of an optimization.

## 3. What AI reverse engineering can and can't do today

| Capability | Evidence | Verdict for a modern AAA game |
|---|---|---|
| Decompile single functions (research systems) | 40–67% of benchmark functions come out right. Accuracy drops on optimized code, and there are no C++ results. A Sep 2026 study found that output which compiles and passes tests is often still wrong: the build rate rose from 75% to 90% while the true behaviour match fell from 74% to 62% [state §2–§3] | Too unreliable without a checker |
| Analyst assistant: Claude Code + IDA/Ghidra connectors | Common setup; Claude is the most-used model. On an 8 KB Atari game, Claude found the lives counter but misnamed the game. Each tool call took ~30 s [state §2] | Fine for small, checkable questions |
| Matching decompilation of N64/GameCube games | Claude Opus 4.5 moved Snowboard Kids 2 from ~25% to ~45% matched in ~3 weeks. Humans finished it after almost two years [state §2, precedents Q2] | Works only because a compiler checks every answer; no such checker exists for modern PC builds |
| AI-built "recompiled" ports of N64/Xbox 360 games | Built on human-made recompilers; widely criticized. The N64 recomp community bans AI-made showcases [state §2] | Not applicable: recompiling removes console-emulation overhead, and PC games already run natively on the Deck through Proton |
| Read protected (Denuvo, virtualized) code | AI tools "will not perform well on obfuscated code". Layered obfuscation caused "universal failure" in one 2025 test [state §3] | Blocked, before even counting the legal problem |
| Understand a whole modern engine | One read of a decompiled ~128 MB executable is roughly 50–160 full 1M-token Claude contexts. Fetching 150,000 functions one at a time at ~30 s each takes ~50 days (est.) [aaa §1] | Not feasible. The only workable approach is studying the few hot spots a profiler points to |

## 4. What could actually make Wilds cheaper, without source code

**Reachable routes**, each with its realistic gain [aaa §3, §6]:

| Route | Example | Gain on the Deck (est.) | Look | Allowed for anti-cheat games? |
|---|---|---|---|---|
| Lower resolution + upscaler | 1024×640 with FSR/XeSS | Up to ~1.3–1.5× when GPU-bound | Softer | Yes |
| Engine settings exposed through REFramework (a runtime mod loader for Capcom games) | Global illumination and fog off, level-of-detail bias, culling, shadows below Lowest | Each 2–20%, overlapping | Flat lighting, pop-in, cutscene breakage | No |
| Shader constant edits | Fewer samples or ray-march steps | 5–10% | Subtle to moderate | No |
| Smaller textures or new low-poly meshes | Asset repacks | ~0% GPU time unless memory is short | Blurrier | No |
| Rewriting algorithms (new GI, new grass, baked lighting) | What Witcher 3's Switch port did | Large | Comparable, if re-tuned | No; needs source code |

**Stacked together** (est.):
- **Field:** about 1.2–1.5×, from ~30 fps to about 36–45 fps, at a "potato" look.
- **CPU-bound hubs:** about 1.0–1.15×.

That roughly matches what the community's Deck mod bundle already claimed (30–45 fps). Its author
marked it obsolete after Capcom's 2026 patches [precedents Q4]. It falls well short of your goal of
High-like visuals.

**For comparison, studios with full source code:**
- Elden Ring on Switch 2 ships at 432–864p handheld and 30–35 fps with the PS4 feature set.
- Witcher 3 on Switch shipped at 540p handheld and 30 fps after about a year of work.

[precedents Q5]

**The one high-leverage legitimate pattern: find a bug and report it.**
- A Redditor noticed Wilds repeatedly re-checking DLC ownership. A bypass reportedly lifted
  minimum fps from 24 to 43.
- Capcom shipped an official fix about two weeks later, measured at +8–20% on minimums
  [precedents Q3].
- Similar cases: Dragon's Dogma 2's NPC "thinking" cost and Alan Wake 2's non-mesh-shader path
  were fixed by the studios themselves.
- Finding such defects by observing the game, then reporting them, helps every player and needs
  no protected code. These finds are rare and lucky, though, not a product.

## 5. Legal and policy picture

| Activity | US | Mexico | Licence / ban risk | Anthropic policy | Source |
|---|---|---|---|---|---|
| Study your own unprotected copy | Low (fair use: *Sega v. Accolade*, *Sony v. Connectix*) | Decompiling is reserved to the copyright owner (LFDA Art. 106-IV); low enforcement for private use | Breaks Capcom's EULA on paper | Fine | [legal §1–§3] |
| Get past Denuvo / anti-tamper to read Wilds' code | **High**: DMCA §1201; fair use is no defence | **High**: LFDA 114 Bis; criminal if knowingly and for profit (CPF 427 Bis, 6 months–6 years); upheld by the Supreme Court in May 2024 | EULA "cracking" ban | **Not allowed** (bypassing security controls) | [legal §1–§2, §5] |
| Runtime mod for personal, offline use (REFramework style) | Low | Low | Tolerated in practice for solo mods; reported Wilds bans were for DLC unlocks | Fine | [legal §3, §6] |
| Distribute a patch of original code that needs the player's own copy | Low–medium (re3 was still sued) | Medium | Takedown risk | Fine if original code and no circumvention | [legal §6] |
| Distribute a rebuilt or "repackaged" game | **High** (Super Mario 64 port taken down; Yuzu emulator settled for $2.4M) | **High** | Bans, takedowns, legal threats | **Not allowed** | [legal §1, §6] |
| Change an anti-cheat game | Low through official tools; high if anti-cheat is bypassed | Same | Space Marine 2 allows mods only in private lobbies, via Saber's own editor | Bypassing anti-cheat not allowed | [legal §3–§4] |

## 6. Can Claude or Claude Code do it?

**What Claude can do well:**
- write REFramework scripts and config tools;
- make shader edits inside a measured test loop;
- explain a handful of decompiled functions a profiler points to;
- build the measurement harness;
- write glue code between existing mod loaders. That is exactly how the mashups were made, and
  Claude is the model most often credited for them.

**What Claude can't do:**
- hold a modern engine in its head;
- read protected code;
- judge visual quality without measurements;
- run on your Deck.

**What I won't do:** help defeat DRM, anti-tamper or anti-cheat, or rebuild and redistribute a
game's code.

## 7. Recommendation

**Don't pursue "reverse engineer and rebuild."** On the evidence it is:
- technically out of reach for modern games;
- at best a 1.2–1.5× gain that looks worse;
- the riskiest legal form of the whole DeckForge idea.

**This is the same answer as the last three investigations, from a different direction.** A modern
game looks good when a strong graphics chip renders it. The practical options are the ones from
our last conversation:
1. Stream from hardware you already own: the Austin PC, or the M3 Max for single-player games.
2. Subscribe to GeForce NOW only in the months you play something heavy.
3. Play the games the Deck handles well, with Lossless Scaling on top.

**DeckForge's research stays useful as a public record.** I can wrap it up whenever you want.
