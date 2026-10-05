"""
Constants and mappings for Hator keyboards.
"""

from typing import Dict, List, Tuple

# Supported Hardware IDs
VENDOR_IDS = [14234, 10473]  # 0x379A, 0x28E9
PRODUCT_IDS = [2336, 2337]   # 0x0920 (Wired), 0x0921 (Wireless 2.4G)
USAGE_PAGE = 65415           # 0xFF87 (WebHID control endpoint)
USAGE = 32                  # 0x0020

# Command IDs (from WebHID protocol)
CMD_BEGIN_CONNECT = 0x10
CMD_END_CONNECT   = 0x11
CMD_GET_DEVICE    = 0x12
CMD_SET_DEVICE    = 0x13
CMD_GET_DDATA     = 0x14  # Read global settings (lightData)
CMD_SET_DATA      = 0x15  # Write global settings (mode, brightness, speed)
CMD_GET_LIGHT     = 0x19  # Read per-key RGB colors
CMD_SET_LIGHT     = 0x1A  # Save per-key RGB colors
CMD_LIVE_SYNC     = 0x1D  # Stream live RGB frame (for animations/audio)
CMD_CLOSE_SYNC    = 0x1E  # Stop live sync streaming
CMD_RESET         = 0x20  # Factory reset keyboard settings
CMD_SCREEN_INFO   = 0x40  # Screen control info packet (magic 0xA5 0x5A)
CMD_SCREEN_DATA   = 0x41  # Screen control data packet
CMD_SCREEN_FINISH = 0x42  # Screen control finish packet

# Preset Lighting Modes
MODES: Dict[int, Tuple[str, str]] = {
    0: ("wave", "Волна"),
    1: ("cloud", "Цветные облака"),
    2: ("neon", "Неон"),
    3: ("swirl", "Вихрь"),
    4: ("blossom", "Цветение"),
    5: ("fly", "Полет"),
    6: ("cross", "Перекресток"),
    7: ("rain", "Дождь"),
    8: ("spectrum", "Спектр"),
    9: ("breathing", "Дыхание"),
    10: ("static", "Постоянное свечение"),
    11: ("ripple", "Рябь"),
    12: ("laser", "Лазер"),
    13: ("reactive", "Реактивный"),
    14: ("spread", "Рассеивание"),
    15: ("scan", "Сканирование"),
    16: ("gradient", "Градиент"),
    17: ("custom", "Пользовательский (RGB per-key)"),
    18: ("off", "Выключено"),
    20: ("music", "Музыкальный"),
}

# 81-key Physical Layout mapping (Key Name -> Index in customLight array)
KEY_MAP: Dict[str, int] = {
    # Function row
    "esc": 0, "escape": 0,
    "f1": 1, "f2": 2, "f3": 3, "f4": 4, "f5": 5, "f6": 6,
    "f7": 7, "f8": 8, "f9": 9, "f10": 10, "f11": 11, "f12": 12,
    "home": 13,
    
    # Number row
    "backquote": 16, "`": 16, "~": 16, "tilde": 16,
    "1": 17, "2": 18, "3": 19, "4": 20, "5": 21,
    "6": 22, "7": 23, "8": 24, "9": 25, "0": 26,
    "-": 27, "minus": 27, "_": 27,
    "=": 28, "equal": 28, "+": 28,
    "backspace": 29, "bksp": 29,
    
    # QWERTY row
    "tab": 32,
    "q": 33, "w": 34, "e": 35, "r": 36, "t": 37,
    "y": 38, "u": 39, "i": 40, "o": 41, "p": 42,
    "[": 43, "{": 43, "bracketleft": 43,
    "]": 44, "}": 44, "bracketright": 44,
    "\\": 45, "|": 45, "backslash": 45,
    "del": 46, "delete": 46,
    
    # ASDF row
    "caps": 48, "capslock": 48,
    "a": 49, "s": 50, "d": 51, "f": 52, "g": 53,
    "h": 54, "j": 55, "k": 56, "l": 57,
    ";": 58, ":": 58, "semicolon": 58,
    "'": 59, '"': 59, "quote": 59,
    "enter": 61, "return": 61,
    "pgup": 63, "pageup": 63,
    
    # ZXCV row
    "shift_l": 64, "left_shift": 64, "shift": 64,
    "z": 66, "x": 67, "c": 68, "v": 69, "b": 70,
    "n": 71, "m": 72,
    ",": 73, "<": 73, "comma": 73,
    ".": 74, ">": 74, "period": 74, "dot": 74,
    "/": 75, "?": 75, "slash": 75,
    "shift_r": 76, "right_shift": 76,
    "up": 78, "arrowup": 78,
    "pgdn": 79, "pagedown": 79,
    
    # Bottom row
    "ctrl_l": 80, "left_ctrl": 80, "ctrl": 80,
    "win": 81, "meta": 81, "super": 81, "gui": 81,
    "alt_l": 82, "left_alt": 82, "alt": 82,
    "space": 86, "spacebar": 86,
    "alt_r": 90, "right_alt": 90,
    "fn": 91, "wakeup": 91,
    "ctrl_r": 92, "right_ctrl": 92,
    "left": 93, "arrowleft": 93,
    "down": 94, "arrowdown": 94,
    "right": 95, "arrowright": 95,
}

# Group Presets
GROUPS: Dict[str, List[str]] = {
    "wasd": ["w", "a", "s", "d"],
    "arrows": ["up", "down", "left", "right"],
    "numbers": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="],
    "fn_row": ["esc", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "home"],
    "nav": ["home", "del", "pgup", "pgdn"],
    "modifiers": ["ctrl_l", "win", "alt_l", "space", "alt_r", "fn", "ctrl_r", "shift_l", "shift_r"],
    "alphabet": [chr(c) for c in range(ord('a'), ord('z') + 1)],
    "all": list(KEY_MAP.keys()),
}

COLOR_PRESETS: Dict[str, Tuple[int, int, int]] = {
    "black": (0, 0, 0),
    "off": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "purple": (180, 0, 255),
    "yellow": (255, 255, 0),
    "orange": (255, 120, 0),
    "pink": (255, 60, 180),
    "lime": (128, 255, 0),
    "ice_blue": (0, 180, 255),
    "gold": (255, 200, 0),
}

# Factory default settings for lightData (from Hator WebHID protocol)
DEFAULT_LIGHT_DATA: List[int] = [
    0x00, 0x00, 0x04, 0x02, 0x01, 0x01, 0xFF, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00,
    0x78, 0x00,  # 15..16: 2.4G backlight off: 120s (2 min)
    0x58, 0x02,  # 17..18: 2.4G sleep: 600s (10 min)
    0x78, 0x00,  # 19..20: BT backlight off: 120s (2 min)
    0x58, 0x02,  # 21..22: BT sleep: 600s (10 min)
    0x58, 0x02,  # 23..24: Wired backlight off: 600s (10 min)
    0x00, 0x00, 0x01, 0xFF, 0x00, 0x00, 0x00, 0x04, 0x01, 0x00,
    0x01, 0xFF, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
]

UDEV_RULES_CONTENT = """# Hator Icefall PRO RGB Keyboard udev rules
# Позволяет управлять подсветкой клавиатуры без прав суперпользователя (root)

# 0x379A (14234) - Hator / I-CHIP (проводной режим 0x0920 и беспроводной 0x0921)
KERNEL=="hidraw*", ATTRS{idVendor}=="379a", MODE="0666", TAG+="uaccess"

# 0x28E9 (10473) - Альтернативный VID Hator
KERNEL=="hidraw*", ATTRS{idVendor}=="28e9", MODE="0666", TAG+="uaccess"
"""
