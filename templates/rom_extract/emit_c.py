# Adapted from the Jackal UEFI recreation project tooling (MIT, same author); generalized for reuse.
"""语言绑定代码生成器示例（C）。

主产物是语言中立的：assets/bin/*.bin + assets/manifest.json（CRC32 回归基线）。
C 数组只是适配层：换成 Rust/JS 等目标语言时，照本文件的形状换一个生成器即可，
bin 与 manifest 不变。确定性生成：同一 ROM 两跑字节一致（REGISTRY 顺序、固定换行、ASCII）。
"""
import json, zlib
from pathlib import Path
from tables import entry_bytes

def c_ident(name):
    s = ''.join(ch if (ch.isalnum() or ch == '_') else '_' for ch in name)
    return ('_' + s) if s[:1].isdigit() else s

def _hex_lines(data, per_line=12):
    return ['    ' + ','.join(f'0x{b:02X}' for b in data[i:i + per_line]) + ','
            for i in range(0, len(data), per_line)]

def emit_all(rom, registry, out_dir, prefix='rom_', generated_dir='generated', header_name='rom_assets'):
    out = Path(out_dir)
    gen = out / generated_dir
    bindir = out / 'assets' / 'bin'
    gen.mkdir(parents=True, exist_ok=True)
    bindir.mkdir(parents=True, exist_ok=True)
    # .c 与 .h 都只用 stdint.h：平台中立（绝不引入 Uefi.h 之类平台 SDK 头），且 .c 自包含。
    c_parts = ['/* Auto-generated. DO NOT EDIT. */',
               '#include <stdint.h>',
               f'#include "{header_name}.h"', '']
    h_parts = ['/* Auto-generated. DO NOT EDIT. */',
               f'#ifndef {header_name.upper()}_H', f'#define {header_name.upper()}_H', '',
               '#include <stdint.h>', '']
    manifest = {'tool': 'rom_extract', 'entries': []}
    for e in registry:
        raw = entry_bytes(rom, e)
        ident = prefix + c_ident(e.name)
        (bindir / f'{e.name}.bin').write_bytes(raw)
        c_parts.append(f'/* {e.name} bank{e.bank} cpu ${e.cpu:04X} asm {e.asm_ref} ({e.evidence}) */')
        c_parts.append(f'const uint8_t {ident}[{len(raw)}] = {{')
        c_parts += _hex_lines(raw)
        c_parts.append('};')
        c_parts.append('')
        h_parts.append(f'extern const uint8_t {ident}[{len(raw)}];')
        manifest['entries'].append({
            'name': e.name, 'bank': e.bank, 'cpu': f'0x{e.cpu:04X}',
            'kind': e.kind, 'count': e.count, 'length': len(raw),
            'crc32': f'0x{zlib.crc32(raw) & 0xFFFFFFFF:08X}',
            'asm_ref': e.asm_ref, 'evidence': e.evidence,
            'bin': f'assets/bin/{e.name}.bin',
        })
    h_parts += ['', f'#endif  /* {header_name.upper()}_H */']
    c_path = gen / f'{header_name}.c'
    h_path = gen / f'{header_name}.h'
    c_path.write_text('\n'.join(c_parts) + '\n', encoding='ascii', newline='\n')
    h_path.write_text('\n'.join(h_parts) + '\n', encoding='ascii', newline='\n')
    man_path = out / 'assets' / 'manifest.json'
    man_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True) + '\n',
                        encoding='ascii', newline='\n')
    return {'c': str(c_path), 'h': str(h_path), 'manifest': str(man_path), 'bin_dir': str(bindir)}
