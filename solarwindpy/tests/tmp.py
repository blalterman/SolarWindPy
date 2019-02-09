#! /usr/bin/env python

import os
import sys
from pathlib import Path

extra = Path(__file__).resolve().parent.parent
#extra = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

extra = str(extra)

print(__file__)
print(extra)
print()

print(*sys.path, sep="\n")
print()

sys.path.insert(0, extra)
print(*sys.path, sep="\n")
