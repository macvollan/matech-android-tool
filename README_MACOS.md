# MacTech Android Tool - macOS Quickstart Guide

Professional Smartphone Hardware Forensics, Live Screen Mirroring & ADB Controller for Apple macOS (Intel & Apple Silicon M1/M2/M3/M4).

## Prerequisites
- macOS 10.13 High Sierra or newer
- Python 3 with Tkinter
- Android Platform Tools (`adb`)

## 1-Step Setup
Open Terminal in this folder and run:
```bash
chmod +x setup_mac.sh
./setup_mac.sh
```
This automatically:
1. Installs or verifies Homebrew.
2. Installs `python`, `python-tk`, `android-platform-tools`, and `scrcpy`.
3. Installs UI dependencies (`customtkinter`, `pillow`).
4. Configures macOS permissions.

## Launching
Choose whichever method you prefer:
1. Double-click **`launch_mac.command`** in Finder.
2. Or double-click **`MacTech Android Tool.app`**.
3. Or in Terminal, run:
   ```bash
   ./launch_mac.command
   ```

### Gatekeeper Note
If macOS shows *"App can't be opened because it is from an unidentified developer"*, either:
- Right-click (or Control-click) `launch_mac.command` or `MacTech Android Tool.app` and choose **Open**.
- Or run in Terminal:
  ```bash
  xattr -cr "MacTech Android Tool.app"
  ```

---
© MacTech Solutions Lab • https://mactechsolutionslab.vercel.app
