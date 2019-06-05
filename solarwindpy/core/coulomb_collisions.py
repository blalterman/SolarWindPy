#!/usr/bin/env python
"""The Plasma class that contains all Ions, magnetic field, and spacecraft information.
"""
import pdb  # noqa: F401
import numpy as np
import pandas as pd

pd.set_option("mode.chained_assignment", "raise")

try:
    from . import base
    from . import plasma
except ImportError:
    import base
    import plasma


class CoulombCollisions(base.Core):
    def __init__(self, plasma):
        super(CoulombCollisions, self).__init__()
        self.set_plasma(plasma)

    @property
    def plasma(self):
        return self._plasma

    def set_plasma(self, new):
        if not isinstance(new, plasma.Plasma):
            raise TypeError
        self._plasma = plasma

    def lnlambda(self, s0, s1):
        r"""
        Calculate the Coulomb logarithm between species s0 and s1.

            :math:`\ln_\lambda_{i,i} = 29.9 - \ln(\frac{z_0 * z_1 * (a_0 + a_1)}{a_0 * T_1 + a_1 * T_0} \sqrt{\frac{n_0 z_0^2}{T_0} + \frac{n_1 z_1^2}{T_z}})`

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
        ions = self.plasma.ions

        z = constants.charge_states.loc[sorted(np.unique([s0, s1]))]
        z0 = z.loc[s0]
        z1 = z.loc[s1]

        a0 = constants.m_amu.loc[s0]
        a1 = constants.m_amu.loc[s1]

        #         fcn = lambda x: x.n  # .xs("", axis=1, level="C")
        n = (
            pd.concat({s: ions.loc[s].n for s in (s0, s1)}, axis=1, names=["S"])
            * units.n
        )

        T = pd.concat(
            {s: ions.loc[s].temperature.scalar for s in (s0, s1)}, axis=1, names=["S"]
        )
        TeV = T * units.temperature * constants.kb.eV

        kwargs = dict(axis=1, level="S")
        nZsqOTeV = n.multiply(z.pow(2.0), **kwargs).multiply(TeV.pow(-1.0), **kwargs)
        right = nZsqOTeV.sum(axis=1).pipe(np.sqrt)

        T0 = TeV.loc[:, s0]
        T1 = TeV.loc[:, s1]
        left = z0 * z1 * (a0 + a1) / (a0 * T1).add(a1 * T0, axis=0)

        lnlambda = (29.9 - np.log(left * right)) / units.lnlambda
        lnlambda.name = "%s,%s" % (s0, s1)

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

    def nuc_ii(self, s):
        r"""Calculate single species self-collision freuqncy following Eq. (45) in

        Fundamenski, W. & Garcia, O. E. Comparison of Coulomb Collision Rates in the
        Plasma Physics and Magnetically Confined Fusion Literature. (2007).
        """
        s = self._chk_species(s)
        assert len(s) == 1
        s = s[0]

        ions = self.plasma.ions

        q4 = self.constants.charges.loc[s] ** 4.0
        e0sq = self.constants.misc.loc["e0"] ** 2.0
        sqrtm = np.sqrt(self.constants.m.loc[s])
        coeff = q4 / (12.0 * (np.pi ** (3.0 / 2.0)) * sqrtm * e0sq)
        n = ions.loc[s].number_density * self.units.n
        temp = (
            ions.loc[s].temperature.par * self.units.temperature * self.constants.kb.eV
        )
        lnlambda = self.plasma.lnlambda(s, s) * self.units.lnlambda
        nuc = coeff * n.multiply(lnlambda, axis=0).divide(temp.pow(3.0 / 2.0), axis=0)
        return nuc

    def nuc_ij(self, sa, sb, both_species=True):
        r"""
        Calculate the two species momentum collision rate following Hernandez & Marsch
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
            msg = (
                "`nuc` can only calculate with individual `sa` and "
                "`sb` species.\nsa: %s\nsb: %s"
            )
            raise ValueError(msg % (sa, sb))

        sa, sb = sa[0], sb[0]

        units = self.units
        constants = self.constants
        plasma = self.plasma
        ions = plasma.ions

        qabsq = constants.charges.loc[[sa, sb]].pow(2).product()
        ma = constants.m.loc[sa]
        masses = constants.m.loc[[sa, sb]]
        mu = masses.product() / masses.sum()
        coeff = qabsq / (4.0 * np.pi * constants.misc.e0 ** 2.0 * ma * mu)

        lnlambda = self.plasma.lnlambda(sa, sb) * units.lnlambda
        nb = self.ions.loc[sb].n * units.n

        w = pd.concat({s: ions.loc[s].w.par for s in [sa, sb]}, axis=1)
        wab = w.pow(2.0).sum(axis=1).pipe(np.sqrt) * units.w

        dv = plasma.dv(sa, sb).magnitude * units.dv
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
                {s: ions.loc[s].mass_density for s in [sa, sb]}, axis=1
            )
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

    def nc_ij(self, sa, sb, both_species=True):
        r"""
        Calculate the two-species Coulomb number between species `sa` and `sb`.

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

        sc = self.plasma.spacecraft
        if sc is None:
            msg = "Plasma doesn't contain spacecraft data. Can't calculate Coulomb number."
            raise ValueError(msg)

        r = sc.distance2sun * self.units.distance2sun
        #         r = self.constants.misc.loc["1AU [m]"] - (
        #             self.gse.x * self.constants.misc.loc["Re [m]"]
        #         )
        vsw = self.plasma.velocity("+".join(self.species)).mag * self.units.v
        tau_exp = r.divide(vsw, axis=0)

        nuc = self.nuc_ij(sa, sb, both_species=both_species) * self.units.nuc

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
