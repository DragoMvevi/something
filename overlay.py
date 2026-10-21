import tkinter as tk
import ctypes

user32 = ctypes.windll.user32
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOPMOST = 0x00000008

TRANSPARENT_COLOR = "#000001"

class TrackingOverlay:
    def __init__(self, master=None, dot_size: int = 8):
        self.dot_size = max(6, dot_size)
        self.master = master
        
        # State variables
        self.probe_x = -100
        self.probe_y = -100
        self.state = "IDLE"
        self.visible = True
        self.running = True
        
        if master is not None:
            self.win = tk.Toplevel(master)
        else:
            self.win = tk.Tk()
            
        self.win.title("GotaOverlay")
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.win.config(bg=TRANSPARENT_COLOR)
        
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{sw}x{sh}+0+0")
        
        # Win32 style: click-through, non-activating, layered
        hwnd = user32.GetParent(self.win.winfo_id())
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOPMOST)
        
        self.canvas = tk.Canvas(self.win, bg=TRANSPARENT_COLOR, highlightthickness=0, width=sw, height=sh)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self._render_loop()

    def _render_loop(self):
        if not self.running or not self.win.winfo_exists():
            return
        
        self.canvas.delete("all")
        
        # Render clean hollow reticle ring with transparent center
        if self.visible and self.probe_x > 0 and self.probe_y > 0 and self.state != "IDLE":
            x, y = self.probe_x, self.probe_y
            r = self.dot_size // 2
            
            if self.state == "TRIGGERED":
                ring_color = "#FF2222"
            elif self.state == "SMART":
                ring_color = "#C084FC"  # Electric Purple for Smart Color Lock
            else:
                ring_color = "#00FF66"  # Vibrant Green for Fixed/Hold
            
            # Hollow ring (transparent center allows BitBlt to sample underneath with 0 occlusion)
            self.canvas.create_oval(
                x - r, y - r, x + r, y + r, 
                outline=ring_color, width=2, fill=""
            )

        self.win.after(16, self._render_loop)

    def update_probe(self, x: int, y: int, state: str):
        self.probe_x = x
        self.probe_y = y
        self.state = state

    def set_visibility(self, visible: bool):
        self.visible = visible

    def close(self):
        self.running = False
        if self.win:
            try:
                self.win.destroy()
            except Exception:
                pass
