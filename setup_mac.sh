#!/usr/bin/env bash
# ==============================================================================
# MacTech Android Tool - macOS Quick Setup Script
# MacTech Solutions Lab - https://mactechsolutionslab.vercel.app
# ==============================================================================

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "============================================================"
echo "  MacTech Android Tool - macOS Setup"
echo "  MacTech Solutions Lab"
echo "============================================================"
echo ""

# 1. Check for Homebrew
if ! command -v brew &>/dev/null; then
    echo "[!] Homebrew is not installed."
    echo "    Installing Homebrew (macOS Package Manager)..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for current session
    if [ -d "/opt/homebrew/bin" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        eval "$(/usr/local/bin/brew shellenv)"
    fi
fi

# 2. Install Python 3, Tkinter, ADB & Scrcpy
echo "[*] Installing dependencies via Homebrew..."
brew install python python-tk android-platform-tools scrcpy || true

# 3. Install Python UI Libraries
echo "[*] Installing CustomTkinter & Pillow..."
python3 -m pip install --user -r requirements.txt || python3 -m pip install --user --break-system-packages -r requirements.txt

# 4. Make launcher scripts executable
chmod +x "$DIR/launch_mac.command"
if [ -f "$DIR/MacTech Android Tool.app/Contents/MacOS/app_launcher" ]; then
    chmod +x "$DIR/MacTech Android Tool.app/Contents/MacOS/app_launcher"
fi

# 5. Fix Gatekeeper Quarantine attribute if downloaded from the web
xattr -d com.apple.quarantine "$DIR/launch_mac.command" 2>/dev/null || true
if [ -d "$DIR/MacTech Android Tool.app" ]; then
    xattr -cr "$DIR/MacTech Android Tool.app" 2>/dev/null || true
fi

echo ""
echo "============================================================"
echo "✔ macOS Setup Completed Successfully!"
echo "  To launch the application:"
echo "    1. Double-click 'launch_mac.command' in Finder"
echo "    2. Or double-click 'MacTech Android Tool.app'"
echo "    3. Or run: ./launch_mac.command in Terminal"
echo "============================================================"
