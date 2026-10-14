# NES ROM 逆向与忠实重建技能

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blue.svg)](https://claude.ai/code)

> 从 6502 反汇编忠实重建红白机游戏的方法论 skill：翻译逻辑、提取资源、证明保真。重建目标平台与语言不限——UEFI 应用、Windows/Linux 桌面程序、Android 应用、Web 页面是同等合法的目标。

[English](README_EN.md) | 简体中文

## 简介

本技能为 Claude Code 提供一套 **NES/Famicom ROM 逆向与忠实重建**的方法论：给定一个 ROM 和它的 6502 反汇编，产出结构清晰、可验证、能长期维护的重建工程。核心做法是**翻译逻辑 + 提取资源**两条腿走路——**不写模拟器**，不复刻 CPU/PPU/APU 的硬件行为，而是把游戏逻辑逐行翻译成目标语言、把素材逐表提取成语言中立的产物，让游戏在目标平台上原样重跑。方法论本身与平台无关：重建目标是 UEFI 应用、桌面程序、安卓应用还是网页，用 C、Rust、JS 还是 Kotlin，走的都是同一套流程；平台专属的实现细节（目标平台的图形 API、构建系统、调试工具链）不属于本 skill 的范围，必要时只给一行指针。

## 特性

- **四铁律方法论** — 证据优先、翻译不重写、校验报错时修登记而非放宽校验、保真优先级排序；违反任何一条的结果都是"看起来完成了、实际不可信"，四条铁律在全文反复落地为可执行动作
- **证据化提取与校验** — 每块被提取的数据都要带 `{汇编标签, bank/地址, 来源行号, 证据}` 四元证据；校验四件套（边界、指针回环、索引范围、条目数对齐）构成零假阴性闸门，报错只回查登记，绝不删掉检查
- **6502 翻译纪律与 quirk 清单** — 命名贴汇编标签、保持帧驱动模型、状态机编号与迁移条件照抄、定点行为逐位还原；计数 0 按 256、进位链隔断、隐式寄存器依赖等语义陷阱逐条成表，每条带现象、语义、翻译要点与实例证据
- **保真验证阶梯** — L1 结构校验 → L2 golden CRC 双侧互证 → L3 锚定测试 → L4 端到端闭环，逐级抬高证据强度；"跑通 ≠ 验证"，结论必须引用具体文件与行号/帧，证据不足按失败处理
- **多模态抽样核对** — 提取产物抽样渲染成 PNG，让 agent 用自己的"眼睛"核对内容；运行侧同样以截图与日志形成闭环，而不是回头问用户"看着对不对"
- **模板开箱即跑** — `templates/rom_extract/` 是完整的提取管线骨架：iNES 解析、表登记与签名定位、结构校验、格式解码、代码生成、零依赖 PNG 渲染；48 个基于合成 mini-ROM 的测试开箱即绿，不依赖任何真实 ROM
- **首次完整实战背书** — 《赤色要塞》复刻：约两天半把一款红白机游戏从反汇编翻译到目标平台并跑通主流程，留下 491 条带证据登记、约 160 项宿主锚定测试、48 项提取器回归与 7 个端到端断言模式

## 安装

### 复制整个目录

本 skill 不是单个 `SKILL.md`：`references/`（深水参考）与 `templates/`（可运行模板）都是运行时要真正读到的内容，必须随目录整体复制到 `~/.claude/skills/` 下——只拷 `SKILL.md` 会得到一份引用了不存在文件的文档。

```bat
:: Windows (cmd)
xcopy /E /I nes-reverse-engineering %USERPROFILE%\.claude\skills\nes-reverse-engineering
```

```bash
# Linux / macOS
cp -r nes-reverse-engineering ~/.claude/skills/
```

复制完成后，`~/.claude/skills/nes-reverse-engineering/` 下应能看到 `SKILL.md`、`README.md`、`references/`、`templates/` 与 `evals/`。

### 环境要求

模板为纯 Python 标准库、零第三方依赖，但需要 **Python 3.10 及以上**（用到了 `Path.write_text(newline=...)`）。`SKILL.md` 与 `references/` 是纯文档，不依赖任何运行时。

## 快速开始

安装后，在 Claude Code 中直接提问即可触发技能：

```
我有一个红白机游戏的 ROM，想把它逆向出来做成 Windows 程序，该从哪里开始？
怎么从 ROM 里找到游戏用的是哪张图形数据表？
NES 的 2bpp tile 数据怎么解码成像素？元精灵表里四个字节分别是什么？
把这页 6502 反汇编逐行翻译成 C，需要注意什么？
How do I faithfully recreate a NES game from its disassembly without writing a cycle-accurate emulator?
```

## 内容目录

### 主文档（`SKILL.md`）

| 章节 | 内容 |
|------|------|
| §0 适用场景与四条铁律 | 重建目标定位、四条铁律、保真优先级、法律提醒 |
| §1 ROM 结构分析 | iNES 头逐字段、mapper 与 bank 窗口、CHR ROM = 0 型 ROM 的特征 |
| §2 反汇编对照工作流 | 反汇编来源选择与勘误处理、把反汇编当"地图"用（标签、`.PAD`、表定义） |
| §3 证据化资源提取 | 声明式表登记、定位程序（明示地址 → 唯一签名 → 读表代码交叉引用）、校验四件套、登记五步 |
| §4 资源格式解码 | 2bpp planar tile、图案装载链（load 表 → segment → RLE）、调色板更新段、元精灵 OAM 序、32x32 metatile 与 layout 分解 |
| §5 产物与基线 | 语言中立三件套（bin + manifest + 抽样渲染 PNG）、可替换的代码生成器、确定性生成、provenance 一路跟到产物 |
| §6 逻辑翻译纪律 | RAM 布局镜像、帧驱动模型、状态机与间接跳转、定点行为逐位还原、quirk 摘要、死代码策略 |
| §7 保真验证阶梯 | L1 结构校验 → L2 golden 基线 → L3 锚定测试 → L4 端到端闭环，以及证据纪律 |
| §8 陷阱速查表 | 高频陷阱的"症状 → 对策"对照表 |
| 快速参考 | 逆向复刻全流程 checklist（阶段 → 产出 → 验证方式） |

### 深水参考（`references/`）

| 文件 | 内容 |
|------|------|
| `references/extraction-playbook.md` | 数据定位深水技法：签名多命中消歧、数据岛扫描、各格式字节级细节与实测结论 |
| `references/6502-quirks.md` | 6502 语义陷阱全表：现象 → 语义 → 翻译要点 → 实例与证据 |
| `references/verification.md` | 验证阶梯实操：golden oracle 写法、锚定测试纪律、端到端编排、多模态核对 checklist |
| `references/case-jackal.md` | 完整案例复盘：规模与时间线、关键技法实例、代表性翻车与修复、成本账 |

### 模板与评估（`templates/`、`evals/`）

| 路径 | 内容 |
|------|------|
| `templates/rom_extract/ines.py` | iNES 头解析与 bank 切分，期望值参数化 |
| `templates/rom_extract/tables.py` | 表登记结构、bank 窗口地址映射、唯一签名定位、空 `REGISTRY` 与示例条目 |
| `templates/rom_extract/validate.py` | 结构校验：边界、指针回环、索引范围 |
| `templates/rom_extract/extractors.py` | 纯函数解码器：2bpp tile、元精灵 OAM 序、调色板、32x32 metatile、H/V 翻转 |
| `templates/rom_extract/pattern_loader.py` | 图案装载链参考实现：RLE 解码、load 表与 segment 解析、场景组装 |
| `templates/rom_extract/emit_c.py` | 语言绑定代码生成器示例（C，可替换）：C 数组 + bin + manifest（CRC32），逐块带 provenance 注释 |
| `templates/rom_extract/render_png.py` | 零依赖 PNG 编码器 + 64 色调色板 + CHR 页/元精灵/关卡屏渲染，供多模态核对 |
| `templates/rom_extract/run_extract.py` | 管线驱动骨架：解析 → 校验（零错误才继续）→ 产物三件套 |
| `templates/rom_extract/tests/` | 合成 mini-ROM 全管线测试（48 个），`python -m unittest discover -s tests` 即绿 |
| [`templates/rom_extract/README.md`](templates/rom_extract/README.md) | 适配指南：拿到模板后哪些必须按目标 ROM 改（iNES 期望与 bank 窗口、装载格式、REGISTRY 登记）、哪些是通用机制、如何换发射目标语言 |
| `evals/evals.json` | 触发评估：10 条中英文提问，检查技能是否在正确的场景命中 |

## 触发条件

当用户提问涉及以下内容时自动触发：

- 逆向 / 复刻红白机（NES / Famicom）游戏，或"把 ROM 做成一个能跑的程序"
- 解析 iNES 结构：PRG/CHR bank、mapper、bank 窗口与地址换算
- 从 ROM 里定位数据表：图形表、调色板、元精灵、关卡 layout、指针表
- NES ROM 资源提取与证据登记（provenance、CRC 基线、抽样渲染核对）
- 2bpp tile 解码、元精灵 OAM 字节序、32x32 metatile 分解
- 把 6502 反汇编逐行翻译成目标语言（C / Rust / JS / Kotlin…）
- 验证复刻与原版是否一致：CRC 互证、锚定测试、截图与日志闭环
- 反汇编注释与 ROM 字节不一致时的取舍与回查
- 英文提问场景：`recreate a NES game from its disassembly`、`NES ROM reverse engineering`、`extract graphics from a Famicom ROM`
- 边界场景：纯目标平台的开发问题（构建系统、平台图形 API、平台调试工具链）不属于本 skill，会落到对应平台 skill

## 首次完整实战

《赤色要塞》（Jackal）的 UEFI Shell 复刻是这套方法论的首次完整实战：Kimi K3 在 Claude Code 中按本 skill 的流程，用约两天半把一款红白机游戏从 6502 反汇编翻译到目标平台，主流程在真实环境里走通——标题、剧情滚动、机降、关卡流转、Game Over / Continue、结局机 9→5 回环，全程没有人工逐行介入代码。已知与原版的差异（Level 4/5 敌群、双人模式、声音）没有藏起来，逐条在代码注释里留痕。项目开源在 [MikeWuPing/UEFI_Jackal](https://github.com/MikeWuPing/UEFI_Jackal)。

这一战同时也是"Token 花在证明自己没做错上"的成本样本：491 条可复核登记、约 160 项宿主锚定测试、48 项提取器回归、7 个端到端断言模式，以及一整套在交付后仍持续产出证据的验证设施。多数被抓住的缺陷（双重偏移、分派表错位、借位链全反）都发生在"单测全绿"的假象之后，靠的就是把验证一路推到真实环境。完整复盘（规模、时间线、关键技法、翻车与修复、成本账）见 `references/case-jackal.md`。

## 相关资源

- [NESdev Wiki](https://www.nesdev.org/wiki/) — NES/Famicom 硬件与格式的权威参考：iNES 头、2bpp tile、OAM、PPU 调色板，本 skill 的字节级细节都以它为准
- 目标平台为 UEFI 应用时：平台层（GOP 图形呈现、键盘输入、QEMU 联调闭环）的实现细节见 `emulator-uefi-shell-app` skill；其余目标平台无附加依赖

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 [MIT](LICENSE) 许可证。

本 skill 只包含方法论、模板代码与案例叙述，不包含任何游戏 ROM 或其提取产物；原 ROM 与提取产物不随代码分发，重建作品不得对外发布原作受版权保护的素材。

---

**注意**：本 skill 需要配合 [Claude Code](https://claude.ai/code) 使用。
