# ⚡ MacTech Android Tool v2.2
### *Enterprise Diagnostic, Hardware Authenticity & Forensic ADB Suite*
**Engineered by MacTech Solutions Lab** | **Author:** Mark Vollan Barracks (`markvollanbarracks@gmail.com`)

[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20Lab-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011-brightgreen.svg)](https://microsoft.com/windows)
[![PayPal Donate](https://img.shields.io/badge/Donate-PayPal-0070BA.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=markvollanbarracks@gmail.com&currency_code=USD&item_name=Support+MacTech+Android+Tool+Development)

---

## 📌 Overview

**MacTech Android Tool** is a high-performance Windows PC application designed for computer repair technicians, digital forensics investigators, and power users. It provides low-level Android hardware interrogation, real-time app inspection, solid-state storage TRIM/defragmentation, broken-screen data extraction, and an industry-first **Forensic Fake Phone & Clone Detector**.

All ADB, MTP, and shell operations execute **completely silently** in the background using native Windows process suppression flags (`STARTF_USESHOWWINDOW` + `CREATE_NO_WINDOW`), preventing any command prompt flashing.

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

### 6. 🎮 Virtual Remote Control & High-Speed Mirroring
- Silent screen capture preview using `exec-out screencap -p`.
- Virtual hardware keypad: Power, Home, Back, App Switcher, Volume Up/Down, Menu/Unlock, Enter.
- Remote PC-to-Phone text typing pipeline.

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

## 🛠️ Installation & Setup

### Requirements
- Windows 10 or 11 (64-bit)
- Python 3.10+ (if running from source)
- Bundled with internal `adb.exe` and WinUSB drivers (no separate SDK download required).

```bash
# Clone the repository
git clone https://github.com/macvollan/mactech-android-tool.git
cd mactech-android-tool

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

---

## 🔒 Security & Privacy Notice
All operations and file transfers execute locally on your computer. No diagnostic telemetry or extracted personal files are ever uploaded or transmitted outside your local machine.

---
*© MacTech Solutions Lab. All rights reserved.*
