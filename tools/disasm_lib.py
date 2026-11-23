"""Disassemble XDK lib functions with their relocation targets named (reference only).

usage: disasm_lib.py <lib> <regex> [match.json]   prints the XBE address too when match.json has one
"""
import json
import re
import sys

from capstone import CS_ARCH_X86, CS_MODE_32, Cs

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
from libmatch import functions, parse_ar, parse_coff  # noqa: E402


def main():
    lib, rx = sys.argv[1:3]
    found = json.load(open(sys.argv[3]))["functions"] if len(sys.argv) > 3 else {}
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = False
    want = re.compile(rx)
    for mn, body in parse_ar(lib):
        c = parse_coff(body)
        if not c:
            continue
        for f in functions(*c, mn):
            if not want.search(f["name"]):
                continue
            va = found.get(f["name"], {}).get("va")
            print("==", f["name"], len(f["b"]), [hex(x) for x in va] if va else "")
            rel = {r[0]: r for r in f["rel"]}
            for i in md.disasm(f["b"], 0):
                note = ""
                for o, r in rel.items():
                    if i.address <= o < i.address + i.size:
                        note = "   ; " + r[2] + (" %+d" % r[3] if r[3] else "")
                print("  %04x %-6s %s%s" % (i.address, i.mnemonic, i.op_str, note))


main()
