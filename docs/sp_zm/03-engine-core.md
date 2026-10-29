# 03 — Engine core (SP/ZM)

The engine is the same code base as MP; behaviour, prototypes and struct layouts described in
[../mp/03-engine-core.md](../mp/03-engine-core.md) apply unless listed here. Every entry is in
[`data/sp_zm/functions.csv`](../../data/sp_zm/functions.csv), most of them matched from MP
(`notes` names the MP address and the match method).

## Dvars

2582 registrations ([`dvars.csv`](../../data/sp_zm/dvars.csv)); 2265 names are shared with MP,
283 exist only here (mostly `ai_*`, save game, campaign UI).

| Address | Function |
|---|---|
| `0x4575D8` | `Dvar_RegisterNew` |
| `0x458578` | `Dvar_RegisterBool` |
| `0x4584B0` | `Dvar_RegisterFloat` |
| `0x458450` / `0x4583F0` / `0x458388` | `Dvar_RegisterVec2/3/4` |
| `0x458518` | `Dvar_RegisterInt` |
| `0x458270` | `Dvar_RegisterEnum` |
| `0x458308` | `Dvar_RegisterString` |
| `0x4580B8` | `Dvar_RegisterColor` |
| `0x458058` / `0x457FF8` | `Dvar_RegisterLinearColorRGB` / `Dvar_RegisterColorXYZ` |
| `0x455FB8` | `Dvar_SetVariant` |

There is **no `Dvar_RegisterInt64`**: the register wrappers are laid out exactly like MP's but
the int64 one between float and int is missing (no 64-bit dvars outside MP stats/online).

## Commands

410 registrations ([`commands.csv`](../../data/sp_zm/commands.csv)), 32 not present in MP.

| Address | Function |
|---|---|
| `0x397160` | `Cmd_AddCommand(name, function, cmd_function_t *alloc)` |
| `0x3957A0` | `Cmd_AddServerCommand` |
| `0x3955C0` | empty client-side stub registered for every server command |
| `0x395710` | `Cmd_RemoveCommand` |
| `0x395BA8` | `Cbuf_AddText(localClient, text)` |

## Common / game

| Address | Name |
|---|---|
| `0x39E6A8` | `Com_Error` |
| `0x468398` | `va` |
| `0x3B2C30` | `Sys_GetValue(index)` — thread-local slots; index 4 = tokenized command args |
| `0x282140` | `G_RegisterDvars` |
| `0x5A2B28` | `G_Spawn` |
| `0x2FC048` | `G_CallSpawn` (spawn table `0xA35B44`) |
| `0x306E70` | `G_FreeEntity` (guess) |
| `0x305650` | `G_ModelIndex` |
| `0x26CFF8` | `ClientCommand` — unlike MP it also handles `god`/`noclip`/`ufo`/`notarget`/`demigod` inline |
| `0x3C33A8` | `SV_GameSendServerCommand` |

### Entities

```c
gentity_t *ent = (gentity_t *)(0x00FA805C + n * 0x34C);
gclient_t *cl  = *(gclient_t **)((char *)ent + 0x13C);   /* MP: +0x144 */
float *angles  = (float *)((char *)cl + 0x180);          /* same as MP */
unsigned char weapon = *((unsigned char *)cl + 0x144);   /* MP: unsigned short */
```

## Rendering / UI

| Address | Name |
|---|---|
| `0x694420` | `R_AddCmdDrawText` |
| `0x685C28` | `Material_RegisterHandle` |
| `0x53F3B0` | `CG_RegisterGraphics` |
| `0x3D87E8` | `UI_DrawText` |
| `0x3DAC10` | `UI_AssetCache` |
