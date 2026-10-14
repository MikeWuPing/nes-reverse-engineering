# Adapted from the Jackal UEFI recreation project tooling (MIT, same author); generalized for reuse.
"""结构校验：返回错误字符串列表，空列表 = 通过。"""
from tables import cpu_to_offset, entry_length, entry_bytes, BANK_SIZE

def validate_registry(rom, registry):
    errors = []
    # 登记名必须唯一：name 是 bin 文件名与 manifest 键，重名会静默互相覆盖
    seen = set()
    for e in registry:
        if e.name in seen:
            errors.append(f'{e.name}: duplicate registration name ({e.asm_ref})')
        seen.add(e.name)
    for e in registry:
        if not (0 <= e.bank < len(rom.banks)):
            errors.append(f'{e.name}: bank {e.bank} out of range 0..{len(rom.banks) - 1} ({e.asm_ref})')
        try:
            off = cpu_to_offset(e.bank, e.cpu) % BANK_SIZE
            n = entry_length(e)
            if off + n > BANK_SIZE:
                errors.append(f'{e.name}: offset ${off:04X}+len {n} overruns bank {e.bank} ({e.asm_ref})')
        except Exception as ex:
            errors.append(f'{e.name}: {ex} ({e.asm_ref})')
        if e.kind == 'metasprite' and not (0 <= e.count <= 64):
            errors.append(f'{e.name}: sprite count {e.count} out of range ({e.asm_ref})')
    # 指针回环：ptr_table 的每个非零 dw 必须指向某条已登记条目的起始 cpu（同 bank）
    for e in registry:
        if e.kind != 'ptr_table':
            continue
        try:
            raw = entry_bytes(rom, e)
        except Exception:
            continue
        targets = set(x.cpu for x in registry if x.bank == e.bank and x is not e)
        for i in range(0, len(raw) - 1, 2):
            ptr = raw[i] | (raw[i + 1] << 8)
            if ptr and ptr not in targets:
                errors.append(f'{e.name}[{i // 2}]: dw ${ptr:04X} not a registered entry in bank {e.bank} ({e.asm_ref})')
    return errors
