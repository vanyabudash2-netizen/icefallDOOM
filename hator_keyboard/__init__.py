"""
Hator Keyboard RGB Controller for Python
Compatible with Hator Icefall PRO (and other keyboards using WebHID protocol)
"""

__version__ = "0.2.0"

from .constants import (
    VENDOR_IDS,
    PRODUCT_IDS,
    USAGE_PAGE,
    USAGE,
    MODES,
    KEY_MAP,
    GROUPS,
    GROUPS as KEY_GROUPS,
    COLOR_PRESETS,
    DEFAULT_LIGHT_DATA,
)
from .keyboard import HatorKeyboard, parse_color
from .screen import image_to_rgb565, create_system_hud_image

__all__ = [
    "HatorKeyboard",
    "parse_color",
    "KEY_MAP",
    "KEY_GROUPS",
    "GROUPS",
    "MODES",
    "COLOR_PRESETS",
    "DEFAULT_LIGHT_DATA",
    "VENDOR_IDS",
    "PRODUCT_IDS",
    "USAGE_PAGE",
    "USAGE",
    "image_to_rgb565",
    "create_system_hud_image",
    "__version__",
]
