"""
Core controller class and protocol implementation for Hator keyboards.
"""

import sys
import time
import datetime
from typing import Dict, List, Tuple, Union, Optional

try:
    if sys.platform.startswith("linux"):
        try:
            import hidraw as hid
        except ImportError:
            import hid
    else:
        import hid
except ImportError:
    hid = None

from .constants import (
    VENDOR_IDS,
    PRODUCT_IDS,
    USAGE_PAGE,
    USAGE,
    CMD_GET_DDATA,
    CMD_SET_DATA,
    CMD_GET_LIGHT,
    CMD_SET_LIGHT,
    CMD_LIVE_SYNC,
    CMD_CLOSE_SYNC,
    CMD_RESET,
    CMD_SCREEN_INFO,
    CMD_SCREEN_DATA,
    CMD_SCREEN_FINISH,
    MODES,
    KEY_MAP,
    GROUPS,
    COLOR_PRESETS,
    DEFAULT_LIGHT_DATA,
)
from .screen import HAS_PIL, image_to_rgb565, create_system_hud_image

if HAS_PIL:
    from PIL import Image


def parse_color(color: Union[str, Tuple[int, int, int], List[int]]) -> Tuple[int, int, int]:
    """Parse color into (R, G, B) tuple with 0..255 values."""
    if isinstance(color, (tuple, list)) and len(color) >= 3:
        return (int(color[0]), int(color[1]), int(color[2]))
    if isinstance(color, str):
        color_lower = color.lower().strip()
        if color_lower in COLOR_PRESETS:
            return COLOR_PRESETS[color_lower]
        if color_lower.startswith("#"):
            color_lower = color_lower[1:]
        if len(color_lower) == 6:
            try:
                r = int(color_lower[0:2], 16)
                g = int(color_lower[2:4], 16)
                b = int(color_lower[4:6], 16)
                return (r, g, b)
            except ValueError:
                pass
    raise ValueError(f"Неизвестный формат цвета: {color}")


def _build_packet(cmd: int, offset: int = 0, payload: Optional[List[int]] = None, req_len: int = 63) -> List[int]:
    """Construct a 63-byte packet with checksum according to Hator WebHID protocol."""
    if payload is None:
        payload = []
    chunk_data_len = len(payload) if payload else (req_len - 7)
    
    packet = [0] * req_len
    packet[0] = cmd
    packet[1] = offset & 0xFF
    packet[2] = (offset >> 8) & 0xFF
    packet[3] = chunk_data_len
    packet[4] = 0  # Checksum low placeholder
    packet[5] = 0  # Checksum high placeholder
    packet[6] = 0  # Reserved
    
    for i, b in enumerate(payload):
        if 7 + i < req_len:
            packet[7 + i] = b
            
    checksum = sum(packet) & 0xFFFF
    packet[4] = checksum & 0xFF
    packet[5] = (checksum >> 8) & 0xFF
    return packet


def _crc16_modbus(data: List[int]) -> List[int]:
    """Calculate CRC-16 (Modbus polynomial 0xA001) used by Hator screen packets."""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return [(crc >> 8) & 0xFF, crc & 0xFF]


class HatorKeyboard:
    """Controller for Hator Keyboard RGB backlighting and TFT screen."""
    
    TOTAL_KEYS = 128
    TOTAL_BYTES = 128 * 3  # 384 bytes
    CHUNK_LEN = 56         # 63 - 7
    REPORT_ID = 6
    
    def __init__(self, vendor_id: Optional[int] = None, product_id: Optional[int] = None):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = None
        self.path = None
        self.custom_colors = [0] * self.TOTAL_BYTES
        self.light_data = list(DEFAULT_LIGHT_DATA)
        self._connected = False

    def find_device(self) -> Optional[bytes]:
        """Find the matching HID device path."""
        if hid is None:
            raise ImportError(
                "Библиотека 'hidapi' не установлена.\n"
                "Установите её командой: pip install hidapi"
            )

        candidates = []
        for d in hid.enumerate():
            v = d.get('vendor_id')
            p = d.get('product_id')
            up = d.get('usage_page')
            u = d.get('usage')
            iface = d.get('interface_number')
            
            # Match vendor and product IDs
            if (self.vendor_id is None and v in VENDOR_IDS) or (self.vendor_id == v):
                if (self.product_id is None and p in PRODUCT_IDS) or (self.product_id == p):
                    # Exact match: WebHID control endpoint usage_page and usage
                    if up == USAGE_PAGE and u == USAGE:
                        self.vendor_id = v
                        self.product_id = p
                        self.path = d['path']
                        return self.path
                    # Fallback when usage_page is not exposed (0):
                    # interface 1 is the vendor-specific control endpoint
                    if up == 0 and u == 0 and iface == 1:
                        candidates.append((v, p, d['path']))
        if candidates:
            v, p, path = candidates[0]
            self.vendor_id = v
            self.product_id = p
            self.path = path
            return self.path
        return None

    def connect(self):
        """Open connection to the keyboard."""
        if hid is None:
            raise ImportError(
                "Библиотека 'hidapi' не установлена.\n"
                "Установите её командой: pip install hidapi"
            )

        path = self.find_device()
        if not path:
            raise ConnectionError(
                "Клавиатура Hator не найдена! Проверьте подключение USB/ресивера."
            )
        self.device = hid.device()
        try:
            self.device.open_path(path)
        except (IOError, OSError) as e:
            if sys.platform.startswith("linux"):
                path_str = path.decode("utf-8", errors="ignore") if isinstance(path, bytes) else str(path)
                raise PermissionError(
                    f"Ошибка доступа к устройству '{path_str}': {e}\n\n"
                    "В Linux для доступа к HID-устройствам от обычного пользователя нужны udev-правила.\n"
                    "Выполните команду для установки правил (требуется sudo один раз):\n\n"
                    "  hator setup-udev --install\n\n"
                    "Либо временно запустите команду через sudo."
                ) from e
            raise
        self._connected = True
        
        # Load current settings from keyboard
        self.read_settings()
        self.read_custom_colors()

    def disconnect(self):
        """Close connection to the keyboard."""
        if self.device:
            try:
                self.device.close()
            except Exception:
                pass
            self.device = None
        self._connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def _send_cmd(self, cmd: int, offset: int = 0, payload: Optional[List[int]] = None) -> List[int]:
        """Send command and read response report."""
        if not self._connected or not self.device:
            raise RuntimeError("Клавиатура не подключена!")
        
        packet = _build_packet(cmd, offset, payload)
        self.device.write([self.REPORT_ID] + packet)
        res = self.device.read(64, timeout_ms=1000)
        if not res or len(res) <= 1:
            raise TimeoutError("Таймаут ожидания ответа от клавиатуры!")
        return res[1:]

    def read_settings(self) -> List[int]:
        """Read 64-byte global lightData settings."""
        data = []
        chunks = (64 + self.CHUNK_LEN - 1) // self.CHUNK_LEN
        for c in range(chunks):
            offset = c * self.CHUNK_LEN
            resp = self._send_cmd(CMD_GET_DDATA, offset)
            data.extend(resp[7:7 + self.CHUNK_LEN])
        self.light_data = data[:64]

        # Check if standby/sleep timeout bytes (15..24) are zeroed out.
        # When timeout bytes are 0, keyboard firmware turns off LEDs after 0 seconds (sleep on keypress).
        # Auto-recover with standard factory defaults if detected.
        needs_fix = False
        if self.light_data[23] == 0 and self.light_data[24] == 0:
            self.light_data[23] = DEFAULT_LIGHT_DATA[23]
            self.light_data[24] = DEFAULT_LIGHT_DATA[24]
            needs_fix = True
        if self.light_data[15] == 0 and self.light_data[16] == 0:
            self.light_data[15] = DEFAULT_LIGHT_DATA[15]
            self.light_data[16] = DEFAULT_LIGHT_DATA[16]
            needs_fix = True
        if self.light_data[17] == 0 and self.light_data[18] == 0:
            self.light_data[17] = DEFAULT_LIGHT_DATA[17]
            self.light_data[18] = DEFAULT_LIGHT_DATA[18]
            needs_fix = True
        if self.light_data[19] == 0 and self.light_data[20] == 0:
            self.light_data[19] = DEFAULT_LIGHT_DATA[19]
            self.light_data[20] = DEFAULT_LIGHT_DATA[20]
            needs_fix = True
        if self.light_data[21] == 0 and self.light_data[22] == 0:
            self.light_data[21] = DEFAULT_LIGHT_DATA[21]
            self.light_data[22] = DEFAULT_LIGHT_DATA[22]
            needs_fix = True

        if needs_fix:
            self.write_settings()

        return self.light_data

    def write_settings(self):
        """Send updated global lightData settings (0x15)."""
        chunks = (64 + self.CHUNK_LEN - 1) // self.CHUNK_LEN
        for c in range(chunks):
            offset = c * self.CHUNK_LEN
            chunk = self.light_data[offset:offset + self.CHUNK_LEN]
            self._send_cmd(CMD_SET_DATA, offset, chunk)

    def read_custom_colors(self) -> List[int]:
        """Read 384-byte custom per-key color array (0x19)."""
        data = []
        chunks = (self.TOTAL_BYTES + self.CHUNK_LEN - 1) // self.CHUNK_LEN
        for c in range(chunks):
            offset = c * self.CHUNK_LEN
            resp = self._send_cmd(CMD_GET_LIGHT, offset)
            data.extend(resp[7:7 + self.CHUNK_LEN])
        self.custom_colors = data[:self.TOTAL_BYTES]
        return self.custom_colors

    def apply(self):
        """Save custom per-key colors to keyboard memory (0x1A) and activate Mode 17 (Custom)."""
        # 1. Send all custom color chunks
        chunks = (self.TOTAL_BYTES + self.CHUNK_LEN - 1) // self.CHUNK_LEN
        for c in range(chunks):
            offset = c * self.CHUNK_LEN
            chunk = self.custom_colors[offset:offset + self.CHUNK_LEN]
            self._send_cmd(CMD_SET_LIGHT, offset, chunk)

        # 2. Ensure Mode 17 (Custom) is active and save settings
        self.light_data[1] = 17
        if self.light_data[2] == 0:
            self.light_data[2] = 4  # Default brightness: max
        self.light_data[5] = 1      # Custom RGB mode
        self.write_settings()

    def set_sleep_timeout(self, wired_minutes: int = 10, wireless_backlight_minutes: int = 2, wireless_sleep_minutes: int = 10):
        """
        Configure keyboard sleep and backlight turn-off timeouts (in minutes).
        - wired_minutes: inactivity time before backlight turns off in USB wired mode (default: 10).
        - wireless_backlight_minutes: inactivity time before backlight turns off in 2.4G / BT mode (default: 2).
        - wireless_sleep_minutes: inactivity time before keyboard enters deep sleep in 2.4G / BT mode (default: 10).
        """
        wb_sec = max(1, int(wired_minutes)) * 60
        self.light_data[23] = wb_sec & 0xFF
        self.light_data[24] = (wb_sec >> 8) & 0xFF

        w24_b_sec = max(1, int(wireless_backlight_minutes)) * 60
        self.light_data[15] = w24_b_sec & 0xFF
        self.light_data[16] = (w24_b_sec >> 8) & 0xFF

        w24_s_sec = max(1, int(wireless_sleep_minutes)) * 60
        self.light_data[17] = w24_s_sec & 0xFF
        self.light_data[18] = (w24_s_sec >> 8) & 0xFF

        self.light_data[19] = w24_b_sec & 0xFF
        self.light_data[20] = (w24_b_sec >> 8) & 0xFF

        self.light_data[21] = w24_s_sec & 0xFF
        self.light_data[22] = (w24_s_sec >> 8) & 0xFF

        self.write_settings()

    def set_mode(self, mode: Union[int, str], brightness: Optional[int] = None, speed: Optional[int] = None):
        """
        Switch keyboard lighting mode.
        mode: integer (0..20) or string name ('wave', 'breathing', 'static', 'custom', 'off', etc.)
        brightness: 0 (off) to 4 (max)
        speed: 0 (slowest) to 4 (fastest)
        """
        mode_id = None
        if isinstance(mode, int):
            mode_id = mode
        elif isinstance(mode, str):
            mode_lower = mode.lower().strip()
            for mid, (mname, _) in MODES.items():
                if mode_lower in (mname, str(mid)):
                    mode_id = mid
                    break
        
        if mode_id is None:
            available = ", ".join(f"{mid}: {name}" for mid, (name, _) in MODES.items())
            raise ValueError(f"Неизвестный режим: {mode}. Доступные режимы: {available}")

        self.light_data[1] = mode_id
        if brightness is not None:
            self.light_data[2] = max(0, min(4, int(brightness)))
        if speed is not None:
            self.light_data[3] = max(0, min(4, int(speed)))
        
        self.write_settings()

    def set_brightness(self, level: int):
        """Set brightness level (0 = off, 1..4 = max)."""
        self.light_data[2] = max(0, min(4, int(level)))
        self.write_settings()

    def set_speed(self, speed: int):
        """Set effect speed (0 = slow .. 4 = fast)."""
        self.light_data[3] = max(0, min(4, int(speed)))
        self.write_settings()

    def set_static_color(self, color: Union[str, Tuple[int, int, int]], brightness: int = 4):
        """Set all keys to a single solid color using Mode 10 (Static)."""
        r, g, b = parse_color(color)
        self.light_data[1] = 10  # Static mode
        self.light_data[2] = max(0, min(4, brightness))
        self.light_data[5] = 0   # Single color flag
        self.light_data[6] = r
        self.light_data[7] = g
        self.light_data[8] = b
        self.write_settings()

    def turn_off(self):
        """Turn off backlighting (Mode 18)."""
        self.set_mode(18)

    # ----------------------------------------------------
    # Custom Per-Key Lighting Methods (Mode 17)
    # ----------------------------------------------------

    def _resolve_key_index(self, key: Union[str, int]) -> int:
        """Resolve key name or integer index to buffer index (0..127)."""
        if isinstance(key, int):
            if 0 <= key < self.TOTAL_KEYS:
                return key
            raise IndexError(f"Индекс клавиши вне диапазона: {key} (допустимо 0..{self.TOTAL_KEYS-1})")
        key_str = str(key).lower().strip()
        if key_str in KEY_MAP:
            return KEY_MAP[key_str]
        raise KeyError(f"Неизвестная клавиша: '{key}'. Используйте list_keys() для просмотра списка.")

    def set_key_color(self, key: Union[str, int], color: Union[str, Tuple[int, int, int]]):
        """Set color of an individual key in buffer."""
        idx = self._resolve_key_index(key)
        r, g, b = parse_color(color)
        self.custom_colors[idx * 3] = r
        self.custom_colors[idx * 3 + 1] = g
        self.custom_colors[idx * 3 + 2] = b

    def get_key_color(self, key: Union[str, int]) -> Tuple[int, int, int]:
        """Get current color of a key from buffer."""
        idx = self._resolve_key_index(key)
        return (
            self.custom_colors[idx * 3],
            self.custom_colors[idx * 3 + 1],
            self.custom_colors[idx * 3 + 2]
        )

    def set_keys_color(self, mapping: Dict[Union[str, int], Union[str, Tuple[int, int, int]]]):
        """Set colors for multiple keys at once."""
        for key, color in mapping.items():
            self.set_key_color(key, color)

    def set_all_keys(self, color: Union[str, Tuple[int, int, int]]):
        """Set all keys to a given color in buffer."""
        r, g, b = parse_color(color)
        for i in range(self.TOTAL_KEYS):
            self.custom_colors[i * 3] = r
            self.custom_colors[i * 3 + 1] = g
            self.custom_colors[i * 3 + 2] = b

    def fill_group(self, group_name: str, color: Union[str, Tuple[int, int, int]]):
        """Fill a predefined group of keys (wasd, arrows, numbers, fn_row, nav, etc.)."""
        group_name = group_name.lower().strip()
        if group_name not in GROUPS:
            raise KeyError(f"Неизвестная группа: '{group_name}'. Доступно: {list(GROUPS.keys())}")
        for key in GROUPS[group_name]:
            self.set_key_color(key, color)

    def clear(self):
        """Clear all keys in buffer (turn all keys off)."""
        self.set_all_keys((0, 0, 0))

    # ----------------------------------------------------
    # Real-Time Streaming (Live Sync Light 0x1D)
    # ----------------------------------------------------

    def stream_frame(self, colors: Optional[List[int]] = None):
        """
        Send a real-time live frame directly to LEDs without saving to flash.
        Perfect for animations, audio visualizers, and games.
        """
        buf = colors if colors is not None else self.custom_colors
        chunks = (self.TOTAL_BYTES + self.CHUNK_LEN - 1) // self.CHUNK_LEN
        for c in range(chunks):
            offset = c * self.CHUNK_LEN
            chunk = buf[offset:offset + self.CHUNK_LEN]
            self._send_cmd(CMD_LIVE_SYNC, offset, chunk)

    def close_stream(self):
        """Exit live streaming mode (0x1E)."""
        self._send_cmd(CMD_CLOSE_SYNC, 0, [])

    # ----------------------------------------------------
    # TFT Screen Control & Reset
    # ----------------------------------------------------

    def screen_home(self):
        """Switch TFT screen to Home Page (standard dashboard with status/clock)."""
        crc = _crc16_modbus([11, 0, 0])
        packet = [0xA5, 0x5A, 11, 0, 0, crc[0], crc[1]]
        self._send_cmd(CMD_SCREEN_INFO, 0, packet)
        self._send_cmd(CMD_SCREEN_FINISH, 0, [])

    def screen_picture(self):
        """Switch TFT screen to custom static Picture page."""
        crc = _crc16_modbus([13, 0, 0])
        packet = [0xA5, 0x5A, 13, 0, 0, crc[0], crc[1]]
        self._send_cmd(CMD_SCREEN_INFO, 0, packet)
        self._send_cmd(CMD_SCREEN_FINISH, 0, [])

    def screen_gif(self):
        """Switch TFT screen to custom GIF animation page."""
        crc = _crc16_modbus([15, 0, 0])
        packet = [0xA5, 0x5A, 15, 0, 0, crc[0], crc[1]]
        self._send_cmd(CMD_SCREEN_INFO, 0, packet)
        self._send_cmd(CMD_SCREEN_FINISH, 0, [])

    def screen_sync_time(self):
        """Synchronize current system date and time to the TFT screen."""
        now = datetime.datetime.now()
        h, m, s = now.hour, now.minute, now.second
        yy, wd, mo, dd = now.year % 100, now.isoweekday(), now.month, now.day

        time_header = [0xA5, 0x5A, 9, 0, 3, 195, 225]
        time_payload = [h, m, s]
        date_header = [0xA5, 0x5A, 10, 0, 4, 1, 80]
        date_payload = [yy, wd, mo, dd]

        for _ in range(3):
            self._send_cmd(CMD_SCREEN_INFO, 0, time_header)
            self._send_cmd(CMD_SCREEN_DATA, 0, time_payload)
            self._send_cmd(CMD_SCREEN_FINISH, 0, [])
            self._send_cmd(CMD_SCREEN_INFO, 0, date_header)
            self._send_cmd(CMD_SCREEN_DATA, 0, date_payload)
            self._send_cmd(CMD_SCREEN_FINISH, 0, [])

    def screen_wake(self):
        """Wake up TFT screen, switch to Home page and sync current time."""
        self.screen_home()
        self.screen_sync_time()

    def upload_screen_image(self, image_or_path: Union[str, "Image.Image"]):
        """
        Upload a 128x128 RGB image to the keyboard TFT screen and activate Picture mode.
        Supports file paths (PNG, JPG, BMP, WebP) or PIL Image objects.
        """
        if not HAS_PIL:
            raise ImportError("Библиотека Pillow не установлена. Установите: pip install pillow (или pip install \"hator-keyboard[all]\")")
        if isinstance(image_or_path, str):
            img = Image.open(image_or_path)
        else:
            img = image_or_path

        pixels = image_to_rgb565(img, 128, 128)

        # 1. Start transfer packet
        self._send_cmd(CMD_SCREEN_INFO, 0, [165, 90, 16, 0, 1, 197, 177, 1])
        time.sleep(0.3)

        # 2. Header packet
        self._send_cmd(CMD_SCREEN_DATA, 0, [165, 90, 12, 128, 0, 3, 208])

        # 3. Stream 32768 image bytes in 56-byte chunks
        chunk_len = self.CHUNK_LEN
        total = len(pixels)
        chunks = (total + chunk_len - 1) // chunk_len
        for c in range(chunks):
            offset = c * chunk_len
            chunk = pixels[offset:offset + chunk_len]
            self._send_cmd(CMD_SCREEN_DATA, offset, chunk)

        # 4. Finish packet
        self._send_cmd(CMD_SCREEN_FINISH, 0, [])

        # 5. Switch to Picture page
        self.screen_picture()

    def update_system_hud(self):
        """Render current system monitoring stats and send to TFT screen."""
        img = create_system_hud_image()
        self.upload_screen_image(img)

    def reset_keyboard(self):
        """Factory reset all keyboard settings (Command 0x20)."""
        self._send_cmd(CMD_RESET, 0, [])
