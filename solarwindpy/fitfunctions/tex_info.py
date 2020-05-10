#!/usr/bin/env python
r"""Extract information from :py:class:`solarwindpy.fitufunctions.FitFunction`
and render information in TeX format. Primary target is `matplotlib` annotation.
"""

import pdb  # noqa: F401
import re

import numpy as np

# from collections import namedtuple
# from inspect import getargspec

# # Compile this once on import to save time.
_remove_exponential_pattern = r"e\+00+"  # Replace the `e+00`for 2 or more zeros.
_remove_exponential_pattern = re.compile(_remove_exponential_pattern)


class TeXinfo(object):
    def __init__(
        self, popt, psigma, TeX_function, chisq_dof,
    ):
        self.set_popt_psigma(popt, psigma)
        self.set_TeX_function(TeX_function)
        self.set_chisq_dof(chisq_dof)

    def __str__(self):
        return self.info

    @property
    def info(self):
        try:
            return self._info
        except AttributeError:
            return self.build_info()

    @property
    def chisq_dof(self):
        return self._chisq_dof

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

    #     @property
    #     def label(self):
    #         r"""The label for use when plotting.
    #         """
    #         # TODO: What is this? How do I use it?
    #         return self.fitfunction.function.func_name.title()

    #     @property
    #     def argnames(self):
    #         try:
    #             # Saved as tuple, so convert from tuple.
    #             return dict(self._argnames)
    #
    #         except AttributeError:
    #             return None

    #     @property
    #     def popt(self):
    #         r"""Create a dictionary with (k, v) pairs corresponding to
    #         (self.argnames, popt \pm psigma) with the appropriate uncertainty.
    #
    #         See `set_TeX_trans_argnames` to translate the argnames for TeX.
    #         """
    #         psigma = self.fitfunction.psigma
    #         popt = self.fitfunction.items()
    #         TeX_popt = {k: self.val_uncert_2_string(v, psigma[k]) for k, v in popt}
    #
    #         translate = self.TeX_argnames
    #         if translate is not None:
    #             for k0, k1 in translate.items():
    #                 TeX_popt[k1] = TeX_popt.pop(k0)
    #
    #         return TeX_popt

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
        chisq_dof=False,
        convert_pow_10=True,
        strip_uncertainties=False,
        simplify_info_for_paper=False,
        additional_info=None,
        annotate_fcn=None,
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
        chisq_dof: bool, scalar
            If True, include chisq/dof in the info. It is printed to 2 decimal
            places.
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
        additional_info: str or iterable of strings
            Additional info added to the fit info annotation box.
        annotate_fcn: FunctionType
           Function that manipulates the final TeX_info str before returning.
        """
        TeX_popt = self.TeX_popt
        TeX_function = self.TeX_function

        template = "%s = %s"
        info = [template % kv for kv in TeX_popt.items()]
        # `.split("\n")` guarantees function is a list, irrespecitve
        # of whether or not it contians 1 or more lines
        info = TeX_function.split("\n") + info

        if chisq_dof:
            info += [fr"\chi^2_\nu = {chisq_dof:.2f}"]

        if convert_pow_10 and (not simplify_info_for_paper):
            # Convert to 10^X notation.
            info = [x.replace(r"e+", r" \times 10^{+") for x in info]
            info = [x.replace(r"e-", r" \times 10^{-") for x in info]
            info = [x.replace(r" \pm", r"} \pm") + r"}" for x in info]

            # Join then re-split info b/c a single iterator is
            # easier than a loop of them.
            info = "\n".join(info)

            # Conver +0X and -0X to +X and -X.
            info, p_sub_cnt = re.subn(r"\+0", r"+", info)
            info, m_sub_cnt = re.subn(r"\-0", r"-", info)

            # Then re-split b/c we assume a lsit in all other pieces.
            info = info.split("\n")

        if strip_uncertainties or simplify_info_for_paper:
            info = [x.split(r"\pm")[0] for x in info]

        if simplify_info_for_paper:
            info = self._simplify_for_paper(info)

        #             breakpoint()
        #             info = [f"$ {ii} $" for ii in (text_info + numeric_info)]
        #             info = "\n".join(info)

        #         print(*info, sep="\n")
        info = [r"$ %s $" % x.replace("$", "") for x in info]
        info = "\n".join(info)

        info = info.replace(r"inf", r"\infty")

        if additional_info is not None:
            info = self._add_additional_info(info, additional_info)

        if annotate_fcn is not None:
            info = annotate_fcn(info)

        self._info = info
        return info

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
        for k, v in kwargs.items():
            if k not in self.popt:
                raise ValueError(
                    f"The TeX_argname {k} has no comparable pair in the popt"
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
