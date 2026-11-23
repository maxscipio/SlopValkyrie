import sys, struct
from minidump.minidumpfile import MinidumpFile

m = MinidumpFile.parse(sys.argv[1])
ex = m.exception.exception_records[0]
rec = ex.ExceptionRecord
print("code", rec.ExceptionCode, rec.ExceptionAddress, ex.ThreadId, rec.NumberParameters)
params = rec.ExceptionInformation
print([hex(p) for p in params[:rec.NumberParameters]])
rd = m.get_reader()

def rd_mem(addr, n):
    try:
        return rd.read(addr, n)
    except Exception as e:
        return None

# MSVC x64 throw: params = magic, object, throwinfo, image base
if rec.NumberParameters >= 4:
    obj, ti, base = params[1], params[2], params[3]
    b = rd_mem(ti, 16)
    if b:
        attrs, unw, fwd, catchtable = struct.unpack("<iiii", b)
        ct = rd_mem(base + catchtable, 8)
        n, first = struct.unpack("<ii", ct)
        for i in range(n):
            ctb = rd_mem(base + first + 4 * i, 4)
            off = struct.unpack("<i", ctb)[0]
            ent = rd_mem(base + off, 28)
            props, tdoff = struct.unpack("<ii", ent[:8])
            td = rd_mem(base + tdoff + 16, 96)
            print("type:", td.split(b"\0")[0])
    ob = rd_mem(obj, 64)
    print("object bytes:", ob.hex() if ob else None)
    if ob:
        for off in range(0, 64, 8):
            p = struct.unpack("<Q", ob[off:off+8])[0]
            s = rd_mem(p, 120)
            if s and all(32 <= c < 127 or c == 0 for c in s[:20]) and s[0]:
                print("string at +%d: %r" % (off, s.split(b"\0")[0]))

