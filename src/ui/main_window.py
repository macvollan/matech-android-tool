"""
MacTech Android Tool - Main Window
MacTech Solutions Lab
Modern, high-performance, dark forensic interface using CustomTkinter
"""

import os
import sys
import io
import webbrowser
import threading
import time
from typing import Optional, List, Dict, Any, Tuple
from tkinter import filedialog, messagebox
import tkinter as tk

try:
    import customtkinter as ctk
    from PIL import Image, ImageTk
except ImportError:
    ctk = None

from ..core.adb_manager import ADBManager
from ..core.command_library import COMMAND_CATEGORIES, VAST_COMMANDS, search_commands
from .theme import THEME

PAYPAL_DONATION_BASE_URL = "https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=markvollanbarracks@gmail.com&currency_code=USD&item_name=Support+MacTech+Android+Tool+Development"
DEFAULT_DONATION_AMOUNT = "3.00"
PAYPAL_DONATION_URL = f"{PAYPAL_DONATION_BASE_URL}&amount={DEFAULT_DONATION_AMOUNT}"
PAYPAL_EMAIL = "markvollanbarracks@gmail.com"

class MainWindow(ctk.CTk if ctk else object):
    def __init__(self, adb_manager: Optional[ADBManager] = None):
        if not ctk:
            raise RuntimeError("customtkinter is required to launch the GUI.")
        
        super().__init__()
        self.adb = adb_manager or ADBManager()

        # Window setup
        self.title("MacTech Android Tool v2.2 - Enterprise Forensic & Diagnostic Suite")
        self.geometry("1240x820")
        self.minsize(1080, 720)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=THEME["bg_main"])

        # Set window icon
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        ico_path = os.path.join(base_dir, "assets", "icon.ico")
        if os.path.exists(ico_path):
            try:
                self.iconbitmap(ico_path)
            except Exception:
                pass

        # State variables
        self.current_view_name = "dashboard"
        self.is_monitoring = True
        self.installed_packages_cache: List[Dict[str, str]] = []
        self.cached_overview: Dict[str, Any] = {}
        self.status_data: Dict[str, Any] = {"connection": "DISCONNECTED", "message": "Initializing..."}

        # Terminal state & command history
        self.command_history: List[str] = []
        self.history_index: int = -1
        self.current_cmd_category: str = "All Commands"
        self.selected_donation_amount: str = DEFAULT_DONATION_AMOUNT

        # Live screen streaming & remote touch interaction state
        self.live_stream_active: bool = False
        self.live_stream_paused: bool = False
        self.live_stream_thread: Optional[threading.Thread] = None
        self.current_screen_img: Optional[Image.Image] = None
        self.screen_render_rect: Optional[Tuple[int, int, int, int]] = None  # (offset_x, offset_y, rendered_w, rendered_h)
        self.device_screen_size: Tuple[int, int] = (1080, 2400)
        self.touch_start_canvas: Optional[Tuple[int, int]] = None
        self.touch_start_phone: Optional[Tuple[int, int]] = None
        self.touch_start_time: float = 0.0
        self.stream_fps: float = 0.0
        self._canvas_img_id = None
        self._canvas_photo = None
        self._quick_refresh_scheduled: bool = False
        self._is_capturing_stream_frame: bool = False

        # Setup GUI Components
        self._setup_layout()
        self._setup_sidebar()
        self._setup_topbar()
        self._setup_content_area()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

        # Load initial view
        self.show_view("dashboard")

        # Start background device detection loop
        self.monitor_thread = threading.Thread(target=self._device_monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _setup_layout(self):
        self.grid_columnconfigure(0, weight=0, minsize=260)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0, minsize=64)
        self.grid_rowconfigure(1, weight=1)

    def _setup_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_sidebar"],
            corner_radius=0,
            border_width=1,
            border_color=THEME["border"]
        )
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(11, weight=1)

        # Header / Brand with Android Logo
        brand_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        brand_frame.grid(row=0, column=0, padx=16, pady=(16, 14), sticky="ew")

        # Load Android Cyber Logo
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        png_path = os.path.join(base_dir, "assets", "icon.png")
        if os.path.exists(png_path):
            try:
                logo_pil = Image.open(png_path)
                self.logo_sidebar_ctk = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(42, 42))
                logo_lbl = ctk.CTkLabel(brand_frame, image=self.logo_sidebar_ctk, text="")
                logo_lbl.pack(side="left", padx=(0, 10))
            except Exception:
                pass

        titles_box = ctk.CTkFrame(brand_frame, fg_color="transparent")
        titles_box.pack(side="left", fill="x", expand=True)

        title_lbl = ctk.CTkLabel(
            titles_box,
            text="MacTech Android",
            font=ctk.CTkFont(family=THEME["font_family"], size=16, weight="bold"),
            text_color=THEME["text_main"]
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            titles_box,
            text="Forensic Suite v2.2",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            text_color="#3DDC84" # Neon Android Green
        )
        sub_lbl.pack(anchor="w")

        # Sidebar Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊 Dashboard & Overview", self.show_dashboard),
            ("current_app", "🚀 Current App on Screen", self.show_current_app),
            ("app_manager", "📦 App Manager & Uninstaller", self.show_app_manager),
            ("fake_detector", "🔍 Clone & Fake Inspector", self.show_fake_detector),
            ("data_recovery", "💾 ADB Data Recovery", self.show_data_recovery),
            ("optimize", "⚡ Clean & Defragment", self.show_optimize),
            ("remote", "🎮 Remote & Mirroring", self.show_remote),
            ("terminal", "💻 Silent ADB Terminal", self.show_terminal),
            ("mtp", "📁 MTP & Storage Explorer", self.show_mtp),
        ]

        for idx, (key, label, cmd) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=label,
                anchor="w",
                font=ctk.CTkFont(family=THEME["font_family"], size=13),
                fg_color="transparent",
                text_color=THEME["text_secondary"],
                hover_color=THEME["bg_card_alt"],
                height=38,
                corner_radius=8,
                command=cmd
            )
            btn.grid(row=idx, column=0, padx=14, pady=3, sticky="ew")
            self.nav_buttons[key] = btn

        # Donation Button in Sidebar
        donate_frame = ctk.CTkFrame(
            self.sidebar_frame,
            fg_color=THEME["bg_card"],
            border_width=1,
            border_color=THEME["border"],
            corner_radius=10
        )
        donate_frame.grid(row=12, column=0, padx=14, pady=(10, 16), sticky="ew")

        donate_lbl = ctk.CTkLabel(
            donate_frame,
            text="❤️ Support Developer",
            font=ctk.CTkFont(family=THEME["font_family"], size=13, weight="bold"),
            text_color="#F43F5E"
        )
        donate_lbl.pack(pady=(10, 2))

        donate_sub = ctk.CTkLabel(
            donate_frame,
            text="Help keep MacTech Lab tools free & powerful.",
            font=ctk.CTkFont(family=THEME["font_family"], size=10),
            text_color=THEME["text_muted"],
            wraplength=200
        )
        donate_sub.pack(padx=10, pady=(0, 8))

        donate_btn = ctk.CTkButton(
            donate_frame,
            text="Donate via PayPal ($3)",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            fg_color="#0070BA",
            hover_color="#005ea6",
            height=32,
            corner_radius=6,
            command=self.open_donation_modal
        )
        donate_btn.pack(padx=12, pady=(0, 12), fill="x")

    def _setup_topbar(self):
        self.topbar_frame = ctk.CTkFrame(
            self,
            fg_color=THEME["bg_card"],
            corner_radius=0,
            border_width=1,
            border_color=THEME["border"],
            height=64
        )
        self.topbar_frame.grid(row=0, column=1, sticky="nsew")
        self.topbar_frame.grid_columnconfigure(0, weight=1)

        # Left: Device Status Pill
        status_box = ctk.CTkFrame(self.topbar_frame, fg_color="transparent")
        status_box.pack(side="left", padx=20, pady=12)

        self.status_indicator = ctk.CTkLabel(
            status_box,
            text="●",
            font=ctk.CTkFont(size=18),
            text_color=THEME["danger"]
        )
        self.status_indicator.pack(side="left", padx=(0, 6))

        self.status_label = ctk.CTkLabel(
            status_box,
            text="Searching for Android phone...",
            font=ctk.CTkFont(family=THEME["font_family"], size=13, weight="bold"),
            text_color=THEME["text_main"]
        )
        self.status_label.pack(side="left")

        # Right: Action Buttons (Force USB Debugging, Refresh, Donate)
        actions_box = ctk.CTkFrame(self.topbar_frame, fg_color="transparent")
        actions_box.pack(side="right", padx=20, pady=12)

        self.btn_force_usb = ctk.CTkButton(
            actions_box,
            text="⚡ Enable / Force Debugging",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            fg_color=THEME["warning"],
            hover_color=THEME["warning_hover"],
            text_color="#000000",
            height=32,
            command=self.open_force_usb_dialog
        )
        self.btn_force_usb.pack(side="left", padx=6)

        self.btn_refresh = ctk.CTkButton(
            actions_box,
            text="🔄 Rescan",
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            fg_color=THEME["bg_card_alt"],
            hover_color=THEME["border_highlight"],
            text_color=THEME["text_main"],
            width=80,
            height=32,
            command=lambda: threading.Thread(target=self._manual_rescan, daemon=True).start()
        )
        self.btn_refresh.pack(side="left", padx=6)

        self.btn_top_donate = ctk.CTkButton(
            actions_box,
            text="☕ Donate ($3)",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            fg_color="#0070BA",
            hover_color="#005ea6",
            width=105,
            height=32,
            command=self.open_donation_modal
        )
        self.btn_top_donate.pack(side="left", padx=6)

    def _setup_content_area(self):
        self.content_container = ctk.CTkFrame(self, fg_color=THEME["bg_main"], corner_radius=0)
        self.content_container.grid(row=1, column=1, sticky="nsew", padx=16, pady=16)
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

    def _highlight_nav(self, active_key: str):
        self.current_view_name = active_key
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.configure(
                    fg_color=THEME["primary"],
                    text_color=THEME["text_main"]
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=THEME["text_secondary"]
                )

    def _clear_content(self):
        for widget in self.content_container.winfo_children():
            widget.destroy()

    def _on_close_window(self):
        self.is_monitoring = False
        self.live_stream_active = False
        self.live_stream_paused = True
        self.destroy()

    def show_view(self, view_name: str):
        if view_name != "remote" and self.live_stream_active and not self.live_stream_paused:
            self.live_stream_paused = True
        elif view_name == "remote" and self.live_stream_active and self.live_stream_paused:
            self.live_stream_paused = False

        views = {
            "dashboard": self.show_dashboard,
            "current_app": self.show_current_app,
            "app_manager": self.show_app_manager,
            "fake_detector": self.show_fake_detector,
            "data_recovery": self.show_data_recovery,
            "optimize": self.show_optimize,
            "remote": self.show_remote,
            "terminal": self.show_terminal,
            "mtp": self.show_mtp,
        }
        if view_name in views:
            views[view_name]()

    # =========================================================================
    # Device Monitor Loop (Silent, Background)
    # =========================================================================

    def _device_monitor_loop(self):
        """Continuously checks ADB & MTP status every 3 seconds silently."""
        while self.is_monitoring:
            try:
                status = self.adb.get_overall_status()
                self.status_data = status
                self.after(0, self._update_topbar_status, status)
            except Exception:
                pass
            time.sleep(3)

    def _manual_rescan(self):
        self.after(0, lambda: self.status_label.configure(text="Rescanning USB bus & ADB ports..."))
        self.adb.restart_adb_server()
        status = self.adb.get_overall_status()
        self.status_data = status
        self.after(0, self._update_topbar_status, status)
        self.after(0, lambda: self.show_view(self.current_view_name))

    def _update_topbar_status(self, status: Dict[str, Any]):
        conn = status.get("connection", "DISCONNECTED")
        if conn == "AUTHORIZED":
            dev = status.get("active_device", {})
            self.status_indicator.configure(text="●", text_color=THEME["success"])
            self.status_label.configure(text=f"Device Online: {dev.get('model', dev.get('serial', 'Connected'))} (Ready)", text_color=THEME["success"])
        elif conn == "UNAUTHORIZED":
            self.status_indicator.configure(text="●", text_color=THEME["warning"])
            self.status_label.configure(text="Connected (Unauthorized) - Please tap 'Allow USB Debugging' on phone screen!", text_color=THEME["warning"])
        elif conn == "MTP_ONLY":
            mtp_dev = status.get("mtp_devices", [{}])[0].get("name", "Phone")
            self.status_indicator.configure(text="●", text_color=THEME["accent_cyan"])
            self.status_label.configure(text=f"USB/MTP Detected: {mtp_dev} (USB Debugging is OFF)", text_color=THEME["accent_cyan"])
        elif conn == "FASTBOOT":
            self.status_indicator.configure(text="●", text_color=THEME["purple"])
            self.status_label.configure(text="Device in FASTBOOT / Bootloader Mode", text_color=THEME["purple"])
        elif conn == "RECOVERY":
            self.status_indicator.configure(text="●", text_color=THEME["purple"])
            self.status_label.configure(text="Device in RECOVERY Mode", text_color=THEME["purple"])
        else:
            self.status_indicator.configure(text="●", text_color=THEME["danger"])
            self.status_label.configure(text="No Device Connected (Plug in phone via USB cable)", text_color=THEME["text_muted"])

    # =========================================================================
    # VIEW 1: Dashboard & Hardware Overview
    # =========================================================================

    def show_dashboard(self):
        self._highlight_nav("dashboard")
        self._clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Header Title
        h_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        h_frame.pack(fill="x", pady=(0, 14))

        title = ctk.CTkLabel(
            h_frame,
            text="📱 Device Health & Specifications Dashboard",
            font=ctk.CTkFont(family=THEME["font_family"], size=20, weight="bold"),
            text_color=THEME["text_main"]
        )
        title.pack(side="left")

        btn_refresh_info = ctk.CTkButton(
            h_frame,
            text="Refresh Specs",
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            height=30,
            command=lambda: threading.Thread(target=self._load_dashboard_data, args=(scroll,), daemon=True).start()
        )
        btn_refresh_info.pack(side="right")

        # Loading placeholder
        self.dash_status_lbl = ctk.CTkLabel(
            scroll,
            text="Analyzing hardware sensors and query buffers...",
            font=ctk.CTkFont(family=THEME["font_family"], size=13),
            text_color=THEME["text_muted"]
        )
        self.dash_status_lbl.pack(pady=20)

        # Async fetch data
        threading.Thread(target=self._load_dashboard_data, args=(scroll,), daemon=True).start()

    def _load_dashboard_data(self, scroll: ctk.CTkScrollableFrame):
        data = self.adb.get_device_overview()
        self.cached_overview = data
        self.after(0, self._render_dashboard_cards, scroll, data)

    def _render_dashboard_cards(self, scroll: ctk.CTkScrollableFrame, data: Dict[str, Any]):
        for widget in scroll.winfo_children():
            if widget != scroll.winfo_children()[0]: # preserve header
                widget.destroy()

        # Row 1: Key Status Cards
        cards_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 14))
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        metric_cards = [
            ("Model / Brand", f"{data.get('brand')} {data.get('model')}", data.get("manufacturer"), THEME["primary"]),
            ("Battery Status", f"{data.get('battery_level')} ({data.get('battery_health')})", f"Temp: {data.get('battery_temp')}", THEME["success"]),
            ("Physical RAM", data.get("total_ram"), f"Free: {data.get('free_ram')}", THEME["purple"]),
            ("Storage (/data)", f"Total: {data.get('storage_total')}", f"Free: {data.get('storage_free')}", THEME["accent_cyan"])
        ]

        for col, (title, main_val, sub_val, color) in enumerate(metric_cards):
            card = ctk.CTkFrame(cards_frame, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
            card.grid(row=0, column=col, padx=6, pady=4, sticky="nsew")

            t_lbl = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family=THEME["font_family"], size=12), text_color=THEME["text_muted"])
            t_lbl.pack(anchor="w", padx=14, pady=(12, 2))

            v_lbl = ctk.CTkLabel(card, text=main_val or "N/A", font=ctk.CTkFont(family=THEME["font_family"], size=15, weight="bold"), text_color=color)
            v_lbl.pack(anchor="w", padx=14, pady=(0, 2))

            s_lbl = ctk.CTkLabel(card, text=sub_val or "N/A", font=ctk.CTkFont(family=THEME["font_family"], size=11), text_color=THEME["text_secondary"])
            s_lbl.pack(anchor="w", padx=14, pady=(0, 12))

        # Row 2: Comprehensive Specification Grids
        spec_frame = ctk.CTkFrame(scroll, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
        spec_frame.pack(fill="x", pady=(0, 14))

        sec_title = ctk.CTkLabel(spec_frame, text="🔍 Technical System Properties", font=ctk.CTkFont(family=THEME["font_family"], size=14, weight="bold"), text_color=THEME["text_main"])
        sec_title.pack(anchor="w", padx=16, pady=(14, 10))

        spec_grid = ctk.CTkFrame(spec_frame, fg_color="transparent")
        spec_grid.pack(fill="x", padx=16, pady=(0, 16))
        spec_grid.grid_columnconfigure((0, 1), weight=1)

        items_left = [
            ("Android Version", f"{data.get('android_version')} (SDK {data.get('sdk_level')})"),
            ("Security Patch", data.get("security_patch")),
            ("Hardware SoC / Board", f"{data.get('hardware')} / {data.get('platform')}"),
            ("CPU Architecture & Cores", f"{data.get('cpu_arch')} ({data.get('cpu_cores')})"),
            ("Serial Number", data.get("serial")),
        ]

        items_right = [
            ("Display Resolution", f"{data.get('display_resolution')} ({data.get('display_density')})"),
            ("Battery Voltage", data.get("battery_voltage")),
            ("Battery State", data.get("battery_status")),
            ("Build Fingerprint / ID", data.get("build_id")),
            ("WLAN IP Address", data.get("ip_address")),
        ]

        for idx, (label, val) in enumerate(items_left):
            row_box = ctk.CTkFrame(spec_grid, fg_color="transparent")
            row_box.grid(row=idx, column=0, sticky="ew", pady=3)
            ctk.CTkLabel(row_box, text=label + ":", font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"), text_color=THEME["text_secondary"], width=170, anchor="w").pack(side="left")
            ctk.CTkLabel(row_box, text=str(val or "Unknown"), font=ctk.CTkFont(family=THEME["font_mono"], size=12), text_color=THEME["text_main"], anchor="w").pack(side="left", fill="x", expand=True)

        for idx, (label, val) in enumerate(items_right):
            row_box = ctk.CTkFrame(spec_grid, fg_color="transparent")
            row_box.grid(row=idx, column=1, sticky="ew", pady=3)
            ctk.CTkLabel(row_box, text=label + ":", font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"), text_color=THEME["text_secondary"], width=170, anchor="w").pack(side="left")
            ctk.CTkLabel(row_box, text=str(val or "Unknown"), font=ctk.CTkFont(family=THEME["font_mono"], size=12), text_color=THEME["text_main"], anchor="w").pack(side="left", fill="x", expand=True)

        # Row 3: Quick Power & Reboot Controls
        ctl_frame = ctk.CTkFrame(scroll, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
        ctl_frame.pack(fill="x", pady=(0, 14))

        c_title = ctk.CTkLabel(ctl_frame, text="⚡ Quick Hardware & Reboot Controls", font=ctk.CTkFont(family=THEME["font_family"], size=14, weight="bold"), text_color=THEME["text_main"])
        c_title.pack(anchor="w", padx=16, pady=(14, 10))

        c_buttons_box = ctk.CTkFrame(ctl_frame, fg_color="transparent")
        c_buttons_box.pack(fill="x", padx=16, pady=(0, 16))

        reboots = [
            ("Normal Reboot", "normal", THEME["primary"]),
            ("Recovery Mode", "recovery", THEME["purple"]),
            ("Fastboot / Bootloader", "bootloader", THEME["accent_cyan"]),
            ("EDL Mode (Qualcomm)", "edl", THEME["warning"]),
            ("Power Off Device", "poweroff", THEME["danger"]),
        ]

        for label, mode, color in reboots:
            btn = ctk.CTkButton(
                c_buttons_box,
                text=label,
                font=ctk.CTkFont(family=THEME["font_family"], size=12),
                fg_color=color,
                height=34,
                corner_radius=6,
                command=lambda m=mode: self._confirm_reboot(m)
            )
            btn.pack(side="left", padx=5, expand=True, fill="x")

        # Row 4: One-Click Engineering & Diagnostics Shortcuts
        wf_frame = ctk.CTkFrame(scroll, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
        wf_frame.pack(fill="x", pady=(0, 14))

        wf_title = ctk.CTkLabel(wf_frame, text="🚀 One-Click Technician Shortcuts", font=ctk.CTkFont(family=THEME["font_family"], size=14, weight="bold"), text_color=THEME["text_main"])
        wf_title.pack(anchor="w", padx=16, pady=(14, 10))

        wf_box = ctk.CTkFrame(wf_frame, fg_color="transparent")
        wf_box.pack(fill="x", padx=16, pady=(0, 16))

        shortcuts = [
            ("🔓 Wake & Unlock", lambda: threading.Thread(target=self.adb.attempt_force_usb_debugging, daemon=True).start(), THEME["primary"]),
            ("🚀 Current App", self.show_current_app, THEME["accent_cyan"]),
            ("🔍 Clone Inspector", self.show_fake_detector, THEME["danger"]),
            ("⚡ Storage TRIM", self.show_optimize, THEME["purple"]),
            ("💾 Data Recovery", self.show_data_recovery, THEME["warning"]),
            ("💻 Silent Terminal (60+ Cmds)", self.show_terminal, THEME["android_green"]),
        ]

        for label, cmd_fn, color in shortcuts:
            s_btn = ctk.CTkButton(
                wf_box,
                text=label,
                font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
                fg_color=color,
                hover_color=THEME["border_highlight"],
                height=34,
                corner_radius=6,
                command=cmd_fn
            )
            s_btn.pack(side="left", padx=4, expand=True, fill="x")

    def _confirm_reboot(self, mode: str):
        if messagebox.askyesno("Confirm Reboot", f"Are you sure you want to issue reboot command ({mode.upper()}) to the device?"):
            ok, msg = self.adb.reboot_device(mode)
            messagebox.showinfo("Reboot", msg)

    # =========================================================================
    # VIEW 2: Current Foreground App on Screen
    # =========================================================================

    def show_current_app(self):
        self._highlight_nav("current_app")
        self._clear_content()

        container = ctk.CTkFrame(self.content_container, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # Header
        h_box = ctk.CTkFrame(container, fg_color="transparent")
        h_box.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            h_box,
            text="🚀 Real-Time Foreground App Tracker & Immediate Uninstaller",
            font=ctk.CTkFont(family=THEME["font_family"], size=20, weight="bold"),
            text_color=THEME["text_main"]
        ).pack(side="left")

        # Action bar
        act_card = ctk.CTkFrame(container, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
        act_card.pack(fill="x", pady=(0, 16), padx=2)

        desc = ctk.CTkLabel(
            act_card,
            text="Identify what application is currently displayed and active on the phone screen. Useful for malware analysis, adware hunting, and instant uninstallation of unwanted overlay or bloatware apps.",
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            text_color=THEME["text_secondary"],
            wraplength=900,
            justify="left"
        )
        desc.pack(anchor="w", padx=16, pady=(12, 12))

        btn_box = ctk.CTkFrame(act_card, fg_color="transparent")
        btn_box.pack(fill="x", padx=16, pady=(0, 14))

        self.btn_inspect_app = ctk.CTkButton(
            btn_box,
            text="🔍 Inspect Active Screen App",
            font=ctk.CTkFont(family=THEME["font_family"], size=13, weight="bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            height=36,
            command=self._inspect_active_app
        )
        self.btn_inspect_app.pack(side="left", padx=(0, 10))

        # Details Display Card
        self.app_details_card = ctk.CTkFrame(container, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
        self.app_details_card.pack(fill="both", expand=True, padx=2)

        self.lbl_app_status = ctk.CTkLabel(
            self.app_details_card,
            text="Click 'Inspect Active Screen App' to query foreground window manager...",
            font=ctk.CTkFont(family=THEME["font_family"], size=14),
            text_color=THEME["text_muted"]
        )
        self.lbl_app_status.pack(pady=40)

    def _inspect_active_app(self):
        self.lbl_app_status.configure(text="Querying window manager focus...")
        def _fetch():
            res = self.adb.get_current_foreground_app()
            self.after(0, self._render_current_app_details, res)
        threading.Thread(target=_fetch, daemon=True).start()

    def _render_current_app_details(self, info: Dict[str, str]):
        for w in self.app_details_card.winfo_children():
            w.destroy()

        pkg = info.get("package", "Unknown")
        if pkg in ["Unknown", "None", ""]:
            ctk.CTkLabel(
                self.app_details_card,
                text="⚠️ Could not detect foreground app.\nEnsure phone screen is unlocked and USB Debugging is authorized.",
                font=ctk.CTkFont(family=THEME["font_family"], size=14),
                text_color=THEME["warning"]
            ).pack(pady=40)
            return

        header_box = ctk.CTkFrame(self.app_details_card, fg_color="transparent")
        header_box.pack(fill="x", padx=20, pady=(16, 10))

        ctk.CTkLabel(
            header_box,
            text=f"Active Package: {pkg}",
            font=ctk.CTkFont(family=THEME["font_family"], size=18, weight="bold"),
            text_color=THEME["accent_cyan"]
        ).pack(anchor="w")

        info_box = ctk.CTkFrame(self.app_details_card, fg_color="transparent")
        info_box.pack(fill="x", padx=20, pady=10)

        rows = [
            ("Package Identifier", pkg),
            ("Active Activity Class", info.get("activity")),
            ("Window Component Focus", info.get("component")),
            ("Version Name", info.get("version", "Unknown"))
        ]

        for label, val in rows:
            r = ctk.CTkFrame(info_box, fg_color="transparent")
            r.pack(fill="x", pady=4)
            ctk.CTkLabel(r, text=label + ":", font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"), text_color=THEME["text_secondary"], width=180, anchor="w").pack(side="left")
            ctk.CTkLabel(r, text=str(val), font=ctk.CTkFont(family=THEME["font_mono"], size=12), text_color=THEME["text_main"], anchor="w").pack(side="left")

        # Action Buttons for Current App
        actions_frame = ctk.CTkFrame(self.app_details_card, fg_color=THEME["bg_card_alt"], corner_radius=8)
        actions_frame.pack(fill="x", padx=20, pady=(20, 20))

        ctk.CTkLabel(actions_frame, text="Dangerous Actions for Active App:", font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"), text_color=THEME["text_muted"]).pack(anchor="w", padx=16, pady=(10, 8))

        btn_row = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 14))

        btn_uninstall_curr = ctk.CTkButton(
            btn_row,
            text="🗑️ UNINSTALL Current App",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            fg_color=THEME["danger"],
            hover_color=THEME["danger_hover"],
            height=34,
            command=lambda: self._execute_uninstall(pkg, user_zero=False)
        )
        btn_uninstall_curr.pack(side="left", padx=(0, 10))

        btn_uninstall_zero = ctk.CTkButton(
            btn_row,
            text="🧹 Debloat (Uninstall User 0)",
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            fg_color=THEME["warning"],
            hover_color=THEME["warning_hover"],
            text_color="#000",
            height=34,
            command=lambda: self._execute_uninstall(pkg, user_zero=True)
        )
        btn_uninstall_zero.pack(side="left", padx=(0, 10))

        btn_force_stop = ctk.CTkButton(
            btn_row,
            text="⏹️ Force Stop",
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            fg_color=THEME["bg_card"],
            hover_color=THEME["border_highlight"],
            height=34,
            command=lambda: self._execute_force_stop(pkg)
        )
        btn_force_stop.pack(side="left", padx=(0, 10))

        btn_clear_data = ctk.CTkButton(
            btn_row,
            text="🧼 Clear Cache & Data",
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            fg_color=THEME["bg_card"],
            hover_color=THEME["border_highlight"],
            height=34,
            command=lambda: self._execute_clear_data(pkg)
        )
        btn_clear_data.pack(side="left")

    def _execute_uninstall(self, pkg: str, user_zero: bool = False):
        mode = "Debloat (User 0)" if user_zero else "Complete Removal"
        if messagebox.askyesno("Confirm Uninstall", f"Are you sure you want to uninstall {pkg}?\nMode: {mode}"):
            ok, msg = self.adb.uninstall_app(pkg, user_zero=user_zero)
            if ok:
                messagebox.showinfo("Success", msg)
                self._inspect_active_app()
            else:
                messagebox.showerror("Error", msg)

    def _execute_force_stop(self, pkg: str):
        ok, msg = self.adb.force_stop_app(pkg)
        messagebox.showinfo("Result", msg)

    def _execute_clear_data(self, pkg: str):
        if messagebox.askyesno("Confirm", f"Clear all cache and app storage for {pkg}?"):
            ok, msg = self.adb.clear_app_data(pkg)
            messagebox.showinfo("Result", msg)

    # =========================================================================
    # VIEW 3: Searchable App Manager & Uninstaller
    # =========================================================================

    def show_app_manager(self):
        self._highlight_nav("app_manager")
        self._clear_content()

        container = ctk.CTkFrame(self.content_container, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # Header & Filter Bar
        h_box = ctk.CTkFrame(container, fg_color="transparent")
        h_box.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            h_box,
            text="📦 Searchable Package & App Manager",
            font=ctk.CTkFont(family=THEME["font_family"], size=20, weight="bold"),
            text_color=THEME["text_main"]
        ).pack(side="left")

        # Search and Filter Options
        ctrl_bar = ctk.CTkFrame(container, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
        ctrl_bar.pack(fill="x", pady=(0, 12))

        search_box = ctk.CTkFrame(ctrl_bar, fg_color="transparent")
        search_box.pack(side="left", padx=16, pady=10)

        self.search_entry = ctk.CTkEntry(
            search_box,
            placeholder_text="Search package name (e.g. facebook, chrome)...",
            width=280,
            height=34,
            fg_color=THEME["bg_input"],
            border_color=THEME["border"]
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_packages())

        self.filter_var = ctk.StringVar(value="user")
        for val, txt in [("user", "User Apps (-3)"), ("all", "All Apps"), ("system", "System Apps (-s)")]:
            r_btn = ctk.CTkRadioButton(
                ctrl_bar,
                text=txt,
                variable=self.filter_var,
                value=val,
                command=self._load_package_list
            )
            r_btn.pack(side="left", padx=10)

        btn_install_apk = ctk.CTkButton(
            ctrl_bar,
            text="📥 Install APK to Phone",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            height=34,
            command=self._browse_and_install_apk
        )
        btn_install_apk.pack(side="right", padx=16, pady=10)

        # App List Scrollable Container
        self.app_list_frame = ctk.CTkScrollableFrame(container, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
        self.app_list_frame.pack(fill="both", expand=True)

        self._load_package_list()

    def _load_package_list(self):
        for w in self.app_list_frame.winfo_children():
            w.destroy()

        loading_lbl = ctk.CTkLabel(
            self.app_list_frame,
            text="Scanning installed packages via PackageManager...",
            font=ctk.CTkFont(family=THEME["font_family"], size=13),
            text_color=THEME["text_muted"]
        )
        loading_lbl.pack(pady=30)

        filter_type = self.filter_var.get()

        def _fetch():
            pkgs = self.adb.list_installed_packages(filter_type=filter_type)
            self.installed_packages_cache = pkgs
            self.after(0, self._render_package_items, pkgs)

        threading.Thread(target=_fetch, daemon=True).start()

    def _filter_packages(self):
        query = self.search_entry.get().strip().lower()
        if not query:
            self._render_package_items(self.installed_packages_cache)
        else:
            filtered = [p for p in self.installed_packages_cache if query in p["package"].lower()]
            self._render_package_items(filtered)

    def _render_package_items(self, pkgs: List[Dict[str, str]]):
        for w in self.app_list_frame.winfo_children():
            w.destroy()

        if not pkgs:
            ctk.CTkLabel(
                self.app_list_frame,
                text="No packages found matching criteria.",
                font=ctk.CTkFont(family=THEME["font_family"], size=13),
                text_color=THEME["text_muted"]
            ).pack(pady=30)
            return

        count_lbl = ctk.CTkLabel(
            self.app_list_frame,
            text=f"Showing {len(pkgs)} packages:",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            text_color=THEME["text_secondary"]
        )
        count_lbl.pack(anchor="w", padx=16, pady=(10, 6))

        for item in pkgs[:150]: # limit rendering to 150 for fluid performance
            pkg_name = item["package"]
            pkg_type = item.get("type", "User")
            installer = item.get("installer", "Unknown")

            row = ctk.CTkFrame(self.app_list_frame, fg_color=THEME["bg_card_alt"], corner_radius=6)
            row.pack(fill="x", padx=12, pady=3)

            col_left = ctk.CTkFrame(row, fg_color="transparent")
            col_left.pack(side="left", padx=12, pady=8, fill="x", expand=True)

            name_lbl = ctk.CTkLabel(
                col_left,
                text=pkg_name,
                font=ctk.CTkFont(family=THEME["font_mono"], size=13, weight="bold"),
                text_color=THEME["text_main"],
                anchor="w"
            )
            name_lbl.pack(anchor="w")

            sub_lbl = ctk.CTkLabel(
                col_left,
                text=f"Type: {pkg_type}  |  Installer: {installer}",
                font=ctk.CTkFont(family=THEME["font_family"], size=11),
                text_color=THEME["text_muted"],
                anchor="w"
            )
            sub_lbl.pack(anchor="w")

            btn_box = ctk.CTkFrame(row, fg_color="transparent")
            btn_box.pack(side="right", padx=12, pady=6)

            btn_inspect = ctk.CTkButton(
                btn_box,
                text="Info",
                width=60,
                height=28,
                font=ctk.CTkFont(size=11),
                fg_color=THEME["primary"],
                command=lambda p=pkg_name: self._show_package_info_dialog(p)
            )
            btn_inspect.pack(side="left", padx=4)

            btn_pull = ctk.CTkButton(
                btn_box,
                text="Extract APK",
                width=85,
                height=28,
                font=ctk.CTkFont(size=11),
                fg_color=THEME["bg_card"],
                hover_color=THEME["border_highlight"],
                command=lambda p=pkg_name: self._pull_package_apk(p)
            )
            btn_pull.pack(side="left", padx=4)

            btn_del = ctk.CTkButton(
                btn_box,
                text="Uninstall",
                width=75,
                height=28,
                font=ctk.CTkFont(size=11),
                fg_color=THEME["danger"],
                hover_color=THEME["danger_hover"],
                command=lambda p=pkg_name: self._execute_uninstall(p)
            )
            btn_del.pack(side="left", padx=4)

    def _show_package_info_dialog(self, pkg: str):
        details = self.adb.get_package_details(pkg)
        msg = (
            f"Package: {details.get('package')}\n\n"
            f"Version Name: {details.get('version_name')}\n"
            f"Version Code: {details.get('version_code')}\n"
            f"First Install Date: {details.get('first_install_time')}\n"
            f"Last Update Date: {details.get('last_update_time')}\n"
            f"APK Path: {details.get('apk_path')}\n"
            f"UID: {details.get('uid')}"
        )
        messagebox.showinfo(f"Package Info: {pkg}", msg)

    def _pull_package_apk(self, pkg: str):
        folder = filedialog.askdirectory(title="Select Folder to Save Extracted APK")
        if folder:
            ok, res = self.adb.pull_apk(pkg, folder)
            if ok:
                messagebox.showinfo("Success", f"APK extracted to:\n{res}")
            else:
                messagebox.showerror("Error", res)

    def _browse_and_install_apk(self):
        apk_path = filedialog.askopenfilename(title="Select Android APK File", filetypes=[("APK Files", "*.apk")])
        if apk_path:
            def _install():
                self.after(0, lambda: messagebox.showinfo("Installing", f"Installing {os.path.basename(apk_path)} to device. Please wait..."))
                ok, msg = self.adb.install_apk(apk_path)
                if ok:
                    self.after(0, lambda: messagebox.showinfo("Installed", msg))
                    self._load_package_list()
                else:
                    self.after(0, lambda: messagebox.showerror("Install Failed", msg))
            threading.Thread(target=_install, daemon=True).start()

    # =========================================================================
    # VIEW 4: Forensic Clone & Fake Phone Inspector (Authenticity Check)
    # =========================================================================

    def show_fake_detector(self):
        self._highlight_nav("fake_detector")
        self._clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Header
        h_box = ctk.CTkFrame(scroll, fg_color="transparent")
        h_box.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            h_box,
            text="🔍 Forensic Authenticity & Clone / Fake Phone Inspector",
            font=ctk.CTkFont(family=THEME["font_family"], size=20, weight="bold"),
            text_color=THEME["text_main"]
        ).pack(side="left")

        # Explain Card
        intro_card = ctk.CTkFrame(scroll, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
        intro_card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            intro_card,
            text=(
                "Counterfeit and clone phones often spoof 'Settings' and build properties to advertise fake Snapdragon 8 Gen 3 CPUs, "
                "fake 16GB RAM, fake 1TB storage, and fake Android 14/15 versions. This forensic engine bypasses the spoofed userland layers "
                "and directly interrogates the Linux kernel (/proc/meminfo, /proc/cpuinfo, /proc/version, physical display dimensions, and OEM signing keys) "
                "to deliver a verifiable authenticity verdict."
            ),
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            text_color=THEME["text_secondary"],
            wraplength=920,
            justify="left"
        ).pack(anchor="w", padx=16, pady=12)

        btn_run_audit = ctk.CTkButton(
            intro_card,
            text="🔬 Run Full Authenticity Audit",
            font=ctk.CTkFont(family=THEME["font_family"], size=13, weight="bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            height=36,
            command=lambda: threading.Thread(target=self._run_authenticity_audit, args=(scroll,), daemon=True).start()
        )
        btn_run_audit.pack(anchor="w", padx=16, pady=(0, 14))

        self.fake_audit_container = ctk.CTkFrame(scroll, fg_color="transparent")
        self.fake_audit_container.pack(fill="both", expand=True)

        # Initial run
        threading.Thread(target=self._run_authenticity_audit, args=(scroll,), daemon=True).start()

    def _run_authenticity_audit(self, scroll: ctk.CTkScrollableFrame):
        for w in self.fake_audit_container.winfo_children():
            w.destroy()

        load_lbl = ctk.CTkLabel(
            self.fake_audit_container,
            text="Performing low-level kernel forensics and cross-referencing hardware IDs...",
            font=ctk.CTkFont(family=THEME["font_family"], size=14),
            text_color=THEME["text_muted"]
        )
        load_lbl.pack(pady=40)

        report = self.adb.inspect_authenticity()
        self.after(0, self._render_authenticity_results, report)

    def _render_authenticity_results(self, rep: Dict[str, Any]):
        for w in self.fake_audit_container.winfo_children():
            w.destroy()

        score = rep.get("score", 100)
        verdict = rep.get("verdict", "UNKNOWN")

        if verdict == "GENUINE / AUTHENTIC":
            v_color = THEME["success"]
            v_bg = "#064E3B"
            v_icon = "🛡️ VERIFIED GENUINE"
        elif verdict == "SUSPICIOUS / MODIFIED":
            v_color = THEME["warning"]
            v_bg = "#78350F"
            v_icon = "⚠️ SUSPICIOUS FIRMWARE"
        else:
            v_color = THEME["danger"]
            v_bg = "#7F1D1D"
            v_icon = "🚨 CONFIRMED COUNTERFEIT / FAKE CLONE"

        # Verdict Banner
        banner = ctk.CTkFrame(self.fake_audit_container, fg_color=v_bg, corner_radius=10)
        banner.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            banner,
            text=f"{v_icon}  (Authenticity Confidence: {score}/100)",
            font=ctk.CTkFont(family=THEME["font_family"], size=16, weight="bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", padx=16, pady=(14, 4))

        for find in rep.get("findings", []):
            ctk.CTkLabel(
                banner,
                text=find,
                font=ctk.CTkFont(family=THEME["font_family"], size=12),
                text_color="#E2E8F0"
            ).pack(anchor="w", padx=16, pady=(0, 12))

        # Anomalies Card (if any)
        anomalies = rep.get("anomalies", [])
        if anomalies:
            anom_card = ctk.CTkFrame(self.fake_audit_container, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["danger"], corner_radius=10)
            anom_card.pack(fill="x", pady=(0, 14))

            ctk.CTkLabel(
                anom_card,
                text="🚩 Critical Hardware & Identity Mismatches Detected:",
                font=ctk.CTkFont(family=THEME["font_family"], size=14, weight="bold"),
                text_color=THEME["danger"]
            ).pack(anchor="w", padx=16, pady=(12, 8))

            for anom in anomalies:
                r = ctk.CTkFrame(anom_card, fg_color="transparent")
                r.pack(fill="x", padx=16, pady=3)
                ctk.CTkLabel(r, text="• " + anom, font=ctk.CTkFont(family=THEME["font_family"], size=12), text_color=THEME["text_main"], wraplength=880, justify="left").pack(anchor="w")
            ctk.CTkLabel(anom_card, text="", height=4).pack()

        # Side-by-Side: Advertised vs Kernel Reality
        comp_card = ctk.CTkFrame(self.fake_audit_container, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
        comp_card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            comp_card,
            text="🔬 Layer Cross-Examination (Advertised vs Raw Kernel Layer)",
            font=ctk.CTkFont(family=THEME["font_family"], size=14, weight="bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", padx=16, pady=(14, 10))

        grid = ctk.CTkFrame(comp_card, fg_color="transparent")
        grid.pack(fill="x", padx=16, pady=(0, 16))
        grid.grid_columnconfigure((0, 1), weight=1)

        # Advertised
        adv_box = ctk.CTkFrame(grid, fg_color=THEME["bg_card_alt"], corner_radius=8)
        adv_box.grid(row=0, column=0, padx=6, sticky="nsew")
        ctk.CTkLabel(adv_box, text="Advertised (build.prop / UI)", font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"), text_color=THEME["accent_cyan"]).pack(anchor="w", padx=12, pady=(10, 6))

        for k, v in rep.get("advertised", {}).items():
            ctk.CTkLabel(adv_box, text=f"{k}: {v}", font=ctk.CTkFont(family=THEME["font_mono"], size=11), text_color=THEME["text_main"]).pack(anchor="w", padx=12, pady=2)
        ctk.CTkLabel(adv_box, text="", height=4).pack()

        # Actual Kernel
        act_box = ctk.CTkFrame(grid, fg_color=THEME["bg_card_alt"], corner_radius=8)
        act_box.grid(row=0, column=1, padx=6, sticky="nsew")
        ctk.CTkLabel(act_box, text="Physical Reality (/proc/ kernel layer)", font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"), text_color=THEME["success"]).pack(anchor="w", padx=12, pady=(10, 6))

        for k, v in rep.get("actual_kernel", {}).items():
            ctk.CTkLabel(act_box, text=f"{k}: {v}", font=ctk.CTkFont(family=THEME["font_mono"], size=11), text_color=THEME["text_main"]).pack(anchor="w", padx=12, pady=2)
        ctk.CTkLabel(act_box, text="", height=4).pack()

    # =========================================================================
    # VIEW 5: ADB Data Recovery
    # =========================================================================

    def show_data_recovery(self):
        self._highlight_nav("data_recovery")
        self._clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Header
        h_box = ctk.CTkFrame(scroll, fg_color="transparent")
        h_box.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            h_box,
            text="💾 ADB Forensic Data Recovery & Media Extraction Suite",
            font=ctk.CTkFont(family=THEME["font_family"], size=20, weight="bold"),
            text_color=THEME["text_main"]
        ).pack(side="left")

        # Overview
        card = ctk.CTkFrame(scroll, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
        card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            card,
            text=(
                "Extract media, photos, WhatsApp documents, voice recordings, and full device backups directly to your PC "
                "even if the phone's touch screen is broken or unresponsive. Uses silent binary ADB pull pipelines with SHA checksum validation."
            ),
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            text_color=THEME["text_secondary"],
            wraplength=920,
            justify="left"
        ).pack(anchor="w", padx=16, pady=12)

        # Category Extraction Buttons Grid
        cats_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        cats_frame.pack(fill="x", pady=(0, 14))
        cats_frame.grid_columnconfigure((0, 1), weight=1)

        categories = [
            ("📸 Camera Photos & DCIM", "dcim", "Pull /sdcard/DCIM/Camera (all original camera photos & 4K videos)", THEME["primary"]),
            ("💬 WhatsApp Media & Voice Notes", "whatsapp", "Extract WhatsApp Images, Video, Audio, and Voice Notes", THEME["success"]),
            ("📁 Downloads & Documents", "documents", "Extract all PDFs, APKs, downloads and user documents", THEME["purple"]),
            ("🎵 Audio & Voice Recordings", "audio", "Extract sound recordings, dictaphone audio, and music", THEME["accent_cyan"]),
            ("📦 Full Internal Storage Dump", "all_storage", "Clone entire /sdcard/ filesystem hierarchy to PC folder", THEME["warning"]),
        ]

        for idx, (title, cat_key, subtext, color) in enumerate(categories):
            row = idx // 2
            col = idx % 2
            col_span = 2 if idx == 4 else 1

            cat_card = ctk.CTkFrame(cats_frame, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
            cat_card.grid(row=row, column=col, columnspan=col_span, padx=6, pady=6, sticky="nsew")

            ctk.CTkLabel(cat_card, text=title, font=ctk.CTkFont(family=THEME["font_family"], size=14, weight="bold"), text_color=THEME["text_main"]).pack(anchor="w", padx=14, pady=(12, 2))
            ctk.CTkLabel(cat_card, text=subtext, font=ctk.CTkFont(family=THEME["font_family"], size=11), text_color=THEME["text_muted"]).pack(anchor="w", padx=14, pady=(0, 10))

            btn = ctk.CTkButton(
                cat_card,
                text="Extract to PC Folder",
                font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
                fg_color=color,
                height=32,
                command=lambda k=cat_key: self._start_category_recovery(k)
            )
            btn.pack(anchor="w", padx=14, pady=(0, 12))

        # Full ADB Backup Card
        bak_card = ctk.CTkFrame(scroll, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
        bak_card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(bak_card, text="🛡️ Full ADB System Backup (.ab Archive)", font=ctk.CTkFont(family=THEME["font_family"], size=14, weight="bold"), text_color=THEME["text_main"]).pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkLabel(
            bak_card,
            text="Triggers native ADB full-system backup archive including APKs and application shared storage. Phone will prompt to confirm backup password on screen.",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            text_color=THEME["text_muted"]
        ).pack(anchor="w", padx=16, pady=(0, 10))

        btn_bak = ctk.CTkButton(
            bak_card,
            text="Generate Full ADB Backup (.ab)",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            fg_color="#0070BA",
            hover_color="#005ea6",
            height=34,
            command=self._start_full_adb_backup
        )
        btn_bak.pack(anchor="w", padx=16, pady=(0, 14))

    def _start_category_recovery(self, category: str):
        dest = filedialog.askdirectory(title=f"Select Destination Folder on PC for {category.upper()}")
        if not dest:
            return

        def _pull():
            messagebox.showinfo("Extraction Started", f"Extraction of {category} has started.\nPlease leave USB cable connected.")
            ok, msg, _ = self.adb.pull_category_media(category, dest)
            if ok:
                messagebox.showinfo("Extraction Complete", msg)
            else:
                messagebox.showerror("Extraction Failed", msg)

        threading.Thread(target=_pull, daemon=True).start()

    def _start_full_adb_backup(self):
        file_path = filedialog.asksaveasfilename(title="Save Android Backup", defaultextension=".ab", filetypes=[("Android Backup", "*.ab")])
        if file_path:
            def _bak():
                messagebox.showinfo("Prompt on Phone", "Please unlock your phone and tap 'Back up my data' when prompted on screen.")
                ok, msg = self.adb.backup_full_adb(file_path)
                if ok:
                    messagebox.showinfo("Success", f"Backup completed and saved to:\n{file_path}")
                else:
                    messagebox.showwarning("Notice", msg)
            threading.Thread(target=_bak, daemon=True).start()

    # =========================================================================
    # VIEW 6: Clean, Optimize & Storage TRIM
    # =========================================================================

    def show_optimize(self):
        self._highlight_nav("optimize")
        self._clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        h_box = ctk.CTkFrame(scroll, fg_color="transparent")
        h_box.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            h_box,
            text="⚡ Storage TRIM, Cache Cleaner & Defragmentation Suite",
            font=ctk.CTkFont(family=THEME["font_family"], size=20, weight="bold"),
            text_color=THEME["text_main"]
        ).pack(side="left")

        # Operations Grid
        tools = [
            (
                "🧹 Global Application Cache Trimmer",
                "Invokes native Android package manager cache trimmer to immediately reclaim disk space from app caches without losing user accounts or settings.",
                "Trim All App Caches",
                THEME["primary"],
                self._run_cache_trim
            ),
            (
                "💾 Solid-State NAND TRIM & Defragment (fstrim)",
                "Issues fstrim commands to /data, /cache, and /system partitions. Unmaps obsolete flash blocks, reduces NAND controller write amplification, and restores fast I/O speed.",
                "Execute fstrim /data & /cache",
                THEME["success"],
                self._run_storage_trim
            ),
            (
                "🗑️ Clean Temp Files & Tombstones",
                "Flushes old crash tombstones, ANR traces, and leftover files from /data/local/tmp that accumulate and waste phone storage.",
                "Clean Temporary Dumps",
                THEME["warning"],
                self._run_clean_temp
            ),
            (
                "🚀 ART Ahead-Of-Time Speed Optimization",
                "Forces the Android Runtime (ART) compiler to compile all application bytecode using 'speed' profile. Eliminates app launch stutters and lag.",
                "Compile ART Speed Profile",
                THEME["purple"],
                self._run_art_optimize
            ),
        ]

        for title, desc, btn_txt, color, cmd in tools:
            card = ctk.CTkFrame(scroll, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
            card.pack(fill="x", pady=(0, 12))

            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family=THEME["font_family"], size=14, weight="bold"), text_color=THEME["text_main"]).pack(anchor="w", padx=16, pady=(12, 4))
            ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(family=THEME["font_family"], size=12), text_color=THEME["text_secondary"], wraplength=880, justify="left").pack(anchor="w", padx=16, pady=(0, 10))

            btn = ctk.CTkButton(
                card,
                text=btn_txt,
                font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
                fg_color=color,
                height=32,
                command=cmd
            )
            btn.pack(anchor="w", padx=16, pady=(0, 12))

    def _run_cache_trim(self):
        def _trim():
            ok, msg = self.adb.clear_all_caches()
            self.after(0, lambda: messagebox.showinfo("Cache Cleaner", msg))
        threading.Thread(target=_trim, daemon=True).start()

    def _run_storage_trim(self):
        def _trim():
            ok, msg = self.adb.trim_storage_defragment()
            self.after(0, lambda: messagebox.showinfo("Storage TRIM (fstrim)", msg))
        threading.Thread(target=_trim, daemon=True).start()

    def _run_clean_temp(self):
        def _clean():
            ok, msg = self.adb.clean_temp_files()
            self.after(0, lambda: messagebox.showinfo("Temp Cleaner", msg))
        threading.Thread(target=_clean, daemon=True).start()

    def _run_art_optimize(self):
        def _opt():
            self.after(0, lambda: messagebox.showinfo("Compiling", "Optimizing application bytecode via ART. This may take 1-2 minutes..."))
            ok, msg = self.adb.speed_boost_art_optimize()
            self.after(0, lambda: messagebox.showinfo("ART Optimization Complete", msg))
        threading.Thread(target=_opt, daemon=True).start()

    # =========================================================================
    # VIEW 7: Remote & Screen Mirroring
    # =========================================================================

    def show_remote(self):
        self._highlight_nav("remote")
        self._clear_content()

        # Reset canvas image references
        self._canvas_img_id = None
        self._canvas_photo = None
        self.screen_render_rect = None

        container = ctk.CTkFrame(self.content_container, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # Header with Title and Streaming Controls
        h_box = ctk.CTkFrame(container, fg_color="transparent")
        h_box.pack(fill="x", pady=(0, 10))

        title_box = ctk.CTkFrame(h_box, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="🎮 Live Phone Screen & Interactive Remote Control",
            font=ctk.CTkFont(family=THEME["font_family"], size=20, weight="bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Live auto-streaming display • Direct touch clicks, swipes & gestures • Virtual hardware controls",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            text_color=THEME["text_muted"]
        ).pack(anchor="w")

        # Header Right Actions (Status pill, Pause/Resume, Sync, 60FPS Scrcpy Popout)
        ctrl_top = ctk.CTkFrame(h_box, fg_color="transparent")
        ctrl_top.pack(side="right")

        self.lbl_stream_badge = ctk.CTkLabel(
            ctrl_top,
            text="● LIVE STREAMING",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            text_color=THEME["success"]
        )
        self.lbl_stream_badge.pack(side="left", padx=(0, 8))

        self.btn_stream_toggle = ctk.CTkButton(
            ctrl_top,
            text="⏸️ Pause Stream",
            width=100,
            height=32,
            font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
            fg_color=THEME["bg_card_alt"],
            hover_color=THEME["border_highlight"],
            command=self._toggle_live_stream
        )
        self.btn_stream_toggle.pack(side="left", padx=4)

        self.btn_sync_frame = ctk.CTkButton(
            ctrl_top,
            text="🔄 Sync Screen",
            width=90,
            height=32,
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            fg_color=THEME["bg_card_alt"],
            hover_color=THEME["border_highlight"],
            command=lambda: self._trigger_quick_refresh(0)
        )
        self.btn_sync_frame.pack(side="left", padx=4)

        self.btn_scrcpy_popout = ctk.CTkButton(
            ctrl_top,
            text="⚡ Ultra 60FPS (Scrcpy)",
            height=32,
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self._launch_scrcpy_mirror
        )
        self.btn_scrcpy_popout.pack(side="left", padx=(6, 0))

        # Main 2-Column Responsive Workspace
        content_split = ctk.CTkFrame(container, fg_color="transparent")
        content_split.pack(fill="both", expand=True)
        content_split.grid_columnconfigure(0, weight=0, minsize=380)
        content_split.grid_columnconfigure(1, weight=1)
        content_split.grid_rowconfigure(0, weight=1)

        # -------------------------------------------------------------
        # Left Panel: Smartphone Frame Mockup + Interactive Live Canvas
        # -------------------------------------------------------------
        phone_card = ctk.CTkFrame(
            content_split,
            fg_color=THEME["bg_card"],
            border_width=1,
            border_color=THEME["border"],
            corner_radius=12
        )
        phone_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        phone_card.grid_rowconfigure(1, weight=1)
        phone_card.grid_columnconfigure(0, weight=1)

        # Top Phone Bezel Mockup
        phone_top_bezel = ctk.CTkFrame(phone_card, fg_color="transparent", height=18)
        phone_top_bezel.grid(row=0, column=0, sticky="ew", padx=14, pady=(8, 4))

        earpiece = ctk.CTkFrame(phone_top_bezel, fg_color="#334155", width=46, height=4, corner_radius=2)
        earpiece.pack(side="top", pady=2)

        # Interactive Canvas for Direct Touch & Screen View
        self.phone_canvas = tk.Canvas(
            phone_card,
            bg="#06090F",
            highlightthickness=1,
            highlightbackground=THEME["border"],
            cursor="hand2",
            takefocus=1
        )
        self.phone_canvas.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 6))

        # Canvas Touch & Gesture Bindings
        self.phone_canvas.bind("<ButtonPress-1>", self._on_screen_touch_press)
        self.phone_canvas.bind("<B1-Motion>", self._on_screen_touch_motion)
        self.phone_canvas.bind("<ButtonRelease-1>", self._on_screen_touch_release)
        self.phone_canvas.bind("<MouseWheel>", self._on_screen_wheel)
        self.phone_canvas.bind("<Button-3>", self._on_screen_right_click)
        self.phone_canvas.bind("<Button-2>", self._on_screen_middle_click)
        self.phone_canvas.bind("<Key>", self._on_screen_keypress)
        self.phone_canvas.bind("<Configure>", self._on_canvas_configure)

        # Bottom Android Nav Bar (Physical button simulation)
        nav_bar = ctk.CTkFrame(phone_card, fg_color="#0F172A", height=38, corner_radius=8)
        nav_bar.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 6))
        nav_bar.grid_columnconfigure((0, 1, 2), weight=1)

        btn_nav_back = ctk.CTkButton(
            nav_bar,
            text="◀  BACK",
            font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
            fg_color="transparent",
            hover_color="#1E293B",
            text_color=THEME["text_secondary"],
            height=30,
            command=lambda: [self.adb.send_keyevent_async(4), self._trigger_quick_refresh(120)]
        )
        btn_nav_back.grid(row=0, column=0, padx=2, pady=4, sticky="ew")

        btn_nav_home = ctk.CTkButton(
            nav_bar,
            text="●  HOME",
            font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
            fg_color="transparent",
            hover_color="#1E293B",
            text_color=THEME["text_secondary"],
            height=30,
            command=lambda: [self.adb.send_keyevent_async(3), self._trigger_quick_refresh(120)]
        )
        btn_nav_home.grid(row=0, column=1, padx=2, pady=4, sticky="ew")

        btn_nav_recents = ctk.CTkButton(
            nav_bar,
            text="■  RECENTS",
            font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
            fg_color="transparent",
            hover_color="#1E293B",
            text_color=THEME["text_secondary"],
            height=30,
            command=lambda: [self.adb.send_keyevent_async(187), self._trigger_quick_refresh(120)]
        )
        btn_nav_recents.grid(row=0, column=2, padx=2, pady=4, sticky="ew")

        # Quick Action Toolbar beneath Nav Bar
        tools_row = ctk.CTkFrame(phone_card, fg_color="transparent")
        tools_row.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 10))

        btn_notifs = ctk.CTkButton(
            tools_row,
            text="🔔 Notifications",
            font=ctk.CTkFont(family=THEME["font_family"], size=10),
            fg_color=THEME["bg_card_alt"],
            hover_color=THEME["border_highlight"],
            height=28,
            command=self._expand_notifications
        )
        btn_notifs.pack(side="left", expand=True, fill="x", padx=(0, 3))

        btn_qs = ctk.CTkButton(
            tools_row,
            text="⚙️ Quick Settings",
            font=ctk.CTkFont(family=THEME["font_family"], size=10),
            fg_color=THEME["bg_card_alt"],
            hover_color=THEME["border_highlight"],
            height=28,
            command=self._expand_settings
        )
        btn_qs.pack(side="left", expand=True, fill="x", padx=3)

        btn_save_shot = ctk.CTkButton(
            tools_row,
            text="💾 Save PNG",
            font=ctk.CTkFont(family=THEME["font_family"], size=10),
            fg_color=THEME["bg_card_alt"],
            hover_color=THEME["border_highlight"],
            height=28,
            command=self._save_screenshot_dialog
        )
        btn_save_shot.pack(side="left", expand=True, fill="x", padx=(3, 0))

        # -------------------------------------------------------------
        # Right Panel: Hardware Keypad, Quick Controls, Typer & Guide
        # -------------------------------------------------------------
        remote_card = ctk.CTkFrame(
            content_split,
            fg_color=THEME["bg_card"],
            border_width=1,
            border_color=THEME["border"],
            corner_radius=12
        )
        remote_card.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        scroll_right = ctk.CTkScrollableFrame(remote_card, fg_color="transparent")
        scroll_right.pack(fill="both", expand=True, padx=12, pady=12)

        # 1. Virtual Hardware Keypad
        ctk.CTkLabel(
            scroll_right,
            text="🕹️ Virtual Hardware Keypad",
            font=ctk.CTkFont(family=THEME["font_family"], size=14, weight="bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(0, 8))

        key_grid = ctk.CTkFrame(scroll_right, fg_color="transparent")
        key_grid.pack(fill="x", pady=(0, 14))
        key_grid.grid_columnconfigure((0, 1, 2), weight=1)

        keys = [
            ("Power (Wake/Sleep)", 26, THEME["danger"]),
            ("Unlock / Menu", 82, THEME["purple"]),
            ("Home Button", 3, THEME["primary"]),
            ("Back Button", 4, THEME["bg_card_alt"]),
            ("App Switcher", 187, THEME["bg_card_alt"]),
            ("Enter / Confirm", 66, THEME["success"]),
            ("Volume +", 24, THEME["bg_card_alt"]),
            ("Volume -", 25, THEME["bg_card_alt"]),
            ("Mute Volume", 164, THEME["bg_card_alt"]),
        ]

        for idx, (label, code, color) in enumerate(keys):
            r = idx // 3
            c = idx % 3
            btn = ctk.CTkButton(
                key_grid,
                text=label,
                font=ctk.CTkFont(family=THEME["font_family"], size=11),
                fg_color=color,
                height=34,
                command=lambda kc=code: [self.adb.send_keyevent_async(kc), self._trigger_quick_refresh(120)]
            )
            btn.grid(row=r, column=c, padx=4, pady=4, sticky="nsew")

        # 2. System Quick Controls
        ctk.CTkLabel(
            scroll_right,
            text="⚡ System Quick Actions",
            font=ctk.CTkFont(family=THEME["font_family"], size=14, weight="bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(4, 8))

        sys_actions_box = ctk.CTkFrame(scroll_right, fg_color="transparent")
        sys_actions_box.pack(fill="x", pady=(0, 14))
        sys_actions_box.grid_columnconfigure((0, 1), weight=1)

        btn_wake_unlock = ctk.CTkButton(
            sys_actions_box,
            text="🔓 Wake & Dismiss Lock",
            font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            height=32,
            command=lambda: [self.adb.attempt_force_usb_debugging(), self._trigger_quick_refresh(200)]
        )
        btn_wake_unlock.grid(row=0, column=0, padx=4, pady=3, sticky="ew")

        btn_rotate = ctk.CTkButton(
            sys_actions_box,
            text="🔄 Rotate Display (90°)",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            fg_color=THEME["bg_card_alt"],
            hover_color=THEME["border_highlight"],
            height=32,
            command=self._rotate_screen
        )
        btn_rotate.grid(row=0, column=1, padx=4, pady=3, sticky="ew")

        btn_paste_clip = ctk.CTkButton(
            sys_actions_box,
            text="📋 Paste PC Clipboard to Phone",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            fg_color=THEME["bg_card_alt"],
            hover_color=THEME["border_highlight"],
            height=32,
            command=self._paste_clipboard_to_phone
        )
        btn_paste_clip.grid(row=1, column=0, padx=4, pady=3, sticky="ew")

        btn_sleep_screen = ctk.CTkButton(
            sys_actions_box,
            text="⏹️ Toggle Screen On/Off",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            fg_color=THEME["bg_card_alt"],
            hover_color=THEME["border_highlight"],
            height=32,
            command=self._turn_screen_off
        )
        btn_sleep_screen.grid(row=1, column=1, padx=4, pady=3, sticky="ew")

        # 3. Quick Text Input Typer
        ctk.CTkLabel(
            scroll_right,
            text="⌨️ Type Text into Active Phone Field",
            font=ctk.CTkFont(family=THEME["font_family"], size=14, weight="bold"),
            text_color=THEME["text_main"]
        ).pack(anchor="w", pady=(4, 6))

        type_box = ctk.CTkFrame(scroll_right, fg_color="transparent")
        type_box.pack(fill="x", pady=(0, 14))

        self.type_entry = ctk.CTkEntry(
            type_box,
            placeholder_text="Type text here and hit 'Send' or Press Enter to type on phone...",
            height=36,
            fg_color=THEME["bg_input"],
            border_color=THEME["border"]
        )
        self.type_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.type_entry.bind("<Return>", lambda e: self._send_keyboard_text())

        btn_send_type = ctk.CTkButton(
            type_box,
            text="Send",
            width=70,
            height=36,
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._send_keyboard_text
        )
        btn_send_type.pack(side="right")

        # 4. Interactive Touch Controls Guide Card
        guide_card = ctk.CTkFrame(
            scroll_right,
            fg_color=THEME["bg_card_alt"],
            border_width=1,
            border_color=THEME["border"],
            corner_radius=10
        )
        guide_card.pack(fill="x", pady=(6, 0))

        ctk.CTkLabel(
            guide_card,
            text="💡 Interactive Screen Controls Guide",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            text_color=THEME["accent_cyan"]
        ).pack(anchor="w", padx=14, pady=(10, 6))

        guide_items = [
            ("👆 Left Click", "Taps directly on app icons, buttons, menus, links & toggles on the phone screen."),
            ("🖐️ Click & Drag", "Swipes up, down, left, right to scroll feeds, switch home pages, or pull notifications."),
            ("📜 Mouse Wheel", "Instantly scrolls content up and down anywhere on the screen."),
            ("🔙 Right Click", "Simulates Android BACK button instantly on click."),
            ("🏠 Middle Click", "Simulates Android HOME button instantly on click."),
            ("⌨️ Keyboard Focus", "Click the screen and type with PC keyboard directly into text boxes on phone."),
            ("⚡ Ultra 60FPS", "Click 'Ultra 60FPS (Scrcpy)' at top right for hardware-accelerated zero-latency mirror with audio.")
        ]

        for title, desc in guide_items:
            item_box = ctk.CTkFrame(guide_card, fg_color="transparent")
            item_box.pack(fill="x", padx=14, pady=2)
            ctk.CTkLabel(
                item_box,
                text=title + ":",
                font=ctk.CTkFont(family=THEME["font_family"], size=11, weight="bold"),
                text_color=THEME["text_main"],
                width=120,
                anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                item_box,
                text=desc,
                font=ctk.CTkFont(family=THEME["font_family"], size=11),
                text_color=THEME["text_secondary"],
                anchor="w",
                wraplength=480,
                justify="left"
            ).pack(side="left", fill="x", expand=True)

        guide_spacer = ctk.CTkLabel(guide_card, text="", height=4)
        guide_spacer.pack()

        # Start live stream automatically!
        self._ensure_live_stream_started()

    # =========================================================================
    # Live Screen Streaming & Direct Touch Input Engine
    # =========================================================================

    def _ensure_live_stream_started(self):
        """Starts background live stream worker if not already running."""
        self.live_stream_active = True
        self.live_stream_paused = False
        if not self.live_stream_thread or not self.live_stream_thread.is_alive():
            self.live_stream_thread = threading.Thread(target=self._live_stream_loop, daemon=True)
            self.live_stream_thread.start()
        self._update_stream_badge(True)

    def _toggle_live_stream(self):
        """Toggles between pause and resume for the live screen stream."""
        self.live_stream_paused = not self.live_stream_paused
        if not self.live_stream_paused:
            self._ensure_live_stream_started()
            if hasattr(self, "btn_stream_toggle") and self.btn_stream_toggle.winfo_exists():
                self.btn_stream_toggle.configure(text="⏸️ Pause Stream", fg_color=THEME["bg_card_alt"])
            self._update_stream_badge(True)
            self._trigger_quick_refresh(0)
        else:
            if hasattr(self, "btn_stream_toggle") and self.btn_stream_toggle.winfo_exists():
                self.btn_stream_toggle.configure(text="▶️ Resume Stream", fg_color=THEME["primary"])
            self._update_stream_badge(False)

    def _update_stream_badge(self, is_live: bool, fps_str: str = ""):
        if hasattr(self, "lbl_stream_badge") and self.lbl_stream_badge.winfo_exists():
            if is_live and not self.live_stream_paused:
                txt = f"● LIVE ({fps_str})" if fps_str else "● LIVE STREAMING"
                self.lbl_stream_badge.configure(text=txt, text_color=THEME["success"])
            elif self.live_stream_paused:
                self.lbl_stream_badge.configure(text="⏸️ PAUSED", text_color=THEME["warning"])
            else:
                self.lbl_stream_badge.configure(text="● OFFLINE", text_color=THEME["text_muted"])

    def _live_stream_loop(self):
        """Continuously streams screen frames from connected device silently."""
        fps_count = 0
        fps_timer = time.time()

        while self.live_stream_active:
            if self.live_stream_paused or self.current_view_name != "remote":
                time.sleep(0.25)
                continue

            conn = self.status_data.get("connection", "DISCONNECTED")
            if conn not in ["AUTHORIZED", "device"]:
                self.after(0, self._render_stream_placeholder, "📱 Waiting for Authorized Device...\nConnect phone and tap 'Allow USB Debugging' on screen.")
                time.sleep(1.0)
                continue

            try:
                self._is_capturing_stream_frame = True
                raw_bytes = self.adb.capture_screen_bytes()
                self._is_capturing_stream_frame = False

                if raw_bytes and self.live_stream_active and not self.live_stream_paused and self.current_view_name == "remote":
                    img = Image.open(io.BytesIO(raw_bytes))

                    fps_count += 1
                    elapsed = time.time() - fps_timer
                    fps_val = self.stream_fps
                    if elapsed >= 1.0:
                        fps_val = round(fps_count / elapsed, 1)
                        self.stream_fps = fps_val
                        fps_count = 0
                        fps_timer = time.time()

                    self.after(0, self._render_live_stream_frame, img, f"{fps_val} FPS")
                else:
                    time.sleep(0.08)
            except Exception:
                self._is_capturing_stream_frame = False
                time.sleep(0.15)

            # Smooth pacing
            time.sleep(0.04)

    def _render_live_stream_frame(self, img: Image.Image, fps_str: str = ""):
        """Renders live PIL Image frame to the Canvas proportionally."""
        if not hasattr(self, "phone_canvas") or not self.phone_canvas.winfo_exists():
            return

        self.current_screen_img = img
        self.device_screen_size = (img.width, img.height)
        self._update_stream_badge(True, fps_str)

        canvas_w = self.phone_canvas.winfo_width()
        canvas_h = self.phone_canvas.winfo_height()
        if canvas_w < 50 or canvas_h < 50:
            canvas_w = 320
            canvas_h = 560

        # Scale image proportionally to fit canvas bounds
        scale = min((canvas_w - 6) / img.width, (canvas_h - 6) / img.height)
        target_w = max(1, int(img.width * scale))
        target_h = max(1, int(img.height * scale))

        scaled_img = img.resize((target_w, target_h), Image.Resampling.BILINEAR)
        photo = ImageTk.PhotoImage(scaled_img)
        self._canvas_photo = photo  # Keep reference to prevent GC

        center_x = canvas_w // 2
        center_y = canvas_h // 2
        offset_x = center_x - (target_w // 2)
        offset_y = center_y - (target_h // 2)
        self.screen_render_rect = (offset_x, offset_y, target_w, target_h)

        # Clear placeholder if present
        self.phone_canvas.delete("placeholder")

        if self._canvas_img_id is None:
            self._canvas_img_id = self.phone_canvas.create_image(
                center_x, center_y,
                image=photo,
                anchor="center",
                tags="screen_frame"
            )
        else:
            self.phone_canvas.itemconfig(self._canvas_img_id, image=photo)
            self.phone_canvas.coords(self._canvas_img_id, center_x, center_y)

    def _render_stream_placeholder(self, msg: str):
        """Draws offline / waiting message on the canvas."""
        if not hasattr(self, "phone_canvas") or not self.phone_canvas.winfo_exists():
            return
        self._update_stream_badge(False)
        if self._canvas_img_id:
            self.phone_canvas.delete(self._canvas_img_id)
            self._canvas_img_id = None
        self.phone_canvas.delete("placeholder")
        cw = self.phone_canvas.winfo_width() or 320
        ch = self.phone_canvas.winfo_height() or 560
        self.phone_canvas.create_text(
            cw // 2, ch // 2,
            text=msg,
            fill=THEME["text_secondary"],
            font=(THEME["font_family"], 11),
            justify="center",
            tags="placeholder"
        )

    def _on_canvas_configure(self, event):
        """Handles canvas resizing to re-scale the active frame."""
        if self.current_screen_img:
            fps_lbl = f"{self.stream_fps} FPS" if self.stream_fps else ""
            self._render_live_stream_frame(self.current_screen_img, fps_lbl)

    def _on_screen_touch_press(self, event):
        """Records initial touch press coordinate for tap vs swipe calculation."""
        if not self.screen_render_rect or not self.device_screen_size:
            return
        ox, oy, rw, rh = self.screen_render_rect
        dw, dh = self.device_screen_size

        if ox <= event.x <= ox + rw and oy <= event.y <= oy + rh:
            phone_x = int((event.x - ox) * (dw / rw))
            phone_y = int((event.y - oy) * (dh / rh))
            phone_x = max(0, min(dw - 1, phone_x))
            phone_y = max(0, min(dh - 1, phone_y))
            self.touch_start_canvas = (event.x, event.y)
            self.touch_start_phone = (phone_x, phone_y)
            self.touch_start_time = time.time()
            self.phone_canvas.focus_set()

    def _on_screen_touch_motion(self, event):
        """Shows visual drag line while dragging across screen."""
        if self.touch_start_canvas:
            self.phone_canvas.delete("drag_line")
            self.phone_canvas.create_line(
                self.touch_start_canvas[0], self.touch_start_canvas[1],
                event.x, event.y,
                fill="#38BDF8", width=3, tags="drag_line"
            )

    def _on_screen_touch_release(self, event):
        """Calculates touch gesture (tap vs swipe) and dispatches to Android."""
        self.phone_canvas.delete("drag_line")
        if not self.touch_start_canvas or not self.touch_start_phone or not self.screen_render_rect or not self.device_screen_size:
            return

        ox, oy, rw, rh = self.screen_render_rect
        dw, dh = self.device_screen_size

        clamped_x = max(ox, min(ox + rw, event.x))
        clamped_y = max(oy, min(oy + rh, event.y))
        phone_x = int((clamped_x - ox) * (dw / rw))
        phone_y = int((clamped_y - oy) * (dh / rh))
        phone_x = max(0, min(dw - 1, phone_x))
        phone_y = max(0, min(dh - 1, phone_y))

        dx = event.x - self.touch_start_canvas[0]
        dy = event.y - self.touch_start_canvas[1]
        dist = (dx**2 + dy**2)**0.5
        dt = time.time() - self.touch_start_time

        if dist < 10 and dt < 0.45:
            # Single Tap on icon / button
            self.adb.send_screen_tap_async(phone_x, phone_y)
            self._show_touch_ripple(event.x, event.y, color="#3DDC84")
            self._trigger_quick_refresh(120)
        elif dist < 10 and dt >= 0.45:
            # Long Press
            self.adb.send_screen_swipe_async(phone_x, phone_y, phone_x, phone_y, duration_ms=650)
            self._show_touch_ripple(event.x, event.y, color="#F59E0B")
            self._trigger_quick_refresh(220)
        else:
            # Swipe / Drag gesture
            dur = int(min(max(dt * 1000, 120), 800))
            self.adb.send_screen_swipe_async(self.touch_start_phone[0], self.touch_start_phone[1], phone_x, phone_y, duration_ms=dur)
            self._show_touch_ripple(event.x, event.y, color="#38BDF8")
            self._trigger_quick_refresh(180)

        self.touch_start_canvas = None
        self.touch_start_phone = None

    def _on_screen_wheel(self, event):
        """Translates mouse wheel scroll into vertical swipe gestures."""
        if not self.device_screen_size:
            return
        dw, dh = self.device_screen_size
        cx = dw // 2
        cy = dh // 2
        step = int(dh * 0.28)

        if event.delta < 0:
            # Scroll down page (swipe finger up)
            self.adb.send_screen_swipe_async(cx, cy + step, cx, cy - step, duration_ms=180)
        else:
            # Scroll up page (swipe finger down)
            self.adb.send_screen_swipe_async(cx, cy - step, cx, cy + step, duration_ms=180)

        self._trigger_quick_refresh(180)

    def _on_screen_right_click(self, event):
        """Right click triggers Android BACK button."""
        self.adb.send_keyevent_async(4)  # KEYCODE_BACK
        self._show_touch_ripple(event.x, event.y, color="#F43F5E")
        self._trigger_quick_refresh(140)

    def _on_screen_middle_click(self, event):
        """Middle click triggers Android HOME button."""
        self.adb.send_keyevent_async(3)  # KEYCODE_HOME
        self._show_touch_ripple(event.x, event.y, color="#38BDF8")
        self._trigger_quick_refresh(140)

    def _on_screen_keypress(self, event):
        """Direct keyboard input into active phone field while focused on canvas."""
        if event.keysym == "BackSpace":
            self.adb.send_keyevent_async(67)
            self._trigger_quick_refresh(100)
        elif event.keysym in ["Return", "KP_Enter"]:
            self.adb.send_keyevent_async(66)
            self._trigger_quick_refresh(140)
        elif event.keysym == "Escape":
            self.adb.send_keyevent_async(4)
            self._trigger_quick_refresh(140)
        elif event.keysym == "space":
            self.adb.send_keyevent_async(62)
            self._trigger_quick_refresh(100)
        elif event.char and event.char.isprintable():
            self.adb.send_text_input(event.char)
            self._trigger_quick_refresh(100)

    def _show_touch_ripple(self, x: int, y: int, color: str = "#3DDC84"):
        """Animates a quick glowing ripple ring under cursor for tactile touch feedback."""
        if not hasattr(self, "phone_canvas") or not self.phone_canvas.winfo_exists():
            return
        r = 6
        ripple = self.phone_canvas.create_oval(x - r, y - r, x + r, y + r, outline=color, width=2)

        def _expand(step=1):
            if not hasattr(self, "phone_canvas") or not self.phone_canvas.winfo_exists():
                return
            if step < 4:
                nr = r + step * 5
                self.phone_canvas.coords(ripple, x - nr, y - nr, x + nr, y + nr)
                self.after(35, lambda: _expand(step + 1))
            else:
                self.phone_canvas.delete(ripple)

        self.after(30, _expand)

    def _trigger_quick_refresh(self, delay_ms: int = 150):
        """Dispatches an immediate frame capture right after touch or button action."""
        if self._quick_refresh_scheduled:
            return
        self._quick_refresh_scheduled = True

        def _fetch_frame():
            self._quick_refresh_scheduled = False
            if self.live_stream_active and not self.live_stream_paused and self.current_view_name == "remote":
                def _grab():
                    raw_bytes = self.adb.capture_screen_bytes()
                    if raw_bytes:
                        try:
                            img = Image.open(io.BytesIO(raw_bytes))
                            fps_lbl = f"{self.stream_fps} FPS" if self.stream_fps else ""
                            self.after(0, self._render_live_stream_frame, img, fps_lbl)
                        except Exception:
                            pass
                threading.Thread(target=_grab, daemon=True).start()

        self.after(delay_ms, _fetch_frame)

    def _launch_scrcpy_mirror(self):
        """Launches full hardware-accelerated 60FPS Scrcpy Mirror with audio."""
        ok, msg = self.adb.launch_scrcpy(stay_awake=True, turn_screen_off=False, always_on_top=True)
        if ok:
            messagebox.showinfo(
                "Ultra 60FPS Scrcpy Mirror",
                f"{msg}\n\n"
                "Features Active:\n"
                "• 60 FPS hardware-accelerated fluid video stream.\n"
                "• Ultra low-latency mouse clicks, drags & keyboard typing.\n"
                "• Phone audio forwarded to PC speakers.\n"
                "• Drag & drop APK to install directly.\n"
                "• Drag & drop files to push to device storage."
            )
        else:
            messagebox.showerror("Scrcpy Launch Failed", msg)

    def _expand_notifications(self):
        """Pulls down Android notification panel."""
        self.adb.run_shell("cmd statusbar expand-notifications")
        self._trigger_quick_refresh(140)

    def _expand_settings(self):
        """Expands Android quick settings shade."""
        self.adb.run_shell("cmd statusbar expand-settings")
        self._trigger_quick_refresh(140)

    def _rotate_screen(self):
        """Toggles Android screen orientation (0, 90, 180, 270)."""
        code, out, _ = self.adb.run_shell("settings get system user_rotation")
        curr_rot = int(out.strip()) if code == 0 and out.strip().isdigit() else 0
        next_rot = (curr_rot + 1) % 4
        self.adb.run_shell("settings put system accelerometer_rotation 0")
        self.adb.run_shell(f"settings put system user_rotation {next_rot}")
        self._trigger_quick_refresh(250)

    def _paste_clipboard_to_phone(self):
        """Copies text from PC clipboard and types it into active field on phone."""
        try:
            clip_text = self.clipboard_get()
            if clip_text:
                self.adb.send_text_input(clip_text)
                self._trigger_quick_refresh(140)
        except Exception:
            pass

    def _turn_screen_off(self):
        """Toggles phone screen power state."""
        self.adb.send_keyevent_async(26)  # KEYCODE_POWER
        self._trigger_quick_refresh(200)

    def _save_screenshot_dialog(self):
        """Saves current live screen frame as a PNG file to PC."""
        save_path = filedialog.asksaveasfilename(
            title="Save Screen Screenshot",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")]
        )
        if save_path:
            if self.current_screen_img:
                try:
                    self.current_screen_img.save(save_path)
                    messagebox.showinfo("Screenshot Saved", f"Saved successfully to:\n{save_path}")
                    return
                except Exception:
                    pass
            ok, res = self.adb.capture_screenshot(save_path)
            if ok:
                messagebox.showinfo("Screenshot Saved", f"Saved successfully to:\n{save_path}")
            else:
                messagebox.showerror("Error Saving Screenshot", res)

    def _send_keyboard_text(self):
        """Sends text input from entry box to active phone field."""
        txt = self.type_entry.get().strip()
        if txt:
            self.adb.send_text_input(txt)
            self.type_entry.delete(0, "end")
            self._trigger_quick_refresh(120)

    # =========================================================================
    # VIEW 8: Silent ADB Terminal Console
    # =========================================================================

    # =========================================================================
    # VIEW 8: Silent ADB Terminal Console & Vast Command Deck
    # =========================================================================

    def show_terminal(self):
        self._highlight_nav("terminal")
        self._clear_content()

        container = ctk.CTkFrame(self.content_container, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # 2-Column Responsive Workspace:
        # Col 0: Command Library Dock (width ~380px)
        # Col 1: Interactive Terminal Console & Output (expanding)
        container.grid_columnconfigure(0, weight=0, minsize=380)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # -------------------------------------------------------------
        # Left Panel: Vast Command Library Dock
        # -------------------------------------------------------------
        deck_frame = ctk.CTkFrame(container, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=12)
        deck_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        deck_frame.grid_rowconfigure(3, weight=1)
        deck_frame.grid_columnconfigure(0, weight=1)

        # Header with Count Badge
        deck_hdr = ctk.CTkFrame(deck_frame, fg_color="transparent")
        deck_hdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))

        ctk.CTkLabel(
            deck_hdr,
            text="📚 Command Deck",
            font=ctk.CTkFont(family=THEME["font_family"], size=15, weight="bold"),
            text_color=THEME["text_main"]
        ).pack(side="left")

        self.cmd_count_badge = ctk.CTkLabel(
            deck_hdr,
            text=f"{len(VAST_COMMANDS)} Ready",
            font=ctk.CTkFont(family=THEME["font_mono"], size=10, weight="bold"),
            fg_color=THEME["bg_card_alt"],
            text_color=THEME["android_green"],
            corner_radius=6,
            padx=8,
            pady=2
        )
        self.cmd_count_badge.pack(side="right")

        # Category Selector Dropdown
        self.category_var = ctk.StringVar(value=self.current_cmd_category)
        cat_menu = ctk.CTkOptionMenu(
            deck_frame,
            values=COMMAND_CATEGORIES,
            variable=self.category_var,
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            fg_color=THEME["bg_card_alt"],
            button_color=THEME["primary"],
            button_hover_color=THEME["primary_hover"],
            command=self._on_command_category_changed
        )
        cat_menu.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))

        # Real-time Search / Filter Input
        self.cmd_search_entry = ctk.CTkEntry(
            deck_frame,
            placeholder_text="🔍 Filter 60+ commands (e.g. battery, dpi)...",
            height=32,
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            fg_color=THEME["bg_input"],
            border_color=THEME["border"]
        )
        self.cmd_search_entry.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 10))
        self.cmd_search_entry.bind("<KeyRelease>", lambda e: self._filter_command_cards())

        # Scrollable Command List
        self.cmd_list_scroll = ctk.CTkScrollableFrame(deck_frame, fg_color="transparent")
        self.cmd_list_scroll.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Render initial list
        self._render_command_cards(VAST_COMMANDS)

        # -------------------------------------------------------------
        # Right Panel: Interactive Terminal Console
        # -------------------------------------------------------------
        console_frame = ctk.CTkFrame(container, fg_color="transparent")
        console_frame.grid(row=0, column=1, sticky="nsew")
        console_frame.grid_rowconfigure(1, weight=1)
        console_frame.grid_columnconfigure(0, weight=1)

        # Top Control Toolbar
        top_bar = ctk.CTkFrame(console_frame, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10, height=44)
        top_bar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        dev_serial = self.adb.selected_device or "Active Device"
        conn_state = self.status_data.get("connection", "DISCONNECTED")
        pill_color = THEME["success"] if conn_state == "AUTHORIZED" else (THEME["warning"] if conn_state == "UNAUTHORIZED" else THEME["danger"])

        dev_box = ctk.CTkFrame(top_bar, fg_color="transparent")
        dev_box.pack(side="left", padx=12, pady=6)

        ctk.CTkLabel(dev_box, text="●", text_color=pill_color, font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 4))
        self.term_dev_lbl = ctk.CTkLabel(
            dev_box,
            text=f"Target: {dev_serial} ({conn_state})",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            text_color=THEME["text_main"]
        )
        self.term_dev_lbl.pack(side="left")

        # Action Buttons
        actions_bar = ctk.CTkFrame(top_bar, fg_color="transparent")
        actions_bar.pack(side="right", padx=10, pady=6)

        btn_clear = ctk.CTkButton(
            actions_bar,
            text="🧹 Clear",
            width=70,
            height=28,
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            fg_color=THEME["bg_card_alt"],
            hover_color=THEME["border_highlight"],
            command=self._clear_terminal_output
        )
        btn_clear.pack(side="left", padx=3)

        btn_copy = ctk.CTkButton(
            actions_bar,
            text="📋 Copy",
            width=70,
            height=28,
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            fg_color=THEME["bg_card_alt"],
            hover_color=THEME["border_highlight"],
            command=self._copy_terminal_output
        )
        btn_copy.pack(side="left", padx=3)

        btn_save = ctk.CTkButton(
            actions_bar,
            text="💾 Save Log",
            width=80,
            height=28,
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            fg_color=THEME["bg_card_alt"],
            hover_color=THEME["border_highlight"],
            command=self._save_terminal_log
        )
        btn_save.pack(side="left", padx=3)

        btn_restart = ctk.CTkButton(
            actions_bar,
            text="🔄 Restart ADB",
            width=95,
            height=28,
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._restart_adb_from_term
        )
        btn_restart.pack(side="left", padx=3)

        # Terminal Textbox
        self.term_output = ctk.CTkTextbox(
            console_frame,
            fg_color="#05080E",
            text_color="#10B981", # Hacker Green
            font=ctk.CTkFont(family=THEME["font_mono"], size=12),
            border_width=1,
            border_color=THEME["border"],
            corner_radius=10,
            wrap="word"
        )
        self.term_output.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        banner = (
            "===============================================================================\n"
            "               MACTECH ANDROID TOOL v2.2 - SILENT ADB TERMINAL CONSOLE         \n"
            "               MacTech Solutions Lab • 100% Background Execution (Zero Flash)  \n"
            "===============================================================================\n"
            "Type any shell or ADB command below (e.g. 'getprop', 'adb devices', 'df -h')   \n"
            "Or click any command in the vast Command Deck on the left to run instantly.    \n"
            "Use UP and DOWN arrow keys in the prompt to navigate your command history.     \n\n"
        )
        self.term_output.insert("end", banner)

        # Bottom Input Dock
        bottom_dock = ctk.CTkFrame(console_frame, fg_color="transparent")
        bottom_dock.grid(row=2, column=0, sticky="ew")

        # Command Entry Bar
        input_bar = ctk.CTkFrame(bottom_dock, fg_color="transparent")
        input_bar.pack(fill="x", pady=(0, 6))

        prompt_lbl = ctk.CTkLabel(
            input_bar,
            text="android:~$",
            font=ctk.CTkFont(family=THEME["font_mono"], size=13, weight="bold"),
            text_color=THEME["accent_cyan"],
            width=80,
            anchor="w"
        )
        prompt_lbl.pack(side="left", padx=(4, 6))

        self.term_input = ctk.CTkEntry(
            input_bar,
            placeholder_text="Enter command (e.g., pm list packages, cat /proc/meminfo, reboot recovery)...",
            height=38,
            fg_color=THEME["bg_input"],
            border_color=THEME["border"],
            font=ctk.CTkFont(family=THEME["font_mono"], size=12)
        )
        self.term_input.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.term_input.bind("<Return>", lambda e: self._execute_terminal_input())
        self.term_input.bind("<Up>", self._history_prev)
        self.term_input.bind("<Down>", self._history_next)

        btn_run = ctk.CTkButton(
            input_bar,
            text="▶ Execute",
            width=95,
            height=38,
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            command=self._execute_terminal_input
        )
        btn_run.pack(side="right")

        # Quick Action Pills Row
        pills_bar = ctk.CTkFrame(bottom_dock, fg_color="transparent")
        pills_bar.pack(fill="x")

        quick_pills = [
            ("dumpsys battery", "dumpsys battery"),
            ("df -h", "df -h"),
            ("getprop", "getprop"),
            ("top -n 1", "top -n 1 -m 6"),
            ("ps -A", "ps -A"),
            ("/proc/meminfo", "cat /proc/meminfo"),
            ("/proc/cpuinfo", "cat /proc/cpuinfo"),
            ("logcat -d", "logcat -d -t 50")
        ]

        for label, cmd_str in quick_pills:
            p_btn = ctk.CTkButton(
                pills_bar,
                text=label,
                font=ctk.CTkFont(family=THEME["font_mono"], size=11),
                fg_color=THEME["bg_card"],
                hover_color=THEME["border_highlight"],
                height=26,
                command=lambda c=cmd_str: self._run_quick_cmd(c)
            )
            p_btn.pack(side="left", padx=3)

    def _on_command_category_changed(self, category: str):
        self.current_cmd_category = category
        self._filter_command_cards()

    def _filter_command_cards(self):
        query = self.cmd_search_entry.get().strip() if hasattr(self, 'cmd_search_entry') else ""
        category = self.category_var.get() if hasattr(self, 'category_var') else "All Commands"
        filtered = search_commands(query, category)
        self._render_command_cards(filtered)
        if hasattr(self, 'cmd_count_badge'):
            self.cmd_count_badge.configure(text=f"{len(filtered)} Found")

    def _render_command_cards(self, commands_list: List[Dict[str, str]]):
        for widget in self.cmd_list_scroll.winfo_children():
            widget.destroy()

        if not commands_list:
            ctk.CTkLabel(
                self.cmd_list_scroll,
                text="No matching commands found.",
                font=ctk.CTkFont(family=THEME["font_family"], size=12),
                text_color=THEME["text_muted"]
            ).pack(pady=20)
            return

        level_colors = {
            "safe": THEME["success"],
            "medium": THEME["warning"],
            "advanced": THEME["danger"]
        }

        for item in commands_list:
            card = ctk.CTkFrame(
                self.cmd_list_scroll,
                fg_color=THEME["bg_card_alt"],
                border_width=1,
                border_color=THEME["border"],
                corner_radius=8
            )
            card.pack(fill="x", pady=4, padx=2)

            # Title & Level Badge
            hdr = ctk.CTkFrame(card, fg_color="transparent")
            hdr.pack(fill="x", padx=10, pady=(8, 2))

            ctk.CTkLabel(
                hdr,
                text=item["name"],
                font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
                text_color=THEME["text_main"],
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

            level = item.get("level", "safe")
            badge_color = level_colors.get(level, THEME["success"])
            ctk.CTkLabel(
                hdr,
                text=level.upper(),
                font=ctk.CTkFont(family=THEME["font_mono"], size=9, weight="bold"),
                text_color=badge_color,
                fg_color=THEME["bg_card"],
                corner_radius=4,
                padx=6,
                pady=1
            ).pack(side="right")

            # Description
            ctk.CTkLabel(
                card,
                text=item["desc"],
                font=ctk.CTkFont(family=THEME["font_family"], size=10),
                text_color=THEME["text_secondary"],
                anchor="w",
                justify="left",
                wraplength=310
            ).pack(fill="x", padx=10, pady=(0, 4))

            # Command Code Box
            code_box = ctk.CTkFrame(card, fg_color="#07090E", corner_radius=4)
            code_box.pack(fill="x", padx=10, pady=(0, 6))

            ctk.CTkLabel(
                code_box,
                text=item["cmd"],
                font=ctk.CTkFont(family=THEME["font_mono"], size=10),
                text_color=THEME["accent_cyan"],
                anchor="w",
                padx=6,
                pady=4
            ).pack(fill="x")

            # Buttons: Load / Run
            btn_box = ctk.CTkFrame(card, fg_color="transparent")
            btn_box.pack(fill="x", padx=10, pady=(0, 8))

            cmd_str = item["cmd"]
            ctk.CTkButton(
                btn_box,
                text="Load in Input",
                width=90,
                height=24,
                font=ctk.CTkFont(family=THEME["font_family"], size=10),
                fg_color=THEME["bg_card"],
                hover_color=THEME["border_highlight"],
                command=lambda c=cmd_str: self._load_command_to_input(c)
            ).pack(side="left", padx=(0, 6))

            ctk.CTkButton(
                btn_box,
                text="Run ▶",
                width=65,
                height=24,
                font=ctk.CTkFont(family=THEME["font_family"], size=10, weight="bold"),
                fg_color=THEME["primary"],
                hover_color=THEME["primary_hover"],
                command=lambda c=cmd_str: self._run_quick_cmd(c)
            ).pack(side="right")

    def _load_command_to_input(self, cmd_str: str):
        self.term_input.delete(0, "end")
        self.term_input.insert(0, cmd_str)
        self.term_input.focus_set()

    def _history_prev(self, event=None):
        if not self.command_history:
            return "break"
        if self.history_index > 0:
            self.history_index -= 1
        elif self.history_index == -1:
            self.history_index = len(self.command_history) - 1
        self.term_input.delete(0, "end")
        self.term_input.insert(0, self.command_history[self.history_index])
        return "break"

    def _history_next(self, event=None):
        if not self.command_history:
            return "break"
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.term_input.delete(0, "end")
            self.term_input.insert(0, self.command_history[self.history_index])
        else:
            self.history_index = len(self.command_history)
            self.term_input.delete(0, "end")
        return "break"

    def _run_quick_cmd(self, cmd_str: str):
        self.term_input.delete(0, "end")
        self.term_input.insert(0, cmd_str)
        self._execute_terminal_input()

    def _execute_terminal_input(self):
        cmd = self.term_input.get().strip()
        if not cmd:
            return
        self.term_input.delete(0, "end")

        if not self.command_history or self.command_history[-1] != cmd:
            self.command_history.append(cmd)
        self.history_index = len(self.command_history)

        self.term_output.insert("end", f"\nandroid:~$ {cmd}\n")
        self.term_output.see("end")

        def _exec():
            code, out, err = self.adb.execute_smart_command(cmd)
            res = out if out else (err if err else "[Command completed with no output]")
            self.after(0, self._append_term_output, res)

        threading.Thread(target=_exec, daemon=True).start()

    def _append_term_output(self, text: str):
        self.term_output.insert("end", text + "\n")
        self.term_output.see("end")

    def _clear_terminal_output(self):
        self.term_output.delete("1.0", "end")
        self.term_output.insert("end", "=== Terminal Cleared ===\n\n")

    def _copy_terminal_output(self):
        txt = self.term_output.get("1.0", "end-1c")
        self._copy_to_clipboard(txt, self)

    def _save_terminal_log(self):
        txt = self.term_output.get("1.0", "end-1c")
        path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log Files", "*.log"), ("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save Terminal Output Log"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(txt)
                messagebox.showinfo("Export Successful", f"Terminal log saved to:\n{path}")
            except Exception as e:
                messagebox.showerror("Export Failed", str(e))

    def _restart_adb_from_term(self):
        self._append_term_output("Restarting ADB server silently...")
        def _r():
            ok, msg = self.adb.restart_adb_server()
            res = "ADB server restarted successfully." if ok else f"ADB restart error: {msg}"
            self.after(0, self._append_term_output, res)
        threading.Thread(target=_r, daemon=True).start()

    # =========================================================================
    # VIEW 9: MTP & Storage Explorer
    # =========================================================================

    def show_mtp(self):
        self._highlight_nav("mtp")
        self._clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_container, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        h_box = ctk.CTkFrame(scroll, fg_color="transparent")
        h_box.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            h_box,
            text="📁 MTP & Windows Portable Device Explorer",
            font=ctk.CTkFont(family=THEME["font_family"], size=20, weight="bold"),
            text_color=THEME["text_main"]
        ).pack(side="left")

        card = ctk.CTkFrame(scroll, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
        card.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(
            card,
            text=(
                "Media Transfer Protocol (MTP) connects directly to Windows Portable Devices (WPD). "
                "This allows reading phone hardware descriptors and storage capacity even when USB Debugging has NOT been enabled yet."
            ),
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            text_color=THEME["text_secondary"],
            wraplength=920,
            justify="left"
        ).pack(anchor="w", padx=16, pady=12)

        mtp_list = self.adb.get_mtp_usb_devices()
        if not mtp_list:
            ctk.CTkLabel(
                scroll,
                text="No MTP / Windows Portable Devices detected on USB bus.\nEnsure phone is plugged in with file transfer enabled.",
                font=ctk.CTkFont(family=THEME["font_family"], size=13),
                text_color=THEME["text_muted"]
            ).pack(pady=40)
            return

        for dev in mtp_list:
            d_card = ctk.CTkFrame(scroll, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
            d_card.pack(fill="x", pady=(0, 12))

            ctk.CTkLabel(d_card, text=f"📱 {dev.get('name')}", font=ctk.CTkFont(family=THEME["font_family"], size=15, weight="bold"), text_color=THEME["accent_cyan"]).pack(anchor="w", padx=16, pady=(12, 4))
            ctk.CTkLabel(d_card, text=f"Manufacturer: {dev.get('manufacturer')}", font=ctk.CTkFont(family=THEME["font_family"], size=12), text_color=THEME["text_secondary"]).pack(anchor="w", padx=16, pady=2)
            ctk.CTkLabel(d_card, text=f"Hardware Instance ID: {dev.get('instance_id')}", font=ctk.CTkFont(family=THEME["font_mono"], size=11), text_color=THEME["text_muted"]).pack(anchor="w", padx=16, pady=(0, 12))

    # =========================================================================
    # DIALOGS & MODALS: Force USB Debugging & PayPal Donation
    # =========================================================================

    def open_force_usb_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Enable & Force USB Debugging Assistance")
        dialog.geometry("720x580")
        dialog.resizable(False, False)
        dialog.configure(fg_color=THEME["bg_main"])
        dialog.grab_set()

        title = ctk.CTkLabel(
            dialog,
            text="⚡ USB Debugging Enabler & Guidance",
            font=ctk.CTkFont(family=THEME["font_family"], size=18, weight="bold"),
            text_color=THEME["text_main"]
        )
        title.pack(padx=20, pady=(20, 8), anchor="w")

        # Quick intent force attempt button
        force_frame = ctk.CTkFrame(dialog, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=10)
        force_frame.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkLabel(
            force_frame,
            text="Attempt to trigger Developer Settings intent on phone:",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            text_color=THEME["text_secondary"]
        ).pack(anchor="w", padx=14, pady=(10, 4))

        btn_attempt = ctk.CTkButton(
            force_frame,
            text="🚀 Wake Up Phone & Launch Developer Settings",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            fg_color=THEME["primary"],
            hover_color=THEME["primary_hover"],
            height=32,
            command=lambda: self._trigger_force_intent(dialog)
        )
        btn_attempt.pack(anchor="w", padx=14, pady=(0, 12))

        # Brand selector for instructions
        ctk.CTkLabel(
            dialog,
            text="Select phone brand for exact unlock sequence:",
            font=ctk.CTkFont(family=THEME["font_family"], size=13, weight="bold"),
            text_color=THEME["text_main"]
        ).pack(padx=20, pady=(0, 6), anchor="w")

        brand_tabs = ctk.CTkSegmentedButton(
            dialog,
            values=["Samsung", "Xiaomi", "Oppo", "Vivo", "Transsion", "Pixel", "General"],
            command=lambda brand: guide_box.configure(text=self.adb.get_usb_debugging_guide(brand))
        )
        brand_tabs.pack(fill="x", padx=20, pady=(0, 10))
        brand_tabs.set("Samsung")

        guide_box = ctk.CTkLabel(
            dialog,
            text=self.adb.get_usb_debugging_guide("Samsung"),
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            text_color=THEME["text_main"],
            justify="left",
            wraplength=660
        )
        guide_box.pack(padx=20, pady=10, fill="both", expand=True)

    def _trigger_force_intent(self, dialog):
        ok, msg = self.adb.attempt_force_usb_debugging()
        messagebox.showinfo("Result", msg, parent=dialog)

    def open_donation_modal(self, default_amount: str = "3.00"):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Support MacTech Solutions Lab Development")
        dialog.geometry("640x540")
        dialog.resizable(False, False)
        dialog.configure(fg_color=THEME["bg_main"])
        dialog.grab_set()

        # Heart & Title
        ctk.CTkLabel(
            dialog,
            text="❤️ Support the Creators & Engineering Lab",
            font=ctk.CTkFont(family=THEME["font_family"], size=18, weight="bold"),
            text_color="#F43F5E"
        ).pack(pady=(22, 6))

        ctk.CTkLabel(
            dialog,
            text="MacTech Android Tool is crafted by Mark Vollan Barracks & MacTech Solutions Lab.\nYour support helps maintain continuous updates, new device security bypasses, and free tools for technicians worldwide.",
            font=ctk.CTkFont(family=THEME["font_family"], size=12),
            text_color=THEME["text_secondary"],
            wraplength=540,
            justify="center"
        ).pack(padx=20, pady=(0, 16))

        # Contribution Tier Selection Card
        tier_card = ctk.CTkFrame(dialog, fg_color=THEME["bg_card"], border_width=1, border_color=THEME["border"], corner_radius=12)
        tier_card.pack(fill="x", padx=30, pady=(0, 14))

        ctk.CTkLabel(
            tier_card,
            text="Select Support Amount (Default: $3.00 USD):",
            font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold"),
            text_color=THEME["text_muted"]
        ).pack(anchor="w", padx=16, pady=(12, 8))

        # Presets Row
        amounts_row = ctk.CTkFrame(tier_card, fg_color="transparent")
        amounts_row.pack(fill="x", padx=16, pady=(0, 10))

        self.selected_donation_amount = default_amount
        preset_btns = {}
        presets = [("☕ $3 (Coffee)", "3.00"), ("⚡ $5", "5.00"), ("🚀 $10", "10.00"), ("💎 $25", "25.00")]

        def _select_amount(amt_val: str):
            self.selected_donation_amount = amt_val
            for val, btn in preset_btns.items():
                if val == amt_val:
                    btn.configure(fg_color=THEME["primary"], text_color="#FFFFFF")
                else:
                    btn.configure(fg_color=THEME["bg_card_alt"], text_color=THEME["text_secondary"])
            btn_donate_action.configure(text=f"🌐 Donate via PayPal (${amt_val})")
            custom_entry.delete(0, "end")
            custom_entry.insert(0, amt_val)

        for label, val in presets:
            b = ctk.CTkButton(
                amounts_row,
                text=label,
                font=ctk.CTkFont(family=THEME["font_family"], size=12, weight="bold" if val == default_amount else "normal"),
                fg_color=THEME["primary"] if val == default_amount else THEME["bg_card_alt"],
                hover_color=THEME["border_highlight"],
                height=34,
                command=lambda v=val: _select_amount(v)
            )
            b.pack(side="left", padx=4, expand=True, fill="x")
            preset_btns[val] = b

        # Custom Amount Row
        custom_row = ctk.CTkFrame(tier_card, fg_color="transparent")
        custom_row.pack(fill="x", padx=16, pady=(0, 14))

        ctk.CTkLabel(
            custom_row,
            text="Or Custom Amount ($ USD):",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            text_color=THEME["text_muted"]
        ).pack(side="left", padx=(0, 8))

        custom_entry = ctk.CTkEntry(
            custom_row,
            width=100,
            height=30,
            font=ctk.CTkFont(family=THEME["font_mono"], size=12, weight="bold"),
            fg_color=THEME["bg_input"],
            border_color=THEME["border"]
        )
        custom_entry.insert(0, default_amount)
        custom_entry.pack(side="left")

        def _on_custom_change(e):
            val = custom_entry.get().strip().replace("$", "")
            if val:
                self.selected_donation_amount = val
                for b in preset_btns.values():
                    b.configure(fg_color=THEME["bg_card_alt"], text_color=THEME["text_secondary"])
                btn_donate_action.configure(text=f"🌐 Donate via PayPal (${val})")

        custom_entry.bind("<KeyRelease>", _on_custom_change)

        # PayPal Execution Action
        def _launch_paypal():
            amt = self.selected_donation_amount or "3.00"
            try:
                amt_float = float(amt)
                formatted_amt = f"{amt_float:.2f}"
            except ValueError:
                formatted_amt = "3.00"
            url = f"{PAYPAL_DONATION_BASE_URL}&amount={formatted_amt}"
            webbrowser.open(url)

        btn_donate_action = ctk.CTkButton(
            dialog,
            text=f"🌐 Donate via PayPal (${default_amount})",
            font=ctk.CTkFont(family=THEME["font_family"], size=14, weight="bold"),
            fg_color="#0070BA",
            hover_color="#005ea6",
            height=44,
            corner_radius=8,
            command=_launch_paypal
        )
        btn_donate_action.pack(padx=30, pady=(0, 12), fill="x")

        # Copy Address fallback
        copy_row = ctk.CTkFrame(dialog, fg_color="transparent")
        copy_row.pack(fill="x", padx=30, pady=(0, 10))

        btn_copy = ctk.CTkButton(
            copy_row,
            text="📋 Copy PayPal Email (markvollanbarracks@gmail.com)",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            fg_color=THEME["bg_card_alt"],
            hover_color=THEME["border_highlight"],
            height=30,
            command=lambda: self._copy_to_clipboard(PAYPAL_EMAIL, dialog)
        )
        btn_copy.pack(fill="x")

        ctk.CTkLabel(
            dialog,
            text="Thank you for fueling open-source diagnostic and forensic software!",
            font=ctk.CTkFont(family=THEME["font_family"], size=11),
            text_color=THEME["text_muted"]
        ).pack(pady=(0, 10))

    def _copy_to_clipboard(self, text: str, parent=None):
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copied", f"Copied {text} to clipboard!", parent=parent)
