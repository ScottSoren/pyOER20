"""This module implements Experiments, which add analysis to types of Measurements

All experiments should have a background-subtracted dataset (EC_MS.Dataset) with
calibrated current and potential, and an mdict containing EC_MS.Molecule objects
which correctly calibrate the MS data of the dataset.

The StandardExperiment is a constant-potential OER (or composite thereof) with
ICPMS-MS samples taken during the measurement. The sample is a labeled test sample or
un-labeled control sample and the electrolyte is natural, so all m/z=34 and m/z=36 is
excess lattice O. The StandardExperiment is only calibrated for O2, though at all
three isotopes, and gets the calibration factor from the trend in the project's
CalibrationSeries. """

from pathlib import Path
import json
import numpy as np
from matplotlib import gridspec, pyplot as plt

from EC_MS import Molecule

from .constants import (
    EXPERIMENT_DIR,
    EXPERIMENT_ID_FILE,
    STANDARD_ALPHA,
    STANDARD_EXPERIMENT_TAGS,
)
from .tools import singleton_decorator, CounterWithFile
from .measurement import Measurement
from .calibration import CalibrationSeries

calibration_series = CalibrationSeries.load()


def all_experiments(experiment_dir=EXPERIMENT_DIR):
    """returns an iterator that yields experiments in order of their id"""
    N_experiments = ExperimentCounter().last()
    for n in range(1, N_experiments):
        try:
            measurement = Experiment.open(n, experiment_dir=experiment_dir)
        except FileNotFoundError as e:
            print(f"itermeasurement skipping {n} due to error = \n{e}")
        else:
            yield measurement


def all_standard_experiments(experiment_dir=EXPERIMENT_DIR):
    N_experiments = ExperimentCounter().last()
    for n in range(1, N_experiments):
        try:
            standard_experiment = StandardExperiment.open(
                n, experiment_dir=experiment_dir
            )
        except (FileNotFoundError, TypeError) as e:
            print(f"itermeasurement skipping {n} due to error = \n{e}")
        else:
            yield standard_experiment

def all_activity_experiments(experiment_dir=EXPERIMENT_DIR):
    N_experiments = ExperimentCounter().last()
    for n in range(1, N_experiments):
        try:
            activity_experiment = ActExperiment.open(
                n, experiment_dir=experiment_dir
            )
            if not activity_experiment.experiment_type.startswith("a"):
                raise TypeError("wrong type of experiment.")
        except (FileNotFoundError, TypeError) as e:
            print(f"itermeasurement skipping {n} due to error = \n{e}")
        else:
            yield activity_experiment


@singleton_decorator
class ExperimentCounter(CounterWithFile):
    """Counts measurements. 'id' increments the counter. 'last()' retrieves last id"""

    _file = EXPERIMENT_ID_FILE


def open_experiment(e_id, experiment_dir=EXPERIMENT_DIR):
    """Open as the appropriate type of Experiment based on the experiment_type field"""
    try:
        path_to_file = next(
            path
            for path in Path(experiment_dir).iterdir()
            if path.stem.startswith(f"e{e_id}")
        )
    except StopIteration:
        raise FileNotFoundError(f"no standard experiment with id = e{e_id}")
    with open(path_to_file, "r") as f:
        e_as_dict = json.load(f)
    e_type = e_as_dict["experiment_type"]
    if e_type in STANDARD_EXPERIMENT_TAGS:
        cls = StandardExperiment
    else:
        cls = Experiment
    return cls(**e_as_dict)


class Experiment:
    """Joins a pyOER measurement with extra metadata and methods for deriving results

    This is a base class for more complex experiments, with methods and saveable
    metadata (typically tspans) for subtracting background, plotting nicely,
    calibrating signals, determining electrolyte isotopic composition, etc.
    It also has a list of TOFs, which (separately) contain the metadata for deriving
    specific results.
    Inheriting classes will contain methods to
    """

    def __init__(
        self,
        m_id,
        experiment_type=None,
        tspan_plot=None,
        F=None,
        alpha=None,
        cap=None,
        tspan_bg=None,
        tspan_F=None,
        tspan_alpha=None,
        tspan_cap=None,
        V_DL=(1.22, 1.3),
        e_id=None,
        **kwargs,
    ):
        """Initiate an experiment

        Args:
            m_id (int): The measurement id
            experiment_type (str): Tag for the type of standard experiment. Options are
                - standard experiments (activity + exchange + dissolution):
                "y": "yes, purely systematic",  # 30 minutes at one current density
                "s": "starts systematic",
                "k": "shortened systematic (<30 minutes)",
                "c": "composite systematic"  # one sample multiple current densities
                - activity experiments (constant potential steps):
            tspan_plot (timespan): The timespan in which to make the experiment
                plot. If not given, the plot will use the measurement's tspan
            F (float): The O2 sensitivity in [C/mol]. By default the experiment will
                use the O2 sensitivity given by the CalibrationSeries represented in
                TREND.json in the calibration directory
            alhpa (float): The ^{16}O portion in the electrolyte. By default it takes
                the natural value of 99.80%
            cap (float): The capacitance- in [Farads], if known.
            tspan_bg (timespan): The timespan to consider the background
            tspan_F (timespan): The timespan from which O2 sensitivity (F) can be
                calculated from the measurement
            tspan_alpha (timespan): The timespan from which the isotopic composition of
                the electrolyte (alpha) can be calculated form the measurement F is to
                be calculated from the measurement
            tspan_cap (timespan): The timespan from which capacitance can be measured
            V_DL (list of float): The voltage range for capacitance calculation / [V]
            plot_specs (dict): Additional specs for the plot, e.g. axis limits ("ylims")
            e_id (int): The StandardExperiment's principle key
        """
        self.m_id = m_id
        self.experiment_type = experiment_type
        self.measurement = Measurement.open(m_id)
        self._dataset = None
        self.tspan_plot = tspan_plot
        self.tspan_bg = tspan_bg
        self.tspan_F = tspan_F
        self.F_0 = F  # for saving, so that if no F is given and the CalibrationSeries
        # is updated, the updated CalibrationSeries will determine F upon loading.
        self._F = None
        self._mdict = {}
        self.tspan_alpha = tspan_alpha
        self.alpha_0 = alpha  # for saving, so that if no alpha is given and the
        # natural ratio is updated, this will determine alpha upon loading.
        self._alpha = None
        self._cap = cap
        self.tspan_cap = tspan_cap
        self.V_DL = V_DL
        self._cap = None
        self._icpms_points = None
        self.id = e_id or ExperimentCounter().id
        self.default_masses = ["M32", "M34", "M36"]
        self._tofs = None
        self.extra_stuff = kwargs

    def as_dict(self):
        return dict(
            m_id=self.m_id,
            experiment_type=self.experiment_type,
            tspan_plot=self.tspan_plot,
            tspan_bg=self.tspan_bg,
            tspan_F=self.tspan_F,
            tspan_cap=self.tspan_cap,
            tspan_alpha=self.tspan_alpha,
            F=self.F_0,
            alpha=self.alpha_0,
            e_id=self.id,
        )

    def __repr__(self):
        return f"e{self.id} is from m{self.m_id} of {self.measurement.sample_name}"

    def save(self):
        self_as_dict = self.as_dict()
        file = EXPERIMENT_DIR / f"{self}.json"
        with open(file, "w") as f:
            json.dump(self_as_dict, f, indent=4)

    @classmethod
    def load(cls, file):
        """Load a standard experiment given the path to its json file."""
        with open(file, "r") as f:
            self_as_dict = json.load(f)
        if "plot_specs" in self_as_dict and "ylims" in self_as_dict["plot_specs"]:
            # json turns integer keys to strings. This fixes.
            self_as_dict["plot_specs"]["ylims"] = {
                int(s): ylim for s, ylim in self_as_dict["plot_specs"]["ylims"].items()
            }
        experiment_class = cls
        if "experiment_type" in self_as_dict:
            if self_as_dict["experiment_type"].startswith("a"):
                experiment_class = ActExperiment
            elif self_as_dict["experiment_type"] in STANDARD_EXPERIMENT_TAGS:
                experiment_class = StandardExperiment
        return experiment_class(**self_as_dict)

    @classmethod
    def open(cls, e_id, experiment_dir=EXPERIMENT_DIR):
        try:
            path_to_file = next(
                path
                for path in Path(experiment_dir).iterdir()
                if path.stem.startswith(f"e{e_id}")
            )
        except StopIteration:
            raise FileNotFoundError(f"no standard experiment with id = e{e_id}")
        return cls.load(path_to_file)

    @property
    def dataset(self):
        if not self._dataset:
            dataset = self.measurement.dataset
            dataset.sync_metadata(
                RE_vs_RHE=self.measurement.RE_vs_RHE,
                A_el=0.196,
            )
            if self.tspan_bg:
                dataset.set_background(self.tspan_bg)
            self._dataset = dataset
        return self._dataset

    @property
    def beta(self):
        """Float: The m/z=34 to m/z=32 signal ratio from oxidation of the electrolyte"""
        return 2 * (1 - self.alpha) / self.alpha

    @property
    def gamma(self):
        """Float: The m/z=34 to m/z=36 signal ratio from oxidation of the electrolyte"""
        return 2 * self.alpha / (1 - self.alpha)

    @property
    def sample(self):
        return self.measurement.sample

    @property
    def sample_name(self):
        return self.measurement.sample_name

    @property
    def tofs(self):
        if not self._tofs:
            self.load_tofs()
        return self._tofs

    def load_tofs(self):
        from .tof import all_tofs

        self._tofs = [tof for tof in all_tofs() if tof.e_id == self.id]

    @property
    def tof_sets(self):
        from .tof import all_tof_sets

        return [t_set for t_set in all_tof_sets() if t_set.experiment.id == self.id]

    def calc_alpha(self, tspan=None):
        """Return fraction ^{16}O in the electrolyte based on tspan with steady OER"""
        tspan = tspan or self.tspan_alpha
        x_32, y_32 = self.dataset.get_signal(mass="M32", tspan=tspan)
        x_34, y_34 = self.dataset.get_signal(mass="M34", tspan=tspan)
        gamma = np.mean(y_34) / np.mean(y_32)
        alpha = 2 / (2 + gamma)
        return alpha

    @property
    def cap(self):
        """Capacitance in Farads"""
        if not self._cap:
            cap_cv = self.measurement.dataset.cut(self.tspan_cap).as_cv()
            self._cap = cap_cv.get_capacitance(V_DL=self.V_DL) * self.dataset.A_el
            # Farad/cm^2 * cm^2
        return self._cap

    @property
    def ECSA(self):
        """Electrochemical surface area in [cm^2]"""
        return self.cap / self.sample.specific_capacitance  # Farad / (Farad/cm^2)

    @property
    def n_sites(self):
        """Number of sites in [mol]"""
        return self.ECSA * self.sample.site_density  # cm^2 * mol/cm^2

    def populate_mdict(self):
        """Fill in self.mdict with the EC-MS.Molecules O2_M32, O2_M34, and O2_M36"""
        for mass in ["M32", "M34", "M36"]:
            m = Molecule("O2")
            m.primary = mass
            m.F_mat = None
            m.F_cal = self.F
            self._mdict[f"O2_{mass}"] = m

    @property
    def mdict(self):
        if not self._mdict:
            self.populate_mdict()
        return self._mdict

    @property
    def F(self):
        if not self._F:
            if self.tspan_F:
                F = 0
                for mass in self.default_masses:
                    try:
                        F += self.dataset.point_calibration(
                            mol="O2",
                            mass=mass,
                            n_el=4,
                            tspan=self.tspan_F,
                        ).F_cal
                    except KeyError:
                        continue
            elif self.F_0:
                F = self.F_0
            else:
                F = calibration_series.F_of_tstamp(self.dataset.tstamp)
            self._F = F
        return self._F

    @property
    def alpha(self):
        if not self._alpha:
            if self.tspan_alpha:
                alpha = self.calc_alpha()
            else:
                alpha = self.alpha_0
            self._alpha = alpha or STANDARD_ALPHA
        return self._alpha

    def calc_flux(self, mol, tspan, **kwargs):
        """Return the flux for a calibrated mol (a key to self.mdict)"""
        m = self.mdict[mol]
        return self.dataset.get_flux(m, tspan=tspan, **kwargs)


class StandardExperiment(Experiment):
    """This class describes the experiments from which 3x TOF measurements are derived

    These are EC-MS measurements of a labeled (or control) sample in non-labeled
    elcctroyte at constant current, which ICP-MS samples taken during or between
    measurements. The class wraps the corresponding measurement with extra functions.

    They are best represented as an EC-MS-ICPMS plot where the MS panel has left and
    rignt y-axes representing labeled and non-labeled O2, respectively. Such a plot
    is made with StandardExperment.plot_EC_MS_ICPMS
    """

    def __init__(
        self,
        m_id,
        experiment_type=None,
        tspan_plot=None,
        F=None,
        alpha=None,
        tspan_bg=None,
        tspan_F=None,
        tspan_alpha=None,
        e_id=None,
        plot_specs=None,
        **kwargs,
    ):
        super().__init__(
            m_id=m_id,
            experiment_type=experiment_type,
            tspan_plot=tspan_plot,
            F=F,
            tspan_F=tspan_F,
            alpha=alpha,
            tspan_alpha=tspan_alpha,
            tspan_bg=tspan_bg,
            e_id=e_id,
            **kwargs,
        )
        if not experiment_type in STANDARD_EXPERIMENT_TAGS:
            raise TypeError(
                f"Cannot make StandardExperiment of '{self.measurement}' "
                f"with experiment_type='{experiment_type}'"
            )
        self.plot_specs = plot_specs
        self._icpms_points = None

    def as_dict(self):
        self_as_dict = super().as_dict()
        self_as_dict.update(plot_specs=self.plot_specs)
        return self_as_dict

    @property
    def icpms_points(self):
        """List of ICPMSPoint: The ICPMS samples from the experiment"""
        if not self._icpms_points:
            self._icpms_points = self.measurement.get_icpms_points()
        return self._icpms_points

    def get_dissolution_points(self):
        """Return the ICPMS sampling times (t_vec) and molar amounts (n_vec)"""
        icpms_points = self.icpms_points
        t_vec = np.array([icpms_point.sampling_time for icpms_point in icpms_points])
        n_vec = np.array([icpms_point.amount for icpms_point in icpms_points])
        return t_vec, n_vec

    def get_dissolution_rates(self):
        """Return the ICPMS sampling times (t_vec) and dissolution raties (n_dot_vec)"""
        t_points, n_points = self.get_dissolution_points()
        t_last = 0
        t_vec = np.array([])
        n_dot_vec = np.array([])
        for (
            t,
            n,
        ) in zip(t_points, n_points):
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


class ActExperiment(Experiment):
    """Activity experiment. Doesn't actually need anything extra. Info in the TOFs."""

    def plot_experiment(self, tspan=None, unit="pmol/s/cm^2"):
        tspan = tspan or self.tspan_plot
        mols = list(self.mdict.values())
        axes = self.dataset.plot_experiment(
            mols=mols, tspan=tspan, unit=unit, logplot=False
        )
        if self.tspan_F:
            self.dataset.plot_flux(
                mols=mols,
                tspan=self.tspan_F,
                ax=axes[0],
                alpha_under=0.3,
                unit=unit,
                logplot=False,
            )
        if self.tspan_cap and (tspan == "all" or not tspan):
            cap_cv = self.measurement.dataset.cut(self.tspan_cap).as_cv()
            t, J = cap_cv.get_capacitance(V_DL=self.V_DL, out=["t", "J"])
            axes[2].fill_between(t, J, np.zeros(t.shape), color="0.5", alpha=0.3)
        for tof in self.tofs:
            self.dataset.plot_flux(
                mols=mols,
                tspan=tof.tspan,
                ax=axes[0],
                alpha_under=0.15,
                unit=unit,
                logplot=False,
            )
        return axes
