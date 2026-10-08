#!/usr/bin/env python
"""The Plasma class that contains all Ions, magnetic field, and spacecraft information.

Propoded Updates
^^^^^^^^^^^^^^^^
-It would be cute if one could call `plasma % a`, i.e. plasma mod
 an ion and return a new plasma without that ion in it. Well, either
 mod or subtract. Subtract and add probably make more sense. (20180129)

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

__all__ = [
    "Plasma",
]

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
from . import alfvenic_turbulence


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
    shorthand such as ``plasma.a`` to access the alpha particle
    :class:`~solarwindpy.core.ions.Ion`
    and ``plasma.p1`` for protons.

    Attributes
    ----------
    data : pandas.DataFrame
        Multi-indexed DataFrame containing plasma measurements with columns
        labeled by ("M", "C", "S") for measurement, component, and species.
    ions : pandas.Series of Ion objects
        Dictionary-like access to individual ion species objects.
    species : tuple of str
        Available ion species identifiers in the plasma, sorted.
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
    Load the example plasma, which holds multi-species data:

    >>> import solarwindpy as swp
    >>> plasma = swp.examples.load_plasma()
    >>> type(plasma.p1).__name__  # Proton ion object
    'Ion'
    >>> plasma.p1.n.tolist()  # Proton number density
    [1.0, 2.0, 3.0]

    Build a Plasma from your own DataFrame with ("M", "C", "S") columns by
    passing it with the species to load; here the example's frame stands in:

    >>> from solarwindpy.core.plasma import Plasma
    >>> mine = Plasma(plasma.data, *plasma.species)
    >>> mine.species
    ('a', 'e', 'p1', 'p2')
    >>> mine.data.equals(plasma.data)
    True

    Calculate plasma physics parameters:

    >>> beta = plasma.beta('p1')          # Plasma beta for protons
    >>> type(beta).__name__
    'DataFrame'
    >>> beta.columns.tolist()
    ['par', 'per', 'scalar']
    >>> beta.loc[:, "scalar"].round(4).tolist()
    [0.3447, 4.178, 4.9268]

    Identify ion species in plasma (stored sorted, as a tuple):

    >>> plasma.species
    ('a', 'e', 'p1', 'p2')
    """

    def __init__(
        self,
        data,
        *species,
        spacecraft=None,
        auxiliary_data=None,
    ):
        r"""Initialize a :class:`Plasma` instance.

        Parameters
        ----------
        data : :class:`pandas.DataFrame`
            Contains the magnetic field and core ion moments. Columns are a
            three-level :class:`~pandas.MultiIndex` labelled ``("M", "C", "S")``
            for measurement, component, and species; the levels may come in
            any order. The index should contain datetime information, for
            example ``Epoch`` when loading from a CDF file. Rows out of time
            order are sorted with a warning (see Notes).
        *species : str
            Iterable of species contained in ``data``.
        spacecraft : :class:`~solarwindpy.core.spacecraft.Spacecraft`, optional
            Spacecraft trajectory and velocity information, at the times of
            ``data`` (see Notes), with column levels named exactly
            ``("M", "C")`` in that order. If ``None``, the Coulomb number
            :py:meth:`~Plasma.nc` method will raise a :class:`ValueError`.
        auxiliary_data : :class:`pandas.DataFrame`, optional
            Additional measurements to carry with the plasma, for example data
            quality flags, at the times of ``data`` (see Notes). Its column
            levels must be named exactly ``("M", "C", "S")`` in that order.

        Raises
        ------
        TypeError
            If ``data`` is not a :class:`pandas.DataFrame`.
        ValueError
            If the time index of ``data`` has missing timestamps (``NaT``); the
            message names how many.

        Notes
        -----
        Thermal speeds assume :math:`mw^2 = 2kT`.

        The data are put in time order by :meth:`set_data`, and every method
        may assume sorted data afterwards. Rows earlier than the row before
        them are counted and located in a warning, then sorted with a stable
        sort, so rows sharing a timestamp keep their order. Spacecraft and
        auxiliary data on the same index as ``data`` come from the same source
        and are sorted the same way without a further warning; at the same
        times in another order, they are reordered to the plasma's with a
        warning. Repeated
        timestamps log a warning and are kept. Missing timestamps (``NaT``)
        have no place in time order, so they raise rather than being sorted.

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
        if not isinstance(data, pd.DataFrame):
            raise TypeError(
                f"Plasma data must be a pandas DataFrame, not {type(data).__name__}"
            )
        # Nothing is attached yet, so `set_data` sorts rather than refusing.
        self._spacecraft = None
        self._auxiliary_data = None
        source = data.index
        self._set_species(*species)
        super(Plasma, self).__init__(data)
        self._set_ions()
        self._set_spacecraft(spacecraft, source)
        self._set_auxiliary_data(auxiliary_data, source)

    def __getattr__(self, attr):
        r"""Return the :class:`~solarwindpy.core.ions.Ion` named ``attr``.

        Python calls this only after normal lookup fails, so ``plasma.p1`` is
        the proton ion. Any other name raises :class:`AttributeError` naming
        it, so :func:`hasattr` and :func:`getattr` with a default work.
        """
        # Read `_ions` from the instance dict: before `_set_ions` runs, going
        # through the `ions` property would re-enter this method.
        ions_ = self.__dict__.get("_ions")
        if ions_ is not None and attr in ions_.index:
            return ions_.loc[attr]
        raise AttributeError(
            f"{self.__class__.__name__!r} object has no attribute {attr!r}"
        )

    @property
    def epoch(self):
        """Time index of the plasma data.

        Returns
        -------
        pandas.DatetimeIndex
            Datetime index containing measurement timestamps.

        Examples
        --------
        >>> import solarwindpy as swp
        >>> plasma = swp.examples.load_plasma()
        >>> times = plasma.epoch.strftime("%Y-%m-%d %H:%M:%S.%f")
        >>> times.tolist()  # doctest: +NORMALIZE_WHITESPACE
        ['1995-01-01 12:35:00.000000', '2022-03-23 19:29:09.000000',
         '2022-10-09 01:47:01.234560']
        >>> plasma.epoch.name
        'epoch'
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
        return self._auxiliary_data

    @property
    def aux(self):
        r"""Shortcut to :py:attr:`auxiliary_data`."""
        return self.auxiliary_data

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

        plasma = cls(data, *species, **kwargs)

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
        )
        return new

    def set_spacecraft(self, new):
        """Set or update the spacecraft trajectory data.

        Parameters
        ----------
        new : Spacecraft or None
            Spacecraft trajectory object containing position and velocity data,
            at the plasma data's times. Times in another order are reordered
            to the plasma's, with a warning.

        Raises
        ------
        ValueError
            If the spacecraft index holds missing timestamps (``NaT``) or other
            times than the plasma data's, or its column levels are not named
            exactly ``("M", "C")``, in that order.

        Notes
        -----
        The spacecraft data is required for calculating certain plasma physics
        parameters such as Coulomb collision frequencies that depend on the
        plasma frame transformation.

        Examples
        --------
        >>> import solarwindpy as swp
        >>> plasma = swp.examples.load_plasma()
        >>> psp = plasma.spacecraft

        Setting ``None`` logs "No spacecraft data passed to Plasma" at INFO:

        >>> plasma.set_spacecraft(None)
        >>> plasma.spacecraft is None
        True
        >>> plasma.set_spacecraft(psp)
        >>> plasma.spacecraft.name
        'PSP'
        >>> plasma.spacecraft.position.data.loc[:, "x"].tolist()  # trajectory
        [-42.0, -22.0, -34.0]
        """
        self._set_spacecraft(new)

    def _set_spacecraft(self, new, source=None):
        """Set the spacecraft; ``source`` is the index the plasma data arrived on.

        Spacecraft data on ``source`` share the plasma data's origin and are
        put in the plasma's order without a warning of their own.
        """
        assert isinstance(new, spacecraft.Spacecraft) or new is None

        if new is not None:
            assert isinstance(new.data.index, pd.DatetimeIndex)
            order = self._plasma_order(new.data.index, "Spacecraft data", source)
            self._require_level_names(new.data.columns, ("M", "C"), "Spacecraft data")
            # Don't test spacecraft data duplicating plasma data b/c labels will
            # overlap even though they represent different quantities because
            # spacecraft only has a 2-level MultiIndex.
            if order is not None:
                new = spacecraft.Spacecraft(new.data.iloc[order], new.name, new.frame)

        self._log_if_missing(new, "spacecraft")
        self._spacecraft = new

    def set_auxiliary_data(self, new):
        """Set or update auxiliary measurement data.

        Parameters
        ----------
        new : pandas.DataFrame or None
            Additional measurements such as data quality flags, derived
            parameters, or instrument-specific metadata, at the plasma data's
            times. Times in another order are reordered to the plasma's, with
            a warning.

        Raises
        ------
        ValueError
            If the auxiliary data's index holds missing timestamps (``NaT``) or
            other times than the plasma data's, its column levels are not named exactly ``("M", "C", "S")`` in that
            order, or it duplicates a plasma data column.

        Notes
        -----
        Auxiliary data provides additional context for plasma measurements
        without being part of the core plasma physics calculations. Common
        examples include quality flags, statistical uncertainties, or
        instrument operational parameters.

        Examples
        --------
        >>> import solarwindpy as swp
        >>> plasma = swp.examples.load_plasma()
        >>> plasma.auxiliary_data is None
        True
        >>> quality_flags = pd.DataFrame({("quality", "", ""): [0, 1, 0]},
        ...                              index=plasma.epoch)
        >>> quality_flags.columns.names = ["M", "C", "S"]
        >>> plasma.set_auxiliary_data(quality_flags)
        >>> plasma.aux.loc[:, ("quality", "", "")].tolist()  # auxiliary data
        [0, 1, 0]
        """
        self._set_auxiliary_data(new)

    def _set_auxiliary_data(self, new, source=None):
        """Set the auxiliary data; ``source`` as in :meth:`_set_spacecraft`."""
        assert isinstance(new, pd.DataFrame) or new is None

        if new is not None:
            assert isinstance(new.index, pd.DatetimeIndex)
            order = self._plasma_order(new.index, "Auxiliary data", source)
            self._require_level_names(new.columns, ("M", "C", "S"), "Auxiliary data")
            if new.columns.isin(self.data.columns).any():
                raise ValueError("Auxiliary data should not duplicate plasma data")
            if order is not None:
                new = new.iloc[order]

        self._log_if_missing(new, "auxiliary_data")
        self._auxiliary_data = new

    def _log_if_missing(self, new, name):
        """Log at INFO that the optional input ``name`` was not passed."""
        if new is None:
            self.logger.info("No %s data passed to %s", name, self.__class__.__name__)

    @staticmethod
    def _require_level_names(columns, expected, what, any_order=False):
        r"""Raise :class:`ValueError` unless ``columns``' levels are named ``expected``.

        Parameters
        ----------
        columns : pd.MultiIndex
            The columns to check.
        expected : tuple of str
            The required level names.
        what : str
            Names the checked frame in the error message.
        any_order : bool, optional
            Accept ``expected`` in any order.
        """
        # Compare as lists: pandas 3 makes a FrozenList both == and != a tuple.
        names = list(columns.names)
        want = list(expected)
        if any_order:
            names, want = sorted(names, key=str), sorted(want)
        if names != want:
            order = " in any order" if any_order else ""
            raise ValueError(
                f"{what} columns must have levels named {tuple(expected)}{order}, "
                f"not {tuple(columns.names)}"
            )

    def _require_plasma_index(self, index, what):
        r"""Raise :class:`ValueError` unless ``index`` equals the plasma data's.

        Parameters
        ----------
        index : pd.Index
            The time index to check.
        what : str
            Names the checked frame in the error message.
        """
        expected = self.data.index
        if index.equals(expected):
            return
        if len(index) != len(expected):
            detail = f"it has {len(index)} rows, the plasma data {len(expected)}"
        else:
            # NaT compares unequal to everything, and the plasma's own index
            # holds none (the constructor refuses it).
            differs = index.to_numpy() != expected.to_numpy()
            row = int(np.flatnonzero(differs)[0])
            detail = f"first difference at row {row}: {index[row]} vs {expected[row]}"
        raise ValueError(
            f"{what} index must equal the plasma data's time index; {detail}"
        )

    @staticmethod
    def _time_order(index, what):
        r"""Locate the rows of ``index`` out of time order, refusing ``NaT``.

        Parameters
        ----------
        index : pd.Index
            The time index to check.
        what : str
            Names the checked frame in the error message.

        Returns
        -------
        behind : np.ndarray
            Positions of rows earlier than the row before them.
        order : np.ndarray or None
            The stable sort putting ``index`` in time order, so rows sharing a
            timestamp keep their order; None when ``index`` is in order.

        Raises
        ------
        ValueError
            If ``index`` holds any ``NaT``, naming how many.
        """
        missing = int(index.isna().sum())
        if missing:
            raise ValueError(
                f"{what} time index has {missing} of {len(index)} "
                "timestamps missing (NaT); drop those rows first"
            )
        values = index.to_numpy()
        behind = np.flatnonzero(values[1:] < values[:-1]) + 1
        order = np.argsort(values, kind="stable") if len(behind) else None
        return behind, order

    def _plasma_order(self, index, what, source=None):
        r"""Return the positions putting ``index`` in the plasma data's order.

        An index holding the plasma's times in another order is reordered to
        it with a warning, unless it equals ``source``, the index the plasma
        data arrived on. Any other mismatch raises.

        Parameters
        ----------
        index : pd.Index
            The time index of spacecraft or auxiliary data.
        what : str
            Names the checked frame in messages.
        source : pd.Index, optional
            The index the plasma data had before sorting.

        Returns
        -------
        np.ndarray or None
            None when ``index`` already equals the plasma data's.

        Raises
        ------
        ValueError
            If ``index`` holds ``NaT``, or other times than the plasma data's.
        """
        _, order = self._time_order(index, what)
        if order is not None and index[order].equals(self.data.index):
            if source is None or not index.equals(source):
                self.logger.warning(
                    "%s hold the plasma data's times in another order; "
                    "reordering them to the plasma's",
                    what,
                )
            return order
        self._require_plasma_index(index, what)
        return None

    def _sort_by_time(self, data):
        r"""Put ``data`` in time order, warning of rows out of order or repeated.

        Missing timestamps (``NaT``) raise. Rows earlier than the row before
        them are counted and located in one warning, then sorted with a stable
        sort, so rows sharing a timestamp keep their order. Data out of order
        raise instead when spacecraft or auxiliary data are attached, since
        sorting would misalign them. Repeated timestamps log a warning and are
        kept.

        Parameters
        ----------
        data : pd.DataFrame
            Plasma data indexed by time.

        Returns
        -------
        pd.DataFrame
            ``data`` in time order; the input itself when already in order.

        Raises
        ------
        ValueError
            If ``data``'s time index holds any ``NaT``, naming how many, or is
            out of order while spacecraft or auxiliary data are attached.
        """
        index = data.index
        behind, order = self._time_order(index, "Plasma data")
        if order is not None:
            if self._spacecraft is not None or self._auxiliary_data is not None:
                raise ValueError(
                    f"{len(behind)} of {len(index)} plasma data rows are earlier "
                    "than the row before them; sorting would misalign the "
                    "attached spacecraft or auxiliary data, so sort the data "
                    "first"
                )
            self.logger.warning(
                "%d of %d rows are earlier than the row before them, first at "
                "rows %s (times %s); sorting the data by time",
                len(behind),
                len(index),
                behind[:5].tolist(),
                [str(t) for t in index[behind[:5]]],
            )
            data = data.iloc[order]
            index = data.index

        repeated = index.duplicated(keep="first")
        if repeated.any():
            rows = np.flatnonzero(repeated)
            self.logger.warning(
                "%d of %d rows repeat an earlier timestamp, first at rows %s "
                "(times %s); keeping them",
                len(rows),
                len(index),
                rows[:5].tolist(),
                [str(t) for t in index[rows[:5]]],
            )
        return data

    def set_data(self, new):
        r"""Set the data in time order, logging its shape and any columns dropped.

        Rows out of time order are sorted with a warning, as at construction
        (see :class:`Plasma`).

        Raises
        ------
        ValueError
            If the column levels are not named ``"M"``, ``"C"`` and ``"S"``;
            if the time index holds missing timestamps (``NaT``); or if the
            rows are out of time order while spacecraft or auxiliary data are
            attached, since sorting would misalign them.
        """
        new = self._sort_by_time(new)
        super(Plasma, self).set_data(new)

        self._require_level_names(
            new.columns, ("M", "C", "S"), "Plasma data", any_order=True
        )
        new = new.reorder_levels(["M", "C", "S"], axis=1).sort_index(axis=1)

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
        self._mask_invalid_species(data)

        coeff = pd.Series({"per": 2.0, "par": 1.0}) / 3.0

        w = (
            data.loc[:, pd.IndexSlice["w", ["par", "per"]]]
            .pow(2)
            .multiply(coeff, axis=1, level="C")
        )

        # skipna=False: within a species, a time missing either part has no
        # scalar thermal speed (docs page `missing_data`).
        w = w.T.groupby("S").sum(skipna=False).T.pow(0.5)

        # TODO: can probably just `w.columns.map(lambda x: ("w", "scalar", x))`
        w.columns = w.columns.to_series().apply(lambda x: ("w", "scalar", x))
        w.columns = self.mi_tuples(w.columns)

        data = pd.concat([data, w], axis=1, sort=False).sort_index(axis=1)

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

    def _mask_invalid_species(self, data):
        r"""Set a species to NaN at every time any of its moments is missing.

        A species' density, velocity components and thermal-speed components
        stand or fall together: if any is missing at a time, every measurement
        of that species is invalid then (docs page :doc:`/missing_data`).
        ``data`` is modified in place, and a warning logs how many times each
        species lost.

        Parameters
        ----------
        data : pd.DataFrame
            Plasma data with column levels ``("M", "C", "S")``.
        """
        moments = data.loc[
            :,
            pd.IndexSlice[
                ["n", "v", "w"], ["", "x", "y", "z", "par", "per"], list(self.species)
            ],
        ]
        invalid = moments.isna().T.groupby(level="S").any().T
        species = data.columns.get_level_values("S")
        for s, missing in invalid.items():
            count = int(missing.sum())
            if count:
                data.loc[missing.to_numpy(), species == s] = np.nan
                self.logger.warning(
                    "masked species %s at %d of %d times: a density, velocity or "
                    "thermal speed component is missing",
                    s,
                    count,
                    len(missing),
                )

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
            # min_count=1: a total with no species present is NaN, not 0.
            n = n.sum(axis=1, skipna=skipna, min_count=1)
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
            # min_count=1: a total with no species present is NaN, not 0.
            rho = rho.sum(axis=1, min_count=1)
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
            # min_count=1: a time where the species is missing stays NaN.
            w = w.T.groupby(level="C").sum(min_count=1).T

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

        Notes
        -----
        A species missing a thermal speed component at a time has no scalar
        pressure then, and a species sum adds the species present, NaN only
        where none is: see :doc:`/missing_data`.
        """
        slist = self._chk_species(*species)
        include_dynamic = False
        if include_dynamic:
            raise NotImplementedError

        pth = {s: self.ions.loc[s].pth for s in slist}
        pth = pd.concat(pth, axis=1, names=["S"], sort=True)
        pth = pth.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)

        if len(species) == 1:
            pth = pth.T.groupby("C").sum(min_count=1).T
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

        Notes
        -----
        A species missing a thermal speed component at a time has no scalar
        temperature then, and a species sum adds the species present, NaN only
        where none is: see :doc:`/missing_data`.
        """
        slist = self._chk_species(*species)
        temp = {s: self.ions.loc[s].temperature for s in slist}
        temp = pd.concat(temp, axis=1, names=["S"], sort=True)
        temp = temp.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)

        if len(species) == 1:
            temp = temp.T.groupby("C").sum(min_count=1).T
        return temp

    def beta(self, *species):
        r"""Get perpendicular, parallel, and scalar plasma beta.

        Parameters
        ----------
        species: str
            Each species is a string. Species handling controlled by :py:meth:`pth`.

        Returns
        -------
        beta : pd.DataFrame
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
        ani : pd.Series or pd.DataFrame
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
            "+", return the center-of-mass velocity. If it contains a single
            species, return that ion's velocity.
        project_m2q: bool, False
            If True, project velocity by :math:`\sqrt{m/q}`. Disables center-of-
            mass species.

        Returns
        -------
        velocity : vector.Vector or pd.Series
            A :py:class:`~solarwindpy.core.vector.Vector` for one species
            string, or a `pd.Series` of them indexed by species when several
            species are passed.
        """
        stuple = self._chk_species(*species)

        if len(stuple) == 1:
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
""".format(species)
            )

        else:
            v = self.ions.loc[list(stuple)].apply(lambda x: x.velocity)
            if len(species) == 1:
                rhos = self.mass_density(*stuple)
                v = pd.concat(
                    v.apply(lambda x: x.cartesian).to_dict(),
                    axis=1,
                    names=["S"],
                    sort=True,
                )
                v = vector.Vector(self._species_weighted_mean(v, rhos))

        return v

    @staticmethod
    def _species_weighted_mean(vectors, weights):
        r"""Weighted mean of vectors over the species present at each time.

        A species is present at a time when its weight and every vector
        component are; one that is absent leaves both the weighted sum and the
        sum of weights. A time with no species present is NaN. See
        :doc:`/missing_data`.

        This relies on species masking when the data are set: a species'
        density and velocity are missing together, so a weight never pairs
        with a missing velocity, nor a velocity with a missing weight.

        Parameters
        ----------
        vectors : pd.DataFrame
            Cartesian components with column levels ``("S", "C")``.
        weights : pd.DataFrame
            One column per species, e.g. mass or charge density.

        Returns
        -------
        mean : pd.DataFrame
            One column per component.
        """
        present = vectors.notna().T.groupby(level="S").all().T & weights.notna()
        weights = weights.where(present)
        weighted = vectors.multiply(weights, axis=1, level="S")
        total = weighted.T.groupby(level="C").sum(min_count=1).T
        return total.divide(weights.sum(axis=1, min_count=1), axis=0)

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
        dv : vector.Vector

        See Also
        --------
        solarwindpy.core.vector.Vector
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
            # Within a species, a missing component makes dv^2 NaN; across
            # species, the sum keeps the species present (docs `missing_data`).
            dvsq_i = dv_i.pow(2.0).T.groupby(level="S").sum(skipna=False).T
            dvsq_rho_i = dvsq_i.multiply(rho_i, axis=1, level="S")
            pdv = dvsq_rho_i.sum(axis=1, min_count=1)

        elif len(stuple) == 2:
            # Can only have 2 species with `project_m2q`.
            dvsq = (
                self.dv(*stuple, project_m2q=project_m2q)
                .cartesian.pow(2)
                .sum(axis=1, skipna=False)
            )
            rho_i = self.mass_density(*stuple)
            # skipna=False: the reduced mass needs both species.
            mu = rho_i.product(axis=1, skipna=False).divide(
                rho_i.sum(axis=1, skipna=False), axis=0
            )
            pdv = dvsq.multiply(mu, axis=0)

        pdv = pdv.multiply(const)
        pdv.name = "pdynamic"

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
        cs : pd.DataFrame or pd.Series
            Depends on the `species` inputs.
        """
        slist = self._chk_species(*species)
        rho = self.mass_density(*species) * self.units.rho
        pth = self.pth(*species) * self.units.pth

        pth = pth.loc[:, "scalar"]

        gamma = self.constants.polytropic_index["scalar"]  # should be 5/3
        cs = pth.divide(rho, axis=0).multiply(gamma).pow(0.5) / self.units.cs

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
        ca : pd.DataFrame or pd.Series
            Depends on the `species` inputs.
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

        return ca

    def afsq(self, *species, pdynamic=False):
        r"""Calculate the square of anisotropy factor.

            :math:`AF^2 = 1 + \frac{\mu_0}{B^2}\left(p_\perp - p_\parallel - p_{\tilde{v}}\right)`

        The pressures come from :py:meth:`pth`, so a species sum adds
        :math:`p_\perp - p_\parallel` over the species present at each time
        (see :doc:`/missing_data`).

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
        pdynamic: bool, str
            If str, the component of the dynamic pressure to use when
            calculating :math:`p_{\tilde{v}}`.

        Returns
        -------
        afsq : pd.Series or pd.DataFrame
            Depends on the number of `species` passed.
        """
        if pdynamic:
            raise NotImplementedError(
                "Youngest beams analysis shows "
                "that dynamic pressure is probably not useful."
            )

        # A missing field component leaves B^2 unknown.
        bsq = self.bfield.cartesian.pow(2.0).sum(axis=1, skipna=False)

        # A species is masked as a whole where any moment is missing, so its
        # p_per and p_par are present together and the species sum of
        # p_per - p_par equals summed p_per minus summed p_par (docs
        # `missing_data`). Dynamic pressure, if ever included, would be
        # subtracted here with the species aligned.
        pth = self.pth(*species)
        dp = pth.loc[:, "per"].subtract(pth.loc[:, "par"])

        mu0 = self.constants.misc.mu0
        coeff = mu0 * self.units.pth / (self.units.b**2.0)

        afsq = 1.0 + (dp.divide(bsq, axis=0) * coeff)

        if len(species) == 1:
            afsq.name = species[0]

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
            a pd.Series is returned. This addresses complications from
            combining the mass density in :py:meth:`ca` with the pressures in
            :py:meth:`afsq`, the latter via :py:meth:`pth`.
        pdynamic: bool, str
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
        # skipna=False: W_ab needs both species' thermal speeds.
        wab = w.pow(2.0).sum(axis=1, skipna=False).pipe(np.sqrt) * units.w

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

        if both_species:
            exp = pd.Series({sa: 1.0, sb: -1.0})
            rho_ratio = pd.concat(
                {s: self.mass_density(s) for s in [sa, sb]}, axis=1, sort=True
            )
            # skipna=False: the ratio needs both species.
            rho_ratio = rho_ratio.pow(exp, axis=1).product(axis=1, skipna=False)
            nuba = nuab.multiply(rho_ratio, axis=0)
            nu = nuab.add(nuba, axis=0)
            nu.name = f"{sa}+{sb}"
        else:
            nu = nuab
            nu.name = f"{sa}-{sb}"

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
        vsw = self.velocity("+".join(self.species)).mag * self.units.v
        tau_exp = r.divide(vsw, axis=0)

        nuc = self.nuc(sa, sb, both_species=both_species) * self.units.nuc

        nc = nuc.multiply(tau_exp, axis=0) / self.units.nc
        nc.name = nuc.name

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
            Natural logarithm of the beam to core VDF ratio. NaN where the
            beam drift cannot be projected onto the magnetic field, e.g. where
            b is missing.

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
        # skipna=False: where b is missing the projection is NaN, and the
        # ratio must be NaN rather than the drift-free value ln(n2 w1^3 / n1 w2^3).
        dvw = dv.divide(w.xs(core, axis=1, level="S")).pow(2).sum(axis=1, skipna=False)

        nbar = n2 / n1
        wbar = (w1_par / w2_par).multiply((w1_per / w2_per).pow(2), axis=0)
        coef = nbar.multiply(wbar, axis=0).apply(np.log)
        f2f1 = coef.add(dvw, axis=0)

        assert isinstance(f2f1, pd.Series)
        sbc = "%s/%s" % (beam, core)
        f2f1.name = sbc

        return f2f1

    def estimate_electrons(self, inplace=False):
        r"""Estimate the electron parameters with a scalar temperature.

        The electron density and velocity follow from quasi-neutrality and
        zero net current, :math:`n_e = \sum_s q_s n_s` and
        :math:`n_e v_e = \sum_s q_s n_s v_s`. The electron temperature equals
        the proton scalar temperature :math:`T_p`, so with :math:`m w^2 = 2 k T`

            :math:`w_e^2 = \frac{m_p}{m_e} w_p^2`.

        :math:`T_p` is taken from species ``p`` if the plasma holds it, and
        otherwise from the core protons ``p1``; the beam ``p2`` is never used.
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
            ve = vi.multiply(niqi, axis=0).divide(ne, axis=0)
        else:
            vi = pd.concat(
                vi.apply(lambda x: x.cartesian).to_dict(), axis=1, names="S", sort=True
            )
            niqi = ni.multiply(qi, axis=1, level="S")
            # Both sums run over the species present at each time; species
            # masking in `set_data` keeps a density from outliving its velocity.
            ne = niqi.sum(axis=1, min_count=1)
            ve = self._species_weighted_mean(vi, niqi)

        # T_e = T_p with m w^2 = 2 k T gives w_e^2 = (m_p / m_e) w_p^2.
        wp = self.w(tkw).loc[:, "scalar"]
        mpme = self.constants.m_in_mp["e"] ** -1
        we = wp.pow(2).multiply(mpme).pipe(np.sqrt)
        # Isotropic electrons: the scalar thermal speed equals both components.
        we = pd.concat([we, we, we], axis=1, keys=["par", "per", "scalar"], sort=True)

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

        return electrons

    def heat_flux(self, *species):
        r"""Calculate the parallel-parallel component of the heat flux tensor.

        For each species :math:`s` this is the third moment of its velocity
        distribution along the magnetic field, taken in the center-of-mass
        frame of the species passed to this method, and only those: for
        ``heat_flux("a+p1")`` or ``heat_flux("a", "p1")`` it is the a+p1
        center of mass, not that of every species in the plasma,

            :math:`Q_{\parallel,s} = \int m_s c_\parallel^3 f_s \, d^3v`,

        where :math:`c_\parallel` is the velocity component along
        :math:`\hat{b}` relative to the center of mass. For a drifting
        bi-Maxwellian with :math:`w^2 = 2kT/m` this evaluates to

            :math:`Q_{\parallel,s} = \rho_s (U_s^3 + \frac{3}{2} U_s w_{\parallel,s}^2)`,

        where :math:`U_s` is the species' drift along :math:`\hat{b}` in the
        center-of-mass frame and :math:`w_{\parallel,s}` its parallel thermal
        speed.

        This is the parallel-parallel part of the energy flux only, not the
        total energy flux along the field: the perpendicular thermal speed
        does not enter.

        Parameters
        ----------
        species: list of strings
            The species to use. If a sum is indicated, take the sum
            of the input species.

        Returns
        -------
        q: `pd.Series` or `pd.DataFrame`
            Dimensionality depends on species inputs. A species sum is a
            partial sum over the species present in each row; a row with no
            species present is NaN.
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

        qs = qa.add(qb, axis=1, level="S").multiply(rho, axis=0)
        if len(species) == 1:
            # min_count=1: a partial sum over the species present, NaN where none is.
            qs = qs.sum(axis=1, min_count=1)
            qs.name = "+".join(species)

        coeff = self.units.rho * (self.units.v**3.0) / self.units.qpar
        q = coeff * qs
        return q

    def qpar(self, *species):
        r"""Shortcut to :py:meth:`heat_flux`."""
        return self.heat_flux(*species)

    def build_alfvenic_turbulence(self, species, **kwargs):
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

        turb = alfvenic_turbulence.AlfvenicTurbulence(v, b, r, species, **kwargs)

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
        w: pd.Series or pd.DataFrame
            See Parameters for more info. A species sum is a partial sum over
            the species present in each row; a row with no species present is
            NaN.
        """
        slist = self._chk_species(*species)

        w = {s: self.ions.loc[s].kinetic_energy_flux for s in slist}
        w = pd.concat(w, axis=1, names=["S"], sort=True)

        if len(species) == 1:
            # min_count=1: a partial sum over the species present, NaN where none is.
            w = w.sum(axis=1, min_count=1)
            w.name = species[0]

        return w

    def Wk(self, *species):
        r"""Shortcut to :py:meth:`~kinetic_energy_flux`."""
        return self.kinetic_energy_flux(*species)
