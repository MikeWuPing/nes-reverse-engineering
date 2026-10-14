# rom_extract 模板适配指南

这份模板不是"拿来即用的提取器"，而是一套**形状确定、内容留白**的提取管线骨架：通用机制已经写好并有 48 项测试兜底，与目标 ROM 绑定的部分——iNES 期望、bank 窗口、装载格式、表登记——需要你按目标 ROM 逐个定制。哪些文件必须改、哪些通常不用改，判断标准只有一条：**它是否依赖"这个游戏"的既定事实**。

环境要求：Python 3.10+，纯标准库、零第三方依赖。

## 必须按目标 ROM 定制的三处

### iNES 期望与 bank 窗口

`ines.py` 有意只做宽容解析——校验 magic、按头字段切出 PRG/CHR bank，把语义期望（PRG 数量、mapper、镜像方式）留给调用方：不同卡带形态不同，把期望写死会在第一步就挡住目标 ROM。真正决定地址换算的是 `tables.py` 的 `FIXED_BANK` 常量与 `cpu_to_offset` 里的窗口判定：模板默认按 UxROM（mapper 2）惯例，bank 0..N-2 映射到 `$8000-$BFFF` 可切换窗口，最后一个 bank 固定映射 `$C000-$FFFF`。目标 ROM 是 MMC3 等其他 mapper 时（分页粒度不同、固定窗口位置不同），改的就是 `FIXED_BANK` 与这两处窗口判定；同一"末 bank 固定"惯例也出现在 `pattern_loader.py` 中 `parse_load_table` / `load_scene` 的默认参数 `bank=7` 上，换 mapper 时一并核对。改完照 `tests/test_tables.py` 的地址映射用例补一条目标形态的断言，让新窗口同样有回归。

### 装载格式（`pattern_loader.py`）

`pattern_loader.py` 镜像的是"load 表 → segment → RLE 流 → CHR RAM"这一种常见形态的**参考实现**：段头是大端 PPU 地址、RLE 用 bit7 区分字面拷贝与重复、计数 0 按 256。**格式的唯一权威是目标 ROM 自己的装载例程**，不是这份实现——控制字节语义、计数语义、段头字节序都可能不同，字节对压缩、整段直拷、多段累加、按行交错都是常见的变体。正确顺序是先读反汇编中的装载例程，把语义结论写成注释，再回来对照改代码；反过来"先跑模板、对不上再猜"会把时间花在错误的方向上。`parse_load_table`、`parse_segment`、`decode_rle`、`load_scene` 四个函数的职责划分可原样保留，换的是其中的格式语义。

### REGISTRY 登记

`tables.py` 的 `REGISTRY` 默认是空表加一条标注为示例的 `EXAMPLE_ENTRY`，这是刻意的：登记工作必须针对目标 ROM 逐条做实，没有捷径。每条登记走五步——读目标 ROM 的反汇编，找到表定义与读它的代码，记录 `asm_ref`（`文件:行号`）；定位地址，优先 `.PAD`/`org` 明示地址，其次 `locate_unique` 唯一字节签名（命中数必须恰为 1），再不行用读表代码的指令交叉引用消歧；把 `count` 与反汇编里这张表的 `dw`/`db` 条目数逐个核对；写入 `REGISTRY`，附上 `evidence`（`.PAD` 地址 / 签名 hex / `ptr-roundtrip` / 实测值）；跑 `validate_registry` 直到零错误。铁律：**校验报错时修正登记，绝不放宽校验**——报错几乎总是地址抄错或 `count` 数错，不是校验太严。

## 通常不用改的通用机制

这些文件实现的是与具体游戏无关的机制，换 ROM 不需要动：

| 文件 | 通用机制 |
|------|----------|
| `extractors.py` | 纯函数解码器：2bpp planar tile、元精灵 OAM 序、调色板、32x32 metatile、H/V 翻转 |
| `render_png.py` | 零依赖 PNG 编码 + 2C02 标准 64 色调色板 + tile 页/元精灵/关卡屏抽样渲染 |
| `validate.py` | 结构校验四件套中机器判定的三件：边界、指针回环、索引范围（第四件"条目数对齐"由登记人手工核对）；返回错误字符串列表，空列表才算通过 |
| `emit_c.py` | manifest + CRC32 基线与确定性生成（固定换行、ASCII、迭代顺序即登记表顺序） |

两处口径需要留神：元精灵字节序 `{y, tile, attr, x}` 是 NES 元精灵表的常见布局而非绝对真理，展开顺序仍以目标 ROM 的 OAM 展开例程为准；attr 的 bit6/bit7 是 OAM 硬件原地镜像（锚点不移动），对象级的翻转补偿（坐标取负并移位一类）属展开/渲染例程，不在提取侧处理。

## 如何换发射目标语言

主产物是语言中立的：`assets/bin/*.bin`（每条登记一份原始字节）+ `assets/manifest.json`（含 CRC32 回归基线）。**`emit_c.py` 只是适配层的一个样板**，换成 Rust / JS / Kotlin 等目标语言时，照它的形状为你的语言写一个新生成器即可——接受同样的路径参数（产物根目录下，绑定代码落在 `generated/` 子目录），为每个数据块输出带 provenance 注释（`name` / `bank` / `cpu` / `asm_ref` / `evidence`）的字面量数组，并按同样字段向 manifest 写入每条目的 CRC32 清单；`emit_c.py` 的 `.c`/`.h` 只用 `stdint.h`，不含任何平台 SDK 头，可作此约定的参照。**bin 与 manifest 一个字节都不变**，CRC 基线不需要重建——校验基线的寿命长于任何一门语言的语法，适配层可以推倒重写，基线要能一直用。

## 快速上手

模板自测基于合成 mini-ROM（`tests/mini_rom.py`），不依赖任何真实 ROM，开箱即绿：

```bash
cd templates/rom_extract
python -m unittest discover -s tests -v    # 48 项
```

把目标 ROM 的表登记进 `REGISTRY` 之后，跑管线：

```bash
python run_extract.py --rom path/to/game.nes --out build_dir
```

校验零错误才会继续（`REGISTRY` 为空时直接报错退出），产物为 `<out>/generated/`（语言绑定适配层）与 `<out>/assets/`（bin + manifest）。抽样渲染属验证步骤、不在这条管线里：用 `render_png.py` 对若干登记条目出 PNG，对着图核对位面组合、元精灵形状与关卡屏内容——结构校验只证明"地址、长度、条目数自洽"，证明不了"解出来的图案就是那个图案"。

## 与主文档的关系

方法论与四条铁律见 `SKILL.md`（§3 证据化提取、§4 格式解码、§5 产物与基线）；签名消歧、数据岛扫描、字节级细节与验证编排等深水技法见 `references/`。
