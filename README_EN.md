# NES ROM Reverse Engineering & Faithful Recreation Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blue.svg)](https://claude.ai/code)

> A methodology skill for faithfully recreating NES/Famicom games from their 6502 disassembly: translate the logic, extract the assets, prove the fidelity. The target platform and language are open — a UEFI application, a Windows/Linux desktop program, an Android app, or a web page are all equally legitimate targets.

English | [简体中文](README.md)

## Overview

This skill gives Claude Code a complete methodology for **NES/Famicom ROM reverse engineering and faithful recreation**: given a ROM and its 6502 disassembly, produce a reconstruction project that is well-structured, verifiable, and maintainable over the long run. The core approach walks on two legs — **translate the logic + extract the assets** — and **does not write an emulator**. Instead of reproducing CPU/PPU/APU hardware behavior, it translates game logic line by line into the target language and extracts assets table by table into language-neutral artifacts, so the game runs as-is on the target platform. The methodology itself is platform-agnostic: whether the target is a UEFI application, a desktop program, an Android app, or a web page, in C, Rust, JS, or Kotlin, the workflow is the same. Platform-specific implementation details (the target's graphics API, build system, debugging toolchain) are out of scope and get at most a one-line pointer.

## Features

- **Four iron laws** — evidence first; translate, never rewrite; when validation fails, fix the registry instead of loosening the check; and a strict fidelity priority order. Violating any one of them yields "looks finished, actually untrustworthy" — the laws recur throughout the document as concrete actions
- **Evidence-backed extraction and validation** — every extracted block of data carries four-part evidence `{asm label, bank/address, source line, evidence}`; the validation quartet (boundary, pointer round-trip, index range, entry-count alignment) forms a zero-false-negative gate — on error you re-check the registry, never delete the check
- **6502 translation discipline and quirk list** — naming tracks the assembly labels, the frame-driven model is preserved, state numbers and transition conditions are copied verbatim, fixed-point behavior is restored bit by bit; semantic traps such as "count 0 means 256", a broken carry chain, and implicit register dependencies are tabulated with symptom, semantics, translation notes, and evidence
- **Fidelity verification ladder** — L1 structural validation → L2 golden CRC cross-checked on both sides → L3 anchored tests → L4 end-to-end closed loop, with evidence strength rising at each rung; "it runs" is not "it is verified" — conclusions must cite specific files and line numbers/frames, and insufficient evidence counts as failure
- **Multimodal spot-checking** — extracted artifacts are sampled and rendered to PNG so the agent can check them with its own "eyes"; on the runtime side the same screenshot-and-log loop applies instead of asking the user "does this look right?"
- **Templates that run out of the box** — `templates/rom_extract/` is a complete extraction pipeline skeleton: iNES parsing, table registry and signature location, structural validation, format decoders, code generation, and dependency-free PNG rendering; 48 tests built on a synthetic mini-ROM are green out of the box and need no real ROM
- **Backed by a complete first real-world run** — the *Jackal* recreation: in about two and a half days, a Famicom game was translated from its disassembly to the target platform with its main flow running end to end, leaving 491 evidence-backed registry entries, ~160 host-anchored tests, 48 extractor regression tests, and 7 end-to-end assertion modes

## Installation

### Copy the whole directory

This skill is not a single `SKILL.md`: both `references/` (deep-dive material) and `templates/` (runnable templates) are real content that gets read at runtime, so the whole directory must be copied into `~/.claude/skills/` — copying only `SKILL.md` leaves you with a document that references files that do not exist.

```bat
:: Windows (cmd)
xcopy /E /I nes-reverse-engineering %USERPROFILE%\.claude\skills\nes-reverse-engineering
```

```bash
# Linux / macOS
cp -r nes-reverse-engineering ~/.claude/skills/
```

After copying, `~/.claude/skills/nes-reverse-engineering/` should contain `SKILL.md`, `README.md`, `references/`, `templates/`, and `evals/`.

### Requirements

The templates use only the Python standard library — no third-party dependencies — but they require **Python 3.10 or newer** (they use `Path.write_text(newline=...)`). `SKILL.md` and `references/` are pure documentation and need no runtime.

## Quick Start

After installation, simply ask Claude Code to trigger the skill:

```
I have a Famicom game ROM and want to reverse-engineer it into a Windows program. Where do I start?
How do I find which graphics data table a ROM uses?
How are NES 2bpp tiles decoded into pixels? What are the four bytes in a metasprite entry?
Walk me through translating this page of 6502 disassembly into C line by line — what should I watch out for?
How do I faithfully recreate a NES game from its disassembly without writing a cycle-accurate emulator?
```

## Contents

### Main document (`SKILL.md`)

| Section | Content |
|---------|---------|
| §0 Scope and the four iron laws | Target positioning, the four iron laws, fidelity priority, legal notes |
| §1 ROM structure analysis | iNES header field by field, mapper and bank windows, the hallmarks of a CHR-ROM = 0 ROM |
| §2 Working against the disassembly | Choosing a disassembly, handling its errata, using it as a "map" (labels, `.PAD`, table definitions) |
| §3 Evidence-backed asset extraction | Declarative table registry, location procedure (explicit address → unique signature → cross-reference the reading code), the validation quartet, the five-step registration routine |
| §4 Asset format decoding | 2bpp planar tiles, the pattern loading chain (load table → segment → RLE), palette update segments, metasprite OAM order, 32x32 metatiles and layout decomposition |
| §5 Artifacts and baseline | The language-neutral trio (bin + manifest + sampled render PNG), a replaceable code generator, deterministic generation, provenance carried all the way into the artifacts |
| §6 Logic translation discipline | RAM layout mirroring, the frame-driven model, state machines and indirect jumps, bit-exact fixed-point behavior, a quirk summary, dead-code policy |
| §7 The fidelity verification ladder | L1 structural validation → L2 golden baseline → L3 anchored tests → L4 end-to-end closed loop, plus evidence discipline |
| §8 Trap quick-reference | A "symptom → countermeasure" table of high-frequency traps |
| Quick reference | The full reverse-engineering checklist as stage → artifact → verification |

### Deep-dive references (`references/`)

| File | Content |
|------|---------|
| `references/extraction-playbook.md` | Deep-dive location techniques: disambiguating multiple signature hits, data-island scanning, byte-level details and measured findings per format |
| `references/6502-quirks.md` | The full 6502 semantic trap table: symptom → semantics → translation notes → instances with evidence |
| `references/verification.md` | Verification ladder in practice: writing a golden oracle, anchored-test discipline, end-to-end orchestration, a multimodal check-off list |
| `references/case-jackal.md` | Complete case retrospective: scale and timeline, key techniques in action, representative failures and fixes, the cost ledger |

### Templates and evals (`templates/`, `evals/`)

| Path | Content |
|------|---------|
| `templates/rom_extract/ines.py` | iNES header parsing and bank splitting, with expectations parameterized |
| `templates/rom_extract/tables.py` | Table registry structures, bank-window address mapping, unique signature location, an empty `REGISTRY` with one example entry |
| `templates/rom_extract/validate.py` | Structural validation: boundaries, pointer round-trips, index ranges |
| `templates/rom_extract/extractors.py` | Pure-function decoders: 2bpp tiles, metasprite OAM order, palettes, 32x32 metatiles, H/V flips |
| `templates/rom_extract/pattern_loader.py` | Reference implementation of a pattern loading chain: RLE decoding, load-table and segment parsing, scene assembly |
| `templates/rom_extract/emit_c.py` | Example language-binding code generator (C, replaceable): C arrays + bins + manifest (CRC32), with provenance comments per block |
| `templates/rom_extract/render_png.py` | Dependency-free PNG encoder + 64-color palette + CHR page / metasprite / level-screen rendering for multimodal checking |
| `templates/rom_extract/run_extract.py` | The pipeline driver skeleton: parse → validate (zero errors before continuing) → the artifact trio |
| `templates/rom_extract/tests/` | Full-pipeline tests on a synthetic mini-ROM (48 of them); `python -m unittest discover -s tests` is green as-is |
| [`templates/rom_extract/README.md`](templates/rom_extract/README.md) | Adaptation guide: what you must change for your target ROM (iNES expectations and bank windows, loader format, REGISTRY registration), what is generic machinery, and how to switch the emit target language |
| `evals/evals.json` | Trigger evals: 10 Chinese/English prompts checking that the skill fires in the right situations |

## Trigger Conditions

The skill is automatically triggered when users ask about:

- Reverse-engineering / recreating a Famicom (NES) game, or "turning this ROM into something that runs"
- Parsing the iNES structure: PRG/CHR banks, mapper, bank windows and address conversion
- Locating data tables inside a ROM: graphics tables, palettes, metasprites, level layouts, pointer tables
- NES ROM asset extraction with evidence registration (provenance, CRC baselines, sampled-render checks)
- 2bpp tile decoding, metasprite OAM byte order, 32x32 metatile decomposition
- Translating 6502 disassembly line by line into a target language (C / Rust / JS / Kotlin…)
- Verifying a recreation against the original: CRC cross-checks, anchored tests, screenshot and log loops
- Deciding what to do when disassembly comments disagree with the ROM bytes, and how to re-check
- English phrasings: `recreate a NES game from its disassembly`, `NES ROM reverse engineering`, `extract graphics from a Famicom ROM`
- Boundary case: questions purely about target-platform development (build systems, platform graphics APIs, platform debug toolchains) are out of scope and route to the matching platform skill

## First Complete Real-World Run

The UEFI Shell recreation of *Jackal* was the first complete run of this methodology: working through this skill's process inside Claude Code, Kimi K3 translated a Famicom game from its 6502 disassembly to the target platform in about two and a half days, with the main flow running in the real environment — title screen, story scroll, helicopter insertion, level transitions, Game Over / Continue, and the ending machine's 9→5 loop — and no human hand-editing the code line by line. The known differences from the original (the Level 4/5 enemy waves, two-player mode, sound) are not hidden; each is documented in the code comments. The project is open-sourced at [MikeWuPing/UEFI_Jackal](https://github.com/MikeWuPing/UEFI_Jackal).

It is also a cost sample of "tokens spent proving you did not get it wrong": 491 re-checkable registry entries, ~160 host-anchored tests, 48 extractor regression tests, 7 end-to-end assertion modes, and a whole verification apparatus that kept producing evidence after delivery. Most of the defects caught (double offsets, misaligned dispatch tables, fully inverted borrow chains) surfaced *after* the unit tests were all green — precisely because verification kept being pushed into the real environment. The full retrospective (scale, timeline, key techniques, failures and fixes, the cost ledger) is in `references/case-jackal.md`.

## Resources

- [NESdev Wiki](https://www.nesdev.org/wiki/) — the authoritative reference for NES/Famicom hardware and formats: the iNES header, 2bpp tiles, OAM, the PPU palette; this skill's byte-level details follow it
- When the target platform is a UEFI application: platform-layer details (GOP graphics presentation, keyboard input, the QEMU closed loop) are covered by the `emulator-uefi-shell-app` skill; other target platforms need no extra dependencies

## Contributing

Issues and Pull Requests are welcome!

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

## License

This project is licensed under the [MIT](LICENSE) License.

This skill contains only methodology, template code, and case narratives — no game ROM or extracted artifacts of one. The original ROM and its extracted artifacts are not distributed with the code, and a recreation must not publish assets that are copyrighted by the original work's rights holder.

---

**Note**: This skill requires [Claude Code](https://claude.ai/code) to function.
