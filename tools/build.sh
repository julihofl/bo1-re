#!/usr/bin/env bash
# Rebuild every derived artifact for the MP EBOOT from ../EBOOT_MP.BIN.
# Optional: RPCS3_MODULES=<rpcs3>/rpcs3/Emu/Cell/Modules re-resolves import NIDs.
set -euo pipefail
cd "$(dirname "$0")"
PY=../.venv/bin/python
mkdir -p ../build

python3 -I self2elf.py ../EBOOT_MP.BIN ../build/EBOOT_MP.elf
if [[ -n "${RPCS3_MODULES:-}" ]]; then
    $PY nids.py ../build/EBOOT_MP.elf ../data/mp/imports.csv ../data/nid_names_extra.txt \
        $(find "$RPCS3_MODULES" -name '*.cpp')
fi
$PY extract_dvars.py
$PY extract_commands.py
$PY extract_builtins.py
$PY gen_headers.py
$PY validate_db.py
$PY elf64to32.py ../build/EBOOT_MP.elf ../build/EBOOT_MP.sym.elf32 --symbols ../data/mp
