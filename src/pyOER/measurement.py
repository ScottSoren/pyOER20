"""Define the Measurement class containing metadata and pointers to raw data.

"""
from pathlib import Path, PureWindowsPath, PurePosixPath
import json
import re
import time
import datetime
from EC_MS import Dataset
from .tools import singleton_decorator, CounterWithFile
from .settings import DATA_DIR

MEASUREMENT_DIR = Path(__file__).absolute().parent.parent.parent / "measurements"
MEASUREMENT_ID_FILE = MEASUREMENT_DIR / "LAST_MEASUREMENT_ID.pyoer20"

if not MEASUREMENT_DIR.exists():
    print(f"Creating new directory:\r\n{MEASUREMENT_DIR}")
    Path.mkdir(MEASUREMENT_DIR)
    with open(MEASUREMENT_ID_FILE, "w") as f:
        f.write("0")


@singleton_decorator
class MeasurementCounter(CounterWithFile):
    """Counts measurements. 'id' increments the counter. 'last()' retrieves last id"""

    _file = MEASUREMENT_ID_FILE


def all_measurements(measurement_dir=MEASUREMENT_DIR):
    """returns an iterator that yields measurements in order of their id"""
    N_measurements = MeasurementCounter().last()
    for n in range(1, N_measurements):
        try:
            measurement = Measurement.open(n, measurement_dir=measurement_dir)
        except FileNotFoundError as e:
            print(f"itermeasurement skipping {n} due to error = \n{e}")
        else:
            yield measurement


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
        date=None,
        analysis_date=None,
        old_data_path=None,
        new_data_path=None,
        dataset=None,
        linked_measurements=None,
        elog_number=None,
        elog=None,
        EC_tag=None,
        category=None,
        **kwargs,
    ):
        """Initiate Measurement object

        Intended use is to load the dataset separately using Measurement.load_dataset()

        Args:
            m_id (int): the unique id of the measurement
            name (str): the name of the measurement
            measurement_dir (Path-like): where to SAVE the measurement metadata
            copied_at (float): the time at which the dataset was read
            old_data_path (Path-like): path to file to load the raw data from pkl
            new_data_path (Path-like): path to file to SAVE the raw data as pkl
            dataset (EC_MS.Dataset): the dataset
            linked_measurements (dict): measurements to link to this one
            kwargs (dict): gets added, not used. Here so that I can add extra stuff when
                saving just to improve readability of the json
        """
        if not m_id:
            m_id = MeasurementCounter().id
        self.id = m_id
        self.name = name
        self.sample = sample
        self.technique = technique
        self.isotope = isotope
        self.date = date
        self.analysis_date = analysis_date
        self.measurement_dir = measurement_dir
        self.copied_at = copied_at  # will be replaced by time.time()
        self.old_data_path = old_data_path
        self.new_data_path = new_data_path
        self._dataset = dataset  # dataset is a managed property
        self.linked_measurements = linked_measurements
        self.extra_stuff = kwargs
        self.elog_number = elog_number
        self._elog = elog  # elog is a managed property
        self.EC_tag = EC_tag
        self.category = category

    def as_dict(self):
        self_as_dict = dict(
            id=self.id,
            name=self.name,
            sample=self.sample,
            technique=self.technique,
            isotope=self.isotope,
            date=self.date,
            analysis_date=self.analysis_date,
            measurement_dir=str(self.measurement_dir),
            copied_at=self.copied_at,
            old_data_path=str(self.old_data_path),
            new_data_path=str(self.new_data_path),
            linked_measurements=self.linked_measurements,
            elog_number=self.elog_number,
            EC_tag=self.EC_tag,
            category=self.category,
            # do not put the dataset into self_as_dict!
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

    def save_with_rename(self, file_name=None):
        if "file_loaded_from" in self.extra_stuff:
            Path(str(self.extra_stuff["file_loaded_from"])).unlink()
        self.save(file_name=file_name)

    @classmethod
    def load(cls, file_name, measurement_dir=MEASUREMENT_DIR):
        """Loads the measurement given its file path"""
        path_to_file = Path(measurement_dir) / file_name
        with open(path_to_file, "r") as f:
            self_as_dict = json.load(f)
        self_as_dict.update(file_loaded_from=path_to_file)
        if "id" in self_as_dict:
            self_as_dict["m_id"] = self_as_dict.pop("id")

        # Change hardcoded path to relative path
        # Should work both Windows -> Linux/Mac and Linux/Mac -> Windows
        # as long as the path specified in measurement file is absolute
        # Only tested Windows -> Linux and Windows -> Windows
        for key in ["old_data_path", "new_data_path"]:
            if self_as_dict[key] != "None":
                if ":" in self_as_dict[key]:
                    path_type = PureWindowsPath
                elif "/" == self_as_dict[key][0]:
                    path_type = PurePosixPath
                else:
                    print(type(self_as_dict[key]), repr(self_as_dict[key]))
                    raise TypeError(
                        f"Could not detect whether {self_as_dict[key]} \
                        was Windows or Posix path"
                    )
                path_parts_list = path_type(self_as_dict[key]).parts
                for i, part in enumerate(path_parts_list):
                    if part == DATA_DIR.name:
                        self_as_dict[key] = str(
                            DATA_DIR.joinpath(*path_parts_list[i + 1 :])
                        )
                        # pycharm complains about using "i" after the loop.
                        break
                else:
                    print("Could not convert PureWindowsPath to local path!")
        # Probably not used, but might as well save the correct path here too
        self_as_dict["measurement_dir"] = str(MEASUREMENT_DIR)
        return cls(**self_as_dict)

    @classmethod
    def open(cls, m_id, measurement_dir=MEASUREMENT_DIR):
        """Opens the measurement given its id"""
        try:
            path_to_file = next(
                path
                for path in Path(measurement_dir).iterdir()
                if path.stem.startswith(f"m{m_id}")
            )
        except StopIteration:
            raise FileNotFoundError(f"no measurement with id = m{m_id}")
        return cls.load(path_to_file)

    def __repr__(self):
        return self.make_name()

    def make_name(self):
        """make a name for self from its id, sample, category, date, and technique"""
        category_string = "u"  # u for uncategorized
        if isinstance(self.category, (list, tuple)):
            category_string = self.category[0]
            for cat in self.category[1:]:
                category_string += f" and {cat}"
        elif self.category:
            category_string = self.category
        self.name = (
            f"m{self.id} is {self.sample} {category_string} on {self.date}"
            f" by {self.technique}"
        )
        return self.name

    @property
    def dataset(self):
        """The EC_MS dataset associated with the measurement"""
        if not self._dataset:
            self.load_dataset()
        return self._dataset

    @property
    def elog(self):
        if not self._elog:
            self.open_elog()
        return self._elog

    def load_dataset(self):
        """load the dataset from the EC_MS pkl file"""
        #  data_path = fix_data_path(self.old_data_path)  # Jakob, write this!!!
        data_path = self.old_data_path  # Until fix_data_path is available.
        self._dataset = Dataset(data_path)
        if self._dataset.empty:
            raise IOError(f"Dataset in {self.old_data_path} loaded empty.")
        return self._dataset

    def save_dataset(self):
        """SAVE the dataset in the new data directory"""
        name = self.name if self.name else self.make_name()
        path_to_pkl = self.new_data_path / (name + ".pkl")
        self.dataset.save(file_name=path_to_pkl)
        self.copied_at = time.time()

    def plot_experiment(self, *args, **kwargs):
        """shortcut to self.dataset.plot_experiment"""
        return self.dataset.plot_experiment(*args, **kwargs)

    def open_elog(self):
        from .elog import ElogEntry

        self._elog = ElogEntry.open(self.elog_number)

    def print_notes(self):
        if not self.elog:
            try:
                self.open_elog()
            except FileNotFoundError:
                print(f"{self.name} has no elog!")
                return
        notes = self.elog.notes
        if self.EC_tag:
            try:
                EC_tag_match = re.search(fr"\n{self.EC_tag}", notes)
            except TypeError:
                print(f"problem searching for '{self.EC_tag}' in:\n{notes}")
                return
            # ^ note, EC_tag has the "..." already in it.
            if EC_tag_match:
                notes = (
                    notes[0 : EC_tag_match.start()]
                    + "\n# ======================================== #\n"
                    + "# ===   MEASUREMENT NOTES START HERE   === #\n"
                    + "# vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv #"
                    + notes[EC_tag_match.start() :]
                )
        print(notes)
