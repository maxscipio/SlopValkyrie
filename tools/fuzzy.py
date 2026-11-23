"""Best approximate position of unmatched XDK lib functions in the XBE (reference use only).

usage: fuzzy.py <default.xbe> <match.json> <lib> <regex> [maxbad]
Lists, for each lib function matching <regex> that libmatch did not find, the XBE
addresses with the fewest differing bytes outside relocation fields.
"""
import json
import re
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("\\", 1)[0])
from libmatch import functions, load_xbe, parse_ar, parse_coff  # noqa: E402


def main():
    xbe, mj, lib, rx = sys.argv[1:5]
    maxbad = float(sys.argv[5]) if len(sys.argv) > 5 else 0.25
    found = json.load(open(mj))["functions"]
    secs = load_xbe(xbe)
    code = [(va, np.frombuffer(b, np.uint8)) for va, b in secs[:1]] + \
           [(va, np.frombuffer(b, np.uint8)) for va, b in secs[1:] if len(b)]
    want = re.compile(rx)
    for mn, body in parse_ar(lib):
        c = parse_coff(body)
        if not c:
            continue
        for f in functions(*c, mn):
            if f["name"] in found or not want.search(f["name"]):
                continue
            fb = np.frombuffer(f["b"], np.uint8)
            mk = np.frombuffer(f["m"], np.uint8) == 0
            n = len(fb)
            best = []
            for va, arr in code:
                if len(arr) < n:
                    continue
                cnt = len(arr) - n + 1
                bad = np.zeros(cnt, np.int32)
                for i in np.nonzero(mk)[0]:
                    bad += arr[i:i + cnt] != fb[i]
                tot = int(mk.sum())
                for p in np.argsort(bad)[:3]:
                    best.append((int(bad[p]), va + int(p), tot))
            best.sort()
            top = [(b, hex(v), t) for b, v, t in best[:3] if b <= maxbad * max(t, 1)]
            print(f["name"][:60], n, top)


main()
