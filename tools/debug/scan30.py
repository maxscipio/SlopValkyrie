import struct, sys, re
import os
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
pats = {
 'mov [r+0x24],0x1e': rb'\xc7[\x40-\x47\x80-\x87]\x24\x1e\x00\x00\x00',
 'imm 1/30f': rb'\x89\x88\x08\x3d',
 'imm 1/30f b': rb'\x08\x89\x88\x3d',
}
for k, p in pats.items():
    print(k)
    for m in re.finditer(p, d, re.S):
        print('  %x' % va_of(m.start()))
