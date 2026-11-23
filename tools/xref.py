"""Find the 32-bit immediates in default.xbe that equal a VA, or the VA of a string: python tools\\xref.py <hexva | "string">"""
import struct, sys

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


def va_of(o):
    for n, va, vs, ro, rs in secs:
        if ro <= o < ro + rs:
            return va + o - ro


arg = sys.argv[1]
targets = []
try:
    targets = [int(arg, 16)]
except ValueError:
    p = 0
    while (p := d.find(arg.encode() + b'\0', p)) >= 0:
        targets.append(va_of(p))
        p += 1
for t in targets:
    print('target %x' % t)
    pat = struct.pack('<I', t)
    p = 0
    while (p := d.find(pat, p)) >= 0:
        print('  at %x (file %x)' % (va_of(p), p))
        p += 1
