# Adapted from the Jackal UEFI recreation project tooling (MIT, same author); generalized for reuse.
"""零依赖 PNG 编码 + 抽样渲染（供多模态核对——agent 的"眼睛"）。

NES_PALETTE 为 2C02 标准 64 色。attr 语义（由目标 ROM 的 OAM 展开例程确认）：
bit6=H 翻转、bit7=V 翻转——这是 OAM 硬件"原地镜像"，锚点不移动。
若目标 ROM 另有对象级翻转标志（坐标取负并移位一类，如 $10 语义），那是展开例程
的对象级逻辑，不在这份按表直渲的采样渲染器范围内。
"""
import struct, zlib
from pathlib import Path
from extractors import decode_tile, flip_h, flip_v

NES_PALETTE = [
    ( 84, 84, 84),(  0, 30,116),(  8, 16,144),( 48,  0,136),( 68,  0,100),( 92,  0, 48),( 84,  4,  0),( 60, 24,  0),
    ( 32, 42,  0),(  8, 58,  0),(  0, 64,  0),(  0, 60,  0),(  0, 50, 60),(  0,  0,  0),(  0,  0,  0),(  0,  0,  0),
    (152,150,152),(  8, 76,196),( 48, 50,236),( 92, 30,228),(136, 20,176),(160, 20,100),(152, 34, 32),(120, 60,  0),
    ( 84, 90,  0),( 40,114,  0),(  8,124,  0),(  0,118, 40),(  0,102,120),(  0,  0,  0),(  0,  0,  0),(  0,  0,  0),
    (236,238,236),( 76,154,236),(120,124,236),(176, 98,236),(228, 84,236),(236, 88,180),(236,106,100),(212,136, 32),
    (160,170,  0),(116,196,  0),( 76,208, 32),( 56,204,108),( 56,180,204),(  0,  0,  0),(  0,  0,  0),(  0,  0,  0),
    (236,238,236),(168,204,236),(188,188,236),(212,178,236),(236,174,236),(236,174,212),(236,180,176),(228,196,144),
    (204,210,120),(180,222,120),(168,226,144),(152,226,180),(160,214,228),(  0,  0,  0),(  0,  0,  0),(  0,  0,  0),
]

def write_png(path, w, h, rgb):
    def chunk(tag, payload):
        c = tag + payload
        return struct.pack('>I', len(payload)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
    if len(rgb) != w * h * 3:
        raise ValueError('rgb length mismatch')
    raw = b''.join(b'\x00' + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
           + chunk(b'IDAT', zlib.compress(raw, 9))
           + chunk(b'IEND', b''))
    Path(path).write_bytes(png)

def _canvas(w, h, color=(0, 0, 0)):
    return bytearray(bytes(color) * (w * h))

def _put_px(buf, w, h, x, y, rgb):
    if 0 <= x < w and 0 <= y < h:
        buf[(y * w + x) * 3:(y * w + x) * 3 + 3] = bytes(rgb)

def render_chr_page(chr_ram, palette, out_path, base=0, tiles_x=16, tiles_y=16):
    w, h = tiles_x * 8, tiles_y * 8
    buf = _canvas(w, h)
    for i in range(tiles_x * tiles_y):
        t = decode_tile(chr_ram[(base + i) * 16:(base + i) * 16 + 16])
        ox, oy = (i % tiles_x) * 8, (i // tiles_x) * 8
        for y in range(8):
            for x in range(8):
                _put_px(buf, w, h, ox + x, oy + y, NES_PALETTE[palette[t[y][x]] & 0x3F])
    write_png(out_path, w, h, bytes(buf))

def render_metasprite(chr_ram, ms, out_path, palette=(0x21, 0x11, 0x01, 0x31), size=48):
    buf = _canvas(size, size, (40, 40, 40))
    cx, cy = size // 2, size // 2
    for s in ms['sprites']:
        t = decode_tile(chr_ram[s['tile'] * 16:s['tile'] * 16 + 16])
        if s['attr'] & 0x40:
            t = flip_h(t)  # 表 attr 位 = OAM 硬件原地镜像，锚点不动
        if s['attr'] & 0x80:
            t = flip_v(t)
        for y in range(8):
            for x in range(8):
                c = t[y][x]
                if c:
                    _put_px(buf, size, size, cx + s['x'] + x, cy + s['y'] + y,
                            NES_PALETTE[palette[c] & 0x3F])
    write_png(out_path, size, size, bytes(buf))

def render_layout_screen(chr_ram, layout_rows, defs, pals, out_path, cols=16, rows=15):
    """layout 行 × 32x32 定义 × 大 tile 调色板 合成近似屏图（多模态核对用）。

    layout_rows: 每行若干"大 tile 索引"（一个索引对应 4x4 个 8x8 tile）；
    defs[idx] / pals[idx]: 该大 tile 的 16 个 tile 索引与 4 色 palette。
    合成出的屏图是近似（滚动/属性细节以目标实现为准），用途是抽样核对画面内容。
    """
    w, h = cols * 32, rows * 32
    buf = _canvas(w, h)
    for ry, row in enumerate(layout_rows[:rows]):
        for rx, idx in enumerate(row[:cols]):
            d = defs[idx]
            pal = pals[idx]
            for t in range(16):
                tile = decode_tile(chr_ram[d[t] * 16:d[t] * 16 + 16])
                ox, oy = rx * 32 + (t % 4) * 8, ry * 32 + (t // 4) * 8
                for y in range(8):
                    for x in range(8):
                        _put_px(buf, w, h, ox + x, oy + y, NES_PALETTE[pal[tile[y][x]] & 0x3F])
    write_png(out_path, w, h, bytes(buf))
