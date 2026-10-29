# 04 — GSC / CSC script VM

Black Ops runs **two script VMs**: server GSC (`scriptInstance_t` 0) and client CSC (1).
Most `Scr_*` functions take the instance explicitly; some have instance-0 copies with the
instance folded in (`Scr_Error_Server` at `0x5D1F60` is `Scr_Error` for instance 0).

Argument order differs between families (watch out when hooking):

- getters: `Scr_GetX(unsigned int argIndex, scriptInstance_t inst)` — index **first**
- adders: `Scr_AddX(value, scriptInstance_t inst)`
- errors: `Scr_Error(scriptInstance_t inst, const char *msg, bool terminal)` — instance first

## API

| Address | Function | Evidence |
|---|---|---|
| `0x5CB210` | `Scr_GetNumParam(inst)` | arg-count checks |
| `0x5D2700` | `Scr_GetType(index, inst)` | `isdefined`, `getdvar` |
| `0x5D20F8` | `Scr_GetPointerType` (guess) | `isdefined`, `isplayer` |
| `0x5D0D68` | `Scr_GetString(index, inst)` | `getdvar`, `setmodel` |
| `0x5D0900` | `Scr_GetConstString(index, inst)` | `getent` key/classname |
| `0x5D16C0` | `Scr_GetInt(index, inst)` | `randomint` |
| `0x5D0DA0` | `Scr_GetFloat(index, inst)` | `randomfloat`, `abs` |
| `0x5CF9B0` | `Scr_GetVector(index, out, inst)` | `distance` |
| `0x354F68` | `Scr_GetEntity(index)` | `isplayer` |
| `0x5DF2A0` | `Scr_AddInt(value, inst)` | `getdvarint`, `gettime` |
| `0x5DF630` | `Scr_AddFloat(value, inst)` | `getdvarfloat`, `distance` |
| `0x5DE750` | `Scr_AddString(value, inst)` | `getdvar` |
| `0x5DEB08` | `Scr_AddVector(value, inst)` | `getorigin`, `getplayerangles` |
| `0x5DF800` | `Scr_AddEntity(ent)` | `getent` |
| `0x5DE930` / `0x5CBE30` | `Scr_MakeArray` / `Scr_AddArray` | `getentarray` |
| `0x5D32E0` | `Scr_AddStruct` | `spawnstruct` |
| `0x5CE3C0` | `Scr_Error(inst, msg, terminal)` | decompiled |
| `0x5CE938` | `Scr_ObjectError(msg)` | "not an entity" |
| `0x5D1B10` | `Scr_ParamError(index, msg)` | parameter messages |
| `0x316B80` | `Scr_ConstructMessageString` | `iprintln*` |

Per-instance state (from `Scr_Error`): `scrVarPub[inst]` at `0x01E8B200` with stride `0x58`
(error message pointer at `+0xC`), `scrVmPub[inst]` around `0x01E93EF4` with stride `0x4320`,
the error message buffer `0x01EA05C0` (1024 bytes), and a `jmp_buf` stack for the VM's
`longjmp`-based error unwinding.

## Builtin tables

All in `data/mp/builtins.csv` (1519 rows). Entry layout for script builtins:
`{ const char *name; opd_t *handler; int developer; }` (12 bytes). Name→handler lookup
functions scan these with `I_stricmp`.

| Table | Address | Entries | Lookup |
|---|---|---|---|
| GSC functions | `0xB5C8AC` | 383 | `Scr_GetFunction` `0x310FD8` |
| GSC player methods | `0xB32C2C` | 166 | `Player_GetMethod` `0x2C3228` |
| GSC hudelem methods | `0xB33440` | 26 | `HudElem_GetMethod` `0x2DEE70` |
| GSC script-entity/vehicle methods | `0xB33918` | 374 | `ScriptEnt_GetMethod` `0x307668` |
| GSC actor methods | `0xB40390` | 79 | `Actor_GetMethod` `0x60EB80` |
| CSC functions | `0xB5A2F4` | 184 | `CScr_GetFunction` `0x144AC0` |
| CSC methods | `0xB311D8` | 112 | `CScr_GetMethod` `0x1448B0` |
| CSC entity methods | `0xB31728` | 29 | `0x15C690` |
| spawn functions `{classname, fn}` | `0xB34BE0` | 22 | `G_CallSpawn` |
| UI menu-script commands `{name, fn}` | `0xB3EE84` | 53 | `0x44B130` |
| remote inspect commands `{name, fn, fn2}` | `0xB41D50` | 8 | `0x650DC0` — see [05-network.md](05-network.md) |

Handlers get automatic names in the symbol ELF: `GScr_<name>`, `PlayerCmd_<name>`,
`HECmd_<name>`, `ScrCmd_<name>`, `ActorCmd_<name>`, `CScr_<name>`, `CScrCmd_<name>`.

Replacing a builtin = overwriting the `handler` word of its table entry with your own OPD
(the tables are in writable memory).

`notify`/`waittill`/`endon` are VM opcodes, not builtins — they are not in the tables.
