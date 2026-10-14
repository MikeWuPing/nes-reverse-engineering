# Adapted from the Jackal UEFI recreation project tooling (MIT, same author); generalized for reuse.
"""提取管线骨架：解析 → 校验（零错误才继续）→ 产物三件套。

用法（登记好目标 ROM 的表之后）：
    python run_extract.py --rom path/to/game.nes --out build_dir

产物：<out>/generated/rom_assets.c/.h（语言绑定适配层，可换）、
      <out>/assets/bin/*.bin + <out>/assets/manifest.json（语言中立主产物，含 CRC32 基线）。
抽样渲染属验证步骤：用 render_png 对若干登记条目出图，多模态核对内容是否正确。
"""
import argparse
from pathlib import Path
import tables
from ines import load_rom
from validate import validate_registry
from emit_c import emit_all

def run(rom_path, out_dir, registry=None):
    registry = tables.REGISTRY if registry is None else registry
    rom = load_rom(rom_path)
    errors = validate_registry(rom, registry)
    if errors:
        raise SystemExit('validation failed:\n' + '\n'.join(errors))
    result = emit_all(rom, registry, Path(out_dir))
    return {'rom': rom, 'result': result}

def main():
    ap = argparse.ArgumentParser(description='NES ROM 资源提取管线')
    ap.add_argument('--rom', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    if not tables.REGISTRY:
        raise SystemExit('REGISTRY 为空：先按 tables.py 的登记程序登记目标 ROM 的表')
    run(args.rom, args.out)
    print(f'OK: {len(tables.REGISTRY)} entries -> {args.out}')

if __name__ == '__main__':
    main()
