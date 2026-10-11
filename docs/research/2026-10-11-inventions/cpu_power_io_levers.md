# CPU, power-sharing and storage levers for Monster Hunter Wilds and Space Marine 2 on Steam Deck OLED (research notes, current to 11 Oct 2026)

Scope note: I ran about 50 searches and fetches. Every claim below has a source link, and anything I could not source is under Gaps. "Measured" means a source published numbers. "Claimed" means a source asserted an effect without numbers. Dates are given so older findings stand out.

Bottom line for the report writer (my inference, explained in the last section): both games are far below the native 45 fps target on the Deck. Wilds runs at about 20–30 fps on lowest settings (Jan 2026), and Space Marine 2 at about 14–24 fps (2024 review). Every code-only lever found here is measured or claimed at single-digit to low-teens percent, and mostly helps 1% lows and stutter rather than average fps. None of them, alone or combined, plausibly closes a 50–100% gap. They are best framed as stability and stutter levers.

---

## 1. Monster Hunter Wilds: CPU-bound or GPU-bound, on low-end hardware and on the Deck?

### Takeaway
On the Deck, Wilds in open field areas is reported as mainly GPU-limited. Settlements and camps with many NPCs are strongly CPU-heavy on desktop. Capcom's 2026 patches targeted CPU hotspots: monster and endemic-life spawn processing, duplicate effect generation, and a hub DLC-check bug. No published source separates CPU-limited from GPU-limited frame time on the Deck itself.

### Cited Findings
- **Launch-era Deck result (Feb 2025).** The benchmark tool on Deck at lowest settings with no upscaling ran "below 30 FPS, often around 20, with dips to 10 FPS or lower". It was still below 30 with FSR Ultra Performance, and it caused a Deck LCD to reboot. Verdict: "pretty much unplayable". — [GamingOnLinux, 6 Feb 2025](https://gamingonlinux.com/2025/02/monster-hunter-wilds-looks-unplayable-on-steam-deck-but-good-on-desktop-linux)
- **No handheld was playable (Feb 2025).** No gaming handheld ran the game at playable performance "even at 1280x800 with upscaling on low settings". "CPU scaling is extremely strong and you're going to want the newest platform possible." — [HotHardware, 27 Feb 2025](https://hothardware.com/news/monster-hunter-wilds-benchmark-tested)
- **The camp is the CPU-heavy scene (Feb 2025).** PCGH used the first-area camp as its CPU benchmark scene because its many NPCs and interactions "clearly strain the processor". Testing was at 720p with CapFrameX, checked for GPU limits. Ray tracing adds CPU management overhead and can worsen the CPU limit in settlements. Only the 7800X3D and 9800X3D exceeded 100 fps. An i5-12400F was judged enough for 60 fps. No 4-core or Zen 2 parts were tested. — [PCGH CPU benchmarks](https://www.pcgameshardware.de/Monster-Hunter-Wilds-Spiel-74697/Specials/Release-PC-Preload-Review-Benchmark-1466495/3/)
- **Deck after the latest patch (28 Jan 2026), lowest settings:**
  - quieter or interior areas: "a fairly stable 30 FPS"
  - large open areas: "high teens or low 20s"
  - Windward Plains: "below 20 FPS near the watering hole"
  - Scarlet Forest: mid-20s
  - Oilwell Basin: at or just above 30

  SDHQ says the Deck's problem "is more related to the GPU than the CPU". The patch was mostly CPU optimisation, and its new GPU options had "almost no effect". — [Steam Deck HQ, 28 Jan 2026](https://steamdeckhq.com/news/monster-hunter-wilds-1040-performance/)
- **After the Jan 2026 PC patch (no version given):** the Deck is "roughly playable at ~30 FPS" with FSR or XeSS upscaling and no frame generation. Per Daniel Owen, minimum fps rose 8% vs Title Update 4 and 20% vs TU3, with averages mostly similar. The patch lowered CPU load and VRAM demand through shader-compilation and texture-streaming changes. — [Notebookcheck, 30 Jan 2026](https://www.notebookcheck.net/Monster-Hunter-Wilds-fixes-DLC-bug-greatly-reduces-FPS-drops-and-runs-at-30-FPS-on-Steam-Deck.1215270.0.html)
- **DLC-check CPU hotspot (fixed 28 Jan 2026).** Around the Support Desk in Base Camp and the Grand Hub, with unclaimed content, "CPU load rises" because the game repeatedly checks claimed-content status. Capcom called it "an unintended bug". It was discovered by a Reddit user. — [VGC](https://www.videogameschronicle.com/news/monster-hunter-wilds-gets-a-pc-patch-which-capcom-says-will-fix-the-recently-reported-dlc-performance-bug)
- **Patch 1.041 (18 Feb 2026) notes:**
  - "Optimized monster and endemic life spawn-time processing to reduce CPU load"
  - "Added effect caching to decrease CPU load when generating duplicate effects"
  - "Optimized rendering processes to reduce CPU/GPU load"
  - added internal LODs to reduce GPU load

  — [Overclock3D](https://overclock3d.net/news/software/monster-hunter-wilds-latest-patch-packs-new-cpu-gpu-optimisations/)
- **Anti-tamper (Mar 2025).** A new REFramework build (Praydog, installed as dinput8.dll) is claimed to fix "stutters that are caused in the game by its anti-tamper tech" and some crashes. Evidence is a screenshot of "smooth frametimes" with no numbers. The DSOGaming author speculates the cause is not Denuvo. — [DSOGaming, 5 Mar 2025](https://www.dsogaming.com/mods/monster-hunter-wilds-mod-fixes-stutters-caused-by-the-anti-tamper-tech/)
- **Community Deck guide.** "The Little Engine that Shouldn't" mentions a ParallelBuildProcessorCount config setting that lowers CPU load. It says Capcom update 1.040.03.02 made the game work on Deck, so the guide is now "outdated". Compatibility was listed as of Nov 2025 for GE-Proton 10-25 and SteamOS 3.7. — [Nexus #183](https://www.nexusmods.com/monsterhunterwilds/mods/183)
- **The Deck's CPU is weak for this workload (2023 measurement).**
  - Van Gogh CPU: one CCX with 4 MB L3 (vs 16 MB on desktop Zen 2)
  - CPU-side memory bandwidth about 25 GB/s ("on the wrong planet"), while the GPU gets over 70 GB/s from the 88 GB/s LPDDR5
  - CPU clock ramp: 1.4 GHz to 1.7 GHz in 0.27 ms, with full boost only after nearly 1 s

  — [Chips and Cheese](https://chipsandcheese.com/p/van-gogh-amds-steam-deck-apu)

### Inferences
- Wilds on the Deck is probably GPU-bound in open fields, where SDHQ saw 20–30 fps and GPU options did nothing. It is probably CPU-bound or CPU-stuttery in camps and hubs (PCGH desktop CPU scene, DLC-check bug, NPC density). So the right power split changes with location. A static CPU cap that helps in the field could hurt in hubs.
- The 4 MB L3 and roughly 25 GB/s CPU bandwidth suggest NPC and monster simulation and the streaming and decompression threads are memory-bound on the Deck. Clock-only levers will have reduced effect on those paths.
- ParallelBuildProcessorCount is a Tier S config-file lever that may cut CPU contention on a 4C/8T part. It is untested on Deck with numbers.

### Gaps
- No source measures Wilds CPU vs GPU frame time on the Deck (for example MangoHud CPU/GPU frame-time split or GPU busy %).
- No source gives Wilds' thread count, a per-thread hotspot profile, or draw-call submission cost.
- REFramework's actual anti-tamper change, and its measured CPU or frame-time effect, are unpublished beyond Praydog's claim.
- No core-count or SMT scaling tests (4C/8T) were found.

---

## 2. Space Marine 2: same questions

### Takeaway
Space Marine 2's horde scenes are CPU-heavy even on a 7800X3D. On the Deck, a forced 640x400 resolution still could not hold 30 fps, which strongly suggests a resolution-independent (likely CPU) bottleneck. Easy Anti-Cheat limits DeckForge to Tier S system-level levers.

### Cited Findings
- **Desktop CPU limit (Sep 2024).** With a 7800X3D, high-end GPUs cap "at around 110 fps" at 1080p Ultra. 1080p with upscaling is "fairly heavily CPU-limited" from an RTX 3060 Ti up. Going from High to Medium gained only 5–10%. The benchmark is "particularly CPU heavy" because the Swarm Engine hordes "heavily utilize both the GPU and CPU". Only one CPU was tested, so there is no scaling data. — [TechSpot, 12 Sep 2024](https://www.techspot.com/review/2891-warhammer-space-marine-2-benchmark/)
- **Deck review (Sep 2024, updated 2026), score 2/5:**
  - lowest settings with FSR 2 Ultra Performance: about 24 fps, dropping to 19
  - forcing 640x400 "still couldn't hold 30 FPS"
  - open areas and large enemy groups: as low as 14 fps
  - interiors: higher
  - wattage 21–24 W, battery about 2.5 h
  - RAM crashes, where the CryoUtilities swap file "can prevent the crash"

  — [Steam Deck HQ](https://steamdeckhq.com/game-reviews/warhammer-40000-space-marine-2/)
- **Update 5.0 (Dec 2024)** added FSR3 and frame generation. The Deck is "a lot more playable" with Low, FSR Performance and FG, but no fps numbers were given. EAC works on Proton. Desktop Linux needed `SteamDeck=1 %command%`. — [GamingOnLinux, 10 Dec 2024](https://www.gamingonlinux.com/2024/12/space-marine-2-adds-dlss3-fsr3-and-frame-generation-more-playable-on-steam-deck-needs-launch-option-for-desktop-linux/page=1/)
- A community bug report describes a "significant CPU bottleneck and low 1% low fps" on a Ryzen 7 5700X with an RTX 4070 Ti Super. I saw only the title, not the numbers. — [Focus community tracker](https://community.focus-entmt.com/focus-entertainment/space-marine-2/bugs/bugs-redirect/10496-significant-cpu-bottleneck-and-low-1-low-fps-on-ryzen-7-5700x-with-rtx-4070-ti-super)

### Inferences
- The 640x400 result plus the 21–24 W draw suggest the Deck is CPU- or simulation-bound in hordes. Shifting watts toward the GPU would likely hurt there, and the right direction is CPU-favouring. That is the opposite of Wilds in the field.
- Because of EAC, the only non-settings levers are OS-level: TDP, CPU scheduler, SMT, cpufreq, swap, THP and Proton version. Injection, DLL swaps and REFramework-style hooks are out, consistent with DeckForge's tier rules.

### Gaps
- No 2025–2026 Deck fps measurements after later patches were found.
- No thread or core scaling data, and no CPU vs GPU frame-time split on the Deck.
- I did not verify which D3D version Space Marine 2 uses on PC (assumed D3D12, unverified).

---

## 3. Storage and decompression

### Takeaway
Wilds ships Microsoft DirectStorage DLLs. The game exposes both CPU and GPU texture decompression; the default path is unconfirmed. vkd3d-proton has supported DirectStorage GPU GDeflate since 2.10 (2023), and since 3.0 ships its own GLSL fallback shader. The "uncompressed textures" mods remove decompression at about 37 GB of extra disk, with only anecdotal stutter gains. On the Deck, storage type barely moves average fps but does affect lows during streaming.

### Cited Findings
- **DirectStorage DLLs.** Wilds ships `dstorage.dll` and `dstoragecore.dll`. A mod swaps them for DirectStorage 1.3.0 DLLs and claims I/O-stutter and fps improvement, without numbers (uploaded Apr 2025, updated Mar 2026). — [Nexus #2003](https://www.nexusmods.com/monsterhunterwilds/mods/2003)
- **DirectStorageOption mod (REFramework-based, updated Jan 2026).** It switches texture decompression between CPU and GPU: "Using 'GPU' mode will decrease CPU load at a price of GPU load increase". It also sets StagingBufferSize (32/64/128/256 MB, game default 64 MB, more VRAM). And it forces Windows file buffering with DisableBypassIO, recommended only for HDDs. It gives no measurements, and the page does not state the game's default mode. — [Nexus #1923](https://www.nexusmods.com/monsterhunterwilds/mods/1923)
- **Community claim (Mar 2025, unverified).** One user says textures stream "onto the CPU for decompression" and that "GPU optimized directstorage is no where to be found". Another reports going from about 30–40 fps with streaming stutter to "70+ stable" after updating the DirectStorage DLLs, on desktop. — [Steam discussion](https://steamcommunity.com/app/2246340/discussions/0/600772765301106662)
- **Texture Decompressor Tool (Mar 2025, updated Feb 2026).** It builds "a patch pak with uncompressed textures", needs REFramework for patch-pak loading, "may improve frame rate stability", and is "still being tested". The compression format is not named on the page. — [Nexus #951](https://www.nexusmods.com/monsterhunterwilds/mods/951)
- **Press coverage of the tool:** "significantly improving stuttering issues on a good number of system configurations", with no data. — [Wccftech, 16 Apr 2025](https://wccftech.com/monster-hunter-wilds-tool-improves-stuttering/amp/)
- **On the Deck:** uncompressed textures "does appear to reduce some of the stuttering" and "might contribute to getting another frame or two". It needs "37gb free space". Prebuilt removal packs "introduce graphical issues/missing textures". StagingBufferSize 32 "may well resolve" frame-gen crashes. — [Nexus #183](https://www.nexusmods.com/monsterhunterwilds/mods/183)
- **vkd3d-proton 2.10 (Sep 2023)** added "DirectStorage MetaCommands, which brings support for GPU accelerated GDeflate", shown working in Ratchet & Clank. No numbers. — [GamingOnLinux, 11 Sep 2023](https://www.gamingonlinux.com/2023/09/vkd3d-proton-v2-10-various-game-fixes-directstorage)
- **vkd3d-proton v3.0:** "We now ship our own fallback shader in GLSL instead of the more awkward HLSL shader that dstorage ships." — [vkd3d-proton releases](https://github.com/HansKristian-Work/vkd3d-proton/releases)
- **Deck storage test (CryoByte33, July 2023, SteamOS 3.4.8):**
  - Average fps was within margin of error across eMMC, internal NVMe, 1 TB NVMe and microSD (HZD, Cyberpunk, Returnal).
  - eMMC and microSD had worse lows "during major asset changes" in Returnal.
  - microSD HZD load took over 90 s.
  - eMMC to SSD gave more than 5x raw read speed and about 70% faster loads.
  - Swappiness 60 vs 1: Cyberpunk 0.1% lows about 10% worse; Returnal 0.1% and 1% lows 17% and 21% lower.

  — [Steam Deck HQ](https://steamdeckhq.com/news/can-steam-deck-drive-size-impact-performance/)

### Inferences
- On the Deck, GPU GDeflate is probably a net loss in Wilds' GPU-bound field areas, because it moves work onto the saturated 8 CU GPU. It might help in CPU-bound hubs. This is the same location-dependent tradeoff as the power split, and it is untested.
- Uncompressed textures trade CPU decompression for about 37 GB of disk and more I/O bandwidth. That is a much better trade on internal NVMe than on microSD, where the extra read volume could worsen streaming lows (from CryoByte33's finding that slow storage hurts lows during asset changes). This is unmeasured for Wilds.
- Under Wine there is no Windows BypassIO, and reads go through the Linux page cache anyway. So "ForceFileBuffering" is probably moot on Linux (unverified).
- Prefetching paks into page cache (readahead or posix_fadvise WILLNEED) is plausible for hot zones only. Wilds' install is tens of GB, the Deck has 16 GB shared RAM, and swap pressure measurably hurts lows. Plausible but untested, with real risk.
- REFramework-dependent options (patch paks, DirectStorageOption) are Tier I. They are allowed for Wilds only if Wilds is confirmed to have no online anti-cheat, and are impossible for Space Marine 2.

### Gaps
- Not confirmed: Wilds' default decompression path, its pak compression format, and its DirectStorage version as shipped.
- No measured CPU-time share for decompression or streaming in Wilds on any hardware.
- No source shows whether Wilds actually exercises GPU GDeflate through vkd3d-proton on RADV and the Deck, or its cost there.
- The internal "How does it work" values for the uncompressed mod were not found.

---

## 4. CPU/GPU power sharing on Van Gogh

### Takeaway
Van Gogh's SMU shares one package budget between CPU and GPU and biases toward the GPU: in GPU-bound loads the CPU is pushed below base clock at about 2–3 W. Userspace can set slow and fast PPT (hwmon power1_cap and power2_cap, or `steamosctl set-tdp-limit`), GPU performance level and manual clock, CPU governor, boost, and since SteamOS 3.8 the CPU scheduler. AMD SmartShift targets APU-plus-discrete-GPU systems, so no Deck equivalent was found. I found no published, measured Deck test showing that a CPU cap raises GPU clock or fps in a GPU-bound game.

### Cited Findings
- **Budget split (2023 measurement).** The APU "appears to be capped at 16 W", with budget "flexibly allocated between the CPU and GPU". GPU-bound: GPU "over 10 W", CPU "squished below base clock" at 2–3 W. Van Gogh "tries to maximize GPU performance" with "heavy sacrifices to the CPU side". — [Chips and Cheese](https://chipsandcheese.com/p/van-gogh-amds-steam-deck-apu)
- **Kernel interface (2021 commit).** hwmon `power1_cap` = slow PPT (thermally significant average, default about 5000 ms) and `power2_cap` = fast PPT (about 10 ms average). Values are written in microwatts (e.g. `echo 15000000`). — [kernel commit ae07970a06](https://upd.dev/kernel/linux/commit/ae07970a0621d6)
- **steamosctl commands.**
  - `get/set-tdp-limit`, with `get-tdp-limit-min/max`
  - `set-gpu-performance-level <auto|low|high|manual|profile_peak>`
  - `set-manual-gpu-clock <MHz>`
  - `set-cpu-scaling-governor`
  - `set-cpu-boost-state <enabled|disabled>`
  - `set-performance-profile`, `set-gpu-power-profile`

  steamos-manager runs a user daemon on the session bus and a root daemon on the system bus for privileged operations. No SMT command is listed. — [steamosctl man page](https://linuxcommandlibrary.com/man/steamosctl)
- **CPU scheduler command.** `steamosctl set-cpu-scheduler lavd` was added in SteamOS 3.8.0 Preview, along with kernel 6.16. — [GamingOnLinux, 20 Mar 2026](https://www.gamingonlinux.com/2026/03/steamos-3-8-0-preview-brings-initial-steam-machine-support-and-improvements-for-many-handhelds/page=1/)
- **SteamOS 3.8.10 stable** is out, per the headline. — [Phoronix](https://phoronix.com/news/SteamOS-3.8.10-Stable)
- **SimpleDeckyTDP README.** The Deck does not need ryzenadj for TDP. SteamOS 3.7.5 switched the scaling driver from `acpi-cpufreq` to `amd-pstate-epp`, which enables EPP and governor controls and CPU boost toggles. — [SimpleDeckyTDP](https://github.com/aarron-lee/SimpleDeckyTDP)
- **SMT (anecdotes, 2023).**
  - Valve treats needing SMT off as a bug. SteamOS 3.5 fixed an AMD kernel behaviour that dropped a core's cache when its SMT sibling slept. — [SDHQ, Feb 2023](https://steamdeckhq.com/news/steamos-3-5-will-have-smt-disabled-performance-improvements/)
  - User reports, all anecdotal and conflicting: Dolphin about 35 fps with SMT on vs 60 off; "an 8-thread TDP cap yields lower clocks than a 4-thread one"; locking the GPU above 1200 MHz let cores boost in Yuzu; `taskset -c 0,2,4,6` suggested as an alternative; later 3.5.x stable users saw no SMT benefit. — [ValveSoftware/SteamOS #864](https://github.com/ValveSoftware/SteamOS/issues/864)
- **AMD SmartShift.** It shifts budget between the APU and a discrete GPU, with "up to 14%" (AMD claim). Its Linux sysfs exposes a bias from -100 to 100. — [Phoronix, 1 Jun 2021](https://www.phoronix.com/news/AMD-SmartShift-Linux-Still-Come)
- **Undervolt and overclock (Apr 2023, BIOS-level, not code-only).** Smokeless UMAF SVI3 offsets cut GPU power by "1-2 watts" and added 16% battery at the same fps. With undervolt plus overclock at 23 W: Cyberpunk High 1% lows +16% and 0.1% lows +27%. Later BIOS (118+) removed overclocking and limited undervolt. — [SDHQ](https://steamdeckhq.com/news/undervolting-and-overclocking-push-your-steam-deck-beyond-its-limits/)

### Inferences
- Because the SMU already favours the GPU when the GPU is busy, the extra headroom from capping CPU clocks in a GPU-bound game is probably small: CPU is already at about 2–3 W, so a cap frees maybe 1–2 W. That could still matter where CPU spikes (streaming, simulation) steal fast-PPT headroom. Plausible, unmeasured.
- The cleanest code-only "SmartShift substitute" is a per-scene controller that sets CPU boost, governor or EPP, max frequency, and the GPU clock floor based on observed frame-time bottleneck. All of these are reachable through steamosctl or sysfs.
- If steamos-manager's root daemon accepts the user session's calls (as the Steam client does), DeckForge may not need its own root for TDP, GPU clock, governor or boost. SMT and `scaling_max_freq` probably need root or a polkit rule. Unverified.
- For Space Marine 2, the evidence points the other way: protect CPU clocks (boost on, avoid low GPU floors), because it is likely CPU-bound in hordes.

### Gaps
- No measured Deck A/B test was found: CPU capped (for example 2.0–2.4 GHz, or boost off) vs uncapped in a GPU-bound game, with GPU clock, fps and per-rail watts. This is the key missing experiment.
- The OLED-specific power limit (15 W vs about 16 W) and SMU arbitration policy are not documented publicly.
- Whether steamosctl calls work unprivileged from a third-party process was not confirmed.

---

## 5. Frame-aware DVFS, performance hints and LAVD

### Takeaway
Academic and Android frame-aware DVFS work shows about 3–23% energy-per-frame savings at about 0–2% fps loss, and in one vendor case study up to 28–50% fps gains, with power up or down depending on preset. LAVD is the Linux analogue. It is now selectable on SteamOS 3.8, but I found no published Deck fps or power numbers. Its author lists known gaps: Unreal Engine games, futex-only lock awareness, and no NTSync awareness.

### Cited Findings
- **Co-Cap (ACM SAC 2016, older).** Cooperative CPU/GPU frequency capping across more than 70 mobile games on ODROID-XU3. Energy per frame fell 10.0–10.6% on average, and 19.1–23.1% for CPU-dominant games. Fps loss was 0.5–1.7%. — [CPS-VO abstract](https://archive.cps-vo.org/biblio/view/39094)
- **V-SYNC-aware GPU DVFS governor on Pixel 8 Pro (ISQED 2025).** Up to 3% lower energy per frame, and 37% less fps variation. — [ISQED](https://www.isqed.org/English/Archives/2025/Technical_Sessions/109.html)
- **ADPF case study (UNISOC, LineageW).** Fps rose 11.5% (Low), up to 28.1% (Medium) and 50.1% (High). Power changed +9.9%, -3.7% and +3.1% respectively. No temperature or stability numbers. — [Android Developers](https://developer.android.com/stories/games/unisoc-adpf)
- **LAVD on a Snapdragon dev board (Dec 2025 slides, unnamed game).** EEVDF about 50 fps vs LAVD about 57 fps with lower energy in one run; equal fps with lower energy in another. No Steam Deck numbers. — [Igalia slides](https://www.igalia.com/downloads/slides/ChangwooMin-TheCurrentStatusAndFutureDirectionOfTheLAVDScheduler.pdf)
- **LAVD early results (Apr 2024).** "better or similar performance to EEVDF" in average fps and 1% lows. No figures in the text. — [Phoronix](https://www.phoronix.com/news/LAVD-Scheduler-Linux-Gaming)
- **LAVD design and limits (LWN, 7 Jan 2026, on the LPC 2025 talk):**
  - prioritises tasks with high waker or wakee frequency
  - tracks futexes to extend lock-holder slices
  - "some users have complained that LAVD does not work well with the games using the Unreal engine"
  - proxy execution doesn't cover user-space futexes
  - no per-game profiles

  — [LWN](https://lwn.net/Articles/1051430/)
- **NTSync awareness.** The LPC 2025 slides list NTsync semantics as needed for lock-holder-preemption handling (future work). — [LPC 2025 slides](https://lpc.events/event/19/contributions/2150/attachments/1951/4162/Steps_Towards_a_Gaming_Optimized_Schedule-lpc2025.pdf)
- **Energy-aware CPU selection (Nov 2025).** Igalia: LAVD "measures and predicts the computing power needed in real time" and picks the CPUs that meet demand with least energy, framed around the Steam Frame. — [Igalia](https://igalia.com/2025/11/helpingvalve.html)
- **scx_lavd README.** "Mainly targets single CCX / single-socket systems", with a default balanced or "autopilot" mode. — [scx_lavd README](https://raw.githubusercontent.com/sched-ext/scx/main/scheds/rust/scx_lavd/README.md)

### Inferences
- The Deck is a single-CCX, 4C/8T part, the case LAVD was built for. Wilds (RE Engine) and Space Marine 2 (Swarm) are not Unreal, so the main reported failure mode may not apply. LAVD is the most "proven-adjacent" code-only CPU lever, but it is unmeasured for these two games. It is a cheap A/B for the bench runner: `steamosctl set-cpu-scheduler lavd`.
- A frame-aware CPU/GPU controller in userspace is plausible on the Deck: read frame time from gamescope or MangoHud, then adjust the levers in section 4. The literature suggests about 10% energy-per-frame savings. On a fixed TDP, that saving could become a few percent more GPU clock in GPU-bound scenes. Unmeasured on any x86 APU I found.

### Gaps
- No published Steam Deck LAVD vs EEVDF fps, 1% low or power data. Benchmarks were promised in an Apr 2026 SNU seminar, but none were found published.
- No AMD or Intel publication with measured iGPU-internal CPU/GPU power-sharing gains was found.
- How LAVD interacts with amd-pstate-epp frequency selection on the Deck is undocumented in what I found.

---

## 6. Linux memory and scheduling knobs (THP, affinity, background threads, vm, split_lock, CryoUtilities)

### Takeaway
Evidence is thin and mostly anecdotal. One informal THP=always test showed +8% fps. Swappiness is the one memory knob with measured Deck numbers (lows), and the swap file prevents Space Marine 2 RAM crashes. CryoUtilities exposes swap, THP, compaction, defrag, page-lock-unfairness and shmem knobs, but published no numbers in text. `split_lock_mitigate` is an x86 penalty knob, probably irrelevant on Zen 2.

### Cited Findings
- **THP (Feb 2023, informal).** `always` on a Ryzen 1600 and GTX 970: Borderlands 3 went from 92 to just over 99 fps (about +8%). TF2 and Dying Light gains were from memory only. The author notes "not using a ton of science". khugepaged hit 100% of a core due to another process. — [Pat's blog](https://blog.patshead.com/2023/02/enabling-transparent-hugepages-can-provide-huge-gaming-performance-improvements.html)
- **Phoronix THP test (6 Jan 2026).** madvise vs always on Linux 6.18, using an EPYC 9655P server, not a gaming setup. I could not retrieve the numbers. — [Phoronix](https://www.phoronix.com/review/thp-madvise-always)
- **CryoUtilities features.** Swap resizer, swappiness, HugePages toggle, HugePage defrag, shmem toggle, compaction proactiveness, page lock unfairness, UMA frame-buffer info. No quantitative claims in the README, and OLED testing is "pending". — [CryoUtilities README](https://cdn.jsdelivr.net/gh/cryobyte33/steam-deck-utilities@main/README.md)
- **CryoUtilities 2 coverage (Feb 2023).** No numbers in the article, only a video. The tweaks may stop some games' hard crashes. Commenters debate whether hugepages help at all. — [GamingOnLinux](https://gamingonlinux.com/2023/02/cryoutilities-2-boosts-steam-deck-performance)
- **Swappiness, measured.** Swappiness 60 vs 1 cost 10–21% on 0.1% and 1% lows in Cyberpunk and Returnal; HZD was within margin. — [SDHQ, Jul 2023](https://steamdeckhq.com/news/can-steam-deck-drive-size-impact-performance/)
- **Space Marine 2 crashes.** The CryoUtilities swap file "can prevent the crash"; the 4 GB UMA plus CryoUtilities "did not help much" for performance. — [SDHQ SM2 review](https://steamdeckhq.com/game-reviews/warhammer-40000-space-marine-2/)
- **split_lock_mitigate (x86).** Default 1, which "penalizes the split lockers with intentional performance degradation". 0 just warns. — [kernel sysctl docs](https://docs.kernel.org/admin-guide/sysctl/kernel.html)
- **Affinity (anecdote).** `taskset -c 0,2,4,6` was suggested as better than disabling SMT for emulators. — [SteamOS #864](https://github.com/ValveSoftware/SteamOS/issues/864)

### Inferences
- Split-lock detection is, to my knowledge, an Intel-introduced feature, so `split_lock_mitigate` is likely a dead end on Zen 2 Van Gogh. This is unverified and needs `/proc/cpuinfo` flags (`split_lock_detect`) on a real Deck.
- THP: one informal +8% desktop data point and no Deck data. Plausible for large-heap games like Wilds under Wine, but the khugepaged and compaction CPU cost on a 4-core part could offset gains. Needs a bench A/B.
- Pinning render threads or deprioritising shader-compile and background threads under Wine requires identifying Wine thread names. There is no published Deck evidence. LAVD's latency-criticality heuristic is the automated version of this idea.

### Gaps
- No exact CryoUtilities recommended values; the docs/tweak-explanation.md fetch failed.
- Whether Valve adopted any CryoUtilities defaults in SteamOS is not established.
- Current SteamOS 3.8 defaults for THP, swappiness and compaction are not established.
- No measured THP results on the Deck for any game.
- No measured core-pinning or nice/ionice results for Proton games on the Deck.

---

## 7. Wine/Proton/vkd3d-proton CPU overhead for D3D12

### Takeaway
The headline NTSync gains (up to several times faster) were measured against plain wineserver sync. Valve says fsync, which SteamOS already uses, is "as fast or faster". SteamOS added the ntsync driver in Jan 2026 (3.7.20 Beta), and Proton 11 stable (7 Jul 2026) supports NTSync. vkd3d-proton's most Deck-relevant CPU fix is the v2.14 queue-submission rewrite. Expect little NTSync gain on the Deck vs fsync.

### Cited Findings
- **Original NTSync numbers (Jan 2024).** RE2 went from 26 to 77 fps and Dirt 3 from 110.6 to 860.7. The baseline was "upstream", that is wineserver without fsync or esync; hardware was not noted. — [GamingOnLinux, 24 Jan 2024](https://gamingonlinux.com/2024/01/proposed-windows-nt-sync-driver-brings-big-wine-proton-performance-improvements)
- **Valve's position (Jul 2025).** Pierre-Loup Griffais: "We already include fsync, which should be as fast or faster as ntsync"; "no urgency in including it in the Deck / SteamOS kernel". GE-Proton 10-9 NTSync was opt-in via `PROTON_USE_NTSYNC=1`. — [GamingOnLinux, 14 Jul 2025](https://www.gamingonlinux.com/2025/07/ge-proton-10-9-released-with-ntsync-and-fsr4-upgrade-support)
- **SteamOS ntsync driver.** SteamOS 3.7.20 Beta "Added ntsync driver" (Jan 2026). No numbers; Proton 11 "might" use it by default. — [GamingOnLinux, 9 Jan 2026](https://gamingonlinux.com/2026/01/steamos-3-7-20-adds-the-ntsync-driver-to-help-improve-some-game-performance)
- **Proton 11 stable (7 Jul 2026)** includes NTSync support, vkd3d-proton proton-20260410 and DXVK 2.7.1-467. Default-on status is not stated. — [comss.ru](https://www.comss.ru/page.php?id=21187)
- **NTSync gains vs fsync.** Gains against esync or fsync are smaller, and GPU-bound games may see little difference. — [lilting.ch, May 2026](https://lilting.ch/en/articles/linux-gaming-ntsync-kernel-windows-api)
- **vkd3d-proton releases:**
  - v2.14 rewrote queue submission, which "works around pathological CPU overhead in amdgpu taking 20ms+ to submit work in some cases"
  - v2.14: 2 frames of latency caused GPU starvation "especially on Deck"
  - v3.0.1: ExecuteIndirect batching; descriptor-heap support is "likely the last release before `VK_EXT_descriptor_heap` lands"

  — [vkd3d-proton releases](https://github.com/HansKristian-Work/vkd3d-proton/releases)
- **DXVK 3.0 (Jun 2026)** offloads shader compilation fully to workers and uses descriptor heaps by default. It is D3D8–11 only, so it is not relevant to D3D12 Wilds except via shared Proton. — [GamingOnLinux](https://gamingonlinux.com/2026/06/dxvk-3-0-brings-lots-of-improvements-for-windows-games-on-linux-steamos)

### Inferences
- Choosing the Proton version (Proton 11 vs 10 vs Experimental) is a legitimate Tier S lever. Gains for Wilds would come from vkd3d-proton submission and ExecuteIndirect changes rather than NTSync. Bench A/B is required; there are no game-specific numbers.

### Gaps
- No Deck measurements of NTSync vs fsync.
- No measured vkd3d-proton CPU overhead for Wilds or Space Marine 2.
- Whether Proton 11 enables NTSync by default on SteamOS 3.8 is unconfirmed.

---

## 8. Lever scorecard: proven, plausible, dead end (synthesis)

### Takeaway
No lever is "proven" for these two games on the Deck with numbers. "Proven elsewhere, untested here" is the best available category. The highest-value, lowest-risk experiments for the bench runner are:
- the LAVD vs EEVDF A/B
- swappiness and swap
- a CPU boost/EPP/max-frequency vs GPU clock floor sweep, per scene type (field vs hub/horde)
- Proton version
- for Wilds only, opt-in Tier I: uncompressed textures on NVMe and the DirectStorage CPU/GPU decompression toggle

### Cited Findings
- **Proven on the Deck, generic games:**
  - low swappiness improves lows by 10–21% — [SDHQ](https://steamdeckhq.com/news/can-steam-deck-drive-size-impact-performance/)
  - a swap file prevents Space Marine 2 RAM crashes — [SDHQ](https://steamdeckhq.com/game-reviews/warhammer-40000-space-marine-2/)
  - storage type affects lows but not averages — [SDHQ](https://steamdeckhq.com/news/can-steam-deck-drive-size-impact-performance/)
- **Proven elsewhere, untested on these games or the Deck:**
  - frame-aware CPU/GPU capping: about 10% energy per frame — [Co-Cap](https://archive.cps-vo.org/biblio/view/39094)
  - LAVD "better or similar" to EEVDF — [Phoronix](https://www.phoronix.com/news/LAVD-Scheduler-Linux-Gaming)
  - THP about +8% in one desktop game — [Pat's blog](https://blog.patshead.com/2023/02/enabling-transparent-hugepages-can-provide-huge-gaming-performance-improvements.html)
- **Claimed only (no numbers):**
  - REFramework anti-tamper stutter fix — [DSOGaming](https://www.dsogaming.com/mods/monster-hunter-wilds-mod-fixes-stutters-caused-by-the-anti-tamper-tech/)
  - uncompressed textures ("a frame or two" on the Deck) — [Nexus #183](https://www.nexusmods.com/monsterhunterwilds/mods/183)
  - DirectStorage DLL swap — [Nexus #2003](https://www.nexusmods.com/monsterhunterwilds/mods/2003)
- **Likely dead ends on the Deck:**
  - SmartShift (dGPU-only design) — [Phoronix](https://www.phoronix.com/news/AMD-SmartShift-Linux-Still-Come)
  - expecting big NTSync gains over fsync — [GamingOnLinux](https://www.gamingonlinux.com/2025/07/ge-proton-10-9-released-with-ntsync-and-fsr4-upgrade-support)
  - split_lock_mitigate on AMD (inference, see section 6)
  - code-only CPU/GPU overclock or undervolt, which needs BIOS tools and was restricted in later BIOS — [SDHQ](https://steamdeckhq.com/news/undervolting-and-overclocking-push-your-steam-deck-beyond-its-limits/)

### Inferences
- **The target gap.** Wilds measures about 20–30 fps on Deck lowest settings and Space Marine 2 about 14–24 fps. A native 45 fps lock needs about +50–125%. The levers above are single-digit to low-teens percent and mostly improve lows. DeckForge should present them as "steadier 30" and stutter-reduction levers, and report 45 fps native as BLOCKED by hardware for both titles unless new evidence appears. This is my inference from the cited numbers.
- **The best power split depends on the scene.** Wilds field areas lean GPU-bound (favour GPU). Wilds hubs and Space Marine 2 hordes lean CPU-bound (favour CPU). A static per-game profile will be wrong part of the time. That argues for a frame-time-driven controller over fixed caps.
- **Space Marine 2 is limited to Tier S levers** (scheduler, TDP, boost/EPP, swap, Proton version) because of EAC.

### Gaps
- The single most decision-relevant missing measurement: a Deck A/B of CPU caps (boost off, or capped max frequency) against GPU clock and fps in Wilds field vs hub, and Space Marine 2 horde vs interior, logged with per-rail power. No public source has done it; it needs DeckForge's own bench runner.

---

## Notes for memory (for the main session)
- Wilds ships DirectStorage DLLs. A REFramework mod exposes CPU/GPU decompression and staging-buffer options.
- SteamOS 3.8 exposes `steamosctl set-cpu-scheduler lavd`, and steamosctl has TDP, GPU clock, governor and boost commands.
- SteamOS 3.7.5 moved to `amd-pstate-epp`, and SteamOS 3.7.20 added the ntsync driver.
- No published Deck LAVD numbers and no Deck CPU-cap-vs-GPU A/B data exist. Both are candidate DeckForge bench experiments.
