# Adapted from the Jackal UEFI recreation project tooling (MIT, same author); generalized for reuse.
"""iNES 解析与 bank 切分（参考实现）。

宽容解析：只做基本结构校验，语义期望（PRG 数量、mapper、镜像方式）由调用方决定——
不同游戏/卡带形态不同，写死期望会挡住大部分 ROM。

窗口约定：本模板的 tables.py 默认按 UxROM（mapper 2）常见布局——
bank 0..N-2 映射 CPU $8000-$BFFF 可切换窗口，最后一个 bank 固定 $C000-$FFFF。
其他 mapper（MMC3 等）请按目标卡带的实际映射调整 tables.FIXED_BANK 与窗口。
"""
from pathlib import Path

BANK_SIZE = 0x4000
CHR_BANK_SIZE = 0x2000

class RomHeaderError(Exception):
    pass

class Rom:
    def __init__(self, header, banks, chr_rom=b'', path=None):
        self.header = header
        self.banks = tuple(banks)
        self.chr_rom = chr_rom
        self.path = path

def parse_header(raw):
    if len(raw) < 16 or raw[:4] != b'NES\x1a':
        raise RomHeaderError(f'bad magic: expected 4E 45 53 1A, got {raw[:4].hex()}')
    return {
        'prg_banks': raw[4],
        'chr_banks': raw[5],
        'mapper': (raw[6] >> 4) | (raw[7] & 0xF0),
        'vertical_mirroring': bool(raw[6] & 0x01),
    }

def load_rom(path):
    data = Path(path).read_bytes()
    header = parse_header(data[:16])
    prg_size = header['prg_banks'] * BANK_SIZE
    prg = data[16:16 + prg_size]
    if len(prg) != prg_size:
        raise RomHeaderError(f'prg size: expected {prg_size}, got {len(prg)}')
    chr_size = header['chr_banks'] * CHR_BANK_SIZE
    chr_rom = data[16 + prg_size:16 + prg_size + chr_size]
    if len(chr_rom) != chr_size:
        raise RomHeaderError(f'chr size: expected {chr_size}, got {len(chr_rom)}')
    banks = [prg[i * BANK_SIZE:(i + 1) * BANK_SIZE] for i in range(header['prg_banks'])]
    return Rom(header, banks, chr_rom=chr_rom, path=str(path))
