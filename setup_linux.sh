#!/usr/bin/env bash
# ==============================================================================
# MacTech Android Tool - Linux One-Step Environment & Udev Setup
# MacTech Solutions Lab - https://mactechsolutionslab.vercel.app
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || realpath "$0" 2>/dev/null || echo "$0")")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  MacTech Android Tool - Linux Environment Installer"
echo "  MacTech Solutions Lab"
echo "============================================================"
echo ""

# 1. Package Manager Detection & System Dependencies
if command -v apt-get &>/dev/null; then
    echo "[*] Detected Debian / Ubuntu / Mint / Pop!_OS"
    echo "[*] Installing required packages (Python3, Tk, ADB, Fastboot, Scrcpy)..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-tk adb fastboot scrcpy
elif command -v dnf &>/dev/null; then
    echo "[*] Detected Fedora / RHEL / CentOS"
    echo "[*] Installing required packages..."
    sudo dnf install -y python3 python3-pip python3-tkinter android-tools scrcpy
elif command -v pacman &>/dev/null; then
    echo "[*] Detected Arch Linux / Manjaro / EndeavourOS"
    echo "[*] Installing required packages..."
    sudo pacman -Sy --noconfirm python python-pip tk android-tools scrcpy
elif command -v zypper &>/dev/null; then
    echo "[*] Detected openSUSE"
    sudo zypper install -y python3 python3-pip python3-tk android-tools scrcpy
else
    echo "[!] Unrecognized package manager. Please ensure python3, tk, adb, and scrcpy are installed manually."
fi

# 2. Python Packages
echo ""
echo "[*] Installing Python dependencies (CustomTkinter, Pillow)..."
python3 -m pip install --user -r requirements.txt || python3 -m pip install --user --break-system-packages -r requirements.txt

# 3. Android USB Udev Rules (Non-root ADB access)
echo ""
echo "[*] Configuring Android USB udev rules for non-root device access..."
UDEV_RULE_FILE="/etc/udev/rules.d/51-android.rules"
if [ ! -f "$UDEV_RULE_FILE" ]; then
    echo '[*] Creating /etc/udev/rules.d/51-android.rules...'
    sudo tee "$UDEV_RULE_FILE" > /dev/null << 'EOF'
# Android ADB & Fastboot udev rules
SUBSYSTEM=="usb", ATTR{idVendor}=="0bb4", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0e79", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0502", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0b05", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="413c", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0489", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="091e", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="18d1", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="201e", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="109b", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="12d1", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="24e3", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="2116", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0482", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="17ef", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="1004", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="22b8", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0e8d", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0409", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="2080", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0955", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="2257", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="10a9", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="1d4d", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0471", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="04da", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="05c6", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="1f53", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="04e8", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="04dd", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0fce", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="0930", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="2717", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="2970", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="19d2", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="usb", ATTR{idVendor}=="2b4c", MODE="0666", GROUP="plugdev"
EOF
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    echo "[✔] Udev rules installed and reloaded."
else
    echo "[✔] Android udev rules file already exists."
fi

# Add current user to plugdev group if it exists
if grep -q plugdev /etc/group; then
    sudo usermod -aG plugdev "$USER" || true
fi

# 4. Create Desktop Application Shortcut
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"
DESKTOP_FILE="$DESKTOP_DIR/mactech-android-tool.desktop"

chmod +x "$SCRIPT_DIR/launch_linux.sh"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=MacTech Android Tool
Comment=Professional Smartphone Hardware Forensics & Live ADB Control
Exec=$SCRIPT_DIR/launch_linux.sh
Icon=$SCRIPT_DIR/assets/icon.png
Terminal=false
Type=Application
Categories=Development;Utility;HardwareSettings;
Keywords=android;adb;fastboot;scrcpy;diagnostics;forensics;
EOF

chmod +x "$DESKTOP_FILE"
echo "[✔] Created desktop shortcut: $DESKTOP_FILE"

echo ""
echo "============================================================"
echo "✔ Setup Completed Successfully!"
echo "  Launch the tool by running:"
echo "    ./launch_linux.sh"
echo "  Or find 'MacTech Android Tool' in your Application Menu."
echo "============================================================"
