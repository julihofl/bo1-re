# bo1-re — Call of Duty: Black Ops (PS3) reverse-engineering database

Addresses, structures, dvars, commands, GSC builtins and notes for building mods for
**Black Ops 1 on PS3, title update 13 (v1.13)**. Multiplayer EBOOT first; SP/ZM follows
with the same pipeline.

| Target | File | SHA-1 | Internal name |
|---|---|---|---|
| MP | `EBOOT_MP.BIN` | `77a74cf2a14ac4029538536458fa8ce18d079fe9` | `t5mp_ps3f.self`, build tag `online_tu13_mp_` |
| SP/ZM | `EBOOT_SP_ZM.BIN` | `94293f3f15bae74978d5801db341d89cf1e88f38` | not analysed yet |

The MP EBOOT is shared by all regions (BLES01031–01035, BLES01105, BLUS30591, NPUB20584).
The binaries themselves are **not** in this repo (see `.gitignore`); put them in the repo root.

## Layout

```
data/mp/            single source of truth (CSV/JSON), see below
include/bo1_mp/     generated C headers for SPRX/PPU mods (do not edit)
docs/               write-ups per subsystem + RE journal
tools/              extraction / analysis pipeline (Python)
build/, analysis/   local outputs (ignored)
```

### Database (`data/mp/`)

| File | Rows | Content |
|---|---|---|
| `functions.csv` | curated | address, game OPD (if any), name, C prototype, subsystem, confidence, evidence |
| `globals.csv` | curated | address, name, type, size, confidence, evidence |
| `structs.json` | curated | struct layouts with per-field confidence |
| `dvars.csv` | 2766 | every static dvar registration: type, default, min/max, enum values, flags, `dvar_t*` global, register site |
| `commands.csv` | 628 | console commands (client + server lists) with handler and `cmd_function_t` |
| `builtins.csv` | 1511 | GSC/CSC functions & methods, spawn functions, UI menu-script commands, net message handlers |
| `imports.csv` | 319 | every PRX import (library, NID, resolved name, stub) — 100% resolved |
| `ghidra_functions.txt` | 11149 | Ghidra's own function starts (merged into the scanner) |

**Confidence** — `confirmed`: proven by string/xref/decompiled behaviour; `likely`: strong
pattern evidence; `guess`: plausible, verify before relying on it.

Functions not in `functions.csv` but in `commands.csv`/`builtins.csv` get automatic names
(`GScr_<name>`, `PlayerCmd_<name>`, `Cmd_<name>_f`, `SV_Cmd_<name>_f`, …) in the symbol export.

## Quick start

```sh
uv venv .venv && uv pip install --python .venv/bin/python -r tools/requirements.txt
tools/build.sh        # SELF -> ELF, extract tables, generate headers, validate, symbol ELF
```

`build/EBOOT_MP.sym.elf32` is an ELF32 with a synthetic `.symtab` carrying every name in
the database. Load it in Ghidra with language **`PowerPC:BE:64:64-32addr`** (or through the
rea MCP server, see [docs/tooling.md](docs/tooling.md)).

## Using the headers

```c
#include "bo1_mp.h"

void hello(void)
{
    BO1_FN(Cbuf_AddText)(0, "say hello\n");          /* call through a synthetic OPD */
    dvar_t *fov = *(dvar_t **)BO1_DVAR_cg_fov;        /* dvar_t* globals from dvars.csv */
    fov->current.value = 90.0f;
}
```

Read [docs/06-modding-howto.md](docs/06-modding-howto.md) before calling or hooking anything.

## Docs

- [00 SELF/ELF format](docs/00-self-format.md)
- [01 Memory map](docs/01-memory-map.md)
- [02 PPU ABI quirks](docs/02-abi-quirks.md)
- [03 Engine core](docs/03-engine-core.md) — dvars, commands, game, render
- [04 GSC/CSC VM](docs/04-gsc-vm.md)
- [05 Network](docs/05-network.md)
- [06 Modding how-to](docs/06-modding-howto.md)
- [Tooling](docs/tooling.md)
- [RE journal](docs/re-journal.md) — pitfalls and peculiarities hit during the work
