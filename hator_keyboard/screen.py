"""
TFT Screen rendering and image utilities for Hator keyboards.
"""

import datetime
import socket
from typing import List

try:
    from PIL import Image, ImageDraw, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def image_to_rgb565(img: "Image.Image", width: int = 128, height: int = 128) -> List[int]:
    """Convert a PIL Image to 128x128 16-bit RGB565 big-endian byte array."""
    if not HAS_PIL:
        raise ImportError("Библиотека Pillow не установлена. Установите: pip install pillow (или pip install \"hator-keyboard[all]\")")
    img = img.convert("RGB")
    if img.size != (width, height):
        img = ImageOps.fit(img, (width, height), Image.Resampling.LANCZOS)
    pixels = []
    for y in range(height):
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            rgb565 = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
            pixels.append((rgb565 >> 8) & 0xFF)
            pixels.append(rgb565 & 0xFF)
    return pixels


def create_system_hud_image(width: int = 128, height: int = 128) -> "Image.Image":
    """Render a cyber-styled system monitoring HUD (CPU, RAM, Temp, Clock) as a 128x128 PIL Image."""
    if not HAS_PIL:
        raise ImportError("Библиотека Pillow не установлена. Установите: pip install pillow (или pip install \"hator-keyboard[all]\")")
    
    w, h = width, height
    img = Image.new("RGB", (w, h), color=(12, 16, 24))
    draw = ImageDraw.Draw(img)

    # Modern cyber frame border
    draw.rectangle([(1, 1), (w - 2, h - 2)], outline=(35, 55, 85), width=1)
    draw.line([(0, 0), (8, 0)], fill=(0, 200, 255), width=2)
    draw.line([(0, 0), (0, 8)], fill=(0, 200, 255), width=2)
    draw.line([(w - 9, h - 1), (w - 1, h - 1)], fill=(0, 200, 255), width=2)
    draw.line([(w - 1, h - 9), (w - 1, h - 1)], fill=(0, 200, 255), width=2)

    # Clock Header
    now_str = datetime.datetime.now().strftime("%H:%M:%S")
    draw.rectangle([(4, 4), (w - 5, 22)], fill=(20, 30, 48))
    draw.text((32, 7), now_str, fill=(0, 230, 255))

    # Stats via psutil if available
    cpu_pct = 0.0
    ram_pct = 0.0
    ram_gb = 0.0
    temp_val = None

    if HAS_PSUTIL:
        cpu_pct = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        ram_pct = ram.percent
        ram_gb = ram.used / (1024 ** 3)
        try:
            temps = psutil.sensors_temperatures()
            if "coretemp" in temps and temps["coretemp"]:
                temp_val = int(temps["coretemp"][0].current)
            elif "k10temp" in temps and temps["k10temp"]:
                temp_val = int(temps["k10temp"][0].current)
            elif "cpu_thermal" in temps and temps["cpu_thermal"]:
                temp_val = int(temps["cpu_thermal"][0].current)
        except Exception:
            pass

    # CPU label and bar
    cpu_label = f"CPU {cpu_pct:.0f}%"
    if temp_val is not None:
        cpu_label += f" {temp_val}°C"
    draw.text((6, 27), cpu_label, fill=(240, 240, 240))
    draw.rectangle([(6, 42), (w - 7, 48)], fill=(25, 35, 50), outline=(50, 70, 95))
    bar_w = int((w - 14) * min(1.0, max(0.0, cpu_pct / 100.0)))
    if bar_w > 0:
        bar_color = (0, 255, 180) if cpu_pct < 70 else (255, 180, 0) if cpu_pct < 85 else (255, 60, 60)
        draw.rectangle([(7, 43), (7 + bar_w, 47)], fill=bar_color)

    # RAM label and bar
    draw.text((6, 54), f"RAM {ram_pct:.0f}% ({ram_gb:.1f}G)", fill=(240, 240, 240))
    draw.rectangle([(6, 69), (w - 7, 75)], fill=(25, 35, 50), outline=(50, 70, 95))
    ram_bar_w = int((w - 14) * min(1.0, max(0.0, ram_pct / 100.0)))
    if ram_bar_w > 0:
        draw.rectangle([(7, 70), (7 + ram_bar_w, 74)], fill=(180, 100, 255))

    # Host info
    hostname = socket.gethostname()[:14]
    draw.rectangle([(4, 82), (w - 5, 98)], fill=(18, 25, 38))
    draw.text((8, 85), f"HOST: {hostname}", fill=(160, 200, 240))

    # Bottom logo
    draw.text((10, 105), "HATOR ICEFALL PRO", fill=(0, 180, 230))
    draw.text((22, 115), "LINUX DRIVER", fill=(90, 120, 150))

    return img
