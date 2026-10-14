import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ines import load_rom, parse_header, RomHeaderError

def mk_rom_bytes(prg_banks=8, chr_banks=0, flags6=0x21, flags7=0x00):
    header = bytes([0x4E, 0x45, 0x53, 0x1A, prg_banks, chr_banks, flags6, flags7] + [0] * 8)
    return header + bytes(prg_banks * 0x4000) + bytes([0xAB]) * (chr_banks * 0x2000)

class TestParseHeader(unittest.TestCase):
    def test_fields(self):
        h = parse_header(mk_rom_bytes()[:16])
        self.assertEqual(h['prg_banks'], 8)
        self.assertEqual(h['chr_banks'], 0)
        self.assertEqual(h['mapper'], 2)
        self.assertTrue(h['vertical_mirroring'])

    def test_rejects_bad_magic(self):
        with self.assertRaises(RomHeaderError):
            parse_header(bytes(16))

class TestLoadRom(unittest.TestCase):
    def _load(self, data):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'x.nes'
            p.write_bytes(data)
            return load_rom(p)

    def test_banks_and_shape(self):
        rom = self._load(mk_rom_bytes())
        self.assertEqual(len(rom.banks), 8)
        self.assertTrue(all(len(b) == 0x4000 for b in rom.banks))
        self.assertEqual(rom.chr_rom, b'')

    def test_chr_rom_captured_separately(self):
        rom = self._load(mk_rom_bytes(prg_banks=2, chr_banks=1))
        self.assertEqual(len(rom.banks), 2)
        self.assertEqual(rom.chr_rom, bytes([0xAB]) * 0x2000)

    def test_truncated_prg_rejected(self):
        with self.assertRaises(RomHeaderError):
            self._load(mk_rom_bytes()[:-1])

    def test_truncated_chr_rejected(self):
        with self.assertRaises(RomHeaderError):
            self._load(mk_rom_bytes(prg_banks=2, chr_banks=1)[:-1])

if __name__ == '__main__':
    unittest.main()
