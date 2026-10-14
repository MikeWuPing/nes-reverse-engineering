import sys, json, unittest, tempfile, zlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mini_rom import build_mini_rom, mini_registry
from ines import load_rom
from validate import validate_registry
from pattern_loader import load_scene
from extractors import parse_metasprite
from render_png import render_chr_page, render_metasprite
from run_extract import run

def write_rom(td):
    p = Path(td) / 'mini.nes'
    p.write_bytes(build_mini_rom())
    return p

class TestPipeline(unittest.TestCase):
    def test_validate_clean(self):
        with tempfile.TemporaryDirectory() as td:
            rom = load_rom(write_rom(td))
            self.assertEqual(validate_registry(rom, mini_registry()), [])

    def test_run_emits_manifest_and_bins(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'out'
            result = run(write_rom(td), out, registry=mini_registry())
            man = json.loads((out / 'assets' / 'manifest.json').read_text(encoding='ascii'))
            self.assertEqual(len(man['entries']), 7)
            meta1 = next(e for e in man['entries'] if e['name'] == 'tblMiniMeta1')
            self.assertEqual(meta1['crc32'],
                             f'0x{zlib.crc32(bytes([0x01, 0xF8, 0x00, 0x00, 0xF8])):08X}')
            self.assertTrue((out / 'generated' / 'rom_assets.c').exists())

    def test_two_runs_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            rom_path = write_rom(td)
            c1 = Path(run(rom_path, Path(td) / 'a', registry=mini_registry())['result']['c'])
            c2 = Path(run(rom_path, Path(td) / 'b', registry=mini_registry())['result']['c'])
            self.assertEqual(c1.read_bytes(), c2.read_bytes())

    def test_scene_load_and_decodes(self):
        with tempfile.TemporaryDirectory() as td:
            rom = load_rom(write_rom(td))
            chr_ram = load_scene(rom, 0xC000, 0)
            self.assertEqual(chr_ram[0x0000:0x0010], bytes(range(16)))  # pattern 落 $0000
            ms = parse_metasprite(bytes([0x01, 0xF8, 0x00, 0x00, 0xF8]))
            self.assertEqual(ms['sprites'][0]['y'], -8)

    def test_samplers_render(self):
        with tempfile.TemporaryDirectory() as td:
            rom = load_rom(write_rom(td))
            chr_ram = load_scene(rom, 0xC000, 0)
            p1 = Path(td) / 'page.png'
            render_chr_page(chr_ram, list(range(16)), p1)
            p2 = Path(td) / 'meta.png'
            render_metasprite(chr_ram, parse_metasprite(bytes([0x01, 0xF8, 0x00, 0x00, 0xF8])), p2)
            self.assertTrue(p1.stat().st_size > 60 and p2.stat().st_size > 60)

if __name__ == '__main__':
    unittest.main()
