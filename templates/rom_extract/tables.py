# Adapted from the Jackal UEFI recreation project tooling (MIT, same author); generalized for reuse.
"""声明式表清单机制。

登记程序（每条登记必须执行，来自 NES 逆向实践）：
  1. 读目标 ROM 的反汇编，找到表定义与读它的代码，记录 asm_ref（文件:行号）；
  2. 定位地址：优先 .PAD/org 明示地址；其次唯一字节签名（locate_unique）；
     再不行用读表的代码指令交叉引用消歧；
  3. 条目数与反汇编的 dw/db 条目数核对一致——不一致时先怀疑登记，再怀疑反汇编；
  4. 写入 REGISTRY，附 evidence（证据字符串：.PAD 地址 / 签名 hex / ptr-roundtrip / 实测值）；
  5. 跑 validate_registry，必须零错误。

铁律：**校验报错时修正登记，绝不放宽校验。**
"""
from dataclasses import dataclass

BANK_SIZE = 0x4000
FIXED_BANK = 7  # UxROM 惯例：8x16KB 时 bank 7 固定 $C000-$FFFF；其他 mapper 改这里

class RegistryError(Exception):
    pass

KIND_SIZES = {  # kind -> 每条目字节数（None = 特殊长度规则，见 entry_length）
    'tile2bpp': 16, 'palette': 1, 'metasprite': None,
    'ptr_table': 2, 'layout_row': 1, 'metatile32': 16,
    'tile_palette': 1, 'ai_raw': 1, 'scene_table': 2, 'load_table': 3,
}

@dataclass(frozen=True)
class TableEntry:
    name: str      # 汇编标签名
    bank: int      # 0..7
    cpu: int       # CPU 地址（可切 bank: $8000-$BFFF；固定 bank: $C000-$FFFF）
    kind: str
    count: int
    asm_ref: str   # 例 'Bank7.ASM:3054'
    evidence: str  # 例 '.PAD $D64F' / 'signature 04F003...' / 'ptr-roundtrip'

def cpu_to_offset(bank, cpu):
    if bank == FIXED_BANK:
        if not (0xC000 <= cpu <= 0xFFFF):
            raise RegistryError(f'cpu ${cpu:04X} outside fixed-bank window for bank {bank}')
        return bank * BANK_SIZE + (cpu - 0xC000)
    if not (0x8000 <= cpu <= 0xBFFF):
        raise RegistryError(f'cpu ${cpu:04X} outside switchable window for bank {bank}')
    return bank * BANK_SIZE + (cpu - 0x8000)

def locate_unique(bank_bytes, sig, name):
    hits = [i for i in range(len(bank_bytes) - len(sig) + 1)
            if bank_bytes[i:i + len(sig)] == sig]
    if len(hits) != 1:
        raise RegistryError(f'{name}: signature hits={len(hits)} (expect 1)')
    return hits[0]

def entry_length(entry):
    size = KIND_SIZES[entry.kind]
    if entry.kind == 'metasprite':
        return 1 + 4 * entry.count
    return size * entry.count

def entry_bytes(rom, entry):
    off = cpu_to_offset(entry.bank, entry.cpu) % BANK_SIZE
    n = entry_length(entry)
    data = rom.banks[entry.bank][off:off + n]
    if len(data) != n:
        raise RegistryError(f'{entry.name}: overruns bank {entry.bank}')
    return data

def by_name(name):
    return next(e for e in REGISTRY if e.name == name)

# 目标 ROM 的真实登记写在这里；模板默认留空。
REGISTRY = []

# 示例条目：演示字段填法，不是任何真实 ROM 的数据；替换为你的目标 ROM 的登记。
EXAMPLE_ENTRY = TableEntry('tblExamplePalette', 7, 0xC000, 'palette', 32,
                           'Example.ASM:1', 'placeholder — replace with a real registration')
