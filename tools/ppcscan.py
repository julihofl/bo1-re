"""Fast reference/call scanner for PS3 PPU code (no full disassembly).

Runs ppcsim.step() linearly over .text (state resets at each function start) and
records every resolved absolute reference plus every `bl` call edge.
"""
import bisect
import pickle
import struct
from collections import defaultdict
from pathlib import Path

from ppcsim import step
from ps3elf import Ps3Elf

TEXT_START, TEXT_END = 0x10230, 0x8C37EC
OPD_START, OPD_END = 0xB461D0, 0xB4F6E8
ROOT = Path(__file__).resolve().parent.parent


class Index:
    def __init__(self, elf: Ps3Elf):
        self.elf = elf
        self.opd = {}         # func addr -> opd addr
        self.refs = defaultdict(list)   # target -> [insn addr]
        self.calls = defaultdict(list)  # callee -> [callsite]
        self.funcs = []       # sorted function starts

    def build(self):
        e = self.elf
        for opd, func, _ in e.opd_entries(OPD_START, OPD_END):
            self.opd[func] = opd
        starts = set(self.opd)
        code = e.read(TEXT_START, TEXT_END - TEXT_START)
        words = struct.unpack(f">{len(code) // 4}I", code)
        # First pass: collect bl targets as additional function starts.
        for i, w in enumerate(words):
            if w >> 26 == 18 and w & 3 == 1:
                li = w & 0x03FFFFFC
                if li & 0x02000000:
                    li -= 0x04000000
                pc = TEXT_START + i * 4
                tgt = (pc + li) & 0xFFFFFFFF
                self.calls[tgt].append(pc)
                starts.add(tgt)
        extra = ROOT / "data/mp/ghidra_functions.txt"
        if extra.exists():
            starts.update(int(l, 16) for l in extra.read_text().split() if l.startswith("0x"))
        self.funcs = sorted(s for s in starts if TEXT_START <= s < TEXT_END)
        fstart = set(self.funcs)
        toc = e.toc
        g, f = {}, {}
        for i, w in enumerate(words):
            pc = TEXT_START + i * 4
            if pc in fstart:
                g.clear()
            ref = step(g, f, pc, w, toc)
            if ref is not None and 0x10000 <= ref < 0x30000000:
                self.refs[ref].append(pc)
        return self

    def func_of(self, addr: int):
        i = bisect.bisect_right(self.funcs, addr) - 1
        return self.funcs[i] if i >= 0 else None

    def words(self, start: int, count: int):
        return struct.unpack(f">{count}I", self.elf.read(start, count * 4))


def load(target: str = "mp") -> Index:
    elf_path = ROOT / f"build/EBOOT_{target.upper()}.elf"
    cp = ROOT / f"build/index_{target}.pkl"
    if cp.exists() and cp.stat().st_mtime > elf_path.stat().st_mtime and all(cp.stat().st_mtime > (Path(__file__).parent / m).stat().st_mtime for m in ('ppcscan.py', 'ppcsim.py', '../data/mp/ghidra_functions.txt')):
        idx = pickle.loads(cp.read_bytes())
        idx.elf = Ps3Elf(elf_path)
        return idx
    idx = Index(Ps3Elf(elf_path)).build()
    elf, idx.elf = idx.elf, None
    cp.write_bytes(pickle.dumps(idx))
    idx.elf = elf
    return idx
