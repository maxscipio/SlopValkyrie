"""Minimal XDVDFS (xiso) reader: list files and extract them.

usage: xiso.py <iso> ls
       xiso.py <iso> extract <dest> [name-filter]
"""
import os
import struct
import sys

SECTOR = 2048


def open_volume(f):
    for base in (0, 0x2600000, 0xFDA0000, 0x18300000):
        f.seek(base + 32 * SECTOR)
        if f.read(20) == b"MICROSOFT*XBOX*MEDIA":
            root_sector, root_size = struct.unpack("<II", f.read(8))
            return base, root_sector, root_size
    raise SystemExit("no XDVDFS volume descriptor found")


def walk(f, base, sector, size, prefix=""):
    if size == 0:
        return
    f.seek(base + sector * SECTOR)
    data = f.read(size)

    def visit(off):
        if off + 14 > len(data):
            return
        left, right, start, fsize, attr, nlen = struct.unpack_from("<HHIIBB", data, off)
        if left == 0xFFFF and right == 0xFFFF and start == 0xFFFFFFFF:
            return
        name = data[off + 14:off + 14 + nlen].decode("latin-1")
        if left:
            yield from visit(left * 4)
        path = prefix + name
        if attr & 0x10:
            yield (path + "/", start, fsize, True)
            yield from walk(f, base, start, fsize, path + "/")
        else:
            yield (path, start, fsize, False)
        if right:
            yield from visit(right * 4)

    yield from visit(0)


def main():
    iso, cmd = sys.argv[1], sys.argv[2]
    with open(iso, "rb") as f:
        base, rs, rsize = open_volume(f)
        entries = list(walk(f, base, rs, rsize))
        if cmd == "ls":
            for p, s, n, d in entries:
                print(f"{n:>12}  {p}")
            return
        dest = sys.argv[3]
        flt = sys.argv[4].lower() if len(sys.argv) > 4 else None
        for p, s, n, d in entries:
            if flt and flt not in p.lower():
                continue
            out = os.path.join(dest, p)
            if d:
                os.makedirs(out, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(out), exist_ok=True)
            f.seek(base + s * SECTOR)
            left = n
            with open(out, "wb") as o:
                while left:
                    chunk = f.read(min(left, 1 << 22))
                    o.write(chunk)
                    left -= len(chunk)
            print(p)


main()
