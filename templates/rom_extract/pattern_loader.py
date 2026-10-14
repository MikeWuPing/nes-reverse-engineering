# Adapted from the Jackal UEFI recreation project tooling (MIT, same author); generalized for reuse.
"""RLE 装载链参考实现（load 表 → segment → RLE 流 → CHR RAM）。

**格式权威是目标 ROM 自己的装载例程**——先读懂它（控制字节语义、计数语义、
段头字节序），再对照本文件调整。本文件镜像的是一种常见形态：

  load 表   = 若干 {db bank, dw segmentCpu} + db $FF 结束
  segment   = ppuAddrHi, ppuAddrLo（注意：大端，先写 PPUADDR 高字节）, RLE 流
  RLE       = $FF 结束；bit7=1 字面拷贝 (b&0x7F) 字节；bit7=0 重复下一字节 (b&0x7F) 次；
              计数 0 按 256（6502 DEC/BNE 先减后判语义）
"""
CHR_RAM_SIZE = 0x4000  # pattern $0000-$1FFF + nametable $2000-$3FFF

def decode_rle(data, start):
    """返回 (解出的字节, 绝对结束位置)。"""
    out = bytearray()
    i = start
    while True:
        b = data[i]; i += 1
        if b == 0xFF:
            return bytes(out), i
        count = b & 0x7F
        if count == 0:
            count = 256
        if b & 0x80:
            out += data[i:i + count]; i += count
        else:
            out += bytes([data[i]]) * count; i += 1

def parse_segment(rom, bank, cpu):
    d = rom.banks[bank]
    o = cpu - 0x8000
    ppu_addr = (d[o] << 8) | d[o + 1]
    payload, _ = decode_rle(d, o + 2)
    return ppu_addr, payload

def parse_load_table(rom, table_cpu, bank=7):
    """load 表默认位于固定 bank（UxROM 惯例为最后一个）；读到 $FF 结束。"""
    d = rom.banks[bank]
    o = table_cpu - (0xC000 if bank == 7 else 0x8000)
    entries = []
    while d[o] != 0xFF:
        entries.append((d[o], d[o + 1] | (d[o + 2] << 8)))
        o += 3
    return entries

def load_scene(rom, scene_table_cpu, scene_index, bank=7):
    """按场景索引装载：scene 表 dw 取 load 表地址，逐个应用 segment 到 CHR RAM。"""
    d = rom.banks[bank]
    o = scene_table_cpu - (0xC000 if bank == 7 else 0x8000) + scene_index * 2
    table_cpu = d[o] | (d[o + 1] << 8)
    chr_ram = bytearray(CHR_RAM_SIZE)
    for b, seg_cpu in parse_load_table(rom, table_cpu, bank):
        ppu_addr, payload = parse_segment(rom, b, seg_cpu)
        if ppu_addr + len(payload) > CHR_RAM_SIZE:
            raise ValueError(
                f'segment ${seg_cpu:04X} bank {b} overruns CHR RAM at ${ppu_addr:04X}+{len(payload)}')
        chr_ram[ppu_addr:ppu_addr + len(payload)] = payload
    return chr_ram
