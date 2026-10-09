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
(Exact URL will match wherever we create the repo.)

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

## Step 5 — First Monster Hunter Wilds baseline (about 20 min)
We use Capcom's free **Monster Hunter Wilds Benchmark** app (search it in the Steam
store) because it's repeatable.
1. Back in Game Mode, open the benchmark app → ⚙ → Properties → **Launch Options**, paste
   the line the setup script printed (`MANGOHUD_CONFIGFILE=... mangohud %command%`).
2. In the Quick Access menu → Performance: per-game profile ON, frame limit OFF,
   TDP default. Write down what you set.
3. Use the graphics settings you normally play with. Take a photo of the settings screen.
4. Run the benchmark **3 times**. The first run warms up shaders; we keep all three and
   discard the first in analysis.
5. Logs appear in `~/deckforge/logs/`. Claude will tell you how to send them (USB stick,
   or over SSH once it's on).

## Step 6 — GPU profile (E1) — we do this together
Capturing a Radeon GPU Profiler trace uses Mesa driver settings that we'll confirm
live, so don't try this alone. It only needs the same benchmark plus one extra launch
option.

## Undo everything
- Remove the launch option text from the game's properties.
- `sudo systemctl disable --now sshd`
- Delete the `~/deckforge` and `~/deckforge-repo` folders in the file manager.
