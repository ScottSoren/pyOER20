"""this module implements methods and classes around point results"""
from pathlib import Path
import json
import numpy as np
from .tools import singleton_decorator, CounterWithFile
from .constants import TOF_DIR, TOF_ID_FILE
from .experiment import open_experiment


def calc_OER_rate(experiment, tspan):
    """Return the total average flux of O2 in [mol/s] in the experiment over tspan"""
    rate = 0
    for mol in "O2_M32", "O2_M34", "O2_M36":
        x, y = experiment.calc_flux(mol, tspan=tspan, unit="mol/s")
        rate += np.mean(y)

    return rate


def calc_dissolution_rate(experiment, tspan, t_electrolysis=None):
    """Return the average dissolution rate during tspan in [mol/s]

    Args:
        experiment (StandardExperiment): the standard experiment
        tspan (timespan): The time interval for which to get average dissolution rate
        t_electrolysis (float): if given, then assume dissolution only occurs over that
            length of time. I.e., divide the icpms_point amount by t_electrolysis.
    """
    t_vec, n_vec = experiment.get_dissolution_points()

    i_before = int(np.argmax(t_vec > tspan[0])) - 1
    i_after = int(np.argmax(t_vec > tspan[-1]))

    t_interval = tspan[-1] - tspan[0]
    if t_electrolysis:
        if i_after > i_before + 1:
            raise TypeError(
                f"Can't adjust '{experiment}' at tspan={tspan} for t_electrolysis"
                f"because the experiment has icpms samples taken during tspan"
            )
        n_during_interval = n_vec[i_after] * t_interval / t_electrolysis
    else:
        if i_after > i_before + 1:
            n_during_interval = (
                n_vec[i_before + 1]
                * (t_vec[i_before + 1] - tspan[0])
                / (t_vec[i_before + 1] - t_vec[i_before])
            )
            for i in range(i_before + 2, i_after):
                n_during_interval += n_vec[i]
            n_during_interval += (
                n_vec[i_after]
                * (tspan[-1] - t_vec[i_after - 1])
                / (t_vec[i_after] - t_vec[i_after - 1])
            )
        else:
            n_during_interval = (
                n_vec[i_after] * t_interval / (t_vec[i_after] - t_vec[i_after - 1])
            )

    return n_during_interval / t_interval


def calc_exchange_rate(experiment, tspan):
    """Return the average rate of lattice O incorporation in O2 in [mol/s] over tspan"""
    beta = experiment.beta
    x_32, y_32 = experiment.calc_flux("O2_M32", tspan=tspan, unit="mol/s")
    x_34, y_34 = experiment.calc_flux("O2_M34", tspan=tspan, unit="mol/s")
    return np.mean(y_34) - np.mean(y_32) * beta


def calc_potential(experiment, tspan):
    """Return the average potential vs RHE in [V] during the experiment over tspan"""
    t, U = experiment.dataset.get_potential(tspan=tspan)
    return np.mean(U)


@singleton_decorator
class TOFCounter(CounterWithFile):
    """Counts measurements. 'id' increments the counter. 'last()' retrieves last id"""

    _file = TOF_ID_FILE


def all_tofs(tof_dir=TOF_DIR):
    """returns an iterator that yields measurements in order of their id"""
    N_tofs = TOFCounter().last()
    for n in range(1, N_tofs + 1):
        try:
            tof = TurnOverFrequency.open(n, tof_dir=tof_dir)
        except FileNotFoundError as e:
            continue
        else:
            yield tof


def all_tof_sets(tof_dir=TOF_DIR):
    tof_sets = {}
    for tof in all_tofs(tof_dir=tof_dir):
        e_id = tof.e_id
        tspan = tuple(int(t) for t in tof.tspan)
        if not (e_id, tspan) in tof_sets:
            tof_sets[(e_id, tspan)] = TurnOverSet()
        tof_sets[(e_id, tspan)].add_tof(tof)
    yield from tof_sets.values()


class TurnOverSet:
    def __init__(
        self,
        t_ids=None,
    ):
        """Initiate a set of turn-over-frequencies taken from one point in an experiment

        Args:
            t_ids (dict): {tof_type: t_id} where tof_type is the action the tof
                describes ("activity", "exchange", "dissolution") and t_id is the id
        """
        self.t_ids = t_ids or {}
        self._tofs = {}
        self.experiment = None
        self.tspan = None

    def __contains__(self, item):
        return item in self.t_ids

    def __repr__(self):
        return f"TurnOverSet({self.t_ids})"

    def add_tof(self, tof):
        tof_type = tof.tof_type
        self.t_ids[tof_type] = tof.id
        self._tofs[tof_type] = tof
        if not self.experiment:
            self.experiment = tof.experiment
        elif not (tof.experiment.id == self.experiment.id):
            raise TypeError(f"can't add {tof} to {self} as experiment is not the same")
        if not self.tspan:
            self.tspan = tof.tspan
        elif not (tof.tspan[0] == self.tspan[0]):
            raise TypeError(f"can't add {tof} to {self} as tspans are not the same")

    def get_tof(self, item):
        if item in self._tofs:
            return self._tofs[item]
        elif item in self.t_ids:
            if self.experiment:
                self._tofs[item] = TurnOverFrequency.open(
                    self.t_ids[item], experiment=self.experiment
                )
            else:
                self._tofs[item] = TurnOverFrequency.open(self.t_ids[item])
                self.experiment = self._tofs[item].experiment
            return self._tofs[item]
        raise KeyError(f"{self} does not have tof for {item}")

    def __getitem__(self, item):
        return self.get_tof(item)

    def __iter__(self):
        yield from self._tofs.values()

    def __getattr__(self, item):
        try:
            return self.get_tof(item)
        except KeyError as e:
            raise AttributeError(e)

    @property
    def sample(self):
        return self.experiment.sample

    @property
    def sample_name(self):
        return self.experiment.sample_name


class TOFCollection:
    """A group of turnoverfrequencies"""

    def __init__(self, tof_list=None):
        self.tof_list = tof_list

    def __iter__(self):
        yield from self.tof_list

    def mean_rate(self):
        return np.mean(np.array([tof.rate for tof in self]))

    def std(self):
        return np.mean(np.array([tof.rate for tof in self]))


class TurnOverFrequency:
    def __init__(
        self,
        tof_type=None,
        rate=None,
        tof=None,
        potential=None,
        e_id=None,
        experiment=None,
        tspan=None,
        r_id=None,
        rate_calc_kwargs=None,
        description=None,
        t_id=None,
    ):
        """Iinitiate a TurnOverFrequency

        Args:
            tof_type (str): The type of TOF. Options are 'activity', 'exchange', and
                'dissolution'.
            rate (float): The un-normalized rate, if known, in [mol/s]
            e_id (int): The id of the associated experiment
            experiment (Experiment): optionally, the Experiment itself can be given to
                save time.
            tspan (timespan): The time interval over which to integrate/average
            r_id (int): The id of the associated roughness measurement
            rate_calc_kwargs (dict): Extra kwargs for the relevant rate calc. function.
            description (str): free-form description of the TOF point
            t_id (int): The principle key. Defaults to incrementing the counter
        """
        self.tof_type = tof_type
        self.e_id = e_id
        self.tspan = tspan
        self.r_id = r_id
        self._experiment = experiment
        self._rate = rate
        self._tof = tof
        self._potential = potential
        self.description = description
        self.rate_calc_kwargs = rate_calc_kwargs or {}
        self.id = t_id or TOFCounter().id

    def as_dict(self):
        """The dictionary represnetation of the TOF's metadata"""
        return dict(
            tof_type=self.tof_type,
            rate=self._rate,  # result!
            tof=self._tof,  # result!
            potential=self._potential,  # result!
            e_id=self.e_id,
            tspan=self.tspan,
            r_id=self.r_id,
            rate_calc_kwargs=self.rate_calc_kwargs,
            description=self.description,
            t_id=self.id,
        )

    def save(self):
        """Save the TOF's metadata to a .json file"""
        self_as_dict = self.as_dict()
        path_to_file = TOF_DIR / f"{self}.json"
        with open(path_to_file, "w") as f:
            json.dump(self_as_dict, f, indent=4)

    @classmethod
    def load(cls, path_to_file, **kwargs):
        """Load a TOF from the metadata stored in a file"""
        with open(path_to_file, "r") as f:
            self_as_dict = json.load(f)
        self_as_dict.update(kwargs)
        return cls(**self_as_dict)

    @classmethod
    def open(cls, t_id, tof_dir=TOF_DIR, **kwargs):
        """Opens the measurement given its id"""
        try:
            path_to_file = next(
                path
                for path in Path(tof_dir).iterdir()
                if path.stem.startswith(f"t{t_id}")
            )
        except StopIteration:
            raise FileNotFoundError(f"no TurnOverFrequency with id = t{t_id}")
        return cls.load(path_to_file, **kwargs)

    def __repr__(self):
        return f"t{self.id} is {self.tof_type} on {self.sample_name} on {self.date}"

    @property
    def experiment(self):
        if not self._experiment:
            self._experiment = open_experiment(self.e_id)
        return self._experiment

    @property
    def measurement(self):
        return self.experiment.measurement

    @property
    def date(self):
        return self.measurement.date

    @property
    def sample(self):
        return self.measurement.sample

    @property
    def sample_name(self):
        return self.measurement.sample_name

    @property
    def element(self):
        return self.sample.element

    @property
    def rate_calculating_function(self):
        """The function that this TOF uses to calculate its rate"""
        if self.tof_type == "activity":
            return calc_OER_rate
        if self.tof_type == "exchange":
            return calc_exchange_rate
        if self.tof_type == "dissolution":
            return calc_dissolution_rate
        raise TypeError(f"no associated rate function for tof_type={self.tof_type}")

    def calc_rate(self, **kwargs):
        """Calculate and return the relevant rate in [mol/s]"""
        rate_calc_kwargs = self.rate_calc_kwargs
        rate_calc_kwargs.update(kwargs)
        rate = self.rate_calculating_function(
            experiment=self.experiment, tspan=self.tspan, **rate_calc_kwargs
        )
        self._rate = rate
        return rate

    @property
    def rate(self):
        """The rate (activity, dissolution, or exchange) in [mol/s]"""
        if not self._rate:
            self.calc_rate()
        return self._rate

    def calc_tof(self):
        self._tof = self.rate / self.experiment.n_sites
        return self._tof

    @property
    def tof(self):
        if not self._tof:
            self.calc_tof()
        return self._tof

    def calc_potential(self):
        self._potential = calc_potential(self.experiment, self.tspan)
        return self._potential

    @property
    def potential(self):
        """The potential vs RHE in [V]"""
        if not self._potential:
            self.calc_potential()
        return self._potential
