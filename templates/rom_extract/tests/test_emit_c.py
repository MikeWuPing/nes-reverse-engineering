import sys, json, unittest, tempfile, zlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tables import TableEntry
from emit_c import emit_all, c_ident
from ines import Rom

class TestEmit(unittest.TestCase):
    def test_deterministic_and_complete(self):
        rom = Rom({}, [bytes([i & 0xFF for i in range(0x4000)])] * 8)
        reg = [TableEntry('tblA', 7, 0xC000, 'palette', 4, 'X.ASM:1', 'test'),
               TableEntry('tblB', 0, 0x8000, 'tile2bpp', 1, 'X.ASM:2', 'test')]
        with tempfile.TemporaryDirectory() as td:
            out1 = emit_all(rom, reg, Path(td) / 'r1')
            out2 = emit_all(rom, reg, Path(td) / 'r2')
            c1 = Path(out1['c']).read_bytes()
            c2 = Path(out2['c']).read_bytes()
            self.assertEqual(c1, c2)
            self.assertIn(b'rom_tblA', c1)
            self.assertIn(b'X.ASM:1', c1)
            self.assertIn(b'stdint.h', c1)          # 平台中立：用 stdint.h 不用 Uefi.h
            man = json.loads(Path(out1['manifest']).read_text(encoding='ascii'))
            self.assertEqual(len(man['entries']), 2)
            self.assertEqual(man['entries'][0]['name'], 'tblA')
            self.assertIn('crc32', man['entries'][0])
            bin0 = Path(out1['bin_dir']) / 'tblA.bin'
            self.assertEqual(zlib.crc32(bin0.read_bytes()) & 0xFFFFFFFF,
                             int(man['entries'][0]['crc32'], 16))

    def test_c_ident(self):
        self.assertEqual(c_ident('tblJeepUpDown_WaterSplash_'), 'tblJeepUpDown_WaterSplash_')
        self.assertEqual(c_ident('2bad'), '_2bad')

if __name__ == '__main__':
    unittest.main()
