#!/usr/bin/env bash
# ============================================================
# Setup Quick Launcher & Server Supervisor (GUI - v2.1)
# Usage: bash setup_launcher_gui.sh
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/.local/share/quicklauncher"

echo "== 1. Cai thu vien GTK cho Python =="
sudo apt update
sudo apt install -y python3-gi gir1.2-gtk-3.0 gir1.2-pango-1.0
sudo apt install -y policykit-1 2>/dev/null   || sudo apt install -y polkitd pkexec   || echo "Canh bao: khong cai duoc goi polkit, app can root co the loi."

echo "== 2. Tao thu muc can thiet =="
mkdir -p "$HOME/.local/bin" "$APP_DIR" "$HOME/.local/share/applications" "$HOME/.config/quicklauncher" "$HOME/.cache/quicklauncher"
touch "$HOME/.config/quicklauncher/items.tsv"

echo "== 3. Dung ban cu (neu co) & cai dat ma nguon moi =="
pkill -f "$APP_DIR/launcher_gui.py" 2>/dev/null || true
rm -f "$HOME/.cache/quicklauncher"/ql-*.sock

cp "$SCRIPT_DIR/core.py" "$APP_DIR/core.py"
cp "$SCRIPT_DIR/launcher_gui.py" "$APP_DIR/launcher_gui.py"
chmod +x "$APP_DIR/launcher_gui.py"

cat > "$HOME/.local/bin/launcher_gui.py" << WRAPPER_EOF
#!/usr/bin/env bash
exec python3 "$APP_DIR/launcher_gui.py" "\$@"
WRAPPER_EOF
chmod +x "$HOME/.local/bin/launcher_gui.py"

echo "== 4. Tao file .desktop =="
cat > "$HOME/.local/share/applications/quicklauncher.desktop" << DESKTOP_EOF
[Desktop Entry]
Type=Application
Name=Quick Launcher
Comment=Mo nhanh app/website va quan ly server du an
Exec=python3 $APP_DIR/launcher_gui.py
Icon=applications-utilities
Terminal=false
Categories=Utility;
StartupNotify=true
DESKTOP_EOF

update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo "== 5. Gan phim tat Super+W (GNOME) =="
if command -v gsettings >/dev/null 2>&1; then
  KB_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/quicklauncher/"
  python3 - "$KB_PATH" <<'PY'
import ast, subprocess, sys

kb_path = sys.argv[1]
schema = "org.gnome.settings-daemon.plugins.media-keys"
cur = subprocess.check_output(["gsettings", "get", schema, "custom-keybindings"], text=True).strip()
if cur.startswith("@as "):
    cur = cur[4:]
try:
    items = list(ast.literal_eval(cur))
except Exception:
    items = []
if kb_path not in items:
    items.append(kb_path)
subprocess.run(["gsettings", "set", schema, "custom-keybindings", repr(items)], check=True)
PY

  KB_SCHEMA="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$KB_PATH"
  gsettings set "$KB_SCHEMA" name "Quick Launcher"
  gsettings set "$KB_SCHEMA" command "python3 $APP_DIR/launcher_gui.py"
  gsettings set "$KB_SCHEMA" binding "<Super>w"
fi

echo ""
echo "============================================"
echo " Cai dat xong ban v2.1!"
echo " - Nhan Super+W de mo Quick Launcher."
echo " - Phim 1 (hoac Ctrl+1): Tab Web & App."
echo " - Phim 2 (hoac Ctrl+2): Tab Quan ly Server."
echo "============================================"
