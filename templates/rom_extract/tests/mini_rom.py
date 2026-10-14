"""合成 mini-ROM：8 个 16KB PRG bank、CHR=0、mapper 2、垂直镜像。

内容布局（供全管线测试断言）：
  bank0 $8000: pattern segment（ppu $0000，RLE 字面拷贝 16 字节 0x00..0x0F）
  bank0 $8100: ptr_table 2 项 → $8110 / $8120
  bank0 $8110: 元精灵 count=1 {y:-8, tile:0, attr:0, x:-8}
  bank0 $8120: 元精灵 count=2 {y:0,tile:1,attr:0,x:-8} + {y:-8,tile:0,attr:$40,x:0}
  bank7 $C000: scene_table 1 项 → $C100
  bank7 $C100: load_table 1 项 {bank 0, $8000} + $FF
  bank7 $C200: palette 16 字节 0x0F,0x01..0x0F
"""
BANK = 0x4000

def build_mini_rom():
    banks = [bytearray(BANK) for _ in range(8)]
    # pattern segment: 段头（大端 ppu 地址 $0000）+ RLE 字面 16 字节 + 结束
    seg = bytes([0x00, 0x00, 0x90]) + bytes(range(16)) + bytes([0xFF])
    banks[0][0x0000:0x0000 + len(seg)] = seg
    # 元精灵 + 指针表
    banks[0][0x0100:0x0104] = bytes([0x10, 0x81, 0x20, 0x81])
    banks[0][0x0110:0x0115] = bytes([0x01, 0xF8, 0x00, 0x00, 0xF8])
    banks[0][0x0120:0x0129] = bytes([0x02, 0x00, 0x01, 0x00, 0xF8, 0xF8, 0x00, 0x40, 0x00])
    # scene 表 + load 表 + palette
    banks[7][0x0000:0x0002] = bytes([0x00, 0xC1])
    banks[7][0x0100:0x0104] = bytes([0x00, 0x00, 0x80, 0xFF])
    banks[7][0x0200:0x0210] = bytes([0x0F] + list(range(1, 16)))
    header = bytes([0x4E, 0x45, 0x53, 0x1A, 8, 0, 0x21, 0] + [0] * 8)
    return header + b''.join(bytes(b) for b in banks)

def mini_registry():
    from tables import TableEntry
    return [
        TableEntry('tblMiniSceneTable', 7, 0xC000, 'scene_table', 1, 'mini_rom.py', 'fixture'),
        TableEntry('tblMiniLoadTable', 7, 0xC100, 'load_table', 1, 'mini_rom.py', 'fixture'),
        TableEntry('tblMiniPatternSegment', 0, 0x8000, 'ai_raw', 20, 'mini_rom.py', 'segment header+RLE'),
        TableEntry('tblMiniPtrTable', 0, 0x8100, 'ptr_table', 2, 'mini_rom.py', 'fixture'),
        TableEntry('tblMiniMeta1', 0, 0x8110, 'metasprite', 1, 'mini_rom.py', 'fixture'),
        TableEntry('tblMiniMeta2', 0, 0x8120, 'metasprite', 2, 'mini_rom.py', 'fixture'),
        TableEntry('tblMiniPalette', 7, 0xC200, 'palette', 16, 'mini_rom.py', 'fixture'),
    ]
