import customtkinter as ctk
import tkinter as tk
import time
import os
import sys

from config import AppConfig
from input_manager import get_vk, cleanup_timers
from overlay import TrackingOverlay
from engine import TriggerEngine

# Set appearance theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("GOTA / AGAR SPLIT DETECTOR • Made by Drago")
        self.geometry("640x790")
        self.resizable(False, False)
        
        self.config = AppConfig.load()
        
        # Initialize Overlay
        self.overlay = TrackingOverlay(master=self, dot_size=self.config.overlay_dot_size)
        self.overlay.set_visibility(self.config.show_overlay)
        
        # Initialize Engine
        self.engine = TriggerEngine(self.config, self.overlay)
        
        self._build_ui()
        
        # Start Engine immediately
        self.engine.start()
        
        # UI update timer
        self._update_diagnostics()
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        # Header / Title Bar
        header_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#18181b")
        header_frame.pack(fill="x", padx=16, pady=(16, 8))
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="⚡ GOTA OPTICAL SPLIT DETECTOR", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#00FFAA"
        )
        title_label.pack(pady=(10, 1))

        author_badge = ctk.CTkLabel(
            header_frame,
            text="★ Made by Drago ★",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#C084FC"
        )
        author_badge.pack(pady=(0, 4))
        
        subtitle = ctk.CTkLabel(
            header_frame, 
            text="Direct Screen Sampling • Adaptive Drift Compensation • Auto-Aim Snap",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#94a3b8"
        )
        subtitle.pack(pady=(0, 10))

        # Status & Telemetry Card
        self.status_card = ctk.CTkFrame(self, corner_radius=10, fg_color="#0f172a")
        self.status_card.pack(fill="x", padx=16, pady=8)
        
        # Status Row
        row1 = ctk.CTkFrame(self.status_card, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(10, 4))
        
        self.lbl_status = ctk.CTkLabel(
            row1, 
            text="STATUS: READY (IDLE)", 
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#38bdf8"
        )
        self.lbl_status.pack(side="left")
        
        self.lbl_latency = ctk.CTkLabel(
            row1, 
            text="Latency: 0.0 µs (<0.01 ms)", 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#4ade80"
        )
        self.lbl_latency.pack(side="right")
        
        # Telemetry Row
        row2 = ctk.CTkFrame(self.status_card, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(0, 10))
        
        self.lbl_triggers = ctk.CTkLabel(
            row2, 
            text="Triggers: 0", 
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#cbd5e1"
        )
        self.lbl_triggers.pack(side="left")
        
        self.lbl_probe_info = ctk.CTkLabel(
            row2, 
            text="Edge Dist: N/A | Color: [0, 0, 0]", 
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#cbd5e1"
        )
        self.lbl_probe_info.pack(side="right")

        # Scrollable Configuration Area
        scroll = ctk.CTkScrollableFrame(self, corner_radius=10, fg_color="#18181b")
        scroll.pack(fill="both", expand=True, padx=16, pady=8)

        # SECTION 1: KEY BINDINGS & MODES
        sec1_title = ctk.CTkLabel(scroll, text="KEY BINDINGS & MODES", font=ctk.CTkFont(size=14, weight="bold"), text_color="#38bdf8")
        sec1_title.pack(anchor="w", pady=(6, 4))
        
        # Fixed Mode Toggle Key
        f_row = ctk.CTkFrame(scroll, fg_color="transparent")
        f_row.pack(fill="x", pady=4)
        ctk.CTkLabel(f_row, text="Fixed Mode Toggle Key (Locks dot & tracks drift):").pack(side="left")
        self.ent_fixed_key = ctk.CTkEntry(f_row, width=80)
        self.ent_fixed_key.insert(0, self.config.fixed_toggle_key)
        self.ent_fixed_key.pack(side="right")

        # Smart Mode Toggle Key (NEW)
        sm_row = ctk.CTkFrame(scroll, fg_color="transparent")
        sm_row.pack(fill="x", pady=4)
        ctk.CTkLabel(sm_row, text="Smart Mode Key (Locks pixel color & fires on ANY change):").pack(side="left")
        self.ent_smart_key = ctk.CTkEntry(sm_row, width=80)
        self.ent_smart_key.insert(0, self.config.smart_toggle_key)
        self.ent_smart_key.pack(side="right")

        # Movable Mode Hold Key
        m_row = ctk.CTkFrame(scroll, fg_color="transparent")
        m_row.pack(fill="x", pady=4)
        ctk.CTkLabel(m_row, text="Movable Mode Hold Key (Follows cursor):").pack(side="left")
        self.ent_movable_key = ctk.CTkEntry(m_row, width=80)
        self.ent_movable_key.insert(0, self.config.movable_hold_key)
        self.ent_movable_key.pack(side="right")

        # Split Action Key
        s_row = ctk.CTkFrame(scroll, fg_color="transparent")
        s_row.pack(fill="x", pady=4)
        ctk.CTkLabel(s_row, text="Split Action Key to Fire:").pack(side="left")
        self.ent_split_key = ctk.CTkEntry(s_row, width=80)
        self.ent_split_key.insert(0, self.config.split_action_key)
        self.ent_split_key.pack(side="right")

        # SECTION 2: AUTO-AIM & REDIRECTION
        ctk.CTkFrame(scroll, height=2, fg_color="#334155").pack(fill="x", pady=12)
        sec2_title = ctk.CTkLabel(scroll, text="AUTO-AIM / CURSOR REDIRECTION", font=ctk.CTkFont(size=14, weight="bold"), text_color="#38bdf8")
        sec2_title.pack(anchor="w", pady=(0, 4))

        self.sw_auto_aim = ctk.CTkSwitch(
            scroll, 
            text="Enable Auto-Aim (Snaps cursor to enemy cell right before splitting)",
            onvalue=True, offvalue=False
        )
        if self.config.auto_aim_enabled:
            self.sw_auto_aim.select()
        self.sw_auto_aim.pack(anchor="w", pady=4)

        self.sw_restore_pos = ctk.CTkSwitch(
            scroll, 
            text="Restore Original Cursor Position after Split",
            onvalue=True, offvalue=False
        )
        if self.config.auto_aim_restore_pos:
            self.sw_restore_pos.select()
        self.sw_restore_pos.pack(anchor="w", pady=4)

        self.sw_cursor_lock = ctk.CTkSwitch(
            scroll, 
            text="Cursor Tether (Mouse physically locks to dot & glides with it)",
            onvalue=True, offvalue=False
        )
        if self.config.cursor_lock_to_dot:
            self.sw_cursor_lock.select()
        self.sw_cursor_lock.pack(anchor="w", pady=4)

        # Pre-Delay Slider
        d_row = ctk.CTkFrame(scroll, fg_color="transparent")
        d_row.pack(fill="x", pady=4)
        self.lbl_predelay = ctk.CTkLabel(d_row, text=f"Auto-Aim Snap Delay: {self.config.auto_aim_pre_delay_ms} ms")
        self.lbl_predelay.pack(side="left")
        self.sl_predelay = ctk.CTkSlider(d_row, from_=0, to=10, number_of_steps=10, width=180, command=self._on_predelay_change)
        self.sl_predelay.set(self.config.auto_aim_pre_delay_ms)
        self.sl_predelay.pack(side="right")

        # SECTION 3: ADAPTIVE DRIFT & SENSITIVITY
        ctk.CTkFrame(scroll, height=2, fg_color="#334155").pack(fill="x", pady=12)
        sec3_title = ctk.CTkLabel(scroll, text="ADAPTIVE DRIFT & EDGE SENSITIVITY", font=ctk.CTkFont(size=14, weight="bold"), text_color="#38bdf8")
        sec3_title.pack(anchor="w", pady=(0, 4))

        # Margin Slider
        mar_row = ctk.CTkFrame(scroll, fg_color="transparent")
        mar_row.pack(fill="x", pady=4)
        self.lbl_margin = ctk.CTkLabel(mar_row, text=f"Edge Safety Margin: {self.config.edge_margin_px} px")
        self.lbl_margin.pack(side="left")
        self.sl_margin = ctk.CTkSlider(mar_row, from_=2, to=20, number_of_steps=18, width=180, command=self._on_margin_change)
        self.sl_margin.set(self.config.edge_margin_px)
        self.sl_margin.pack(side="right")

        # Max Drift Rate Slider
        drift_row = ctk.CTkFrame(scroll, fg_color="transparent")
        drift_row.pack(fill="x", pady=4)
        self.lbl_drift = ctk.CTkLabel(drift_row, text=f"Max Drift Speed: {self.config.max_drift_rate_px} px/tick")
        self.lbl_drift.pack(side="left")
        self.sl_drift = ctk.CTkSlider(drift_row, from_=2, to=15, number_of_steps=13, width=180, command=self._on_drift_change)
        self.sl_drift.set(self.config.max_drift_rate_px)
        self.sl_drift.pack(side="right")

        # Dark Threshold Slider
        dark_row = ctk.CTkFrame(scroll, fg_color="transparent")
        dark_row.pack(fill="x", pady=4)
        self.lbl_dark = ctk.CTkLabel(dark_row, text=f"Background Dark Threshold: {self.config.dark_threshold}")
        self.lbl_dark.pack(side="left")
        self.sl_dark = ctk.CTkSlider(dark_row, from_=10, to=80, number_of_steps=70, width=180, command=self._on_dark_change)
        self.sl_dark.set(self.config.dark_threshold)
        self.sl_dark.pack(side="right")

        # Tracking Movement Speed Slider (Smooth Glide vs Snappy)
        spd_row = ctk.CTkFrame(scroll, fg_color="transparent")
        spd_row.pack(fill="x", pady=4)
        self.lbl_speed = ctk.CTkLabel(spd_row, text=f"Dot Movement Speed: {int(self.config.tracking_speed * 100)}%")
        self.lbl_speed.pack(side="left")
        self.sl_speed = ctk.CTkSlider(spd_row, from_=0.05, to=1.0, number_of_steps=19, width=180, command=self._on_speed_change)
        self.sl_speed.set(self.config.tracking_speed)
        self.sl_speed.pack(side="right")

        # Smart Mode Color Change Tolerance Slider
        tol_row = ctk.CTkFrame(scroll, fg_color="transparent")
        tol_row.pack(fill="x", pady=4)
        self.lbl_tol = ctk.CTkLabel(tol_row, text=f"Smart Color Delta Sensitivity: {self.config.color_change_tolerance}")
        self.lbl_tol.pack(side="left")
        self.sl_tol = ctk.CTkSlider(tol_row, from_=10, to=120, number_of_steps=110, width=180, command=self._on_tol_change)
        self.sl_tol.set(self.config.color_change_tolerance)
        self.sl_tol.pack(side="right")

        # Polling Frequency Slider (500 Hz - 2000 Hz)
        hz_row = ctk.CTkFrame(scroll, fg_color="transparent")
        hz_row.pack(fill="x", pady=4)
        self.lbl_hz = ctk.CTkLabel(hz_row, text=f"Engine Polling Rate: {self.config.sample_rate_hz} Hz ({1000/self.config.sample_rate_hz:.1f} ms)")
        self.lbl_hz.pack(side="left")
        self.sl_hz = ctk.CTkSlider(hz_row, from_=500, to=2000, number_of_steps=15, width=180, command=self._on_hz_change)
        self.sl_hz.set(self.config.sample_rate_hz)
        self.sl_hz.pack(side="right")

        # SECTION 4: OVERLAY
        ctk.CTkFrame(scroll, height=2, fg_color="#334155").pack(fill="x", pady=12)
        sec4_title = ctk.CTkLabel(scroll, text="VISUAL OVERLAY", font=ctk.CTkFont(size=14, weight="bold"), text_color="#38bdf8")
        sec4_title.pack(anchor="w", pady=(0, 4))

        self.sw_overlay = ctk.CTkSwitch(
            scroll, 
            text="Show Clean Tracking Dot Overlay",
            onvalue=True, offvalue=False
        )
        if self.config.show_overlay:
            self.sw_overlay.select()
        self.sw_overlay.pack(anchor="w", pady=4)

        # Footer Actions
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=12)

        self.btn_save = ctk.CTkButton(
            footer, 
            text="APPLY & SAVE SETTINGS", 
            font=ctk.CTkFont(weight="bold"),
            fg_color="#0284c7", hover_color="#0369a1",
            command=self._apply_settings
        )
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_toggle_engine = ctk.CTkButton(
            footer, 
            text="STOP ENGINE", 
            font=ctk.CTkFont(weight="bold"),
            fg_color="#ef4444", hover_color="#dc2626",
            width=140,
            command=self._toggle_engine
        )
        self.btn_toggle_engine.pack(side="right")

        # Footer Credit
        credit_lbl = ctk.CTkLabel(
            self,
            text="⚡ Made by Drago • External Sub-1ms Optical Split Detection Engine",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#64748b"
        )
        credit_lbl.pack(pady=(0, 6))

    def _on_predelay_change(self, val):
        self.lbl_predelay.configure(text=f"Auto-Aim Snap Delay: {int(val)} ms")

    def _on_margin_change(self, val):
        self.lbl_margin.configure(text=f"Edge Safety Margin: {int(val)} px")

    def _on_drift_change(self, val):
        self.lbl_drift.configure(text=f"Max Drift Speed: {int(val)} px/tick")

    def _on_dark_change(self, val):
        self.lbl_dark.configure(text=f"Background Dark Threshold: {int(val)}")

    def _on_tol_change(self, val):
        self.lbl_tol.configure(text=f"Smart Color Delta Sensitivity: {int(val)}")

    def _on_speed_change(self, val):
        self.lbl_speed.configure(text=f"Dot Movement Speed: {int(val * 100)}%")

    def _on_hz_change(self, val):
        hz = int(val)
        self.lbl_hz.configure(text=f"Engine Polling Rate: {hz} Hz ({1000/hz:.1f} ms)")

    def _apply_settings(self):
        self.config.fixed_toggle_key = self.ent_fixed_key.get().strip().upper()
        self.config.fixed_toggle_vk = get_vk(self.config.fixed_toggle_key)
        
        self.config.smart_toggle_key = self.ent_smart_key.get().strip().upper()
        self.config.smart_toggle_vk = get_vk(self.config.smart_toggle_key)
        
        self.config.movable_hold_key = self.ent_movable_key.get().strip().upper()
        self.config.movable_hold_vk = get_vk(self.config.movable_hold_key)
        
        self.config.split_action_key = self.ent_split_key.get().strip()
        self.config.split_action_vk = get_vk(self.config.split_action_key)
        
        self.config.auto_aim_enabled = bool(self.sw_auto_aim.get())
        self.config.auto_aim_restore_pos = bool(self.sw_restore_pos.get())
        self.config.auto_aim_pre_delay_ms = int(self.sl_predelay.get())
        self.config.cursor_lock_to_dot = bool(self.sw_cursor_lock.get())
        
        self.config.edge_margin_px = int(self.sl_margin.get())
        self.config.max_drift_rate_px = int(self.sl_drift.get())
        self.config.tracking_speed = float(self.sl_speed.get())
        self.config.dark_threshold = int(self.sl_dark.get())
        self.config.color_change_tolerance = int(self.sl_tol.get())
        self.config.sample_rate_hz = int(self.sl_hz.get())
        
        self.config.show_overlay = bool(self.sw_overlay.get())
        
        self.config.save()
        self.engine.reload_config(self.config)
        self.btn_save.configure(text="SETTINGS APPLIED!")
        self.after(1500, lambda: self.btn_save.configure(text="APPLY & SAVE SETTINGS"))

    def _toggle_engine(self):
        if self.engine.running:
            self.engine.stop()
            self.btn_toggle_engine.configure(text="START ENGINE", fg_color="#10b981", hover_color="#059669")
            self.lbl_status.configure(text="STATUS: STOPPED", text_color="#ef4444")
        else:
            self.engine.start()
            self.btn_toggle_engine.configure(text="STOP ENGINE", fg_color="#ef4444", hover_color="#dc2626")
            self.lbl_status.configure(text="STATUS: READY (IDLE)", text_color="#38bdf8")

    def _update_diagnostics(self):
        if self.engine.running:
            mode_text = self.engine.mode
            if mode_text == "FIXED":
                self.lbl_status.configure(text="STATUS: LOCKED [FIXED MODE]", text_color="#00FFAA")
            elif mode_text == "SMART":
                self.lbl_status.configure(text=f"STATUS: SMART LOCKED [RGB{self.engine.locked_color}]", text_color="#C084FC")
            elif mode_text == "MOVABLE":
                self.lbl_status.configure(text="STATUS: ACTIVE [MOVABLE HOLD]", text_color="#f59e0b")
            else:
                self.lbl_status.configure(text=f"STATUS: {self.engine.status_message}", text_color="#38bdf8")
            
            lat_us = self.engine.last_latency_us
            lat_ms = lat_us / 1000.0
            self.lbl_latency.configure(text=f"Latency: {lat_us:.1f} µs ({lat_ms:.3f} ms)")
            
            r, g, b = self.engine.last_rgb
            if mode_text == "SMART":
                self.lbl_probe_info.configure(text=f"Color Delta: {self.engine.last_edge_dist:.0f} | Cur RGB: [{r},{g},{b}]")
            else:
                self.lbl_probe_info.configure(text=f"Edge Dist: {self.engine.last_edge_dist:.1f}px | RGB: [{r},{g},{b}]")
            self.lbl_triggers.configure(text=f"Triggers: {self.engine.trigger_count}")
        
        self.after(50, self._update_diagnostics)

    def on_close(self):
        self.engine.stop()
        if self.overlay:
            self.overlay.close()
        cleanup_timers()
        try:
            self.quit()
        except Exception:
            pass
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = App()
    app.mainloop()
