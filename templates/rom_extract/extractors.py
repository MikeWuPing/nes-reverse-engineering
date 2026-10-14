# Adapted from the Jackal UEFI recreation project tooling (MIT, same author); generalized for reuse.
"""NES 数据格式解码器（纯函数，语言/平台无关）。

元精灵字节序 {y, tile, attr, x} 是 NES 元精灵表的常见布局（OAM 序）。这是参考约定，
不是绝对真理：**以目标 ROM 的元精灵展开例程为准**——先读它怎么写 OAM，再决定解析顺序。
attr 的 bit6/bit7 是 OAM 硬件原地镜像（不移动锚点）；对象级的翻转补偿（坐标取负并移位一类）属展开/渲染例程，不属提取侧。
"""

def decode_tile(tile16):
    """16 字节 2bpp planar tile → 8x8 色号（0-3）。前 8 行低平面、后 8 行高平面。"""
    if len(tile16) != 16:
        raise ValueError('tile must be 16 bytes')
    rows = []
    for r in range(8):
        lo, hi = tile16[r], tile16[8 + r]
        rows.append([(((hi >> (7 - c)) & 1) << 1) | ((lo >> (7 - c)) & 1) for c in range(8)])
    return rows

def decode_tiles(data):
    if len(data) % 16:
        raise ValueError(f'tile data length {len(data)} not multiple of 16')
    return [decode_tile(data[i:i + 16]) for i in range(0, len(data), 16)]

def _s8(b):
    return b - 256 if b >= 128 else b

def parse_metasprite(data):
    """{count, sprites:[{y, tile, attr, x}]}，y/x 为有符号偏移。"""
    count = data[0]
    if len(data) < 1 + 4 * count:
        raise ValueError(f'metasprite truncated: count {count}, have {len(data)}')
    sprites = []
    for i in range(count):
        o = 1 + 4 * i
        sprites.append({'y': _s8(data[o]), 'tile': data[o + 1], 'attr': data[o + 2], 'x': _s8(data[o + 3])})
    return {'count': count, 'sprites': sprites}

def parse_palette(data):
    return list(data)

def parse_metatile32(data):
    """32x32 大 tile = 4x4 个 8x8 tile 的索引表（16 项）。"""
    if len(data) != 16:
        raise ValueError('32x32 metatile must be 16 tile indexes')
    return list(data)

def flip_h(tile):
    return [list(reversed(row)) for row in tile]

def flip_v(tile):
    return list(reversed(tile))
