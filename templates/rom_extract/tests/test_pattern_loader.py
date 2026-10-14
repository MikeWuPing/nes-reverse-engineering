import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pattern_loader import decode_rle, parse_segment, parse_load_table, load_scene
from ines import Rom

def mk_rom(banks):
    return Rom({'prg_banks': len(banks)}, [bytes(b) for b in banks])

class TestDecodeRle(unittest.TestCase):
    def test_literal_run(self):
        out, end = decode_rle(bytes([0x83, 1, 2, 3, 0xFF, 9, 9]), 0)
        self.assertEqual(out, bytes([1, 2, 3]))
        self.assertEqual(end, 5)

    def test_repeat_run(self):
        out, _ = decode_rle(bytes([0x03, 0xAB, 0xFF]), 0)
        self.assertEqual(out, bytes([0xAB] * 3))

    def test_count_zero_means_256(self):
        # 6502 DEC/BNE 先减后判：计数 0 按 256
        out, _ = decode_rle(bytes([0x80] + [7] * 256 + [0xFF]), 0)
        self.assertEqual(len(out), 256)

class TestSegmentAndTable(unittest.TestCase):
    def test_segment_header_big_endian_and_payload(self):
        b2 = bytearray(0x4000)
        b2[0x10:0x16] = bytes([0x20, 0x00, 0x82, 0xAA, 0xBB, 0xFF])
        rom = mk_rom([bytearray(0x4000)] * 2 + [b2] + [bytearray(0x4000)] * 5)
        addr, payload = parse_segment(rom, 2, 0x8010)
        self.assertEqual(addr, 0x2000)
        self.assertEqual(payload, bytes([0xAA, 0xBB]))

    def test_load_table_until_ff(self):
        b7 = bytearray(0x4000)
        b7[0x100:0x107] = bytes([2, 0x10, 0x80, 3, 0x20, 0x81, 0xFF])
        rom = mk_rom([bytearray(0x4000)] * 7 + [b7])
        self.assertEqual(parse_load_table(rom, 0xC100), [(2, 0x8010), (3, 0x8120)])

    def test_load_scene_applies_payloads(self):
        b7 = bytearray(0x4000)
        b7[0:2] = bytes([0x00, 0xC1])
        b7[0x100:0x104] = bytes([1, 0x00, 0x80, 0xFF])
        b1 = bytearray(0x4000)
        b1[0:5] = bytes([0x00, 0x02, 0x02, 0xEE, 0xFF])
        rom = mk_rom([bytearray(0x4000), b1] + [bytearray(0x4000)] * 5 + [b7])
        chr_ram = load_scene(rom, 0xC000, 0)
        self.assertEqual(len(chr_ram), 0x4000)
        self.assertEqual(chr_ram[0x0002:0x0004], bytes([0xEE, 0xEE]))

    def test_scene_overrun_rejected(self):
        b7 = bytearray(0x4000)
        b7[0:2] = bytes([0x00, 0xC1])
        b7[0x100:0x104] = bytes([1, 0x00, 0x80, 0xFF])
        b1 = bytearray(0x4000)
        b1[0:20] = bytes([0xFF, 0xF0, 0x90]) + bytes(16) + bytes([0xFF])  # ppu $FFF0 + 16 字节，越界
        rom = mk_rom([bytearray(0x4000), b1] + [bytearray(0x4000)] * 5 + [b7])
        with self.assertRaises(ValueError):
            load_scene(rom, 0xC000, 0)

if __name__ == '__main__':
    unittest.main()
