# MacTech Android Tool - Linux Quickstart Guide

Professional Smartphone Hardware Forensics, Live Screen Mirroring & ADB Controller.

## Prerequisites
- Python 3.8 or newer
- Android Tools (`adb`, `fastboot`)
- `scrcpy` (optional, for ultra 60FPS mirroring)

## 1-Minute Automated Setup
Open a terminal in this directory and run:
```bash
chmod +x setup_linux.sh
./setup_linux.sh
```
This automatically:
1. Installs system packages via your package manager (`apt`, `dnf`, or `pacman`).
2. Installs Python UI libraries (`customtkinter`, `pillow`).
3. Installs Android udev rules (`51-android.rules`) so your user account can interact with connected Android devices via USB without `sudo`.
4. Adds **MacTech Android Tool** to your desktop application menu.

## Launching
```bash
./launch_linux.sh
```
Or search for **MacTech Android Tool** in your application launcher.

---
© MacTech Solutions Lab • https://mactechsolutionslab.vercel.app
