# Can AI reverse engineer a modern game and rebuild it for the Steam Deck?

Status: **ASSESSMENT**, 2026-10-12. An independent verifier reviewed it (PASS WITH FIXES, 13
findings), and this version addresses them.

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
- **(est.)**: an estimate or inference.
- **[checked]**: I confirmed it myself on the primary page.

**This is not legal advice.** The legal ratings below are the researcher's and my estimates, not
rulings.

---

## 1. The short answer

**No, not for modern games, and the viral clips aren't doing what they appear to do.**

1. **The mashups are not rebuilds** [state §1, checked].
   - People direct Claude agents (and some Codex) to write "passthrough" mods. Both games run at
     the same time, linked through existing community mod loaders, and one game's picture is laid
     over the other's. VGC calls it "an elaborate green-screen".
   - Nothing is optimized. Running two games at once roughly doubles the load.
   - The famous Elden Ring + Minecraft mod hasn't been released.
2. **AI reverse engineering has a documented win only on a small, old game with an automatic
   answer-checker** [state §2, aaa §5].
   - The one documented case is an N64 game, where a compiler confirms every recovered function
     byte for byte.
   - Claude Opus 4.5 took that project from about 25% to about 45% matched in about three weeks,
     more than the previous three months, by doing the easiest functions first.
   - The project still took almost two years, and humans finished the last functions.
   - A GameCube claim (Super Smash Bros. Melee) is unverified.
   - Nobody has done this for a PS5-era game, with or without AI [precedents, bottom line].
3. **A modern AAA game is a different scale of problem** [aaa §1, §4; legal §3]:
   - **Code size:** hundreds of megabytes, about 100,000–200,000 functions (est.).
   - **Protection:** Monster Hunter Wilds ships Denuvo anti-tamper [checked], plus a reported
     Capcom anti-tamper layer.
   - **No checker:** nothing tells you an answer is right.
   - **Patches:** a new version every few weeks; Wilds had 28 updates in 16 months.
4. **The big gains need source code** [aaa §3, §6; precedents Q5].
   - Real ports of PS4- and PS5-era games to weaker hardware got their 2–3× (est.) by rewriting
     algorithms and restructuring content. With full source code, that took a studio about a year
     (Witcher 3 on Switch started at 10 fps).
   - Without source code, what's reachable in Wilds tops out around 1.2–1.5× in the field, at a
     "potato" look, and about 1.0–1.15× in CPU-limited hubs (est.). It may be lower: today's ~30
     fps baseline already uses upscaling.
5. **The rebuild-and-repackage version is the legally riskiest form of the idea** (est.)
   [legal §1–§3, §6]:
   - **US:** getting usable code out of Wilds very likely means getting past Denuvo and Capcom's
     anti-tamper. That is a separate legal violation (DMCA §1201), and fair use is no defence to it.
     Some in-between techniques have no clear precedent either way.
   - **Mexico:** decompiling is a right reserved to the copyright owner. Circumventing protection
     is a crime when done knowingly and for profit (6 months to 6 years).
   - **Redistribution:** rebuilt game code is plain infringement.
   - **My line:** I won't help defeat DRM, anti-tamper or anti-cheat, or rebuild and redistribute a
     game's code.

## 2. What the viral mashups really are

| What people think | What is happening | Source |
|---|---|---|
| "AI reverse-engineered Elden Ring and merged it with Minecraft" | A Claude-coded "passthrough" mod: two games run at once and one is overlaid on the other ([Decrypt, 8 Oct 2026, checked](https://decrypt.co/380407/ai-video-game-mod-mashups-are-taking-off-here-are-the-wackiest-examples); [VGC, 5 Oct 2026, checked](https://videogameschronicle.com/news/ai-game-mashup-videos-on-social-media-spark-debate-and-backlash-among-players-and-modders/)). Its creator hasn't published how it was built. It is likely built like the community's reference design, SkyCraft: one game runs hidden and passes its state and picture over shared memory, and the other draws the final frame (est.) | [state §1] |
| "Elden Ring + Call of Duty" | Most likely a Black Ops gun mode inside the same mod, not a separate merge | [state §1] |
| "The AI understood the whole game" | The heavy lifting is existing mod loaders (Skyrim's SKSE, Minecraft's Fabric, Unreal's UE4SS); the AI writes the glue. A community guide calls decompiling a "last resort" | [state §1]; [AI game modding guide](https://github.com/trevaintdead/ai-game-modding-guides/blob/main/guides/02-passthrough-mods.md) |
| "AI world models can recreate games" | A separate track (Google Genie 3, Microsoft's Quake II demo). Sessions last 60 seconds, objects vanish within about a second, and the image is low-resolution. They don't run the real game | [state §1] |

**What it means for the Deck:** a passthrough mod adds a second game, extra memory and extra
frame delay. That makes it the opposite of an optimization.

## 3. What AI reverse engineering can and can't do today

| Capability | Evidence | Verdict for a modern AAA game |
|---|---|---|
| **Decompile single functions** (research systems) | 40–67% of benchmark functions pass the benchmark's tests. Accuracy drops on optimized code, and no results exist for C++. A Sep 2026 study found output that compiles and passes tests is sometimes still wrong: about 5%, up to 13% [state §2–§3] | Too unreliable without a checker |
| **Analyst assistant** (Claude Code connected to the IDA or Ghidra disassemblers) | A common setup; Claude is the most often documented model (anecdotal). On an 8 KB Atari game, Claude found the lives counter but misnamed the game. Each tool call took ~30 s [state §2] | Fine for small, checkable questions |
| **Matching decompilation of N64 games** | One documented case (above); human-finished after almost two years [state §2, aaa §5] | Works because a compiler checks every answer. No such checker exists for modern PC builds |
| **AI-built "recompiled" ports of N64 and Xbox 360 games** | Built on recompilers that humans made; widely criticized. The N64 recomp community bans AI-made showcases [state §2] | Not applicable. Recompiling removes console-emulation overhead, and PC games already run natively on the Deck through Proton |
| **Read protected (Denuvo, virtualized) code** | AI tools "will not perform well on obfuscated code". Layered obfuscation caused "universal failure" in one 2025 test [state §3] | Blocked, before counting the legal problem |
| **Understand a whole modern engine** | Based on Devil May Cry 5's ~128 MB *unprotected* executable (Wilds' size is unknown): one decompiled read is about 50–100 full 1M-token Claude contexts, or ~150 disassembled (est.). Fetching 150,000 functions one at a time at ~30 s each takes ~50 days (est.) [aaa §1] | Not feasible. The only workable approach is studying the few hot spots a profiler points to |

## 4. What could make Wilds cheaper without source code

**Routes, with realistic gains (all gains est.)** [aaa §3, §6]:

| Route | Example | Gain on the Deck | Look | Allowed for anti-cheat games? |
|---|---|---|---|---|
| Lower resolution + upscaler | 1024×640 with FSR/XeSS | Up to ~1.3–1.5× on resolution-bound passes; less once fixed costs count | Softer | Yes |
| Engine settings exposed through REFramework (a runtime mod loader for Capcom games) | Global illumination and fog off, level-of-detail bias, culling, shadows below Lowest | Each 2–20%, overlapping | Flat lighting, pop-in, cutscene breakage | No |
| Shader constant edits | Fewer samples or ray-march steps | 5–10% | Subtle to moderate | No |
| Smaller textures; new low-poly meshes | Asset repacks | Textures ~0% unless memory is short; meshes small beyond the level-of-detail bias | Blurrier | No |
| Rewriting algorithms (new GI, new grass, baked lighting) | What Witcher 3's Switch port did | Large | Comparable, if re-tuned | No; needs source code |

**Stacked together** (est.):
- **Field:** about 1.2–1.5×, from ~30 fps to about 36–45 fps, at a "potato" look.
- **CPU-bound hubs:** about 1.0–1.15×.

That is roughly what the community's Deck mod bundle already claimed (30–45 fps). Its author
marked it obsolete after Capcom's 2026 patches [precedents Q4]. It falls well short of your goal of
High-like visuals.

**For comparison, studios with full source code** [precedents Q5]:
- Elden Ring on Switch 2 ships at 432–864p handheld and 30–35 fps with the PS4 feature set.
- Witcher 3 on Switch shipped at 540p handheld and 30 fps after about a year of work.

**The one high-leverage pattern: spot a defect and report it** [precedents Q3]:
- **What happened:** a Redditor noticed Wilds repeatedly re-checking DLC ownership. Bypassing that
  check reportedly lifted minimum fps from 24 to 43.
- **Caution on the method:** tampering with a DLC check is risky territory. The only Wilds bans
  reported were for a DLC-unlock mod [legal §3].
- **The legitimate part** is noticing the symptom and reporting it.
- **The outcome:** Capcom shipped its own fix about two weeks later, measured at +8–20% on minimum
  fps.
- **Similar cases:** Dragon's Dogma 2's NPC "thinking" cost and Alan Wake 2's non-mesh-shader path
  were fixed by the studios themselves.
- **Limits:** spotting such symptoms needs no protected code (est.), but these finds are rare and
  lucky, not a product.

## 5. Legal and policy picture (ratings are estimates)

| Activity | US | Mexico | Licence / ban risk | Anthropic policy | Source |
|---|---|---|---|---|---|
| Study your own *unprotected* copy | Low (fair use: *Sega v. Accolade*, *Sony v. Connectix*) | Medium on paper, low in practice. Decompiling is reserved to the copyright owner (LFDA Art. 106-IV); private use is not criminal without profit | Breaks Capcom's EULA on paper; low ban risk offline | Generally fine | [legal §1–§3, risk table] |
| Get past Denuvo / anti-tamper to read Wilds' code | High: very likely DMCA §1201 circumvention; fair use is no defence | High: LFDA 114 Bis; criminal if knowingly and for profit (CPF 427 Bis, 6 months–6 years). The Supreme Court upheld the regime in May 2024 | EULA bans "cracking" | Likely prohibited (bypassing security controls). I won't do it either way | [legal §1–§2, §5] |
| Runtime mod for personal, offline use (REFramework style) | Low, but an untested grey area. If a mod disables part of the anti-tamper, circumvention questions arise | Low | The EULA bans modifying on paper. In practice Capcom tolerates solo mods; the reported bans were for DLC unlocks | Generally fine | [legal §3, §6] |
| Distribute a patch of *original* code or config that needs the player's own copy | Low | Low–medium | Takedown risk | Fine | [legal §6] |
| Distribute a patch containing decompiled or reimplemented game code | Medium–high (the re3 GTA project was sued and settled) | Medium | Takedowns, legal threats | Likely prohibited (IP) | [legal §1, §6] |
| Distribute a rebuilt or "repackaged" game | High: the Super Mario 64 PC port was taken down as an unauthorized derivative work. Stripping DRM adds §1201 trafficking; the Yuzu emulator's makers settled such a suit for $2.4M | High | Bans, takedowns, legal threats | Likely prohibited | [legal §1, §6] |
| Change an anti-cheat game (Space Marine 2) | Low through Saber's official tools or its unencrypted game data files, in private lobbies. High ban risk for injecting while Easy Anti-Cheat runs; high legal risk if anti-cheat is bypassed | Same | Modded players are barred from public sessions | Bypassing anti-cheat likely prohibited | [legal §3–§4] |

## 6. Can Claude or Claude Code do it?

**What Claude can likely help with (est.):**
- REFramework scripts and config tools;
- shader edits inside a measured test loop;
- building the measurement harness;
- explaining a handful of decompiled functions, but only for code that isn't DRM- or
  anti-tamper-protected. Its accuracy on modern optimized C++ is unmeasured [aaa §5];
- writing glue code between existing mod loaders. That is how the mashups were made, and Claude is
  the model most often credited for them.

**What Claude can't do:**
- hold a modern engine in its head;
- read protected code;
- judge visual quality without measurements.

It also won't touch your Deck directly. That is a project rule (R7), not a technical limit; a bench
runner would do it.

**What I won't do:** help defeat DRM, anti-tamper or anti-cheat, or rebuild and redistribute a
game's code.

## 7. Recommendation

**Don't pursue "reverse engineer and rebuild."** On this evidence it is:
- technically out of reach for modern games;
- legally the riskiest form of the idea;
- no better than routes that don't rebuild anything, which top out around 1.2–1.5× (est.) at a
  worse look.

**What the evidence does support, if you want any technical work at all** [aaa §6]:
- **Measured REFramework-parameter and shader-constant tuning** for Wilds (not anti-cheat games),
  inside an automatic measurement harness. Expect the "potato" ceiling above, not High-like
  visuals.
- **Spotting performance defects and reporting them** to developers.

**The wider decision is already made.** In our previous conversation you decided DeckForge's
optimizer isn't worth building, and this research doesn't change that.

**The streaming options come from that conversation, not from this research:**
- stream from hardware you own (the Austin PC; the M3 Max for single-player games);
- subscribe to GeForce NOW only in months you play something heavy;
- enjoy the games the Deck handles well, with Lossless Scaling on top.
