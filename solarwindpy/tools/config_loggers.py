#!/usr/bin/env python
r"""Configure :py:mod:`solarwindpy` loggers.
"""

import pdb  # noqa: F401
import logging
import logging.config
import yaml

from pathlib import Path


def config_loggers(prefix, main, config_source="auto"):
    r"""Specify `FileHandler` `filename`s for :py:mod:`solarwindpy` loggers and
    configure the loggers.

    Parameters
    ----------
    prefix: str or Path
        The path prefix for the `FileHandler` instances.
    main: str or Path
        The name of the main file running `solarwindpy`. For example, the name of the
        ipython notebook used.
    config_source: str or Path
        If "auto", use the `logging.yaml` file adjascent to this module. Otherwise, can
        specify a path to the config file. Should be in `yaml` format.
    """

    if config_source == "auto":
        config_source = Path(__file__).parent / "logging.yaml"
    else:
        config_source = Path(config_source)

    with open(config_source, "rt") as f:
        config = yaml.safe_load(f.read())

    path_prefix = Path(prefix) / main / "logs"
    # Want to check dict location and need to specify file names.
    for k, v in config["handlers"].items():
        # The following should add the path prefix to each filename and reconfigure the
        # names to have the `path_prefix`.
        if v["class"] == "logging.FileHandler":
            fname = path_prefix / v["filename"]
            fname = fname.with_suffix(".log").resolve()

            if not fname.parent.exists():
                fname.parent.mkdir(parents=True, exist_ok=True)
            fname.touch(exist_ok=True)

            v["filename"] = fname

    logging.config.dictConfig(config)
    logging.getLogger("main").info("Loggers configured")
