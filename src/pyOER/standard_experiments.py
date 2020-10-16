import numpy as np
from matplotlib import gridspec, pyplot as plt

from .measurement import Measurement
from EC_MS import Molecule
from .calibration import CalibrationSeries

STANDARD_ALPHA = 0.9980  # the natural ratio ^{16}O/(^{16}O + ^{18}O) in oxygen

calibration_series = CalibrationSeries.load()


class StandardExperiment:
    def __init__(
        self,
        m_id,
        tspan_plot=None,
        F=None,
        alpha=None,
        tspan_bg=None,
        tspan_F=None,
        tspan_alpha=None,
        plot_specs=None,
        **kwargs,
    ):

        self.measurement = Measurement.open(m_id)
        self.dataset = self.measurement.dataset
        self.dataset.sync_metadata(
            RE_vs_RHE=self.measurement.RE_vs_RHE, A_el=0.196,
        )
        self.tspan_plot = tspan_plot
        if tspan_bg:
            self.dataset.set_background(tspan_bg)
        self.tspan_F = tspan_F
        if tspan_F:
            F = self.dataset.point_calibration(
                mol="O2", mass="M32", n_el=4, tspan=tspan_F,
            )
        self.F = F or calibration_series.F_of_tstamp(self.dataset.tstamp)
        self.mdict = {}
        self.populate_mdict()
        self.tspan_alpha = tspan_alpha
        if tspan_alpha:
            alpha = self.calc_alpha()
        self.alpha = alpha or STANDARD_ALPHA
        self._icpms_points = None
        self.plot_specs = plot_specs or {}
        self.extra_stuff = kwargs

    def calc_alpha(self, tspan=None):
        """Return fraction ^{16}O in the electrolyte based on tspan with steady OER"""
        tspan = tspan or self.tspan_alpha
        x_32, y_32 = self.dataset.get_signal(mass="M32", tspan=tspan)
        x_34, y_34 = self.dataset.get_signal(mass="M34", tspan=tspan)
        gamma = np.mean(y_34) / np.mean(y_32)
        alpha = 2 / (2 + gamma)
        return alpha

    @property
    def beta(self):
        return 2 * (1 - self.alpha) / self.alpha

    @property
    def icpms_points(self):
        if not self._icpms_points:
            self._icpms_points = self.measurement.get_icpms_points()
        return self._icpms_points

    def populate_mdict(self):
        for mass in ["M32", "M34", "M36"]:
            m = Molecule("O2")
            m.primary = mass
            m.F_mat = None
            m.F_cal = self.F
            self.mdict[f"O2_{mass}"] = m

    def get_dissolution_points(self):
        icpms_points = self.icpms_points
        t_vec = np.array([icpms_point.sampling_time for icpms_point in icpms_points])
        n_vec = np.array([icpms_point.amount for icpms_point in icpms_points])
        return t_vec, n_vec

    def get_dissolution_rates(self):
        t_points, n_points = self.get_dissolution_points()
        t_last = 0
        t_vec = np.array([])
        n_dot_vec = np.array([])
        for t, n, in zip(t_points, n_points):
            if t == 0:
                continue
            if t == t_last:
                input(f"Waring! {self.measurement} has two ICPMS samples at t={t}.")
                continue
            t_vec = np.append(t_vec, t)
            n_dot = n / (t - t_last)
            n_dot_vec = np.append(n_dot_vec, n_dot)
            t_last = t
        return t_vec, n_dot_vec

    def get_dissolution_differential(self, tspan=None):
        """Return t, n_dot for plotting the dissolution rate over tspan"""
        t_vec, n_dot_vec = self.get_dissolution_rates()
        t_diff = np.array([tspan[0] if tspan else 0])
        n_dot_diff = np.array([])
        # t_diff is one longer than n_dot_diff
        for t, n_dot in zip(t_vec, n_dot_vec):
            t_diff = np.append(t_diff, np.array([t, t]))
            n_dot_diff = np.append(n_dot_diff, np.array([n_dot, n_dot]))
            if tspan and t > tspan[-1]:
                break
        t_diff = t_diff[:-1]
        if tspan:
            t_diff[-1] = tspan[-1]
        return t_diff, n_dot_diff

    def plot_EC_MS_ICPMS(
        self, tspan=None, highlight=True, showsamples=True, ylims=None
    ):
        """Make a 3-panel plot showing EC-MS data with ICPMS samples

        Args:
            tspan (list of float): The timespan for which to plot. Defaults to
                self.tspan_plot, or finally to the dataset's tspan.
            highlight (bool): Whether to highlight the excess 18-O.
            showsamples (bool): Whether to draw vertical lines at ICPMS sampling times
            ylims (dict): Y-axes limits if not to use the matplotlib-determined. Keys
                are 0-4 as in list below. ylims defaults to self.plot_specs["ylims"]
                Specifying axes[0].ylim automatically specifies axes[3].ylim according
                to self.beta
        Returns list of Axes:
            0: The minority-isotope signals (^{18}O2 and ^{16}O^{18}O fluxes)
            1: The electrochemical potential
            2: The electrochemical current
            3: The majority-isotope signal (^{16}O2 flux)
            4: The ICPMS-determined dissolution rate
        """

        tspan = tspan or self.tspan_plot
        beta = self.beta
        # ---------- setting up the gridspace for the ECMS-ICPMS plot --------- #
        plt.subplots()
        gs = gridspec.GridSpec(4, 1)
        # gs.update(hspace=0.025)
        # gs.update(hspace=0.05)
        ax0 = plt.subplot(gs[0:1, 0])  # the axis for the ICPMS data
        # the list of axes for the EC-MS data:
        axes = [plt.subplot(gs[1:3, 0])]
        axes += [plt.subplot(gs[3, 0])]
        axes += [axes[-1].twinx()]

        fig = plt.gcf()
        fig.set_figwidth(8)
        fig.set_figheight(7)

        O2_M32 = self.mdict["O2_M32"]
        O2_M34 = self.mdict["O2_M34"]
        O2_M36 = self.mdict["O2_M36"]
        axes = self.dataset.plot_experiment(
            mols=[[O2_M34, O2_M36], [O2_M32]],
            logplot=False,
            tspan=tspan,
            ax=axes,
            endpoints=10,
            verbose=False,
        )

        axes[0].set_ylabel("$^{18}$O signal / (pmol s$^{-1}$)")
        axes[-1].set_ylabel("$^{16}$O$_2$ signal / (pmol s$^{-1}$)")
        axes[1].set_ylabel("U vs RHE / (V)")
        axes[2].set_ylabel("J / (mA cm$^{-2}$)")
        axes[1].set_xlabel("time / (s)")
        # colorax(ax[0], O2_M34.get_color(), lr='left')

        x32, y32 = self.dataset.get_flux(O2_M32, unit="pmol/s", tspan=tspan)
        x34, y34 = self.dataset.get_flux(O2_M34, unit="pmol/s", tspan=tspan)

        if highlight:  # highlight the labeled lattice oxygen evolution
            y34_interp = np.interp(x32, x34, y34)
            axes[0].fill_between(x32, y32 * beta, y34_interp, color="r", alpha=0.5)

        ax0.set_xlim(axes[1].get_xlim())
        ax0.tick_params(
            axis="x", bottom=True, top=True, labelbottom=False, labeltop="on"
        )
        axes[0].tick_params(
            axis="x", bottom=True, top=True, labelbottom=False, labeltop=False
        )
        axes[0].set_xlabel("")
        axes[-1].tick_params(
            axis="x", bottom=True, top=True, labelbottom=False, labeltop=False
        )

        try:
            element = self.icpms_points[0].element
        except IndexError:
            print(f"{self.measurement} has no ICPMS points!")
        else:
            ax0.set_ylabel(element + " diss. / (pmol s$^{-1}$)")
            ax0.set_xlabel("time / (s)")
            ax0.xaxis.set_label_position("top")

            t_diff, n_dot_diff = self.get_dissolution_differential(tspan=tspan)

            ax0.plot(t_diff, n_dot_diff * 1e12, "k-")
            ax0.set_ylim(bottom=0)
            ax0.set_xlim(axes[0].get_xlim())
            ax0.tick_params(
                axis="x", bottom=False, top=True, labelbottom=False, labeltop=True
            )
            ax0.set_ylabel(element + " diss. / (pmol s$^{-1}$)")
            ax0.set_xlabel("time / (s)")
            if showsamples:
                ylim0 = ax0.get_ylim()
                ylim1 = axes[0].get_ylim()
                ylim2 = axes[1].get_ylim()

                sampling_times = [
                    icpms_point.sampling_time for icpms_point in self.icpms_points
                ]
                for t in sampling_times:
                    ax0.plot([t, t], ylim0, "b--")
                    axes[0].plot([t, t], ylim1, "b--")
                    axes[1].plot([t, t], ylim2, "b--")

                ax0.set_ylim(ylim0)
                axes[0].set_ylim(ylim1)
                axes[1].set_ylim(ylim2)

        axes = axes + [ax0]

        # scale M32 axis according to M34 axis limits and natural O isotope ratio!
        ylim_1 = axes[0].get_ylim()
        ylim_2_corrected = [ylim_1[0] / beta, ylim_1[-1] / beta]
        axes[3].set_ylim(ylim_2_corrected)

        ylims = ylims or self.plot_specs.get("ylims", {})
        for key, ylim in ylims.items():
            if key < 5:
                ax = axes[key]
            else:
                print(f"Warning, you requested ylims={ylims} but wtf is {key}???")
                break
            ax.set_ylim(ylim)
            if key == 0:  # keep the isotopic scaling!
                axes[3].set_ylim([lim / beta for lim in ylim])

        return axes
