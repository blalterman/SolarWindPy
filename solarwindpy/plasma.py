#!/usr/bin/env python
"""
Name   : plasma.py
Author : B. L. Alterman
e-mail : balterma@umich.edu

Description
-----------
-Contains Plasma class.

Propodes Updates
----------------
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

Notes
-----
-

"""

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import pdb
import logging

import re         as re
import numpy      as np
import pandas     as pd
import warnings
import itertools

from numbers import Number
from pandas import MultiIndex as MI

from abc import ABC, abstractmethod, abstractproperty

from scipy import constants
from scipy.constants import physical_constants

# We rely on views via DataFrame.xs to reduce memory size and do not
# `.copy(deep=True)`, so we want to make sure that this doesn't
# accidentally cause a problem.
pd.set_option("mode.chained_assignment", "raise")

try:
    from . import base
    from . import vector
    from . import tensor
    from . import ions
#    from . import alfvenic_turbulence as alf_turb
except ImportError:
    import base
    import vector
    import tensor
    import ions
#    import alfvenic_turbulence as alf_turb

class Plasma(base.Base):

    def __init__(self, data, *species):
        r"""
        Instantiate a plasma.

        Parameters
        ----------
        data: pd.DataFrame
            Contains n, v, w, and b at a minimum.
        species: iterable of strings
            The species included in the plasma.
        """
        self._init_logger()
        self._set_species(*species)
        super(Plasma, self).__init__(data)
        self._set_ions()

    def __getattr__(self, attr):
        if attr in self.ions.index:
            return self.ions.loc[attr]
        else:
            return super(Plasma, self).__getattr__(attr)

    @property
    def auxiliary_data(self):
        try:
            return self._auxiliary_data
        except AttributeError:
            raise AttributeError("No auxiliary data set.")
    @property
    def aux(self):
        return self.auxiliary_data

    def save(self, fname, dkey="FC", akey="FC_AUX", data_modifier_fcn=None, aux_modifier_fcn=None):
        r"""
        Save the plasma's underlying data and aux DataFrame to an HDF5 file at `fname`.

        Parameters
        ----------
        fname: str or `pathlib.Path`.
            File name pointing to the save location.
            The typical use when creating a data file in `Create_Datafile.ipynb`
            is `fname("swe", "h5", strip_date=True)`.
        dkey: None
            The HDF5 file key at which to store the data.
        akey: None
            The HDF5 file key at which to store the auxiliary_data.
        data_modifier_fcn: None, FunctionType
            A function to modify the data saved, e.g. if you don't want to save
            a specific species in the data file, you can pass.

                def modify_data(data):
                    return data.drop("a", axis=1, level="S")

            It can only take one argument, `data`.
        aux_modifier_fcn: None, FunctionType
            A function to modify the auxiliary_data saved. See
            `data_modifier_fcn` for syntax.
        """
        fname = str(fname)
        data  = self.data
        aux   = self.aux

        if data_modifier_fcn is not None:
            from types import FunctionType
            if not isinstance(data_modifier_fcn, FunctionType):
                msg = ("`modifier_fcn` must be a FunctionType. "
                       "You passes '%s`.") % type(data_modifier_fcn)
                raise TypeError(msg)
            data = data_modifier_fcn(data)

        if aux_modifier_fcn is not None:
            from types import FunctionType
            if not isinstance(aux_modifier_fcn, FunctionType):
                msg = ("`modifier_fcn` must be a FunctionType. "
                       "You passes '%s`.") % type(aux_modifier_fcn)
                raise TypeError(msg)
            aux = aux_modifier_fcn(aux)

        # Recalculate "w_scalar" on load, so no need to save.
        data.drop("scalar", axis=1, level="C").to_hdf(fname, key=dkey)
        self.logger.info("data saved\n{:<5}  %s\n{:<5}  %s\n{:<5}  %s".format("file", "dkey", "shape"),
                         fname,
                         dkey,
                         data.shape
                        )

        aux.to_hdf(fname, key=akey)
        self.logger.info("aux saved\n{:<5}  %s\n{:<5}  %s\n{:<5}  %s".format("file", "akey", "shape"),
                         fname,
                         akey,
                         aux.shape
                        )

    @classmethod
    def load_from_file(cls, fname, *species, dkey="FC", akey="FC_AUX", **kwargs):
        r"""
        Load data from an HDF5 file at `fname` and create a plasma.

        Parameters
        ---------
        fname: str or pathlib.Path
            The file from which to load the data.
        species: list-like of str
            The species to load. If none are passed, they are automatically
            selected from the data.
        dkey: str, "FC"
            The key for getting data from HDF5 file.
        akey: str, "FC_AUX"
            key for getting auxiliary data from HDF5 file.
        kwargs:
            Passed to `Plasma.__init__`.
        """

        data = pd.read_hdf(fname, key=dkey)
        data.columns.names = ["M", "C", "S"]

        if not species:
            species = [s for s in data.columns.get_level_values("S").unique() if s]
        s_chk = [isinstance(s, str) for s in species]
        if not np.all(s_chk):
            msg = "Only string species are allowed. Default or passed species: {}.".format(s_chk)
            raise ValueError(msg)

        plasma = cls(data, *species, **kwargs)
        plasma.logger.info("Loaded plasma from file\nFile:  %s\n\ndkey:  %s", str(fname), dkey)

        if akey:
            aux = pd.read_hdf(fname, key=akey)
            aux.columns.names = ["M", "C", "S"]

            if not plasma.data.index.equals(aux.index):
                msg = "You cannot load auxiliary data with an index that does not equal the plasma index."
                raise ValueError(msg)

            plasma._auxiliary_data = aux
            plasma.logger.info("Loaded auxiliary_data from file\nFile:  %s\nakey:  %s", str(fname), akey)

        # Put a try-except statement here to log when no auxiliary data is loaded.

        return plasma

    def _set_species(self, *species):
        r"""
        Initialize `species` property to make overriding `set_data`
        easier.
        """
        species = self._clean_species_for_setting(*species)
        self._species = species
        self.logger.debug("%s init with species %s", self.__class__.__name__,  (species))

    def _chk_species(self, *species):
        r"""
        Check the species in each Plasma method call.
        """
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
            msg = ("Requested species unavailable.\n"
                   "Requested: %s\n"
                   "Available: %s\n"
                   "Unavailable: %s")
            # print(msg % (requested, available, unavailable), flush=True, end="\n")
            raise ValueError(msg % (requested, available, unavailable))
        return species

    @property
    def species(self):
        return self._species
    @property
    def ions(self):
        return self._ions
    def _set_ions(self):
        species = self.species
        if len(species) == 1:
            species = species[0].split(",")
        assert np.all(["+" not in s for s in species]), \
            "Plasma.species can't contain '+'."
        species = tuple(species)

        ions_         = pd.Series({s: ions.Ion(self.data, s) for s in species})
        self._ions    = ions_
        self._species = species

    def set_data(self, new):
        assert isinstance(new, pd.DataFrame)
        new = new.reorder_levels(["M", "C", "S"], axis=1).sort_index(axis=1)
        # new = new.sort_index(axis=1, inplace=True)
        assert new.columns.names == ["M", "C", "S"]

        # These are the only quantities we want in plasma.
        tk_plasma = pd.IndexSlice[["year", "fdoy", "gse", "b", "n", "v", "w"],
                                  ["", "x", "y", "z", "per", "par", "lat", "lon", "theta_rms", "mag_rms"],
                                  list(self.species) + [""],
                                 ]

        data = new.loc[:, tk_plasma].sort_index(axis=1)
        # We'll store this data in a secondary container.
        aux  = new.drop(data.columns, axis=1).sort_index(axis=1)

#        drop_species = new.columns.get_level_values("S").unique()
#        drop_species = [x for x in drop_species if x not in
#                        self.species and x != ""]
#        new = new.drop(drop_species, axis=1, level="S")
#
#        drop_errors = [k for k in new.columns if "err" in k[0]]
#        new = new.drop(drop_errors, axis=1)

        coeff = pd.Series({"per": 2.0, "par": 1.0}) / 3.0
        w    = data.w.drop("scalar",
                           axis=1,
                           level="C").pow(2).multiply(coeff,
                                                      axis=1,
                                                      level="C")
        # TODO: test `skipna=False` to ensure we don't accidentially create valid data
        #          where there is none.
        w = w.sum(axis=1, level="S", skipna=False).pipe(np.sqrt)
        w.columns = w.columns.to_series().apply(lambda x: ("w", "scalar", x))

        data = pd.concat([data,w,], axis=1)

        data.columns = self.mi_tuples(data.columns)
        data = data.sort_index(axis=1)

        # Because of subclassing, we call a __init__ a whole bunch,
        # so drop duplicates when added in by accident.
        data = data.loc[:, ~data.columns.duplicated()]

        self._data = data
        self.logger.debug("plasma shape: %s", data.shape)
        self._auxiliary_data = aux
        self.logger.debug("auxiliary data added to plasma\nshape: %s\ncolumns: %s",
                          aux.shape,
                          "\n    ".join([""] + [str(x) for x in aux.columns.values])
                          )

        self._bfield = vector.BField(data.b.xs("", axis=1, level="S"))
        # self._gse = GSE(new)

        nan_frame = data.isna()
        nan_info  = pd.DataFrame({"count": nan_frame.sum(axis=0),
                                  "mean": nan_frame.mean(axis=0)})
        # Log to DEBUG if no NaNs. Otherwise log to INFO.
        if nan_info.any().any():
            self.logger.info("%.0f spectra contain at least one NaN",
                              nan_info.any(axis=1).sum())
#             self.logger.log(10 * int(1 + nan_info.any().any()),
#                             "plasma NaN info\n%s", nan_info.to_string())
            self.logger.debug("plasma NaN info\n%s", nan_info.to_string())
        else:
            self.logger.debug("plasma does not contain NaNs")

        pct = [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99]
        stats = pd.concat({"lin": data.describe(percentiles=pct),
                           "log": data.pipe(np.log10).describe(percentiles=pct)},
                          axis=0).unstack(level=0).sort_index(axis=0).sort_index(axis=1).T
        self.logger.debug("plasma stats\n%s\n%s",
                           stats.loc[:, ["count", "mean", "std"]].to_string(),
                           stats.drop(["count", "mean", "std"], axis=1).to_string())

    @property
    def gse(self):
        return vector.Vector(self.data.gse.xs("", axis=1, level="S"))
    @property
    def bfield(self):
        return self._bfield
        #return vector.Vector(self.data.b.xs("", axis=1, level="S"))
    @property
    def b(self):
        r"""
        Shortcut for `bfield`.
        """
        return self.bfield
    def number_density(self, *species):
        r"""
        Get the ion number densities.
        """
        slist = self._chk_species(*species)
        n = self.data.n
        #print("<Module>",
        #      "<n>",
        #      type(n),
        #      n,
        #      sep="\n")
        if "C" in n.columns.names:
            n = n.xs("", axis=1, level="C")
        out = n.loc[:, slist[0] if len(slist) == 1 else slist]
        #print(
        #      "<xs(c)>",
        #      type(n),
        #      n,
        #      "<out>",
        #      type(out),
        #      out,
        #      "", sep="\n")
        return out
    def n(self, *species):
        r"""
        Shortcut to `number_density`.
        """
        return self.number_density(*species)

    def mass_density(self, *species):
        r"""
        Get the plasma mass densities.

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". If this is the case, the species are summed ovver and
            a pd.Series is returned. Otherwise, the individual quantities are
            returned as a pd.DataFrame.

        Returns
        -------
        rho: pd.Series or pd.DataFrame
            See Parameters for more info.
        """
        slist = self._chk_species(*species)

        rho = {s: self.ions.loc[s].rho for s in slist}
        rho = pd.concat(rho, axis=1, names=["S"]).sort_index(axis=1)

        if len(species) == 1:
            rho = rho.sum(axis=1)
            rho.name = species[0]
        return rho
    def rho(self, *species):
        r"""
        Shortcut to `mass_density` method.
        """
        return self.mass_density(*species)

    def pth(self, *species):
        r"""
        Get the thermal pressure.

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". If this is the case, the species are summed ovver and
            a pd.Series is returned. Otherwise, the individual quantities are
            returned as a pd.DataFrame.

        Returns
        -------
        pth: pd.Series or pd.DataFrame
            See Parameters for more info.
        """
        slist = self._chk_species(*species)
        include_dynamic=False
        if include_dynamic:
            raise NotImplementedError

        pth = {s: self.ions.loc[s].pth for s in slist}
        pth = pd.concat(pth, axis=1, names=["S"]).sort_index(axis=1)
        pth = pth.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)

        if len(species) == 1:
            pth = pth.sum(axis=1, level="C")
            # pth["S"] = species[0]
            # pth = pth.set_index("S", append=True).unstack()
            # pth = pth.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)
        return pth

    def temperature(self, *species):
        r"""
        Get the thermal temperature.

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". If this is the case, the species are summed ovver and
            a pd.Series is returned. Otherwise, the individual quantities are
            returned as a pd.DataFrame.

        Returns
        -------
        temp: pd.Series or pd.DataFrame
            See Parameters for more info.
        """
        slist = self._chk_species(*species)
        temp = {s: self.ions.loc[s].temperature for s in slist}
        temp = pd.concat(temp, axis=1, names=["S"]).sort_index(axis=1)
        temp = temp.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)

        if len(species) == 1:
            temp = temp.sum(axis=1, level="C")
            # temp["S"] = species[0]
            # temp = temp.set_index("S", append=True).unstack()
            # temp = temp.reorder_levels(["C", "S"], axis=1).sort_index(axis=1)
        return temp

    def beta(self, *species):
        r"""
        Get the plasma beta.

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". If this is the case, the species are summed ovver and
            a pd.Series is returned. Otherwise, the individual quantities are
            returned as a pd.DataFrame.

        Returns
        -------
        beta: pd.Series or pd.DataFrame
            See Parameters for more info.

        Derivation
        ----------
        In uncertain units, the NRL Plasma Formulary (2016) defined $\beta$:

            $\beta = 8 \pi n k_B T / B^2 = (2 k_b T / m) / (B^2 / 4 \phi \rho)$

        and the Alfven speed as:

            $C_A^2 = B^2 / 4 \pi \rho$.

        I define thermal speed as:

            $w^2 = 2 k_B T / m$.

        Combining these equations, we get:

            $\beta = w^2 / C_A^2$,

        which is independent of dimensional constants. Given I define $p_{th} = \rho w^2/2$ and
        $C_A^2 = B^2/\mu_0 \rho$ in SI units, I can rewrite $\beta$

            $\beta = (2 p_{th} / \rho) (\mu_0 \rho / B^2) = 2 \mu_0 p_{th}/B^2$.
        """
        slist = self._chk_species(*species)
        include_dynamic=False
        if include_dynamic:
            raise NotImplementedError

        pth  = self.pth(*species)
        bsq  = self.bfield.mag.pow(2)
        beta = pth.divide(bsq, axis=0)

        units  = self.units.pth / (self.units.b**2.0)
        coeff  = (2.0 * self.constants.misc.mu0 * units)
        beta  *= coeff
        return beta

    def anisotropy(self, *species):
        r"""
        Get the thermal temperature.

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". If this is the case, the species are summed ovver and
            a pd.Series is returned. Otherwise, the individual quantities are
            returned as a pd.DataFrame.

        Returns
        -------
        temperature: pd.Series or pd.DataFrame
            See Parameters for more info.
        """
        include_dynamic=False
        if include_dynamic:
            raise NotImplementedError

        pth = self.pth(*species).drop("scalar", axis=1)
        exp = pd.Series({"par": -1, "per": 1})

        if len(species) > 1:
        # if "S" in pth.columns.names:
            ani = pth.pow(exp, axis=1, level="C").product(axis=1, level="S")
        else:
            ani = pth.pow(exp, axis=1).product(axis=1)
            ani.name = species[0]

        return ani

    def velocity(self, *species):
        r"""
        Get the ion velocity or calculate the center of mass velocity.

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". If this is the case, the species are summed ovver and
            a pd.Series is returned. Otherwise, the individual quantities are
            returned as a pd.DataFrame.

        Returns
        -------
        velocity: pd.DataFrame
        """
        stuple = self._chk_species(*species)

        # print("", "<Module>", sep="\n")

        if len(stuple) == 1:
            # print("<Module.ion>")
            v = self.ions.loc[stuple[0]].velocity
        else:
            # print("<Module.sum>")
            v = self.ions.loc[list(stuple)].apply(lambda x: x.velocity)
            if len(species) == 1:
                rhos = self.mass_density(*stuple)
                v = pd.concat(v.apply(lambda x: x.cartesian).to_dict(),
                              axis=1, names=["S"])
                rv = v.multiply(rhos, axis=1, level="S").sum(axis=1, level="C")
                v = rv.divide(rhos.sum(axis=1),axis=0)
                v = vector.Vector(v)

        return v
    def v(self, *species):
        r"""
        Shortcut to `velocity`.
        """
        return self.velocity(*species)

    def dv(self, s0, s1):
        r"""
        Calculate the differential flow between species `s0` and
        species `s1`: $v_{s0} - v_{s1}$.

        Parameters
        ----------
        s0, s1: str
            If either species contains a "+", the center-of-mass velocity
            for the indicated species is used.
        Returns
        -------
        dv: vector.Vector

        See Also
        --------
        vector.Vector
        """
        if s0 == s1:
            msg = ("The differential flow between a species and itself "
                   "is identically zero.\ns0: %s\ns1: %s")
            raise NotImplementedError(msg % (s0, s1))

        v0 = self.velocity(s0)
        v1 = self.velocity(s1)

        dv = v0.cartesian.subtract(v1.cartesian)
        dv = vector.Vector(dv)

        return dv

    def pdynamic(self, *species):
        r"""
        Calculate the dynamic or drift pressure for the given species.

            $p_{\tilde{v}} = 0.5 \sum_i \rho_i (v_i - v_\mathrm{com})^2$

        Parameters
        ----------
        species: list-like of str
            List-like of individual species, e.g. ["a", "p1"].
            Can NOT be a list-like including sums, e.g. ["a", "p1+p2"].

        Returns
        -------
        pdv: pd.Series
            Dynamic pressure due to `species`.
        """
        stuple = self._chk_species(*species)
        if len(stuple) == 1:
            msg = "Must have >1 species to calculate dynamic pressure.\nRequested: {}"
            raise ValueError(msg.format(species))

        #pdb.set_trace()

        scom       = "+".join(species)
        const      = 0.5 * self.units.rho * (self.units.dv**2.0) / self.units.pth
        rho_i      = self.mass_density(*stuple)
        dv_i       = pd.concat({s: self.dv(s, scom).cartesian for s in stuple},
                               axis=1, names="S")
        dvsq_i     = dv_i.pow(2.0).sum(axis=1, level="S")
        dvsq_rho_i = dvsq_i.multiply(rho_i, axis=1, level="S")
        pdv        = dvsq_rho_i.sum(axis=1).multiply(const)
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
        #pdv = const * dv_i.pow(2.0).sum(axis=1,
        #                                level="S").multiply(rhi_i,
        #                                                    axis=1,
        #                                                    level="S").sum(axis=1)
        pdv.name = "pdynamic"

#        print(
#              "<dvsq_rho_i>", type(dvsq_rho_i), dvsq_rho_i,
#              "<pdv>", type(pdv), pdv,
#              sep="\n",
#              end="\n\n")

        return pdv

    def pdv(self, *species):
        r"""
        Shortcut to `pdynamic`.
        """
        return self.pdynamic(*species)

    def ca(self, *species):
        r"""
        Calculate the isotropic MHD Alfven speed.

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". If this is the case, the species are summed over and
            a pd.Series is returned. Otherwise, the individual quantities are
            returned as a pd.DataFrame.

        Returns
        -------
        ca: pd.DataFrame or pd.Series depending on `species` inputs.
        """
        stuple = self._chk_species(*species)

        rho = self.mass_density(*species)
        b = self.bfield.mag

        units = self.units
        mu0 = self.constants.misc.mu0
        coeff =  units.b / (np.sqrt(units.rho * mu0) * units.ca)
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
        r"""
        Calculate the square of anisotropy factor:

            $AF^2 = 1 + \frac{\mu_0}{B^s}\left(p_\perp - p_\parallel - p_{\tilde{v}}\right)$

        N.B. Because of the $1 +$, afsq(s0, s1).sum(axis=1) is not the
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
            calculating $p_{\tilde{v}}$.

        Returns
        -------
        afsq: pd.Series or pd.DataFrame depending on the len(species).
        """
        if pdynamic:
            raise NotImplementedError("Youngest beams analysis shows "
                "that dynamic pressure is probably not useful.")

        # The following is used to specifiy whether column levels
        # need to be aligned when multiple species are present.
        multi_species = len(species) > 1

        bsq = self.bfield.cartesian.pow(2.0).sum(axis=1)

        pth = self.pth(*species).drop("scalar", axis=1)
        sum_coeff = pd.Series({"per": 1, "par": -1})
        dp = pth.multiply(sum_coeff, axis=1, level="C" if multi_species else None)

        # The following level kwarg controls returning a DataFrame
        # of the various species or a single result for one species.
        # My guess is that following this line, we'd insert the subtraction
        # of the dynamic pressure with the appropriate alignment of the
        # species as necessary.
        dp = dp.sum(axis=1, level="S" if multi_species else None)

        mu0 = self.constants.misc.mu0
        coeff = mu0 * self.units.pth / (self.units.b**2.0)

        afsq = 1.0 + ( dp.divide(bsq, axis=0) * coeff )

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

            $C_{A;Ani} = C_A\sqrt{AFSQ}$

        Parameters
        ----------
        species: str
            Each species is a string. If only one string is passed, it can
            contain "+". In either case, all species are summed over and
            a pd.Series is returned. This addresses complications from the
tuple = self._chk_species(*species)
mass densities in Ca and AFSQ, the latter via pth.
        pydnamic: bool, str
            If str, the component of the dynamic pressure to use when
            calculating $p_{\tilde{v}}$.

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
        r"""
        Calculate the Coulomb logarithm between species s0 and s1.

            $\ln_\lambda_{i,i} = 29.9 - \ln(\frac{z_0 * z_1 * (a_0 + a_1)}{a_0 * T_1 + a_1 * T_0} \sqrt{\frac{n_0 z_0^2}{T_0} + \frac{n_1 z_1^2}{T_z}})$

        Parameters
        ----------
        species: str
            Each species is a string. It cannot be a sum of species,
            nor can it be an iterable of species.

        Returns
        -------
        lnlambda: pd.Series
            Only pd.Series is returned because Coulomb require
            species alignment in such a fashion that array
            operations using DataFrame alignment won't work.

        See Also
        --------
        nuc
        """
        s0 = self._chk_species(s0)
        s1 = self._chk_species(s1)

        if len(s0) > 1 or len(s1) > 1:
            msg = ("`lnlambda` can only calculate with individual s0 and "
                "s1 species.\ns0: %s\ns1: %s")
            raise ValueError(msg % (s0, s1))

        s0 = s0[0]
        s1 = s1[0]

        constants = self.constants
        units = self.units

        z = constants.charge_states.loc[sorted([s0, s1])]
        z0 = z.loc[s0]
        z1 = z.loc[s1]

        a0 = constants.m_amu.loc[s0]
        a1 = constants.m_amu.loc[s1]

        fcn = lambda x: x.n#.xs("", axis=1, level="C")
        n = pd.concat({s: self.ions.loc[s].n for s
                         in (s0, s1)}, axis=1, names=["S"]) * units.n

        T   = pd.concat({s: self.ions.loc[s].temperature.scalar for s
                         in (s0, s1)}, axis=1, names=["S"])
        TeV = T * units.temperature * constants.kb.eV

        kwargs = dict(axis=1, level="S")
        nZsqOTeV = n.multiply(z.pow(2.0), **kwargs).multiply(TeV.pow(-1.0),
            **kwargs)
        right = nZsqOTeV.sum(axis=1).pipe(np.sqrt)

        T0 = TeV.loc[:, s0]
        T1 = TeV.loc[:, s1]
        left = z0 * z1 * ( a0 + a1 ) / (a0 * T1).add(a1 * T0, axis=0)

        lnlambda = ( 29.9 - np.log( left * right ) ) / units.lnlambda
        lnlambda.name = "%s,%s" % ( s0, s1 )

        # print("",
        #       "<Module>",
        #       "<s0, s1>: %s, %s" % (s0, s1),
        #       "<Z>", type(z), z,
        #       "<ions>", type(self.ions), self.ions,
        #       "<n>", type(n), n,
        #       "<T>", type(T), T,
        #       "<T [eV]>", type(TeV), TeV,
        #       "<n Z^s / T [eV]>", type(nZsqOTeV), nZsqOTeV,
        #       "<sqrt( sum(n_i Z_i^s / T_i [eV]) )>", type(right), right,
        #       "<T0>", type(T0), T0,
        #       "<T1>", type(T1), T1,
        #       "<left>", type(left), left,
        #       "<lnlambda>", type(lnlambda), lnlambda,
        #       "<Module Done>",
        #       "",
        #       sep="\n")

        return lnlambda

    def nuc(self, sa, sb, both_species=True):
        r"""
        Calculate the momentum collision rate following Hernandez & Marsch
        (JGR 1985; doi:10.1029/JA090iA11p11062).

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
        """
        from scipy.special import erf

        sa = self._chk_species(sa)
        sb = self._chk_species(sb)

        if len(sa) > 1 or len(sb) > 1:
            msg = ("`nuc` can only calculate with individual `sa` and "
                "`sb` species.\nsa: %s\nsb: %s")
            raise ValueError(msg % (sa, sb))

        sa, sb = sa[0], sb[0]

        units = self.units
        constants = self.constants

        qabsq = constants.charges.loc[[sa, sb]].pow(2).product()
        ma = constants.m.loc[sa]
        masses = constants.m.loc[[sa, sb]]
        mu = masses.product()/masses.sum()
        coeff = qabsq / (4.0 * np.pi * constants.misc.e0**2.0 * ma * mu)

        lnlambda = self.lnlambda(sa, sb) * units.lnlambda
        nb = self.ions.loc[sb].n * units.n

        w = pd.concat({s: self.ions.loc[s].w.par for s in [sa, sb]},
                      axis=1)
        wab = w.pow(2.0).sum(axis=1).pipe(np.sqrt) * units.w

        dv = self.dv(sa, sb).magnitude * units.dv
        dvw = dv.divide(wab, axis=0)

        # longitudinal diffusion rate.
        ldr1 = erf(dvw)
        ldr2 = dvw.multiply((2.0/np.sqrt(np.pi)) * np.exp(-1*dvw.pow(2.0)), axis=0)
        ldr = dvw.pow(-3.0).multiply(ldr1.subtract(ldr2, axis=0), axis=0)

        nuab = coeff * nb.multiply(lnlambda,
                                   axis=0).multiply(ldr,
                                   axis=0).multiply(wab.pow(-3.0), axis=0)
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
            rho_ratio = pd.concat({s: self.mass_density(s) for s in [sa, sb]},
                                  axis=1)
            rho_ratio = rho_ratio.pow(exp, axis=1).product(axis=1)
            nuba = nuab.multiply(rho_ratio, axis=0)
            nu = nuab.add(nuba, axis=0)
            nu.name = "%s+%s" % (sa, sb)
            # print(
            #       "<rho_a/rho_b>", type(rho_ratio), rho_ratio,
            #       "<nuba>", type(nuba), nuba,
            #       sep="\n")
        else:
            nu = nuab
            nu.name = "%s-%s" % (sa, sb)

        # print(
        #       "<both_species> %s" % both_species,
        #       "<nu>", type(nu), nu,
        #       "",
        #       sep="\n")


        return nu


    def nc(self, sa, sb, both_species=True):
        r"""
        Calculate the Coulomb number between species `sa` and `sb`.

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
            msg = ("`nc` can only calculate with individual `sa` and "
                "`sb` species.\nsa: %s\nsb: %s")
            raise ValueError(msg % (sa, sb))

        sa, sb = sa[0], sb[0]

        r = constants.au - (self.gse.x * self.constants.misc.loc["Re [m]"])
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
        r"""
        Calculate the ratio of a Bimaxwellian proton beam to a Bimaxwellian proton
        core VDF at the peak beam velocity.

        To avoid overflow erros, we return ln(ratio).

        The VDF for species $i$ at velocity $v_j$ is:

            $f_i(v_j) = \frac{n_i}{(\pi w_i ^2)^{3/2}} \exp[ -(\frac{v_j - v_i}{w_i})^2]$

        The beam to core VDF ratio evaluated at the proton beam velocity is:

            $\frac{f_2}{f_1}|_{v_2} = \frac{n_2}{n_1} ( \frac{w_1}{w_2} )^3 \exp[ (\frac{v_2 - v_1}{w_1})^2 ]$

        where $n$ is the number density, $w$ gives the thermal speed, and $u$ is
        the bulk velocity.

        In the case of a Bimaxwellian, we $w^3 = w_\parallel w_\perp^2$ and
        $(\frac{v - v_i}{w_i})^2 = (\frac{v - v_i}{w_i})_\parallel^2 + (\frac{v - v_i}{w_i})_perp^2$.

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
        """

        n1 = self.xs(("n", "", core), axis=1)
        n2 = self.xs(("n", "", beam), axis=1)

        w = self.w.drop("scalar", axis=1, level="C")
        w1_par = w.par.p1
        w1_per = w.per.p1
        w2_par = w.par.p2
        w2_per = w.per.p2

        if beam == "a":
#             msg = "Based on a conversation with Justin, I'm not sure if we want to use this cut, so it's disabled."
            raise NotImplementedError

        # We calculate at the peak beam velocity, so we only need one dv.
        dv2 = self.dv(beam, core).project(self.b)

        # We're using a Bimaxwellian, so this should be sufficient.
        dv2_par = dv2.par
        dv2_per = dv2.per

        if beam == "p2":
            # BUG?
            # If Mike's code didn't properly subtract the y-GSE component
            # of the proton beam velocity due to the Earth's orbital motion
            # around the sun.
#             dvw = dv2_par.divide(w1_par, axis=0).pow(2)
            dvw = dv2.divide(w.xs(core, axis=1, level="S")).pow(2).sum(axis=1)
        elif beam == "a":
            w1.columns = w1.columns.get_level_values("Component")
            dvw = dv2.divide(w1, axis=1, level="C").pow(2).sum(axis=1)
        else:
            msg = "Unrecognizez beam: %s" % beam
            raise ValueError(msg)

        f2f1 = dvw#.pipe(np.exp)

        nbar = n2 / n1
        wbar = (w1_par / w2_par) * (w1_per / w2_per).pow(2)
        # f2f1 = nbar * wbar * f2f1
        f2f1 = np.log(nbar * wbar) + f2f1

        assert isinstance(f2f1, pd.Series)
        sbc = "%s/%s" % (beam, core)
        f2f1.name = sbc

        return f2f1

    @property
    def dt2ts(self):
        r"""
        Convert the (year, fdoy) data to a timestamp.

        Algorithm mostly copied from `space_plasma.tools.py`. (20171128T1435)
        """
        try:
            return self._ts
        except AttributeError:
            return self.calc_dt2ts()
    def calc_dt2ts(self):
        self.logger.debug("Calculating dt2ts")

        year = self.data.year.astype(int)
        fdoy = self.data.fdoy

        errors = "raise"
        # Subtract 1 b/c dates start at 1, but time deltas start at zero.
        dt = pd.to_timedelta(fdoy - 1.0, unit="D", errors=errors)
        yy = pd.to_datetime(year, format="%Y", errors=errors)
        ts = yy.add(dt, axis=0)
        ts.name = "timestamp"

        #print("<Module>",
        #      "<year>", type(year), year,
        #      "<fody>", type(fdoy), fdoy,
        #      "<dt>", type(dt), dt,
        #      "<yy>", type(yy), yy,
        #      "<ts>", type(ts), ts,
        #      "", sep="\n")
        self._ts = ts
        return ts

    @property
    def dt2jd(self):
        r"""
        Convet (year, fdoy) to Julian date.

        Notes
        -----
        Not tested in `test_plasma.py`.
        """
        try:
            return self._jd
        except AttributeError:
            return self.calc_dt2jd()
    def calc_dt2jd(self):
        self.logger.debug("Calculating dt2jd")
        yy = pd.to_datetime(self.data.year.astype(int), format="%Y", errors="raise")
        fd = self.data.fdoy

        jd = pd.DatetimeIndex(yy).to_julian_date()
        jd = pd.Series(jd.values, index=yy.index, name="jd")
        jd = jd.add(fd, axis=0)
        jd.name = "jd"
        self._jd = jd
        return jd

    def estimate_electrons(self, inplace=False):
        r"""
        Estimate the electron parameters.
        """

        species = self.species

        if "e" in species:
            msg = (r"Estimating electrons when there are e- in the data has been disabled because I've screwed it up and estimated them as zero b/c of various strange things. I need to disable `inplace` when `e` in speces and do some ther things for this to work.")
            raise NotImplementedError(msg)

        if "p" not in species and "p1" not in species:
            msg = ("Plasma must contain (core) protons to estimate electrons.\n"
                   "Available species: {}".format(species))
            raise ValueError(msg)
        elif "p" in species and "p1" in species:
            msg = ("Plasma cannot contain protons (p) and core protons (p1).\n"
                   "Available species: {}".format(species))
            raise ValueError(msg)
        elif "p" in species and "p1" not in species:
            tkw = "p"
            exp = pd.Series({"p": 1.0, "e": -1.0})
        elif "p" not in species and "p1" in species:
            tkw = "p1"
            exp = pd.Series({"p1": 1.0, "e": -1.0})
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
            vi = pd.concat(vi.apply(lambda x: x.cartesian).to_dict(), axis=1, names="S")
            niqi = ni.multiply(qi, axis=1, level="S")
            ne = niqi.sum(axis=1)
            niqivi = vi.multiply(niqi, axis=1, level="S").sum(axis=1, level="C")

        ve = niqivi.divide(ne, axis=0)

        wp   = self.w.scalar.loc[:, tkw]
        nrat = self.number_density(tkw).divide(ne, axis=0)
        mpme = self.constants.m_in_mp["e"]**-1
        we   = (nrat * mpme).multiply(wp.pow(2), axis=0).pipe(np.sqrt)
        we   = pd.concat([we, we], axis=1, keys=["par", "per"])

        ne.name = ""
        electrons = pd.concat([ne, ve, we], axis=1,
                                            keys=["n", "v", "w"],
                                            names=["M", "C"])
        mask = ~ne.astype(bool)
        electrons = electrons.mask(mask, axis=0)

        electrons = ions.Ion(electrons, "e")

        if inplace:
#             raise NotImplementedError("After adding `aux` to Plasma, this was not updated to account for it.")

            cols = electrons.data.columns
            cols = [x + ("e",) for x in cols.values]
            cols = pd.MultiIndex.from_tuples(cols, names=["M", "C", "S"])
            electrons.data.columns = cols

            data = self.data
#             data.update(electrons.data, join="outer")
#             if not data.columns.intersection(electrons.data.columns).size:
#                 species = sorted(self.species + ("e",))
#                 self.__set_species(*species)
#                 self._set_ions()

            if data.columns.intersection(electrons.data.columns).size:
                data.update(electrons.data)
            else:
                data = pd.concat([data,
                                  electrons.data,
                                  self.auxiliary_data], axis=1).sort_index(axis=1)
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
        r"""
        Calculate the parallel heat flux

            $Q_\parallel = \rho (v^3 + \frac{3/2}vw^2)$

        Parameters
        ----------
        species: list of strings
            The species to use. If a sum is indicated, take the sum
            of the input species.

        Returns
        -------
        q: pd.Series or pd.DataFrame
            Dimensionality depends on species inputs.
        """

        slist = self._chk_species(*species)
        rho = self.mass_density(*slist)
        v   = {s: self.v(s).project(self.b).par for s in slist}
        v   = pd.concat(v, axis=1, names=["S"]).sort_index(axis=1)
        v.columns.name = "S"
        w   = self.data.w.par.loc[:, slist]

        qa = v.pow(3)
        qb = v.multiply(w.pow(2), axis=1, level="S")

#        print("<Module>",
#              "<species> {}".format(species),
#              "<rho>", type(rho), rho,
#              "<v>", type(v), v,
#              "<w>", type(w), w,
#              "<qa>", type(qa), qa,
#              "<qb>", type(qb), qb,
#              sep="\n")

        qs = qa.add( (3./2.) * qb, axis=1, level="S").multiply(rho, axis=0)
        if len(species) == 1:
            qs = qs.sum(axis=1)
            qs.name = "+".join(species)

#        print("<qpar>", type(qs), qs,
#              sep="\n")

        coeff = self.units.rho * (self.units.v**3.0) / self.units.qpar
        q = coeff * qs
        return q

    def qpar(self, *species):
        r"""
        Shortcut to `heat_flux`.
        """
        return self.heat_flux(*species)

    # @property
    # def w(self):
    #     return self._w

    def build_alfvenic_turbulence(self, species, auto_reindex=True):
        raise NotImplementedError("Still working on module dev")
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
        auto_reindex: bool
            Passed to `AlfvenicTurbulence`. If True, reindex the input data
            such that it is a continuous, monotonic, and increasing
            `pd.Int64Index` so that `window` and `min_periods` rolling
            aggregation on spectrum number is roughly analagous to time.
        """
        species_ = species.split(",")

        auto_reindex = bool(auto_reindex)
        b = self.bfield.cartesian

        if len(species_) == 1:
            slist = self._chk_species(species_[0])
            v = self.velocity(species)
            r = self.mass_density(species)

        elif len(species_) == 2:
            slist0 = self._chk_species(species_[0])
            slist1 = self._chk_species(species_[1])

            s0 = "+".join(slist0)
            s1 = "+".join(slist1)
            v = self.dv(s0, s1)
            r  = self.mass_density(s1)

        else:
            msg = "`species` can only contain at most 1 comma\nspecies: %s"
            raise ValueError(msg % species)


        turb = alf_turb.AlfvenicTurbulence(v, b, r, species,
                                           auto_reindex=auto_reindex)


        return turb





















