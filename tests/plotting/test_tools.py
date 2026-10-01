#!/usr/bin/env python
"""Tests for ``solarwindpy.plotting.tools``.

Plots run on the Agg backend and assertions read what matplotlib holds: figure
sizes, axes positions, legend entries, saved files. Expected values come from
rcParams, hand computations, or hand-built frames.
The only fake is the clock that stamps saved PNGs.
"""

import logging
from datetime import datetime

import matplotlib

matplotlib.use("Agg")

import matplotlib.image as mpimg  # noqa: E402
import pytest  # noqa: E402
from matplotlib import pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402
from matplotlib.transforms import Bbox  # noqa: E402

from solarwindpy.plotting import tools as plotting_tools  # noqa: E402

CBAR_LOCS = ("top", "bottom", "left", "right")


@pytest.fixture(autouse=True)
def close_figures():
    """Close every figure a test opened."""
    yield
    plt.close("all")


def _pos(ax):
    """Axes position in figure coordinates, as (x0, y0, x1, y1)."""
    p = ax.get_position()
    return p.x0, p.y0, p.x1, p.y1


# ---------------------------------------------------------------------------
# subplots
# ---------------------------------------------------------------------------


class TestSubplots:
    """``subplots`` scales the per-panel size by the grid and the scale factors."""

    def test_figure_size_is_panel_size_times_grid_times_scale(self):
        """Width = base_w * scale_width * ncols; height = base_h * scale_height * nrows.

        Base (3, 2) from rcParams, 2x3 grid, scales (1.5, 0.5): (13.5, 2.0).
        ON FAILURE: the code is wrong.
        """
        with matplotlib.rc_context({"figure.figsize": (3.0, 2.0)}):
            fig, axes = plotting_tools.subplots(
                nrows=2, ncols=3, scale_width=1.5, scale_height=0.5
            )
        # rel 1e-12: products of exact binary fractions.
        assert fig.get_size_inches() == pytest.approx([13.5, 2.0], rel=1e-12, abs=0)
        assert axes.shape == (2, 3)

    def test_figsize_kwarg_is_the_per_panel_size(self):
        """A ``figsize`` kwarg replaces the rcParams base and is scaled by the grid.

        (10, 5) for a 1x2 grid gives a (20, 5) figure.
        ON FAILURE: the code is wrong, unless the author rejects figsize as a
        per-panel size (the docstring says kwargs pass straight to plt.subplots).
        """
        fig, axes = plotting_tools.subplots(nrows=1, ncols=2, figsize=(10, 5))
        # rel 1e-12: exact integers.
        assert fig.get_size_inches() == pytest.approx([20.0, 5.0], rel=1e-12, abs=0)

    def test_other_kwargs_reach_pyplot_subplots(self):
        """``sharex=True`` is forwarded: setting one panel's xlim sets them all.

        ON FAILURE: the code is wrong.
        """
        fig, axes = plotting_tools.subplots(nrows=2, ncols=2, sharex=True)
        axes[0, 0].set_xlim(-3, 7)
        for ax in axes.flat:
            assert ax.get_xlim() == (-3, 7)

    def test_single_panel_returns_one_axes(self):
        """A 1x1 grid returns a Figure and a single Axes, as plt.subplots does.

        ON FAILURE: the code is wrong.
        """
        fig, ax = plotting_tools.subplots()
        assert isinstance(fig, Figure)
        assert isinstance(ax, Axes)


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------


class _FixedDatetime(datetime):
    """A clock frozen at 2024-01-02T03:04:05."""

    @classmethod
    def now(cls, tz=None):
        return cls(2024, 1, 2, 3, 4, 5)


@pytest.fixture
def frozen_clock(monkeypatch):
    """Freeze the clock ``save`` reads for its PNG timestamp (clock boundary)."""
    monkeypatch.setattr(plotting_tools, "datetime", _FixedDatetime)


class TestSave:
    """``save`` writes PDF and PNG, stamps only the PNG, and forwards kwargs."""

    @pytest.mark.parametrize(
        "pdf, png", [(True, True), (True, False), (False, True), (False, False)]
    )
    def test_writes_exactly_the_requested_formats(self, tmp_path, pdf, png):
        """``pdf``/``png`` flags select which of ``<spath>.pdf``/``.png`` exist.

        ON FAILURE: the code is wrong.
        """
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 2])
        plotting_tools.save(fig, tmp_path / "fig", pdf=pdf, png=png, log=False)
        written = sorted(p.name for p in tmp_path.iterdir())
        expected = sorted(
            name for name, wanted in (("fig.pdf", pdf), ("fig.png", png)) if wanted
        )
        assert written == expected

    def test_axes_input_saves_its_figure_and_kwargs_reach_savefig(self, tmp_path):
        """An Axes saves its parent figure; ``dpi`` and ``bbox_inches`` pass through.

        A (2, 1) inch figure saved at dpi 50 with bbox_inches set to the whole
        figure (overriding save's default "tight") is 100 x 50 pixels.
        ON FAILURE: the code is wrong.
        """
        fig, ax = plt.subplots(figsize=(2.0, 1.0))
        plotting_tools.save(
            ax,
            tmp_path / "fig",
            pdf=False,
            add_info=False,
            log=False,
            dpi=50,
            bbox_inches=Bbox([[0.0, 0.0], [2.0, 1.0]]),
        )
        height, width = mpimg.imread(tmp_path / "fig.png").shape[:2]
        assert (width, height) == (100, 50)

    def test_png_is_stamped_with_the_save_time_at_info_xy(self, tmp_path, frozen_clock):
        """``add_info`` adds one figure text ending in the save time, at (info_x, info_y).

        The timestamp format is %Y%m%dT%H%M%S of the frozen clock. The name
        before it is attribution wording and is not asserted.
        ON FAILURE: the code is wrong.
        """
        fig, ax = plt.subplots()
        plotting_tools.save(
            fig, tmp_path / "fig", pdf=False, info_x=0.25, info_y=0.75, log=False
        )
        assert len(fig.texts) == 1
        stamp = fig.texts[0]
        assert stamp.get_text().endswith(" 20240102T030405")
        assert stamp.get_position() == (0.25, 0.75)

    @pytest.mark.parametrize(
        "kwargs",
        [dict(add_info=False), dict(add_info=True, png=False)],
        ids=["add_info=False", "pdf-only"],
    )
    def test_no_stamp_without_add_info_or_without_png(
        self, tmp_path, frozen_clock, kwargs
    ):
        """The stamp belongs to the PNG only; without a PNG or add_info, no text.

        ON FAILURE: the code is wrong.
        """
        fig, ax = plt.subplots()
        plotting_tools.save(fig, tmp_path / "fig", log=False, **kwargs)
        assert fig.texts == []

    def test_log_true_records_the_path_and_each_suffix(self, tmp_path, caplog):
        """With ``log=True`` INFO records name the resolved base path and each format.

        ON FAILURE: the code is wrong.
        """
        caplog.set_level(logging.INFO, logger=plotting_tools.__name__)
        fig, ax = plt.subplots()
        spath = tmp_path / "fig"
        plotting_tools.save(fig, spath, log=True)
        messages = [
            r.getMessage() for r in caplog.records if r.name == plotting_tools.__name__
        ]
        assert any(str(spath.resolve()) in m for m in messages)
        assert any(m.endswith("pdf") for m in messages)
        assert any(m.endswith("png") for m in messages)

    def test_log_false_records_nothing(self, tmp_path, caplog):
        """With ``log=False`` the module logger emits nothing.

        ON FAILURE: the code is wrong.
        """
        caplog.set_level(logging.DEBUG, logger=plotting_tools.__name__)
        fig, ax = plt.subplots()
        plotting_tools.save(fig, tmp_path / "fig", log=False)
        assert [r for r in caplog.records if r.name == plotting_tools.__name__] == []

    @pytest.mark.parametrize(
        "fig_arg, path_arg",
        [("figure", "not_a_path"), ("not_a_figure", "path")],
        ids=["str path", "non-figure"],
    )
    def test_rejects_a_non_path_or_a_non_figure(self, tmp_path, fig_arg, path_arg):
        """``spath`` must be a Path and ``fig`` a Figure or Axes; nothing is written.

        ON FAILURE: the code is wrong.
        """
        fig, ax = plt.subplots()
        fig_value = fig if fig_arg == "figure" else "not_a_figure"
        path_value = tmp_path / "fig" if path_arg == "path" else str(tmp_path / "f")
        with pytest.raises((AssertionError, TypeError)):
            plotting_tools.save(fig_value, path_value, log=False)
        assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------
# joint_legend
# ---------------------------------------------------------------------------


class TestJointLegend:
    """``joint_legend`` merges, deduplicates, sorts, and places one legend."""

    def test_labels_are_deduplicated_and_sorted(self):
        """Labels from every axes appear once each, in sorted order.

        ON FAILURE: the code is wrong.
        """
        fig, axes = plt.subplots(1, 3)
        axes[0].plot([0, 1], label="zeta")
        axes[0].plot([0, 1], label="alpha")
        axes[1].plot([0, 1], label="zeta")
        axes[2].plot([0, 1], label="mu")
        legend = plotting_tools.joint_legend(*axes)
        assert [t.get_text() for t in legend.get_texts()] == ["alpha", "mu", "zeta"]

    def test_first_occurrence_of_a_label_supplies_its_handle(self):
        """A duplicated label keeps the handle from the first axes it appears on.

        The two "same" lines differ in colour; the legend shows the first colour.
        ON FAILURE: the code is wrong.
        """
        fig, axes = plt.subplots(1, 2)
        axes[0].plot([0, 1], label="same", color="red")
        axes[1].plot([0, 1], label="same", color="blue")
        legend = plotting_tools.joint_legend(*axes)
        (handle,) = legend.legend_handles
        assert matplotlib.colors.same_color(handle.get_color(), "red")

    @pytest.mark.parametrize("idx, expected_idx", [(-1, 2), (0, 0), (1, 1)])
    def test_legend_is_placed_on_axes_idx_for_legend_only(self, idx, expected_idx):
        """The legend lives on ``axes[idx_for_legend]`` and no other axes.

        ON FAILURE: the code is wrong.
        """
        fig, axes = plt.subplots(1, 3)
        for i, ax in enumerate(axes):
            ax.plot([0, 1], label=f"line {i}")
        legend = plotting_tools.joint_legend(*axes, idx_for_legend=idx)
        for i, ax in enumerate(axes):
            assert (ax.get_legend() is legend) == (i == expected_idx)

    def test_default_location_anchors_lower_left_at_1p05_0p1(self):
        """By default the legend's lower-left corner sits at axes fraction (1.05, 0.1).

        That is just right of the host axes, per the docstring's idx=-1 note.
        ON FAILURE: the code is wrong.
        """
        fig, axes = plt.subplots(1, 2)
        axes[0].plot([0, 1], label="a")
        legend = plotting_tools.joint_legend(*axes)
        fig.canvas.draw()
        lb = legend.get_window_extent()
        ab = axes[1].get_window_extent()
        # abs 1e-9: display-coordinate arithmetic; a real misplacement is >= 1e-2.
        assert (lb.x0 - ab.x0) / ab.width == pytest.approx(1.05, abs=1e-9)
        assert (lb.y0 - ab.y0) / ab.height == pytest.approx(0.1, abs=1e-9)

    def test_kwargs_reach_axes_legend(self):
        """``loc`` overrides the default and other kwargs (``title``) are forwarded.

        ON FAILURE: the code is wrong.
        """
        fig, axes = plt.subplots(1, 2)
        axes[0].plot([0, 1], label="a")
        legend = plotting_tools.joint_legend(*axes, loc="upper left", title="T")
        fig.canvas.draw()
        lb = legend.get_window_extent()
        ab = axes[1].get_window_extent()
        assert ab.x0 <= lb.x0 < lb.x1 <= ab.x1
        assert legend.get_title().get_text() == "T"

    def test_errorbar_entry_is_drawn_as_its_data_line(self):
        """An errorbar container is represented by its line, without error bars.

        Matplotlib's own legend draws the bars as a LineCollection; the joint
        legend passes ``container[0]`` so no LineCollection appears.
        ON FAILURE: the code is wrong.
        """
        fig, axes = plt.subplots(1, 2)
        axes[0].errorbar([1, 2], [1, 2], yerr=[0.1, 0.2], label="err", color="C3")
        axes[1].plot([1, 2], [2, 1], label="line")
        legend = plotting_tools.joint_legend(*axes)
        assert [t.get_text() for t in legend.get_texts()] == ["err", "line"]
        assert not any(isinstance(a, LineCollection) for a in legend.findobj())
        err_handle = legend.legend_handles[0]
        assert matplotlib.colors.same_color(err_handle.get_color(), "C3")

    def test_fixture_matplotlib_legend_draws_errorbars(self):
        """The errorbar fixture above does separate the two behaviours.

        Matplotlib's plain ``ax.legend`` over the same errorbar contains a
        LineCollection, so its absence in the joint legend is informative.
        ON FAILURE: the fixture no longer separates a container handle from its
        data line; fix the fixture.
        """
        fig, ax = plt.subplots()
        ax.errorbar([1, 2], [1, 2], yerr=[0.1, 0.2], label="err")
        legend = ax.legend()
        assert any(isinstance(a, LineCollection) for a in legend.findobj())


# ---------------------------------------------------------------------------
# build_ax_array_with_common_colorbar
# ---------------------------------------------------------------------------


class TestBuildAxArrayWithCommonColorbar:
    """Grid of panels plus one colour-bar axes along a chosen side."""

    @pytest.mark.parametrize("cbar_loc", CBAR_LOCS)
    def test_panels_are_in_row_major_reading_order(self, cbar_loc):
        """``axes[i, j]`` is row i from the top, column j from the left.

        ON FAILURE: the code is wrong.
        """
        fig, axes, cax = plotting_tools.build_ax_array_with_common_colorbar(
            2, 3, cbar_loc=cbar_loc
        )
        assert axes.shape == (2, 3)
        for i in range(2):
            for j in range(2):
                assert _pos(axes[i, j])[0] < _pos(axes[i, j + 1])[0]
        for j in range(3):
            assert _pos(axes[0, j])[1] > _pos(axes[1, j])[1]

    @pytest.mark.parametrize("cbar_loc", CBAR_LOCS)
    def test_colorbar_is_on_the_named_side_of_every_panel(self, cbar_loc):
        """The colour bar lies entirely beyond every panel on the ``cbar_loc`` side.

        ON FAILURE: the code is wrong.
        """
        fig, axes, cax = plotting_tools.build_ax_array_with_common_colorbar(
            2, 2, cbar_loc=cbar_loc
        )
        cx0, cy0, cx1, cy1 = _pos(cax)
        for ax in axes.flat:
            x0, y0, x1, y1 = _pos(ax)
            beyond = {
                "right": cx0 > x1,
                "left": cx1 < x0,
                "top": cy0 > y1,
                "bottom": cy1 < y0,
            }
            assert beyond[cbar_loc]

    @pytest.mark.parametrize("cbar_loc", CBAR_LOCS)
    def test_colorbar_spans_the_whole_grid(self, cbar_loc):
        """The bar runs from the first to the last panel along its long side.

        ON FAILURE: the code is wrong.
        """
        fig, axes, cax = plotting_tools.build_ax_array_with_common_colorbar(
            3, 2, cbar_loc=cbar_loc
        )
        cx0, cy0, cx1, cy1 = _pos(cax)
        # rel 1e-12: gridspec boundaries from the same cumulative ratios.
        tol = dict(rel=1e-12, abs=1e-15)
        if cbar_loc in ("left", "right"):
            assert cy1 == pytest.approx(_pos(axes[0, 0])[3], **tol)
            assert cy0 == pytest.approx(_pos(axes[-1, 0])[1], **tol)
        else:
            assert cx0 == pytest.approx(_pos(axes[0, 0])[0], **tol)
            assert cx1 == pytest.approx(_pos(axes[0, -1])[2], **tol)

    @pytest.mark.parametrize(
        "cbar_loc, expected",
        [
            ("left", (3 * 3 * 1.3, 2 * 2)),
            ("right", (3 * 3 * 1.3, 2 * 2)),
            ("top", (3 * 3, 2 * 2 * 1.3)),
            ("bottom", (3 * 3, 2 * 2 * 1.3)),
        ],
    )
    def test_auto_figsize_scales_base_by_grid_and_adds_colorbar_room(
        self, cbar_loc, expected
    ):
        """Auto size = base * (ncols, nrows), times 1.3 along the colour-bar axis.

        Base (3, 2), 2 rows x 3 columns.
        ON FAILURE: the code is wrong.
        """
        with matplotlib.rc_context({"figure.figsize": (3.0, 2.0)}):
            fig, axes, cax = plotting_tools.build_ax_array_with_common_colorbar(
                2, 3, cbar_loc=cbar_loc
            )
        # rel 1e-12: float products.
        assert fig.get_size_inches() == pytest.approx(expected, rel=1e-12, abs=0)

    def test_explicit_figsize_and_fig_kwargs_are_used(self):
        """An explicit ``figsize`` is used as is; ``fig_kwargs`` reach plt.figure.

        ON FAILURE: the code is wrong.
        """
        fig, axes, cax = plotting_tools.build_ax_array_with_common_colorbar(
            3, 1, figsize=(5, 12), fig_kwargs={"dpi": 50}
        )
        assert tuple(fig.get_size_inches()) == (5, 12)
        assert fig.dpi == 50

    def test_gs_kwargs_reach_the_gridspec(self):
        """``gs_kwargs={"left": 0.2}`` puts the leftmost panel's edge at 0.2.

        ON FAILURE: the code is wrong.
        """
        fig, axes, cax = plotting_tools.build_ax_array_with_common_colorbar(
            2, 2, cbar_loc="right", gs_kwargs={"left": 0.2}
        )
        # rel 1e-12: gridspec stores the value directly.
        assert _pos(axes[0, 0])[0] == pytest.approx(0.2, rel=1e-12, abs=0)

    def test_hspace_and_wspace_set_the_gaps_between_panels(self):
        """Default spacing 0 makes panels touch; positive spacing opens a gap.

        ON FAILURE: the code is wrong.
        """
        fig, axes, cax = plotting_tools.build_ax_array_with_common_colorbar(2, 2)
        # abs 1e-12: adjacent gridspec cells share a boundary up to rounding.
        assert _pos(axes[0, 0])[1] == pytest.approx(_pos(axes[1, 0])[3], abs=1e-12)
        assert _pos(axes[0, 0])[2] == pytest.approx(_pos(axes[0, 1])[0], abs=1e-12)

        fig, axes, cax = plotting_tools.build_ax_array_with_common_colorbar(
            2, 2, hspace=0.5, wspace=0.5
        )
        assert _pos(axes[0, 0])[1] > _pos(axes[1, 0])[3]
        assert _pos(axes[0, 0])[2] < _pos(axes[0, 1])[0]

    @pytest.mark.parametrize(
        "sharex, sharey", [(True, True), (True, False), (False, True), (False, False)]
    )
    def test_sharex_and_sharey_link_limits_only_when_requested(self, sharex, sharey):
        """Setting limits on one panel moves the others iff that axis is shared.

        ON FAILURE: the code is wrong.
        """
        fig, axes, cax = plotting_tools.build_ax_array_with_common_colorbar(
            2, 2, sharex=sharex, sharey=sharey
        )
        for ax in axes.flat:
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
        axes[0, 0].set_xlim(-10, 10)
        axes[0, 0].set_ylim(-5, 5)
        for ax in axes.flat[1:]:
            assert (ax.get_xlim() == (-10, 10)) == sharex
            assert (ax.get_ylim() == (-5, 5)) == sharey

    @pytest.mark.parametrize(
        "cbar_loc, axis, side", [("top", "xaxis", "top"), ("left", "yaxis", "left")]
    )
    def test_colorbar_ticks_face_away_from_the_panels(self, cbar_loc, axis, side):
        """A top bar carries ticks and label on top; a left bar on the left.

        ON FAILURE: the code is wrong.
        """
        fig, axes, cax = plotting_tools.build_ax_array_with_common_colorbar(
            2, 2, cbar_loc=cbar_loc
        )
        long_axis = getattr(cax, axis)
        assert long_axis.get_ticks_position() == side
        assert long_axis.get_label_position() == side

    @pytest.mark.parametrize(
        "nrows, ncols, shape", [(1, 3, (3,)), (3, 1, (3,)), (2, 3, (2, 3))]
    )
    def test_degenerate_dimensions_are_squeezed(self, nrows, ncols, shape):
        """A single row or column comes back as a 1-D array of panels.

        ON FAILURE: the code is wrong.
        """
        fig, axes, cax = plotting_tools.build_ax_array_with_common_colorbar(
            nrows, ncols
        )
        assert axes.shape == shape
        assert all(isinstance(ax, Axes) for ax in axes.flat)
        assert isinstance(cax, Axes)

    def test_single_panel_is_returned_as_an_axes(self):
        """A 1x1 grid returns the panel itself, not a 0-d array.

        ON FAILURE: the code is wrong.
        """
        fig, ax, cax = plotting_tools.build_ax_array_with_common_colorbar(1, 1)
        assert isinstance(ax, Axes)
        assert ax is not cax

    def test_cbar_loc_is_case_insensitive(self):
        """``"RIGHT"`` places the bar as ``"right"`` does.

        ON FAILURE: the code is wrong.
        """
        fig, axes, cax = plotting_tools.build_ax_array_with_common_colorbar(
            2, 2, cbar_loc="RIGHT"
        )
        assert _pos(cax)[0] > max(_pos(ax)[2] for ax in axes.flat)

    def test_unknown_cbar_loc_raises_valueerror(self):
        """A location other than top/bottom/left/right is rejected.

        ON FAILURE: the code is wrong.
        """
        with pytest.raises(ValueError):
            plotting_tools.build_ax_array_with_common_colorbar(2, 2, cbar_loc="middle")
