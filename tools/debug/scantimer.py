"""Find functions that load the timer pointer [0x3219cc] and then touch +0x24/+0x20/+0x08 of the result."""
import struct, sys, re
from capstone import *
import os
d = open(os.environ.get('XBE', os.path.join('assets', 'default.xbe')), 'rb').read()
base = 0x10000
ns = struct.unpack_from('<I', d, 0x11C)[0]
sh = struct.unpack_from('<I', d, 0x120)[0] - base
secs = []
for i in range(ns):
    f, va, vs, ro, rs, nm = struct.unpack_from('<IIIIII', d, sh + i * 56)
    secs.append((d[nm - base:nm - base + 12].split(b'\0')[0].decode('latin1'), va, vs, ro, rs))
text = [s for s in secs if s[0] == '.text'][0]
_, va, vs, ro, rs = text
code = d[ro:ro + rs]
md = Cs(CS_ARCH_X86, CS_MODE_32)
hits = []
for m in re.finditer(rb'[\x8b\xa1].{0,1}\xcc\x19\x32\x00', code, re.S):
    a = va + m.start()
    ins = list(md.disasm(code[m.start():m.start() + 40], a))
    if not ins:
        continue
    first = ins[0]
    if '0x3219cc' not in first.op_str:
        continue
    reg = first.op_str.split(',')[0]
    txt = ' | '.join('%x %s %s' % (i.address, i.mnemonic, i.op_str) for i in ins[1:6])
    if re.search(r'\+ 0x(24|20|8)\]', txt) or '[%s]' % reg in txt:
        hits.append((a, txt))
for a, t in hits:
    print('%x  %s' % (a, t))
