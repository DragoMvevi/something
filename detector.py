import ctypes
import time

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

SRCCOPY = 0x00CC0020

class CellDetector:
    def __init__(self, dark_threshold: int = 35, edge_margin_px: int = 8, 
                 max_drift_rate_px: int = 4, patch_size: int = 32, search_radius_px: int = 20,
                 tracking_speed: float = 0.20):
        self.dark_threshold = dark_threshold
        self.edge_margin_px = edge_margin_px
        self.max_drift_rate_px = max_drift_rate_px
        self.patch_size = patch_size
        self.half = patch_size // 2
        self.search_radius_px = search_radius_px
        self.tracking_speed = max(0.01, min(1.0, tracking_speed))
        
        self.hdc_screen = None
        self.hdc_mem = None
        self.hbm = None
        self.old_bm = None
        
        # Dedicated memory DC & staging bitmap for 100% accurate Windows DWM screen reading
        self.hdc_screen = user32.GetDC(0)
        self.hdc_mem = gdi32.CreateCompatibleDC(self.hdc_screen)
        self.hbm = gdi32.CreateCompatibleBitmap(self.hdc_screen, patch_size, patch_size)
        self.old_bm = gdi32.SelectObject(self.hdc_mem, self.hbm)
        
        # Cardinal directions for edge scan (Left, Right, Up, Down)
        self.cardinal_dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def close(self):
        if self.hdc_mem:
            gdi32.SelectObject(self.hdc_mem, self.old_bm)
            gdi32.DeleteObject(self.hbm)
            gdi32.DeleteDC(self.hdc_mem)
            self.hdc_mem = None
        if self.hdc_screen:
            user32.ReleaseDC(0, self.hdc_screen)
            self.hdc_screen = None

    def __del__(self):
        self.close()

    def is_dark(self, r: int, g: int, b: int) -> bool:
        """Determines if pixel is the dark/black background."""
        return max(r, g, b) <= self.dark_threshold

    def evaluate_probe(self, probe_x: int, probe_y: int) -> dict:
        """
        Grabs a 32x32 staging patch around the probe in ~30 microseconds.
        Samples center pixel and surrounding perimeter.
        """
        t0 = time.perf_counter()
        
        # Fast BitBlt staging copy (bypasses GWM/DWM GetPixel limitations)
        gdi32.BitBlt(
            self.hdc_mem, 0, 0, self.patch_size, self.patch_size,
            self.hdc_screen, int(probe_x - self.half), int(probe_y - self.half), 
            SRCCOPY
        )
        
        # Sample exact center pixel
        raw_center = gdi32.GetPixel(self.hdc_mem, self.half, self.half)
        center_r = raw_center & 0xFF
        center_g = (raw_center >> 8) & 0xFF
        center_b = (raw_center >> 16) & 0xFF
        
        # 1. CORE TRIGGER: If center touches the dark/black background -> SPLIT DETECTED!
        if self.is_dark(center_r, center_g, center_b):
            t_end = time.perf_counter()
            return {
                "is_split": True,
                "is_on_cell": False,
                "new_x": probe_x,
                "new_y": probe_y,
                "rgb": (center_r, center_g, center_b),
                "edge_dist": 0.0,
                "elapsed_us": (t_end - t0) * 1e6
            }

        # 2. Cell Color Drift Tracking:
        # Check distance to nearest black pixel along 4 cardinal directions inside the 32x32 patch
        min_black_dist = 999.0
        black_dx = 0
        black_dy = 0
        max_scan = self.half - 1
        
        for dx, dy in self.cardinal_dirs:
            for step in range(2, max_scan, 2):
                sx = self.half + dx * step
                sy = self.half + dy * step
                raw_s = gdi32.GetPixel(self.hdc_mem, sx, sy)
                sr = raw_s & 0xFF
                sg = (raw_s >> 8) & 0xFF
                sb = (raw_s >> 16) & 0xFF
                
                if self.is_dark(sr, sg, sb):
                    dist = float(step)
                    if dist < min_black_dist:
                        min_black_dist = dist
                        black_dx = dx
                        black_dy = dy
                    break

        new_x = probe_x
        new_y = probe_y
        
        # Bidirectional Edge Distance Locking (Smooth subpixel adjustment):
        # Result: The dot stays permanently locked at the exact edge margin smoothly!
        if min_black_dist < 900.0:
            error = min_black_dist - self.edge_margin_px
            if abs(error) >= 0.5:
                step = min(float(self.max_drift_rate_px), abs(error)) * self.tracking_speed
                if error < 0:
                    # Too close to black edge -> nudge away from black (-black_dx)
                    new_x = float(probe_x) - black_dx * step
                    new_y = float(probe_y) - black_dy * step
                else:
                    # Too deep inside cell -> nudge toward black edge (+black_dx)
                    new_x = float(probe_x) + black_dx * step
                    new_y = float(probe_y) + black_dy * step

        t_end = time.perf_counter()
        return {
            "is_split": False,
            "is_on_cell": True,
            "new_x": new_x,
            "new_y": new_y,
            "rgb": (center_r, center_g, center_b),
            "edge_dist": min_black_dist if min_black_dist < 900 else -1.0,
            "elapsed_us": (t_end - t0) * 1e6
        }

    def sample_pixel(self, x: int, y: int) -> tuple[int, int, int]:
        """Samples the exact physical screen pixel color at (x, y) using BitBlt."""
        gdi32.BitBlt(
            self.hdc_mem, 0, 0, 1, 1,
            self.hdc_screen, int(x), int(y), 
            SRCCOPY
        )
        raw = gdi32.GetPixel(self.hdc_mem, 0, 0)
        return (raw & 0xFF, (raw >> 8) & 0xFF, (raw >> 16) & 0xFF)

    def evaluate_smart_probe(self, probe_x: int, probe_y: int, ref_rgb: tuple[int, int, int], tolerance: int = 35) -> dict:
        """
        Smart Mode with Edge Tracking:
        - Monitors the color at probe_x, probe_y.
        - If center changes past tolerance -> FIRES!
        - If on locked color -> auto-tracks boundary with bidirectional edge locking!
        """
        t0 = time.perf_counter()
        
        # Grab 32x32 staging patch for instant evaluation and tracking
        gdi32.BitBlt(
            self.hdc_mem, 0, 0, self.patch_size, self.patch_size,
            self.hdc_screen, int(probe_x - self.half), int(probe_y - self.half), 
            SRCCOPY
        )
        
        raw_center = gdi32.GetPixel(self.hdc_mem, self.half, self.half)
        cr = raw_center & 0xFF
        cg = (raw_center >> 8) & 0xFF
        cb = (raw_center >> 16) & 0xFF
        
        ref_r, ref_g, ref_b = ref_rgb
        diff = abs(cr - ref_r) + abs(cg - ref_g) + abs(cb - ref_b)
        
        # 1. Trigger Check: Did color change past tolerance?
        if diff > tolerance:
            t_end = time.perf_counter()
            return {
                "is_split": True,
                "color_diff": diff,
                "rgb": (cr, cg, cb),
                "new_x": probe_x,
                "new_y": probe_y,
                "edge_dist": 0.0,
                "elapsed_us": (t_end - t0) * 1e6
            }
            
        # 2. Smart Edge Drift Tracking:
        # Search for nearest boundary pixel differing from ref_rgb
        min_edge_dist = 999.0
        edge_dx = 0
        edge_dy = 0
        max_scan = self.half - 1
        
        for dx, dy in self.cardinal_dirs:
            for step in range(2, max_scan, 2):
                sx = self.half + dx * step
                sy = self.half + dy * step
                raw_s = gdi32.GetPixel(self.hdc_mem, sx, sy)
                sr = raw_s & 0xFF
                sg = (raw_s >> 8) & 0xFF
                sb = (raw_s >> 16) & 0xFF
                
                s_diff = abs(sr - ref_r) + abs(sg - ref_g) + abs(sb - ref_b)
                if s_diff > tolerance:
                    dist = float(step)
                    if dist < min_edge_dist:
                        min_edge_dist = dist
                        edge_dx = dx
                        edge_dy = dy
                    break

        new_x = probe_x
        new_y = probe_y
        
        # Bidirectional Edge Distance Locking (Smooth subpixel adjustment):
        if min_edge_dist < 900.0:
            error = min_edge_dist - self.edge_margin_px
            if abs(error) >= 0.5:
                step = min(float(self.max_drift_rate_px), abs(error)) * self.tracking_speed
                if error < 0:
                    new_x = float(probe_x) - edge_dx * step
                    new_y = float(probe_y) - edge_dy * step
                else:
                    new_x = float(probe_x) + edge_dx * step
                    new_y = float(probe_y) + edge_dy * step

        t_end = time.perf_counter()
        return {
            "is_split": False,
            "color_diff": diff,
            "rgb": (cr, cg, cb),
            "new_x": new_x,
            "new_y": new_y,
            "edge_dist": min_edge_dist if min_edge_dist < 900 else -1.0,
            "elapsed_us": (t_end - t0) * 1e6
        }
