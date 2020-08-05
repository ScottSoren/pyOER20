"""This module links Measuremnt to sensitivity factor and electrolyte isotope ratio"""

from pathlib import Path
import json
import numpy as np
from EC_MS.utils.extraction_class import Extraction
from EC_MS import Chem
from .measurement import Measurement
from .tools import singleton_decorator, CounterWithFile

CALIBRATION_DIR = Path(__file__).parent.parent.parent / "calibrations"
CALIBRATION_ID_FILE = CALIBRATION_DIR / "LAST_CALIBRATION_ID.pyoer20"

if not CALIBRATION_DIR.exists():
    # This block of code makes it so I can delete calibrations/ and start over quickly.
    Path.mkdir(CALIBRATION_DIR)
    with open(CALIBRATION_ID_FILE, "w") as counter_file:
        counter_file.write("0")


def all_calibrations(calibration_dir=CALIBRATION_DIR):
    """returns an iterator that yields measurements in order of their id"""
    N_calibrations = CalibrationCounter().last()
    for n in range(1, N_calibrations + 1):
        try:
            calibration = Calibration.open(n, calibration_dir=calibration_dir)
        except FileNotFoundError as e:
            print(f"all_calibrations() is skipping {n} due to error = \n{e}")
        else:
            yield calibration


@singleton_decorator  # ... this is not really necessary as the file is read each time.
class CalibrationCounter(CounterWithFile):
    """Counts calibrations. 'id' increments the counter. 'last()' retrieves last id"""

    _file = CALIBRATION_ID_FILE


calibration_counter = CalibrationCounter()


class Calibration:
    """Class for referencing calibration raw data and storing a calibration result"""

    # -------- all of this should be a template like a baseclass ---------------- #

    def __init__(
        self,
        c_id=None,
        m_id=None,
        tspan=None,
        cal_tspans=None,
        t_bg=None,
        F=None,
        alpha=None,
        category=None,
        isotope=None,
        **kwargs,
    ):
        """Initiate the calibration

        Args:
            c_id (int): calibration number (self.id)
            m_id (int): measurement number
            tspan (tspan): timespan of the measurement used for the calibration
            F (dict): sensitivity factors
            alpha (float): isotope ratio in electrolyte
            category (string): typically either "good" or "bad"
            isotope (string): typically "16" or "18"
        """
        if c_id is None:
            c_id = calibration_counter.id
        self.id = c_id
        self.m_id = m_id
        self.tspan = tspan
        self.cal_tspans = cal_tspans
        self.t_bg = t_bg
        if F is None:
            F = {}
        self.F = F
        self.alpha = alpha
        self.category = category
        self.isotope = isotope
        self._measurement = None  # measurement is a managed property
        self._extraction = None  # extraction is a managed property
        self.extra_stuff = kwargs
        self.name = self.make_name()

    def as_dict(self):
        """Return the dictionary representation of the calibration"""
        self_as_dict = {
            "c_id": self.id,
            "m_id": self.m_id,
            "tspan": self.tspan,
            "cal_tspans": self.cal_tspans,
            "t_bg": self.t_bg,
            "F": self.F,
            "alpha": self.alpha,
            "category": self.category,
            "isotope": self.isotope,
        }
        return self_as_dict

    @classmethod
    def load(cls, file_name, calibration_dir=CALIBRATION_DIR):
        path_to_file = Path(calibration_dir) / file_name
        with open(path_to_file) as f:
            self_as_dict = json.load(f)
        self_as_dict.update(file_loaded_from=path_to_file)
        if "id" in self_as_dict:
            self_as_dict["c_id"] = self_as_dict.pop("id")
        return cls(**self_as_dict)

    @classmethod
    def open(cls, c_id, calibration_dir=CALIBRATION_DIR):
        """Opens the measurement given its id"""
        try:
            path_to_file = next(
                path
                for path in Path(calibration_dir).iterdir()
                if path.stem.startswith(f"c{c_id}")
            )
        except StopIteration:
            raise FileNotFoundError(f"no calibration with id = m{c_id}")
        return cls.load(path_to_file)

    def save(self, file_name=None, calibration_dir=CALIBRATION_DIR):
        self_as_dict = self.as_dict()
        if not file_name:
            file_name = self.make_name() + ".json"
        with open(Path(calibration_dir) / file_name, "w") as f:
            json.dump(self_as_dict, f, indent=4)

    def save_with_rename(self, file_name=None):
        if "file_loaded_from" in self.extra_stuff:
            Path(str(self.extra_stuff["file_loaded_from"])).unlink()
        self.save(file_name=file_name)

    # -------- now starts the calibration-specific stuff ---------------- #
    @property
    def measurement(self):
        if not self._measurement:
            self._measurement = Measurement.open(self.m_id)
        return self._measurement

    def make_name(self):
        c_id = self.id
        date = self.measurement.date
        sample = self.measurement.sample
        category = self.category
        name = f"c{c_id} is a {category} cal with {sample} on {date}"
        return name

    @property
    def extraction(self):
        """The EC_MS dataset for the calibration measurement as an Extraction object"""
        if not self._extraction:
            self._extraction = Extraction(
                dataset=self.measurement.dataset,
                tspan_ratio=self.tspan,
                t_bg=self.t_bg,
                electrolyte=self.isotope,
            )
        return self._extraction

    def calibration_curve(self, ax=None, **kwargs):
        """Calibrate O2 using EC_MS.Dataset.calibration_curve() and self.tspans"""
        F_O2 = 0
        for mass in ["M32", "M34", "M36"]:
            O2, ax = self.extraction.calibration_curve(
                mol="O2",
                mass=mass,
                n_el=4,
                tspans=self.cal_tspans,
                t_bg=self.t_bg,
                out=["Molecule", "ax"],
                ax=ax,
                **kwargs,
            )
            F_O2 += O2.F_cal
        self.F["O2"] = F_O2
        return F_O2

    def cal_F_O2(self):
        """calibrate the O2 signal based on assumption of OER during self.tspan"""
        Y_cum = 0
        for mass in ["M32", "M34", "M36"]:
            x, y = self.extraction.get_signal(
                mass=mass, tspan=self.tspan, t_bg=self.t_bg, unit="A",
            )
            Y = np.trapz(y, x)
            Y_cum += Y
        t, I = self.extraction.get_current(tspan=self.tspan, unit="A")
        Q = np.trapz(I, t)
        n = Q / (4 * Chem.Far)
        F_O2 = Y_cum / n

        self.F["O2"] = F_O2

        return F_O2

    def cal_alpha(self):
        """calibrate the isotope ratio based on the assumption of OER during self.tspan"""
        alpha = self.extraction.get_alpha()
        self.alpha = alpha

        return alpha


class CalibrationTrend:
    """A class to describe the trend of calibrations and predict F based on tstamp"""

    pass
