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


@singleton_decorator  # ... this is not really necessary as the file is read each time.
class CalibrationCounter(CounterWithFile):
    """Counts calibrations. 'id' increments the counter. 'last()' retrieves last id"""

    _file = CALIBRATION_ID_FILE


calibration_counter = CalibrationCounter()


class Calibration:
    """Class for referencing calibration raw data and storing a calibration result"""

    def __init__(
        self,
        c_id=None,
        m_id=None,
        tspan=None,
        t_bg=None,
        F=None,
        alpha=None,
        category=None,
        isotope=None,
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
        self.t_bg = t_bg
        self.F = F
        self.alpha = alpha
        self.category = category
        self.isotope = isotope
        self.name = self.make_name()
        self._measurement = None  # measurement is a managed property
        self._extraction = None  # extraction is a managed property

    def as_dict(self):
        """Return the dictionary representation of the calibration"""
        self_as_dict = {
            "c_id": self.id,
            "m_id": self.m_id,
            "tspan": self.tspan,
            "t_bg": self.t_bg,
            "F": self.F,
            "alpha": self.alpha,
            "category": self.category,
            "isotope": self.isotope,
        }
        return self_as_dict

    @classmethod
    def load(cls, file_name, calibration_dir=CALIBRATION_DIR):
        with open(Path(calibration_dir) / file_name) as f:
            self_as_dict = json.load(f)
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
                if path.stem.startswith(f"m{c_id}")
            )
        except StopIteration:
            raise FileNotFoundError(f"no measurement with id = m{c_id}")
        return cls.load(path_to_file)

    def save(self, file_name=None, calibration_dir=CALIBRATION_DIR):
        self_as_dict = self.as_dict()
        if not file_name:
            file_name = self.make_name() + ".json"
        with open(Path(calibration_dir) / file_name) as f:
            json.dump(self_as_dict, f)

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
        if not self._extraction:
            self._extraction = Extraction(
                dataset=self.measurement.dataset,
                tspan_ratio=self.tspan,
                electrolyte=self.isotope,
            )
        return self._extraction

    def cal_O2_and_ratio(self):
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
        F = Y_cum / n
        alpha = self.extraction.get_ratio()

        self.F["O2"] = F
        self.alpha = alpha

        return F, alpha
