# ⚡ MacTech Android Tool v2.3 (Universal Edition)
### *Cross-Platform Hardware Forensics, Live Screen Mirroring & ADB Diagnostic Suite*
**Engineered by MacTech Solutions Lab** | **Author:** Mark Vollan Barracks (`markvollanbarracks@gmail.com`)

[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20Lab-blue.svg)](LICENSE)
[![Platforms](https://img.shields.io/badge/Platforms-Windows%20%7C%20Linux%20%7C%20macOS-brightgreen.svg)](https://mactechsolutionslab.vercel.app/products.html#mactech-android)
[![PayPal Donate](https://img.shields.io/badge/Donate-PayPal-0070BA.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=markvollanbarracks@gmail.com&currency_code=USD&item_name=Support+MacTech+Android+Tool+Development)

---

## 📌 Overview

**MacTech Android Tool** is a high-performance cross-platform application for **Windows**, **Linux**, and **macOS** designed for computer repair technicians, digital forensics investigators, and power users. It provides low-level Android hardware interrogation, real-time app inspection, solid-state storage TRIM/defragmentation, broken-screen data extraction, live interactive screen mirroring with touch and precision trackpad gestures, and an industry-first **Forensic Fake Phone & Clone Detector**.

All ADB, Fastboot, and shell operations execute silently in the background with process window suppression, preventing terminal flashing.

---

## 💻 Cross-Platform Support

| Platform | Supported Environments | Quick Launch |
| :--- | :--- | :--- |
| **Windows** | Windows 10 & 11 (64-bit) | Run `MacTech_Android_Tool.exe` or `Launch_Tool.bat` |
| **Linux** | Ubuntu, Debian, Arch, Fedora, openSUSE | Run `./launch_linux.sh` (or `./setup_linux.sh`) |
| **macOS** | Apple Silicon (M1/M2/M3/M4) & Intel (macOS 10.13+) | Double-click `launch_mac.command` or `MacTech Android Tool.app` |

---

## 🌟 Key Features

### 1. 🔍 Forensic Fake / Clone Phone Inspector
Counterfeit devices (fake Samsung Galaxy S24 Ultra, clone iPhone 15/16 Pro Max running Android, fake Xiaomi/Tecno) routinely spoof Android's `Settings` app and userland `build.prop` files to advertise fake 16GB RAM, Snapdragon 8 Gen 3 CPUs, 1TB storage, and Android 14/15.
- **Direct Kernel Memory Check:** Queries raw `cat /proc/meminfo` (`MemTotal`) to uncover true physical RAM (often exposing 1GB or 2GB on clones claiming 16GB).
- **Physical CPU & SoC Auditing:** Reads `/proc/cpuinfo` hardware identifiers, detecting obsolete 32-bit MediaTek MT6580 or Spreadtrum chipsets masked as modern 64-bit processors.
- **Kernel Build Date vs OS Release:** Flags fake Android 14 ROMs that run antique Linux 3.18 or 4.4 kernels compiled years prior.
- **Physical Window Resolution:** Compares advertised QHD+ resolutions against raw `wm size` outputs.
- **Build Signature & Test-Keys:** Detects unofficial developer test-keys and spoofed OEM fingerprints.

### 2. 🚀 Active Foreground App Tracker & Immediate Uninstaller
- Queries the Android Window Manager and Activity Manager (`dumpsys window mCurrentFocus`) to pinpoint the exact package and activity class currently running on screen.
- One-click instant uninstallation of malware, adware overlays, and unwanted foreground bloatware.
- Options for standard uninstallation or non-root User 0 debloating (`pm uninstall -k --user 0`).

### 3. 📦 Comprehensive Searchable App Manager
- Browse installed packages categorized into **User Apps (-3)**, **System Apps (-s)**, or **All Packages**.
- Search in real-time by package name or vendor.
- Deep package inspection: first install date/time, last update date/time, version name/code, APK location.
- Extract any installed APK to PC or install new `.apk` packages via drag-and-drop.

### 4. 💾 ADB Data Recovery Suite
- Extract user data from devices with shattered or unresponsive touch screens:
  - **Camera & DCIM:** Full photos and high-resolution videos.
  - **WhatsApp Media:** Pictures, videos, voice notes, and documents.
  - **Documents & Downloads:** Downloaded PDFs, invoices, and archives.
  - **Audio & Dictaphone:** Sound recordings and music files.
  - **Full Storage Clone:** Copies entire `/sdcard/` structure.
  - **Full ADB Backup:** Generates native encrypted `.ab` system backup archives.

### 5. ⚡ Clean, Storage TRIM & ART Defragmentation
- **Native Cache Trimmer:** Invokes `pm trim-caches` across all applications.
- **Storage TRIM (fstrim):** Issues low-level flash TRIM commands to `/data`, `/cache`, and `/system` to unmap deleted blocks and restore NAND I/O read/write speeds.
- **Temp Dumps Cleaner:** Cleans `/data/local/tmp`, old ANR traces, and tombstones.
- **ART Ahead-Of-Time Speed Boost:** Forces Android Runtime compiler optimization (`cmd package compile -m speed -a`) to eliminate stutter and UI lag.

### 6. 🎮 Live Screen Stream & Interactive Remote Control
- **Real-Time Live Auto-Stream:** Continuous low-latency screen streaming without pressing manual refresh buttons. See everything happening on the phone live.
- **Direct Touch & Click Control:** Click directly on phone screen icons, menus, and buttons to open apps and trigger actions.
- **Drag & Swipe Gestures:** Click and drag to swipe through home screens, scroll through lists, feeds, and settings menus.
- **Mouse Wheel Scrolling:** Use your PC mouse wheel to smoothly scroll up and down on the phone display.
- **Android Navigation Shortcuts:** Dedicated `◀ BACK`, `● HOME`, and `■ RECENTS` navigation buttons below the screen canvas.
- **Gesture Shortcuts:** Right-click simulates Android `BACK`, Middle-click simulates Android `HOME`.
- **Direct PC Keyboard Input:** Type text with your computer keyboard directly into focused input fields on the device.
- **Visual Touch Feedback:** Glowing ripple animations give instant tactile visual confirmation of your taps on screen.
- **⚡ Ultra 60FPS Scrcpy Window:** One-click launch for full hardware-accelerated 60FPS low-latency mirroring with audio pass-through and drag-and-drop file transfers.

### 7. 📁 MTP & Windows Portable Device Explorer
- Detects devices connected via USB cable even when **USB Debugging is OFF**.
- Queries Windows Portable Devices (WPD) via PowerShell and WMI to read model name, storage volumes, and capacity.

### 8. 💻 Silent Interactive Terminal
- Direct command-line shell with preset pills (`getprop`, `df -h`, `dumpsys battery`, `ip addr`, `top -n 1`, `ps -A`).

---

## ☕ Support the Developer & Lab

If this tool assisted your diagnostics or recovered valuable client data, please consider supporting MacTech Solutions Lab:
- **PayPal Donation Link:** [Donate to MacTech Solutions Lab](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=markvollanbarracks@gmail.com&currency_code=USD&item_name=Support+MacTech+Android+Tool+Development)
- **PayPal Direct Account:** `markvollanbarracks@gmail.com`

---

## 🛠️ Installation & Setup by Operating System

### 🪟 Windows (10 / 11)
- **Standalone:** Download `MacTech_Android_Tool_v2.3_Windows.zip`, extract, and run `MacTech_Android_Tool.exe` or `Launch_Tool.bat`. Run `Trust_Publisher_And_Run.bat` to trust the MacTech Solutions Lab Authenticode certificate and bypass Windows SmartScreen.
- **From Source:**
  ```cmd
  pip install -r requirements.txt
  python main.py
  ```

### 🐧 Linux (Ubuntu / Debian / Fedora / Arch)
- **Automated Setup:**
  ```bash
  chmod +x setup_linux.sh launch_linux.sh
  ./setup_linux.sh
  ```
  *This automatically configures Python 3, ADB, Scrcpy, and USB udev permissions (`51-android.rules`).*
- **Launch:** Run `./launch_linux.sh` or find **MacTech Android Tool** in your application launcher.

### 🍎 macOS (Apple Silicon M1/M2/M3/M4 & Intel)
- **Automated Setup:**
  ```bash
  chmod +x setup_mac.sh launch_mac.command
  ./setup_mac.sh
  ```
- **Launch:** Double-click `launch_mac.command` in Finder, double-click `MacTech Android Tool.app`, or run `./launch_mac.command` in Terminal.

---

## 🔒 Security & Privacy Notice
All operations and file transfers execute locally on your computer. No diagnostic telemetry or extracted personal files are ever uploaded or transmitted outside your local machine.

---
*© MacTech Solutions Lab. All rights reserved.*
