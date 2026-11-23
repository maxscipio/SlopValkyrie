import struct, sys
from capstone import *
import os
# XBE=<path> overrides; default is assets\default.xbe of the current directory
d = open(os.environ.get('XBE', os.path.join('assets', 'default.xbe')), 'rb').read()
base = 0x10000
ns = struct.unpack_from('<I', d, 0x11C)[0]
sh = struct.unpack_from('<I', d, 0x120)[0] - base
secs = []
for i in range(ns):
    f, va, vs, ro, rs, nm = struct.unpack_from('<IIIIII', d, sh + i * 56)
    secs.append((d[nm - base:nm - base + 12].split(b'\0')[0].decode('latin1'), va, vs, ro, rs))


def off(a):
    for n, va, vs, ro, rs in secs:
        if va <= a < va + vs:
            return ro + a - va


def sym(a):
    o = off(a)
    if o is None or o + 4 > len(d):
        return ''
    s = d[o:o + 48].split(b'\0')[0]
    if len(s) >= 4 and all(32 <= c < 127 for c in s):
        return '  ; "%s"' % s.decode()
    return ''


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = False
start = int(sys.argv[1], 16)
n = int(sys.argv[2], 16)
o = off(start)
import re
for i in md.disasm(d[o:o + n], start):
    note = ''
    for m in re.finditer(r'0x([0-9a-f]{6})\b', i.op_str):
        a = int(m.group(1), 16)
        if a >= 0x11000 and off(a) is not None:
            note = sym(a) or note
    print('%x  %s %s%s' % (i.address, i.mnemonic, i.op_str, note))
