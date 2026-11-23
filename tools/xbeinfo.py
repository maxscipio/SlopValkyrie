"""Print what decides how to port an XBE: title, title id, build type, sections, linked XDK libraries (and which of
those the SDK already has signatures for).

usage: xbeinfo.py <default.xbe> [sdk\\xdk]
"""
import os
import struct
import sys

BASE_DEFAULT = 0x10000


def main():
    path = sys.argv[1]
    d = open(path, "rb").read()
    if d[:4] != b"XBEH":
        raise SystemExit("not an XBE")
    u32 = lambda o: struct.unpack_from("<I", d, o)[0]
    base = u32(0x104)
    off = lambda va: va - base
    cert = off(u32(0x118))
    title = d[cert + 0x0C:cert + 0x0C + 80].decode("utf-16le").split("\0")[0]
    tid = u32(cert + 0x08)
    entry_raw = u32(0x128)
    kind = "retail" if (entry_raw ^ 0xA8FC57AB) < 0x10000000 else "debug"
    entry = entry_raw ^ (0xA8FC57AB if kind == "retail" else 0x94859D4B)
    print(f"file        {path} ({len(d):,} bytes)")
    print(f"title       {title}")
    print(f"title id    {tid:08X} ({chr(tid >> 24 & 255)}{chr(tid >> 16 & 255)}-{tid & 0xFFFF:03d})")
    print(f"build       {kind}, base {base:#x}, entry {entry:#x}, image {u32(0x10C):#x}")
    print(f"debug name  {d[off(u32(0x14C)):off(u32(0x14C)) + 120].split(b'\0')[0].decode('latin1')}")

    ns, sh = u32(0x11C), off(u32(0x120))
    print("sections")
    for i in range(ns):
        flags, va, vs, ro, rs, nm = struct.unpack_from("<IIIIII", d, sh + i * 56)
        name = d[off(nm):off(nm) + 12].split(b"\0")[0].decode("latin1")
        print(f"  {name:<10} va {va:#010x} size {vs:#9x} flags {flags:#x}{'  exec' if flags & 4 else ''}")

    nl, la = u32(0x160), off(u32(0x164))
    libs = []
    for i in range(nl):
        name = d[la + i * 16:la + i * 16 + 8].split(b"\0")[0].decode("latin1")
        major, minor, build, flags = struct.unpack_from("<HHHH", d, la + i * 16 + 8)
        libs.append((name, build, flags))
    have = set()
    if len(sys.argv) > 2 and os.path.isdir(sys.argv[2]):
        have = {x for x in os.listdir(sys.argv[2]) if os.path.isdir(os.path.join(sys.argv[2], x))}
    print("libraries")
    for name, build, flags in libs:
        print(f"  {name:<9} {build}  (flags {flags:#06x})")
    builds = sorted({b for _, b, _ in libs})
    if have:
        print(f"SDK xdk/ has: {', '.join(sorted(have))}")
        for b in builds:
            print(f"  build {b}: {'signatures available' if str(b) in have else 'NO signatures/layout: see PORTING_GUIDE step 4'}")


main()
