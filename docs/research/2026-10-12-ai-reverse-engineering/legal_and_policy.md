# Legal and policy constraints on reverse engineering and modifying commercial PC games (DeckForge), as of October 12, 2026

This is not legal advice. Labels used below: **[Law]** is statute, regulation or court holding. **[Contract]** is EULA or ToS text. **[Report]** is press or community reporting. **[Inference]** is my own reasoning.

Research-wide caveats:
- Some primary pages could not be fetched: the SCJN press release, Justia for MDY, the 2027 petitions index page, and the Space Marine 2 store page, which is age-gated.
- The Mexican statute texts come from the mley.mx mirror. That site says its verification is not confirmed, so check the text against the DOF or diputados.gob.mx.

## 1. US law

### Takeaway
There are two separate legal tracks, and the difference between them is the key point.
- **Copyright.** Disassembling your own copy to understand how it works can be fair use (Sega, Connectix). Distributing code or assets derived from the game is classic infringement.
- **DMCA §1201 (anti-circumvention).** Bypassing DRM, anti-tamper or anti-cheat is a separate violation. Fair use is not a defense to it, the interoperability exemption is narrow, and no triennial exemption covers personal performance modding.

Monster Hunter Wilds is still sold with Denuvo, so "AI-decompile and rebuild" for that game almost certainly runs into §1201.

### Cited Findings

**Fair use for reverse engineering**
- [Law] *Sega v. Accolade*, 977 F.2d 1510 (9th Cir., Oct 20, 1992; amended Jan 6, 1993). The court held that disassembly is "a fair use of the copyrighted work, as a matter of law" when it is "the only way to gain access to the ideas and functional elements" and "there is a legitimate reason for seeking such access." Limits:
  - The ruling "does not ... insulate Accolade from a claim of copyright infringement with respect to its finished products."
  - The court called the question "fairly debatable."
  - It held that §117 did not protect the conduct.
  — [OpenJurist](https://openjurist.org/977/f2d/1510/sega-enterprises-ltd-v-accolade-inc)
- [Law] *Sony v. Connectix*, 203 F.3d 596 (9th Cir., Feb 10, 2000).
  - Intermediate copying of the PlayStation BIOS during reverse engineering was fair use.
  - The emulator was "modestly transformative" because it created a new platform.
  - Key fact: "Sony does not claim that the Virtual Game Station itself contains object code that infringes."
  — [OpenJurist](https://openjurist.org/203/f3d/596/sony-computer-entertainment-inc-v-connectix-corporation)

**Contracts can waive reverse-engineering rights**
- [Law] *Davidson & Associates v. Jung* (Blizzard v. bnetd), 422 F.3d 630 (8th Cir., Sept 1, 2005).
  - EULA and ToU bans on reverse engineering are enforceable and not preempted. Citing *Bowers v. Baystate*, the court said "private parties are free to contractually forego the limited ability to reverse engineer."
  - The §1201(f) interoperability exemption failed for two reasons: the circumvention "constitutes infringement," and the purpose was not solely interoperability, because the emulator also bypassed CD-key checks.
  — [OpenJurist](https://openjurist.org/422/f3d/630/davidson-associates-v-jung)

**Breach of ToS vs. copyright, and anti-cheat as a protection measure**
- [Law] *MDY v. Blizzard*, 629 F.3d 928 (9th Cir., Dec 14, 2010).
  - Breaching a license term is copyright infringement only if the term has a nexus to the copyright owner's exclusive rights. Using a bot against the ToS was not infringement.
  - MDY was still liable for DMCA trafficking for circumventing the Warden anti-cheat, as to WoW's "dynamic non-literal elements."
  - The court rejected *Chamberlain*'s requirement that circumvention be linked to infringement.
  - The district court, following *Vernor*, held that purchasers are licensees, not owners, so §117 did not protect them.
  — [Wikipedia summary (secondary)](https://en.wikipedia.org/wiki/MDY_Industries,_LLC_v._Blizzard_Entertainment,_Inc.)

**The anti-circumvention statute, 17 U.S.C. §1201**
- [Law] Text of §1201 — [Cornell LII](https://www.law.cornell.edu/uscode/text/17/1201):
  - §1201(a)(1)(A): "No person shall circumvent a technological measure that effectively controls access to a work."
  - §1201(a)(2) bans trafficking in circumvention technology. §1201(b)(1) covers tools "primarily designed or produced for the purpose of circumventing" copy controls.
  - §1201(a)(3)(B): a measure "effectively controls access" if it "requires the application of information, or a process or a treatment."
  - §1201(c)(1) preserves fair use only as a defense "to copyright infringement," not to circumvention.
  - §1201(f) (reverse engineering for interoperability):
    - (f)(1) allows a person who has lawfully obtained the right to use a program to circumvent "for the sole purpose of identifying and analyzing those elements of the program that are necessary to achieve" interoperability of an independently created program.
    - (f)(3) allows sharing the results only to enable interoperability, and only without infringing.
    - (f)(4) defines interoperability as "the ability of computer programs to exchange information."

**Triennial exemptions (current rule from the 2024 cycle, 89 FR 85446, Oct 28, 2024)**
- [Law] 37 CFR 201.40 — [eCFR](https://www.ecfr.gov/current/title-37/chapter-II/subchapter-A/part-201/section-201.40):
  - (b)(19)(i) covers games only where the rights holder "has ceased to provide access to an external computer server." Within that:
    - (A) allows individuals to circumvent "to restore access to the game for personal, local gameplay."
    - (B) allows preservation by libraries, archives and museums.
  - (b)(19)(ii) covers preservation of games that are no longer commercially available.
  - (b)(18) covers good-faith security research on a lawfully acquired device. Under (b)(18)(iii), it is not a defense under other laws such as the CFAA.
  - (b)(15) covers repair. For consoles, repair is limited to the optical drive.
  - There is **no general exemption for personal modification of software**.
- [Report] On Oct 25, 2024 the Copyright Office refused a new exemption that would have let libraries give researchers remote access to preserved games. ESA said it "would never support remote game access for research purposes." — [Video Game History Foundation](https://gamehistory.org/dmca-2024-statement/)

**2027 cycle (formally the "tenth triennial")**
- [Law/Process] Timeline — [Copyright Office NewsNet 1088](https://copyright.gov/newsnet/2026/1088.html); [1201/2027 page](https://www.copyright.gov/1201/2027/index.html):
  - Notice of inquiry published June 9, 2026.
  - New and renewal petitions were due Aug 24, 2026.
  - Comments on renewal petitions were due Sept 28, 2026.
  - Renewed exemptions would run October 2027 to October 2030.
  - Docket COLC-2026-0100.
- [Report] Renewal petitions titled "Abandoned Video Games" were filed by Dan Elkins and Ken Austin — [petition PDF (Elkins)](https://www.copyright.gov/1201/2027/petitions/renewal/Renewal-Pet-Abandoned-Video-Games-Dan-Elkins.pdf); [petition PDF (Austin)](https://www.copyright.gov/1201/2027/petitions/renewal/Renewal-Pet-Abandoned-Video-Games-Ken-Austin.pdf). I did not open them. I found no new petition for personal game modding or performance modding.

**Notable cases**
- [Report] **re3/reVC**, *Take-Two v. Papenhoff*, N.D. Cal. 3:21-cv-06831 — [TorrentFreak, Apr 2023](https://torrentfreak.com/take-two-dismisses-claims-against-lead-defendants-in-gta-mods-lawsuit-230405/):
  - GitHub DMCA takedown, then counter-notices, then a lawsuit in Sept 2021 alleging "willful and malicious" infringement and misrepresentation in the counter-notices.
  - Settlement in principle on Feb 6, 2023. Stipulated dismissal with prejudice of the four named defendants on Apr 3, 2023. Doe defendants were dismissed without prejudice.
- [Report] The re3 defense pleaded fair use, interoperability and bug-fixing. Users needed their own copy because the projects did not include the data files — [GamingOnLinux, Nov 2021](https://www.gamingonlinux.com/2021/11/gta-modders-behind-re3-and-revc-fire-back-in-court).
- [Report] **Super Mario 64 PC port** (May 2020). Nintendo's representatives targeted hosts of the *compiled* port, calling it "an unauthorized derivative work based on Nintendo's copyrighted work" — [VGC](https://www.videogameschronicle.com/news/nintendo-takes-action-against-mario-64-pc-port/).
- [Report] **Ocarina of Time PC port** (Ship of Harkinian, Mar 2022). It requires a user-supplied ROM, extracts assets locally, and ships no Nintendo assets. No Nintendo action was reported at the time — [VGC](https://www.videogameschronicle.com/news/zelda-ocarina-of-time-pc-port/).
- [Report] **Yuzu** (Mar 2024). Nintendo sued Tropic Haze under the DMCA anti-circumvention and trafficking provisions, describing Yuzu as "software primarily designed to circumvent technological measures." The case settled within about a week:
  - $2.4M payment.
  - Permanent injunction on distributing Yuzu or similar software.
  - Deletion of the keys and surrender of the domain.
  — [Engadget](https://www.engadget.com/makers-of-switch-emulator-yuzu-quickly-settle-with-nintendo-for-24-million-203204698.html)
- [Report] **Bungie v. AimJunkies/Phoenix Digital** — arbitration award (Feb 2023), $4,396,222 total — [TorrentFreak](https://torrentfreak.com/bungie-wins-4-3-million-award-against-cheat-seller-in-arbitration-230220/):
  - DMCA circumvention: $255,000, for 102 violations at $2,500 each.
  - DMCA trafficking: $3,402,500.
  - Breach of contract was also found.
  - The arbitrator relied on testimony that a developer "connected reverse engineering tools to the Destiny 2 process" and tried to "circumvent the protections Bungie had in place."
- [Report] Separately, a W.D. Wash. jury on May 24, 2024 found AimJunkies liable for copyright infringement and awarded $63,210. The §1201 claims had gone to arbitration under the license agreement — [MBHB](https://www.mbhb.com/intelligence/snippets/destiny-developer-obtains-first-of-its-kind-jury-verdict-against-hackers/).

### Inferences
- **Denuvo and Capcom's anti-tamper are very likely "technological measures."** The MH Wilds store page lists Denuvo with a "5 different PC within a day machine activation limit," which is an access control that "requires the application of information." Stripping, decrypting or bypassing that layer to get clean code to decompile is very likely circumvention under §1201(a)(1)(A).
- **Fair use does not cure circumvention.** In the 9th Circuit (MDY), §1201 liability does not depend on infringement.
- **§1201(f) is a poor fit.** It requires the *sole purpose* of interoperability with an *independently created* program. "Rebuild the game optimized for Deck" is not that, and Davidson v. Jung read the exemption narrowly.
- **Untested gray zone.** Analyzing code after the game has decrypted itself in memory, or hooking at runtime without disabling the protection, has no clear US precedent. It is not clearly safe.
- **Distribution drives the risk.** Every US enforcement action found involved distribution: re3, the SM64 port, Yuzu, AimJunkies. Private study of one's own copy has no reported enforcement, but absence of enforcement is not legality.
- **Publisher behavior varies.** re3 and Ship of Harkinian are both decompilation-based and both required the user's own game data. One was sued and one was left alone. Decompilation-derived code is a publisher-dependent risk, not a doctrinally safe harbor.
- **Jurisdiction.** US law reaches acts done in the US and distribution through US platforms such as GitHub, which is where re3's DMCA notice landed. Living in CDMX does not remove US exposure if the work is hosted or distributed in the US or performed while in the US.

### Gaps
- I did not fetch the text of §1203 (civil remedies, statutory $200–$2,500 per act) or §1204 (criminal, "willfully and for commercial advantage"). The $2,500-per-act figure above comes from the Bungie award, not the statute text. Verify.
- I did not fetch *Micro Star v. FormGen* (9th Cir. 1998; user-made levels as derivative works) or *Lewis Galoob v. Nintendo* (9th Cir. 1992; Game Genie not a derivative work). These are the leading cases on mods and patches as derivative works.
- I did not read the 2027 "Abandoned Video Games" petitions, and the full list of new petitions was not reachable.
- I found no case squarely deciding whether decompiling a Denuvo-protected binary for personal study violates §1201.
- Nintendo actions against decomp or recomp ports in 2024–2026 were not comprehensively surveyed.

## 2. Mexico law

### Takeaway
Mexico is in some ways stricter than the US for this project.
- The 2020 T-MEC reform made decompilation, reverse engineering and disassembly an exclusive right of the software owner.
- It added a ban on circumventing technological protection measures, with a narrow interoperability exception.
- Circumventing protection is criminal when done knowingly and for profit: 6 months to 6 years in prison.
- The Supreme Court upheld the regime in May 2024.
- I found no enforcement against modders.

### Cited Findings
- [Law] **LFDA Art. 106** gives the software rights holder the right to authorize or prohibit:
  - (I) reproduction;
  - (II) translation, adaptation and modification;
  - (III) distribution;
  - (IV) "decompilation, reverse engineering and disassembly" ("revertir la ingeniería de un programa");
  - (V) public communication.
  Fractions III and IV were reformed, and V was added, by the DOF of July 1, 2020 — [mley.mx LFDA 106](https://mley.mx/LFDA/articulo/106/).
- [Law] **LFDA Art. 114 Bis** (added July 1, 2020) defines a technological protection measure as "cualquier tecnología, dispositivo o componente" that protects rights or controls access. Rights holders can sue civilly under Arts. 213 and 216 Bis, independently of criminal or administrative action — [mley.mx 114 Bis](https://mley.mx/LFDA/articulo/114-bis/).
- [Law] **LFDA Art. 114 Ter** is an exception for works whose protection term has expired, so it is not relevant here — [mley.mx 114 Ter](https://mley.mx/LFDA/articulo/114-ter/).
- [Law] **LFDA Art. 114 Quáter** lists circumvention that is *not* a violation — [mley.mx 114 Quáter](https://mley.mx/LFDA/articulo/114-qu%C3%A1ter/):
  - (I) good-faith, non-infringing reverse engineering of a lawfully obtained program, limited to elements not previously available, "con el único propósito de lograr la interoperabilidad de un programa de computación creado independientemente con otros programas" (with the sole purpose of making an independently created program interoperate with others);
  - security testing authorized by the system owner;
  - encryption research;
  - library acquisition decisions;
  - privacy, law enforcement and accessibility;
  - other case-by-case exceptions that INDAUTOR grants on request with evidence.
- [Law] **LFDA Art. 232 Bis** fines anyone who produces, distributes, imports, sells or offers devices, products or systems promoted, mainly used, or designed to circumvent an effective protection measure: 1,000 to 20,000 times the daily UMA. The text shown does not require a profit motive — [mley.mx 232 Bis](https://mley.mx/LFDA/articulo/232-bis/index.html.md).
- [Law] **Código Penal Federal Art. 427 Bis.** Knowingly ("a sabiendas") and "con fines de lucro" circumventing an effective protection measure carries "prisión de seis meses a seis años" and 500 to 1,000 días multa. Added by the DOF of July 1, 2020 — [mley.mx CPF 427 Bis](https://mley.mx/CPF/articulo/427-bis/index.html.md).
- [Law] **CPF Art. 427 Ter.** Manufacturing, importing, distributing or commercializing circumvention devices "con fines de lucro" carries the same penalty — [mley.mx CPF 427 Ter](https://mley.mx/CPF/articulo/427-ter/index.html.md).
- [Law] **LFDA Art. 216 Bis.** Civil damages "en ningún caso será inferior al cuarenta por ciento del precio de venta al público" (never less than 40% of the retail price) of the original product — [mley.mx 216 Bis](https://mley.mx/LFDA/articulo/216-bis/).
- [Report] **Supreme Court ruling.** On May 30, 2024, the SCJN (acciones de inconstitucionalidad 217/2020 and 249/2020, brought by CNDH and Senate members) upheld:
  - notice-and-takedown, by a 6–5 vote;
  - the LFDA and CPF provisions that criminalize circumvention.
  Artículo 19 criticized that circumvention is criminalized "aún en los casos en lo que dicha elusión sea necesaria" (even where circumvention is necessary) to exercise rights — [Zeta Tijuana](https://zetatijuana.com/2024/05/scjn-valida-censura-digital-y-criminaliza-elusion-de-candados-digitales-acusa-articulo-19/). The official SCJN press release was not fetchable: [SCJN comunicado 7854](https://www.internet2.scjn.gob.mx/red2/comunicados/noticia.asp?id=7854).
- [Report] **IMPI-backed explainer** (2020, Grupo de Trabajo Antipiratería):
  - Circumvention is sanctionable, but infringement is not automatic. It must be established in an IMPI administrative procedure, and the decision can be challenged.
  - Exceptions include interoperability, and "uso legítimo" may be recognized through IMPI resolutions.
  — [gob.mx PDF](https://www.gob.mx/cms/uploads/attachment/file/598313/Lo_ba_sico_sobre_las_medidas_tecnolo_gicas_de_proteccio_n_y_el_aviso_y_retirada.pdf)
- [Report] **Enforcement focus.** A 2019 article (pre-reform) had industry pushing enforcement against sellers of unlicensed games and pirate-disc labs. No actions against modders were named — [DPL News](https://dplnews.com/frena-pirateria-avance-del-sector-videojuegos/).

### Inferences
- **Decompiling is reserved by statute.** Under Art. 106(IV), decompiling a game is a right reserved to the rights holder. Mexico has no US-style open-ended fair use. The only explicit carve-out found is the TPM-context interoperability exception in 114 Quáter(I). Personal study by decompilation is therefore technically outside the statute, though enforcement against a private individual is very unlikely.
- **The criminal line is profit.** CPF 427 Bis and Ter require "fines de lucro." Purely personal, non-commercial circumvention is probably not criminal, but it may still bring civil or administrative exposure.
- **Monetizing changes the picture.** Monetizing distribution (Patreon, donations tied to downloads, paid builds) could arguably meet "fines de lucro" and move a circumvention tool or patch into criminal territory.
- **Device rules may reach tools.** Art. 232 Bis targets devices and systems designed to circumvent. A distributed DRM-stripping patcher or loader would likely qualify, whether or not it is monetized.

### Gaps
- I did not verify LFDA Art. 148 (general limitations), Art. 105 (backup copy) or Art. 107 (software rights).
- I did not confirm whether the act of circumvention itself, as opposed to devices, is an administrative infraction under a separate article (232 Ter or similar).
- I did not get the official SCJN text or engrose.
- I found no Mexican enforcement case against modders or game reverse engineers. I searched in Spanish.
- Japanese law, which governs Capcom's EULA (Unfair Competition Prevention Act; Japan has prosecuted save-editing sellers), was not researched.

## 3. Contracts: Steam, Capcom, Saber/Focus

### Takeaway
Every relevant contract prohibits reverse engineering and modification on paper.
- **Steam** reserves applicable-law rights.
- **Capcom's EULA** for MH Wilds bans "modifying" and "reverse engineering," limits the license to private gameplay, and is governed by Japanese law.
- **MH Wilds still ships with Denuvo** as of Oct 12, 2026, plus a Capcom in-house anti-tamper layer.
- **Saber** actively supports mods for Space Marine 2 through Integration Studio, but bars modded players from public sessions.

In practice, bans have followed DLC unlocking, cheating and multiplayer disruption, not solo cosmetic or performance mods.

### Cited Findings

**Steam Subscriber Agreement** (last updated Sept 10, 2026) — [SSA](https://store.steampowered.com/subscriber_agreement/)
- [Contract] §2.A: "The Content and Services are licensed, not sold."
- [Contract] §2.G: "Except as otherwise permitted under this Agreement (including any Subscription Terms or Rules of Use), or under applicable law notwithstanding these restrictions, you may not ... reverse engineer, derive source code from, modify, disassemble, decompile, create derivative works based on" the Content without Valve's written consent.
- [Contract] §4.B:
  - "You agree that you will not tamper with the execution of Steam or Content and Services unless otherwise authorized by Valve."
  - The user agrees not to "disable, circumvent, or otherwise interfere with" software designed to prevent or report Cheats.
  - "You may not use Cheats, mods, hacks, or any other unauthorized third-party software" in connection with marketplace, account-creation and Steam processes.
  - The definition of Cheats is tied to "unfair competitive advantage when playing multiplayer versions ... or modifications."
- [Contract] Valve may restrict or terminate accounts or Subscriptions (§§4.D, 9.C).
- [Contract] Governing law (§10): Washington law, with exclusive venue in King County courts for users outside the EU and UK. There is no arbitration clause.

**Monster Hunter Wilds**
- [Contract] Steam store page, fetched Oct 12, 2026: "Incorporates 3rd-party DRM: Denuvo Anti-tamper." It also lists a "5 different PC within a day machine activation limit," a required third-party EULA, and a base price of $39.99. No anti-cheat is listed — [Steam store](https://store.steampowered.com/app/2246340/Monster_Hunter_Wilds/).
- [Contract] MH Wilds EULA (effective Jan 26, 2024) — [Steam EULA 2246340](https://store.steampowered.com/eula/2246340_eula_0):
  - §1.1: license "only for the purpose of private gameplay."
  - §8.1(i) prohibits "modifying, altering, translating" and "reverse engineering, or extracting the code."
  - §8.1(ii) prohibits "analyzing communication protocols or any other data used in the Program."
  - §8.1(vii) prohibits BOT and cheat tools. §8.1(viii) prohibits "cracking."
  - §8.2 lets Capcom stop or limit use. §10.2 lets Capcom rescind the agreement.
  - §14.1–14.2: Japanese law, with Tokyo District Court as the court of first instance.
  - §14.4 preserves user rights under local law.
- [Report] **Capcom anti-tamper in Wilds.** In March 2025, modder praydog said Wilds' stutters come from its anti-tamper. The writer guessed it was Capcom's own layer rather than Denuvo, which is unconfirmed. A REFramework update (installed as dinput8.dll) fixed the stutters — [DSOGaming, Mar 5, 2025](https://www.dsogaming.com/mods/monster-hunter-wilds-mod-fixes-stutters-caused-by-the-anti-tamper-tech/).
- [Report] **Capcom's 2023 R&D talk** — [Game World Observer, Nov 1, 2023](https://gameworldobserver.com/2023/11/01/capcom-mods-cheats-in-house-anti-piracy-tool-silver-bullet):
  - "Mods that are not officially supported by the game are impossible to distinguish from cheat tools, implementation-wise."
  - Capcom planned an in-house RE Engine "Security Module" layered with Denuvo, not replacing it.
- [Report] **Capcom's Wilds warning** (after Title Update 1): "We have confirmed the unauthorized modification of game data," and "Modified data can ... render the game unplayable." This concerned hacked multiplayer quests — [PCGamesN](https://www.pcgamesn.com/monster-hunter-wilds/mods-warning).
- [Report] **Reported Wilds bans** (Mar 24, 2025). Players were reportedly permanently banned for a mod that unlocked paid DLC. This is unconfirmed, and Capcom did not answer the outlet. Mods were otherwise tolerated, with more than 700 on Nexus — [MeinMMO](https://mein-mmo.de/monster-hunter-wilds-mods-permanenter-account-bann/).
- [Report] **Capcom's Enigma anti-tamper** made modding harder. Capcom rolled it back from Resident Evil Revelations after backlash, citing an "issue observed" — [SI Videogames](https://videogames.si.com/news/capcom-enigma-protection-resident-evil-revelations-anti-mod).
- [Report, titles only, not opened] Capcom removed Denuvo from Monster Hunter World and Monster Hunter Stories — [OC3D](https://overclock3d.net/news/software/denuvo-has-been-removed-from-monster-hunter-world/); [DSOGaming](https://www.dsogaming.com/news/capcom-has-removed-denuvo-from-monster-hunter-stories/).

**Space Marine 2**
- [Report] Saber statement of Nov 21, 2024 — [GamingBolt](https://gamingbolt.com/warhammer-40000-space-marine-2-will-prohibit-mods-from-public-sessions-with-next-update):
  - Game files were left unencrypted so players could mod.
  - Modded players are barred from public sessions because mods hurt server stability and saves.
  - Private lobbies stay allowed, and Saber will "continue to provide all necessary server infrastructure" for modded play with friends.
- [Report] Saber released the official Integration Studio around May 2025. It is "the exact same editor we use internally," covering AI trees, UI/HUD and scenarios — [Nexus Mods news, May 15, 2025](https://www.nexusmods.com/rust/news/15273).
- [Report] SM2 runs Easy Anti-Cheat. A back-end change in Sept 2026 made it crash with EAC on Proton Experimental, affecting the Steam Deck. Users reported that Proton 9 or 11 work — [GamingOnLinux, Sept 1, 2026](https://gamingonlinux.com/2026/09/warhammer-40-000-space-marine-2-update-is-causing-issues-for-steamos-linux-players).

### Inferences
- **The Steam carve-out matters in the US.** "Under applicable law notwithstanding these restrictions" probably preserves whatever fair-use or §1201(f) room exists. But Davidson v. Jung shows US courts enforce anti-reverse-engineering contract terms, and the Capcom EULA has its own ban.
- **Contract breach is mainly a ban and termination risk.** Under MDY (9th Cir.), breaking ToS covenants is mainly a contract issue, not copyright. The bigger consequence is account or license termination, which can be done without notice under SSA §4.D.
- **"Rebuild and repackage" conflicts with the Capcom license.** §1.1 "private gameplay" combined with §8.1(i) means distributing rebuilt Wilds binaries is plainly outside the license.
- **Saber's posture is the most permissive found.** Official tools, unencrypted files, and modded private lobbies make SM2's single-player and private modding contractually low-risk. EAC and public matchmaking are the hard line.

### Gaps
- I did not retrieve the Space Marine 2 EULA or any Integration Studio license terms. The store page was age-gated.
- I did not confirm whether Capcom's in-house anti-tamper is still active in the current Wilds build, or whether Capcom has announced Denuvo removal plans for Wilds.
- I found no official Capcom mod policy page for Wilds. The statements found are press-reported.

## 4. Anti-cheat (Easy Anti-Cheat, BattlEye)

### Takeaway
- Anti-cheat vendors ban for cheats. Game developers set the policy.
- Proxy-DLL mods (dxgi.dll, d3d9.dll, dinput8.dll), the way REFramework and OptiScaler install, are exactly what anti-cheat blocks or flags.
- Bypassing anti-cheat is a §1201 issue (Bungie arbitration, MDY) and an SSA §4.B breach.
- The documented low-risk pattern is mods only with anti-cheat off and offline, or through the developer's own sanctioned channel.

### Cited Findings
- [Report] **BattlEye FAQ** — [BattlEye FAQ](https://www.battleye.com/support/faq/):
  - Bans are "for the use of actual cheats/hacks."
  - "non-cheat overlays and visual enhancement tools like Reshade or SweetFX are generally supported," but they are blocked in PUBG and Fortnite.
  - Players are told to "Ensure that there is no d3d9.dll, dxgi.dll or dsound.dll file in your game directory" and not to use tweaked system files.
  - Macro tools may lead to a kick rather than a ban.
- [Report] **EAC FAQ as published by Saber** (written for Insurgency: Sandstorm):
  - EAC can flag "untrusted and/or unknown system files."
  - "EAC has a zero-tolerance policy against cheating."
  - There is an appeal form.
  — [Saber support](https://support.saber.games/hc/en-us/articles/22303848570001-Easy-Anti-Cheat-FAQ)
- [Report] The EAC support site offers ban appeals and sends players to "the relevant game's support channel" — [easy.ac](https://easy.ac/support/articles).
- [Report] **Elden Ring (EAC).** Players disable EAC to run mods such as the DLSS mod and to play offline. Going back online with modded saves "could lead to your account being temporarily banned from online play." Updated June 21, 2024 — [Windows Central](https://windowscentral.com/how-disable-anti-cheat-elden-ring).
- [Contract] SSA §4.B forbids disabling, circumventing or interfering with anti-cheat — [SSA](https://store.steampowered.com/subscriber_agreement/).
- [Law/Report] Circumventing anti-cheat protections was the basis of the DMCA §1201(a)(1), (a)(2) and (b) awards in Bungie v. AimJunkies — [MBHB](https://www.mbhb.com/intelligence/snippets/destiny-developer-obtains-first-of-its-kind-jury-verdict-against-hackers/). The trafficking liability over the Warden anti-cheat in MDY v. Blizzard rests on the same theory — [Wikipedia](https://en.wikipedia.org/wiki/MDY_Industries,_LLC_v._Blizzard_Entertainment,_Inc.).

### Inferences
- **DeckForge's existing tier rule matches the evidence.** Tier S only for games with kernel or online anti-cheat (Helldivers 2/GameGuard, SM2/EAC) is consistent with what I found. Injection (Tier I) into an EAC game while EAC is active risks bans. Disabling EAC to inject risks §1201 and SSA claims.
- **Ban precedents for pure performance mods are sparse.** Documented bans cluster around cheats, DLC unlocks, and modded data reaching online play. Performance mods mostly cause kicks, blocked DLLs, or temporary online restrictions.

### Gaps
- I did not reach an official Epic or EAC developer policy page stating that bans are per game and set by the developer. The answer text on easy.ac did not load.
- I did not find a documented permanent ban for a pure performance or upscaler mod in an EAC or BattlEye title. The GTA Online BattlEye false-positive reports surfaced in search but were not verified.

## 5. AI provider policies (Anthropic)

### Takeaway
- Anthropic's Usage Policy never mentions reverse engineering, DRM, anti-cheat or piracy by name.
- Three clauses cover the risky parts: IP infringement, circumventing other platforms' terms, and bypassing security controls without authorization.
- Modding your own copy, interoperability analysis and writing original mod code are not prohibited.
- Circumventing DRM or anti-cheat, and distributing copyrighted code, map onto prohibited categories.
- A new AUP version takes effect Nov 12, 2026.

### Cited Findings
- [Policy] **Current version, effective Sept 15, 2025** (archived, superseded Nov 12, 2026) — [Anthropic AUP archive](https://www.anthropic.com/legal/archive/22742366-2ef0-4c7a-a833-6523f10d3944):
  - "Infringe, misappropriate, or violate the intellectual property rights of a third party."
  - "Engage in actions or behaviors that circumvent the guardrails or terms of other platforms or services."
  - "Bypass security controls such as authentication systems, endpoint protection, or monitoring tools."
  - "Discover or exploit vulnerabilities in systems, networks, or applications without authorization of the system owner."
  - "Create or distribute malware, ransomware, or other types of malicious code."
  - There is no security-research carve-out.
- [Policy] **New version, effective Nov 12, 2026** — [Anthropic AUP](https://www.anthropic.com/legal/aup):
  - The section heading becomes "Do Not Compromise Computer or Network Systems Without Authorization."
  - It keeps the IP clause and the "circumvent the guardrails or terms of other platforms or services" clause.
  - "Bypass security controls such as authentication systems, endpoint protection, or monitoring tools without authorization."
  - It adds: "This section does not prohibit security research, testing, or tool development conducted on systems you own or operate" (also covering authorized bug bounties).
  - It mentions a Cyber Verification Program for adjusted access.
  - There is no mention of "anti-cheat," "piracy," "DRM," or "reverse engineering."

### Inferences
- **Likely fine:**
  - studying a game you own;
  - writing original config tools, launch-option tuning, and original runtime hooks or mods;
  - interoperability analysis such as file formats and settings files.
  None of these infringe, circumvent another platform's terms, or bypass security controls.
- **Likely prohibited:**
  - Stripping Denuvo or Capcom anti-tamper, or bypassing EAC. These are "security controls" or "monitoring tools," violate the SSA and EULA ("terms of other platforms"), and likely violate §1201 and LFDA (the "applicable laws" clause).
  - Generating or distributing decompiled game code or ripped assets (IP clause).
- **The new carve-out is narrow.** "Systems you own or operate" probably covers your own PC and Deck, but not the publisher's licensed software or online services. It is a security-research exemption, not a modding or DRM exemption.
- **Practical effect.** Expect Claude to help with Tier S and Tier I work and to decline DRM or anti-cheat removal and redistribution of game code.

### Gaps
- I did not research OpenAI, Google or other providers' policies.
- I did not review Anthropic's Consumer or Commercial Terms, or model-level cyber safeguards, beyond the AUP mention.

## 6. The practical safe zone in the modding community

### Takeaway
What survives:
- original code that loads at runtime or patches in place on the user's own legally obtained install;
- no bundled game assets or binaries;
- no DRM or anti-cheat bypass;
- no online or multiplayer impact;
- or the publisher's official tools.

What gets taken down: compiled ports or binaries containing derived code or assets (SM64 port), redistributed decompiled engines (re3, even though it required the user's own data), circumvention tools (Yuzu), and cheats (AimJunkies).

### Cited Findings
- [Policy] **Nexus Mods File Submission Guidelines** (updated Sept 29, 2026) — [Nexus Mods](https://help.nexusmods.com/article/28-file-submission-guidelines):
  - "User submissions which include copyrighted content, be it game files or images, are prohibited" without the owner's permission.
  - Content that "enables or promotes illegal activity, including ... software piracy" may be moderated.
  - "Files that may be disruptive to any persistent multiplayer environment are prohibited."
  - Internet-connecting executables are restricted.
  - Copyright holders use a report function or the DMCA Claims Form.
- [Report] **Required own copy, no assets, left up:** Ship of Harkinian (OoT) — [VGC](https://www.videogameschronicle.com/news/zelda-ocarina-of-time-pc-port/).
- [Report] **Required own data files, still sued and settled:** re3/reVC — [GamingOnLinux](https://www.gamingonlinux.com/2021/11/gta-modders-behind-re3-and-revc-fire-back-in-court); [TorrentFreak](https://torrentfreak.com/take-two-dismisses-claims-against-lead-defendants-in-gta-mods-lawsuit-230405/).
- [Report] **Compiled port binary, taken down as a derivative work:** SM64 PC port — [VGC](https://www.videogameschronicle.com/news/nintendo-takes-action-against-mario-64-pc-port/).
- [Report] **Runtime hooking tolerated in practice:** REFramework installs as dinput8.dll and even fixed Wilds' anti-tamper stutter with no reported Capcom action — [DSOGaming](https://www.dsogaming.com/mods/monster-hunter-wilds-mod-fixes-stutters-caused-by-the-anti-tamper-tech/). Capcom's countermeasure has been technical (Enigma), not legal — [SI](https://videogames.si.com/news/capcom-enigma-protection-resident-evil-revelations-anti-mod).
- [Report] **Publisher-sanctioned modding:** Saber's Integration Studio and private modded lobbies — [Nexus Mods](https://www.nexusmods.com/rust/news/15273); [GamingBolt](https://gamingbolt.com/warhammer-40000-space-marine-2-will-prohibit-mods-from-public-sessions-with-next-update).

### Inferences
- **The highest-risk version of the idea.** The project as framed (AI-decompile Wilds or SM2 and "rebuild" or "repackage" for the Deck) sits in the zone that gets taken down. For Wilds it also requires defeating Denuvo and Capcom anti-tamper, which brings §1201, LFDA 114 Bis and CPF 427 Bis exposure.
- **The defensible version.** DeckForge's current Tier S and Tier I scheme fits the community safe zone:
  - settings files, launch options, TDP and refresh-rate tuning;
  - original runtime hooks or OptiScaler-style injection on non-anti-cheat games;
  - distributed as original code or config that operates on the user's own install, with no game bytes and no DRM touch.
- **Using AI for analysis only.** AI-assisted reverse engineering used to *understand* engine settings, config formats and render paths, without distributing derived code or bypassing protection, is the lower-risk use of the idea.
- **SM2 should go through official tools.** For Space Marine 2, Saber's official tooling is the legitimate route for deep changes. EAC rules out Tier I on public play.

### Gaps
- I found no takedown data on performance-only patch distributions such as DLSS/FSR injectors on Nexus.
- I did not check Nexus's handling of Capcom requests specifically.

## Risk table

Ratings are relative and qualitative, combining legal exposure on paper with observed enforcement likelihood. Each is my inference from the findings above.

| Activity | US risk | Mexico risk | Contract / ban risk | AI-provider policy (Anthropic AUP) | Notes |
|---|---|---|---|---|---|
| Decompile own copy for study | **Low** if the code is unprotected (Sega/Connectix fair use for intermediate copying). **Medium** for MH Wilds, because getting usable code likely means circumventing Denuvo or Capcom anti-tamper (§1201, where fair use is no defense). | **Medium on paper, low in practice.** LFDA 106(IV) reserves decompilation to the rights holder. 114 Quáter(I) only covers interoperability. No profit means no CPF 427 Bis. No enforcement found. | Breaches SSA §2.G (unless "applicable law" permits) and Wilds EULA §8.1(i)–(ii). Ban risk is low if it stays offline and private. | Generally permitted (own copy, no distribution). Not permitted if it requires bypassing anti-tamper ("bypass security controls"). | SM2's files were deliberately left unencrypted by Saber, which makes it lower risk than Wilds. |
| Circumvent DRM or anti-tamper (Denuvo, Capcom anti-tamper) | **High.** §1201(a)(1)(A). No triennial exemption fits; (b)(19) only covers discontinued servers. §1201(f) is narrow (Davidson). Statutory damages; the Bungie arbitrator awarded $2,500 per act. | **High.** LFDA 114 Bis plus civil damages (216 Bis, at least 40% of retail). Criminal if knowingly and for profit: CPF 427 Bis, 6 months to 6 years. SCJN upheld this in May 2024. | Wilds EULA §8.1(viii) "cracking." SSA §4.B tampering. Possible license or account termination. | Likely prohibited: "bypass security controls," "circumvent ... terms of other platforms," and the applicable-law clause. | Wilds still lists Denuvo as of Oct 12, 2026. This is the line DeckForge should not cross. |
| Runtime mod for personal use (REFramework or OptiScaler style, no DRM touch, offline or solo) | **Low.** Contract issue under MDY rather than copyright. No circumvention if the protection is not disabled; this is an untested gray area. | **Low.** Technically within the modification right (106 II), but private and non-commercial. No enforcement found. | Wilds EULA bans "modifying" on paper. In practice Capcom tolerates solo mods; the reported bans were for DLC unlocks and hacked quests. SM2 allows mods in private lobbies only. | Permitted (original code on your own system). | Proxy-DLL loading (dxgi or dinput8) is what anti-cheat flags, so keep this to non-anti-cheat games (DeckForge Tier I). |
| Distribute a patch that requires the user's own copy | **Low to Medium.** Low if it contains only original code or config. Medium to high if it contains decompiled or reimplemented game code (re3 was sued and settled) or circumvents protection (§1201(a)(2) trafficking). | **Medium.** Adaptation and distribution rights (106 II–III). If the patch circumvents protection: LFDA 232 Bis fines (1,000–20,000 UMA) and CPF 427 Ter if for profit. | DMCA takedowns on GitHub or Nexus; cease-and-desist letters. Nexus bars copyrighted game files and anything that enables piracy. | Permitted if the code is original and nothing is circumvented. Not if it ships decompiled code (IP clause). | Requiring the user's own copy is necessary but not sufficient: re3 required the user's data and still drew a lawsuit; Ship of Harkinian did not. |
| Distribute a modified exe or game assets ("repackaged" game) | **High.** Direct reproduction and distribution infringement (the SM64 port was taken down as an "unauthorized derivative work"). Plus §1201 trafficking if DRM is stripped (Yuzu: $2.4M settlement). | **High.** 106(I)/(III) infringement, civil damages of at least 40% of retail, and criminal exposure if for profit. | Account bans, takedowns, likely legal threats. Outside Wilds EULA §1.1 "private gameplay." | Prohibited (IP infringement clause). | This is the riskiest form of the proposal, and the publisher's identity matters little here. |
| Modify an anti-cheat game (SM2/EAC, Helldivers 2/GameGuard) | **Low** through official tools in private modded play (Saber Integration Studio). **High** if anti-cheat is bypassed or disabled for online play (§1201 per Bungie and MDY). | **Low** through official tools. **High** if anti-cheat is circumvented (LFDA 114 Bis; criminal if for profit). | **High** for injection while anti-cheat is active: SSA §4.B, EAC "zero-tolerance," Elden Ring-style online bans. SM2 bars modded players from public sessions. | Bypassing anti-cheat is likely prohibited ("circumvent ... terms of other platforms," "bypass ... monitoring tools"). Official-tool modding is permitted. | Matches DeckForge's Tier S-only rule for anti-cheat games. EAC on Proton is fragile (SM2 crash, Sept 2026). |

Points for the user's memory or lawyer brief:
- MH Wilds still uses Denuvo as of Oct 12, 2026.
- The Anthropic AUP update is effective Nov 12, 2026.
- The 2027 DMCA §1201 cycle is underway (petitions closed Aug 24, 2026; exemptions start Oct 2027).
- Mexico's criminal circumvention offense requires a profit motive (CPF 427 Bis/Ter).
- The Capcom EULA is governed by Japanese law (Tokyo court).
- The Steam SSA is governed by Washington law (King County).
