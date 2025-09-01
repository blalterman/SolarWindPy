#!/usr/bin/env python
r"""Spiral mesh plots and associated binning utilities."""

import pdb  # noqa: F401
import logging

import numpy as np
import pandas as pd
import matplotlib as mpl

from datetime import datetime
from numbers import Number
from collections import namedtuple
from numba import njit, prange

from matplotlib import pyplot as plt

from . import base
from . import labels as labels_module

InitialSpiralEdges = namedtuple("InitialSpiralEdges", "x,y")
# SpiralMeshData = namedtuple("SpiralMeshData", "x,y")
SpiralMeshBinID = namedtuple("SpiralMeshBinID", "id,fill,visited")
SpiralFilterThresholds = namedtuple(
    "SpiralFilterThresholds", "density,size", defaults=(False,)
)


@njit(parallel=True)
def get_counts_per_bin(bins, x, y):
    nbins = bins.shape[0]
    cell_count = np.full(nbins, 0, dtype=np.int64)

    for i in prange(nbins):
        x0, x1, y0, y1 = bins[i]
        left = x >= x0
        right = x < x1
        bottom = y >= y0
        top = y < y1
        chk_cell = left & right & bottom & top
        cell_count[i] = chk_cell.sum()

    return cell_count


@njit(parallel=True)
def calculate_bin_number_with_numba(mesh, x, y):
    fill = -9999
    zbin = np.full(x.size, fill, dtype=np.int64)

    nbins = mesh.shape[0]
    bin_visited = np.zeros(nbins, dtype=np.int64)
    for i in prange(nbins):
        x0, x1, y0, y1 = mesh[i]

        # Assume that largest x- and y-edges are extended by larger of 1% and 0.01
        # so that we can just naively use < instead of a special case of <=.
        # At time of writing (20200418), `SpiralPlot.initialize_mesh` did this.
        tk = (x >= x0) & (x < x1) & (y >= y0) & (y < y1)

        zbin[tk] = i
        bin_visited[i] += 1

    return zbin, fill, bin_visited


class SpiralMesh(object):
    def __init__(self, x, y, initial_xedges, initial_yedges, min_per_bin=250):
        self.set_data(x, y)
        self.set_min_per_bin(min_per_bin)
        self.set_initial_edges(initial_xedges, initial_yedges)
        self._cell_filter_thresholds = SpiralFilterThresholds(density=False, size=False)

    @property
    def bin_id(self):
        return self._bin_id

    @property
    def cat(self):
        r""":py:class:`pd.Categorical` version of `bin_id`, with fill bin removed."""
        return self._cat

    @property
    def data(self):
        return self._data

    @property
    def initial_edges(self):
        return self._initial_edges

    @property
    def mesh(self):
        return self._mesh

    @property
    def min_per_bin(self):
        return self._min_per_bin

    @property
    def cell_filter_thresholds(self):
        return self._cell_filter_thresholds

    @property
    def cell_filter(self):
        r"""Boolean :py:class:`Series` identifying properly filled mesh cells.

        Series selects mesh cells that meet density and area criteria specified
        by :py:meth:`mesh_cell_filter_thresholds`.

        Notes
        ----
        Neither `density` nor `size` convert log-scale edges into linear scale.
        Doing so would overweight the area of mesh cells at larger values on a
        given axis.
        """
        density = self.cell_filter_thresholds.density
        size = self.cell_filter_thresholds.size

        x = self.mesh[:, [0, 1]]
        y = self.mesh[:, [2, 3]]

        dx = x[:, 1] - x[:, 0]
        dy = y[:, 1] - y[:, 0]
        dA = dx * dy

        tk = np.full_like(dx, True, dtype=bool)
        if size:
            size_quantile = np.quantile(dA, size)
            tk_size = dA < size_quantile
            tk = tk & (tk_size)
        if density:
            cnt = np.bincount(self.bin_id.id, minlength=self.mesh.shape[0])
            assert cnt.shape == tk.shape
            cell_density = cnt / dA
            density_quantile = np.quantile(cell_density, density)
            tk_density = cell_density > density_quantile
            tk = tk & tk_density

        return tk

    def set_cell_filter_thresholds(self, **kwargs):
        r"""Set or update the :py:meth:`mesh_cell_filter_thresholds`.

        Parameters
        ----------
        density: scalar
            The density quantile above which we want to select bins, e.g.
            above the 0.01 quantile. This ensures that each bin meets some
            sufficient fill factor.
        size: scalar
            The size quantile below which we want to select bins, e.g.
            below the 0.99 quantile. This ensures that the bin isn't so large
            that it will appear as an outlier.
        """
        density = kwargs.pop("density", False)
        size = kwargs.pop("size", False)
        if len(kwargs.keys()):
            extra = "\n".join(["{}: {}".format(k, v) for k, v in kwargs.items()])
            raise KeyError("Unexpected kwarg\n{}".format(extra))

        self._cell_filter_thresholds = SpiralFilterThresholds(
            density=density, size=size
        )

    def set_initial_edges(self, xedges, yedges):
        self._initial_edges = InitialSpiralEdges(xedges, yedges)

    def set_data(self, x, y):
        data = pd.concat({"x": x, "y": y}, axis=1)
        self._data = data  # SpiralMeshData(x, y)

    def set_min_per_bin(self, new):
        self._min_per_bin = int(new)

    def initialize_bins(self):
        # Leaves initial edges altered when we change maximum edge.
        xbins = self.initial_edges.x
        ybins = self.initial_edges.y

        #         # Account for highest bin = 0 already done in `SpiralPlot2D.initialize_mesh`.
        #         xbins[-1] = np.max([0.01, 1.01 * xbins[-1]])
        #         ybins[-1] = np.max([0.01, 1.01 * ybins[-1]])

        left = xbins[:-1]
        right = xbins[1:]
        bottom = ybins[:-1]
        top = ybins[1:]

        nx = left.size
        ny = bottom.size

        mesh = np.full((nx * ny, 4), np.nan, dtype=np.float64)
        for x0, x1, i in zip(left, right, range(nx)):
            for y0, y1, j in zip(bottom, top, range(ny)):
                # NOTE: i*ny+j means go to i'th row, which has
                #       nrow * number of bins passed. Then go
                #       to j'th bin because we have to traverse
                #       to the j'th y-bin too.
                mesh[(i * ny) + j] = [x0, x1, y0, y1]

        mesh = np.array(mesh)

        #         pdb.set_trace()

        self.initial_mesh = np.array(mesh)
        return mesh

    @staticmethod
    def process_one_spiral_step(bins, x, y, min_per_bin):
        #         print("Processing spiral step", flush=True)
        #         start0 = datetime.now()
        cell_count = get_counts_per_bin(bins, x, y)

        bins_to_replace = cell_count > min_per_bin
        nbins_to_replace = bins_to_replace.sum()

        if not nbins_to_replace:
            return None, 0

        xhyh = 0.5 * (bins[:, [0, 2]] + bins[:, [1, 3]])

        def split_this_cell(idx):
            x0, x1, y0, y1 = bins[idx]
            xh, yh = xhyh[idx]

            # Reduce calls to `np.array`.
            # Just return a list here.
            split_cell = [
                [x0, xh, y0, yh],
                [xh, x1, y0, yh],
                [xh, x1, yh, y1],
                [x0, xh, yh, y1],
            ]

            return split_cell

        new_cells = bins_to_replace.sum() * [None]
        for i, idx in enumerate(np.where(bins_to_replace)[0]):
            new_cells[i] = split_this_cell(idx)

        new_cells = np.vstack(new_cells)

        bins[bins_to_replace] = np.nan

        #         stop = datetime.now()
        #         print(f"Done Building replacement grid cells (dt={stop-start1})", flush=True)
        #         print(f"Done Processing spiral step (dt={stop-start0})", flush=True)

        return new_cells, nbins_to_replace

    @staticmethod
    def _visualize_logged_stats(stats_str):
        from matplotlib import pyplot as plt

        stats = [[y.strip() for y in x.split("  ") if y] for x in stats_str.split("\n")]
        stats.pop(1)  # Remove column underline row
        stats = np.array(stats)
        index = pd.Index(stats[1:, 0].astype(int), name="Step")
        n_replaced = stats[1:, 1].astype(int)

        dt = pd.to_timedelta(stats[1:, 2]).total_seconds()
        dt_unit = "s"
        if dt.max() > 60:
            dt /= 60
            dt_unit = "m"
        if dt.max() > 60:
            dt /= 60
            dt_unit = "H"
        if dt.max() > 24:
            dt /= 24
            dt_unit = "D"

        dt_key = f"Elapsed [{dt_unit}]"
        stats = pd.DataFrame({dt_key: dt, "N Divisions": n_replaced}, index=index)

        #         stats = pd.Series(stats[1:, 1].astype(int), index=stats[1:, 0].astype(int), name=stats[0, 1])
        #         stats.index.name = stats[0, 0]

        fig, ax = plt.subplots()
        tax = ax.twinx()

        x = stats.index
        k = f"Elapsed [{dt_unit}]"
        ax.plot(x, stats.loc[:, k], label=k, marker="+", ms=8)

        k = "N Divisions"
        tax.plot(x, stats.loc[:, k], label=k, c="C1", ls="--", marker="x", ms=8)

        tax.grid(False)
        ax.set_xlabel("Step Number")
        ax.set_ylabel(dt_key)
        tax.set_ylabel("N Divisions")

        h0, l0 = ax.get_legend_handles_labels()
        h1, l1 = tax.get_legend_handles_labels()

        ax.legend(
            h0 + h1,
            l0 + l1,
            title=rf"$\Delta t = {stats.loc[:, dt_key].sum():.0f} \, {dt_unit}$",
        )

        ax.set_yscale("log")
        tax.set_yscale("log")

        return ax, tax, stats

    def generate_mesh(self):
        logger = logging.getLogger("__main__")
        start = datetime.now()
        logger.warning(f"Generating {self.__class__.__name__} at {start}")

        x = self.data.x.values
        y = self.data.y.values

        min_per_bin = self.min_per_bin
        #         max_bins = int(1e5)

        initial_bins = self.initialize_bins()

        # To reduce memory needs, only process data in mesh.
        x0 = initial_bins[:, 0].min()
        x1 = initial_bins[:, 1].max()
        y0 = initial_bins[:, 2].min()
        y1 = initial_bins[:, 3].max()
        tk_data_in_mesh = (
            (x0 <= x)
            & (x <= x1)
            & (y0 <= y)
            & (y <= y1)
            & np.isfinite(x)
            & np.isfinite(y)
        )
        x = x[tk_data_in_mesh]
        y = y[tk_data_in_mesh]

        initial_cell_count = get_counts_per_bin(initial_bins, x, y)
        #         initial_cell_count = self.get_counts_per_bin_loop(initial_bins, x, y)
        bins_to_replace = initial_cell_count > min_per_bin
        nbins_to_replace = bins_to_replace.sum()

        #         raise ValueError

        list_of_bins = [initial_bins]
        active_bins = initial_bins

        logger.warning(
            """
 Step      N      Elapsed Time
======  =======  =============="""
        )
        step_start = datetime.now()
        step = 0
        while nbins_to_replace > 0:
            active_bins, nbins_to_replace = self.process_one_spiral_step(
                active_bins, x, y, min_per_bin
            )
            now = datetime.now()
            #             if not(step % 10):
            logger.warning(f"{step:>6}  {nbins_to_replace:>7}  {(now - step_start)}")
            list_of_bins.append(active_bins)
            step += 1
            step_start = now

        list_of_bins = [b for b in list_of_bins if b is not None]
        final_bins = np.vstack(list_of_bins)
        valid_bins = np.isfinite(final_bins).all(axis=1)
        final_bins = final_bins[valid_bins]

        stop = datetime.now()
        #         logger.warning(f"Complete at {stop}")
        logger.warning(f"\nCompleted {self.__class__.__name__} at {stop}")
        logger.warning(f"Elasped time {stop - start}")
        logger.warning(f"Split bin threshold {min_per_bin}")
        logger.warning(
            f"Generated {final_bins.shape[0]} bins for {x.size} spectra (~{x.size / final_bins.shape[0]:.3f} spectra per bin)\n"
        )

        self._mesh = final_bins

    #         return final_bins

    def calculate_bin_number(self):
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Calculating {self.__class__.__name__} bin_number at {datetime.now()}"
        )
        x = self.data.loc[:, "x"].values
        y = self.data.loc[:, "y"].values
        mesh = self.mesh
        nbins = mesh.shape[0]

        start = datetime.now()
        zbin, fill, bin_visited = calculate_bin_number_with_numba(mesh, x, y)
        stop = datetime.now()

        logger.warning(f"Elapsed time {stop - start}")

        #         return calculate_bin_number_with_numba_broadcast(mesh, x, y, fill)

        #             if ( verbose > 0 and
        #                  (i % verbose == 0) ):
        #                     print(i+1, end=", ")

        if (zbin == fill).any():
            #         if (zbin < 0).any():
            #             pdb.set_trace()
            logger.warning(
                f"""`zbin` contains {(zbin == fill).sum()} ({100 * (zbin == fill).mean():.1f}%) fill values that are outside of mesh.
They will be replaced by NaNs and excluded from the aggregation.
"""
            )
            # raise ValueError(msg % (zbin == fill).sum())

        # Set fill bin to zero
        is_fill = zbin == fill
        #         zbin[~is_fill] += 1
        #         zbin[is_fill] = -1
        #         print(zbin.min())
        #         zbin += 1
        #         print(zbin.min())
        # `minlength=nbins` forces us to include empty bins at the end of the array.
        bin_frequency = np.bincount(zbin[~is_fill], minlength=nbins)
        n_empty = (bin_frequency == 0).sum()
        logger.warning(
            f"""Largest bin population is {bin_frequency.max()}
{n_empty} of {nbins} bins ({100 * n_empty / nbins:.1f}%) are empty
"""
        )

        if not bin_visited.all():
            logger.warning(f"{(~bin_visited).sum()} bins went unvisited.")
        if (bin_visited > 1).any():
            logger.warning(f"({(bin_visited > 1).sum()} bins visted more than once.")

        if nbins - bin_frequency.shape[0] != 0:
            raise ValueError(
                f"{nbins - bin_frequency.shape[0]} mesh cells do not have an associated z-value"
            )

        # zbin = _pd.Series(zbin, index=self.data.index, name="zbin")
        # # Pandas groupby will treat NaN as not belonging to a bin.
        # zbin.replace(fill, _np.nan, inplace=True)
        bin_id = SpiralMeshBinID(zbin, fill, bin_visited)
        self._bin_id = bin_id
        return bin_id

    def place_spectra_in_mesh(self):
        self.generate_mesh()
        bin_id = self.calculate_bin_number()
        return bin_id

    def build_cat(self):
        bin_id = self.bin_id.id
        fill = self.bin_id.fill

        # Integer number corresponds to the order over
        # which the mesh was traversed.
        cat = pd.Categorical(bin_id, ordered=False)
        if fill in bin_id:
            cat.remove_categories(fill, inplace=True)

        self._cat = cat


class SpiralPlot2D(base.PlotWithZdata, base.CbarMaker):
    r"""2D spiral plotting with adaptive mesh refinement.

    Examples
    --------
    splot = SpiralPlot2D(...)
    splot.initialize_mesh()
    """

    def __init__(
        self, x, y, z=None, logx=False, logy=False, initial_bins=5, clip_data=False
    ):
        super().__init__()
        self.set_log(x=logx, y=logy)
        self.set_data(x, y, z, clip_data)
        self.set_labels(x="x", y="y", z=labels_module.Count() if z is None else "z")
        self.calc_initial_bins(initial_bins)
        self.set_clim(None, None)

    @property
    def clim(self):
        return self._clim

    @property
    def initial_bins(self):
        return dict(self._initial_bins)

    @property
    def grouped(self):
        return self._grouped

    @property
    def mesh(self):
        return self._mesh

    def agg(self, fcn=None):
        r"""Aggregate the z-values into their bins."""
        self.logger.debug("aggregating z-data")

        #         start = datetime.now()
        #         self.logger.warning(f"Start {start}")

        if fcn is None:
            if self.data.loc[:, "z"].unique().size == 1:
                fcn = "count"
            else:
                fcn = "mean"

        gb = self.grouped
        agg = gb.agg(fcn)

        c0, c1 = self.clim
        if c0 is not None or c1 is not None:
            cnt = gb.agg("count")
            tk = pd.Series(True, index=agg.index)

            if c0 is not None:
                tk = tk & (cnt >= c0)
            if c1 is not None:
                tk = tk & (cnt <= c1)

            agg = agg.where(tk)

        # reindex to ensure we have a z-value for every bin.
        reindex = pd.RangeIndex(start=0, stop=self.mesh.mesh.shape[0], step=1)
        agg = agg.reindex(reindex)

        cell_filter = self.mesh.cell_filter
        if agg.shape != cell_filter.shape:
            raise ValueError(
                f"""Unable to algin `agg` and `cell_filter.
agg    : {agg.shape}
filter : {cell_filter.shape}"""
            )
        #         pdb.set_trace()
        agg = agg.where(cell_filter, axis=0)

        #         stop = datetime.now()
        #         self.logger.warning(f"Stop {stop}")
        #         self.logger.warning(f"Elapsed {stop - start}")

        return agg

    def build_grouped(self):
        cat = self.mesh.cat
        z = self.data.loc[:, "z"]

        if not (cat.size == z.size):
            raise ValueError(
                f"""`cat` must have same size as data's first dimesion
cat  : {cat.size}
data : {z.size}
"""
            )

        gb = z.groupby(cat)
        self._grouped = gb

    def calc_initial_bins(self, nbins):
        data = self.data
        keys = ("x", "y")
        bins = {}

        if isinstance(nbins, int):
            # Single paramter for `nbins`.
            nbins = {k: nbins for k in keys}

        elif len(nbins) == len(keys):
            # Passed one bin spec per axis
            nbins = {k: v for k, v in zip(keys, nbins)}

        else:
            msg = f"Unrecognized `nbins`\ntype: {type(nbins)}\n bins:{nbins}"
            raise ValueError(msg)

        for k, b in nbins.items():
            # Numpy and Astropy don't like NaNs when calculating bins.
            # Infinities in bins (typically from log10(0)) also create problems.
            d = data.loc[:, k].replace([-np.inf, np.inf], np.nan).dropna()

            if not isinstance(b, (int, np.ndarray)):
                raise TypeError("Only want in integer or np.ndarrays for initial edges")

            if isinstance(b, int):
                # Lets calculate the following quantiles.
                b = np.quantile(
                    d, np.linspace(0, 1, b + 1)
                )  # Need N + 1 edges to make N bins.

            # Extend the right most bin by the larger of 1% or 0.01 (in the case of zero)
            # So that y < y1 inludes data at real data edge.
            b[-1] = np.max([0.01, 1.01 * b.max()])

            assert not np.isnan(b).any()

            bins[k] = b

        bins = tuple(bins.items())
        self._initial_bins = bins
        return bins

    def initialize_mesh(self, **kwargs):
        x = self.data.loc[:, "x"]
        y = self.data.loc[:, "y"]

        #         if self.log.x:
        #             x = x.apply(np.log10)
        #         if self.log.y:
        #             y = y.apply(np.log10)

        xbins = self.initial_bins["x"]
        ybins = self.initial_bins["y"]

        mesh = SpiralMesh(x, y, xbins, ybins, **kwargs)
        # Attach mesh before anything else.
        # Makes debugging easier.
        self._mesh = mesh

        mesh.place_spectra_in_mesh()
        mesh.build_cat()

    def set_clim(self, lower=None, upper=None):
        """Set the min (lower) and max (upper) counts per bin.

        This limit is applied after the :py:meth:`groupby.agg` is run."""
        assert isinstance(lower, Number) or lower is None
        assert isinstance(upper, Number) or upper is None
        self._clim = base.RangeLimits(lower, upper)

    def set_data(self, x, y, z, clip):
        super().set_data(x, y, z, clip)
        data = self.data
        if self.log.x:
            data.loc[:, "x"] = np.log10(np.abs(data.loc[:, "x"]))
        if self.log.y:
            data.loc[:, "y"] = np.log10(np.abs(data.loc[:, "y"]))
        self._data = data

    def _limit_color_norm(self, norm):
        pct = self.data.loc[:, "z"].quantile([0.01, 0.99])
        v0 = pct.loc[0.01]
        v1 = pct.loc[0.99]
        if norm.vmin is None:
            norm.vmin = v0
        if norm.vmax is None:
            norm.vmax = v1
        norm.clip = True

    def make_plot(
        self,
        ax=None,
        cbar=True,
        limit_color_norm=False,
        cbar_kwargs=None,
        fcn=None,
        alpha_fcn=None,
        **kwargs,
    ):

        #         start = datetime.now()
        #         self.logger.warning("Making plot")
        #         self.logger.warning(f"Start {start}")

        if ax is None:
            fig, ax = plt.subplots()

        C = self.agg(fcn=fcn)
        C = np.ma.masked_invalid(C.values)
        assert isinstance(C, np.ndarray)
        assert C.ndim == 1
        if C.shape[0] != self.mesh.mesh.shape[0]:
            raise ValueError(
                f"""{self.mesh.mesh.shape[0] - C.shape[0]} mesh cells do not have a z-value associated with them. The z-values and mesh are not properly aligned."""
            )

        xmesh = self.mesh.mesh[:, [0, 1]]
        ymesh = self.mesh.mesh[:, [2, 3]]

        if self.log.x:
            xmesh = 10.0**xmesh
        if self.log.y:
            ymesh = 10.0**ymesh

        # (x,y) of bin's lower left corner.
        xy = zip(xmesh[:, 0], ymesh[:, 0])
        dx = xmesh[:, 1] - xmesh[:, 0]
        dy = ymesh[:, 1] - ymesh[:, 0]

        start1 = datetime.now()
        self.logger.warning("Making patches")
        self.logger.warning(f"Start {start1}")

        patches = [
            mpl.patches.Rectangle(this_xy, this_dx, this_dy)
            for this_xy, this_dx, this_dy in zip(xy, dx, dy)
        ]

        stop1 = datetime.now()
        self.logger.warning(f"Stop {stop1}")
        self.logger.warning(f"Elapsed {stop1 - start1}")

        # TODO: `match_original=False` if calculate alpha for each patch.
        edgecolors = "none"
        linewidth = 0.0
        collection = mpl.collections.PatchCollection(
            patches, linewidth=linewidth, edgecolors=edgecolors
        )

        collection.set_array(C)

        cmap = kwargs.pop("cmap", None)
        norm = kwargs.pop("norm", None)
        if len(kwargs):
            raise ValueError(f"Unexpected kwargs {kwargs.keys()}")
        #         assert not kwargs

        if limit_color_norm and norm is not None:
            self._limit_color_norm(norm)

        collection.set_alpha(None)
        collection.set_cmap(cmap)
        collection.set_norm(norm)
        collection.autoscale_None()

        ax.add_collection(collection, autolim=False)

        minx = xmesh[:, 0].min()
        miny = ymesh[:, 0].min()
        maxx = xmesh[:, 1].max()
        maxy = ymesh[:, 1].max()
        collection.sticky_edges.x[:] = [minx, maxx]
        collection.sticky_edges.y[:] = [miny, maxy]
        corners = (minx, miny), (maxx, maxy)
        ax.update_datalim(corners)
        ax.autoscale_view()

        cbar_or_mappable = collection
        if cbar:
            if cbar_kwargs is None:
                cbar_kwargs = dict()

            if "cax" not in cbar_kwargs.keys() and "ax" not in cbar_kwargs.keys():
                cbar_kwargs["ax"] = ax

            cbar = self._make_cbar(collection, norm=norm, **cbar_kwargs)
            cbar_or_mappable = cbar

        self._format_axis(ax)

        if alpha_fcn is not None:
            alpha_agg = np.ma.masked_invalid(self.agg(fcn=alpha_fcn).values)
            # Feature scale then invert so smallest STD
            # is most opaque.
            alpha_agg = mpl.colors.Normalize()(alpha_agg)
            alpha = 1 - alpha_agg
            self.logger.warning("Scaling alpha filter as alpha**0.25")
            alpha = alpha**0.25

            # Set masked values to zero. Otherwise, masked
            # values are rendered as black.
            alpha = alpha.filled(0)

            # Must draw to initialize `facecolor`s
            plt.draw()
            colors = collection.get_facecolors()
            colors[:, 3] = alpha
            collection.set_facecolor(colors)

        #         stop = datetime.now()
        #         self.logger.warning(f"Stop {stop}")
        #         self.logger.warning(f"Elapsed {stop - start}")

        return ax, cbar_or_mappable

    def _verify_contour_passthrough_kwargs(
        self, ax, clabel_kwargs, edges_kwargs, cbar_kwargs
    ):
        if clabel_kwargs is None:
            clabel_kwargs = dict()
        if edges_kwargs is None:
            edges_kwargs = dict()
        if cbar_kwargs is None:
            cbar_kwargs = dict()
        if "cax" not in cbar_kwargs.keys() and "ax" not in cbar_kwargs.keys():
            cbar_kwargs["ax"] = ax

        return clabel_kwargs, edges_kwargs, cbar_kwargs

    def plot_contours(
        self,
        ax=None,
        label_levels=True,
        cbar=True,
        limit_color_norm=False,
        cbar_kwargs=None,
        fcn=None,
        plot_edges=False,
        edges_kwargs=None,
        clabel_kwargs=None,
        skip_max_clbl=True,
        use_contourf=False,
        #         gaussian_filter_std=0,
        #         gaussian_filter_kwargs=None,
        **kwargs,
    ):
        """Make a contour plot on `ax` using `ax.contour`.

        Parameters
        ----------
        ax: mpl.axes.Axes, None
            If None, create an `Axes` instance from `plt.subplots`.
        label_levels: bool
            If True, add labels to contours with `ax.clabel`.
        cbar: bool
            If True, create color bar with `labels.z`.
        limit_color_norm: bool
            If True, limit the color range to 0.001 and 0.999 percentile range
            of the z-value, count or otherwise.
        cbar_kwargs: dict, None
            If not None, kwargs passed to `self._make_cbar`.
        fcn: FunctionType, None
            Aggregation function. If None, automatically select in :py:meth:`agg`.
        plot_edges: bool
            If True, plot the smoothed, extreme edges of the 2D histogram.
        clabel_kwargs: None, dict
            If not None, dictionary of kwargs passed to `ax.clabel`.
        skip_max_clbl: bool
            If True, don't label the maximum contour. Primarily used when the maximum
            contour is, effectively, a point.
        maximum_color:
            The color for the maximum of the PDF.
        use_contourf: bool
            If True, use `ax.contourf`. Else use `ax.contour`.
        gaussian_filter_std: int
            If > 0, apply `scipy.ndimage.gaussian_filter` to the z-values using the
            standard deviation specified by `gaussian_filter_std`.
        gaussian_filter_kwargs: None, dict
            If not None and gaussian_filter_std > 0, passed to :py:meth:`scipy.ndimage.gaussian_filter`
        kwargs:
            Passed to :py:meth:`ax.pcolormesh`.
            If row or column normalized data, `norm` defaults to `mpl.colors.Normalize(0, 1)`.
        """
        levels = kwargs.pop("levels", None)
        cmap = kwargs.pop("cmap", None)
        norm = kwargs.pop(
            "norm",
            None,
            #             mpl.colors.BoundaryNorm(np.linspace(0, 1, 11), 256, clip=True)
            #             if self.axnorm in ("c", "r")
            #             else None,
        )
        linestyles = kwargs.pop(
            "linestyles",
            [
                "-",
                ":",
                "--",
                (0, (7, 3, 1, 3, 1, 3, 1, 3, 1, 3)),
                "--",
                ":",
                "-",
                (0, (7, 3, 1, 3, 1, 3)),
            ],
        )

        if ax is None:
            fig, ax = plt.subplots()

        (
            clabel_kwargs,
            edges_kwargs,
            cbar_kwargs,
        ) = self._verify_contour_passthrough_kwargs(
            ax, clabel_kwargs, edges_kwargs, cbar_kwargs
        )

        inline = clabel_kwargs.pop("inline", True)
        inline_spacing = clabel_kwargs.pop("inline_spacing", -3)
        fmt = clabel_kwargs.pop("fmt", "%s")

        if ax is None:
            fig, ax = plt.subplots()

        C = self.agg(fcn=fcn).values
        assert isinstance(C, np.ndarray)
        assert C.ndim == 1
        if C.shape[0] != self.mesh.mesh.shape[0]:
            raise ValueError(
                f"""{self.mesh.mesh.shape[0] - C.shape[0]} mesh cells do not have a z-value associated with them. The z-values and mesh are not properly aligned."""
            )

        x = self.mesh.mesh[:, [0, 1]].mean(axis=1)
        y = self.mesh.mesh[:, [2, 3]].mean(axis=1)

        if self.log.x:
            x = 10.0**x
        if self.log.y:
            y = 10.0**y

        tk_finite = np.isfinite(C)
        x = x[tk_finite]
        y = y[tk_finite]
        C = C[tk_finite]

        contour_fcn = ax.tricontour
        if use_contourf:
            contour_fcn = ax.tricontourf

        if levels is None:
            args = [x, y, C]
        else:
            args = [x, y, C, levels]

        qset = contour_fcn(*args, linestyles=linestyles, cmap=cmap, norm=norm, **kwargs)

        try:
            args = (qset, levels[:-1] if skip_max_clbl else levels)
        except TypeError:
            # None can't be subscripted.
            args = (qset,)

        class nf(float):
            # Source: https://matplotlib.org/3.1.0/gallery/images_contours_and_fields/contour_label_demo.html
            # Define a class that forces representation of float to look a certain way
            # This remove trailing zero so '1.0' becomes '1'
            def __repr__(self):
                return str(self).rstrip("0")

        lbls = None
        if label_levels:
            qset.levels = [nf(level) for level in qset.levels]
            lbls = ax.clabel(
                *args,
                inline=inline,
                inline_spacing=inline_spacing,
                fmt=fmt,
                **clabel_kwargs,
            )

        cbar_or_mappable = qset
        if cbar:
            # Pass `norm` to `self._make_cbar` so that we can choose the ticks to use.
            cbar = self._make_cbar(qset, norm=norm, **cbar_kwargs)
            cbar_or_mappable = cbar

        self._format_axis(ax)

        return ax, lbls, cbar_or_mappable, qset


#    def plot_surface(self):
#
#        from scipy.interpolate import griddata
#
#        z = self.agg()
#        x = self.mesh.mesh[:, [0, 1]].mean(axis=1)
#        y = self.mesh.mesh[:, [2, 3]].mean(axis=1)
#
#        is_finite = np.isfinite(z)
#        z = z[is_finite]
#        x = x[is_finite]
#        y = y[is_finite]
#
#        xi = np.linspace(x.min(), x.max(), 100)
#        yi = np.linspace(y.min(), y.max(), 100)
#        # VERY IMPORTANT, to tell matplotlib how is your data organized
#        zi = griddata((x, y), y, (xi[None, :], yi[:, None]), method="cubic")
#
#        if ax is None:
#            fig = plt.figure(figsize=(8, 8))
#            ax = fig.add_subplot(projection="3d")
#
#        xig, yig = np.meshgrid(xi, yi)
#
#        ax.plot_surface(xx, yy, zz, cmap="Spectral_r", norm=chavp.norms.vsw)
