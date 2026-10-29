# Tooling

All tools live in `tools/` and run from there (`../.venv/bin/python <tool>`). `tools/build.sh`
runs the whole pipeline. The tools currently hard-code MP section bounds and anchor
addresses; SP/ZM needs these parameterised.

| Tool | Purpose |
|---|---|
| `self2elf.py` | fake-signed SELF → ELF64 (verifies segments are plain and contiguous) |
| `elf64to32.py` | ELF64 → ELF32/EM_PPC (headers only); `--symbols data/mp` appends `.symtab` and real section names |
| `symelf.py` | `.symtab`/`.strtab`/`.shstrtab` writer used by `elf64to32.py` |
| `ps3elf.py` | ELF reader: segments, OPD, PRX_PARAM, imports |
| `nids.py` | resolve import NIDs: `sha1(name + suffix)[:4]` little-endian; candidates from RPCS3 `REG_FUNC`/`REG_FNID` sources + `data/nid_names_extra.txt` |
| `ppcsim.py` | one-instruction constant propagation (`lis/addi/ori/mr/rldicl/lfs/fmr/...`) |
| `ppcscan.py` | builds and caches the xref index (absolute refs + `bl` call graph + function starts) |
| `sim.py` | call-site argument recovery (whole-function forward simulation, snapshot per call site) |
| `argscan.py` | rank callees by constant string arguments — the main identification heuristic |
| `extract_dvars.py` / `extract_commands.py` / `extract_builtins.py` | regenerate the big tables |
| `overview.py` | per-function summary of an address range (size, callers, callees, strings) |
| `strxref.py` | substring → strings → referencing functions |
| `disasm.py` | Capstone disassembly with string/name annotations |
| `db.py` | upsert curated functions/globals (`func`, `glob`, `bulk` TSV) |
| `names.py` | curated + auto-derived names |
| `gen_headers.py` | `include/bo1_mp/*.h` |
| `validate_db.py` | consistency checks against the ELF |

## rea / Ghidra

The rea MCP server (Ghidra 12.1.4 provider) only admits **ELF32 EM_PPC**, and selects the
language from `REA_GHIDRA_LANGUAGE_ID`. Configure the server with

```
REA_GHIDRA_LANGUAGE_ID=PowerPC:BE:64:64-32addr
```

and open `build/EBOOT_MP.sym.elf32`. The synthetic symbols make Ghidra create the ~4.5k
functions that are only reachable through `.opd` (it does not parse PS3 OPDs itself) and
carry all database names. Full auto-analysis takes ~5 min (2/3 of it in "Decompiler Switch
Analysis"). rea sessions are ephemeral: names set with `set_addresses_names` vanish on close,
so put names into `data/` and regenerate the ELF instead.

Ghidra's own function list was exported once into `data/mp/ghidra_functions.txt`
(`list_procedures` → `export_evidence_bundle`), and is merged into the scanner's function starts.
