# 03 — Engine core

Addresses: MP TU13. Every entry is in `data/mp/functions.csv` / `globals.csv` with its evidence.

## Dvars

| Address | Function |
|---|---|
| `0x4C9B98` | `Dvar_RegisterNew(name, type, flags, DvarValue value, DvarLimits domain, desc)` |
| `0x4CAAE0` | `Dvar_RegisterBool(name, value, flags, desc)` |
| `0x4CA9C0` | `Dvar_RegisterFloat(name, value, min, max, flags, desc)` |
| `0x4CA960` / `0x4CA900` / `0x4CA898` | `Dvar_RegisterVec2/3/4` |
| `0x4CAA80` | `Dvar_RegisterInt(name, value, min, max, flags, desc)` |
| `0x4CA780` | `Dvar_RegisterEnum(name, valueList, default, flags, desc)` |
| `0x4CA818` | `Dvar_RegisterString(name, value, flags, desc)` |
| `0x4CA5C8` | `Dvar_RegisterColor(name, r, g, b, a, flags, desc)` |
| `0x4CAA20` | `Dvar_RegisterInt64` |
| `0x4CA568` / `0x4CA508` | `Dvar_RegisterLinearColorRGB` / `Dvar_RegisterColorXYZ` |
| `0x4C8570` | `Dvar_SetVariant(dvar, value, source)` |
| `0x4C45D0` | `Dvar_ValueToString(dvar, value)` |
| `0x4C44A0` | `Dvar_IsValidName(name)` |

`dvarType_t`: `0 bool, 1 float, 2 vec2, 3 vec3, 4 vec4, 5 int, 6 enum, 7 string, 8 color,
9 int64, 10 linear color rgb, 11 color xyz` — read directly from the `li r4, <type>` of each wrapper.

### `dvar_t` (0x70 bytes)

```
+0x00 const char *name        +0x18 DvarValue current
+0x04 const char *description +0x28 DvarValue latched
+0x08 uint hash               +0x38 DvarValue reset
+0x0C u16 flags               +0x48 DvarValue (unverified, "saved"?)
+0x10 dvarType_t type         +0x58 DvarLimits domain
+0x14 bool modified           +0x68 dvar_t *hashNext
```

- Pool `s_dvarPool` `0x18F01B0`, max **4096** dvars ("Can't create dvar '%s': %i dvars already exist").
- Hash: `h = 5381; for c: h = h*33 + tolower(c)` (computed as `(h & 0x7FFFFFF)*32 + c + h`),
  bucket `h & 0x3FF` in `s_dvarHashTable` (`0x19601B4`).
- Registration is guarded by a reader/writer spin lock (`0x18F01A4`/`0x18F01A8`) that sleeps
  50 ms (`0x3D2B20(0x32)`) while contended.

### Flags (bits seen across all 2766 registrations)

| Bit | Count | Meaning | Evidence |
|---|---|---|---|
| `0x0001` | 357 | archive | by analogy (cg_drawFPS etc.) |
| `0x0002` | 6 | userinfo | `name`, `password`, `rate` |
| `0x0004` | 14 | serverinfo | `g_gametype`, `mapname`, `com_maxclients` |
| `0x0008` | 2 | systeminfo | `sv_cheats` |
| `0x0010` | 2 | init? | `sv_cheats`, `r_streamFull` |
| `0x0020` | 12 | latch | code: forces `Dvar_SetVariant(latched)` in `Dvar_RegisterNew` |
| `0x0040` | 61 | read-only (ROM) | `cl_ingame`, `cl_paused` |
| `0x0080` | 1108 | cheat | code: reset to default when the cheat dvar at `0x19611B4` is off |
| `0x0100` | 148 | ? | mostly bg_/hud tuning |
| `0x1000` | 312 | ? | |
| `0x2000` | 33 | ? | ai_* |
| `0x4000` | 227 | name copied with `CopyString` | code in `Dvar_RegisterNew` |

`data/mp/dvars.csv` has, for each registration: type, default, min/max, enum strings, flags,
description (mostly empty in retail) and **`dvar_ptr`**: the global where the returned
`dvar_t*` is stored (2657 of 2766 recovered). Some names are registered more than once by
different modules (e.g. `sv_cheats` in SV, game and UI code), each with its own pointer.

## Commands

| Address | Function |
|---|---|
| `0x39B280` | `Cmd_AddCommand(name, function_opd, cmd_function_t *alloc)` |
| `0x3998B8` | `Cmd_AddServerCommand(name, function_opd, cmd_function_t *alloc)` |
| `0x399828` | `Cmd_RemoveCommand(name)` |
| `0x399CC8` | `Cbuf_AddText(localClientNum, text)` |
| `0x3996D8` | `Cbuf_AddServerText_f` — empty stub (`blr`) |

`cmd_function_t` (0x14): `next +0x0`, `name +0x4`, `function +0x10` (an **OPD pointer**).
Server commands are registered twice: in the client list with the empty stub, and in the
server list (`0x14648B0`) with the real handler. `commands.csv` has both rows (`kind`
client/server); `handler` is empty for the stub rows.

## Common

| Address | Function |
|---|---|
| `0x3A2B38` | `Com_Error(code, fmt, ...)` — codes 0/1/3/6 observed (fatal/drop/disconnect/localization) |
| `0x4DB3D8` | `va(fmt, ...)` |
| `0x4BC0C8` / `0x4BC090` | `CopyString` / `FreeString` |
| `0x46390` | `I_stricmp` |
| `0x4DA5B0` | `I_strncpyz(dst, src, size)` |
| `0x4DD0E8` | `I_strncat` |
| `0x46E64` / `0x471A8` | `snprintf` / `vsnprintf` core |
| `0x44824` | `strtol` |
| `0x48CF0` | `longjmp` |

No high-traffic `Com_Printf(channel, fmt)` was found — retail appears to have most console
printing compiled out (see the journal).

## Game (server side)

| Address | Item |
|---|---|
| `0x012AB290` | `g_entities`, `gentity_t` = `0x2F8` bytes, `client` at `+0x144` |
| `0x01213800` | `level`, `level.clients` at `+0x0` |
| `0x013950C8` | `g_clients`, `gclient_t` = `0x2A38` bytes |
| `0x2EEC80` | `G_InitGame` |
| `0x2ECBF0` | `G_RegisterDvars` |
| `0x5B90F8` | `G_Spawn` |
| `0x356BE0` | `G_CallSpawn` (table `spawn_functions`) |
| `0x371DB0` | `G_FreeEntity` |
| `0x316A00` | `G_SetModel` |
| `0x36FFA0` | `G_ModelIndex` |
| `0x370238` | `G_FindConfigstringIndex` |
| `0x3E95F0` | `SV_GameSendServerCommand(clientNum, type, text)` — `-1` = all clients |

`gclient_t`: `ps.viewangles` at `+0x180` (confirmed via `getplayerangles`), current weapon
index (u16) at `+0x144`.

## Rendering / UI

| Address | Function |
|---|---|
| `0x754410` | `R_AddCmdDrawText(text, maxChars, font, x, y, xScale, yScale, rotation, color, style)` |
| `0x1C5FA0` | `CL_RegisterFont(name, imageTrack)` — fonts: `fonts/normalfont`, `fonts/bigfont`, `fonts/smallfont`, `fonts/boldfont`, `fonts/consolefont`, `fonts/extrabigfont`, `fonts/objectivefont`, `fonts/smallDevFont`, `fonts/bigDevFont` |
| `0x7458D8` | `Material_RegisterHandle(name, imageTrack)` (e.g. `"white"`) |
| `0x430770` | `UI_AssetCache` |
| `0x42E2E8` | `UI_DrawText` (guess) |
