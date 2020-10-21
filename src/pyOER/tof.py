"""this module implements methods and classes around point results"""

from .measurement import Measurement

def calc_OER_rate(
        standard_experiment,
        tspan
):
    pass


def calc_dissolution_rate(
        standard_experiment,
        tspan
):
    pass


def calc_exchange_rate(
        standard_experiment,
        tspan
):
    pass


def calc_potential(
        standard_experiment,
        tspan
):
    pass


class TurnOverFrequency:
    def __init__(
            self,
            tof_type=None,
            m_id=None,
            tspan=None,
            r_id=None,
    ):
        """Iinitiate a TurnOverFrequency"""
        self.m_id = m_id
        self._measurement = None
        self._standard_experiment = None

    @property
    def measurement(self):
        if not self._measurement:
            self._measurement = Measurement.open(self.m_id)
        return self._measurement

    @property
    def standard_experiment(self):
        if not self._standard_experiment:
            self._standard_experiment = self.measurement.get_standard_experiment()
        return self._standard_experiment

