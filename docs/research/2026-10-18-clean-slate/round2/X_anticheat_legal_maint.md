# Round 2 sceptic report: cross-cutting risks, clusters A–I (anti-cheat, legal, maintenance, prior art)

I am not a lawyer. Everything legal below is a cautious reading, not advice.

## Headline findings
1. **Tier S should be defined by where the binary came from, not by whether it runs inside the game.**
   - Valve's own code already runs inside every Deck game. The gamescope WSI layer is an implicit Vulkan layer (`gamescope/layer/VkLayer_FROG_gamescope_wsi.json.in:13`), and gamescope switches it on for every game (`src/steamcompmgr.cpp:9411`).
   - Anti-cheat tolerates that because every Deck runs the same Valve-shipped binaries. Anything that makes a Deck look non-stock is the risk.
   - EA's stated reason for dropping Linux from Apex (Oct 31, 2024): "no reliable way for us to differentiate a legitimate Steam Deck from a malicious cheat" ([GOL](https://www.gamingonlinux.com/2024/10/ea-respawn-now-block-apex-legends-from-running-on-linux-and-steam-deck/page=1)).
   - **Proposed split:**
     - **S0:** out of process (kernel, sysfs, scheduler, the compositor's own process, reading hidraw).
     - **S1:** stock Valve binaries, changed only through documented environment variables or config files.
     - **Tier I:** anything that replaces a binary or shader, or reads or writes game memory.
2. **The core of Cluster A already ships.** RADV's source says `RADV_FORCE_VRS_CONFIG_FILE` "is used by SteamOS" (`radv_device.c:1512`). SteamOS exposes it as the per-game "Half-Rate Shading" toggle ([SDHQ](https://steamdeckhq.com/tips-and-guides/the-sdhq-performance-settings-encyclopedia/)). Blanket 2x2 therefore gains nothing over the status quo. Only the motion and direction gating is new.
3. **Two Round 1 suggestions must be struck:**
   - 7_outsider's "confirm on a throwaway account". That is probing anti-cheat, and it breaches SSA §4.B.
   - 4_systems' "use sampling perf on anti-cheat titles". See the perf row below.
4. **Both target anti-cheat titles verified:**
   - **Space Marine 2 = Easy Anti-Cheat** [checked]. Its EULA Art. 14.1.1 says EAC "analyses the binary codes of the game and scans the memory" ([Steam EULA](https://store.steampowered.com/eula/2183900_eula_0)).
     - areweanticheatyet still lists SM2 as "Broken", last changed 2024-10-05 [contradicted: it runs on Proton 9 and 11, and the Deck rating is "Playable", [GOL, Sept 2026](https://gamingonlinux.com/2026/09/warhammer-40-000-space-marine-2-update-is-causing-issues-for-steamos-linux-players)].
     - SM2 also has its own "Mods Detected" multiplayer gate, which already misfires on GE-Proton 10-34 ([Focus bug 11284, Jun 2026, "Reproduction in progress"](https://community.focus-entmt.com/focus-entertainment/space-marine-2/bugs/bugs-redirect/11284-eac-client-runtime-never-initializes-on-linux-proton-%E2%80%94-multiplayer-blocked-with-false-mods-detected)).
   - **Helldivers 2 = nProtect GameGuard** [checked: games.json from the AWACY repo]. It runs only because of Valve's per-game Proton Hotfix ([Feb 2024](https://gamingonlinux.com/2024/02/proton-hotfix-updated-to-support-helldivers-2-on-steam-deck-linux), [Apr 2026](https://gamingonlinux.com/2026/04/proton-hotfix-updated-to-fix-helldivers-2-on-linux-steamos-systems)). Any custom Proton build breaks it.

## 1. The nine items in the Tier S audit

Nobody publishes what EAC or BattlEye check on Linux.
- Valve's documentation says only that kernel-space anti-cheat is unsupported and that vendors run in user space ([Steamworks](https://partner.steamgames.com/doc/steamdeck/proton)).
- Epic says only that Proton support is opt-in per game ([EOS, Sept 2021](https://onlineservices.epicgames.com/en-US/news/epic-online-services-launches-anti-cheat-support-for-linux-mac-and-steam-deck)).
- BattlEye says the same ([GOL, Sept 2021](https://www.gamingonlinux.com/2021/09/battleye-confirms-linux-support-for-steam-deck-will-be-opt-in-like-easy-anti-cheat/page=1)).
- EAC's Linux module (`easyanticheat_x64.so`) loads into the same process as Mesa and DXVK. It can therefore see the libraries that process has loaded and its environment variables [inference].

| Item | Verdict | Evidence |
|---|---|---|
| RADV env vars on stock Mesa | **Safe-likely (S1)** | SteamOS uses the VRS config file itself. Hidden cost: `force_vrs_enabled` is part of the pipeline key (`radv_pipeline_graphics.c:1770`). Wave32 perftest flags change the compiled code. Either can make Valve's pre-cache miss (see experiment X3). |
| Custom Mesa via `VK_ICD_FILENAMES` | **Risky / unknown → Tier I** | On Windows, EAC flags GPU-driver DLLs it does not trust: AMD's own signed `amdihk64.dll` after an Apex update ([EA forum, Aug 2026](https://forums.ea.com/discussions/apex-legends-technical-issues-en/apex-s30-crash-eac-untrusted-amdihk64-dll-on-amd-rx-500-series/13622334)), and modded drivers ([Steam, 2022](https://steamcommunity.com/discussions/forum/1/5706632550018613471)). Valve's "any tampering with CS code will result in a VAC ban" over AMD Anti-Lag+ ([Guru3D, Oct 2023](https://www.guru3d.com/story/amd-in-counterstrike-2-can-result-in-vac-ban)) shows "driver-level" is no shield. A custom build also gets a new cache UUID (`radv_physical_device.c:316–345`), which throws away every Valve pre-cache. Weak counter-evidence: distro Mesa builds run EAC games [inference]. |
| Mesa SPIR-V shader replacement | **Risky → Tier I** | It rewrites the game's own code. Shader swaps are the classic wallhack vector, and the SM2 EULA Art. 3 bans modification. Mesa's docs call it debugging/testing and say it usually needs the cache disabled ([docs](https://docs.mesa3d.org/spirv/index.html)). |
| vkd3d-proton / DXVK config on stock DLLs | **Safe-likely (S1)** | Valve and the upstream projects ship per-game entries in these same tables. Custom DXVK or vkd3d builds are Tier I. |
| `sched_setattr` / renice / SCHED_IDLE from another process | **Safe-likely (S0)** | Long-standing precedent: GameMode's daemon changes game niceness, SCHED_ISO and I/O priority ([README](https://github.com/FeralInteractive/gamemode)). Residual risk: the game can observe its own priorities. |
| Reading `/proc/<pid>/task/*/comm` | **Safe (S0)** | Metadata only. Never read `/proc/<pid>/mem`. |
| perf / ftrace | **Split** | Scheduler tracepoints: safe-likely. Sampling with user call graphs: risky, because `perf --call-graph dwarf` copies user stack memory [not re-fetched], which is functionally an external memory reader. uprobes: risky, because they write int3 into code pages that EAC scans (Art. 14.1.1). Debuggers are named EAC targets ([Saber FAQ](https://support.saber.games/hc/en-us/articles/22303848570001-Easy-Anti-Cheat-FAQ)). Use only on games without anti-cheat. |
| gamescope effects and reprojection | **Safe (S0) only inside gamescope's process** | As a new Vulkan layer it is Tier I. lsfg-vk "is a Vulkan layer that hooks into Vulkan applications" ([README](https://cdn.jsdelivr.net/gh/pancaketas/lsfg-vk@develop/README.md)), so it is Tier I under DeckForge's rule. |
| Reading controller hidraw alongside Steam | **Safe (S0) for anti-cheat** | Read only, outside the game. Never write feature reports or inject input. Multi-reader behaviour not verified. |

## 2. Legal lines

**Prior work.** `docs/research/2026-10-12-ai-reverse-engineering/legal_and_policy.md` already covers §1201, LFDA 106/114, CPF 427 Bis and the Capcom and Steam contracts. I add three things:
- **Micro Star v. FormGen** ([154 F.3d 1107](https://law.resource.org/pub/us/case/reporter/F3/154/154.F3d.1107.html)). Data files are derivative works when "the audiovisual displays assume a concrete or permanent form" in them. Galoob is distinguished because there "the audiovisual display was defined by the original game cartridge".
- **Oracle v. Rimini** (9th Cir., Dec 2024). "Mere interoperability isn't enough"; a derivative work "must actually incorporate" the original ([Meeker](https://heathermeeker.com/2025/01/06/9th-circuit-clarifies-derivative-works-of-software-oracle-v-remini-street/)).
- **Thomson Reuters v. Ross** (3d Cir., about Sept 29, 2026, sealed). It affirmed no fair use for AI training in a competing non-generative product ([IPWatchdog](https://ipwatchdog.com/2026/09/30/third-circuit-affirms-revised-fair-use-ruling-against-ross-ai-legal-research-platform-in-sealed-opinion/)). The opinion is sealed, so I could not read its reasoning.

**Mexico** has no open-ended fair use. LFDA Art. 148 is a closed list and requires "sin alterar la obra" ([mley 148](https://mley.mx/LFDA/articulo/148/)).
- Fraction IV allows one private, non-profit copy. A commercial company cannot use it. So bench work should be done by Fede personally, not through FedPacch or Chispa.
- Art. 78: derivative works "sólo podrán ser explotadas cuando hayan sido autorizadas" ([LFDA](https://www.diputados.gob.mx/LeyesBiblio/pdf/LFDA.pdf)).

| Cluster | US | Mexico | Publisher non-objection needed? |
|---|---|---|---|
| **H**: ship lighting measured from rendered output | Medium–high. It records the game's own art-directed lighting in permanent form, which is closer to Micro Star than to Galoob, and non-literal incorporation is what Rimini asks about. Capture also needs UE4SS and a capture layer (EULA breach). | High (Art. 78, no fair use) | **Yes, per publisher.** Rescue: each user harvests GI locally on their own machine and it is never distributed → low–medium. |
| **D1/D2**: ship per-game weights | Medium for distribution. The law is unsettled after Ross, but the weights don't substitute for the game, which helps on market effect. Memorised HUD elements or textures would be reproduction. | Medium (no text-and-data-mining exception) | **Yes, to distribute.** On-device training (D2's least-squares RAISR) needs none. |
| **F**: hash → transform tables | Low. Hashes and compiler flags are facts and methods (§102(b)); Rimini covers interoperability. | Low for the table. Applying the transform locally modifies the program, a right Art. 106 II reserves (on paper). | No for knob tables. Advisable for shader rewrites. |
| **B**: local Replay Lab captures | Low (Sega-style intermediate copying, no distribution) | Low–medium (Art. 148 IV, natural person only) | No. **Hard rule:** captures and raw frames never enter a Claude session, CI or the cloud. Only derived numbers leave the bench. |

**EULAs:**
- **Focus (SM2):** bans modifying, decompiling and derivative works (Art. 3). Bans "third-party software not expressly authorised… that interacts with the Multimedia Program". Allows game content only "strictly for non-commercial purposes" (App. 2). French law.
- **Game Science (Wukong)** ([EULA](https://store.steampowered.com/eula/2358720_eula_0)):
  - bans reverse engineering (2.2(1));
  - bans derivative works "of data" (8.2(4));
  - defines a cheat as "any program that operates externally to the software of the Game and which impacts operations during gameplay" (8.3), which literally covers Cluster C;
  - PRC law.
- **Sony (Helldivers 2):** 1.4(b) bans reverse engineering of "middleware (such as anti-cheat software)"; 1.4(e) bans "unauthorised mods" ([EULA](https://store.steampowered.com/eula/553850_eula_0)).
- **Capcom:** see the prior doc (§8.1(i)–(ii) also ban "analyzing… data used in the Program", which covers Cluster B on Wilds).
- **Remedy (Alan Wake 2):** Epic-only, not on Steam ([3DNews](https://3dnews.ru/1117324/gendirektor-epic-games-podtverdil-chto-alan-wake-2-ne-viydet-v-steam)). EULA [could not verify].
- **GSC (Stalker 2):** the Steam EULA page failed to load [could not verify]. The official Zone Kit mod SDK ([itc.ua](https://itc.ua/en/news/s-t-a-l-k-e-r-2-will-receive-patch-1-5-next-week-new-weapons-zonekit-editor-and-more/)) is the most permissive signal among these publishers.
- **Licence trap:** lsfg-vk moved to CC BY-NC-ND 4.0 on Aug 28, 2026 ([GOL](https://www.gamingonlinux.com/2026/08/lossless-scaling-frame-generation-on-linux-lsfg-vk-moves-away-from-github-changes-license-due-to-ai-slop-forks/)). DeckForge (MIT, donation-funded) cannot fork or bundle it, only point users to it.

## 3. Maintenance burden and upstream paths

SteamOS's root filesystem is read-only, and updates overwrite it ([README](https://github.com/Chloe-ko/SteamDeckPersistentRootFs/blob/main/README.md)). Any system-level gamescope, kernel or Mesa replacement is therefore a recurring fight with every update.

- **A.** Low for the daemon. Steam owns the same VRS file, so collisions are possible (X2). **Upstream:** Valve built the knob for power saving ([Phoronix 2022](https://www.phoronix.com/news/RADV-Dynamic-VRS)), and per-game VRS options sit in a Draft MR ([MR 16471](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/16471)). Ask Valve to add a "motion" mode to the toggle; the burden then goes to zero.
- **B.** Very high. Pass hashes churn with game patches *and* vkd3d-proton updates, and replays break across driver versions. The UE5 cvar subset is low. Not upstreamable, except as publisher "Deck presets".
- **C.** Medium. Steam and steamos-manager rewrite sysfs values, and SteamOS changed the frequency driver to amd-pstate-epp in 3.7.5 ([SimpleDeckyTDP README](https://github.com/aarron-lee/SimpleDeckyTDP)). **Most upstreamable cluster:**
  - LimitNICE → SteamOS (a one-line limits file, per Proton's `docs/THREAD_PRIORITY.md`);
  - epp_boost → kernel;
  - critical-thread hints → Proton.
- **D1.** Very high: per-game retraining, OptiScaler's proxy DLLs overwritten by game updates, and decky-framegen's FSR4 build compiled from AMD's leaked SDK ([GOL](https://www.gamingonlinux.com/2025/09/steam-deck-plugin-adds-amd-fsr4-support-to-improve-visuals/page=1/)), so never depend on that path.
- **D2.** Medium–high: needs gamescope integration. The generic pass can go upstream to gamescope; the per-game weights cannot.
- **E.** Medium: re-validate each game patch (automatable on the bench). Keep to user-config files; SM2's "Mods Detected" gate is a reason not to touch the install directory.
- **F.** High: hash churn, cache loss, and a Mesa fork. **Upstream rescue:** turn the findings into per-app entries in Mesa driconf and vkd3d-proton/DXVK tables. That is how the Wilds `no_upload_hvv` fix shipped (`device_workarounds.c:160–164`, per 4_systems). The burden then disappears.
- **G.** High unless Valve takes it; a gamescope fork is not viable for a non-engineer.
- **H.** Very high: data per version, server hotfixes, and keys tied to Steam build IDs that don't exist for Alan Wake 2.
- **I.** A custom Proton build means a Proton fork for every release, and it loses Valve's per-game hotfixes. Publisher pressure is the lowest code burden.

## 4. What already exists
- **A:** the SteamOS Half-Rate Shading toggle. No motion-gated tool found.
- **C:**
  - SimpleDeckyTDP: governor and EPP controls, SMT, CPU boost, per-game TDP;
  - PowerTools: CPU threads and frequencies, GPU frequency, PPT, per-game settings; its GitHub repo was archived in 2023 ([repo](https://github.com/NGnius/PowerTools));
  - GameMode;
  - CryoUtilities: a HugePages toggle ([README](https://cdn.jsdelivr.net/gh/cryobyte33/steam-deck-utilities@main/README.md)).
  - **New:** deadline-aware, per-critical-thread control.
- **D:** decky-framegen/OptiScaler; Reshadeck, which drives gamescope's ReShade path ([repo](https://github.com/safijari/Reshadeck)).
- **G:** lsfg-vk and decky-lsfg-vk do interpolation in-process ([repo](https://github.com/xXJSONDeruloXx/decky-lsfg-vk)). An input-latched warp is new.
- **I:** proton-cachyos x86-64-v3 builds ([pkg](https://packages.cachyos.org/package/cachyos-v3/x86_64_v3/proton-cachyos-slr)).
- **B, E (perceptual scoring at the Deck's viewing geometry), F (automated search) and H:** nothing equivalent found.

## Matrix

| Cluster | Tier claim holds? | Anti-cheat risk, SM2 | Legal risk | Maintenance | Already exists? |
|---|---|---|---|---|---|
| A VRS | Yes for the env/config path (S1). No for a Mesa patch or layer (I). | Low (Valve's path); a custom Mesa patch is high | Low | Low (high with a Mesa fork) | Yes: Half-Rate Shading |
| B Interleaver / Lab | No: the layer and capture are I. UE5 cvars are S1. | Excluded; cvars low | Low; contract breach on Wilds | Very high | GFXReconstruct only |
| C Scheduling / power | Yes (S0), except stack-sampling perf and uprobes | Low / unknown; uprobes high | Low (Wukong EULA text) | Medium | Partly (4 tools) |
| D1 | Tier I, correctly labelled | Excluded | Medium | Very high | OptiScaler / FSR4 |
| D2 | Yes as a gamescope pass | Low | Medium shipped / low on-device | Medium–high | Reshadeck host |
| E | Yes (user config only) | Low | Low | Medium | Human guides only |
| F | Split: env vars S1; SPIR-V replacement and custom RADV are I | Medium (env) / high (replacement) | Low | High | Upstream tables |
| G | Yes inside gamescope; no as a layer | Low | Low | High | lsfg-vk (interpolation) |
| H | No | Excluded | High shipped | Very high | None |
| I (Proton build) | No | High | Low | Very high | proton-cachyos |

## Falsification experiments (bench Deck, ≤2 weeks, no anti-cheat titles on Tier I)

**X1. Hash churn (F, B).**
- **Setup:** Wukong Benchmark Tool (no anti-cheat). Dump the top-30 pipeline BLAKE3 hashes under Proton 10, 11 and Experimental.
- **Pass:** ≥90% of hashes stable across one Proton version change.
- **Kill:** hash-keyed shipping is dead if <70% survive.
- **Owner:** switch the Proton version three times. About 2 days.

**X2. Override (A, C).**
- **Setup:** a daemon sets the VRS file, EPP, GPU clock floor and per-core caps. Fede follows a checklist: QAM toggles, TDP slider, suspend, reboot, game launch. The daemon reads every value back once per second.
- **Kill:** "set-and-forget" is dead if any value reverts in >5% of seconds, or if Steam rewrites the VRS file.
- **Owner:** about 1 hour of button presses.

**X3. Pre-cache cost (S1 env vars, custom Mesa).**
- **Setup:** first-launch runs after a cache reset: baseline vs `RADV_FORCE_VRS=2x2` vs `pswave32` vs a custom-built Mesa.
- **Measure:** gamescope frame times of 50 ms or more in the first 5 minutes.
- **Kill:** a knob is not shippable if it adds more than 20 such spikes over baseline.

**X4. Vendor policy (all S0/S1 items, SM2 and HD2).**
- **Setup:** Fede sends the nine-item table, using a template, to Focus/Saber support (EAC developer contact) and to Arrowhead/Sony.
- **Judge:** the written answer for each item.
- **Default:** no answer within 14 days means the item stays Tier I for that game. No account testing.

**X5. Memorisation gate (D, before any distribution).**
- **Setup:** train D2, run model inversion and nearest-patch search.
- **Kill:** distribution is dead if any 64×64 output patch has SSIM ≥0.9 to a training patch, or if 2 of 3 blind viewers recognise a HUD element or logo.
- **Owner:** view 20 image pairs.

## Verdicts

| Cluster | Verdict |
|---|---|
| A | SURVIVES WITH CHANGES: drive the existing SteamOS VRS file; the gain is only motion gating; Tier I for any Mesa patch until it is upstream. |
| B | SURVIVES WITH CHANGES: UE5 cvars only on anti-cheat games; the Lab stays on the bench as Fede's personal work. |
| C | SURVIVES: S0, excluding stack-sampling perf and uprobes; push LimitNICE and epp_boost upstream. |
| D1 | SURVIVES WITH CHANGES: non-anti-cheat games only; no FSR4-leak lineage; non-objection before shipping weights. |
| D2 | SURVIVES WITH CHANGES: on-device training only, as a native gamescope pass. |
| E | SURVIVES: user-config files only. |
| F | SURVIVES WITH CHANGES: env-var search (S1) plus upstream tables. SPIR-V replacement and custom RADV are DEAD as Tier S; tried rescuing via "exact transforms", but anti-cheat cannot verify exactness. |
| G | SURVIVES WITH CHANGES: inside gamescope, pitched to Valve upstream. |
| H | DEAD as a shipped dataset. Tried rescues: measurements-not-assets (fails Micro Star), and hosting by contributors (still distribution). SURVIVES as local, per-user harvesting on games without anti-cheat. |
| I | Custom Proton DEAD (breaks HD2's hotfix; Tier I). Publisher pressure SURVIVES. |

## What would change my mind
- **A:** X2 shows Steam never rewrites the VRS file, and motion gating beats the static toggle by ≥1.5 ms.
- **B:** a publisher provides a "Deck update-rate" cvar set itself.
- **C:** Epic or Saber writes that external renice/sysfs changes are prohibited.
- **D1:** OptiScaler is shipped by Valve (e.g. through Proton), which removes the proxy-DLL burden.
- **D2:** X5 passes and a publisher non-objects.
- **E:** SM2's "Mods Detected" fires on user-config edits.
- **F:** X1 shows ≥90% hash stability and Mesa accepts per-app ACO knobs in driconf.
- **G:** Valve adds input-latched reprojection to gamescope, or declines it in writing.
- **H:** a publisher grants non-objection.
- **I:** Valve ships a znver2 Proton.

**Key facts to keep:**
- SteamOS already exposes forced VRS as "Half-Rate Shading".
- lsfg-vk is now CC BY-NC-ND 4.0.
- HD2 depends on Valve's Proton Hotfix.
- areweanticheatyet's SM2 entry is stale.
- Bench captures and raw frames must never be uploaded to Claude, CI or the cloud.
