"""Address -> name mapping from the data/ databases.

Curated names (functions.csv, globals.csv, imports.csv) win over names derived
automatically from handler tables (builtins.csv, commands.csv).
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILTIN_PREFIX = {
    "gsc_functions": "GScr_", "gsc_methods_player": "PlayerCmd_", "gsc_methods_hudelem": "HECmd_",
    "gsc_methods_scriptent_vehicle": "ScrCmd_", "gsc_methods_actor": "ActorCmd_", "csc_functions": "CScr_",
    "csc_methods": "CScrCmd_", "csc_methods_entity": "CScrEntCmd_", "spawn_functions": "SP_",
    "weapon_spawn_or_field_parsers": "WeapParse_", "ui_menu_script_commands": "UIScript_",
}


def _rows(target, name):
    p = ROOT / "data" / target / name
    return csv.DictReader(p.open()) if p.exists() else []


def auto_function_names(target: str = "mp") -> dict:
    names = {}
    for r in _rows(target, "commands.csv"):
        if r["handler"]:
            prefix = "SV_Cmd_" if r["kind"] == "server" else "Cmd_"
            names.setdefault(int(r["handler"], 16), f"{prefix}{r['name'].replace('+', 'plus_').replace('-', 'minus_')}_f")
    for r in _rows(target, "builtins.csv"):
        prefix = BUILTIN_PREFIX.get(r["table"], "NetMsg_")
        names.setdefault(int(r["handler"], 16), f"{prefix}{r['name']}")
    return names


def curated_names(target: str = "mp") -> dict:
    names = {}
    for r in _rows(target, "imports.csv"):
        names[int(r["stub_code"], 16)] = r["name"]
    for r in _rows(target, "functions.csv"):
        names[int(r["addr"], 16)] = r["name"]
    for r in _rows(target, "globals.csv"):
        names[int(r["addr"], 16)] = r["name"]
    return names


def load_names(target: str = "mp") -> dict:
    names = auto_function_names(target)
    names.update(curated_names(target))
    return names
