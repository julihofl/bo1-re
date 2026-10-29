# 04 — GSC / CSC script VM (SP/ZM)

Same VM and API as MP ([../mp/04-gsc-vm.md](../mp/04-gsc-vm.md)): getters take
`(argIndex, inst)`, adders `(value, inst)`, server = instance 0, client = instance 1.

## API

| Address | Function |
|---|---|
| `0x5B5088` | `Scr_GetNumParam` |
| `0x5B9840` | `Scr_GetType` |
| `0x5BCB60` / `0x5BBCF8` / `0x5BBCC0` | `Scr_GetInt` / `Scr_GetFloat` / `Scr_GetString` |
| `0x5BB858` | `Scr_GetConstString` |
| `0x5BA908` | `Scr_GetVector` |
| `0x2FA5C8` | `Scr_GetEntity` |
| `0x5C8BF0` / `0x5C8DC0` / `0x5C8840` / `0x5C9548` | `Scr_AddInt` / `AddFloat` / `AddString` / `AddVector` |
| `0x5C98E8` | `Scr_AddEntity` |
| `0x5C9160` / `0x5B5CA8` | `Scr_MakeArray` / `Scr_AddArray` |
| `0x5BD3D0` | `Scr_AddStruct` |
| `0x5B84A8` / `0x5B90A0` | `Scr_Error` / instance-0 variant |
| `0x5B8A28` / `0x5B8C50` | `Scr_ObjectError` / `Scr_ParamError` |

## Builtin tables

[`builtins.csv`](../../data/sp_zm/builtins.csv), 1696 rows (incl. the inspect and terminal tables). 458 GSC names exist only here (AI,
animation, save game, ropes, curves, badplaces…). SP/ZM splits MP's script-entity/vehicle table
in two and adds sentient and CSC tables:

| Table | Address | Entries | Lookup |
|---|---|---|---|
| GSC functions | `0xA593B8` | 437 | `Scr_GetFunction` `0x2BC3E0` |
| GSC player methods | `0xA337EC` | 167 | `Player_GetMethod` `0x25A8E0` |
| GSC hudelem methods | `0xA3400C` | 23 | `HudElem_GetMethod` `0x275190` |
| GSC script-entity methods | `0xA3460C` | 291 | `ScriptEnt_GetMethod` `0x2B3F88` |
| GSC vehicle methods | `0xA354A4` | 108 | `Vehicle_GetMethod` `0x2DB828` |
| GSC actor methods | `0xA32FA8` | 115 | `Actor_GetMethod` `0x236558` |
| GSC sentient methods (threat bias) | `0xA35F08` | 11 | `Sentient_GetMethod` `0x323C08` |
| CSC functions | `0xA56FF8` | 154 | `CScr_GetFunction` `0x10E598` |
| CSC functions (SP extras: profile, achievements, dynents, extracam) | `0xA5F69C` | 54 | `0x54A130` |
| CSC methods | `0xA30BD8` | 114 | `CScr_GetMethod` `0x10E3B0` |
| CSC player methods | `0xA3E8E8` | 36 | `0x54A130` |
| spawn functions | `0xA35B44` | 29 | `G_CallSpawn` `0x2FC048` |
| UI menu-script commands | `0xA3DC48` | 64 | `0x3EC718` |

`spawn_manager` appears twice in the spawn table — the first match wins.
