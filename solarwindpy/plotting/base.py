#!/usr/bin/env python
r"""Contains plotting :py:class:`Base` class.
"""

import pdb  # noqa: F401
import logging

from pathlib import Path
from collections import namedtuple
from abc import ABC, abstractmethod

LogAxes = namedtuple("LogAxes", "x,y", defaults=(False,))
AxesLabels = namedtuple("AxesLabels", "x,y,z", defaults=(None,))


class Base(ABC):
    r"""ABC for core plot tools.

    Properties
    ----------

    Methods
    -------

    Abstract Properites
    -------------------

    Abstract Methods
    ----------------

    """

    @abstractmethod
    def __init__(self):
        self._init_logger()

    def __str__(self):
        return self.__class__.__name__

    @property
    def logger(self):
        return self._logger

    def _init_logger(self):
        logger = logging.getLogger("{}.{}".format(__name__, self.__class__.__name__))
        self._logger = logger

    @property
    def data(self):
        return self._data

    @property
    def clip(self):
        return self._clip

    @property
    def log(self):
        return self._log

    @property
    def labels(self):
        return self._labels

    @property
    def path(self):
        r"""Path for saving figure.
        """
        return self._path

    def set_log(self, x=None, y=None):
        if x is None:
            x = self.log.x
        if y is None:
            y = self.log.y
        log = LogAxes(x, y)
        self._log = log

    def set_labels(self, **kwargs):
        r"""Set or update x, y, or z labels. Any label not specified in kwargs
        is propagated from `self.labels.<x, y, or z>`.
        """

        x = kwargs.pop("x", self.labels.x)
        y = kwargs.pop("y", self.labels.y)
        z = kwargs.pop("z", self.labels.z)

        if len(kwargs.keys()):
            extra = "\n".join(["{}: {}".format(k, v) for k, v in kwargs.items()])
            raise KeyError("Unexpected kwarg\n{}".format(extra))

        self._labels = AxesLabels(x, y, z)

    @abstractmethod
    def set_path(self, new, add_scale=False):
        r"""Build the plot save path.

        Parameters
        ----------
        new: str or Path
            If str and == "auto", then build path from `self.labels`. Otherwise,
            assume parameter specifies the desired path and use `Path(new)`.
        add_scale: bool
            If True, add information about the axis scales to the end of the path.
        """
        # TODO: move "auto" methods here to iterate through `AxesLabels` named tuple
        #       and pull the strings for creating the path. Also check for each
        #       label's scale and add that information.

        if new == "auto":
            try:
                x = self.labels.x.path
            except AttributeError:
                x = self.labels.x
                if not (isinstance(x, str) and x != "None"):
                    x = "x"
                elif isinstance(x, str):
                    x = x.replace(" ", "-")

            try:
                y = self.labels.y.path
            except AttributeError:
                y = self.labels.y
                if not (isinstance(y, str) and y != "None"):
                    y = "y"
                elif isinstance(y, str):
                    y = y.replace(" ", "-")

            try:
                z = self.labels.z.path
            except AttributeError:
                z = self.labels.z
                if not (isinstance(z, str) and z != "None"):
                    z = "z"
                elif isinstance(z, str):
                    z = z.replace(" ", "-")

            path = Path(self.__class__.__name__)

        elif new is None:
            path = Path("")
            x = y = z = None

        else:
            path = Path(new)
            x = y = z = None

        scale_info = None
        if add_scale:
            xscale = "logX" if self.log.x else "linX"
            yscale = "logY" if self.log.y else "linY"
            scale_info = [xscale, yscale]

        return path, x, y, z, scale_info

    @abstractmethod
    def set_data(self):
        pass

    @abstractmethod
    def _format_axis(self, ax):
        pass

    @abstractmethod
    def make_plot(self):
        pass
