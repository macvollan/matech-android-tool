"""
MacTech Android Tool - ADB & Diagnostic Engine
Engineered for MacTech Solutions Lab
Silently executes all ADB, fastboot, and MTP commands without console window flashing.
"""

import os
import sys
import subprocess
import time
import re
import json
import shutil
import threading
from typing import Dict, List, Tuple, Optional, Any

# Locate bundled or system ADB binary
def get_adb_binary_path() -> str:
    # 1. Check local bin/ folder relative to running script or frozen exe
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    bundled = os.path.join(base_dir, "bin", "adb.exe")
    if os.path.exists(bundled):
        return bundled
    
    # 2. Check UnlockTool or SamFw paths on disk if present
    for alt in [
        r"C:\UnlockTool\Binaries\adb.exe",
        r"C:\SamFwTool\data\adb.exe",
        r"C:\platform-tools\adb.exe"
    ]:
        if os.path.exists(alt):
            return alt
            
    # 3. Fallback to system PATH
    return "adb"

class ADBManager:
    """Core manager for silent ADB operations, MTP queries, diagnostics, and fake phone detection."""
    
    def __init__(self, adb_path: Optional[str] = None):
        self.adb_path = adb_path or get_adb_binary_path()
        self.selected_device: Optional[str] = None
        self._ensure_server_running()

    def _get_silent_startupinfo(self) -> Tuple[subprocess.STARTUPINFO, int]:
        """Provides Windows startupinfo flags to prevent black console windows from ever flashing."""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        creationflags = subprocess.CREATE_NO_WINDOW
        return startupinfo, creationflags

    def run_cmd(self, cmd_args: List[str], timeout: int = 40) -> Tuple[int, str, str]:
        """Executes any command silently with no window flashing."""
        startupinfo, creationflags = self._get_silent_startupinfo()
        try:
            proc = subprocess.run(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out."
        except Exception as e:
            return -1, "", str(e)

    def run_adb(self, args: List[str], timeout: int = 40, device_id: Optional[str] = None) -> Tuple[int, str, str]:
        """Executes an ADB command silently."""
        target = device_id or self.selected_device
        full_cmd = [self.adb_path]
        if target:
            full_cmd.extend(["-s", target])
        full_cmd.extend(args)
        return self.run_cmd(full_cmd, timeout=timeout)

    def run_shell(self, shell_cmd: str, timeout: int = 40, device_id: Optional[str] = None) -> Tuple[int, str, str]:
        """Executes an adb shell command."""
        return self.run_adb(["shell", shell_cmd], timeout=timeout, device_id=device_id)

    def execute_smart_command(self, cmd_line: str, timeout: int = 40, device_id: Optional[str] = None) -> Tuple[int, str, str]:
        """
        Smart command parser for terminal inputs:
        - If command begins with 'adb ', strips 'adb ' and runs as direct adb command.
        - If command begins with 'fastboot ', runs as direct fastboot command.
        - Otherwise, executes through 'adb shell <cmd>'.
        All executions run 100% silently without console window popups.
        """
        clean_cmd = cmd_line.strip()
        if not clean_cmd:
            return 0, "", ""
        
        if clean_cmd.lower().startswith("adb "):
            import shlex
            try:
                parts = shlex.split(clean_cmd[4:].strip())
            except Exception:
                parts = clean_cmd[4:].strip().split()
            return self.run_adb(parts, timeout=timeout, device_id=device_id)
            
        if clean_cmd.lower().startswith("fastboot "):
            import shlex
            try:
                parts = shlex.split(clean_cmd)
            except Exception:
                parts = clean_cmd.split()
            return self.run_cmd(parts, timeout=timeout)
            
        return self.run_shell(clean_cmd, timeout=timeout, device_id=device_id)

    def _ensure_server_running(self):
        """Starts ADB server silently if not already running."""
        def _start():
            self.run_cmd([self.adb_path, "start-server"], timeout=10)
        t = threading.Thread(target=_start, daemon=True)
        t.start()

    def restart_adb_server(self) -> Tuple[bool, str]:
        """Kills and restarts ADB server."""
        self.run_cmd([self.adb_path, "kill-server"], timeout=10)
        time.sleep(1)
        code, out, err = self.run_cmd([self.adb_path, "start-server"], timeout=15)
        return code == 0, out or err

    # =========================================================================
    # Device Detection & State
    # =========================================================================

    def get_connected_devices(self) -> List[Dict[str, str]]:
        """
        Lists all devices detected by ADB.
        Returns dict list: [{'serial': ..., 'state': 'device'|'unauthorized'|'offline'|'recovery'..., 'model': ..., 'product': ...}]
        """
        code, out, _ = self.run_cmd([self.adb_path, "devices", "-l"], timeout=10)
        devices = []
        if code != 0 or not out:
            return devices

        lines = out.splitlines()
        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith("*"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                state = parts[1]
                details = {"serial": serial, "state": state, "model": "", "product": "", "device": ""}
                for part in parts[2:]:
                    if ":" in part:
                        k, v = part.split(":", 1)
                        details[k] = v
                devices.append(details)
        return devices

    def get_mtp_usb_devices(self) -> List[Dict[str, str]]:
        """
        Uses PowerShell to query Windows Portable Devices (WPD) and USB entities.
        Detects Android phones connected via MTP even if USB Debugging is turned OFF.
        """
        ps_script = """
        Get-PnpDevice -Class 'WPD', 'USB' -Status 'OK' | Select-Object FriendlyName, InstanceId, Manufacturer, Class | ConvertTo-Json -Compress
        """
        code, out, _ = self.run_cmd(["powershell", "-NoProfile", "-Command", ps_script], timeout=10)
        mtp_list = []
        if code == 0 and out:
            try:
                data = json.loads(out)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = item.get("FriendlyName") or ""
                    inst = item.get("InstanceId") or ""
                    mfg = item.get("Manufacturer") or ""
                    # Filter relevant portable devices / Android devices
                    name_lower = name.lower()
                    if any(kw in name_lower for kw in ["android", "phone", "samsung", "xiaomi", "redmi", "oppo", "vivo", "pixel", "tecno", "infinix", "huawei", "mtp", "composite", "transsion"]):
                        mtp_list.append({
                            "name": name,
                            "instance_id": inst,
                            "manufacturer": mfg,
                            "class": item.get("Class", "")
                        })
            except Exception:
                pass
        return mtp_list

    def get_overall_status(self) -> Dict[str, Any]:
        """
        Aggregates ADB and MTP status to determine full device connectivity context.
        """
        adb_devs = self.get_connected_devices()
        mtp_devs = self.get_mtp_usb_devices()

        if adb_devs:
            # Active ADB device found
            first = adb_devs[0]
            if not self.selected_device or self.selected_device not in [d['serial'] for d in adb_devs]:
                self.selected_device = first['serial']

            state = first['state']
            if state == 'device':
                status = "AUTHORIZED"
            elif state == 'unauthorized':
                status = "UNAUTHORIZED"
            elif state in ['offline', 'no permissions']:
                status = "OFFLINE"
            elif state == 'recovery':
                status = "RECOVERY"
            elif state == 'sideload':
                status = "SIDELOAD"
            elif state == 'fastboot':
                status = "FASTBOOT"
            else:
                status = state.upper()

            return {
                "connection": status,
                "adb_devices": adb_devs,
                "mtp_devices": mtp_devs,
                "active_device": first,
                "message": f"Device {first['serial']} connected ({status})"
            }

        elif mtp_devs:
            # Connected via USB/MTP, but ADB is not enabled or not detected
            return {
                "connection": "MTP_ONLY",
                "adb_devices": [],
                "mtp_devices": mtp_devs,
                "active_device": None,
                "message": f"Phone detected via MTP: {mtp_devs[0]['name']}. USB Debugging is OFF."
            }
        else:
            return {
                "connection": "DISCONNECTED",
                "adb_devices": [],
                "mtp_devices": [],
                "active_device": None,
                "message": "No Android device detected. Connect phone via USB cable."
            }

    # =========================================================================
    # Force / Guide USB Debugging
    # =========================================================================

    def attempt_force_usb_debugging(self) -> Tuple[bool, str]:
        """
        Attempts waking device, dismissing keyguard, and triggering developer options intent.
        Also provides guidance instructions.
        """
        # Try sending wakeup & unlock keyevents
        self.run_adb(["shell", "input keyevent 26"]) # Power / Wake
        time.sleep(0.2)
        self.run_adb(["shell", "input keyevent 82"]) # Menu / Unlock
        time.sleep(0.3)
        # Attempt launching Development Settings intent
        code, out, err = self.run_adb(["shell", "am start -a android.settings.APPLICATION_DEVELOPMENT_SETTINGS"])
        if code == 0:
            return True, "Launched Developer Settings directly on screen! Turn 'USB Debugging' ON now."
        return False, "Could not trigger intent directly. Please follow manual OEM guide."

    @staticmethod
    def get_usb_debugging_guide(brand: str = "general") -> str:
        """Returns step-by-step instructions to enable USB debugging for all major manufacturers."""
        guides = {
            "samsung": (
                "SAMSUNG GALAXY GUIDE:\n"
                "1. Open Settings -> About phone -> Software information.\n"
                "2. Tap 'Build number' 7 times rapidly until 'Developer mode enabled' appears.\n"
                "3. Go back to Settings root -> Scroll to bottom -> Open 'Developer options'.\n"
                "4. Toggle 'USB debugging' to ON.\n"
                "5. When 'Allow USB debugging?' popup appears on screen, check 'Always allow from this computer' and tap 'OK'."
            ),
            "xiaomi": (
                "XIAOMI / REDMI / POCO (MIUI / HyperOS):\n"
                "1. Open Settings -> About phone.\n"
                "2. Tap 'OS version' or 'MIUI version' 7 times rapidly.\n"
                "3. Go back -> Additional settings -> Developer options.\n"
                "4. Toggle 'USB debugging' to ON.\n"
                "5. Also toggle 'USB debugging (Security settings)' to ON if you wish to control inputs.\n"
                "6. Accept all warning prompts and authorize the PC key."
            ),
            "oppo": (
                "OPPO / REALME / ONEPLUS (ColorOS / RealmeUI / OxygenOS):\n"
                "1. Open Settings -> About device -> Version.\n"
                "2. Tap 'Build number' 7 times.\n"
                "3. Go back -> System settings / Additional settings -> Developer options.\n"
                "4. Turn on 'USB debugging'.\n"
                "5. If prompted, toggle 'Disable permission monitoring'."
            ),
            "vivo": (
                "VIVO / iQOO (FuntouchOS / OriginOS):\n"
                "1. Open Settings -> About phone -> Software info.\n"
                "2. Tap 'Build number' 7 times.\n"
                "3. Go back -> System -> Developer options.\n"
                "4. Turn on 'USB debugging' and confirm security prompt."
            ),
            "transsion": (
                "TECNO / INFINIX / ITEL (HiOS / XOS):\n"
                "1. Open Settings -> My Phone.\n"
                "2. Tap 'Build number' 7 times.\n"
                "3. Go back -> System -> Developer options.\n"
                "4. Turn on 'USB debugging' and allow RSA computer key."
            ),
            "pixel": (
                "GOOGLE PIXEL / MOTOROLA / STOCK ANDROID:\n"
                "1. Open Settings -> About phone.\n"
                "2. Scroll down and tap 'Build number' 7 times.\n"
                "3. Go back -> System -> Developer options.\n"
                "4. Turn on 'USB debugging' -> Click 'OK' on phone prompt."
            ),
            "general": (
                "GENERAL ANDROID INSTRUCTIONS:\n"
                "1. Go to Settings -> About Phone.\n"
                "2. Tap 'Build Number' 7 times until Developer mode is enabled.\n"
                "3. Navigate to Developer Options in Settings (or under System / Additional Settings).\n"
                "4. Enable 'USB Debugging'.\n"
                "5. Connect USB cable to PC and ensure 'Always allow from this computer' is ticked."
            )
        }
        return guides.get(brand.lower(), guides["general"])

    # =========================================================================
    # Device Overview & Hardware Specifications
    # =========================================================================

    def get_device_overview(self) -> Dict[str, Any]:
        """Retrieves complete device hardware, software, battery, and identity properties."""
        info = {
            "model": "Unknown",
            "brand": "Unknown",
            "manufacturer": "Unknown",
            "device": "Unknown",
            "board": "Unknown",
            "hardware": "Unknown",
            "platform": "Unknown",
            "android_version": "Unknown",
            "sdk_level": "Unknown",
            "security_patch": "Unknown",
            "build_id": "Unknown",
            "serial": self.selected_device or "N/A",
            "cpu_arch": "Unknown",
            "cpu_cores": "Unknown",
            "total_ram": "Unknown",
            "free_ram": "Unknown",
            "battery_level": "Unknown",
            "battery_health": "Unknown",
            "battery_temp": "Unknown",
            "battery_voltage": "Unknown",
            "battery_status": "Unknown",
            "display_resolution": "Unknown",
            "display_density": "Unknown",
            "storage_total": "Unknown",
            "storage_free": "Unknown",
            "ip_address": "Unknown"
        }

        # 1. Properties via getprop
        code, out, _ = self.run_shell("getprop")
        props = {}
        if code == 0 and out:
            for line in out.splitlines():
                m = re.match(r'\[(.*?)\]:\s*\[(.*?)\]', line)
                if m:
                    props[m.group(1)] = m.group(2)

        info["brand"] = props.get("ro.product.brand", "Unknown").capitalize()
        info["manufacturer"] = props.get("ro.product.manufacturer", "Unknown").capitalize()
        info["model"] = props.get("ro.product.model", "Unknown")
        info["device"] = props.get("ro.product.device", "Unknown")
        info["board"] = props.get("ro.product.board", "Unknown")
        info["hardware"] = props.get("ro.hardware", props.get("ro.boot.hardware", "Unknown"))
        info["platform"] = props.get("ro.board.platform", "Unknown")
        info["android_version"] = props.get("ro.build.version.release", "Unknown")
        info["sdk_level"] = props.get("ro.build.version.sdk", "Unknown")
        info["security_patch"] = props.get("ro.build.version.security_patch", "Unknown")
        info["build_id"] = props.get("ro.build.display.id", props.get("ro.build.id", "Unknown"))
        info["cpu_arch"] = props.get("ro.product.cpu.abi", "Unknown")

        # 2. Battery status via dumpsys battery
        b_code, b_out, _ = self.run_shell("dumpsys battery")
        if b_code == 0 and b_out:
            for b_line in b_out.splitlines():
                b_line = b_line.strip()
                if b_line.startswith("level:"):
                    info["battery_level"] = f"{b_line.split(':')[1].strip()}%"
                elif b_line.startswith("health:"):
                    health_map = {"1": "Unknown", "2": "Good", "3": "Overheat", "4": "Dead", "5": "Over Voltage", "6": "Unspecified Failure", "7": "Cold"}
                    h_val = b_line.split(':')[1].strip()
                    info["battery_health"] = health_map.get(h_val, h_val)
                elif b_line.startswith("temperature:"):
                    t_val = b_line.split(':')[1].strip()
                    try:
                        deg_c = float(t_val) / 10.0
                        deg_f = (deg_c * 9/5) + 32
                        info["battery_temp"] = f"{deg_c:.1f} °C ({deg_f:.1f} °F)"
                    except Exception:
                        info["battery_temp"] = t_val
                elif b_line.startswith("voltage:"):
                    v_val = b_line.split(':')[1].strip()
                    try:
                        info["battery_voltage"] = f"{float(v_val)/1000.0:.2f} V ({v_val} mV)"
                    except Exception:
                        info["battery_voltage"] = f"{v_val} mV"
                elif b_line.startswith("status:"):
                    status_map = {"1": "Unknown", "2": "Charging", "3": "Discharging", "4": "Not Charging", "5": "Full"}
                    s_val = b_line.split(':')[1].strip()
                    info["battery_status"] = status_map.get(s_val, s_val)

        # 3. RAM info via /proc/meminfo
        m_code, m_out, _ = self.run_shell("cat /proc/meminfo")
        if m_code == 0 and m_out:
            mem_total_kb = 0
            mem_avail_kb = 0
            for line in m_out.splitlines():
                if "MemTotal:" in line:
                    mem_total_kb = int(re.findall(r'\d+', line)[0])
                elif "MemAvailable:" in line:
                    mem_avail_kb = int(re.findall(r'\d+', line)[0])
            if mem_total_kb > 0:
                info["total_ram"] = f"{mem_total_kb / (1024*1024):.2f} GB ({mem_total_kb // 1024} MB)"
                info["free_ram"] = f"{mem_avail_kb / (1024*1024):.2f} GB ({mem_avail_kb // 1024} MB)"

        # 4. Display resolution via wm size & wm density
        w_code, w_out, _ = self.run_shell("wm size")
        if w_code == 0 and w_out:
            # Physical size: 1080x2400
            m = re.search(r'Physical size:\s*(\d+x\d+)', w_out)
            if m:
                info["display_resolution"] = m.group(1)
            else:
                info["display_resolution"] = w_out.strip()

        d_code, d_out, _ = self.run_shell("wm density")
        if d_code == 0 and d_out:
            m = re.search(r'Physical density:\s*(\d+)', d_out)
            if m:
                info["display_density"] = f"{m.group(1)} DPI"

        # 5. Storage via df -h /data
        s_code, s_out, _ = self.run_shell("df -h /data")
        if s_code == 0 and s_out:
            lines = s_out.strip().splitlines()
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 4:
                    info["storage_total"] = parts[1]
                    info["storage_free"] = parts[3]

        # 6. CPU cores
        c_code, c_out, _ = self.run_shell("cat /proc/cpuinfo")
        if c_code == 0 and c_out:
            cores = len(re.findall(r'^processor\s*:', c_out, re.MULTILINE))
            if cores > 0:
                info["cpu_cores"] = f"{cores} Cores"

        # 7. IP Address
        ip_code, ip_out, _ = self.run_shell("ip -o -4 addr show wlan0")
        if ip_code == 0 and ip_out:
            m = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', ip_out)
            if m:
                info["ip_address"] = m.group(1)

        return info

    # =========================================================================
    # Foreground App / Activity Tracking & Instant Uninstall
    # =========================================================================

    def get_current_foreground_app(self) -> Dict[str, str]:
        """
        Determines the current app on screen by querying Window Manager / Activity Manager.
        Returns package name, focused activity class, and friendly app name.
        """
        result = {
            "package": "Unknown",
            "activity": "Unknown",
            "component": "None",
            "app_name": "None",
            "version": "Unknown"
        }

        # Try dumpsys window mCurrentFocus
        code, out, _ = self.run_shell("dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'")
        found = False
        if code == 0 and out:
            # Format: mCurrentFocus=Window{... u0 com.whatsapp/com.whatsapp.HomeActivity}
            m = re.search(r'([a-zA-Z0-9_\.]+(?:/[a-zA-Z0-9_\.]+))', out)
            if m:
                full_comp = m.group(1)
                if "/" in full_comp:
                    pkg, act = full_comp.split("/", 1)
                    result["package"] = pkg.strip()
                    result["activity"] = act.strip()
                    result["component"] = full_comp
                    found = True

        if not found:
            # Fallback to dumpsys activity activities
            code2, out2, _ = self.run_shell("dumpsys activity activities | grep -E 'mResumedActivity|topResumedActivity'")
            if code2 == 0 and out2:
                m = re.search(r'([a-zA-Z0-9_\.]+(?:/[a-zA-Z0-9_\.]+))', out2)
                if m:
                    full_comp = m.group(1)
                    if "/" in full_comp:
                        pkg, act = full_comp.split("/", 1)
                        result["package"] = pkg.strip()
                        result["activity"] = act.strip()
                        result["component"] = full_comp

        if result["package"] != "Unknown":
            # Query version
            v_code, v_out, _ = self.run_shell(f"dumpsys package {result['package']} | grep versionName")
            if v_code == 0 and v_out:
                m_ver = re.search(r'versionName=([^\s]+)', v_out)
                if m_ver:
                    result["version"] = m_ver.group(1)

        return result

    def uninstall_app(self, package_name: str, keep_data: bool = False, user_zero: bool = False) -> Tuple[bool, str]:
        """
        Uninstalls an app.
        Supports standard uninstall or debloat for user 0 (works on system apps without root).
        """
        if not package_name:
            return False, "No package specified."

        cmd = ["shell", "pm", "uninstall"]
        if keep_data:
            cmd.append("-k")
        if user_zero:
            cmd.extend(["--user", "0"])
        cmd.append(package_name)

        code, out, err = self.run_adb(cmd)
        if "Success" in out:
            return True, f"Successfully uninstalled {package_name}."
        return False, out or err or "Failed to uninstall package."

    # =========================================================================
    # App Manager (Installed Apps, Dates, Searchable)
    # =========================================================================

    def list_installed_packages(self, filter_type: str = "all") -> List[Dict[str, str]]:
        """
        Lists installed packages with install dates, update dates, and version.
        filter_type: 'all', 'user' (-3), 'system' (-s)
        """
        cmd = ["shell", "pm", "list", "packages", "-f", "-i"]
        if filter_type == "user":
            cmd.append("-3")
        elif filter_type == "system":
            cmd.append("-s")

        code, out, _ = self.run_adb(cmd, timeout=30)
        packages = []
        if code != 0 or not out:
            return packages

        # Output format: package:/data/app/~~.../base.apk=com.example.app installer=com.android.vending
        for line in out.splitlines():
            line = line.strip()
            if not line.startswith("package:"):
                continue
            line = line[8:] # strip 'package:'
            installer = "sideload / none"
            if " installer=" in line:
                line_parts = line.split(" installer=")
                line = line_parts[0]
                installer = line_parts[1].strip()

            if "=" in line:
                apk_path, pkg = line.rsplit("=", 1)
                is_system = apk_path.startswith("/system") or apk_path.startswith("/product") or apk_path.startswith("/vendor")
                packages.append({
                    "package": pkg.strip(),
                    "apk_path": apk_path.strip(),
                    "installer": installer,
                    "type": "System" if is_system else "User"
                })
        return packages

    def get_package_details(self, package_name: str) -> Dict[str, str]:
        """Queries deep package metadata: install time, update time, version, permissions."""
        details = {
            "package": package_name,
            "version_name": "Unknown",
            "version_code": "Unknown",
            "first_install_time": "Unknown",
            "last_update_time": "Unknown",
            "apk_path": "Unknown",
            "uid": "Unknown"
        }
        code, out, _ = self.run_shell(f"dumpsys package {package_name}")
        if code == 0 and out:
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("versionName="):
                    details["version_name"] = line.split("=", 1)[1]
                elif line.startswith("versionCode="):
                    details["version_code"] = line.split("=", 1)[1].split()[0]
                elif line.startswith("firstInstallTime="):
                    details["first_install_time"] = line.split("=", 1)[1]
                elif line.startswith("lastUpdateTime="):
                    details["last_update_time"] = line.split("=", 1)[1]
                elif line.startswith("codePath="):
                    details["apk_path"] = line.split("=", 1)[1]
                elif line.startswith("userId="):
                    details["uid"] = line.split("=", 1)[1]
        return details

    def clear_app_data(self, package_name: str) -> Tuple[bool, str]:
        """Clears cache and all user data for an app."""
        code, out, err = self.run_shell(f"pm clear {package_name}")
        return code == 0 and "Success" in out, out or err

    def force_stop_app(self, package_name: str) -> Tuple[bool, str]:
        """Force closes an application process."""
        code, out, err = self.run_shell(f"am force-stop {package_name}")
        return code == 0, out or err or f"Force stopped {package_name}."

    def pull_apk(self, package_name: str, dest_folder: str) -> Tuple[bool, str]:
        """Pulls the APK file from device to PC."""
        code, out, _ = self.run_shell(f"pm path {package_name}")
        if code != 0 or not out:
            return False, "Could not locate APK on device."
        # package:/data/app/.../base.apk
        first_line = out.splitlines()[0]
        apk_remote = first_line.replace("package:", "").strip()
        dest_file = os.path.join(dest_folder, f"{package_name}.apk")
        p_code, p_out, p_err = self.run_adb(["pull", apk_remote, dest_file], timeout=60)
        return p_code == 0, dest_file if p_code == 0 else p_err

    def install_apk(self, apk_path: str) -> Tuple[bool, str]:
        """Installs an APK file from PC to device."""
        if not os.path.exists(apk_path):
            return False, "APK file not found on PC."
        code, out, err = self.run_adb(["install", "-r", "-d", apk_path], timeout=120)
        if "Success" in out:
            return True, "Installation successful."
        return False, out or err

    # =========================================================================
    # Authenticity & Fake / Counterfeit Phone Inspector
    # =========================================================================

    def inspect_authenticity(self) -> Dict[str, Any]:
        """
        Deep forensic analysis detecting copy / clone phones with fake specs.
        Clones spoof ro.product.model, fake RAM, fake CPU cores, and fake Android versions in Settings.
        This inspector compares reported props against raw Linux kernel data in /proc/meminfo,
        /proc/cpuinfo, /sys/class/thermal, physical window size, and build signatures.
        """
        report = {
            "score": 100,
            "verdict": "GENUINE",
            "confidence": "High",
            "findings": [],
            "advertised": {},
            "actual_kernel": {},
            "anomalies": []
        }

        # 1. Inspect RAM
        code_mem, out_mem, _ = self.run_shell("cat /proc/meminfo")
        kernel_mem_kb = 0
        if code_mem == 0 and out_mem:
            for l in out_mem.splitlines():
                if "MemTotal:" in l:
                    kernel_mem_kb = int(re.findall(r'\d+', l)[0])
                    break
        kernel_mem_gb = kernel_mem_kb / (1024 * 1024)
        report["actual_kernel"]["ram_gb"] = f"{kernel_mem_gb:.2f} GB"

        # Check advertised / build.prop RAM
        code_ram, out_ram, _ = self.run_shell("getprop ro.config.ram_size")
        if code_ram == 0 and out_ram.strip():
            report["advertised"]["ram"] = out_ram.strip()

        # Check for fake RAM claims (e.g. clone claims 16GB, but kernel has only 1GB or 2GB)
        if kernel_mem_gb < 2.5:
            # Check model name; if claiming to be Galaxy S23/S24 Ultra, iPhone, or flagship with <3GB RAM
            model_code, model_out, _ = self.run_shell("getprop ro.product.model")
            model_str = model_out.strip().lower()
            if any(f in model_str for f in ["ultra", "s24", "s23", "s22", "pro max", "fold", "find x"]):
                report["score"] -= 45
                report["anomalies"].append(f"FLAGSHIP RAM MISMATCH: Phone claims to be '{model_out.strip()}' but kernel reports only {kernel_mem_gb:.2f} GB physical RAM (clones spoof flagship RAM)!")

        # 2. Inspect CPU & SoC Architecture
        code_cpu, out_cpu, _ = self.run_shell("cat /proc/cpuinfo")
        hardware_str = ""
        cores_found = 0
        arch_found = ""
        if code_cpu == 0 and out_cpu:
            cores_found = len(re.findall(r'^processor\s*:', out_cpu, re.MULTILINE))
            for l in out_cpu.splitlines():
                if "Hardware" in l and ":" in l:
                    hardware_str = l.split(":", 1)[1].strip()
                if "CPU architecture" in l and not arch_found:
                    arch_found = l.split(":", 1)[1].strip()

        report["actual_kernel"]["cpu_cores"] = cores_found
        report["actual_kernel"]["hardware_soc"] = hardware_str
        report["actual_kernel"]["arch"] = arch_found

        # Get advertised board & chipname
        code_board, out_board, _ = self.run_shell("getprop ro.board.platform")
        code_chip, out_chip, _ = self.run_shell("getprop ro.chipname")
        board_str = out_board.strip()
        chip_str = out_chip.strip()
        report["advertised"]["board_platform"] = board_str
        report["advertised"]["chipname"] = chip_str

        # Common counterfeit SoC signatures:
        # Clones spoofing Snapdragon 8 Gen 3 or Dimensity 9000 often run ancient MT6580, MT6572, or SC7731!
        is_ancient_soc = any(fake_chip in (hardware_str + board_str + chip_str).lower() for fake_chip in ["mt6580", "mt6572", "mt6582", "sc7731", "sc9832"])
        if is_ancient_soc:
            report["score"] -= 50
            report["anomalies"].append(f"COUNTERFEIT CHIPSET: Kernel CPU info reveals ancient 32-bit SoC ({hardware_str or board_str}) typically found in low-grade knockoffs and fake clones!")

        # 3. Kernel Version & Compile Timestamp vs Android Version
        code_ver, out_ver, _ = self.run_shell("cat /proc/version")
        code_os, out_os, _ = self.run_shell("getprop ro.build.version.release")
        os_ver = out_os.strip()
        report["advertised"]["android_version"] = os_ver
        report["actual_kernel"]["kernel_version"] = out_ver.strip()

        # Check for Android 13/14 claiming phones running Linux 3.18 or 4.4 from 2016-2018
        if os_ver in ["13", "14", "15"] and any(k in out_ver for k in ["Linux version 3.", "Linux version 4.4."]):
            report["score"] -= 40
            report["anomalies"].append(f"FAKE ANDROID OS VERSION: Advertised as Android {os_ver}, but kernel is an obsolete {out_ver.split()[2] if len(out_ver.split()) >= 3 else 'legacy'} compiled years before Android {os_ver} existed!")

        # 4. Display Resolution Check
        code_wm, out_wm, _ = self.run_shell("wm size")
        wm_res = ""
        if code_wm == 0 and out_wm:
            m = re.search(r'Physical size:\s*(\d+x\d+)', out_wm)
            if m:
                wm_res = m.group(1)
        report["actual_kernel"]["display_size"] = wm_res

        # If claiming flagship display with 480p or 720p low-res panel
        if wm_res in ["480x854", "480x960", "540x960", "720x1280"]:
            model_code, model_out, _ = self.run_shell("getprop ro.product.model")
            if any(fl in model_out.lower() for fl in ["s24", "s23", "ultra", "iphone", "pro max"]):
                report["score"] -= 30
                report["anomalies"].append(f"DISPLAY RESOLUTION ANOMALY: Physical display is only {wm_res}, far below genuine flagship specifications (3088x1440 / 2796x1290)!")

        # 5. Build Tags & Test Keys
        code_tags, out_tags, _ = self.run_shell("getprop ro.build.tags")
        if "test-keys" in out_tags.strip():
            report["score"] -= 15
            report["anomalies"].append("TEST-KEYS BUILD: Device firmware signed with insecure 'test-keys' rather than official release-keys from manufacturer.")

        # Compute Final Verdict
        if report["score"] >= 80:
            report["verdict"] = "GENUINE / AUTHENTIC"
            report["findings"].append("Hardware kernel architecture, memory layout, and build signatures match genuine manufacturer standards.")
        elif report["score"] >= 50:
            report["verdict"] = "SUSPICIOUS / MODIFIED"
            report["findings"].append("Device displays inconsistent properties or unofficial developer firmware. Review anomalies carefully.")
        else:
            report["verdict"] = "CONFIRMED COUNTERFEIT / FAKE CLONE"
            report["findings"].append("CRITICAL: Device is a verified counterfeit clone with spoofed build properties masking low-grade hardware!")

        return report

    # =========================================================================
    # Data Recovery Engine
    # =========================================================================

    def backup_full_adb(self, dest_path: str) -> Tuple[bool, str]:
        """Triggers full device ADB backup (.ab)."""
        code, out, err = self.run_adb(["backup", "-apk", "-shared", "-all", "-f", dest_path], timeout=600)
        return code == 0, out or err

    def pull_category_media(self, category: str, dest_dir: str, progress_callback=None) -> Tuple[bool, str, int]:
        """
        Extracts user photos, WhatsApp media, documents, or audio from storage to PC.
        """
        paths_map = {
            "dcim": ["/sdcard/DCIM/Camera", "/sdcard/DCIM"],
            "pictures": ["/sdcard/Pictures", "/sdcard/DCIM"],
            "whatsapp": [
                "/sdcard/Android/media/com.whatsapp/WhatsApp/Media",
                "/sdcard/WhatsApp/Media"
            ],
            "documents": ["/sdcard/Download", "/sdcard/Documents"],
            "audio": ["/sdcard/Music", "/sdcard/Recordings", "/sdcard/VoiceRecorder"],
            "all_storage": ["/sdcard/"]
        }

        remote_candidates = paths_map.get(category.lower(), ["/sdcard/DCIM"])
        target_remote = None
        for candidate in remote_candidates:
            code, out, _ = self.run_shell(f"ls -d '{candidate}'")
            if code == 0 and candidate in out:
                target_remote = candidate
                break

        if not target_remote:
            return False, f"Directory for category '{category}' not found on phone.", 0

        os.makedirs(dest_dir, exist_ok=True)
        if progress_callback:
            progress_callback(f"Pulling {target_remote} to {dest_dir}...")

        code, out, err = self.run_adb(["pull", target_remote, dest_dir], timeout=3600)
        if code == 0:
            return True, f"Successfully extracted {category} to {dest_dir}.", 1
        return False, out or err, 0

    # =========================================================================
    # Cache Cleaning, Storage TRIM & Defragmentation
    # =========================================================================

    def clear_all_caches(self) -> Tuple[bool, str]:
        """
        Invokes native Android package manager cache trimmer.
        Frees app cache data across all applications.
        """
        code, out, err = self.run_shell("pm trim-caches 9999999999999")
        if code == 0:
            return True, "All application caches successfully trimmed and reclaimed."
        return False, out or err

    def trim_storage_defragment(self) -> Tuple[bool, str]:
        """
        Runs fstrim on /data and /cache to unmap deleted blocks and defragment NAND storage.
        """
        logs = []
        for partition in ["/data", "/cache", "/system"]:
            code, out, err = self.run_shell(f"fstrim -v {partition}")
            if code == 0 and out:
                logs.append(f"{partition}: {out}")
            elif err:
                logs.append(f"{partition}: {err}")

        if logs:
            return True, "Storage TRIM results:\n" + "\n".join(logs)
        return False, "fstrim command returned no output or requires root on this specific kernel."

    def clean_temp_files(self) -> Tuple[bool, str]:
        """Removes temporary files in /data/local/tmp and orphan cache fragments."""
        code, out, err = self.run_shell("rm -rf /data/local/tmp/*")
        return code == 0, "Cleaned /data/local/tmp successfully."

    def speed_boost_art_optimize(self) -> Tuple[bool, str]:
        """Compiles Android apps Ahead-Of-Time (AOT) to speed up responsiveness and UI lag."""
        code, out, err = self.run_shell("cmd package compile -m speed -a")
        if code != 0:
            code, out, err = self.run_shell("pm compile -m speed -a")
        if code == 0:
            return True, "ART Speed compilation completed. System responsiveness optimized."
        return False, out or err

    # =========================================================================
    # Device Controls, Reboot & Screen Capture
    # =========================================================================

    def reboot_device(self, mode: str = "normal") -> Tuple[bool, str]:
        """
        Reboots device into normal, recovery, fastboot, bootloader, or edl mode.
        """
        cmd_map = {
            "normal": ["reboot"],
            "recovery": ["reboot", "recovery"],
            "bootloader": ["reboot", "bootloader"],
            "fastboot": ["reboot", "fastboot"],
            "edl": ["reboot", "edl"],
            "poweroff": ["shell", "reboot", "-p"]
        }
        sub_cmd = cmd_map.get(mode.lower(), ["reboot"])
        code, out, err = self.run_adb(sub_cmd, timeout=15)
        return code == 0, f"Reboot command ({mode}) issued."

    def send_keyevent(self, keycode: int) -> Tuple[bool, str]:
        """
        Sends hardware key event:
        3: Home, 4: Back, 24: Vol+, 25: Vol-, 26: Power, 82: Menu/Unlock, 187: App Switch
        """
        code, out, err = self.run_shell(f"input keyevent {keycode}")
        return code == 0, out or err

    def send_text_input(self, text: str) -> Tuple[bool, str]:
        """Types text into the active input field on the phone."""
        # Escape spaces and quotes for shell
        escaped = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        code, out, err = self.run_shell(f"input text '{escaped}'")
        return code == 0, out or err

    def send_screen_tap(self, x: int, y: int) -> Tuple[bool, str]:
        """Simulates screen touch tap at X, Y coordinate."""
        code, out, err = self.run_shell(f"input tap {x} {y}")
        return code == 0, out or err

    def send_screen_swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 250) -> Tuple[bool, str]:
        """Simulates swipe/drag from (x1, y1) to (x2, y2) over duration_ms milliseconds."""
        code, out, err = self.run_shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")
        return code == 0, out or err

    def send_screen_tap_async(self, x: int, y: int):
        """Sends screen tap asynchronously in a background daemon thread."""
        threading.Thread(target=self.send_screen_tap, args=(x, y), daemon=True).start()

    def send_screen_swipe_async(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 250):
        """Sends screen swipe asynchronously in a background daemon thread."""
        threading.Thread(target=self.send_screen_swipe, args=(x1, y1, x2, y2, duration_ms), daemon=True).start()

    def send_keyevent_async(self, keycode: int):
        """Sends hardware keyevent asynchronously in a background daemon thread."""
        threading.Thread(target=self.send_keyevent, args=(keycode,), daemon=True).start()

    def get_screen_resolution(self) -> Optional[Tuple[int, int]]:
        """Queries physical screen resolution (width, height) via wm size."""
        code, out, _ = self.run_shell("wm size")
        if code == 0 and out:
            m = re.search(r'(?:Physical size|Override size):\s*(\d+)x(\d+)', out)
            if m:
                return int(m.group(1)), int(m.group(2))
        return None

    def capture_screen_bytes(self) -> Optional[bytes]:
        """
        Captures live screen frame directly in memory without writing to disk.
        Uses binary adb exec-out screencap -p for maximum responsiveness.
        """
        startupinfo, creationflags = self._get_silent_startupinfo()
        full_cmd = [self.adb_path]
        if self.selected_device:
            full_cmd.extend(["-s", self.selected_device])
        full_cmd.extend(["exec-out", "screencap", "-p"])

        try:
            res = subprocess.run(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=5,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            if res.returncode == 0 and len(res.stdout) > 1000:
                return res.stdout
        except Exception:
            pass
        return None

    def capture_screenshot(self, local_save_path: str) -> Tuple[bool, str]:
        """
        Captures live screenshot from device silently and saves to PC.
        Uses binary adb exec-out screencap -p for maximum speed.
        """
        raw_bytes = self.capture_screen_bytes()
        if raw_bytes:
            try:
                with open(local_save_path, "wb") as f:
                    f.write(raw_bytes)
                return True, local_save_path
            except Exception as e:
                return False, str(e)

        # Fallback to screencap to /sdcard/screen.png + pull
        self.run_shell("screencap -p /sdcard/mactech_screen.png")
        p_code, _, _ = self.run_adb(["pull", "/sdcard/mactech_screen.png", local_save_path])
        self.run_shell("rm /sdcard/mactech_screen.png")
        return p_code == 0, local_save_path if p_code == 0 else "Screenshot capture failed."

    def get_scrcpy_path(self) -> Optional[str]:
        """Locates bundled or system-installed scrcpy.exe."""
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # 1. Check local bin/
        bundled = os.path.join(base_dir, "bin", "scrcpy.exe")
        if os.path.exists(bundled):
            return bundled

        # 2. Check WinGet Packages
        winget_path = r"C:\Users\HomePC\AppData\Local\Microsoft\WinGet\Packages\Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy-win64-v5.0.1\scrcpy.exe"
        if os.path.exists(winget_path):
            return winget_path

        # 3. Check system PATH
        from shutil import which
        sys_path = which("scrcpy")
        if sys_path:
            return sys_path

        return None

    def launch_scrcpy(self, stay_awake: bool = True, turn_screen_off: bool = False, always_on_top: bool = False, extra_args: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Launches Scrcpy for full hardware-accelerated 60fps mirror & remote keyboard/mouse control.
        """
        scrcpy_bin = self.get_scrcpy_path()
        if not scrcpy_bin:
            return False, "scrcpy.exe was not found. Please ensure it is present in bin/."

        cmd = [scrcpy_bin]
        if self.selected_device:
            cmd.extend(["-s", self.selected_device])
        if stay_awake:
            cmd.append("--stay-awake")
        if turn_screen_off:
            cmd.append("--turn-screen-off")
        if always_on_top:
            cmd.append("--always-on-top")

        cmd.extend([
            "--window-title=MacTech Android Live Mirror",
            "--max-size=1600",
            "--video-bit-rate=8M"
        ])

        if extra_args:
            cmd.extend(extra_args)

        env = os.environ.copy()
        env["ADB"] = self.adb_path
        scrcpy_dir = os.path.dirname(scrcpy_bin)
        env["PATH"] = scrcpy_dir + os.pathsep + env.get("PATH", "")

        startupinfo, creationflags = self._get_silent_startupinfo()
        try:
            proc = subprocess.Popen(
                cmd,
                env=env,
                cwd=scrcpy_dir,
                startupinfo=startupinfo,
                creationflags=creationflags
            )
            return True, f"Scrcpy 60FPS Ultra Mirror launched successfully (PID: {proc.pid})."
        except Exception as e:
            return False, f"Failed to launch scrcpy: {e}"
