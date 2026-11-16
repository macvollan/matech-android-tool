#!/usr/bin/env bash
# ==============================================================================
# MacTech Android Tool - Linux Universal Launcher
# MacTech Solutions Lab - https://mactechsolutionslab.vercel.app
# ==============================================================================

set -e

# Resolve script directory (handles symlinks)
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0" 2>/dev/null || realpath "$0" 2>/dev/null || echo "$0")")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "  MacTech Android Tool v2.3 (Linux Edition)"
echo "  Automated Android Diagnostic & Forensic Suite"
echo "============================================================"

# Check for Python 3
if ! command -v python3 &>/dev/null; then
    echo "[!] Python 3 was not found."
    echo "    Please install Python 3 and Tkinter:"
    echo "    Ubuntu/Debian: sudo apt install python3 python3-pip python3-tk"
    echo "    Fedora/RHEL:   sudo dnf install python3 python3-pip python3-tkinter"
    echo "    Arch Linux:    sudo pacman -S python python-pip tk"
    exit 1
fi

# Ensure pip packages are installed
python3 -c "import customtkinter, PIL" 2>/dev/null || {
    echo "[*] Installing required Python libraries (customtkinter, pillow)..."
    python3 -m pip install --user -r requirements.txt || {
        echo "[!] Automatic pip install failed. Trying with --break-system-packages..."
        python3 -m pip install --user --break-system-packages -r requirements.txt || true
    }
}

# Check for ADB
if ! command -v adb &>/dev/null && [ ! -f "bin/adb" ]; then
    echo "[!] Warning: ADB was not found on your system."
    echo "    Install Android platform-tools via:"
    echo "    Ubuntu/Debian: sudo apt install adb"
    echo "    Arch Linux:    sudo pacman -S android-tools"
    echo "    Fedora:        sudo dnf install android-tools"
fi

# Launch MacTech Android Tool
echo "[*] Launching MacTech Android Tool..."
exec python3 "$SCRIPT_DIR/main.py" "$@"
