# RE journal — peculiarities and pitfalls

Chronological notes from reversing the MP EBOOT (TU13). Each entry: what happened, why, and
what to do about it.

## Container / loading

1. **Fake-signed SELF, plain ELF inside.** Key revision `0x8000`, segments neither compressed
   nor encrypted; the whole ELF sits at `0x900`. My first extractor read the segment-info
   offset from the wrong SCE extended-header field (`0x58` instead of `0x48`) and the sub-segments
   (TLS/PROC_PARAM/PRX_PARAM) use `encrypted=0` rather than `2` — both now handled.
2. **Section names and comment are zeroed.** Only PT_LOAD data survived the retail →
   fake-signed rebuild. Sections had to be named from type/flags/content.
3. **rea rejects the SELF and the PPC64 ELF** ("unsupported ELF architecture"); it only admits
   ELF32 EM_PPC, raw-binary does not offer PowerPC and the GameCube DOL lane would pick a 32-bit
   Gekko language (no `ld`/`std`/`rldicl`). Fix: rewrite the headers to ELF32 (segments stay
   byte-identical; PS3 addresses are 32-bit) and set `REA_GHIDRA_LANGUAGE_ID=PowerPC:BE:64:64-32addr`.
   rea also cannot open a Ghidra `.gpr` project.
4. **Ghidra does not follow PS3 `.opd`.** 4558 functions reachable only via descriptors
   (command handlers, builtins, threads) were missing and could not be decompiled. Fix: synthetic
   `.symtab` with one `STT_FUNC` per OPD/`bl` target.

## Code patterns

5. **Strings are not in the TOC.** Code materialises addresses with `lis`+`addi` (sign-extended
   low half: `lis r4,0x8f; addi r4,r4,-0x56d0` → `0x8EA930`). The TOC (`0xB576E8`) is small and
   mostly used for a few globals.
6. **Float args consume GPR slots** (see 02-abi-quirks). Argument recovery that ignored this
   assigned `flags`/`desc` to the wrong registers.
7. **Non-volatile float constants.** Dvar registration functions load float defaults into
   `f21..f31` once at the start; a short backward scan missed them (`cg_fov` showed no default).
   Fix: simulate each function forward once and snapshot at every call site.
8. **`li -1; clrldi 33` = `INT_MAX`.** Integer maxima are built with a rotate/mask, not `lis/ori`;
   the simulator needs real `rldicl` semantics (first version reported `g_speed` max as `-1`).
9. **Stale register tracking produces false xrefs.** The first scanner kept `lis` values after
   the register was overwritten by unrelated instructions (a `lfs` got annotated as `'ire_smoke'`).
   The shared `ppcsim.step()` now clears every destination register it does not model.
10. **Tail calls hide function starts.** Small wrappers end with `b target` instead of `bl`;
    deriving function starts only from `bl` targets merged neighbouring functions (the dvar
    domain-text function looked like part of `0x4C7BF0`). Ghidra's function list is merged in.
11. **Server commands use a stub.** Every server command is also registered in the client command
    list with an empty `blr` handler (`0x3996D8`); the real handler is in the server list.
12. **Script getters take `(argIndex, inst)`, errors take `(inst, ...)`**, and some functions
    exist twice (generic + instance-0 specialised, e.g. `Scr_Error` / `0x5D1F60`).
13. **Error strings start with `0x15`.** Messages passed to `Com_Error` carry a leading `\x15`
    byte; substring searches must not anchor at the start.
14. **No `Com_Printf` hub.** No function with many `(channel, fmt)` calls exists; console prints
    seem compiled out in retail. `0x474578` (83 callers, takes a time stamp and a lock) looks like an
    event/log recorder rather than `Com_Printf` — unresolved.
15. **`'\n'` breaks `isprintable()`**: the first search for `Cbuf_AddText` (commands end in a
    newline) returned nothing because of the printable-string filter.
16. **Tool name clash**: a helper named `dis.py` shadowed Python's `dis` module and broke
    `capstone`'s import chain — renamed to `disasm.py`.

## Open questions

- Meaning of dvar flags `0x100`, `0x1000`, `0x2000`; field at `dvar_t+0x48`.
- `MSG_WriteBits` / `MSG_ReadBits` identification is pattern-based only.
- Exact size of `level_locals_t`, `MAX_GENTITIES` and the `g_clients` element count.
- Section 14 (`0x974100`, writable, 1.7 MB) — SPU images? Not analysed.
