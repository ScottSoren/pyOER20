# -*- coding: utf-8 -*-
"""
Created on Wed Sep 16 12:56:04 2020

@author: scott
"""

from pathlib import Path
import json
import numpy as np
from matplotlib import pyplot as plt
from .tools import singleton_decorator, CounterWithFile
from EC_MS import Chem

ICPMS_DIR = Path(__file__).parent.parent.parent / "icpms"
ICPMS_ID_FILE = ICPMS_DIR / "LAST_ICPMS_ID.pyoer20"
ICPMS_CALIBRATION_ID_FILE = ICPMS_DIR / "LAST_ICPMS_CALIBRATION_ID.pyoer20"


@singleton_decorator
class ICPMSSampleCounter(CounterWithFile):
    """Counts icpms samples. 'id' increments the counter. 'last()' retrieves last id"""

    _file = ICPMS_ID_FILE


@singleton_decorator
class ICPMSCalCounter(CounterWithFile):
    """Counts icpms cals. 'id' increments the counter. 'last()' retrieves last id"""

    _file = ICPMS_CALIBRATION_ID_FILE


class ICPMSPoint:
    def __init__(
        self,
        i_id,
        ic_id,
        m_id,
        element,
        mass,
        signal,
        sampling_time,
        initial_volume,
        dilution,
    ):
        """Initiate an ICP-MS measurement

        Args:
            i_id (int): The ICPMS sample id. Defaults to ICPMSSampleCounter.id
            ic_id (int): The id of the corresponding ICPMS calibration.
            m_id (int): The corresponding EC measurement id.
            element (str): The metal element measured
            mass (str): The mass at which the ICPMS was measuring for element.
            signal (float): The (averaged) ICPMS signal
            dilution (float): The ratio of concentration in the initial volume to
                concentration in the ICPMS sample as measured
            initial_volume (float): The volume of the containing electrolyte before any
                dilution, in [m^3]
            sampling_time (float): The time relative to Measurement.open(m_id).tstamp
                that the ICPMS sample was taken, in [s]

        """
        self.id = i_id
        self.ic_id = ic_id
        self.m_id = m_id
        self.element = element
        self.mass = mass
        self.signal = signal
        self.dilution = dilution
        self.initial_volume = initial_volume
        self.sampling_time = sampling_time
        if ic_id is not None:
            self.calibration = ICPMSCalibration.open(ic_id)
        self.icpms_dir = ICPMS_DIR

    def as_dict(self):
        """Dictionary representation of the ICPMS point"""
        self_as_dict = dict(
            id=self.id,
            ic_id=self.ic_id,
            m_id=self.m_id,
            element=self.element,
            mass=self.mass,
            signal=self.signal,
            dilution=self.dilution,
            initial_volume=self.initial_volume,
            sampling_time=self.sampling_time,
        )
        return self_as_dict

    def save(self, file_name=None):
        """Save the ICPMS measurement as .json in self.icpms_dir / file_name"""
        self_as_dict = self.as_dict()
        if not file_name:
            file_name = f"i{self.id} is {self.element} after {self.dilution}x dilution"
        print(f"saving measurement '{file_name}'")
        path_to_measurement = Path(self.icpms_dir) / file_name
        with open(path_to_measurement, "w") as f:
            json.dump(self_as_dict, f, indent=4)

    @classmethod
    def load(cls, file_name, icpms_dir=ICPMS_DIR):
        """Loads the measurement given its file path"""
        path_to_file = Path(icpms_dir) / file_name
        with open(path_to_file, "r") as f:
            self_as_dict = json.load(f)
        self_as_dict.update(file_loaded_from=path_to_file)
        if "id" in self_as_dict:
            self_as_dict["i_id"] = self_as_dict.pop("id")
        return cls(**self_as_dict)

    @classmethod
    def open(cls, i_id, icpms_dir=ICPMS_DIR):
        """Opens the measurement given its id"""
        try:
            path_to_file = next(
                path
                for path in Path(icpms_dir).iterdir()
                if path.stem.startswith(f"i{i_id}")
            )
        except StopIteration:
            raise FileNotFoundError(f"no icpms sample with id = {i_id}")
        return cls.load(path_to_file)

    @property
    def concentration(self):
        """Return the concentration of the element in original sample in [mol/m^3]"""
        c1 = self.calibration.signal_to_concentration(self.signal)
        c0 = c1 * self.dilution
        return c0

    @property
    def amount(self):
        """Return the amount element in initial volume in [mol]"""
        return self.concentration * self.initial_volume


class ICPMSCalibration:
    def __init__(
        self, ic_id, date, element, ppbs, signals, wash_signals,
    ):
        """Initiate an ICP-MS calibration

        Args:
            ic_id (int: the id of the ICPMS calibration
            date (str): the scott-formatted date the calibration was measured on
            element (str): the element
            ppbs (np.array): concentrations in [ppb]
            signals (np.array): signals in [counts]
        """
        self.id = ic_id
        self.date = date
        self.element = element
        self.ppbs = ppbs
        self.signals = signals
        self.wash_signals = wash_signals
        self.icpms_dir = ICPMS_DIR
        self._calibration_curve = None

    def as_dict(self):
        """Dictionary representation of the ICPMS calibration"""
        self_as_dict = dict(
            id=self.id,
            date=self.date,
            element=self.element,
            ppbs=self.ppbs,
            signals=self.signals,
        )
        return self_as_dict

    def save(self, file_name=None):
        """Save the ICPMS calibration as .json in self.icpms_dir / file_name"""
        self_as_dict = self.as_dict()
        if not file_name:
            file_name = f"i{self.id} is icpms calibration for {self.element}"
        print(f"saving measurement '{file_name}'")
        path_to_measurement = Path(self.icpms_dir) / file_name
        with open(path_to_measurement, "w") as f:
            json.dump(self_as_dict, f, indent=4)

    @classmethod
    def load(cls, file_name, icpms_dir=ICPMS_DIR):
        """Loads the measurement given its file path"""
        path_to_file = Path(icpms_dir) / file_name
        with open(path_to_file, "r") as f:
            self_as_dict = json.load(f)
        self_as_dict.update(file_loaded_from=path_to_file)
        if "id" in self_as_dict:
            self_as_dict["ic_id"] = self_as_dict.pop("id")
        return cls(**self_as_dict)

    def make_calibration_curve(self):
        """Make self._calibration_curve best fit of ln(self.ppbs) to ln(self.signals)"""
        ln_cal_amounts = np.log(self.ppbs)
        ln_cal_counts = np.log(self.signals)

        p = np.polyfit(ln_cal_counts, ln_cal_amounts, deg=1)
        print(p)  # debugging

        def calibration_curve(counts):
            """Return the concentration in [ppb] given signal in [counts]"""
            ln_counts = np.log(counts)
            ln_ppb = p[0] * ln_counts + p[1]
            ppb = np.exp(ln_ppb)
            return ppb

        self._calibration_curve = calibration_curve

    @classmethod
    def open(cls, ic_id, icpms_dir=ICPMS_DIR):
        """Opens the measurement given its id"""
        try:
            path_to_file = next(
                path
                for path in Path(icpms_dir).iterdir()
                if path.stem.startswith(f"i{ic_id}")
            )
        except StopIteration:
            raise FileNotFoundError(f"no icpms calibration with id = {ic_id}")
        return cls.load(path_to_file)

    @property
    def calibration_curve(self):
        """The calibration curve converting counts to parts per billion"""
        if not self._calibration_curve:
            self.make_calibration_curve()
        return self._calibration_curve

    def signal_to_concentration(self, signal):
        """Return concentration in [mol/m^3] of ICPMS sample given its signal"""
        ppb_amount = self.calibration_curve(signal)
        kg_per_m3 = ppb_amount * 1e-6
        kg_per_mol = Chem.get_mass(self.element) * 1e-3
        concentration = kg_per_m3 / kg_per_mol
        return concentration

    def plot_calibration(self, ax=None):
        """Plot the ICPMS calibration (as fig A.4 of Scott's PhD thesis)

        Args:
            ax (plt.Axis):
        """
        ppbs = self.ppbs
        signals = self.signals
        calibration_curve = self.calibration_curve
        if not ax:
            fig, ax = plt.subplots()
            ax.set_xlabel("amount / [ppb]")
            ax.set_ylabel("counts")
            ax.set_xscale("log")
            ax.set_yscale("log")

        ax.plot(ppbs, signals, "ks", markersize=7)
        x_fit, y_fit = calibration_curve(signals), signals

        if self.wash_signals is not None:
            wash = self.wash_signals
            mean = np.mean(wash)
            std = np.std(wash)

            y_fit = np.append(mean, y_fit)
            x_fit = np.append(calibration_curve(mean), x_fit)
            ax.plot(x_fit, y_fit, "r--")

            xlim = ax.get_xlim()
            ax.plot(xlim, [mean, mean], "k--")
            ax.plot(xlim, [mean + 3 * std, mean + 3 * std], "k:")
            ax.set_xlim(xlim)

        else:
            ax.plot(x_fit, y_fit, "r--")
