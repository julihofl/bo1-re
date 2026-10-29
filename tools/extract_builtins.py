#!/usr/bin/env python3
"""Dump the static name->handler tables (GSC/CSC builtins, spawn funcs, UI script cmds, net handlers)."""
import csv
import sys

import ppcscan

OPD_START, OPD_END = 0xB461D0, 0xB4F6E8
# start, stride, table name, lookup function (references the table)
TABLES = [
    (0xB5C8AC, 12, "gsc_functions", 0x310FD8),
    (0xB32C2C, 12, "gsc_methods_player", 0x2C3228),
    (0xB33440, 12, "gsc_methods_hudelem", 0x2DEE70),
    (0xB33918, 12, "gsc_methods_scriptent_vehicle", 0x307668),
    (0xB40390, 12, "gsc_methods_actor", 0x60EB80),
    (0xB5A2F4, 12, "csc_functions", 0x144AC0),
    (0xB311D8, 12, "csc_methods", 0x1448B0),
    (0xB31728, 12, "csc_methods_entity", 0x15C690),
    (0xB34BE0, 8, "spawn_functions", 0x356BE0),
    (0xB34D38, 8, "weapon_spawn_or_field_parsers", None),
    (0xB3EE84, 8, "ui_menu_script_commands", 0x44B130),
    (0xB31910, 8, "net_msg_handlers_a", 0x1B44A0),
    (0xB319F8, 8, "net_msg_handlers_b", 0x1E5220),
    (0xB31AE8, 8, "net_msg_handlers_c", 0x203AD8),
    (0xB31BA0, 8, "net_msg_handlers_d", 0x216368),
    (0xB3ECC4, 8, "net_msg_handlers_e", 0x3F1560),
]


def entries(elf, start, stride):
    a = start
    while True:
        name_ptr, opd = elf.u32(a), elf.u32(a + 4)
        if not (OPD_START <= opd < OPD_END and (opd - OPD_START) % 8 == 0):
            return
        try:
            name = elf.cstr(name_ptr)
        except ValueError:
            return
        if not name.isprintable():
            return
        dev = elf.u32(a + 8) if stride >= 12 else ""
        yield a, name, opd, elf.u32(opd), dev
        a += stride


def main():
    elf = ppcscan.load().elf
    rows = []
    for start, stride, table, lookup in TABLES:
        for entry, name, opd, func, dev in entries(elf, start, stride):
            rows.append({"table": table, "name": name, "handler": f"0x{func:08X}", "handler_opd": f"0x{opd:08X}",
                         "developer": dev, "entry": f"0x{entry:08X}",
                         "lookup_func": f"0x{lookup:08X}" if lookup else ""})
    out = sys.argv[1] if len(sys.argv) > 1 else "../data/mp/builtins.csv"
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    for t, n in Counter(r["table"] for r in rows).items():
        print(f"{t:34s} {n}", file=sys.stderr)


if __name__ == "__main__":
    main()
