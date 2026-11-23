"""Match the functions of XDK .lib files against an XBE by bytes, relocations masked.

usage: libmatch.py <default.xbe> <out.json> <lib>...

The libraries are read as a reference only. Functions that share their bytes are told
apart by the relocation targets they point at, repeated until nothing more resolves.
Writes {lib symbol: {lib, len, va: [..]}} for every function found, and the data
symbols the matched functions refer to.
"""
import json
import struct
import sys
from collections import Counter, defaultdict

DIR32, DIR32NB, REL32 = 6, 7, 0x14
ABS_TYPES = (DIR32, DIR32NB)
FIELD_TYPES = (DIR32, DIR32NB, REL32, 0xA, 0xB)


def parse_ar(path):
    d = open(path, "rb").read()
    assert d[:8] == b"!<arch>\n"
    pos = 8
    longnames = b""
    out = []
    while pos + 60 <= len(d):
        hdr = d[pos:pos + 60]
        name = hdr[:16].decode("latin-1").strip()
        size = int(hdr[48:58])
        body = d[pos + 60:pos + 60 + size]
        pos += 60 + size + (size & 1)
        if name == "//":
            longnames = body
        elif name in ("/", ""):
            continue
        else:
            if name.startswith("/") and name[1:].isdigit():
                o = int(name[1:])
                e = min(x for x in (longnames.find(b"\n", o), longnames.find(b"\0", o), len(longnames)) if x >= 0)
                name = longnames[o:e].decode("latin-1")
            out.append((name.rstrip("/"), body))
    return out


def parse_coff(b):
    if len(b) < 20:
        return None
    machine, nsec, _, symptr, nsym = struct.unpack_from("<HHIII", b, 0)
    if machine != 0x14C or nsec == 0 or nsec > 4000:
        return None
    strs = b[symptr + nsym * 18:]

    def sname(raw):
        if raw[:4] == b"\0\0\0\0":
            o = struct.unpack("<I", raw[4:8])[0]
            return strs[o:strs.index(b"\0", o)].decode("latin-1")
        return raw.rstrip(b"\0").decode("latin-1")

    syms = []
    symmap = {}
    i = 0
    while i < nsym:
        o = symptr + i * 18
        nm = sname(b[o:o + 8])
        val, sn, ty, sc, aux = struct.unpack_from("<IhHBB", b, o + 8)
        symmap[i] = len(syms)
        syms.append((nm, val, sn, ty, sc))
        i += 1 + aux
    secs = []
    for i in range(nsec):
        o = 20 + i * 40
        size, rawp, relp = struct.unpack_from("<III", b, o + 16)
        nr = struct.unpack_from("<H", b, o + 32)[0]
        fl = struct.unpack_from("<I", b, o + 36)[0]
        data = b[rawp:rawp + size] if not (fl & 0x80) else b""
        relocs = []
        for r in range(nr):
            va_, si, ty = struct.unpack_from("<IIH", b, relp + r * 10)
            relocs.append((va_, symmap.get(si), ty))
        secs.append({"data": data, "relocs": relocs, "flags": fl})
    return secs, syms


def functions(secs, syms, obj):
    """yield dicts for the external and static functions in executable sections"""

    def key(nm, ty, sc):
        if sc == 2:
            return nm
        return obj + ":" + nm if sc == 3 and ty == 0x20 else None

    by_sec = defaultdict(list)
    for nm, val, sn, ty, sc in syms:
        if sn > 0 and secs[sn - 1]["flags"] & 0x20000000 and key(nm, ty, sc):
            by_sec[sn - 1].append((val, key(nm, ty, sc)))
    for si, lst in by_sec.items():
        s = secs[si]
        lst.sort()
        data = s["data"]
        mask = bytearray(len(data))
        for va, _, ty in s["relocs"]:
            if ty in FIELD_TYPES and va + 4 <= len(mask):
                for k in range(4):
                    mask[va + k] = 1
        for j, (val, nm) in enumerate(lst):
            end = next((v for v, _ in lst[j + 1:] if v > val), len(data))
            if end <= val:
                continue
            rel = []
            for va, sidx, ty in s["relocs"]:
                if val <= va < end and va + 4 <= end and ty in FIELD_TYPES and sidx is not None:
                    tn, tv, tsn, tty, tsc = syms[sidx]
                    tk = key(tn, tty, tsc)
                    if tk:
                        addend = struct.unpack_from("<i", data, va)[0]
                        rel.append((va - val, ty, tk, addend, tsn > 0))
            yield {"name": nm, "b": bytes(data[val:end]), "m": bytes(mask[val:end]), "rel": rel}


def load_xbe(path):
    d = open(path, "rb").read()
    base = 0x10000
    ns = struct.unpack_from("<I", d, 0x11C)[0]
    sp = struct.unpack_from("<I", d, 0x120)[0] - base
    secs = []
    for i in range(ns):
        fl, va, vs, ra, rs = struct.unpack_from("<IIIII", d, sp + i * 56)
        secs.append((va, d[ra:ra + rs]))
    return secs


def main():
    xbe, out, libs = sys.argv[1], sys.argv[2], sys.argv[3:]
    secs = load_xbe(xbe)
    big = b"".join(b for _, b in secs)
    starts = []
    off = 0
    for va, b in secs:
        starts.append((off, va, len(b)))
        off += len(b)
    index = defaultdict(list)
    for i in range(len(big) - 3):
        index[big[i:i + 4]].append(i)

    def to_va(o):
        for s, va, n in starts:
            if s <= o < s + n:
                return va + o - s
        return None

    def read32(va):
        for s, v, n in starts:
            if v <= va and va + 4 <= v + n:
                return struct.unpack_from("<I", big, s + va - v)[0]
        return None

    funcs = {}
    tried = set()
    for lib in libs:
        for mname, body in parse_ar(lib):
            c = parse_coff(body)
            if not c:
                continue
            for f in functions(*c, mname):
                fb, mk = f["b"], f["m"]
                if len(fb) < 8 or f["name"] in funcs:
                    continue
                a = next((i for i in range(len(fb) - 3) if not any(mk[i:i + 4])), None)
                if a is None:
                    continue
                tried.add(f["name"])
                hits = set()
                for p in index.get(fb[a:a + 4], ()):
                    s = p - a
                    if s < 0 or s + len(fb) > len(big):
                        continue
                    cand = big[s:s + len(fb)]
                    if all(mk[i] or cand[i] == fb[i] for i in range(len(fb))):
                        va = to_va(s)
                        if va is not None:
                            hits.add(va)
                if hits:
                    f["lib"] = lib.split("\\")[-1]
                    f["va"] = hits
                    funcs[f["name"]] = f

    def data_bases():
        votes = defaultdict(Counter)
        for f in funcs.values():
            if len(f["va"]) != 1:
                continue
            c = next(iter(f["va"]))
            for off, ty, tn, add, defined in f["rel"]:
                if ty in ABS_TYPES and tn not in funcs:
                    v = read32(c + off)
                    if v is not None:
                        votes[tn][(v - add) & 0xFFFFFFFF] += 1
        return votes

    # drop candidates whose relocations point at something that has settled elsewhere or is not in the image
    changed = True
    while changed:
        changed = False
        votes = data_bases()
        claims = Counter(va for f in funcs.values() for va in f["va"])
        dead = []
        for fname, f in funcs.items():
            keep = set()
            for c in f["va"]:
                ok = True
                for off, ty, tn, add, defined in f["rel"]:
                    t = funcs.get(tn)
                    v = read32(c + off)
                    if t:
                        wants = [tv + add if ty in ABS_TYPES else tv + add - (c + off + 4) for tv in t["va"]]
                        if v is None or all((v - w) & 0xFFFFFFFF for w in wants):
                            ok = False
                            break
                        continue
                    elif tn in tried and (len(f["va"]) > 1 or claims[c] > 1):
                        ok = False  # a function the image does not contain
                        break
                    elif ty in ABS_TYPES and votes.get(tn):
                        top, n = votes[tn].most_common(1)[0]
                        if n < 2 or n < sum(votes[tn].values()) * 0.8:
                            continue
                        want = top + add
                    else:
                        continue
                    if v is None or (v - want) & 0xFFFFFFFF:
                        ok = False
                        break
                if ok:
                    keep.add(c)
            if keep != f["va"]:
                changed = True
                if keep:
                    f["va"] = keep
                else:
                    dead.append(fname)
        for fname in dead:
            del funcs[fname]

    # data the matched functions refer to
    votes = data_bases()
    data = {k: [[hex(a), n] for a, n in c.most_common(3)] for k, c in votes.items()}

    res = {n: {"lib": f["lib"], "len": len(f["b"]), "va": sorted(f["va"])} for n, f in funcs.items()}
    json.dump({"functions": res, "data": data, "absent": sorted(tried - set(funcs))}, open(out, "w"), indent=0)
    print(len(res), "functions found,", sum(len(f["va"]) == 1 for f in funcs.values()), "unique;", len(data), "data symbols")


if __name__ == "__main__":
    main()
