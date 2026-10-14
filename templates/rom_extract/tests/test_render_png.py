import sys, struct, unittest, zlib, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from render_png import write_png, render_metasprite, render_chr_page, render_layout_screen, NES_PALETTE

class TestPng(unittest.TestCase):
    def test_png_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 't.png'
            write_png(p, 4, 4, bytes([255, 0, 0] * 16))
            data = p.read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            ln, tag = struct.unpack('>I4s', data[8:16])
            self.assertEqual(tag, b'IHDR')
            w, h = struct.unpack('>II', data[16:24])
            self.assertEqual((w, h), (4, 4))
            pos, idat = 8, b''
            while pos < len(data):
                n, t = struct.unpack('>I4s', data[pos:pos + 8])
                crc = struct.unpack('>I', data[pos + 8 + n:pos + 12 + n])[0]
                self.assertEqual(crc, zlib.crc32(data[pos + 4:pos + 8 + n]) & 0xFFFFFFFF)
                if t == b'IDAT':
                    idat += data[pos + 8:pos + 8 + n]
                pos += 12 + n
            self.assertEqual(len(zlib.decompress(idat)), 4 * (1 + 4 * 3))

    def test_palette_size(self):
        self.assertEqual(len(NES_PALETTE), 64)
        self.assertTrue(all(len(c) == 3 for c in NES_PALETTE))

class TestRender(unittest.TestCase):
    def test_metasprite_flip_runs(self):
        chr_ram = bytearray(0x4000)
        chr_ram[32:40] = bytes([0xF0] * 8)
        chr_ram[40:48] = bytes([0xF0] * 8)
        ms = {'count': 1, 'sprites': [{'x': 0, 'tile': 2, 'attr': 0x40, 'y': 0}]}
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'm.png'
            render_metasprite(chr_ram, ms, p)
            self.assertTrue(p.exists() and p.stat().st_size > 60)

    def test_chr_page_size(self):
        chr_ram = bytearray(0x4000)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'c.png'
            render_chr_page(chr_ram, list(range(16)), p)
            data = p.read_bytes()
            w, h = struct.unpack('>II', data[16:24])
            self.assertEqual((w, h), (128, 128))

def _read_png_pixels(path):
    """测试用最小 PNG 回读（本模板 PNG 固定 filter 0、truecolor）。"""
    data = Path(path).read_bytes()
    pos, idat, w, h = 8, b'', 0, 0
    while pos < len(data):
        n, t = struct.unpack('>I4s', data[pos:pos + 8])
        payload = data[pos + 8:pos + 8 + n]
        if t == b'IHDR':
            w, h = struct.unpack('>II', payload[:8])
        if t == b'IDAT':
            idat += payload
        pos += 12 + n
    raw = zlib.decompress(idat)
    stride = 1 + w * 3
    return w, h, [raw[y * stride + 1:(y + 1) * stride] for y in range(h)]

def _px(rows, x, y):
    o = x * 3
    return tuple(rows[y][o:o + 3])

class TestFlipPlacementAndLayout(unittest.TestCase):
    def _chr_with_corner_pixel(self):
        chr_ram = bytearray(0x4000)
        chr_ram[3 * 16] = 0x80  # tile 3 的 (0,0) 像素置位（lo 平面）
        return chr_ram

    def test_hflip_is_in_place_mirror(self):
        ms = {'count': 1, 'sprites': [{'x': 0, 'y': 0, 'tile': 3, 'attr': 0x40}]}
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'h.png'
            render_metasprite(self._chr_with_corner_pixel(), ms, p)
            w, h, rows = _read_png_pixels(p)
            self.assertEqual(_px(rows, 24 + 7, 24), (8, 76, 196))  # 亮点镜像到 (7,0)
            self.assertEqual(_px(rows, 24, 24), (40, 40, 40))

    def test_vflip_is_in_place_mirror(self):
        ms = {'count': 1, 'sprites': [{'x': 0, 'y': 0, 'tile': 3, 'attr': 0x80}]}
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'v.png'
            render_metasprite(self._chr_with_corner_pixel(), ms, p)
            w, h, rows = _read_png_pixels(p)
            self.assertEqual(_px(rows, 24, 24 + 7), (8, 76, 196))
            self.assertEqual(_px(rows, 24, 24), (40, 40, 40))

    def test_layout_screen_smoke(self):
        chr_ram = bytearray(0x4000)
        chr_ram[0:16] = bytes([0xFF] * 8 + [0] * 8)  # tile 0 全像素色号 1
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'l.png'
            render_layout_screen(chr_ram, [[0]], [[0] * 16], [[0x21, 0x11, 0x01, 0x31]], p, cols=1, rows=1)
            w, h, rows = _read_png_pixels(p)
            self.assertEqual((w, h), (32, 32))
            self.assertEqual(_px(rows, 0, 0), (8, 76, 196))

if __name__ == '__main__':
    unittest.main()
