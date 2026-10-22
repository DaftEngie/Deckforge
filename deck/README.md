# Steam Deck setup and first baseline (week 1)

Everything here is reversible and changes nothing outside `~/deckforge` on the Deck,
except Steam launch options you set by hand (delete the text to undo).

## Before you start (once the Deck is charged)
- Plug the Deck in. Benchmarks always run plugged in.
- Close all games.

## Step 1 — Desktop Mode and a terminal (5 min)
1. Hold the power button → **Switch to Desktop**.
2. Open the app menu → System → **Konsole**.
3. If you have never set a password, type `passwd` and choose one. (You'll need it for SSH.)

## Step 2 — Get DeckForge onto the Deck (2 min)
In Konsole:
```
cd ~
git clone https://github.com/DaftEngie/deckforge.git deckforge-repo
```
(The repo is public, so no GitHub sign-in is needed on the Deck.)

## Step 3 — Run the setup script (1 min)
```
bash ~/deckforge-repo/deck/setup_deck.sh
```
Read the output. Lines marked `[todo]` need you; everything else is done.
Send Claude the whole output (a phone photo is fine).

## Step 4 — Turn on SSH (1 min, if the script said it's off)
```
sudo systemctl enable --now sshd
```
This lets your Mac send benchmark jobs later. Undo anytime with
`sudo systemctl disable --now sshd`.

## Step 5 — Log your normal play (Game Mode only)
**Always play and measure in Game Mode.** In Desktop Mode, heavy games such as
Monster Hunter Wilds can freeze on a black screen and rewrite their own settings for the
desktop screen. This happened on 2026-10-21.

1. Re-run `bash ~/deckforge-repo/deck/setup_deck.sh`. It writes
   `~/deckforge/mangohud-session.conf` and prints the launch option to use.
2. In Game Mode, go to the game → ⚙ → Properties → **Launch Options** and paste:
   `MANGOHUD_CONFIGFILE=/home/deck/deckforge/mangohud-session.conf mangohud %command%`
3. Play normally. Logging starts 60 seconds after launch, which skips the title screens,
   and runs until you quit. A small stats overlay is visible while it logs.
4. **Quit the game normally** before reading the log. A log from a game that is still
   running is incomplete.
5. In Desktop Mode → Konsole, run:
   `cd ~/deckforge-repo && PYTHONPATH=src python3 -m deckforge.measure`
   With in-game frame generation on, add `--fg-multiplier 2`.
6. To stop logging, delete the launch option text.

Logs are about 140 KB per minute. A 2-hour session is about 17 MB.

Optional: Capcom's free **Monster Hunter Wilds Benchmark** plays a fixed scene, which
is useful for repeatable comparisons. Use the same launch option on it.

## Step 6 — GPU profile (E1) — we do this together
Capturing a Radeon GPU Profiler trace uses Mesa driver settings that we'll confirm
live, so don't try this alone. It only needs the same benchmark plus one extra launch
option.

## Undo everything
- Remove the launch option text from the game's properties.
- `sudo systemctl disable --now sshd`
- Delete the `~/deckforge` and `~/deckforge-repo` folders in the file manager.
