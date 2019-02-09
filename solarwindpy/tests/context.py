print("starting file", __file__)
import os
import sys
import pdb

from pathlib import Path

#print(*sys.path, sep="\n", end="\n\n")

sys.path.insert(0,
                str(Path(__file__).resolve().parent.parent))

#print(*sys.path, sep="\n")

import solarwindpy
#pdb.set_trace()

print("done context file")

