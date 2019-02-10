#!/usr/bin/env python
r"""
Name   : plotting
Author : B. L. Alterman
e-mail : balterma@umich.edu
alias  : pp

Description
-----------
-Tools for plotting

Propodes Updates
----------------
-

Do Not Try
----------
-

Notes
-----
-

"""

import pdb
import logging
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from datetime import datetime
from pathlib import Path

from . import labels, histograms, tools

subplots = tools.subplots

subplots = tools.subplots
save     = tools.save