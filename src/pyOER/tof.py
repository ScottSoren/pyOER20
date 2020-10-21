"""this module implements methods and classes around point results"""

import numpy as np
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

    n_during_interval / t_interval


def calc_exchange_rate(experiment, tspan):
    """Return the average rate of lattice O incorporation in O2 in [mol/s] over tspan"""
    beta = experiment.beta
    x_32, y_32 = experiment.calc_flux("O2_M32", tsapn=tspan, unit="mol/s")
    x_34, y_34 = experiment.calc_flux("O2_M34", tsapn=tspan, unit="mol/s")
    return np.mean(y_34) - np.mean(y_32) * beta


def calc_potential(experiment, tspan):
    """Return the average potential vs RHE in [V] during the experiment over tspan"""
    t, U = experiment.dataset.get_potential(tspan=tspan)
    return np.mean(U)


class TurnOverFrequency:
    def __init__(
        self, tof_type=None, e_id=None, tspan=None, r_id=None, rate_calc_kwargs=None
    ):
        """Iinitiate a TurnOverFrequency

        Args:
            tof_type (str): The type of TOF. Options are 'activity', 'exchange', and
                'dissolution'.
            e_id (int): The id of the associated experiment
            tspan (timespan): The time interval over which to integrate/average
            r_id (int): The id of the associated roughness measurement
            rate_calc_kwargs (dict): Extra kwargs for the relevant rate calc. function
        """
        self.tof_type = tof_type
        self.e_id = e_id
        self.tspan = tspan
        self.r_id = r_id
        self._experiment = None
        self._rate = None
        self.rate_calc_kwargs = rate_calc_kwargs or {}

    @property
    def experiment(self):
        if not self._experiment:
            self._experiment = open_experiment(self.e_id)
        return self._experiment

    @property
    def rate_calculating_function(self):
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
