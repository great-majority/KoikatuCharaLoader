#!/usr/bin/env python3
"""
quickdiff.py ― compare one Koikatu‑character PNG against its re‑saved version

Usage:
    python quickdiff.py ORIGINAL.png  [--parser ./xd3_to_bindiff.py]

Steps performed automatically:
 1. Load ORIGINAL.png with KoikatuCharaData, save to a **temp dir**.
 2. Run `xdelta3 -f -e -s ORIGINAL temp/NEW patch.xd3`.
 3. Pipe `xdelta3 printdelta patch.xd3` through the human parser.
 4. **Print only the DELETE/INSERT/REPLACE lines** produced by the parser.

All temporaries are removed on exit.  No extra output is produced.
"""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from kkloader import KoikatuCharaData

XDELTA_BIN = "xdelta3"  # change via env if necessary

def main(argv=None):
    ap = argparse.ArgumentParser(description="Round‑trip a single PNG and show bindiff lines")
    ap.add_argument("png", type=Path, help="Original character PNG file")
    ap.add_argument("--parser", default="./xd3_to_bindiff.py", type=Path, help="Path to xd3_to_bindiff.py")
    args = ap.parse_args(argv)

    if not args.png.is_file():
        sys.exit(f"File not found: {args.png}")

    # 1. round‑trip into temp dir
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        saved = tmpdir / args.png.name
        patch = tmpdir / "patch.xd3"

        print(args.png)
        kc = KoikatuCharaData.load(str(args.png))
        kc.save(saved)

        # 2. make xdelta patch
        subprocess.run([
            XDELTA_BIN, "-f", "-e", "-s", str(args.png), str(saved), str(patch)
        ], check=True)

        # 3. pipe through parser, print only final result lines
        proc_print = subprocess.Popen([XDELTA_BIN, "printdelta", str(patch)], stdout=subprocess.PIPE)
        proc_parse = subprocess.Popen([sys.executable, str(args.parser)], stdin=proc_print.stdout)
        proc_parse.communicate()
        proc_print.stdout.close()
        proc_print.wait()

if __name__ == "__main__":
    main()
