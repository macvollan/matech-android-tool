#!/usr/bin/env bash
# ==============================================================================
# MacTech Android Tool - macOS Launcher
# MacTech Solutions Lab - https://mactechsolutionslab.vercel.app
# ==============================================================================

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "============================================================"
echo "  MacTech Android Tool v2.3 (macOS Edition)"
echo "  MacTech Solutions Lab"
echo "============================================================"

# Ensure Homebrew and standard PATHs are accessible
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:$PATH"

# Locate Python 3
PYTHON_BIN=""
if command -v python3 &>/dev/null; then
    PYTHON_BIN="python3"
elif [ -f "/opt/homebrew/bin/python3" ]; then
    PYTHON_BIN="/opt/homebrew/bin/python3"
elif [ -f "/usr/local/bin/python3" ]; then
    PYTHON_BIN="/usr/local/bin/python3"
else
    echo "[!] Python 3 was not found on your Mac."
    echo "    Please install Python 3 via Homebrew: brew install python python-tk"
    echo "    Or download from https://www.python.org/downloads/macos/"
    read -p "Press Return to exit..."
    exit 1
fi

# Check for required python modules
$PYTHON_BIN -c "import customtkinter, PIL" 2>/dev/null || {
    echo "[*] Installing required modules (customtkinter, pillow)..."
    $PYTHON_BIN -m pip install --user -r requirements.txt || true
}

# Check for ADB
if ! command -v adb &>/dev/null && [ ! -f "bin/adb" ]; then
    echo "[!] Notice: ADB was not found in PATH."
    echo "    Install Android Platform Tools via Homebrew:"
    echo "      brew install android-platform-tools scrcpy"
    echo ""
fi

echo "[*] Starting MacTech Android Tool..."
exec $PYTHON_BIN "$DIR/main.py" "$@"
