# !/usr/bin/env python
__all__ = ["TeXinfo"]

r"""Extract information from :py:class:`solarwindpy.fitufunctions.FitFunction`
and render information in TeX format. Primary target is `matplotlib` annotation.
"""

import pdb  # noqa: F401
import re
import numpy as np
from numbers import Number

# Compile this once on import to save time.
_remove_exponential_pattern = r"e\+00+"  # Replace the `e+00`for 2 or more zeros.
_remove_exponential_pattern = re.compile(_remove_exponential_pattern)


class TeXinfo(object):
    def __init__(
        self, popt, psigma, TeX_function, chisq_dof, initial_guess_info=None, npts=None,
    ):
        r"""A container for printing :py:class:`FitFunction` info on a figure.

        Parameters
        ----------
        popt, psigma: dict
            Optimized fit parameters and their uncertainties.
        TeX_function: str
            TeX-formatted function for printing
        chisq_dof: scalar, None
            If not None, chisq per degree of freedom for the fit.
        initial_guess_info: dict, None
            If not None, a dict with keys corresponding to function arg names
            and values that are (p0, fit_bounds) for that fit parameter.
        npts: scalar, None
            If not None, the number of data points in the fit. If not None,
            cast to int.
        """
        self.set_popt_psigma(popt, psigma)
        self.set_TeX_function(TeX_function)
        self.set_chisq_dof(chisq_dof)
        self.set_initial_guess_info(initial_guess_info)
        self.set_npts(npts)

    def __str__(self):
        return self.info

    @property
    def info(self):
        try:
            return self._info
        except AttributeError:
            return self.build_info()

    @property
    def initial_guess_info(self):
        info = self._initial_guess_info
        if info is None:
            # Fit failed to make a guess
            return None

        translate = self.TeX_argnames
        if translate is not None:
            for k0, k1 in translate.items():
                info[k1] = info.pop(k0)

        #         info = [
        #             (
        #                 f"${k}$",
        #                 f"upper = {v.bounds[1]:.3e}",
        #                 f"guess = {v.p0:.3e}",
        #                 f"lower = {v.bounds[0]:.3e}",
        #             )
        #             for k, v in info.items()
        #         ]

        info = [
            (f"${k}$", f"{v.bounds[0]:.3e}  {v.p0:.3e}  {v.bounds[1]:.3e}")
            for k, v in info.items()
        ]

        info = ["\n".join(param) for param in info]
        info = "\n\n".join(info)

        return info

    @property
    def chisq_dof(self):
        return self._chisq_dof

    @property
    def npts(self):
        return self._npts

    @property
    def popt(self):
        return dict(self._popt)

    @property
    def psigma(self):
        return dict(self._psigma)

    @property
    def TeX_argnames(self):
        try:
            # Saved as tuple, so convert from tuple.
            return dict(self._TeX_argnames)

        except AttributeError:
            return None

    @property
    def TeX_function(self):
        return self._TeX_function

    @property
    def TeX_popt(self):
        r"""Create a dictionary with (k, v) pairs corresponding to
        (self.argnames, popt \pm psigma) with the appropriate uncertainty.

        See `set_TeX_trans_argnames` to translate the argnames for TeX.
        """
        psigma = self.psigma
        popt = self.popt.items()
        TeX_popt = {k: self.val_uncert_2_string(v, psigma[k]) for k, v in popt}

        translate = self.TeX_argnames
        if translate is not None:
            for k0, k1 in translate.items():
                TeX_popt[k1] = TeX_popt.pop(k0)

        return TeX_popt

    @property
    def TeX_relative_error(self):
        r"""Create a dictionary with (k, v) pairs corresponding to
        (self.argnames, psigma/popt).
        """
        psigma = self.psigma
        popt = self.popt
        TeX = {k: v / popt[k] for k, v in psigma.items()}

        translate = self.TeX_argnames
        if translate is not None:
            for k0, k1 in translate.items():
                TeX[k1] = TeX.pop(k0)

        return TeX

    @staticmethod
    def _check_and_add_math_escapes(x):
        r"""
        Add "$" math escapes to a string.

        This function can probably be turned into a
        static method.
        """
        assert isinstance(x, str)
        if not x.count("$"):
            x = r"$%s$" % x

        if x.count("$") % 2:
            msg = (
                "An even number of math escapes are necessary."
                " You have %s" % x.count("$")
            )
            raise ValueError(msg)

        return x

    @staticmethod
    def _calc_precision(value):
        r"""Primarily for use with the `val_uncert_2_string` and other methods
         that may require this.
         """
        # Convert the fractional part to an exponential string.
        # E.g. 0.0009865 -> 9.865000e-04
        precision = "%e" % value  # (value - int(value))

        # Split the exponential notation at the `e`,  a la
        # "1.250000e-04"; take the exponent "4", excluding the sign.
        precision = int(precision.partition("e")[2])

        return precision

    @staticmethod
    def _simplify_for_paper(info):
        text_info = []
        numeric_info = []
        for ii in info:
            ii = ii.strip("$")
            try:
                # (1) Right strip trailing zeros.
                # (2) Right strip trailing decimals.
                tmp = ii.replace(" ", "").split("=")
                ii = f"""{tmp[0]} = {str(float(tmp[1])).rstrip("0").rstrip(".")}"""
                numeric_info.append(ii)

            except ValueError:
                text_info.append(ii)

        all_info = text_info + numeric_info
        return all_info

    def _add_additional_info(self, info, additional_info):
        if additional_info is not None:
            if hasattr(additional_info, "__iter__") and not isinstance(
                additional_info, str
            ):
                for i, this_info in enumerate(additional_info):
                    additional_info[i] = self._check_and_add_math_escapes(this_info)

                additional_info = "\n".join(additional_info)
                additional_info = self._check_and_add_math_escapes(additional_info)

            if not isinstance(additional_info, str):
                raise TypeError("Additional info must be a string")

            combined_info = info + "\n" + additional_info
            return combined_info

    def _build_fit_parameter_info(
        self,
        chisq_dof=False,
        convert_pow_10=True,
        strip_uncertainties=False,
        simplify_info_for_paper=False,
        npts=False,
        relative_error=False,
    ):
        TeX_function = self.TeX_function
        TeX_popt = self.TeX_popt

        template = "%s = %s"
        info = [template % kv for kv in TeX_popt.items()]
        # `.split("\n")` guarantees function is a list, irrespecitve
        # of whether or not it contians 1 or more lines
        info = TeX_function.split("\n") + info

        #         pdb.set_trace()

        if relative_error:
            template = r"\Delta({0})/{0} = {1:.1e}"
            rel_err = self.TeX_relative_error
            rel_err = [template.format(k, v) for k, v in rel_err.items()]
            info += [""] + rel_err  # blank for visual cue

        if npts and self.npts is not None:
            info += [
                "",  # blank line for visual cue
                r"N_\mathrm{pts} = {%.0f}" % self.npts,
            ]

        if chisq_dof:
            #             info += [
            #                 "",  # blank line for visual cue
            #                 fr"\chi^2_\nu = {self.chisq_dof.linear:.2f}",
            #                 #                      r"\widehat{\chi}^2_\nu = {%.2f}" % self.chisq_dof.robust,
            #                 r"\chi^2_{\nu;R} = {%.2f}" % self.chisq_dof.robust,
            #             ]

            chisq_info = (
                r"\chi^2_\nu = {%.2f} \; \; \; \; \; \; \; \; \; \; \; \; \; \; \; \; \chi^2_{\nu;R} = {%.2f}"
                % (self.chisq_dof.linear, self.chisq_dof.robust)
            )
            if (not npts) or (self.npts is None):
                chisq_info = ["", chisq_info]  # blank line for visual cue
            #             info += [
            #                 "",  # blank line for visual cue
            #                 r"\chi^2_\nu = {%.2f} \; \; \; \; \; \; \; \; \; \; \; \; \chi^2_{\nu;R} = {%.2f}" % (self.chisq_dof.linear, self.chisq_dof.robust),
            #             ]
            else:
                chisq_info = [chisq_info]

            info += chisq_info

        if convert_pow_10 and (not simplify_info_for_paper):
            # Convert to 10^X notation.
            info = "\n".join(info)
            info, eplus_cnt = re.subn(r"e\+", r" \\times 10^{+", info)
            info, eminus_cnt = re.subn(r"e-", r" \\times 10^{-", info)

            # Conver +0X and -0X to +X and -X. Improves readability.
            info, p_sub_cnt = re.subn(r"\+0", r"+", info)
            info, m_sub_cnt = re.subn(r"\-0", r"-", info)

            # Re-split b/c we assume a lsit in all other pieces.
            info = info.split("\n")

            # Account for NaNs that don't have an exponential form to convert.
            # NaNs are present when a fit fails
            for idx, this_info in enumerate(info):
                this_info = [
                    x + "}" if x.count("{") > x.count("}") else x
                    for x in this_info.split(r"\pm")
                ]
                this_info = r"\pm".join(this_info)
                info[idx] = this_info

        if strip_uncertainties or simplify_info_for_paper:
            info = [x.split(r"\pm")[0] for x in info]

        if simplify_info_for_paper:
            info = self._simplify_for_paper(info)

        #             breakpoint()
        #             info = [f"$ {ii} $" for ii in (text_info + numeric_info)]
        #             info = "\n".join(info)

        #         print(*info, sep="\n")

        # IF statement to add blank lines for spacing chisq_nu and other stats.
        info = [r"$ %s $" % x.replace("$", "") if x else "\n" for x in info]
        info = "\n".join(info)

        info = info.replace(r"inf", r"\infty")

        return info

    #     @property
    #     def label(self):
    #         r"""The label for use when plotting.
    #         """
    #         # TODO: What is this? How do I use it?
    #         return self.fitfunction.function.func_name.title()

    def annotate_info(self, ax, **kwargs):
        r"""Add the `TeX_info` annotation to ax.

        Parameters
        ----------
        ax: mpl.Axes.axis_subplot

        bbox: dict
            dict(color="wheat", alpha=0.75)
        xloc, yloc: scalar
            0.05, 0.9
        ha, va: str
            ha - horizontalalignment (defaults "left")
            va - verticalalignment (default "right")
        transform:
            ax.transAxes
        kwargs:
            Others passed to `ax.text`.
        """
        info = self  # .info()

        bbox = kwargs.pop("bbox", dict(color="wheat", alpha=0.75))
        xloc = kwargs.pop("xloc", 0.05)
        yloc = kwargs.pop("yloc", 0.9)
        horizontalalignment = kwargs.pop("ha", "left")
        verticalalignment = kwargs.pop("va", "top")
        axtrans = kwargs.pop("transform", ax.transAxes)

        ax.text(
            xloc,
            yloc,
            info,
            bbox=bbox,
            horizontalalignment=horizontalalignment,
            verticalalignment=verticalalignment,
            transform=axtrans,
            **kwargs,
        )

    def build_info(
        self,
        **kwargs,
        #         chisq_dof=True,
        #         convert_pow_10=True,
        #         strip_uncertainties=False,
        #         simplify_info_for_paper=False,
        #         add_initial_guess=False,
        #         additional_info=None,
        #         annotate_fcn=None,
    ):
        r"""
        Generate a TeX-formatted string with the desired info

        Parameters
        ----------
        TeX_popt: dict
            :py:method:`FitFunction.TeX_popt` dictionary, which contains
            keys identifying the parameter and values their value.
        TeX_function: str
            :py:meth:`FitFunction.TeX_function` contents giving the functional
            form in TeX.
        chisq_dof: bool
            If True, include chisq/dof in the info. It is printed to 2 decimal
            places.
        relative_error: bool
            If True, print out relative error as :math:`\Delta(x)/x` for all
            fit parameters x.
        npts: bool
            If True, include the number of points in the fit.
        convert_pow_10: bool
            If True, use 10^{X} format. Otherwise, use eX format.
            Note that `simplify_info_for_paper` must be disabled.
        strip_uncertaintites: bool
            If True, strip fit uncertainties from reported parameters.
        simplify_info_for_paper: bool
            If True, simplify the printout to only print the quantities
            to their uncertainty in standard decimal (not expoential)
            notation.
            This option overrides `convert_pow_10`.
        add_initial_guess: dict, None
            If not None, a dict with keys corresponding to function arg names
            and values that are (p0, fit_bounds) for that fit parameter.
        additional_info: str or iterable of strings
            Additional info added to the fit info annotation box.
        annotate_fcn: FunctionType
           Function that manipulates the final TeX_info str before returning.
        """

        chisq_dof = kwargs.pop("chisq_dof", True)
        npts = kwargs.pop("npts", False)
        relative_error = kwargs.pop("relative_error", False)
        convert_pow_10 = kwargs.pop("convert_pow_10", True)
        strip_uncertainties = kwargs.pop("strip_uncertainties", False)
        simplify_info_for_paper = kwargs.pop("simplify_info_for_paper", False)
        add_initial_guess = kwargs.pop("add_initial_guess", False)
        additional_info = kwargs.pop("additional_info", None)
        annotate_fcn = kwargs.pop("annotate_fcn", None)

        if kwargs:
            raise ValueError(f"Unused kwargs {kwargs.keys()}")

        if np.all([np.isnan(v) for v in self.popt.values()]):
            info = f"${self.TeX_function}$\n\nFit Failed"

        else:
            info = self._build_fit_parameter_info(
                chisq_dof=chisq_dof,
                convert_pow_10=convert_pow_10,
                strip_uncertainties=strip_uncertainties,
                simplify_info_for_paper=simplify_info_for_paper,
                relative_error=relative_error,
                npts=npts,
            )

        if add_initial_guess:
            initial_guess = self.initial_guess_info
            if initial_guess is None:
                initial_guess = "\nInitial Guess Failed"
            else:
                initial_guess = "\n" + initial_guess

            info = self._add_additional_info(info, initial_guess)

        if additional_info is not None:
            info = self._add_additional_info(info, additional_info)

        if annotate_fcn is not None:
            info = annotate_fcn(info)

        self._info = info
        return info

    def set_initial_guess_info(self, new):
        if not (isinstance(new, dict) or new is None):
            raise TypeError(
                f"Unsure how to parse `initial_guess_info` of type {type(new)}"
            )

        self._initial_guess_info = new

    def set_npts(self, new):
        if not isinstance(new, Number) and (new is not None):
            raise TypeError(f"Unexpected npts type ({type(new)})")

        if new is not None:
            new = int(new)
        self._npts = new

    def set_popt_psigma(self, popt, psigma):
        for k in popt:
            if k not in psigma:
                raise ValueError(f"key ({k}) must be in both 'popt' and 'psigma' ")
        self._popt = popt.items()
        self._psigma = psigma.items()

    def set_TeX_argnames(self, **kwargs):
        r"""Define the mapping to format LaTeX function argnames.
        """
        # Save a tuple so immutable.
        popt = self.popt
        initial_guess = self.initial_guess_info
        for k, v in kwargs.items():
            if k not in popt:
                raise ValueError(
                    f"The TeX_argname {k} has no comparable pair in the popt"
                )

            if (initial_guess is not None) and k not in initial_guess:
                raise ValueError(
                    f"The TeX_argname {k} has no comparable pair in the initial_guess_info"
                )

        self._TeX_argnames = kwargs.items()

    def set_TeX_function(self, TeX_function):
        self._TeX_function = TeX_function

    def set_chisq_dof(self, new):
        self._chisq_dof = new

    def val_uncert_2_string(self, value, uncertainty):
        r"""
        Convert a value, uncertainty pair to a string in which the
        value is reported to the first non-zero digit of the uncertainty.

        Require that value > uncertainty.

        Example
        -------
        >>> a = 3.1415
        >>> b = 0.01
        >>> val_uncert_2_string(a, b)
        "3.14 \pm 0.01"
        """

        # if np.isfinite(uncertainty) and value <= uncertainty:
        #     msg = ("Must be that value > uncertainty\n"
        #            "value = %s\nuncertainty = %s")
        #     raise ValueError(msg % (value, uncertainty))

        vprecision = 3
        if np.isfinite(uncertainty):
            uprecision = self._calc_precision(uncertainty)
            vprecision = self._calc_precision(value)
            vprecision = vprecision - uprecision

        #         else:
        #             self.logger.warning(
        #                 "1-sigma fit uncertainty is %s.\nSetting to -3.", uncertainty
        #             )

        template = r"{:.%se} \pm {:.0e}"
        template = template % abs(vprecision)

        out = template.format(value, uncertainty)

        # Clean out unnecessary
        # pdb.set_trace()
        # out = re.subn(_remove_exponential_pattern, "", out)
        # out = out[0] # Drop the number of repetitions removed.
        # pdb.set_trace()
        return out
