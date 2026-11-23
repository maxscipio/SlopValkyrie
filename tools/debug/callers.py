"""callers.py <hexva>... : E8 callers and FF15 [thunk] users of function VAs in default.xbe; also xbe kernel imports by name."""
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


for a in sys.argv[1:]:
    t = int(a, 16)
    print('target %x' % t)
    for n, va, vs, ro, rs in secs:
        if n not in ('.text', 'D3D', 'DSOUND', 'XGRPH', 'XPP', 'WMADEC', 'D3DX'):
            continue
        p = ro
        end = ro + rs - 5
        while (p := d.find(b'\xe8', p, end)) >= 0:
            rel = struct.unpack_from('<i', d, p + 1)[0]
            tgt = (va + p - ro + 5 + rel) & 0xFFFFFFFF
            if tgt == t:
                print('  call from %x (%s)' % (va + p - ro, n))
            p += 1
