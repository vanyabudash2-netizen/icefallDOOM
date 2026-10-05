"""
Basic unit tests for hator_keyboard package.
"""

import unittest
from hator_keyboard import (
    parse_color,
    KEY_MAP,
    KEY_GROUPS,
    MODES,
    COLOR_PRESETS,
    __version__,
)
from hator_keyboard.keyboard import _build_packet, _crc16_modbus


class TestHatorKeyboard(unittest.TestCase):

    def test_version(self):
        self.assertIsInstance(__version__, str)
        self.assertTrue(len(__version__) > 0)

    def test_parse_color_hex(self):
        self.assertEqual(parse_color("#FF0000"), (255, 0, 0))
        self.assertEqual(parse_color("00FF00"), (0, 255, 0))
        self.assertEqual(parse_color("#123456"), (0x12, 0x34, 0x56))

    def test_parse_color_names(self):
        self.assertEqual(parse_color("red"), (255, 0, 0))
        self.assertEqual(parse_color("green"), (0, 255, 0))
        self.assertEqual(parse_color("blue"), (0, 0, 255))
        self.assertEqual(parse_color("off"), (0, 0, 0))

    def test_parse_color_tuple(self):
        self.assertEqual(parse_color((10, 20, 30)), (10, 20, 30))
        self.assertEqual(parse_color([100, 150, 200]), (100, 150, 200))

    def test_parse_color_invalid(self):
        with self.assertRaises(ValueError):
            parse_color("unknown_color_name_xyz")

    def test_key_map(self):
        self.assertIn("esc", KEY_MAP)
        self.assertIn("w", KEY_MAP)
        self.assertIn("space", KEY_MAP)
        self.assertEqual(KEY_MAP["esc"], 0)

    def test_key_groups(self):
        self.assertIn("wasd", KEY_GROUPS)
        self.assertIn("arrows", KEY_GROUPS)
        self.assertEqual(KEY_GROUPS["wasd"], ["w", "a", "s", "d"])

    def test_modes(self):
        self.assertIn(0, MODES)
        self.assertEqual(MODES[0][0], "wave")
        self.assertIn(17, MODES)
        self.assertEqual(MODES[17][0], "custom")

    def test_build_packet(self):
        cmd = 0x14
        offset = 0
        pkt = _build_packet(cmd, offset)
        self.assertEqual(len(pkt), 63)
        self.assertEqual(pkt[0], cmd)
        self.assertEqual(pkt[1], 0)
        self.assertEqual(pkt[2], 0)
        # Checksum calculation: sum of packet bytes where bytes 4 and 5 are 0
        stored_cs = pkt[4] | (pkt[5] << 8)
        raw_sum = (sum(pkt[:4]) + sum(pkt[6:])) & 0xFFFF
        self.assertEqual(stored_cs, raw_sum)

    def test_crc16_modbus(self):
        crc = _crc16_modbus([11, 0, 0])
        self.assertEqual(len(crc), 2)


if __name__ == "__main__":
    unittest.main()
