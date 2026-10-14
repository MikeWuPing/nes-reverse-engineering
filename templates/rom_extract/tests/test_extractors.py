import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from extractors import decode_tile, decode_tiles, parse_metasprite, parse_palette, parse_metatile32, flip_h

class TestTile(unittest.TestCase):
    def test_lo_plane_only(self):
        t = decode_tile(bytes([0xFF] * 8 + [0x00] * 8))
        self.assertTrue(all(px == 1 for row in t for px in row))

    def test_hi_plane_only(self):
        t = decode_tile(bytes([0x00] * 8 + [0xFF] * 8))
        self.assertTrue(all(px == 2 for row in t for px in row))

    def test_bit_pair_combination(self):
        # 第 0 行：lo bit7=1, hi bit7=1 → 色号 3；bit6 均 0 → 色号 0
        t = decode_tile(bytes([0x80] + [0] * 7 + [0x80] + [0] * 7))
        self.assertEqual(t[0][0], 3)
        self.assertEqual(t[0][1], 0)

    def test_decode_tiles_count_and_guard(self):
        self.assertEqual(len(decode_tiles(bytes(32))), 2)
        with self.assertRaises(ValueError):
            decode_tiles(bytes(17))

class TestMetasprite(unittest.TestCase):
    def test_four_byte_oam_order(self):
        # 字节序 {y, tile, attr, x}（OAM 序）；attr bit6=H 翻转、bit7=V 翻转
        ms = parse_metasprite(bytes([
            0x02,
            0xF0, 0x03, 0x00, 0xF8,
            0x00, 0x05, 0x40, 0x00]))
        self.assertEqual(ms['count'], 2)
        self.assertEqual(ms['sprites'][0], {'y': -16, 'tile': 3, 'attr': 0x00, 'x': -8})
        self.assertEqual(ms['sprites'][1], {'y': 0, 'tile': 5, 'attr': 0x40, 'x': 0})

    def test_truncated_rejected(self):
        with self.assertRaises(ValueError):
            parse_metasprite(bytes([0x03, 0, 0, 0, 0]))

class TestOthers(unittest.TestCase):
    def test_palette_passthrough(self):
        self.assertEqual(parse_palette(bytes(range(16))), list(range(16)))

    def test_metatile32_shape(self):
        self.assertEqual(parse_metatile32(bytes(range(16))), list(range(16)))
        with self.assertRaises(ValueError):
            parse_metatile32(bytes(15))

    def test_flip_h(self):
        tile = [[0, 1, 2, 3, 0, 0, 0, 0]] + [[0] * 8] * 7
        self.assertEqual(flip_h(tile)[0][0], 0)
        self.assertEqual(flip_h(tile)[0][7], 0)
        self.assertEqual(flip_h(tile)[0][4], 3)

if __name__ == '__main__':
    unittest.main()
