#!/usr/bin/env python3
"""Extract every statically registered dvar (name, type, defaults, limits, flags, dvar_t* global)."""
import csv
import sys

import ppcscan
from sim import Sim, s32

# addr -> (type name, gpr arg layout, fpr value count, fpr limit count)
# GPR slots after floats are shifted because PPC64 floats also consume a GPR slot.
REGISTER_FUNCS = {
    0x4CAAE0: ("bool",   {"value": 4, "flags": 5, "desc": 6}, 0, 0),
    0x4CA9C0: ("float",  {"flags": 7, "desc": 8}, 1, 2),
    0x4CA960: ("vec2",   {"flags": 8, "desc": 9}, 2, 2),
    0x4CA900: ("vec3",   {"flags": 9, "desc": 10}, 3, 2),
    0x4CA898: ("vec4",   {"flags": 10, "desc": None}, 4, 2),
    0x4CAA80: ("int",    {"value": 4, "min": 5, "max": 6, "flags": 7, "desc": 8}, 0, 0),
    0x4CA780: ("enum",   {"enum_list": 4, "value": 5, "flags": 6, "desc": 7}, 0, 0),
    0x4CA818: ("string", {"value": 4, "flags": 5, "desc": 6}, 0, 0),
    0x4CA5C8: ("color",  {"flags": 8, "desc": 9}, 4, 0),
    0x4CAA20: ("int64",  {"value": 4, "min": 5, "max": 6, "flags": 7, "desc": 8}, 0, 0),
    0x4CA568: ("linear_color_rgb", {"flags": 9, "desc": 10}, 3, 2),
    0x4CA508: ("color_xyz", {"flags": 9, "desc": 10}, 3, 2),
}


def fmt_float(v):
    return "" if v is None else f"{v:g}"


def main():
    idx = ppcscan.load()
    sim = Sim(idx)
    elf = idx.elf

    def string(addr):
        if addr is None:
            return None
        addr &= 0xFFFFFFFF
        try:
            s = elf.cstr(addr)
            return s if s.isprintable() else None
        except (ValueError, UnicodeDecodeError):
            return None

    def enum_values(addr):
        vals = []
        try:
            while (p := elf.u32(addr + 4 * len(vals))) and len(vals) < 64:
                vals.append(string(p) or "?")
        except ValueError:
            return ""
        return "|".join(vals)

    states = sim.states_at([s for fn in REGISTER_FUNCS for s in idx.calls.get(fn, [])])
    rows, missing = [], 0
    for func, (tname, layout, nval, nlim) in REGISTER_FUNCS.items():
        for site in idx.calls.get(func, []):
            g, f = states[site]
            name = string(g.get(3))
            if name is None:
                missing += 1
                continue
            row = {"name": name, "type": tname, "register_site": f"0x{site:08X}",
                   "register_func": f"0x{func:08X}"}
            if nval:
                row["default"] = " ".join(fmt_float(f.get(i)) for i in range(1, nval + 1))
                if nlim:
                    row["min"] = fmt_float(f.get(nval + 1))
                    row["max"] = fmt_float(f.get(nval + 2))
            if "value" in layout:
                v = g.get(layout["value"])
                if tname == "string":
                    row["default"] = string(v) if v is not None else ""
                elif tname == "bool":
                    row["default"] = "" if v is None else str(int(bool(v & 0xFF)))
                else:
                    row["default"] = "" if v is None else str(s32(v) if tname != "int64" else v)
            for k in ("min", "max"):
                if k in layout:
                    v = g.get(layout[k])
                    row[k] = "" if v is None else str(s32(v) if tname != "int64" else v)
            if "enum_list" in layout:
                row["enum_values"] = enum_values(g[layout["enum_list"]] & 0xFFFFFFFF) if layout["enum_list"] in g else ""
            fl = g.get(layout["flags"])
            row["flags"] = "" if fl is None else f"0x{fl & 0xFFFFFFFF:X}"
            row["description"] = (string(g.get(layout["desc"])) or "") if layout["desc"] else ""
            ptr = sim.stored_result(site, g)
            row["dvar_ptr"] = f"0x{ptr:08X}" if ptr else ""
            rows.append(row)

    rows.sort(key=lambda r: (r["name"].lower(), r["register_site"]))
    fields = ["name", "type", "default", "min", "max", "enum_values", "flags", "dvar_ptr", "description",
              "register_func", "register_site"]
    out = sys.argv[1] if len(sys.argv) > 1 else "../data/mp/dvars.csv"
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} dvar registrations, {missing} call sites without a constant name", file=sys.stderr)


if __name__ == "__main__":
    main()
