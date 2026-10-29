"""Append a synthetic .symtab/.strtab and a rebuilt .shstrtab to an ELF32 image.

The retail-derived EBOOT has its section names zeroed and no symbols. Ghidra only
creates functions it can reach by flow or symbols, so address-taken PS3 functions
(reachable only through .opd) would be missing. One STT_FUNC per known entry point
fixes that and carries the database names into any ELF-aware tool.
"""
import struct

# Reconstructed section names by index; "?" marks names inferred from content only.
SECTION_NAMES = {
    1: ".init", 2: ".text", 3: ".fini", 4: ".sceStub.text", 5: ".rodata.sceResident",
    6: ".rodata.sceFNID", 7: ".lib.ent.top", 8: ".lib.ent.btm", 9: ".lib.stub.top", 10: ".lib.stub",
    11: ".lib.stub.btm", 12: ".rodata", 13: ".rodata.guid?", 14: ".spu_image?", 15: ".sys_proc_param",
    16: ".sys_proc_prx_param", 17: ".ctors", 18: ".dtors", 19: ".ctors_end?", 20: ".data.rel.ro?",
    21: ".data.sceFStub", 22: ".opd", 23: ".toc", 24: ".tdata", 25: ".tbss", 26: ".data", 27: ".bss",
    28: ".unk28", 29: ".comment?", 30: ".shstrtab_zeroed",
}
STT_OBJECT, STT_FUNC, STB_GLOBAL = 1, 2, 1


def add_symbols(img: bytes, symbols) -> bytes:
    """symbols: iterable of (name, value, size, kind) with kind in {"func", "object"}."""
    d = bytearray(img)
    shoff, = struct.unpack(">I", d[32:36])
    shnum, shstrndx = struct.unpack(">HH", d[48:52])
    shdrs = [list(struct.unpack(">10I", d[shoff + i * 40:shoff + i * 40 + 40])) for i in range(shnum)]
    alloc = [(i, h[3], h[3] + h[5]) for i, h in enumerate(shdrs) if h[2] & 2 and h[5]]

    def shndx(va):
        return next((i for i, lo, hi in alloc if lo <= va < hi), 0xFFF1)  # SHN_ABS if unmapped

    strtab = bytearray(b"\0")
    syms = bytearray(16)  # null symbol
    for name, value, size, kind in symbols:
        off = len(strtab)
        strtab += name.encode() + b"\0"
        info = (STB_GLOBAL << 4) | (STT_FUNC if kind == "func" else STT_OBJECT)
        syms += struct.pack(">IIIBBH", off, value, size, info, 0, shndx(value))

    shstr = bytearray(b"\0")
    for i, h in enumerate(shdrs):
        if i in SECTION_NAMES:
            h[0] = len(shstr)
            shstr += SECTION_NAMES[i].encode() + b"\0"

    def new_name(n):
        nonlocal shstr
        off = len(shstr)
        shstr += n.encode() + b"\0"
        return off

    def append(blob, align):
        nonlocal d
        d += b"\0" * (-len(d) % align)
        off = len(d)
        d += blob
        return off

    symtab_idx, strtab_idx = len(shdrs), len(shdrs) + 1
    sym_off = append(bytes(syms), 4)
    str_off = append(bytes(strtab), 1)
    shdrs.append([new_name(".symtab"), 2, 0, 0, sym_off, len(syms), strtab_idx, 1, 4, 16])
    shdrs.append([new_name(".strtab"), 3, 0, 0, str_off, len(strtab), 0, 0, 1, 0])
    shstr_name = new_name(".shstrtab")
    shstr_off = append(bytes(shstr), 1)
    shdrs.append([shstr_name, 3, 0, 0, shstr_off, len(shstr), 0, 0, 1, 0])
    new_shoff = append(b"".join(struct.pack(">10I", *h) for h in shdrs), 4)
    d[32:36] = struct.pack(">I", new_shoff)
    d[48:52] = struct.pack(">HH", len(shdrs), len(shdrs) - 1)
    return bytes(d)
