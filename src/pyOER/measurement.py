"""Define the Measurement class containing metadata and pointers to raw data.

"""

from pathlib import Path
import json
import time
import datetime
from EC_MS import Dataset
from .tools import singleton_decorator

MEASUREMENT_DIR = Path(__file__).parent.parent.parent / "measurements"
MEASUREMENT_ID_FILE = MEASUREMENT_DIR / "LAST_MEASUREMENT_ID.pyoer20"

if not MEASUREMENT_DIR.exists():
    Path.mkdir(MEASUREMENT_DIR)
    with open(MEASUREMENT_ID_FILE, "w") as f:
        f.write("0")


@singleton_decorator
class MeasurementCounter:
    _id = None

    @property
    def id(self):
        with open(MEASUREMENT_ID_FILE, "r") as f:
            self._id = int(f.read()) + 1
        with open(MEASUREMENT_ID_FILE, "w") as f:
            f.write(str(self._id))
        return self._id


measurement_counter = MeasurementCounter()


class Measurement:
    """class containing metadata and pointers to raw data.
    Used mainly for saving and loading links."""

    def __init__(
        self,
        m_id=None,
        measurement_dir=MEASUREMENT_DIR,
        copied_at=None,
        name=None,
        sample=None,
        technique=None,
        isotope=None,
        measurement_date=None,
        analysis_date=None,
        old_data_path=None,
        new_data_path=None,
        dataset=None,
        linked_measurements=None,
        **kwargs,
    ):
        """Initiate Measurement object

        Intended use is to load the dataset separately using Measurement.load_dataset()

        Args:
            m_id (int): the unique id of the measurement
            name (str): the name of the measurement
            measurement_dir (Path-like): where to save the measurement metadata
            copied_at (float): the time at which the dataset was read
            old_data_path (Path-like): path to file to load the raw data from pkl
            new_data_path (Path-like): path to file to save the raw data as pkl
            dataset (EC_MS.Dataset): the dataset
            linked_measurements (dict): measurements to link to this one
            kwargs (dict): gets added, not used. Here so that I can add extra stuff when
                saving just to improve readability of the json
        """
        if not m_id:
            m_id = measurement_counter.id
        self.id = m_id
        self.name = name
        self.sample = sample
        self.technique = technique
        self.isotope = isotope
        self.measurement_date = measurement_date
        self.analysis_date = analysis_date
        self.measurement_dir = measurement_dir
        self.copied_at = copied_at  # will be replaced by time.time()
        self.old_data_path = old_data_path
        self.new_data_path = new_data_path
        self.dataset = dataset
        self.linked_measurements = linked_measurements
        self.extra_stuff = kwargs

    def as_dict(self):
        self_as_dict = dict(
            id=self.id,
            name=self.name,
            sample=self.sample,
            technique=self.technique,
            isotope=self.isotope,
            measurement_date=self.measurement_date,
            analysis_date=self.analysis_date,
            measurement_dir=str(self.measurement_dir),
            copied_at=self.copied_at,
            old_data_path=str(self.old_data_path),
            new_data_path=str(self.new_data_path),
            linked_measurements=self.linked_measurements
            # do not put the dataset into self.dict!
        )
        if self.copied_at:  # just for human-readability of measurement .json
            self_as_dict["copied_on"] = datetime.datetime.fromtimestamp(
                self.copied_at
            ).strftime("%Y-%m-%d %H:%M:%S")
        return self_as_dict

    def save(self, file_name=None, save_dataset=False):
        self_as_dict = self.as_dict()
        if not file_name:
            if not self.name:
                self.make_name()
            file_name = self.name + ".json"
        print(f"saving measurement '{file_name}'")
        path_to_measurement = Path(self.measurement_dir) / file_name
        with open(path_to_measurement, "w") as f:
            json.dump(self_as_dict, f, indent=4)
        if save_dataset:
            self.save_dataset()

    @classmethod
    def load(cls, file_name, measurement_dir=MEASUREMENT_DIR):
        """Loads the measurement given its file path"""
        path_to_file = Path(measurement_dir) / file_name
        with open(path_to_file, "r") as f:
            self_as_dict = json.load(f)
        return cls(**self_as_dict)

    @classmethod
    def open(cls, m_id, measurement_dir=MEASUREMENT_DIR):
        """Opens the measurement given its id"""
        path_to_file = next(
            path
            for path in Path(measurement_dir).iterdir()
            if path.stem.startswith(f"m{m_id}")
        )
        return cls.load(path_to_file)

    def make_name(self):
        self.name = (
            f"m{self.id} is {self.sample} measured on {self.measurement_date} by "
            f"{self.technique}"
        )
        return self.name

    def load_dataset(self):
        self.dataset = Dataset(self.old_data_path)
        if self.dataset.empty:
            raise IOError(f"Dataset in {self.old_data_path} loaded empty.")
        return self.dataset

    def save_dataset(self):
        self.dataset.save(self.new_data_path)
        self.copied_at = time.time()
