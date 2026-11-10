"""
MacTech Android Tool - Vast Command Library & Presets
Engineered for MacTech Solutions Lab
Over 60+ categorized, battle-tested ADB and shell commands for diagnostics,
forensics, debloating, hardware telemetry, performance optimization, and recovery.
"""

from typing import List, Dict, Optional

COMMAND_CATEGORIES = [
    "All Commands",
    "Power & Boot",
    "Display & UI",
    "Battery & Hardware",
    "Packages & Apps",
    "Network & IP",
    "Forensics & Clones",
    "Speed & Performance",
    "Logs & Debugging",
    "Storage & Recovery"
]

VAST_COMMANDS: List[Dict[str, str]] = [
    # =========================================================================
    # Category 1: Power & Boot Modes
    # =========================================================================
    {
        "category": "Power & Boot",
        "name": "Normal Reboot",
        "cmd": "reboot",
        "desc": "Safely reboots the Android operating system.",
        "level": "safe"
    },
    {
        "category": "Power & Boot",
        "name": "Reboot to Recovery",
        "cmd": "reboot recovery",
        "desc": "Reboots directly into stock or custom (TWRP/OrangeFox) recovery.",
        "level": "safe"
    },
    {
        "category": "Power & Boot",
        "name": "Reboot to Bootloader / Fastboot",
        "cmd": "reboot bootloader",
        "desc": "Reboots phone into Fastboot / Bootloader mode for partition flashing.",
        "level": "medium"
    },
    {
        "category": "Power & Boot",
        "name": "Reboot to EDL Mode",
        "cmd": "reboot edl",
        "desc": "Reboots Qualcomm device into Emergency Download Mode (Firehose).",
        "level": "advanced"
    },
    {
        "category": "Power & Boot",
        "name": "Reboot to Safe Mode",
        "cmd": "setprop persist.sys.safemode 1; reboot",
        "desc": "Boots into Safe Mode, disabling all 3rd-party apps and startup malware.",
        "level": "medium"
    },
    {
        "category": "Power & Boot",
        "name": "Power Off Device",
        "cmd": "reboot -p",
        "desc": "Powers off and shuts down device completely.",
        "level": "safe"
    },
    {
        "category": "Power & Boot",
        "name": "Wake Up Screen",
        "cmd": "input keyevent 26",
        "desc": "Simulates pressing physical Power key to turn on display.",
        "level": "safe"
    },
    {
        "category": "Power & Boot",
        "name": "Unlock Lockscreen",
        "cmd": "input keyevent 82",
        "desc": "Dismisses lockscreen / keyguard if no secure PIN or pattern is set.",
        "level": "safe"
    },
    {
        "category": "Power & Boot",
        "name": "Simulate Home Button",
        "cmd": "input keyevent 3",
        "desc": "Sends KeyCode 3 (KEYCODE_HOME) to return to launcher.",
        "level": "safe"
    },
    {
        "category": "Power & Boot",
        "name": "Simulate Back Button",
        "cmd": "input keyevent 4",
        "desc": "Sends KeyCode 4 (KEYCODE_BACK) to navigate back.",
        "level": "safe"
    },

    # =========================================================================
    # Category 2: Display & UI
    # =========================================================================
    {
        "category": "Display & UI",
        "name": "Get Screen Resolution",
        "cmd": "wm size",
        "desc": "Queries physical framebuffer resolution (e.g. 1080x2400).",
        "level": "safe"
    },
    {
        "category": "Display & UI",
        "name": "Set Resolution (1080x2400)",
        "cmd": "wm size 1080x2400",
        "desc": "Overrides display resolution (useful for gaming or testing).",
        "level": "medium"
    },
    {
        "category": "Display & UI",
        "name": "Reset Screen Resolution",
        "cmd": "wm size reset",
        "desc": "Restores factory default display resolution.",
        "level": "safe"
    },
    {
        "category": "Display & UI",
        "name": "Get Screen Density (DPI)",
        "cmd": "wm density",
        "desc": "Shows active display pixel density (DPI).",
        "level": "safe"
    },
    {
        "category": "Display & UI",
        "name": "Set Compact UI DPI (420)",
        "cmd": "wm density 420",
        "desc": "Changes DPI to 420 to fit more content and compact UI.",
        "level": "medium"
    },
    {
        "category": "Display & UI",
        "name": "Reset Screen Density",
        "cmd": "wm density reset",
        "desc": "Restores default OEM display DPI.",
        "level": "safe"
    },
    {
        "category": "Display & UI",
        "name": "Show Touch Circles",
        "cmd": "settings put system show_touches 1",
        "desc": "Enables visual touch dot indicator under fingers.",
        "level": "safe"
    },
    {
        "category": "Display & UI",
        "name": "Hide Touch Circles",
        "cmd": "settings put system show_touches 0",
        "desc": "Disables visual touch dot indicator.",
        "level": "safe"
    },
    {
        "category": "Display & UI",
        "name": "Show Pointer Location Crosshairs",
        "cmd": "settings put system pointer_location 1",
        "desc": "Displays real-time touch coordinate bar and crosshairs for digitizer testing.",
        "level": "safe"
    },
    {
        "category": "Display & UI",
        "name": "Hide Pointer Location",
        "cmd": "settings put system pointer_location 0",
        "desc": "Disables digitizer coordinate overlay.",
        "level": "safe"
    },
    {
        "category": "Display & UI",
        "name": "Keep Screen Awake on USB",
        "cmd": "svc power stayon true",
        "desc": "Forces screen to remain powered while connected to USB.",
        "level": "safe"
    },
    {
        "category": "Display & UI",
        "name": "Reset Screen Stay Awake",
        "cmd": "svc power stayon false",
        "desc": "Restores normal screen sleep timeout.",
        "level": "safe"
    },

    # =========================================================================
    # Category 3: Battery & Hardware
    # =========================================================================
    {
        "category": "Battery & Hardware",
        "name": "Full Battery Dumpsys",
        "cmd": "dumpsys battery",
        "desc": "Pulls battery level, health status, temperature, voltage, and charger AC/USB.",
        "level": "safe"
    },
    {
        "category": "Battery & Hardware",
        "name": "Simulate 100% Battery",
        "cmd": "dumpsys battery set level 100",
        "desc": "Simulates 100% battery level for testing low-power triggers.",
        "level": "medium"
    },
    {
        "category": "Battery & Hardware",
        "name": "Simulate 15% Low Battery",
        "cmd": "dumpsys battery set level 15",
        "desc": "Simulates 15% battery warning state.",
        "level": "medium"
    },
    {
        "category": "Battery & Hardware",
        "name": "Simulate Unplugged Charger",
        "cmd": "dumpsys battery unplug",
        "desc": "Forces device into battery discharging mode while tethered.",
        "level": "medium"
    },
    {
        "category": "Battery & Hardware",
        "name": "Reset Battery Emulation",
        "cmd": "dumpsys battery reset",
        "desc": "Restores real physical battery hardware telemetry readings.",
        "level": "safe"
    },
    {
        "category": "Battery & Hardware",
        "name": "CPU Core Frequencies",
        "cmd": "cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq",
        "desc": "Reads current clock frequency in kHz across all active CPU cores.",
        "level": "safe"
    },
    {
        "category": "Battery & Hardware",
        "name": "Thermal Sensor Status",
        "cmd": "dumpsys thermalservice",
        "desc": "Dumps thermal status, throttle temperatures, and cooling devices.",
        "level": "safe"
    },
    {
        "category": "Battery & Hardware",
        "name": "Physical Sensor List",
        "cmd": "dumpsys sensorservice",
        "desc": "Inspects accelerometer, gyroscope, magnetic, proximity, and light sensors.",
        "level": "safe"
    },

    # =========================================================================
    # Category 4: Packages & Apps
    # =========================================================================
    {
        "category": "Packages & Apps",
        "name": "Active App on Screen",
        "cmd": "dumpsys window | grep -E \"mCurrentFocus|mFocusedApp\"",
        "desc": "Reveals active package name and focused activity window on screen.",
        "level": "safe"
    },
    {
        "category": "Packages & Apps",
        "name": "List 3rd-Party User Apps",
        "cmd": "pm list packages -3",
        "desc": "Filters installed packages to show user-installed apps only.",
        "level": "safe"
    },
    {
        "category": "Packages & Apps",
        "name": "List System Packages",
        "cmd": "pm list packages -s",
        "desc": "Lists OEM and Android pre-installed system apps.",
        "level": "safe"
    },
    {
        "category": "Packages & Apps",
        "name": "List Disabled / Frozen Apps",
        "cmd": "pm list packages -d",
        "desc": "Lists packages that are currently disabled or frozen.",
        "level": "safe"
    },
    {
        "category": "Packages & Apps",
        "name": "Find APK File Path",
        "cmd": "pm path com.whatsapp",
        "desc": "Finds internal APK storage directory on filesystem (replace package name).",
        "level": "safe"
    },
    {
        "category": "Packages & Apps",
        "name": "Force Stop App",
        "cmd": "am force-stop com.whatsapp",
        "desc": "Terminates all running processes of the target app.",
        "level": "safe"
    },
    {
        "category": "Packages & Apps",
        "name": "Clear App User Data",
        "cmd": "pm clear com.whatsapp",
        "desc": "Wipes app storage, cache, and database (resets to newly installed state).",
        "level": "medium"
    },
    {
        "category": "Packages & Apps",
        "name": "Grant Secure Settings Permission",
        "cmd": "pm grant com.termux android.permission.WRITE_SECURE_SETTINGS",
        "desc": "Grants privileged secure settings write access to an application.",
        "level": "medium"
    },
    {
        "category": "Packages & Apps",
        "name": "Debloat / Freeze (User 0)",
        "cmd": "pm uninstall -k --user 0 com.facebook.katana",
        "desc": "Uninstalls carrier bloatware without requiring root access.",
        "level": "medium"
    },
    {
        "category": "Packages & Apps",
        "name": "Re-enable Frozen App",
        "cmd": "pm enable com.facebook.katana",
        "desc": "Re-enables a previously disabled package.",
        "level": "safe"
    },

    # =========================================================================
    # Category 5: Network & IP
    # =========================================================================
    {
        "category": "Network & IP",
        "name": "Show IP & Interfaces",
        "cmd": "ip addr show",
        "desc": "Displays all network interfaces (wlan0, rmnet0) and assigned IP addresses.",
        "level": "safe"
    },
    {
        "category": "Network & IP",
        "name": "Show IP Routing Table",
        "cmd": "ip route",
        "desc": "Displays default gateway and interface routing table.",
        "level": "safe"
    },
    {
        "category": "Network & IP",
        "name": "Show Open Sockets & Ports",
        "cmd": "netstat -tlpn",
        "desc": "Lists active TCP/UDP listeners and established network sockets.",
        "level": "safe"
    },
    {
        "category": "Network & IP",
        "name": "Ping Test (8.8.8.8)",
        "cmd": "ping -c 4 8.8.8.8",
        "desc": "Tests network reachability and packet latency from the device.",
        "level": "safe"
    },
    {
        "category": "Network & IP",
        "name": "Turn Wi-Fi Radio ON",
        "cmd": "svc wifi enable",
        "desc": "Enables phone's Wi-Fi radio.",
        "level": "safe"
    },
    {
        "category": "Network & IP",
        "name": "Turn Wi-Fi Radio OFF",
        "cmd": "svc wifi disable",
        "desc": "Disables phone's Wi-Fi radio.",
        "level": "safe"
    },
    {
        "category": "Network & IP",
        "name": "Enable Airplane Mode",
        "cmd": "cmd connectivity airplane-mode enable",
        "desc": "Immediately switches on Airplane Mode.",
        "level": "safe"
    },
    {
        "category": "Network & IP",
        "name": "Disable Airplane Mode",
        "cmd": "cmd connectivity airplane-mode disable",
        "desc": "Switches off Airplane Mode.",
        "level": "safe"
    },
    {
        "category": "Network & IP",
        "name": "Show DNS Configuration",
        "cmd": "getprop | grep dns",
        "desc": "Displays active DNS resolver IP properties.",
        "level": "safe"
    },

    # =========================================================================
    # Category 6: Forensics & Clones
    # =========================================================================
    {
        "category": "Forensics & Clones",
        "name": "Raw Linux CPU Hardware",
        "cmd": "cat /proc/cpuinfo",
        "desc": "Reads raw kernel CPU hardware specs. Disproves spoofed Settings.",
        "level": "safe"
    },
    {
        "category": "Forensics & Clones",
        "name": "Raw Physical RAM Size",
        "cmd": "cat /proc/meminfo",
        "desc": "Reads actual physical memory in kB. Unmasks fake RAM modifications.",
        "level": "safe"
    },
    {
        "category": "Forensics & Clones",
        "name": "Storage Mounts & Capacities",
        "cmd": "df -h",
        "desc": "Displays true partition sizes in human-readable GB/MB.",
        "level": "safe"
    },
    {
        "category": "Forensics & Clones",
        "name": "Kernel Version & Compile Date",
        "cmd": "uname -a",
        "desc": "Inspects Linux kernel compile string, timestamp, and machine architecture.",
        "level": "safe"
    },
    {
        "category": "Forensics & Clones",
        "name": "Check SELinux Security Status",
        "cmd": "getenforce",
        "desc": "Queries SELinux enforcement (Enforcing, Permissive, Disabled).",
        "level": "safe"
    },
    {
        "category": "Forensics & Clones",
        "name": "List Block Partitions by Name",
        "cmd": "ls -la /dev/block/by-name/",
        "desc": "Lists hardware flash partitions (boot, recovery, system, vendor, userdata).",
        "level": "safe"
    },
    {
        "category": "Forensics & Clones",
        "name": "Firmware Release Keys vs Test-Keys",
        "cmd": "getprop ro.build.tags",
        "desc": "Reveals test-keys (indicates cloned or non-certified unofficial ROM).",
        "level": "safe"
    },
    {
        "category": "Forensics & Clones",
        "name": "Chipset & Platform Properties",
        "cmd": "getprop | grep -E \"ro.product|ro.board|ro.hardware|ro.chipname\"",
        "desc": "Queries true silicon board vendor and motherboard hardware identifier.",
        "level": "safe"
    },

    # =========================================================================
    # Category 7: Speed & Performance
    # =========================================================================
    {
        "category": "Speed & Performance",
        "name": "Trim App Caches Globally",
        "cmd": "pm trim-caches 9999999999999",
        "desc": "Reclaims unused cached files across all installed applications.",
        "level": "safe"
    },
    {
        "category": "Speed & Performance",
        "name": "Storage NAND TRIM (/data)",
        "cmd": "fstrim -v /data",
        "desc": "Sends TRIM command to flash storage to defragment deleted blocks.",
        "level": "safe"
    },
    {
        "category": "Speed & Performance",
        "name": "Clean /data/local/tmp",
        "cmd": "rm -rf /data/local/tmp/*",
        "desc": "Deletes leftover temp files, extracted APK artifacts, and orphan scripts.",
        "level": "safe"
    },
    {
        "category": "Speed & Performance",
        "name": "Speed Boost: 0.5x Animations",
        "cmd": "settings put global window_animation_scale 0.5; settings put global transition_animation_scale 0.5; settings put global animator_duration_scale 0.5",
        "desc": "Doubles interface transition speed for a snappy, fluid feel.",
        "level": "safe"
    },
    {
        "category": "Speed & Performance",
        "name": "Ultra Fast: 0x Animations",
        "cmd": "settings put global window_animation_scale 0; settings put global transition_animation_scale 0; settings put global animator_duration_scale 0",
        "desc": "Disables animations completely for instantaneous zero-latency app switches.",
        "level": "safe"
    },
    {
        "category": "Speed & Performance",
        "name": "Reset Animations to Default (1.0x)",
        "cmd": "settings put global window_animation_scale 1; settings put global transition_animation_scale 1; settings put global animator_duration_scale 1",
        "desc": "Restores standard OEM animation scales.",
        "level": "safe"
    },
    {
        "category": "Speed & Performance",
        "name": "Compile Apps with AOT Speed",
        "cmd": "cmd package compile -m speed -a",
        "desc": "Forces Android Runtime (ART) Ahead-Of-Time optimization across all apps.",
        "level": "safe"
    },
    {
        "category": "Speed & Performance",
        "name": "Clean Demo Mode (Status Bar)",
        "cmd": "settings put global sysui_demo_allowed 1; am broadcast -a com.android.systemui.demo -e command enter; am broadcast -a com.android.systemui.demo -e command clock -e hhmm 1000; am broadcast -a com.android.systemui.demo -e command battery -e level 100",
        "desc": "Cleans status bar for screenshots (10:00 AM, 100% battery, no clutter).",
        "level": "safe"
    },
    {
        "category": "Speed & Performance",
        "name": "Exit Clean Demo Mode",
        "cmd": "am broadcast -a com.android.systemui.demo -e command exit",
        "desc": "Exits demo mode and restores live status bar icons.",
        "level": "safe"
    },

    # =========================================================================
    # Category 8: Logs & Debugging
    # =========================================================================
    {
        "category": "Logs & Debugging",
        "name": "Dump Last 100 Logcat Lines",
        "cmd": "logcat -d -t 100",
        "desc": "Dumps the 100 most recent system events from buffer.",
        "level": "safe"
    },
    {
        "category": "Logs & Debugging",
        "name": "Filter Fatal Crashes (*:E)",
        "cmd": "logcat -d *:E",
        "desc": "Filters logs to display only critical error-level events and stack traces.",
        "level": "safe"
    },
    {
        "category": "Logs & Debugging",
        "name": "Kernel Ring Buffer (dmesg)",
        "cmd": "dmesg | tail -n 100",
        "desc": "Dumps recent low-level Linux kernel log messages and hardware events.",
        "level": "safe"
    },
    {
        "category": "Logs & Debugging",
        "name": "Dump DropBox App Crashes",
        "cmd": "dumpsys dropbox --print",
        "desc": "Prints tombstone crash logs and ANR (Application Not Responding) records.",
        "level": "safe"
    },
    {
        "category": "Logs & Debugging",
        "name": "Clear All Logcat Buffers",
        "cmd": "logcat -c",
        "desc": "Wipes log buffers to prepare for clean diagnostic capture.",
        "level": "safe"
    },

    # =========================================================================
    # Category 9: Storage & Recovery
    # =========================================================================
    {
        "category": "Storage & Recovery",
        "name": "List Top Disk Space Users",
        "cmd": "du -h -d 1 /sdcard/",
        "desc": "Lists directory sizes inside internal storage to locate large files.",
        "level": "safe"
    },
    {
        "category": "Storage & Recovery",
        "name": "Check DCIM Camera Photos Count",
        "cmd": "ls -1 /sdcard/DCIM/Camera | wc -l",
        "desc": "Counts number of captured photos in standard camera roll.",
        "level": "safe"
    },
    {
        "category": "Storage & Recovery",
        "name": "Check WhatsApp Media Storage",
        "cmd": "du -sh /sdcard/Android/media/com.whatsapp",
        "desc": "Calculates total size of WhatsApp chats and shared media.",
        "level": "safe"
    },
    {
        "category": "Storage & Recovery",
        "name": "Check Download Directory Files",
        "cmd": "ls -la /sdcard/Download",
        "desc": "Inspects recently downloaded files in user storage.",
        "level": "safe"
    }
]

def search_commands(query: str = "", category: str = "All Commands") -> List[Dict[str, str]]:
    """Filters commands by query and category."""
    q = query.strip().lower()
    results = []
    for c in VAST_COMMANDS:
        if category != "All Commands" and c["category"] != category:
            continue
        if q:
            match_name = q in c["name"].lower()
            match_cmd = q in c["cmd"].lower()
            match_desc = q in c["desc"].lower()
            if not (match_name or match_cmd or match_desc):
                continue
        results.append(c)
    return results
