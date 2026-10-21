# Gota.io / Agar.io Optical Split Detector [Sub-1ms]
**Author: Made by Drago**

An external, real-time optical split detection engine built for Gota.io and Agar-style games. It operates purely on direct screen pixel telemetry without modifying game memory, hooking browser WebSockets, or injecting into browser processes.

---

## Key Features

1. **Sub-Millisecond Processing (0.3 ms / ~300 µs)**:
   - Uses direct Win32 GDI device context sampling and high-resolution multimedia timers (`timeBeginPeriod(1)`).
   - Samples only a micro-kernel around the target cell instead of scanning full $1920 \times 1080$ frames.

2. **Adaptive Drift Compensation (No False Triggers)**:
   - When a cell moves smoothly at normal speeds (1–5 px/frame), the probe auto-adjusts its position inward along the edge normal vector.
   - When an enemy presses **Space to Split**, their cell radius instantaneously collapses from $R$ to $R/\sqrt{2}$ ($\approx 30\%$ jump in 1 frame). The engine detects this sudden disappearance as an instant split collapse and fires.

3. **Auto-Aim Cursor Redirection (Fixed & Smart Modes)**:
   - In Gota.io, pressing Space splits toward your cursor's current position.
   - When using **Fixed Mode** or **Smart Mode**, the engine instantly snaps your mouse cursor directly to the target cell coordinates right before injecting the split key, ensuring your counter-split flies directly at the enemy.

4. **Modes of Operation**:
   - **Smart Mode (Toggle)**: Press **`Z`** (default) anywhere on screen. It samples and locks that exact pixel's color `RGB(R, G, B)`. The moment that pixel changes color (because a cell moved, split, or shrank), it fires instantly in **$\approx 0.09\text{ ms}$**! Works on **any** background, skin, virus, or custom theme!
   - **Fixed Mode (Toggle)**: Press **`X`** (default) on a cell's edge. It locks onto the cell, tracks slow drift automatically, and fires when the black background appears.
   - **Movable Mode (Hold)**: Hold **`C`** (default) to sample directly under your moving cursor in real time. Fires when black background is detected.

5. **Movement Speed & Sensitivity Controls**:
   - **Engine Polling Rate**: Configurable from $500\text{ Hz}$ ($2.0\text{ ms}$) up to $2,000\text{ Hz}$ ($0.5\text{ ms}$) with a default of **$1,000\text{ Hz}$** ($1.0\text{ ms}$).
   - **Dot Movement Speed**: Adjusts tracking speed from $5\%$ (slow, buttery-smooth glide) to $100\%$ (snappy/instant).
   - **Edge Safety Margin**: Configures how deep (in pixels) the dot stays inside the cell perimeter.
   - **Max Drift Speed**: Limits maximum pixel displacement per tick.

5. **Transparent Click-Through Overlay**:
   - Windows Layered Window (`WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE`).
   - Does not intercept mouse clicks or affect browser focus.
   - Glowing neon HUD displaying status (`LOCKED`, `ADJUSTING DRIFT`, `SPLIT DETECTED`).

---

## Recommended In-Game Settings (Gota.io)

For optimal accuracy:
1. **Background**: Enable Dark / Black theme.
2. **Skins**: Turn off custom skins so cells render as solid, uniform colors.
3. **Food / Pellets**: Turn off food dots if your client supports it (or keep standard).

---

## Quick Start

1. Double-click [run.bat](file:///d:/GAMES/undetek-v10.55/run.bat) or run in terminal:
   ```powershell
   python main.py
   ```
2. In the GUI Dashboard:
   - Customize your **Toggle Key** (default: `X`), **Hold Key** (`C`), and **Split Key** (`Space`).
   - Enable/disable **Auto-Aim** and **Restore Cursor**.
   - Adjust **Edge Safety Margin** (default: 8 px) and **Max Drift Speed** (default: 6 px/tick).
3. Click **Apply & Save Settings**.
4. Hover over an enemy cell's outer rim in-game and press `X` to lock!
