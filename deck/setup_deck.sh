#!/usr/bin/env bash
# DeckForge — Steam Deck bench setup (Phase 0).
#
# Safe by design:
#   - Creates folders only under ~/deckforge. Never deletes or overwrites anything.
#   - Does not touch your global MangoHud config, Steam files or games.
#   - Never runs sudo. Steps that need your password are printed for you to run.
# Re-running it is harmless.
set -u

DF="$HOME/deckforge"
report="$DF/env.txt"

say()  { printf '%s\n' "$*"; }
ok()   { printf '  [ok]   %s\n' "$*"; }
todo() { printf '  [todo] %s\n' "$*"; }

say "== DeckForge Deck setup =="

# 1. Folders (mkdir -p never removes or overwrites anything)
mkdir -p "$DF/logs" "$DF/captures" "$DF/bench" "$DF/backups"
ok "folders ready under $DF"

# 2. Environment report (what every benchmark result will be tagged with)
board="$(cat /sys/devices/virtual/dmi/id/board_name 2>/dev/null || echo unknown)"
case "$board" in
  Galileo) model="OLED" ;;
  Jupiter) model="LCD" ;;
  *)       model="unknown ($board)" ;;
esac
os_ver="$(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-unknown} ${VERSION_ID:-}")"
mesa_ver="$(pacman -Q mesa 2>/dev/null || echo 'mesa: unknown')"
{
  echo "date: $(date -Iseconds)"
  echo "device_model: $model"
  echo "os: $os_ver"
  echo "kernel: $(uname -r)"
  echo "$mesa_ver"
  echo "free_space_home: $(df -h "$HOME" | awk 'NR==2 {print $4}')"
} > "$report"
ok "environment recorded in $report"
sed 's/^/         /' "$report"

# 3. MangoHud (SteamOS ships it; we only add a separate config file for benchmarks)
if command -v mangohud >/dev/null 2>&1; then
  ok "MangoHud found"
else
  todo "MangoHud not found on PATH. Tell Claude; we'll install it as a Flatpak/user package."
fi
conf="$DF/mangohud-bench.conf"
if [ -e "$conf" ]; then
  ok "benchmark MangoHud config already exists (left unchanged): $conf"
else
  cat > "$conf" <<EOF
# DeckForge benchmark logging config. Used only when a game's launch options point here.
fps
frametime
gpu_stats
cpu_stats
output_folder=$DF/logs
log_interval=0
autostart_log=10
log_duration=60
EOF
  ok "benchmark MangoHud config written: $conf"
fi

# 4. Python environment for the bench runner (in your home folder, survives updates)
if [ -x "$DF/venv/bin/python" ]; then
  ok "Python venv already exists"
elif python3 -m venv "$DF/venv" >/dev/null 2>&1; then
  ok "Python venv created at $DF/venv"
else
  todo "Could not create a Python venv. Tell Claude; we'll use a different method."
fi

# 5. SSH, so your Mac can send benchmark jobs (needs your password, so you run it)
if systemctl is-active --quiet sshd 2>/dev/null; then
  ok "SSH is running"
else
  todo "SSH is off. Run these two commands yourself:"
  say  "           passwd                          # only if you never set a password"
  say  "           sudo systemctl enable --now sshd"
fi
ip_addr="$(ip -4 -o addr show 2>/dev/null | awk '$2 != "lo" {print $4}' | cut -d/ -f1 | head -n1)"
say "  [info] Deck address on your Wi-Fi: ${ip_addr:-unknown}  (from the Mac: ssh deck@${ip_addr:-<address>})"

# 6. What to paste into a game's Launch Options for a baseline run
say ""
say "== Launch options for a logged benchmark run =="
say "MANGOHUD_CONFIGFILE=$conf mangohud %command%"
say ""
say "Done. Nothing outside $DF was changed."
