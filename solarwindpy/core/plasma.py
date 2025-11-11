#!/usr/bin/env python
"""The Plasma class that contains all Ions, magnetic field, and spacecraft information.

Propoded Updates
^^^^^^^^^^^^^^^^
-It would be cute if one could call `plasma % a`, i.e. plasma mod
 an ion and return a new plasma without that ion in it. Well, either
 mod or subtract. Subtract and add probably make more sense. (20180129)

-See (https://drive.google.com/drive/folders/0ByIrJAE4KMTtaGhRcXkxNHhmY2M)
 for the various methods that might be worth considering including __getattr__
 vs __getattribute__, __hash__, __deepcopy__, __copy__, etc. (20180129)

-Convert `Plasma.__call__` to `Plasma.__getitem__` and `Plasma.__iter__` to
 to allow iterating over ions. (20180316)
 N.B. This could have complicated results as to how we actually access the
 underlying data and objects stored in the DataFrame.

-Define `__format__` methods for use with `str.format`. (20180316)

-Define `Plasma.__len__` to return the number of ions in the plasma. (20180316)

-Split each class into its own file. Suggested by EM. (BLA 20180217)

-Add `Plasma.dropna(*args, **kwargs)` that passes everything to `plasma.data.dropna`
 and then calls `self.__Plasma__set_ions()` to update the ions after drop. (20180404)

-Moved `_conform_species` to base.Base so that it is accessable for
 alfvenic_turbulence.py. Did not move tests out of `test_plasma.py`.  (20181121)
"""
import numpy as np
import pandas as pd
import itertools

# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.

from . import base
from . import vector
from . import ions
from . import spacecraft
from . import alfvenic_turbulence as alf_turb


class Plasma(base.Base):
    r"""Container for multi-species plasma physics data and analysis.

    The Plasma class serves as the central container for solar wind plasma
    analysis, combining ion moment data, magnetic field measurements, and
    spacecraft trajectory information for comprehensive plasma physics calculations.

    This class enables analysis of multi-species plasma including protons,
    alpha particles, and heavier ions. It provides convenient access to ion
    species through attribute shortcuts and supports advanced plasma physics
    calculations such as plasma beta, Coulomb collision frequencies, and
    thermal parameters.

    Attribute access is first attempted on the underlying :py:attr:`ions` table
    before falling back to ``super().__getattr__``. This allows convenient
    shorthand such as ``plasma.a`` to access the alpha particle :class:`Ion`
    and ``plasma.p1`` for protons.

    Attributes
    ----------
    data : pandas.DataFrame
        Multi-indexed DataFrame containing plasma measurements with columns
        labeled by ("M", "C", "S") for measurement, component, and species.
    ions : pandas.Series of Ion objects
        Dictionary-like access to individual ion species objects.
    species : list of str
        Available ion species identifiers in the plasma.
    spacecraft : Spacecraft, optional
        Spacecraft trajectory and velocity information.
    auxiliary_data : pandas.DataFrame, optional
        Additional measurements such as quality flags or derived parameters.

    Notes
    -----
    Thermal speeds assume the relationship :math:`mw^2 = 2kT` where :math:`m`
    is ion mass, :math:`w` is thermal speed, :math:`k` is Boltzmann's constant,
    and :math:`T` is temperature.

    The underlying data structure uses a three-level MultiIndex for columns:
    - Level 0 (M): Measurement type ('n', 'v', 'w', 'b', etc.)
    - Level 1 (C): Component ('x', 'y', 'z', 'par', 'per', etc.)
    - Level 2 (S): Species identifier ('p1', 'a', 'o6', etc.)

    Examples
    --------
    Create a plasma object from multi-species data:

    >>> import pandas as pd
    >>> import numpy as np
    >>> # Create sample MultiIndex data
    >>> epoch = pd.date_range('2023-01-01', periods=3, freq='1min')
    >>> columns = pd.MultiIndex.from_tuples([
    ...     ('n', '', 'p1'), ('v', 'x', 'p1'), ('v', 'y', 'p1'), ('v', 'z', 'p1'),
    ...     ('n', '', 'a'), ('v', 'x', 'a'), ('v', 'y', 'a'), ('v', 'z', 'a'),
    ...     ('w', 'par', 'p1'), ('w', 'per', 'p1'), ('w', 'par', 'a'), ('w', 'per', 'a'),
    ...     ('b', 'x', ''), ('b', 'y', ''), ('b', 'z', '')
    ... ], names=['M', 'C', 'S'])
    >>> data = pd.DataFrame(np.random.rand(3, len(columns)),
    ...                     index=epoch, columns=columns)
    >>> plasma = Plasma(data, 'p1', 'a')  # Protons and alphas
    >>> type(plasma.p1).__name__  # Proton ion object
    'Ion'

    Calculate plasma physics parameters:

    >>> beta = plasma.beta('p1')          # Plasma beta for protons  # doctest: +SKIP
    >>> type(beta).__name__  # doctest: +SKIP
    'Tensor'

    Idenfity ion species in plasma:

    >>> plasma.species  # doctest: +SKIP
    ['p1', 'a']
    """

    def __init__(
        self,
        data,
        *species,
        spacecraft=None,
        auxiliary_data=None,
        log_plasma_stats=False,
    ):
        r"""Initialize a :class:`Plasma` instance.

        Parameters
        ----------
        data : :class:`pandas.DataFrame`
            Contains the magnetic field and core ion moments. Columns are a
            three-level :class:`~pandas.MultiIndex` labelled ``("M", "C", "S")``
            for measurement, component, and species. The index should contain
            datetime information, for example ``Epoch`` when loading from a CDF
            file.
        *species : str
            Iterable of species contained in ``data``.
        spacecraft : :class:`~solarwindpy.core.spacecraft.Spacecraft`, optional
            Spacecraft trajectory and velocity information. If ``None``, the
            Coulomb number :py:meth:`~Plasma.nc` method will raise a
            :class:`ValueError`.
        auxiliary_data : :class:`pandas.DataFrame`, optional
            Additional measurements to carry with the plasma, for example data
            quality flags. The column labelling scheme must match ``data``.
        log_plasma_stats : bool, default ``False``
            Log summary statistics when ``data`` is set.

        Notes
        -----
        Thermal speeds assume :math:`mw^2 = 2kT`.

        Examples
        --------
        >>> epoch = pd.Series({0: pd.to_datetime("1995-01-01"),
        ...                    1: pd.to_datetime("2015-03-23"),
        ...                    2: pd.to_datetime("2022-10-09")}, name="Epoch")
        >>> data = {
        ... ("b", "x", ""): {0: 0.5, 1: 0.6, 2: 0.7},
        ... ("b", "y", ""): {0: -0.25, 1: -0.26, 2: 0.27},
        ... ("b", "z", ""): {0: 0.3, 1: 0.4, 2: -0.7},
        ... ("n", "", "a"): {0: 0.5, 1: 1.0, 2: 1.5},
        ... ("n", "", "p1"): {0: 1.0, 1: 2.0, 2: 3.0},
        ... ("v", "x", "a"): {0: 125.0, 1: 250.0, 2: 375.0},
        ... ("v", "x", "p1"): {0: 100.0, 1: 200.0, 2: 300.0},
        ... ("v", "y", "a"): {0: 250.0, 1: 375.0, 2: 750.0},
        ... ("v", "y", "p1"): {0: 200.0, 1: 300.0, 2: 600.0},
        ... ("v", "z", "a"): {0: 500.0, 1: 750.0, 2: 1000.0},
        ... ("v", "z", "p1"): {0: 400.0, 1: 600.0, 2: 800.0},
        ... ("w", "par", "a"): {0: 3.0, 1: 4.0, 2: 5.0},
        ... ("w", "par", "p1"): {0: 10.0, 1: 20.0, 2: 30.0},
        ... ("w", "per", "a"): {0: 7.0, 1: 9.0, 2: 10.0},
        ... ("w", "per", "p1"): {0: 7.0, 1: 26.0, 2: 28.0},
        ... }
        >>> data = pd.DataFrame.from_dict(data, orient="columns")
        >>> data.columns.names = ["M", "C", "S"]
        >>> data.index = epoch
        >>> data.T  # doctest: +NORMALIZE_WHITESPACE
        Epoch     1995-01-01  2015-03-23  2022-10-09
        M C   S
        b x             0.50        0.60        0.70
          y            -0.25       -0.26        0.27
          z             0.30        0.40       -0.70
        n     a         0.50        1.00        1.50
              p1        1.00        2.00        3.00
        v x   a       125.00      250.00      375.00
              p1      100.00      200.00      300.00
          y   a       250.00      375.00      750.00
              p1      200.00      300.00      600.00
          z   a       500.00      750.00     1000.00
              p1      400.00      600.00      800.00
        w par a         3.00        4.00        5.00
              p1       10.00       20.00       30.00
          per a         7.00        9.00       10.00
              p1        7.00       26.00       28.00
        >>> plasma = Plasma(data, "a", "p1")
        """
        self._init_logger()
        self._set_species(*species)
        self.set_log_plasma_stats(log_plasma_stats)
        super(Plasma, self).__init__(data)
        self._set_ions()
        self.set_spacecraft(spacecraft)
        self.set_auxiliary_data(auxiliary_data)

    def __getattr__(self, attr):
        if attr in self.ions.index:
            return self.ions.loc[attr]
        else:
            return super(Plasma, self).__getattr__(attr)

    @property
    def epoch(self):
        """Time index of the plasma data.

        Returns
        -------
        pandas.DatetimeIndex
            Datetime index containing measurement timestamps.

        Examples
        --------
        >>> plasma.epoch  # doctest: +SKIP
        DatetimeIndex(['1995-01-01', '2015-03-23', '2022-10-09'],
                      dtype='datetime64[ns]', name='Epoch', freq=None)
        """
        return self.data.index

    @property
    def spacecraft(self):
        r"""`Spacecraft` object stored in `plasma`."""
        return self._spacecraft

    @property
    def sc(self):
        r"""Shortcut to :py:attr:`spacecraft`."""
        return self.spacecraft

    @property
    def auxiliary_data(self):
        r"""Any data that does not fall into the following categories.

        Epoch is index.

            -magnetic field
            -ion velocity
            -ion number density
            -ion thermal speed
        """
        #         try:
        return self._auxiliary_data

    #         except AttributeError:
    #             raise AttributeError("No auxiliary data set.")

    @property
    def aux(self):
        r"""Shortcut to :py:attr:`auxiliary_data`."""
        return self.auxiliary_data

    @property
    def log_plasma_at_init(self):
        """Flag indicating whether to log plasma statistics during initialization.

        Returns
        -------
        bool
            True if plasma statistics should be logged at initialization.

        See Also
        --------
        set_log_plasma_stats : Method to modify this setting
        """
        return self._log_plasma_at_init

    def set_log_plasma_stats(self, new):
        """Set flag for logging plasma statistics during initialization.

        Parameters
        ----------
        new : bool
            Whether to enable logging of plasma statistics.

        Notes
        -----
        When enabled, summary statistics including density ranges, velocity
        distributions, and magnetic field statistics are logged during
        plasma initialization.

        Examples
        --------
        >>> plasma.set_log_plasma_stats(True)  # doctest: +SKIP
        >>> plasma.log_plasma_at_init  # doctest: +SKIP
        True
        """
        self._log_plasma_at_init = bool(new)

    def save(
        self,
        fname,
        dkey="FC",
        sckey="SC",
        akey="FC_AUX",
        data_modifier_fcn=None,
        sc_modifier_fcn=None,
        aux_modifier_fcn=None,
    ):
        r"""Save the plasma's data and aux DataFrame to an HDF5 file at `fname`.

        Parameters
        ----------
        fname: str or `pathlib.Path`.
            File name pointing to the save location.
            The typical use when creating a data file in `Create_Datafile.ipynb`
            is `fname("swe", "h5", strip_date=True)`.
        dkey: None
            The HDF5 file key at which to store the data.
        sckey: None
            The HDF5 file key at which to store the spacecraft data.
        akey: None
            The HDF5 file key at which to store the auxiliary_data.
        data_modifier_fcn: None, FunctionType
            A function to modify the data saved, e.g. if you don't want to save
            a specific species in the data file, you can pass.

                def modify_data(data):
                    return data.drop("a", axis=1, level="S")

            It can only take one argument, `data`.
        spacecraft_modifier_fcn: None, FunctionType
            A function to modifie the spacecraft data saved. See `data_modifier_fcn`
            for syntax.
        aux_modifier_fcn: None, FunctionType
            A function to modify the auxiliary_data saved. See
            `data_modifier_fcn` for syntax.
        """
        from types import FunctionType

        fname = str(fname)
        data = self.data
        sc = self.sc
        aux = self.aux

        if data_modifier_fcn is not None:
            if not isinstance(data_modifier_fcn, FunctionType):
                msg = (
                    "`modifier_fcn` must be a FunctionType. " "You passes '%s`."
                ) % type(data_modifier_fcn)
                raise TypeError(msg)
            data = data_modifier_fcn(data)

        # Recalculate "w_scalar" on load, so no need to save.
        data.drop("scalar", axis=1, level="C").to_hdf(fname, key=dkey)
        self.logger.info(
            "data saved\n{:<5}  %s\n{:<5}  %s\n{:<5}  %s".format(
                "file", "dkey", "shape"
            ),
            fname,
            dkey,
            data.shape,
        )

        msg = "`modifier_fcn` must be a FunctionType. " "You passes '%s`."
        if sc is not None:
            sc = sc.data
            if sc_modifier_fcn is not None:
                if not isinstance(sc_modifier_fcn, FunctionType):
                    raise TypeError(msg % type(sc_modifier_fcn))
                sc = sc_modifier_fcn(sc)

            sc.to_hdf(fname, key=sckey)
            self.logger.info(
                "spacecraft saved\n{:<5}  %s\n{:<5}  %s\n{:<5}  %s".format(
                    "file", "sckey", "shape"
                ),
                fname,
                sckey,
                sc.shape,
            )
        else:
            self.logger.info("No spacecraft data to save")

        if aux is not None:
            if aux_modifier_fcn is not None:
                if not isinstance(aux_modifier_fcn, FunctionType):
                    raise TypeError(msg % type(aux_modifier_fcn))
                aux = aux_modifier_fcn(aux)

            aux.to_hdf(fname, key=akey)
            self.logger.info(
                "aux saved\n{:<5}  %s\n{:<5}  %s\n{:<5}  %s".format(
                    "file", "akey", "shape"
                ),
                fname,
                akey,
                aux.shape,
            )
        else:
            self.logger.info("No auxiliary data to save")

    @classmethod
    def load_from_file(
        cls,
        fname,
        *species,
        dkey="FC",
        sckey="SC",
        akey="FC_AUX",
        sc_frame=None,
        sc_name=None,
        start=None,
        stop=None,
        **kwargs,
    ):
        r"""Load data from an HDF5 file at `fname` and create a plasma.

        Parameters
        ----------
        fname: str or pathlib.Path
            The file from which to load the data.
        species: list-like of str
            The species to load. If none are passed, they are automatically
            selected from the data.
        dkey: str, "FC"
            The key for getting data from HDF5 file.
        sckey: str, "SC"
            The key for getting spacecraft data from the HDF5 file.
        akey: str, "FC_AUX"
            key for getting auxiliary data from HDF5 file.
        start, stop: None, parsable by `pd.to_datetime`
            If not None, time to start/stop for loading data.
        kwargs:
            Passed to `Plasma.__init__`.
        """

        data = pd.read_hdf(fname, key=dkey)
        data.columns.names = ["M", "C", "S"]

        if start is not None or stop is not None:
            data = data.loc[start:stop]

        if not species:
            species = [s for s in data.columns.get_level_values("S").unique() if s]
        s_chk = [isinstance(s, str) for s in species]
        if not np.all(s_chk):
            msg = "Only string species allowed. Default or passed species: {}.".format(
                s_chk
            )
            raise ValueError(msg)

        log_at_init = kwargs.pop("log_plasma_stats", False)
        plasma = cls(data, *species, log_plasma_stats=log_at_init, **kwargs)

        plasma.logger.warning(
            "Loaded plasma from file\nFile:  %s\n\ndkey  :  %s\nshape : %s\nstart : %s\nstop  : %s",
            str(fname),
            dkey,
            data.shape,
            data.index.min(),
            data.index.max(),
        )

        if sckey:
            sc = pd.read_hdf(fname, key=sckey)
            sc.columns.names = ("M", "C")

            if (sc_name is None) or (sc_frame is None):
                raise ValueError(
                    "Must specify spacecraft name and frame\nname : %s\nframe: %s"
                    % (sc_name, sc_frame)
                )

            if start is not None or stop is not None:
                sc = sc.loc[data.index]

            sc = spacecraft.Spacecraft(sc, sc_name, sc_frame)

            plasma.set_spacecraft(sc)
            plasma.logger.warning(
                "Spacecraft data loaded\nsc_key: %s\nshape: %s", sckey, sc.data.shape
            )

        if akey:
            aux = pd.read_hdf(fname, key=akey)
            aux.columns.names = ("M", "C", "S")

            if start is not None or stop is not None:
                aux = aux.loc[data.index]

            plasma.set_auxiliary_data(aux)
            plasma.logger.warning(
                "Auxiliary data loaded from file\nakey: %s\nshape: %s", akey, aux.shape
            )

        return plasma

    def _set_species(self, *species):
        r"""Initialize `species` property to make overriding `set_data` easier.

        Initialize `species` property to make overriding `set_data`
        easier.
        """
        species = self._clean_species_for_setting(*species)
        self._species = species
        self.logger.debug("%s init with species %s", self.__class__.__name__, (species))

    def _chk_species(self, *species):
        r"""Internal tool to verify species string formats and availability.

        Check the species in each :py:class:`Plasma` method call and ensure
        they are available in the :py:attr:`ions`."""
        species = self._conform_species(*species)
        minimal_species = [s.split("+") for s in species]
        minimal_species = np.unique([*itertools.chain(minimal_species)])
        minimal_species = pd.Index(minimal_species)

        #        print("",
        #              "<_chk_species>",
        #              "<conformed>: {}".format(species),
        #              "<minimal>: {}".format(minimal_species),
        #              "<available>: {}".format(self.ions.index),
        #              sep="\n",
        #              end="\n\n")

        unavailable = minimal_species.difference(self.ions.index)

        if unavailable.any():
            requested = ", ".join(sorted(species))
            available = ", ".join(sorted(self.ions.index.values))
            unavailable = ", ".join(unavailable.values)
            msg = (
                "Requested species unavailable.\n"
                "Requested: %s\n"
                "Available: %s\n"
                "Unavailable: %s"
            )
            # print(msg % (requested, available, unavailable), flush=True, end="\n")
            raise ValueError(msg % (requested, available, unavailable))
        return species

    @property
    def species(self):
        r"""Tuple of species contained in plasma."""
        return self._species

    @property
    def ions(self):
        r"""`pd.Series` containing the ions."""
        return self._ions

    def _set_ions(self):
        species = self.species
        if len(species) == 1:
            species = species[0].split(",")
        assert np.all(
            ["+" not in s for s in species]
        ), "Plasma.species can't contain '+'."
        species = tuple(species)

        ions_ = pd.Series({s: ions.Ion(self.data, s) for s in species})
        self._ions = ions_
        self._species = species

    def drop_species(self, *species: str) -> "Plasma":
        """Return a new :class:`Plasma` without the specified species.

        Parameters
        ----------
        *species : str
            Species to remove from the plasma.

        Returns
        -------
        Plasma
            A new plasma containing only the remaining species.

        Raises
        ------
        ValueError
            If all species are removed.
        """

        species_to_drop = self._chk_species(*species)
        remaining = [s for s in self.species if s not in species_to_drop]
        if not remaining:
            raise ValueError("Must have >1 species. Can't have empty plasma.")

        mask_keep = (
            self.data.columns.get_level_values("S") == ""
        ) | self.data.columns.get_level_values("S").isin(remaining)
        data = self.data.loc[:, mask_keep]

        aux = None
        if self.auxiliary_data is not None:
            aux_mask = (
                self.auxiliary_data.columns.get_level_values("S") == ""
            ) | self.auxiliary_data.columns.get_level_values("S").isin(remaining)
            aux = self.auxiliary_data.loc[:, aux_mask]

        new = Plasma(
            data,
            *remaining,
            spacecraft=self.spacecraft,
            auxiliary_data=aux,
            log_plasma_stats=self.log_plasma_at_init,
        )
        return new

    def set_spacecraft(self, new):
        """Set or update the spacecraft trajectory data.

        Parameters
        ----------
        new : Spacecraft or None
            Spacecraft trajectory object containing position and velocity data.
            Must have matching datetime index with plasma data.

        Raises
        ------
        AssertionError
            If spacecraft index does not match plasma data index.

        Notes
        -----
        The spacecraft data is required for calculating certain plasma physics
        parameters such as Coulomb collision frequencies that depend on the
        plasma frame transformation.

        Examples
        --------
        >>> sc = Spacecraft(trajectory_data)  # doctest: +SKIP
        >>> plasma.set_spacecraft(sc)  # doctest: +SKIP
        >>> plasma.spacecraft.position  # Access trajectory data  # doctest: +SKIP
        """
        assert isinstance(new, spacecraft.Spacecraft) or new is None

        if new is not None:
            assert isinstance(new.data.index, pd.DatetimeIndex)
            assert new.data.index.equals(self.data.index)
            assert new.data.columns.names == ("M", "C")
            # Don't test spacecraft data duplicating plasma data b/c labels will
            # overlap even though they represent different quantities because
            # spacecraft only has a 2-level MultiIndex.

        self._log_object_at_load(new.data if new is not None else new, "spacecraft")
        self._spacecraft = new

    def set_auxiliary_data(self, new):
        """Set or update auxiliary measurement data.

        Parameters
        ----------
        new : pandas.DataFrame or None
            Additional measurements such as data quality flags, derived
            parameters, or instrument-specific metadata. Must have matching
            datetime index with plasma data.

        Raises
        ------
        AssertionError
            If auxiliary data index does not match plasma data index.

        Notes
        -----
        Auxiliary data provides additional context for plasma measurements
        without being part of the core plasma physics calculations. Common
        examples include quality flags, statistical uncertainties, or
        instrument operational parameters.

        Examples
        --------
        >>> quality_flags = pd.DataFrame({'quality': [0, 1, 0]},  # doctest: +SKIP
        ...                              index=plasma.epoch)
        >>> plasma.set_auxiliary_data(quality_flags)  # doctest: +SKIP
        >>> plasma.aux.quality  # Access auxiliary data  # doctest: +SKIP
        """
        assert isinstance(new, pd.DataFrame) or new is None

        if new is not None:
            assert isinstance(new.index, pd.DatetimeIndex)
            assert new.index.equals(self.data.index)
            assert new.columns.names == ("M", "C", "S")
            if new.columns.isin(self.data.columns).any():
                raise ValueError("Auxiliary data should not duplicate plasma data")

        self._log_object_at_load(new, "auxiliary_data")
        self._auxiliary_data = new

    def _log_object_at_load(self, data, name):

        if data is None:
            self.logger.info("No %s data passed to %s", name, self.__class__.__name__)
            return None

        elif self.log_plasma_at_init:

            nan_frame = data.isna()
            nan_info = pd.DataFrame(
                {"count": nan_frame.sum(axis=0), "mean": nan_frame.mean(axis=0)}
            )
            # Log to DEBUG if no NaNs. Otherwise log to INFO.
            if nan_info.any().any():
                self.logger.info(
                    "%s %.0f spectra contain at least one NaN",
                    name,
                    nan_info.any(axis=1).sum(),
                )
                #             self.logger.log(10 * int(1 + nan_info.any().any()),
                #                             "plasma NaN info\n%s", nan_info.to_string())
                self.logger.debug("%s NaN info\n%s", name, nan_info.to_string())
            else:
                self.logger.debug("%s does not contain NaNs", name)

            pct = [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]
            stats = (
                pd.concat(
                    {
                        "lin": data.describe(percentiles=pct),
                        "log": data.applymap(np.log10).describe(percentiles=pct),
                    },
                    axis=0,
                )
                .unstack(level=0)
                .sort_index(axis=0)
                .sort_index(axis=1)
                .T
            )
            self.logger.debug(
                "%s stats\n%s\n%s",
                name,
                stats.loc[:, ["count", "mean", "std"]].to_string(),
                stats.drop(["count", "mean", "std"], axis=1).to_string(),
            )

    def set_data(self, new):
        r"""Set the data and log statistics about it."""
        #         assert isinstance(new, pd.DataFrame)
        super(Plasma, self).set_data(new)

        new = new.reorder_levels(["M", "C", "S"], axis=1).sort_index(axis=1)
        # new = new.sort_index(axis=1, inplace=True)
        assert new.columns.names == ["M", "C", "S"]

        #         assert isinstance(new.index, pd.DatetimeIndex)
        #         if not new.index.is_monotonic:
        #             self.logger.warning(
        #                 r"""A non-monotonic DatetimeIndex typically indicates the presence of bad data. This will impact perfomance and prevent some DatetimeIndex-dependent functionality from working."""
        #             )

        # These are the only quantities we want in plasma.
        # TODO: move `theta_rms`, `mag_rms` and anything not common to
        #       multiple spacecraft to `auxiliary_data`. (20190216)
        tk_plasma = pd.IndexSlice[
            ["b", "n", "v", "w"],
            ["", "x", "y", "z", "per", "par"],
            list(self.species) + [""],
        ]

        data = new.loc[:, tk_plasma].sort_index(axis=1)
        dropped = new.drop(data.columns, axis=1)
        data = data.loc[:, ~data.columns.duplicated()]

        coeff = pd.Series({"per": 2.0, "par": 1.0}) / 3.0

        w = (
            data.loc[:, pd.IndexSlice["w", ["par", "per"]]]
            .pow(2)
            .multiply(coeff, axis=1, level="C")
        )

        #         w = (
        #         data.w.drop("scalar", axis=1, level="C")
        #         .pow(2)
        #         .multiply(coeff, axis=1, level="C")
        #         )

        # TODO: test `skipna=False` to ensure we don't accidentially create valid data
        #       where there is none. Actually, not possible as we are combining along
        #       "S".

        # Workaround for `skipna=False` bug. (20200814)
        # w = w.sum(axis=1, level="S", skipna=False).applymap(np.sqrt)
        # Changed to new groupby method (20250611)
        w = w.T.groupby("S").sum().T.pow(0.5)
        #         w_is_finite = w.notna().all(axis=1, level="S")
        #         w = w.sum(axis=1, level="S").applymap(np.sqrt)
        #         w = w.where(w_is_finite, axis=1, level="S")

        # TODO: can probably just `w.columns.map(lambda x: ("w", "scalar", x))`
        w.columns = w.columns.to_series().apply(lambda x: ("w", "scalar", x))
        w.columns = self.mi_tuples(w.columns)

        #         data = pd.concat([data, w], axis=1, sort=True)
        data = pd.concat([data, w], axis=1, sort=False).sort_index(
            axis=1
        )  # .sort_idex(axis=0)

        data.columns = self.mi_tuples(data.columns)
        data = data.sort_index(axis=1)

        self._data = data
        self.logger.debug(
            "plasma shape: %s\nstart: %s\nstop: %s",
            data.shape,
            data.index.min(),
            data.index.max(),
        )
        if dropped.columns.values.any():
            self.logger.info(
                "columns dropped from plasma\n%s",
                [str(c) for c in dropped.columns.values],
            )
        else:
            self.logger.info("no columns dropped from plasma")

        self._bfield = vector.BField(data.b.xs("", axis=1, level="S"))

        self._log_object_at_load(data, "plasma")

    @property
    def bfield(self):
        r"""Magnetic field data."""
        return self._bfield

    @property
    def b(self):
        r"""Shortcut for :py:attr:`bfield`."""
        return self.bfield

    def number_density(self, *species, skipna=True):
        r"""Get the plasma number densities.

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". If this is the case, the species are summed over and
            a pd.Series is returned. Otherwise, the individual quantities are
            returned as a pd.DataFrame.
        skipna: bool, default True
            Follows `pd.DataFrame.sum` convention. If True, NA excluded from
            results. If False, NA propagates. False is helpful to identify
            when a species is not measured using NaNs in its number density.

        Returns
        -------
        n: pd.Series or pd.DataFrame
            See Parameters for more info.
        """
        slist = self._chk_species(*species)

        n = {s: self.ions.loc[s].n for s in slist}
        n = pd.concat(n, axis=1, names=["S"], sort=True)

        if len(species) == 1:
            n = n.sum(axis=1, skipna=skipna)
            n.name = species[0]

        return n

    def n(self, *species, skipna=True):
        r"""Shortcut to :py:meth:`number_density`."""
        return self.number_density(*species, skipna=skipna)

    def mass_density(self, *species):
        r"""Get the plasma mass densities.

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". If this is the case, the species are summed over and
            a pd.Series is returned. Otherwise, the individual quantities are
            returned as a pd.DataFrame.

        Returns
        -------
        rho: pd.Series or pd.DataFrame
            See Parameters for more info.
        """
        slist = self._chk_species(*species)

        rho = {s: self.ions.loc[s].rho for s in slist}
        rho = pd.concat(rho, axis=1, names=["S"], sort=True)

        if len(species) == 1:
            rho = rho.sum(axis=1)
            rho.name = species[0]
        return rho

    def rho(self, *species):
        r"""Shortcut to :py:meth:`mass_density`."""
        return self.mass_density(*species)

    def thermal_speed(self, *species):
        r"""Get the thermal speed.

        Parameters
        ----------
        species: str
            Each species is a string. A total species ("s0+s1+...") cannot be passed
            because the result is physically amibguous.

        Returns
        -------
        w: pd.Series or pd.DataFrame
            See Parameters for more info.
        """
        if np.any(["+" in s for s in species]):
            raise NotImplementedError(
                "The result of a total species thermal speed is physically ambiguous"
            )

        slist = self._chk_species(*species)
        w = {s: self.ions.loc[s].thermal_speed.data for s in slist}
        w = pd.concat(w, axis=1, names=["S"], sort=True)
        w = w.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)

        if len(species) == 1:
            # w = w.sum(axis=1, level="C")
            w = w.T.groupby(level="C").sum().T

        return w

    def w(self, *species):
        r"""Shortcut to :py:meth:`thermal_speed`."""
        return self.thermal_speed(*species)

    def pth(self, *species):
        r"""Get the thermal pressure.

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". If this is the case, the species are summed over and
            a pd.Series is returned. Otherwise, the individual quantities are
            returned as a pd.DataFrame.

        Returns
        -------
        pth: pd.Series or pd.DataFrame
            See Parameters for more info.
        """
        slist = self._chk_species(*species)
        include_dynamic = False
        if include_dynamic:
            raise NotImplementedError

        pth = {s: self.ions.loc[s].pth for s in slist}
        pth = pd.concat(pth, axis=1, names=["S"], sort=True)
        pth = pth.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)

        if len(species) == 1:
            pth = pth.T.groupby("C").sum().T
            # pth["S"] = species[0]
            # pth = pth.set_index("S", append=True).unstack()
            # pth = pth.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)
        return pth

    def temperature(self, *species):
        r"""Get the thermal temperature.

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". If this is the case, the species are summed over and
            a pd.Series is returned. Otherwise, the individual quantities are
            returned as a pd.DataFrame.

        Returns
        -------
        temp: pd.Series or pd.DataFrame
            See Parameters for more info.
        """
        slist = self._chk_species(*species)
        temp = {s: self.ions.loc[s].temperature for s in slist}
        temp = pd.concat(temp, axis=1, names=["S"], sort=True)
        temp = temp.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)

        if len(species) == 1:
            temp = temp.T.groupby("C").sum().T
            # temp["S"] = species[0]
            # temp = temp.set_index("S", append=True).unstack()
            # temp = temp.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)
        return temp

    def beta(self, *species):
        r"""Get perpendicular, parallel, and scalar plasma beta.

        Parameters
        ----------
        species: str
            Each species is a string. Species handling controlled by :py:meth:`pth`.

        Returns
        -------
        beta: :py:class:`pd.DataFrame`
            See Parameters for more info.

        Notes
        -----
        In uncertain units, the NRL Plasma Formulary (2016) defined
        :math:`\beta`:

            :math:`\beta = \frac{8 \pi n k_B T}{B^2} = \frac{2 k_b T / m}{B^2 / 4 \phi \rho}`

        and the Alfven speed as:

            :math:`C_A^2 = B^2 / 4 \pi \rho`.

        I define thermal speed as:

            :math:`w^2 = \frac{2 k_B T}{m}`.

        Combining these equations, we get:

            :math:`\beta = w^2 / C_A^2`,

        which is independent of dimensional constants. Given I define
        :math:`p_{th} = \frac{1}{2} \rho w^2` and :math:`C_A^2 = \frac{1}{\mu_0}B^2 \rho` in SI units, I can
        rewrite :math:`\beta`

            :math:`\beta = \frac{2 p_{th}}{\rho} \frac{\mu_0 \rho}{B^2} = \frac{2 \mu_0 p_{th}}{B^2}`.
        """
        slist = self._chk_species(*species)  # noqa: F841
        include_dynamic = False
        if include_dynamic:
            raise NotImplementedError

        pth = self.pth(*species)
        bsq = self.bfield.mag.pow(2)
        beta = pth.divide(bsq, axis=0)

        units = self.units.pth / (self.units.b**2.0)
        coeff = 2.0 * self.constants.misc.mu0 * units
        beta *= coeff
        return beta

    def anisotropy(self, *species):
        r"""Pressure anisotropy.

        Note that for a single species, the pressure anisotropy is just the
        temperature anisotropy.

        Parameters
        ----------
        species: str
            Each species is a string. Species handling is primarily controlled
            by :py:meth:`pth`.

        Returns
        -------
        ani: :py:class:`pd.Series` or :py:class:`pd.DataFrame`
            See Parameters for more info.
        """
        pth = self.pth(*species).drop("scalar", axis=1)

        include_dynamic = False
        if include_dynamic:
            raise NotImplementedError
            pdv = self.pdv(*species)
            pth.loc[:, "par"] = pth.loc[:, "par"].add(pdv, axis=0)

        exp = pd.Series({"par": -1, "per": 1})

        if len(species) > 1:
            # if "S" in pth.columns.names:
            #             ani = pth.pow(exp, axis=1, level="C").product(axis=1, level="S")
            ani = pth.pow(exp, axis=1, level="C").T.groupby(level="S").prod().T
        else:
            ani = pth.pow(exp, axis=1).product(axis=1)
            ani.name = species[0]

        return ani

    def velocity(self, *species, project_m2q=False):
        r"""Get an ion velocity or calculate the center-of-mass velocity.

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed and contains
            "+", return a pd.Series containing the center-of-mass velocity
            :py:class:`~solarwindpy.core.vector.Vector`. If contains a single species,
            return that ion's velocity.
        project_m2q: bool, False
            If True, project velocity by :math:`\sqrt{m/q}`. Disables center-of-
            mass species.

        Returns
        -------
        velocity: :py:class:`pd.Series` or :py:class:`pd.DataFrame`
        """
        stuple = self._chk_species(*species)

        # print("", "<Module>", sep="\n")

        if len(stuple) == 1:
            # print("<Module.ion>")
            s = stuple[0]
            v = self.ions.loc[s].velocity
            if project_m2q:
                m2q = np.sqrt(
                    self.constants.m_in_mp[s] / self.constants.charge_states[s]
                )
                v = v.data.multiply(m2q)
                v = vector.Vector(v)

        elif project_m2q:
            raise NotImplementedError(
                """A multi-species velocity is not valid when projecting by sqrt(m/q).
species: {}
""".format(
                    species
                )
            )

        else:
            # print("<Module.sum>")
            v = self.ions.loc[list(stuple)].apply(lambda x: x.velocity)
            if len(species) == 1:
                rhos = self.mass_density(*stuple)
                v = pd.concat(
                    v.apply(lambda x: x.cartesian).to_dict(),
                    axis=1,
                    names=["S"],
                    sort=True,
                )
                rv = (
                    v.multiply(rhos, axis=1, level="S").T.groupby(level="C").sum().T
                )  # sum(axis=1, level="C")
                v = rv.divide(rhos.sum(axis=1), axis=0)
                v = vector.Vector(v)

        return v

    def v(self, *species, project_m2q=False):
        r"""Shortcut to `velocity`."""
        return self.velocity(*species, project_m2q=project_m2q)

    def dv(self, s0, s1, project_m2q=False):
        r"""Calculate the differential flow between species `s0` and `s1`.

        Calculate the differential flow between species `s0` and
        species `s1`: :math:`v_{s0} - v_{s1}`.

        Parameters
        ----------
        s0, s1: str
            If either species contains a "+", the center-of-mass velocity
            for the indicated species is used.
        project_m2q: bool, False
            If True, project each speed by :math:`\sqrt{m/q}`. Disables center-
            of-mass species.

        Returns
        -------
        dv: vector.Vector

        See Also
        --------
        vector.Vector
        """
        if s0 == s1:
            msg = (
                "The differential flow between a species and itself "
                "is identically zero.\ns0: %s\ns1: %s"
            )
            raise NotImplementedError(msg % (s0, s1))

        v0 = self.velocity(s0, project_m2q=project_m2q).cartesian
        v1 = self.velocity(s1, project_m2q=project_m2q).cartesian

        dv = v0.subtract(v1)
        dv = vector.Vector(dv)

        return dv

    def pdynamic(self, *species, project_m2q=False):
        r"""Calculate the dynamic or drift pressure for the given species.

            :math:`p_{\tilde{v}} = 0.5 \sum_i \rho_i (v_i - v_\mathrm{com})^2`

        The calculation is done in the plasma frame.

        Parameters
        ----------
        species: list-like of str
            List-like of individual species, e.g. ["a", "p1"].
            Can NOT be a list-like including sums, e.g. ["a", "p1+p2"].
        project_m2q: bool, False
            If True, project the velocities by :math:`\sqrt{m/q}`. Allows for only
            two species to be passed and takes the differential flow between them.

        Returns
        -------
        pdv: pd.Series
            Dynamic pressure due to `species`.
        """
        stuple = self._chk_species(*species)
        if len(stuple) == 1:
            msg = "Must have >1 species to calculate dynamic pressure.\nRequested: {}"
            raise ValueError(msg.format(species))

        const = 0.5 * self.units.rho * (self.units.dv**2.0) / self.units.pth

        if not project_m2q:
            # Calculate as m*v
            scom = "+".join(species)
            rho_i = self.mass_density(*stuple)
            dv_i = pd.concat(
                {s: self.dv(s, scom).cartesian for s in stuple},
                axis=1,
                names="S",
                sort=True,
            )
            dvsq_i = dv_i.pow(2.0).T.groupby(level="S").sum().T
            dvsq_rho_i = dvsq_i.multiply(rho_i, axis=1, level="S")
            pdv = dvsq_rho_i.sum(axis=1)

        elif len(stuple) == 2:
            # Can only have 2 species with `project_m2q`.
            dvsq = (
                self.dv(*stuple, project_m2q=project_m2q).cartesian.pow(2).sum(axis=1)
            )
            rho_i = self.mass_density(*stuple)
            mu = rho_i.product(axis=1).divide(rho_i.sum(axis=1), axis=0)
            pdv = dvsq.multiply(mu, axis=0)

        pdv = pdv.multiply(const)
        pdv.name = "pdynamic"

        #        print("",
        #              "<Module>",
        #              "<stuple>: {}".format(stuple),
        #              "<scom> %s" % scom,
        #              "<const> %s" % const,
        #              "<rho_i>", type(rho_i), rho_i,
        #              "<dv_i>", type(dv_i), dv_i,
        #              "<dvsq_i>", type(dvsq_i), dvsq_i,
        #              "<dvsq_rho_i>", type(dvsq_rho_i), dvsq_rho_i,
        #              "<pdv>", type(pdv), pdv,
        #              sep="\n",
        #              end="\n\n")

        #        dvsq_rho_i = dvsq_i.multiply(rho_i, axis=1, level="S")
        #        pdv        = dvsq_rho_i.sum(axis=1).multiply(const)
        # pdv = const * dv_i.pow(2.0).sum(axis=1,
        #                                level="S").multiply(rhi_i,
        #                                                    axis=1,
        #                                                    level="S").sum(axis=1)
        #        pdv.name = "pdynamic"

        #        print(
        #              "<dvsq_rho_i>", type(dvsq_rho_i), dvsq_rho_i,
        #              "<pdv>", type(pdv), pdv,
        #              sep="\n",
        #              end="\n\n")

        return pdv

    def pdv(self, *species, project_m2q=False):
        r"""Shortcut to :py:meth:`pdynamic`."""
        return self.pdynamic(*species, project_m2q=project_m2q)

    def sound_speed(self, *species):
        r"""Calculate the sound speed.

        Parameters
        ----------
        species: str
            TODO: What controls species?

        Returns
        -------
        cs: pd.DataFrame or pd.Series depending on `species` inputs.
        """
        slist = self._chk_species(*species)
        rho = self.mass_density(*species) * self.units.rho
        pth = self.pth(*species) * self.units.pth

        pth = pth.loc[:, "scalar"]

        #         gamma = self.units_constants.misc.loc["gamma"]  # should be 5.0/3.0
        gamma = self.constants.polytropic_index["scalar"]  # should be 5/3
        cs = pth.divide(rho, axis=0).multiply(gamma).pow(0.5) / self.units.cs

        #         raise NotImplementedError(
        #             "How do we name this species? Need to figure out species processing up top."
        #         )
        if len(species) == 1:
            cs.name = species[0]
        else:
            assert cs.columns.isin(slist).all()

        return cs

    def cs(self, *species):
        r"""Shortcut to :py:meth:`sound_speed`."""
        return self.sound_speed(*species)

    def ca(self, *species):
        r"""Calculate the isotropic MHD Alfven speed.

        Parameters
        ----------
        species: str
            Species controlled by :py:meth:`mass_density`

        Returns
        -------
        ca: pd.DataFrame or pd.Series depending on `species` inputs.
        """
        stuple = self._chk_species(*species)  # noqa: F841

        rho = self.mass_density(*species)
        b = self.bfield.mag

        units = self.units
        mu0 = self.constants.misc.mu0
        coeff = units.b / (np.sqrt(units.rho * mu0) * units.ca)
        ca = rho.pow(-0.5).multiply(b, axis=0) * coeff

        if len(species) == 1:
            ca.name = species[0]

        # print_inline_debug_info = False
        # if print_inline_debug_info:
        #     print("",
        #             "<Module>",
        #             "<species>", stuple,
        #             "<b>", type(b), b,
        #             "<rho>", type(rho), rho,
        #             "<ca>", type(ca), ca,
        #             sep="\n")

        return ca

    def afsq(self, *species, pdynamic=False):
        r"""Calculate the square of anisotropy factor.

            :math:`AF^2 = 1 + \frac{\mu_0}{B^s}\left(p_\perp - p_\parallel - p_{\tilde{v}}\right)`

        N.B. Because of the :math:`1 +`, afsq(s0, s1).sum(axis=1) is not the
             same as afsq(s0+s1). The two are related by:

                afsq.(s0+s1) = 1 + (afsq(s0, s1) - 1).sum(axis=1)

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". If this is the case, the species are summed over and
            a pd.Series is returned. Otherwise, the individual quantities are
            returned as a pd.DataFrame.
        pydnamic: bool, str
            If str, the component of the dynamic pressure to use when
            calculating :math:`p_{\tilde{v}}`.

        Returns
        -------
        afsq: pd.Series or pd.DataFrame depending on the len(species).
        """
        if pdynamic:
            raise NotImplementedError(
                "Youngest beams analysis shows "
                "that dynamic pressure is probably not useful."
            )

        # The following is used to specifiy whether column levels
        # need to be aligned when multiple species are present.
        multi_species = len(species) > 1

        bsq = self.bfield.cartesian.pow(2.0).sum(axis=1)

        pth = self.pth(*species)
        pth = pth.drop("scalar", axis=1)

        sum_coeff = pd.Series({"per": 1, "par": -1})
        dp = pth.multiply(sum_coeff, axis=1, level="C" if multi_species else None)

        # The following level kwarg controls returning a DataFrame
        # of the various species or a single result for one species.
        # My guess is that following this line, we'd insert the subtraction
        # of the dynamic pressure with the appropriate alignment of the
        # species as necessary.
        #         dp = dp.sum(axis=1, level="S" if multi_species else None)
        if multi_species:
            dp = dp.T.groupby(level="S").sum().T
        else:
            dp = dp.sum(axis=1)

        mu0 = self.constants.misc.mu0
        coeff = mu0 * self.units.pth / (self.units.b**2.0)

        afsq = 1.0 + (dp.divide(bsq, axis=0) * coeff)

        if len(species) == 1:
            afsq.name = species[0]

        #        print(""
        #              "<Module>",
        #              "<species>: {}".format(species),
        #              "<bsq>", type(bsq), bsq,
        #              "<coeff>", type(coeff), coeff,
        #              "<pth>", type(pth), pth,
        #              "<dp>", type(dp), dp,
        #              "<afsq>", type(afsq), afsq,
        #              "",
        #              sep="\n")

        return afsq

    def caani(self, *species, pdynamic=False):
        r"""
        Calculate the anisotropic MHD Alfven speed:

            :math:`C_{A;Ani} = C_A\sqrt{AFSQ}`

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". In either case, all species are summed over and
            a pd.Series is returned. This addresses complications from the
            `stuple = self._chk_species(*species)` mass densities in Ca and AFSQ,
            the latter via :py:meth:`pth`.
        pydnamic: bool, str
            If str, the component of the dynamic pressure to use when
            calculating :math:`p_{\tilde{v}}`.

        Returns
        -------
        caani: pd.Series
            Only pd.Series is returned because of the combination of mass
            density and pressure terms in the CaAni equation.

        See Also
        --------
        ca, afsq
        """
        stuple = self._chk_species(*species)
        ssum = "+".join(stuple)

        ca = self.ca(ssum)
        afsq = self.afsq(ssum, pdynamic=pdynamic)
        caani = ca.multiply(afsq.pipe(np.sqrt))

        # print("",
        #       "<Module>",
        #       "<species>: {}".format(ssum),
        #       "<ca>", type(ca), ca,
        #       "<afsq>", type(afsq), afsq,
        #       "<caani>", type(caani), caani,
        #       "",
        #       sep="\n")

        return caani

    def lnlambda(self, s0, s1):
        r"""Calculate the Coulomb logarithm between species s0 and s1.

            :math:`\ln_\lambda_{i,i} = 29.9 - \ln(\frac{z_0 * z_1 * (a_0 + a_1)}{a_0 * T_1 + a_1 * T_0} \sqrt{\frac{n_0 z_0^2}{T_0} + \frac{n_1 z_1^2}{T_1}})`

        Parameters
        ----------
        species: str
            Each species is a string. It cannot be a sum of species,
            nor can it be an iterable of species.

        Returns
        -------
        lnlambda: pd.Series
            Only `pd.Series` is returned because Coulomb require
            species alignment in such a fashion that array
            operations using `pd.DataFrame` alignment won't work.

        See Also
        --------
        nuc
        """
        s0 = self._chk_species(s0)
        s1 = self._chk_species(s1)

        if len(s0) > 1 or len(s1) > 1:
            msg = (
                "`lnlambda` can only calculate with individual s0 and "
                "s1 species.\ns0: %s\ns1: %s"
            )
            raise ValueError(msg % (s0, s1))

        s0 = s0[0]
        s1 = s1[0]

        constants = self.constants
        units = self.units

        z0 = constants.charge_states.loc[s0]
        z1 = constants.charge_states.loc[s1]

        a0 = constants.m_amu.loc[s0]
        a1 = constants.m_amu.loc[s1]

        n0 = self.ions.loc[s0].n * units.n
        n1 = self.ions.loc[s1].n * units.n

        T0 = self.ions.loc[s0].temperature.scalar * units.temperature * constants.kb.eV
        T1 = self.ions.loc[s1].temperature.scalar * units.temperature * constants.kb.eV

        r0 = n0.multiply(z0**2.0).divide(T0, axis=0)
        r1 = n1.multiply(z1**2.0).divide(T1, axis=0)
        right = r0.add(r1).pipe(np.sqrt)

        left = z0 * z1 * (a0 + a1) / (a0 * T1).add(a1 * T0, axis=0)

        lnlambda = (29.9 - np.log(left * right)) / units.lnlambda
        lnlambda.name = "%s,%s" % (s0, s1)

        #        print("",
        #              "<Module>",
        #              "<ions>", type(self.ions), self.ions,
        #              "<s0, s1>: %s, %s" % (s0, s1),
        #              "<z0>", z0,
        #              "<z1>", z1,
        #              "<n0>", type(n0), n0,
        #              "<n1>", type(n1), n1,
        #              "<T0>", type(T0), T0,
        #              "<T1>", type(T1), T1,
        #              "<r0>", type(r0), r0,
        #              "<r1>", type(r1), r1,
        #              "<right>", type(right), right,
        #              "<left>", type(left), left,
        #              "<lnlambda>", type(lnlambda), lnlambda,
        #              "<Module Done>",
        #              "",
        #              sep="\n")

        return lnlambda

    def nuc(self, sa, sb, both_species=True):
        r"""Calculate the momentum collision rate following [1].

        Parameters
        ----------
        sa, sb: str
            The test, field particle species. Each can only identify a single
            ion species and it cannot be an iterable of lists, etc.
        both_species: bool
            If True, calculate the effective collision rate for a
            two-ion-species plasma following Eq. (23). Otherwise, calculate
            it following Eq. (18).

        Returns
        -------
        nu: pd.Series

        Notes
        -----
        If nu.name is "sa-sb", then `both_species=False` in calclulation.
        If nu.name is "sa+sb", then `both_species=True`.

        See Also
        --------
        lnlambda, nc

        References
        ----------
        [1] Hernández, R., & Marsch, E. (1985). Collisional time scales for
            temperature and velocity exchange between drifting Maxwellians.
            Journal of Geophysical Research, 90(A11), 11062.
            <https://doi.org/10.1029/JA090iA11p11062>.
        """
        from scipy.special import erf

        sa = self._chk_species(sa)
        sb = self._chk_species(sb)

        if len(sa) > 1 or len(sb) > 1:
            msg = (
                "`nuc` can only calculate with individual `sa` and "
                "`sb` species.\nsa: %s\nsb: %s"
            )
            raise ValueError(msg % (sa, sb))

        sa, sb = sa[0], sb[0]

        units = self.units
        constants = self.constants

        qabsq = constants.charges.loc[[sa, sb]].pow(2).product()
        ma = constants.m.loc[sa]
        masses = constants.m.loc[[sa, sb]]
        mu = masses.product() / masses.sum()
        coeff = qabsq / (4.0 * np.pi * constants.misc.e0**2.0 * ma * mu)

        lnlambda = self.lnlambda(sa, sb) * units.lnlambda
        nb = self.ions.loc[sb].n * units.n

        w = pd.concat(
            {s: self.ions.loc[s].w.data.par for s in [sa, sb]}, axis=1, sort=True
        )
        wab = w.pow(2.0).sum(axis=1).pipe(np.sqrt) * units.w

        dv = self.dv(sa, sb).magnitude * units.dv
        dvw = dv.divide(wab, axis=0)

        # longitudinal diffusion rate.
        ldr1 = erf(dvw)
        ldr2 = dvw.multiply((2.0 / np.sqrt(np.pi)) * np.exp(-1 * dvw.pow(2.0)), axis=0)
        ldr = dvw.pow(-3.0).multiply(ldr1.subtract(ldr2, axis=0), axis=0)

        nuab = coeff * nb.multiply(lnlambda, axis=0).multiply(ldr, axis=0).multiply(
            wab.pow(-3.0), axis=0
        )
        nuab /= units.nuc

        # print("",
        #       "<Module>",
        #       "<species>: {}".format((sa, sb)),
        #       "<ma>", type(ma), ma,
        #       "<masses>", type(masses), masses,
        #       "<mu>", type(mu), mu,
        #       "<qab^2>", type(qabsq), qabsq,
        #       "<qa^2 qb^2 / 4 pi e0^2 ma mu>", type(coeff), coeff,
        #       "<w>", type(w), w,
        #       "<wab>", type(wab), wab,
        #       "<lnlambda>", type(lnlambda), lnlambda,
        #       "<nb>", type(nb), nb,
        #       "<wab>", type(wab), wab,
        #       "<dv>", type(dv), dv,
        #       "<dv/wab>", type(dvw), dvw,
        #
        #       "<erf(dv/wab)>", type(ldr1), ldr1,
        #       "<(dv/wab) * 2/sqrt(pi) * exp(-(dv/wab)^2)>", type(ldr2), ldr2,
        #       "<transverse diffusion rate>", type(ldr), ldr,
        #       "<nuab>", type(nuab), nuab,
        #       sep="\n")

        if both_species:
            exp = pd.Series({sa: 1.0, sb: -1.0})
            rho_ratio = pd.concat(
                {s: self.mass_density(s) for s in [sa, sb]}, axis=1, sort=True
            )
            rho_ratio = rho_ratio.pow(exp, axis=1).product(axis=1)
            nuba = nuab.multiply(rho_ratio, axis=0)
            nu = nuab.add(nuba, axis=0)
            #             nu.name = "%s+%s" % (sa, sb)
            nu.name = f"{sa}+{sb}"
            # print(
            #       "<rho_a/rho_b>", type(rho_ratio), rho_ratio,
            #       "<nuba>", type(nuba), nuba,
            #       sep="\n")
        else:
            nu = nuab
            #             nu.name = "%s-%s" % (sa, sb)
            nu.name = f"{sa}-{sb}"

        # print(
        #       "<both_species> %s" % both_species,
        #       "<nu>", type(nu), nu,
        #       "",
        #       sep="\n")

        return nu

    def nc(self, sa, sb, both_species=True):
        r"""Calculate the Coulomb number between species `sa` and `sb`.

        Parameters
        ----------
        sa, sb: str
            Species identifying the ions to use in calculation. Can't be a
            combination of things like "s0+s1", "s0,s1", nor ("s0", "s1").
        both_species: bool
            Passed to `nuc`. If True, calculate the two-ion-plasma collision frequency.

        Returns
        -------
        nc: pd.Series
            Coulomb number

        See Also
        --------
        nuc, lnlambda
        """
        sa = self._chk_species(sa)
        sb = self._chk_species(sb)

        if len(sa) > 1 or len(sb) > 1:
            msg = (
                "`nc` can only calculate with individual `sa` and "
                "`sb` species.\nsa: %s\nsb: %s"
            )
            raise ValueError(msg % (sa, sb))

        sa, sb = sa[0], sb[0]

        sc = self.spacecraft
        if sc is None:
            msg = "Plasma doesn't contain spacecraft data. Can't calculate Coulomb number."
            raise ValueError(msg)

        r = sc.distance2sun * self.units.distance2sun
        #         r = self.constants.misc.loc["1AU [m]"] - (
        #             self.gse.x * self.constants.misc.loc["Re [m]"]
        #         )
        vsw = self.velocity("+".join(self.species)).mag * self.units.v
        tau_exp = r.divide(vsw, axis=0)

        nuc = self.nuc(sa, sb, both_species=both_species) * self.units.nuc

        nc = nuc.multiply(tau_exp, axis=0) / self.units.nc
        nc.name = nuc.name
        # Nc name should be handled by nuc name conventions.

        # print("",
        #       "<Module>",
        #       "<species>: {}".format((sa, sb)),
        #       "<both species>: %s" % both_species,
        #       "<r>", type(r), r,
        #       "<vsw>", type(vsw), vsw,
        #       "<tau_exp>", type(tau_exp), tau_exp,
        #       "<nuc>", type(nuc), nuc,
        #       "<nc>", type(nc), nc,
        #       "",
        #       sep="\n")

        return nc

    def vdf_ratio(self, beam="p2", core="p1"):
        r"""Calculate the ratio of the VDFs at the beam velocity.

        Calculate the ratio of a bi-Maxwellian proton beam to a bi-Maxwellian
        proton core VDF at the peak beam velocity.

        To avoid overflow erros, we return ln(ratio).

        The VDF for species :math:`i` at velocity :math:`v_j` is:

            :math:`f_i(v_j) = \frac{n_i}{(\pi w_i ^2)^{3/2}} \exp[ -(\frac{v_j - v_i}{w_i})^2]`

        The beam to core VDF ratio evaluated at the proton beam velocity is:

            :math:`\frac{f_2}{f_1}|_{v_2} = \frac{n_2}{n_1} ( \frac{w_1}{w_2} )^3 \exp[ (\frac{v_2 - v_1}{w_1})^2 ]`

        where :math:`n` is the number density, :math:`w` gives the thermal
        speed, and :math:`u` is the bulk velocity.

        In the case of a Bimaxwellian, we :math:`w^3 = w_\parallel w_\perp^2`
        :math:`(\frac{v - v_i}{w_i})^2 = (\frac{v - v_i}{w_i})_\parallel^2 + (\frac{v - v_i}{w_i})_\perp^2`.

        Parameters
        ----------
        plasma : pd.DataFrame
            Contains the number densities, vector velocities, and thermal speeds
            of the beam and core species.
        beam : str, "p2"
            The beam population, defaults to proton beams.
        core : str, "p1"
            The core population, defaults to proton core.

        Returns
        -------
        f2f1 : pd.Series
            Natural logarithm of the beam to core VDF ratio.

        Notes
        -----
        This routine was written for Faraday cup data quality validation, so
        alpha particle velocities are projected with by :math:`\sqrt{2.0}` to
        the velocity window in which they are measured.
        """
        beam = self._chk_species(beam)
        core = self._chk_species(core)

        if len(beam) > 1:
            raise ValueError(
                """VDFs are evaluated on a species-by-species basis. Beam `{}` is invalid.""".format(
                    beam
                )
            )
        if len(core) > 1:
            raise ValueError(
                """VDFs are evaluated on a species-by-species basis. Core `{}` is invalid.""".format(
                    core
                )
            )

        beam = beam[0]
        core = core[0]

        n1 = self.data.xs(("n", "", core), axis=1)
        n2 = self.data.xs(("n", "", beam), axis=1)

        w = self.w(beam, core).drop("scalar", axis=1, level="C")
        w1_par = w.par.loc[:, core]
        w1_per = w.per.loc[:, core]
        w2_par = w.par.loc[:, beam]
        w2_per = w.per.loc[:, beam]

        dv = self.dv(beam, core, project_m2q=True).project(self.b)
        dvw = dv.divide(w.xs(core, axis=1, level="S")).pow(2).sum(axis=1)

        nbar = n2 / n1
        wbar = (w1_par / w2_par).multiply((w1_per / w2_per).pow(2), axis=0)
        coef = nbar.multiply(wbar, axis=0).apply(np.log)
        # f2f1 = nbar * wbar * f2f1
        f2f1 = coef.add(dvw, axis=0)

        assert isinstance(f2f1, pd.Series)
        sbc = "%s/%s" % (beam, core)
        f2f1.name = sbc

        #        print("",
        #              "<Module>",
        #              "<species>: {},{}".format(beam, core),
        #              "<ni>", type(n1), n1,
        #              "<nj>", type(n2), n2,
        #              "<nbar>", type(nbar), nbar,
        #              "<w1_par>", type(w1_par), w1_par,
        #              "<w1_per>", type(w1_per), w1_per,
        #              "<w2_par>", type(w2_par), w2_par,
        #              "<w2_per>", type(w2_per), w2_per,
        #              "<wbar>", type(wbar), wbar,
        #              "<coef>", type(coef), coef,
        #              "<dv>", type(dv), dv,
        #              "<dvw>", type(dvw), dvw,
        #              "<f2f1>", type(f2f1), f2f1,
        #              "",
        #              sep="\n"
        #             )

        return f2f1

    def estimate_electrons(self, inplace=False):
        r"""Estimate the electron parameters with a scalar temperature.

        Assume temperature is the same as proton scalar temerature.
        """

        species = self.species

        if "e" in species:
            msg = (
                r"Estimating electrons when there are e- in the data has been "
                r"disabled because I've screwed it up and estimated them as zero b/c "
                r"of various strange things. I need to disable `inplace` when `e` in "
                r"speces and do some ther things for this to work."
            )
            raise NotImplementedError(msg)

        if "p" not in species and "p1" not in species:
            msg = (
                "Plasma must contain (core) protons to estimate electrons.\n"
                "Available species: {}".format(species)
            )
            raise ValueError(msg)
        elif "p" in species and "p1" in species:
            msg = (
                "Plasma cannot contain protons (p) and core protons (p1).\n"
                "Available species: {}".format(species)
            )
            raise ValueError(msg)
        elif "p" in species and "p1" not in species:
            tkw = "p"
        elif "p" not in species and "p1" in species:
            tkw = "p1"
        else:
            msg = "Unrecognized species: {}".format(species)
            raise ValueError(species)

        qi = self.constants.charge_states.loc[list(species)]
        ni = self.number_density(*species)
        vi = self.velocity(*species)
        if isinstance(vi, vector.Vector):
            # Then we only have a single component proton plasma.
            qi = qi.loc[species[0]]
            vi = vi.cartesian
            niqi = ni.multiply(qi)
            ne = niqi
            niqivi = vi.multiply(niqi, axis=0)
        else:
            vi = pd.concat(
                vi.apply(lambda x: x.cartesian).to_dict(), axis=1, names="S", sort=True
            )
            niqi = ni.multiply(qi, axis=1, level="S")
            ne = niqi.sum(axis=1)
            # niqivi = vi.multiply(niqi, axis=1, level="S").sum(axis=1, level="C")
            niqivi = (
                vi.multiply(niqi, axis=1, level="S").T.groupby(level="C").sum().T
            )  # sum(axis=1, level="C")

        ve = niqivi.divide(ne, axis=0)

        wp = self.w(tkw).loc[:, "scalar"]
        nrat = self.number_density(tkw).divide(ne, axis=0)
        mpme = self.constants.m_in_mp["e"] ** -1
        we = (nrat * mpme).multiply(wp.pow(2), axis=0).pipe(np.sqrt)
        we = pd.concat([we, we], axis=1, keys=["par", "per"], sort=True)

        ne.name = ""
        electrons = pd.concat(
            [ne, ve, we], axis=1, keys=["n", "v", "w"], names=["M", "C"], sort=True
        )
        mask = ~ne.astype(bool)
        electrons = electrons.mask(mask, axis=0)

        electrons = ions.Ion(electrons, "e")

        if inplace:
            cols = electrons.data.columns
            cols = [x + ("e",) for x in cols.values]
            cols = pd.MultiIndex.from_tuples(cols, names=["M", "C", "S"])
            electrons.data.columns = cols

            data = self.data
            if data.columns.intersection(electrons.data.columns).size:
                data.update(electrons.data)
            else:
                data = pd.concat([data, electrons.data], axis=1, sort=True)
                species = sorted(self.species + ("e",))
                self._set_species(*species)
                self.set_data(data)
                self._set_ions()

        #        print("<Module>",
        #              "<species>: {}".format(species),
        #              "<qi>", type(qi), qi,
        #              "<ni>", type(ni), ni,
        #              "<vi>", type(vi), vi,
        #              "<wp>", type(wp), wp,
        #              "<niqi>", type(niqi), niqi,
        #              "<niqivi>", type(niqivi), niqivi,
        #              "<ne>", type(ne), ne,
        #              "<ve>", type(ve), ve,
        #              "<we>", type(we), we,
        #              "<electrons>", type(electrons), electrons, electrons.data,
        #              "<plasma.species>: {}".format(self.species),
        #              "<plasma.ions>", type(self.ions), self.ions,
        #              "<plasma.data>", type(self.data), self.data.T,
        #              "", sep="\n")

        return electrons

    def heat_flux(self, *species):
        r"""Calculate the parallel heat flux.

            :math:`Q_\parallel = \rho (v^3 + \frac{3}{2}vw^2)`

        where :math:`v` is each species' velocity in the Center-of-Mass frame and
        :math:`w` is each species parallel thermal speed.

        Parameters
        ----------
        species: list of strings
            The species to use. If a sum is indicated, take the sum
            of the input species.

        Returns
        -------
        q: `pd.Series` or `pd.DataFrame`
            Dimensionality depends on species inputs.
        """

        slist = self._chk_species(*species)
        if len(slist) <= 1:
            raise ValueError("Must have >1 species to calculate heatflux.")

        scom = "+".join(slist)
        rho = self.mass_density(*slist)
        dv = {s: self.dv(s, scom).project(self.b).par for s in slist}
        dv = pd.concat(dv, axis=1, names=["S"], sort=True)
        dv.columns.name = "S"
        w = self.data.w.par.loc[:, slist]

        qa = dv.pow(3)
        qb = dv.multiply(w.pow(2), axis=1, level="S").multiply(3.0 / 2.0)

        #        print("<Module>",
        #              "<species> {}".format(species),
        #              "<rho>", type(rho), rho,
        #              "<v>", type(v), v,
        #              "<w>", type(w), w,
        #              "<qa>", type(qa), qa,
        #              "<qb>", type(qb), qb,
        #              sep="\n")

        qs = qa.add(qb, axis=1, level="S").multiply(rho, axis=0)
        if len(species) == 1:
            qs = qs.sum(axis=1)
            qs.name = "+".join(species)

        #        print("<qpar>", type(qs), qs,
        #              sep="\n")

        coeff = self.units.rho * (self.units.v**3.0) / self.units.qpar
        q = coeff * qs
        return q

    def qpar(self, *species):
        r"""Shortcut to :py:meth:`heat_flux`."""
        return self.heat_flux(*species)

    def build_alfvenic_turbulence(self, species, **kwargs):
        # raise NotImplementedError("Still working on module dev")
        r"""Create an Alfvenic turbulence instance.

        Parameters
        ----------
        species: str
            Species identifier. When no `,` present, use center-of-mass
            velocity as the velocity term. Alternatively, may contain up to
            one `,`. This is a unique `Plasma` case in which `s0+s1,s0+s1+s2`
            is a valid identifier. Here, the 2nd species is treated as the
            mass density passed to `AlfvenTurbulence` and used for converting
            magentic field in Alfven units.
        kwargs:
            Passed to `rolling` method in
            :py:class:`~solarwindpy.core.alfvenic_turbulence.AlfvenicTurbulence`
            to specify window size.
        """
        species_ = species.split(",")

        b = self.bfield.cartesian

        if len(species_) == 1:
            # Don't hold onto `_chk_species` return because we need `velocity` and
            # `mass_density` to process center-of-mass species. (20190325)
            self._chk_species(species_[0])
            v = self.velocity(species)
            r = self.mass_density(species)

        elif len(species_) == 2:
            slist0 = self._chk_species(species_[0])
            slist1 = self._chk_species(species_[1])

            s0 = "+".join(slist0)
            s1 = "+".join(slist1)
            v = self.dv(s0, s1)
            r = self.mass_density(s1)

        else:
            msg = "`species` can only contain at most 1 comma\nspecies: %s"
            raise ValueError(msg % species)

        v = v.cartesian

        turb = alf_turb.AlfvenicTurbulence(v, b, r, species, **kwargs)

        return turb

    def S(self, *species):
        r"""Shortcut to :py:meth:`specific_entropy`."""
        return self.specific_entropy(*species)

    def specific_entropy(self, *species):
        r"""Calculate the specific entropy following [1] as.

            :math:`p_\mathrm{th} \rho^{-\gamma}`

        where :math:`gamma=5/3`, :math:`p_\mathrm{th}` is the thermal presure,
        and :math:`rho` is the mass density.

        Parameters
        ----------
        species: str or list-like of str
            Comma separated strings ("a,p1") are invalid.
            Comma separated lists ("a", "p1") are valid.
            Total effective species ("a+p1") are valid and use

                :math:`p_\mathrm{th} = \sum_s p_{\mathrm{th},s}`
                :math:`\rho = \sum_s \rho_s`.

        References
        ----------
        [1] Siscoe, G. L. (1983). Solar System Magnetohydrodynamics (pp.
            11–100). <https://doi.org/10.1007/978-94-009-7194-3_2>.
        """
        multi_species = len(species) > 1
        gamma = self.constants.polytropic_index["scalar"]

        pth = self.pth(*species).xs(
            "scalar", axis=1, level="C" if multi_species else None
        )
        rho = self.rho(*species)

        pth *= self.units.pth
        rho *= self.units.rho

        out = pth.multiply(
            rho.pow(-gamma),
            axis=1 if multi_species else 0,
            level="S" if multi_species else None,
        )
        out /= self.units.specific_entropy
        out.name = "S"

        return out

    def kinetic_energy_flux(self, *species):
        r"""Calculate the plasma kinetic energy flux.

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". If this is the case, the species are summed over and
            a pd.Series is returned. Otherwise, the individual quantities are
            returned as a pd.DataFrame.

        Returns
        -------
        rho: pd.Series or pd.DataFrame
            See Parameters for more info.
        """
        slist = self._chk_species(*species)

        w = {s: self.ions.loc[s].kinetic_energy_flux for s in slist}
        w = pd.concat(w, axis=1, names=["S"], sort=True)

        if len(species) == 1:
            w = w.sum(axis=1)
            w.name = species[0]

        return w

    def Wk(self, *species):
        r"""Shortcut to :py:meth:`~kinetic_energy_flux`."""
        return self.kinetic_energy_flux(*species)
