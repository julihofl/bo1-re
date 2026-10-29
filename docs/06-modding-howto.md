# 06 — Modding how-to

Everything here targets the MP EBOOT TU13. Addresses differ in other versions and in the SP/ZM EBOOT.

## Calling a game function

PPU function pointers are pointers to OPDs. The generated header builds one per function:

```c
#include "bo1_mp.h"

BO1_FN(Cbuf_AddText)(0, "fast_restart\n");
/* expands to ((Cbuf_AddText_t)&bo1_opd_Cbuf_AddText)(...), with
   bo1_opd_Cbuf_AddText = { 0x00399CC8, BO1_TOC } */
```

If the game itself has a descriptor (`BO1_GAME_OPD_<name>`), you may cast that address instead.
Float arguments: let the compiler handle them through the typedef — never pass floats as ints.

## Reading/writing dvars

```c
dvar_t *d = *(dvar_t **)BO1_DVAR_jump_height;   /* pointer stored by the register call */
d->current.value = 999.0f;                       /* bypasses domain checks and flags */
```

Writing `current` directly skips `Dvar_SetVariant` (no modified flag, no latch, no
cheat protection) — fine for local tweaks, wrong for dvars that must be networked.
`DVAR_CHEAT (0x80)` dvars are reset to their reset value while cheats are off
(`Dvar_RegisterNew`), so either clear the flag (`d->flags &= ~0x80`) or write after init.

## Entities and players

```c
gentity_t *ent = (gentity_t *)(BO1_g_entities + clientNum * 0x2F8);
gclient_t *cl  = *(gclient_t **)((char *)ent + 0x144);
float *angles  = (float *)((char *)cl + 0x180);     /* ps.viewangles */
```

`structs.h` contains padded structs with `_Static_assert`s for the confirmed offsets.

## Server commands to clients

`SV_GameSendServerCommand(-1, 0, "...")` reaches all clients. The game itself sends
`va("%c \"%s\"", 'g' /* bold */ or 'f', text)` for `iprintlnbold`/`iprintln`.

## Hooking

1. **Table hooks (preferred)**: GSC builtins, spawn functions, console commands and party
   message handlers are called through OPD pointers stored in writable memory
   (`builtins.csv`: `entry`, `commands.csv`: `cmd_function`). Replace the pointer with your
   own OPD; keep the original to chain.
2. **Inline hooks**: patch the first instruction with a branch to a trampoline. Remember that
   code may be reached both by `bl` (direct) and via OPD (indirect); the TOC of your trampoline
   must be the game TOC `0x00B576E8` when you jump back.
3. Prefer `cmd_function_t` re-use: `Cmd_AddCommand` keeps your static struct — allocate it in
   your SPRX's data, not on the stack.

## Checklist before trusting an address

- Check `confidence` in the CSV (`guess` = verify yourself).
- Check the version string (`online_tu13_mp_`) of the EBOOT you are patching.
- Run `tools/validate_db.py` after edits.
