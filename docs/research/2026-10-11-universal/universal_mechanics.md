# Universal, anti-cheat-safe settings optimizer for SteamOS / Steam Deck: feasibility and mechanics (research as of 2026-10-11)

Labels: **[docs]** = vendor documentation; **[measured]** = someone ran a test; **[claimed]** = a vendor, user or press statement with no test behind it; **[inference]** = my reasoning, not sourced. Dates are publication dates as fetched.

Process note: the WebSearch budget for this turn ran out near the end. The Proton-version benchmarks, Creation/id/Decima/Snowdrop/Anvil settings formats and the EAC integrity-catalog docs could not be searched, and they are listed under Gaps. They can be picked up in a follow-up.

## Overall takeaway

A universal optimizer is feasible as a two-layer design.

- **Layer 1: engine-agnostic levers** that work for every game with no injection. These are gamescope resolution, upscaling and frame cap, refresh pairing, TDP and clocks via steamos-manager, env-var options for the Proton/DXVK/RADV stack, and shader caches.
- **Layer 2: engine-family adapters** for settings files. Unreal Engine is the only family large and uniform enough to justify a real cvar-level adapter. Unity has a uniform storage location but no uniform semantics. Each proprietary engine needs a small per-title adapter.

The binding constraint is anti-cheat *policy*, not technology. Publishers, not the AC vendors, decide what counts as a cheat. PUBG's rule is the clearest precedent: config edits are a violation if they produce "changes that cannot be made via the in-game settings menu." Marvel Rivals (2026) actively detects and penalizes modified configs.

Valve's SDK 1.65 hooks (July 2026) are developer-side and coarse. They will not make a third-party tuner redundant soon, but they show where Valve is heading.

---

## 1. Engine share of demanding 2023–2026 releases

### Takeaway
Nobody publishes a statistic for the "demanding / AAA" subset. Across all Steam releases, Unity leads by title count and Unreal leads by units sold, and custom engines fell below half of units sold in 2024. Unreal is the only engine family big enough among demanding titles to justify deep generic support.

### Cited Findings
- **[claimed/estimate, VGI report, Jan 2025]** Share of Steam games *released*:
  - 2023: Unity 50%, Unreal 26%, Godot+GameMaker 8%, custom/in-house 16%.
  - 2024: Unity 50–51% (two slides disagree), Unreal 28%, Godot+GameMaker 9%, custom 13%.
  - Source: [VGI / Sensor Tower, The Big Game Engines Report of 2025 (PDF)](https://app.sensortower.com/vgi/assets/reports/The_Big_Game_Engines_Report_of_2025.pdf)
- **[claimed/estimate, same report]** Share of *units sold*:
  - 2023: Unity 27%, Unreal 19%, Godot/GameMaker 1%, custom 52%.
  - 2024: Unity 26%, Unreal 31%, Godot/GameMaker 2%, custom 42%.
  - Custom engines fell to "less than half of all units sold" in 2024 "for the first time." The report credits UE5 and titles such as Black Myth: Wukong for Unreal's jump.
  - Source: [VGI report PDF](https://app.sensortower.com/vgi/assets/reports/The_Big_Game_Engines_Report_of_2025.pdf)
- **[claimed, same report]** The "larger end of the market gets increasingly dominated by custom game engines," while Unreal "is quickly winning share from custom engines, becoming the go-to game engine for many AAA studios." Despite the 2025 title, the report contains no 2025 data and no clean AAA-only split. Sources: [VGI PDF](https://app.sensortower.com/vgi/assets/reports/The_Big_Game_Engines_Report_of_2025.pdf); [Sensor Tower blog, Jan 2025](https://sensortower.com/blog/the-big-game-engines-report-of-2025)
- **[measured detection counts, SteamDB, fetched 2026-10-11]** Games detected per engine:
  - Unity 66,528; Unreal 20,824 (no UE4/UE5 split shown); GameMaker 6,563; Godot 5,115; Frostbite 43; RE Engine 40; Source 2 13.
  - SteamDB says it is "certainly undercounting."
  - Source: [SteamDB Technologies](https://steamdb.info/tech/)

### Inferences
- **[inference, unverified title list]** By title count, roughly 40–55% of demanding 2023–2026 PC releases relevant to a Deck tuner use UE4/UE5. This is my estimate from known titles, not a published statistic, and needs a proper count before it goes into any public material. Examples:
  - UE5: Black Myth: Wukong, S.T.A.L.K.E.R. 2, Silent Hill 2, Remnant II, Lords of the Fallen, Marvel Rivals, THE FINALS, ARC Raiders, Clair Obscur, Oblivion Remastered, Borderlands 4.
  - UE4: Hogwarts Legacy, Jedi: Survivor, FF7 Rebirth, Lies of P, Tekken 8.
- **[inference]** The remainder splits across about 10 proprietary engines, each shipping only 1–5 demanding PC titles a year:
  - RE Engine (Capcom), Frostbite (EA), id Tech / Motor, Decima (Sony/Kojima), Snowdrop and Anvil (Ubisoft), Creation 2 (Bethesda), Swarm (Saber), Source 2 (Valve), Stingray-derived (Helldivers 2).
- **[inference]** This shape argues for one deep UE adapter, one shallow Unity adapter (resolution and command line only), and per-title adapters for the top proprietary titles.

### Gaps
- No published engine share for "demanding" or AAA titles in 2023–2026. VGI's 1M+-units chart could not be read from the PDF text.
- No public UE4 vs UE5 split; SteamDB lumps them together.
- No 2025–2026 statistics found.

---

## 2. Unreal Engine: universal user-settings control

### Takeaway
Writing cvars to Engine.ini works in many shipped UE games. The engine's priority system lets `[SystemSettings]` override scalability groups and GameUserSettings. It does *not* override values the game sets in code or via the console, and cheat-flagged cvars behave differently in shipping builds.

`sg.*` levels are re-defined per project, so "sg.Shadow=1" is not comparable across games. Raw `r.*` cvars are portable syntactically, but their cost differs by game.

The well-known community "Ultra+" packs typically rely on UE4SS injection and disabling EAC. They are not a model DeckForge can copy for anti-cheat games.

### Cited Findings
- **[docs] Cvar priority order, lowest to highest:**
  - SetByConstructor → Scalability → GameSetting ("in game UI or from file") → ProjectSetting → DeviceProfile → SystemSettingsIni → ConsoleVariablesIni → Commandline → Code → Console.
  - A lower-priority set is rejected with a log line, e.g. "wasn't set (Priority SetByDeviceProfile < SetByCommandline)."
  - Source: [Epic, Console Variables in C++](https://dev.epicgames.com/documentation/en-us/unreal-engine/console-variables-cplusplus-in-unreal-engine)
- **[docs] Flag descriptions:**
  - `ECVF_Cheat`: "behave differently in a final release build."
  - `ECVF_ReadOnly`: "cannot be changed by the user (from console)."
  - `ECVF_ScalabilityGroup`: these cvars control others and their "names should start with 'sg.'"
  - `ECVF_SetBySystemSettingsIni`: "Used by the [ConsoleVariables] section of Engine.ini as well as FSystemSettings."
  - Source: [Epic, EConsoleVariableFlags](https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Core/EConsoleVariableFlags)
- **[docs] Scalability groups:**
  - The reference page lists `sg.*` groups at levels 0–3 (Low to Epic), defined in `BaseScalability.ini`.
  - "You can customize any of the Scalability Settings used in your Unreal Engine project" via `DefaultScalability.ini`.
  - Source: [Epic, Scalability Reference](https://dev.epicgames.com/documentation/en-us/unreal-engine/scalability-reference-for-unreal-engine)
- **[docs] Lumen budgets:**
  - "Lumen targets 30 and 60 frames per second (fps) on consoles with 8ms and 4ms frame budgets at 1080p."
  - Scalability tiers: Epic = 30 fps console budget; High = 60 fps console; Medium = Switch 2 / medium-spec PC; "Low scalability level disables Lumen features."
  - Key knobs: `sg.GlobalIlluminationQuality`, `sg.ReflectionQuality`, `r.Lumen.Reflections.*`, `r.Lumen.ScreenProbeGather.*` (DownsampleFactor, TracingOctahedronResolution), RadianceCache probe budgets, `r.LumenScene.*.UpdateFactor`, async-compute toggles.
  - Switching Lumen reflections to SSR saves "1 ms on Xbox Series S."
  - Source: [Epic, Lumen Performance Guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine)
- **[docs/community wiki] PCGamingWiki on UE5 config:**
  - User config is "usually located in %LOCALAPPDATA%\<Game>\Saved\Config\" and "should take priority over all others."
  - Engine.ini accepts cvars "only if entered into a [SystemSettings] section."
  - "Some games don't acknowledge user config changes."
  - Scalability.ini edits may be "ignored depending on the graphics settings."
  - Some games store values in savegames, which override them on load.
  - "Most games ship with the console disabled," and re-enabling it needs "third-party DLL injection" (UE4SS).
  - Source: [PCGamingWiki, Engine:Unreal Engine 5](https://www.pcgamingwiki.com/wiki/Engine:Unreal_Engine_5)
- **[claimed, mod page, 2026-01-25] Ultra+ for Lords of the Fallen:**
  - Requires a script to disable EAC and ships prepackaged UE4SS.
  - Warns that separate Engine.ini mods may cause crashes.
  - The team says it "can modify most things in UE games," with game-specific tips.
  - Source: [Nexus Mods, Ultra+ LotF](https://www.nexusmods.com/lordsofthefallen2023/mods/82)
- **[claimed, 2026-07-31] Marvel Rivals (UE5) detects config edits.** Players with configs saw a penalty pop-up reading "Unauthorized modification to your client detected." The configs involved changed rendering quality, mouse smoothing and acceleration, and hero sprites. Source: [EsportNow](https://esportnow.gg/games/news/a-ban-wave-is-hitting-modded-marvel-rivals-players)

### Inferences
- **[inference] Engine.ini outranks the game's own settings.** `[SystemSettings]` (SystemSettingsIni, priority 5) beats GameUserSettings/menu values (GameSetting, 2) and `sg.*` scalability (1). An Engine.ini tweak therefore overrides the in-game menu, which by definition makes it "non-menu-reachable." That has direct anti-cheat policy consequences (see §4).
- **[inference] What defeats it:**
  - games that apply settings via `SetByCode` on load or when settings are applied;
  - cvars compiled out or cheat-flagged in shipping;
  - games that overwrite the user ini or keep settings in saves.
- **[inference] Launch options can carry cvars.** The command line outranks the ini. UE's `-ini:Engine:[SystemSettings]:r.X=Y` and `-ExecCmds=` switches could in principle carry cvars without touching files, but I did not verify that they survive in shipping builds. Test this.
- **[inference] Proton path:**
  - UE5: `compatdata/<appid>/pfx/drive_c/users/steamuser/AppData/Local/<ProjectName>/Saved/Config/Windows/` (`GameUserSettings.ini`, `Engine.ini`).
  - UE4: the last folder is `WindowsNoEditor/`.
  - Some publishers relocate config to `Documents/My Games/<Game>/Saved/Config/`.
  - The project folder name is the internal project name, not the store title. A discovery step must glob for `*/Saved/Config/Windows*/GameUserSettings.ini` inside the prefix.
  - PCGamingWiki confirms only the part up to `Saved\Config\`; the subfolder names come from prior knowledge.
- **[inference] Can a cross-game cost model be built?**
  - Engine-level `r.*` cvars (Lumen, Nanite, VSM `r.Shadow.Virtual.*`, TSR `r.TSR.*`, `r.ScreenPercentage`) exist in every game on a given UE version. A cvar *catalog* is therefore portable.
  - *Costs* are content-dependent, and Epic publishes only coarse budgets (Lumen 4 ms / 8 ms), not per-cvar ms.
  - A cross-game cost model has to be learned from measurement, with Epic's tiers as priors. It cannot be derived from documentation.
  - `sg.*` values must be read per game, because projects redefine them.
- **[inference] Community tweak transfer:** generic Engine.ini packs transfer *syntactically* but not *reliably*:
  - packs crash games or are silently ignored;
  - the polished packs (Ultra+) use injection.
  - Expect a "works in many, verify each" hit rate.

### Gaps
- No published list of UE games that block or overwrite Engine.ini. Evidence is anecdotal (Steam and Nexus threads).
- Exact shipping-build behavior of `ECVF_Cheat` (ignored vs. locked) is not stated in the docs.
- No per-cvar ms cost tables for VSM, Nanite or TSR found.
- Whether UE command-line cvar injection works in shipping builds is unverified.

---

## 3. Unity and other engines' settings formats

### Takeaway
Unity has a uniform storage location (the registry; `user.reg` under Wine) but no uniform keys or semantics. Only resolution and fullscreen keys and command-line flags are universal.

RE Engine, Frostbite and Stingray-derived settings are plain text. Swarm (Space Marine 2) is reportedly encrypted. I could not verify Creation, id Tech, Decima, Snowdrop or Anvil this session.

### Cited Findings
- **[docs] Unity PlayerPrefs:**
  - On Windows standalone, stored at `HKCU\Software\<Company>\<Product>`; on Linux native, `~/.config/unity3d/<Company>/<Product>`.
  - "Unity stores PlayerPrefs in a local registry, without encryption."
  - Key names get a hash suffix, e.g. `DeckBase_h3232628825`.
  - Source: [Unity PlayerPrefs](https://docs.unity3d.com/ScriptReference/PlayerPrefs.html)
- **[community wiki] Universal Unity keys and flags:**
  - Registry keys: `Screenmanager Resolution Width_h182942802`, `Screenmanager Resolution Height_h2627697771`, `Screenmanager Is Fullscreen mode_h3981298716`.
  - Command-line flags: `-screen-width`, `-screen-height`, `-screen-fullscreen`, `-force-vulkan`, `-force-d3d11`, `-window-mode exclusive`, `-popupwindow`.
  - Source: [PCGamingWiki, Engine:Unity](https://www.pcgamingwiki.com/wiki/Engine:Unity)
- **[claimed, 2025-03-02] RE Engine (Monster Hunter Wilds):**
  - `config.ini` lives in the install folder (`steamapps/common/MonsterHunterWilds`) as plain `key=value`.
  - It includes non-menu keys such as `ParallelBuildProcessorCount=16` and `RenderWorkerThreadPriorityAboveNormal=Enable`.
  - Users set it read-only to stop overwrites.
  - Source: [Icy Veins](https://www.icy-veins.com/monster-hunter-wilds/news/monster-hunter-wilds-performance-optimization-fps-boost/)
- **[claimed, 2025-10-13] Frostbite (Battlefield 6):**
  - `PROFSAVE_profile` lives at `Documents/Battlefield 6/settings/<steam|ea|epic>/` as plain text, e.g. `GstRender.ShadowQuality 0`.
  - A user-created `user.cfg` in the install folder accepts console commands (`Thread.ProcessorCount 8`, `WorldRender.MotionBlurEnable 0`).
  - Source: [MeinMMO](https://mein-mmo.de/battlefield-6-user-cfg-profsave_profile-aendern/)
- **[claimed by a user, 2024-09-13] Space Marine 2 (Swarm):** "the settings file is actually encrypted!" and "there is no way to edit the game's user settings out of the game." Source: [Steam forum](https://steamcommunity.com/app/2183900/discussions/0/4760956432755644947)
- **[claimed by a user, 2024-02-09] Helldivers 2:**
  - `compatdata/553850/pfx/drive_c/users/steamuser/AppData/Roaming/Arrowhead/Helldivers2/user_settings.config` is plain `key = value` (e.g. `fullscreen = false`).
  - The thread reports no bans.
  - Source: [Steam forum](https://steamcommunity.com/app/553850/discussions/0/4206994256761719530)

### Inferences
- **[inference] Unity under Proton:** PlayerPrefs land in `compatdata/<appid>/pfx/user.reg` under `[Software\\<Company>\\<Product>]`.
  - Editing a Wine `.reg` file safely requires the prefix to be idle; wineserver rewrites it on exit.
  - Many Unity games keep graphics settings in their own JSON or binary files under `AppData/LocalLow/<Company>/<Product>/`, so a Unity adapter is per-title beyond resolution.
- **[inference, prior knowledge, unverified this session]** These should be treated as hypotheses until checked:
  - Creation Engine (Starfield): plain ini under `Documents/My Games/Starfield/`.
  - id Tech (Doom Eternal): plain-text cvar `.local` config under `Saved Games/id Software/`.
  - Snowdrop and Anvil: per-game ini/cfg under Documents.
  - Decima ports: unknown.
- **[inference]** RE Engine's `config.ini` sits in the *install folder*. Install files are more likely to fall under anti-tamper or anti-cheat integrity scans than AppData files, and Steam "verify files" can revert them.

### Gaps
- Not verified: Creation, id Tech, Decima, Snowdrop, Anvil and Source 2 formats.
- Not verified: the Unity value encoding in `user.reg` (int as dword, float, and string as hex binary).
- Not verified: whether Space Marine 2's encryption is real or just a binary format.

---

## 4. Anti-cheat policy on settings-file edits

### Takeaway
I found **no public statement from Easy Anti-Cheat or BattlEye** on config edits. Enforcement is set per game by the publisher.

The clearest precedent is PUBG's rule that config edits producing "changes that cannot be made via the in-game settings menu" violate the rules. Marvel Rivals went from "please don't" (Dec 2024) to client-side detection with penalties (Jul–Aug 2026).

A safe policy: in online or anti-cheat games, write only values reachable from the menu, in the game's own user-settings file, never cvars, never install-folder files, and never while the game is running. Keep a per-game "no writes at all" list.

### Cited Findings
- **[claimed, PUBG FAQ, c. 2017; article undated in fetch]**
  - "editing any game files to gain an unfair advantage is against the Rules of Conduct. This includes changing any game configuration files to result in changes that cannot be made via the in-game settings menu."
  - It was prompted by ini edits that removed fog.
  - Source: [TechRaptor](https://techraptor.net/gaming/news/editing-playerunknowns-battlegrounds-files-is-now-bannable-offense)
- **[claimed, 2024-12-19] Marvel Rivals:** the community manager said "we kindly advise against modifying any game files in Marvel Rivals, as it may lead to unexpected issues." Players were editing .ini files for mouse acceleration and frame rate. Sources: [TalkEsport](https://www.talkesport.com/marvel-rivals/marvel-rivals-avoid-modifying-game-files/); [PCGamesN](https://www.pcgamesn.com/marvel-rivals/game-files)
- **[claimed, 2026-07-31] Marvel Rivals ban wave:** a penalty pop-up "Unauthorized modification to your client detected" hit players running configs that tweak rendering quality, mouse smoothing and acceleration, or sprites. Source: [EsportNow](https://esportnow.gg/games/news/a-ban-wave-is-hitting-modded-marvel-rivals-players)
- **[claimed, article dated 2026-08-17 as fetched] Marvel Rivals match-cancel abuse:**
  - Players dropped config files in mid-match to trigger detection and cancel losing games.
  - NetEase warned that modded configs "for performance or optimisation" could bring "temporary suspension."
  - The date may be off by a year; verify it.
  - Source: [PC Gamer](https://pcgamer.com/games/third-person-shooter/marvel-rivals-players-are-messing-with-their-config-files-to-cancel-games-with-no-consequence-before-they-get-a-loss)
- **[claimed, 2026-01-09] ARC Raiders (UE5, EAC):** players edited local configs to force ultra-wide FOV and "high-visibility presets." Source: [MP1st](https://mp1st.com/news/arc-raiders-config-settings-unfair-advantages)
- **[docs, updated 2026-02-26] Embark's ban policy:**
  - It does not mention config files.
  - It bans "third-party tools that affect gameplay" and warns "external software, even unintentionally that interacts with the game may trigger anti-cheat violations."
  - Source: [Embark ban policy](https://id.embark.games/arc-raiders/support/faq/161-ban-and-enforcement-policy)
- **[docs, undated] EA, Battlefield 6:** the rules page covers third-party cheat software and exploits and requires Javelin. It is silent on `user.cfg` and PROFSAVE. Source: [EA Help](https://help.ea.com/en/articles/battlefield/battlefield-6/play-by-the-rules)

### Inferences
- **[inference] Proposed safe policy:**
  - **Tier S-online** (any game with online anti-cheat or competitive multiplayer):
    - edit only the keys the in-game menu writes, only to values the menu offers;
    - write only to the user settings file (AppData or Documents), never the install folder;
    - write only when the game is not running;
    - no Engine.ini `[SystemSettings]` and no `user.cfg`.
    - Rationale: by UE's priority rules, `[SystemSettings]` overrides the menu, so it is non-menu-reachable by construction.
  - **Hard denylist** (no file writes at all): titles with demonstrated config detection, starting with Marvel Rivals.
  - **Tier S-offline** (single-player, no anti-cheat): cvar-level edits allowed.
  - Prefer engine-agnostic levers (gamescope, TDP, frame cap), which never touch the game.
- **[inference] Where the risk is concentrated.** From these examples, enforcement targets competitive advantage: foliage, fog, FOV, visibility, input smoothing. A Deck tuner that only *lowers* quality toward menu presets carries little *intent* risk. Detection is mechanical, though (file presence or hash), so intent does not protect the user. The menu-reachable rule is the defensible line.

### Gaps
- No EAC or BattlEye vendor statement on config files found.
- No EAC integrity-catalog documentation on whether user-dir configs are covered (search budget ran out).
- No Valorant/Vanguard or Helldivers 2/GameGuard statement on config edits found.

---

## 5. Measurement without injection

### Takeaway
Yes. Gamescope already measures each app's frame time out-of-process and sends it to mangoapp (the Steam performance overlay) over a System V message queue. It can also write stats to a file (`--stats-path`). amdgpu sysfs and hwmon expose GPU busy %, clocks and SoC power to any process.

Screenshots come from the compositor, so external capture is possible. Built-in benchmarks exist in about 168 PC games overall, but only about 23 of them are 2023–2026 releases. Scene reproduction will mostly have to rely on save files plus a fixed camera or idle capture.

### Cited Findings
- **[docs] mangoapp** "takes frame information from gamescope." It is a separate transparent OpenGL app and is "no longer directly injected into the game." Source: [mangoapp(1) man page](https://man.archlinux.org/man/mangoapp.1.en.txt)
- **[source code] gamescope `mangoapp.cpp`:**
  - Message struct `mangoapp_msg_v1` fields: `pid`, `app_frametime_ns`, `fsrUpscale`, `fsrSharpness`, `visible_frametime_ns`, `latency_ns`, `outputWidth/Height`, `displayRefresh`, `bAppWantsHDR`, `bSteamFocused`, `engineName[40]`.
  - IPC: `ftok("mangoapp", 65)` plus `msgget` and non-blocking `msgsnd`.
  - `app_frametime` is the delta between successive app frame commits that gamescope sees.
  - Source: [gamescope src/mangoapp.cpp](https://raw.githubusercontent.com/ValveSoftware/gamescope/master/src/mangoapp.cpp)
- **[docs] gamescope options:**
  - `-T/--stats-path` "Write statistics to specified path".
  - `--framerate-limit`.
  - `-F` filter: linear, nearest, fsr, nis, pixel.
  - `--sharpness` 0–20.
  - `-w/-h` internal resolution.
  - Super+S takes a screenshot.
  - Sources: [DeepWiki gamescope CLI](https://deepwiki.com/ValveSoftware/gamescope/5.1-command-line-options); [gamescope man summary](https://linuxcommandlibrary.com/man/gamescope)
- **[docs] amdgpu sysfs and hwmon:**
  - `gpu_busy_percent` is SMU-computed load.
  - `gpu_metrics` dumps temperature, frequency, utilization, power and throttler status.
  - hwmon `power1_average` / `power1_input`: "power used by the SoC in microWatts. On APUs this includes the CPU."
  - `power1_cap`, `pp_dpm_sclk`, and `power_dpm_force_performance_level` are also exposed.
  - Source: [Linux kernel amdgpu thermal/power docs](https://docs.kernel.org/gpu/amdgpu/thermal.html)
- **[docs, reverse-engineered] Steam client hooks:** `GameSessions.RegisterForScreenshotNotification` and `RegisterForAppLifetimeNotifications` are exposed to frontend plugins. Source: [SteamBrew docs, GameSessions](https://docs.steambrew.app/plugins/ts/client/src/interfaces/GameSessions)
- **[claimed list, updated 2026-07-20] Built-in benchmarks:**
  - 168 unique PC games have built-in benchmarks; 23 are 2023–2026 releases.
  - Examples: Monster Hunter Wilds, Doom: The Dark Ages, AC Shadows, AC Mirage, AC Black Flag Resynced (2026), Forza Horizon 6 (2026), CoD MW3/BO6/BO7, F1 23/24/25, Avatar: Frontiers of Pandora, Marvel Rivals, HZD Remastered, Returnal, Civ 7, Anno 117, Talos Principle 2, Company of Heroes 3, Forspoken, Skull and Bones, The Crew Motorfest.
  - Source: [XS Reviews list](https://xsreviews.co.uk/news/games-with-built-in-benchmarks-how-to-benchmark-your-pc/)
- **[docs, 2026-10-01/05] Valve's Deck framerate data:**
  - Valve added a Steam Deck framerate *distribution* chart for developers, under Technical Tools > Steam Hardware Compatibility Review.
  - It uses opted-in users' data, Verified titles only.
  - Sources: [Steamworks news](https://store.steampowered.com/news/group/4145017/view/676258795703239816); [GamingOnLinux](https://gamingonlinux.com/2026/10/valve-give-game-developers-more-steam-deck-framerate-data)

### Inferences
- **[inference] Reading the queue directly is a bad idea.** SysV `msgrcv` is destructive, so a second reader would compete with mangoapp and blank the Steam overlay. Better options:
  - read `--stats-path` output, which requires adding a flag to the gamescope-session command line (a SteamOS session config change);
  - or run only when the overlay is off.
  - Either way this is compositor-side and invisible to the game, so it is anti-cheat safe.
- **[inference] Steam's performance overlay does not load a layer into the game; mangoapp is out of process.** Steam's regular in-game overlay (gameoverlayrenderer) *is* in-process, but anti-cheat titles already tolerate it.
- **[inference] Screenshots:** gamescope screenshots are composited output (post-upscale, including HUD). That suits perceptual image-quality scoring of what the user sees, but not render-resolution analysis. Decky can be notified of Steam screenshots via `RegisterForScreenshotNotification` and then read the files.
- **[inference] Benchmark coverage.** About 23 benchmarked titles out of a few hundred demanding releases is roughly 5–15% coverage. UE games rarely have one. Scene reproduction should default to save-file plus idle-scene or fixed-route captures, with benchmarks as a bonus. Most benchmarks also need manual menu navigation; few expose a command-line flag.

### Gaps
- No primary doc for the gamescope `--stats-path` file format, or for a scriptable screenshot trigger (a gamescopectl-style command or X atom).
- No count of which benchmarks are command-line-launchable.

---

## 6. Integration surface (Decky, alternatives, upstream)

### Takeaway
A Decky plugin can do everything DeckForge needs at runtime through reverse-engineered SteamClient APIs: set launch options, react to launch and exit, set resolution overrides, read and write the per-game performance profile. These APIs are undocumented and break with Steam client updates.

Decky had breakages in March, April, June and July 2026 that needed loader patches. The robust core should therefore be a standalone service plus CLI, with Decky as a thin optional UI.

### Cited Findings
- **[reverse-engineered docs] `SteamClient.Apps`:**
  - `SetAppLaunchOptions(appId, launchOptions)`.
  - `GetLaunchOptionsForApp(appId)`, which "does not retrieve launch/argument options inputted by the user."
  - `RegisterForGameActionStart(cb)`.
  - `RunGame(appId, launchOptions, …)`, where options are "appended before the ones specified in the application's settings."
  - `TerminateApp`, `SetAppResolutionOverride(appId, resolution)`.
  - Source: [SteamBrew docs, Apps](https://docs.steambrew.app/plugins/ts/client/src/interfaces/Apps)
- **[reverse-engineered docs]** `GameSessions.RegisterForAppLifetimeNotifications(cb)` handles launch and exit. Source: [SteamBrew GameSessions](https://docs.steambrew.app/plugins/ts/client/src/interfaces/GameSessions)
- **[claimed, PowerTools issue, undated] Steam's per-game performance profile:**
  - "There's a front-end JS API exposed in `SteamClient.System.Perf`" whose data is "encoded in base64" protobuf.
  - Steam config is separated into "Global" and "App," then by AppID.
  - The PowerTools author warns "There is no guarantee that the format of the binary representation won't change."
  - Source: [PowerTools #88](https://github.com/NGnius/PowerTools/issues/88)
- **[claimed, 2026-04-29]** The Steam Deck client Stable update of about April 28, 2026 left Decky "currently unusable." Source: [PCGames.de](https://www.pcgames.de/Steam-Deck-Hardware-277668/News/Neues-Update-Decky-Loader-1529736/)
- **[docs] Decky releases in 2026:**
  - v3.2.3 (Mar 31): a reroll after an "Axios supply-chain attack," plus "Fixes for march 19th 2026 beta."
  - v3.2.4-pre1 (May 15) and v3.2.4 (May 28): beta UI fixes.
  - v3.2.5-pre1 (Jun 6) and v3.2.6 (Jun 24): "fixes for june 2026 beta errorboundary."
  - v3.2.7-pre1 (Jul 14).
  - v3.2.8-pre1 (Jul 25) and v3.2.8 (Sep 2): "support renamed Steam initialization API."
  - Source: [Decky Loader releases](https://github.com/SteamDeckHomebrew/decky-loader/releases)
- **[claimed, 2026-05-15] steamos-manager:**
  - Valve open-sourced it in May 2025. It handles "TDP management, GPU clock management, BIOS updates."
  - It is hosted at gitlab.steamos.cloud/holo/steamos-manager, with a Steam Frame branch.
  - Source: [GamingOnLinux](https://gamingonlinux.com/2026/05/were-inching-closer-to-the-steam-frame-release-with-a-steamos-manager-update)
- **[claimed]** A community fork package `steamos-manager-hhd` exists on the AUR. Source: [AUR](https://aur.archlinux.org/packages/steamos-manager-hhd)
- **[claimed]** NVIDIA engineers contributed gamescope support, so Valve's gamescope repo does take outside contributions from vendors. Source: [Phoronix](https://www.phoronix.com/news/Gamescope-NVIDIA-Pending)

### Inferences
- **[inference] Decky stability.** There was no Decky release between Mar 31 and May 15, 2026. If the April 28 breakage was in the loader, Stable users went 2–4 weeks without a fix. Decky is "mostly working, breaks roughly monthly on beta and occasionally on Stable." An optimizer that must not leave games in a half-configured state cannot depend on it.
- **[inference] Recommended architecture:**
  - a systemd **user** service plus CLI as the source of truth;
  - it writes launch options via `localconfig.vdf` only while Steam is closed (already known), or via Decky's `SetAppLaunchOptions` while Steam is running;
  - it sets TDP and clocks via steamos-manager D-Bus;
  - an optional Decky front-end for the per-game UI and the launch/exit hooks.
  - A Flatpak desktop app is fine for Desktop Mode, but sandboxing complicates D-Bus and `compatdata` access.
- **[inference] Writing Steam's own per-game profile via the Perf protobuf is attractive.** It shows in Steam's UI and is what the user expects. It is also the most fragile surface; treat it as best-effort and verify it by reading hwmon `power1_cap`.
- **[inference] Upstream contribution.** Valve has opened steamos-manager, and its gamescope repo takes vendor contributions (NVIDIA). I found no evidence of Valve merging *third-party user features* into the SteamOS UI. Upstreaming small, generic things (gamescope stats, steamos-manager D-Bus properties) is plausible. Upstreaming a "tuner" is not.

### Gaps
- No contribution policy found for steamos-manager.
- No root-cause write-up of the April 2026 Decky break.
- `SteamClient.System.Perf` method signatures were not retrieved (doc fetch failed).

---

## 7. Steamworks SDK 1.65 hardware-default and performance-reporting APIs

### Takeaway
These are *in-game, developer-side* calls:

- one returns a coarse tier or device token, so the game can choose its own preset;
- two report the game's chosen quality tier and render resolution into Valve's opt-in framerate telemetry.

Third parties cannot read the developer's per-device mapping, cannot contribute defaults (the partner site only), and cannot read the telemetry. They signal Valve's direction (crowd-sourced fps-by-setting data). They will not replace per-game tuning toward a locked 45 fps soon.

### Cited Findings
- **[claimed, 2026-07-24]** SDK 1.65 removed `ISteamUtils::IsRunningOnSteamDeck()` and added:
  - `IsRunningOnSteamHardware()` ("for analytics, support or diagnostic purposes");
  - `GetSteamHardwareDefaultConfig()`;
  - `IsRunningUnderProton()`;
  - and, on ISteamApps, `SetGamePerformanceSetting()` and `SetGameRenderResolution()`.
  - Sources: [GamingOnLinux](https://www.gamingonlinux.com/2026/07/valves-steamworks-sdk-v1-65-brings-changes-for-steam-machine-steam-frame-and-steam-deck/page=1/); [SteamDeckHQ](https://steamdeckhq.com/news/steamworks-sdk-165-update/)
- **[docs] `GetSteamHardwareDefaultConfig`:**
  - Returns `ESteamDefaultHardwareConfig`: None 0, Low 1, Medium 2, High 3, Max 4, SteamDeck 5, SteamMachine 6, SteamFrame 7.
  - "By default, this method will return a value corresponding to the device type returned by IsRunningOnSteamHardware."
  - "You can also change what value the Steam Client returns per device through the Steamworks Partner Site."
  - It may return a value for third-party handhelds of similar performance (e.g. SteamOS devices).
  - Source: [Steamworks ISteamUtils](https://partner.steamgames.com/doc/api/ISteamUtils)
- **[docs] `SetGamePerformanceSetting(EGamePerformanceSetting)`:**
  - Enum: NotSet 0, Low 1, Medium 2, High 3, Ultra 4, Custom 4 (as fetched; Ultra and Custom showing the same value is likely a docs typo).
  - `SetGameRenderResolution(unWidth, unHeight)` "Allows the game to report to Steam servers what the render resolution settings are set to."
  - "This data will be included with anonymous framerate data if the user has opted into sharing of those data."
  - The signatures on the page omit the parameters, an inconsistency in the docs.
  - Source: [Steamworks ISteamApps](https://partner.steamgames.com/doc/api/ISteamApps)
- **[claimed, Oct 2026]** The developer-facing Deck framerate distribution chart covers Verified titles only. Source: [GamingOnLinux](https://gamingonlinux.com/2026/10/valve-give-game-developers-more-steam-deck-framerate-data)
- **[claimed, Apr 2026, headline only, not fetched]** Press reported Valve may show crowd-sourced fps estimates on store pages. Source: [TechSpot](https://www.techspot.com/news/111951-steam-could-soon-show-estimated-fps-based-crowd.html)

### Inferences
- **[inference] What a third party can do with these:**
  - It cannot read a game's "Deck default" from outside. The mapping lives on Valve's servers and resolves to a token the game interprets with its own code.
  - It can query `IsRunningUnderProton`-style facts only from its own Steam API context, which is useless for settings.
  - Valve's telemetry is not exposed to third parties.
- **[inference] Redundancy over time.** Adoption requires SDK integration per game, so it will be slow and mostly new titles. Even when adopted, it picks a preset tier. It does not tune individual settings, does not target a 45 fps lock, and does not adapt per scene.
  - The real long-term threat is Valve exposing "fps at setting X on Deck" to users, or auto-applying "Deck defaults" in the client.
  - DeckForge should position as finer-grained, measurement-driven, and covering back-catalog games that never adopt the SDK.
  - If Valve ever publishes the aggregate data, DeckForge should consume it as a prior.

### Gaps
- No public data on adoption of `GetSteamHardwareDefaultConfig` by shipped games.
- Unclear whether `SetGamePerformanceSetting` data feeds the October 2026 charts.

---

## 8. Universal runtime levers (no per-game knowledge, no injection)

### Takeaway
The highest-value universal levers are:

- gamescope resolution and upscaling (largest gain, visible image cost);
- frame cap with refresh pairing (pacing and power, no image cost);
- TDP/GPU steering via steamos-manager.

Env-var options for the translation and driver stack (`DXVK_CONFIG`, `VKD3D_CONFIG`, RADV) are universal per graphics API. Swap/zram tweaks measured as no gain. Shader pre-caching helps stutter, not fps. I found almost no *measured* Deck numbers for these levers in 2025–2026; DeckForge's bench runner will have to produce them.

### Cited Findings
- **[docs] gamescope:** internal resolution `-w/-h`, upscale filter `-F fsr|nis|linear|nearest|pixel`, `--sharpness 0–20`, `--framerate-limit` ("Cap the frame rate without changing the refresh rate"). Sources: [DeepWiki](https://deepwiki.com/ValveSoftware/gamescope/5.1-command-line-options); [man summary](https://linuxcommandlibrary.com/man/gamescope)
- **[docs] DXVK environment config:**
  - `DXVK_CONFIG="dxgi.hideAmdGpu = True; dxgi.syncInterval = 0"` sets config "through the environment instead of a configuration file," with `;` as separator.
  - `DXVK_CONFIG_FILE` points to a `dxvk.conf`.
  - Source: [DXVK README](https://raw.githubusercontent.com/doitsujin/dxvk/master/README.md)
- **[docs]** amdgpu `pp_dpm_sclk` and `power_dpm_force_performance_level` are the clock-control surface; hwmon `power1_cap` reflects the TDP cap. Source: [kernel amdgpu docs](https://docs.kernel.org/gpu/amdgpu/thermal.html)
- **[measured, single game, 2023-04-21] CryoUtilities on Hogwarts Legacy:**
  - The recommended settings (swap and swappiness) plus a 4 GB UMA framebuffer "keeps basically every result within margin of error."
  - 1% lows on the Low preset took a "12% hit" the author couldn't reproduce.
  - ZRAM gave "Worse to identical performance."
  - Source: [SteamDeckHQ](https://steamdeckhq.com/news/hogwarts-legacys-performance-deck-dive/)
- **[claimed, 2026-08-21] Shader pre-caching:**
  - It pre-compiles shaders to prevent stutters; "Open-world and massive games like 'Elden Ring' seem to benefit the most."
  - Costs are downloads and storage.
  - With it off, the Deck still compiles shaders locally.
  - No measurements.
  - Source: [BGR](https://www.bgr.com/2237494/should-you-enable-pre-caching-steam-deck/)
- **[claimed, 2026-07-24] TDP guidance:** "12-15W for demanding modern titles at 40-60fps," with a step-down method (lower TDP 1 W at a time until frame time turns uneven, then go back one step). No measurements. Source: [Evetech](https://evezone.evetech.co.za/build-lab/steam-deck-tdp-tuning-sensible-watts-per-game)

### Inferences
- **[inference] Resolution and upscaling are the biggest universal knob.**
  - In GPU-bound scenes, cost scales roughly with pixel count, so 800p → 600p (about 0.56× pixels) can approach 1.5× fps in GPU-bound scenes.
  - The cost is FSR1/NIS softness; HUD text is upscaled too.
  - A game-provided temporal upscaler (FSR2/3/TSR/XeSS) at the same internal resolution usually looks better, so prefer the in-game upscaler when it exists (menu-reachable, Tier S) and fall back to gamescope otherwise.
- **[inference] Frame cap and refresh pairing for the 45 fps target:**
  - On OLED (45–90 Hz), 45 fps at 90 Hz or 45 Hz gives even pacing.
  - On LCD (40–60 Hz), use 45 Hz.
  - Panel ranges are from prior knowledge, not re-verified.
  - The cap itself adds no fps but cuts power, heat and frame-time variance. It is fully compositor-side.
- **[inference] Env-var options.** `DXVK_CONFIG`, `VKD3D_CONFIG` (append-only), and RADV/Mesa env options (e.g. anisotropy or LOD overrides) live inside Proton's own translation layer, which anti-cheat already tolerates. They are not "injection" in the DLL-swap sense.
  - Risk: some anti-cheat runtimes may flag unusual environments. There is no evidence either way.
  - Gains are typically small; they are quality or compatibility knobs, not big fps levers.
- **[inference] Proton version.** This needs per-game knowledge. For anti-cheat games, the Proton build must include the EAC/BattlEye runtime support Valve ships. Switching to a community build such as GE can break anti-cheat, so restrict it to non-AC games.

### Gaps
- No 2025–2026 measured Deck data found for TDP-vs-fps curves, Proton-version deltas, refresh pairing or shader-cache stutter reduction (search budget exhausted).
- No measurements of how `RADV_FORCE_VRS` compares with gamescope downscaling at equal fps.

---

## Summary tables

### Table A: engine families

| Engine family | Settings location / format | Writable? | Cvar-level control? | Est. share of demanding games | Anti-cheat notes |
|---|---|---|---|---|---|
| Unreal Engine 4/5 | `pfx/.../AppData/Local/<Project>/Saved/Config/Windows/` (UE4: `WindowsNoEditor`): `GameUserSettings.ini` (sg.*, resolution) + `Engine.ini`. Plain ini. Some titles use Documents/My Games. | Yes, plain text. Some games ignore or overwrite it or keep settings in saves. | Yes: Engine.ini `[SystemSettings]` outranks menu and sg.*; loses to code/console; cheat cvars restricted in shipping. sg.* levels redefined per project. | 26–28% of all Steam releases, 31% of 2024 units (VGI, claimed). About 40–55% of demanding 2023–26 titles (inference). | Marvel Rivals detects config mods ("Unauthorized modification…", Jul 2026). ARC Raiders FOV/visibility edits flagged by players. Ultra+ packs need UE4SS and EAC off: not usable. Online games: menu-reachable GameUserSettings values only, no Engine.ini cvars. |
| Unity | Registry `HKCU\Software\<Company>\<Product>` (Wine `pfx/user.reg`), keys hash-suffixed `_h…`; many games also use custom files in LocalLow. | Yes (unencrypted per Unity docs), but key names and meanings are per game. | No general cvar layer. Universal command-line flags: `-screen-width/-height`, `-screen-fullscreen`, `-force-vulkan/-force-d3d11`. | About 50% of all releases but a small share of demanding ones (26% of units). | Low risk for resolution and command-line flags; the rest is per title. |
| RE Engine (Capcom) | `config.ini` in the **install folder**, plain key=value (MH Wilds). | Yes. Users set it read-only. Steam verify can revert it. | Partial: exposes non-menu keys (thread counts, priorities). | Small: a few titles a year (inference). | Install-folder file, so higher tamper-scan risk (inference). Online titles: menu values only. |
| Frostbite (EA) | `Documents/<Game>/settings/<store>/PROFSAVE_profile`, plain `GstRender.*`; optional `user.cfg` (console commands) in the install folder. | Yes. | Yes, via `user.cfg` console commands. | Small (BF6, Dragon Age) (inference). | BF6 uses Javelin kernel anti-cheat. EA rules are silent on configs. Avoid `user.cfg` in online; PROFSAVE menu-equivalent values only. |
| Swarm (Saber, Space Marine 2) | Encrypted settings file (user report). | No (claimed). | No. | 1–2 titles. | EAC. Engine-agnostic levers only. |
| Stingray-derived (Helldivers 2) | `AppData/Roaming/Arrowhead/Helldivers2/user_settings.config`, plain `key = value`. | Yes. | No (settings keys only). | 1 title. | GameGuard. No config-ban reports found. Menu values only. |
| Creation 2, id Tech/Motor, Decima, Snowdrop, Anvil, Source 2 | **Unverified this session.** Prior knowledge: mostly plain ini/cfg under Documents or Saved Games (id Tech uses cvar-style text). | Likely yes (unverified). | id Tech and Creation likely cvar/ini-level (unverified). | Each a few % (inference). | Per title. Ubisoft and Valve online titles need menu-only values. |

### Table B: universal levers

| Universal lever | Needs per-game knowledge? | Anti-cheat safe? | Expected gain | Image cost |
|---|---|---|---|---|
| gamescope internal resolution + FSR1/NIS upscale (`-w/-h`, `-F`, Steam scaling filter) | No; the game must render at the nested resolution, true for most. | Yes: compositor-side, never touches the game (inference). | Largest universal fps lever when GPU-bound; about pixel-proportional (inference, unmeasured here). | Medium–high: spatial-upscale softness, HUD upscaled. Prefer the in-game temporal upscaler when available. |
| Frame cap + refresh pairing (45 fps at 45/90 Hz) | No. | Yes (compositor and Steam). | No fps gain. Even pacing, lower power and heat, headroom for quality (inference). | None (slight latency). |
| TDP / GPU clock / governor / scheduler via steamos-manager | No for safe defaults; the per-game optimum needs measurement. | Yes: system-level, outside the game. | Battery and thermals; small fps change at a fixed cap. No measured 2025–26 Deck data found. | None. |
| Driver dynamic VRS (`RADV_FORCE_VRS_CONFIG_FILE`) | No. | Probably: driver env var, no injection (inference; testing-only per prior research). | See prior research. | Text and detail degradation (prior research). |
| `DXVK_CONFIG` / `VKD3D_CONFIG` (append) / RADV env options | No, but per graphics API (D3D9–11 vs 12). | Probably: part of the Proton stack anti-cheat already tolerates (inference; no evidence either way). | Small; mostly quality or compatibility knobs. | None to small (e.g. forced anisotropy improves the image). |
| Proton version choice | Yes (compatibility per game). | Mixed: anti-cheat games need Valve Proton with EAC/BattlEye runtime support; community builds can break anti-cheat (inference). | Unmeasured here; mostly compatibility, occasionally performance. | None. |
| zram / swap / swappiness (CryoUtilities-style) | No. | Yes. | Measured about zero: "within margin of error"; ZRAM "worse to identical" (Hogwarts Legacy, 2023). | None. |
| Shader pre-caching (Fossilize, Steam setting) | No. | Yes. | Less stutter, especially open-world (claimed); no average-fps gain. No measurements. | None (storage and download cost). |

*Nothing in this report needs saving to user memory. It is project research output; if wanted, it can be saved as a Deck Forge project doc (e.g. `claude/deckforge-universal-optimizer-feasibility.md`).*
