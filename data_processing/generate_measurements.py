"""This top-level module will organize all EC_MS data
I don't actually think it's necessary to copy it.
"""

from pathlib import Path
import re
from pyOER import Measurement, MeasurementCounter

OLD_DATA_DIRECTORIES = [
    Path("../../Data/ECMS").absolute().resolve(),
    Path("../../Analysis").absolute().resolve(),
]
NEW_DATA_DIRECTORY = Path("../data/EC_MS_pickles")
MEASUREMENT_DIR = Path("../tables/measurements")

MATCHERS = {
    "sample": r"([A-Z][a-z]+[0-9]+[A-Z]?)",
    "measurement_date": r"([0-9]{2}[A-L][0-9]{2})",
    "isotope": r"(?:(16|18)O|O(16|18))",
}

NON_DATASETS_FILE = MEASUREMENT_DIR / "non_ECMS_dataset_pickles.txt"


def get_pickle_paths(parent_path):
    pps = []  # pickle_paths
    for f in parent_path.iterdir():
        path = parent_path / f
        if path.is_dir():
            pps += get_pickle_paths(path)
        elif path.suffix == ".pkl":
            pps += [path]
    return pps


def read_metadata_from_path(path):
    metadata = {}
    for name, matcher in MATCHERS.items():
        match = re.search(matcher, str(path))
        if match:
            metadata[name] = match.group(1)
    return metadata


def check_if_EC_MS_pickle(measurement):
    try:
        measurement.load_dataset()
    except (IOError, TypeError) as e:
        print(f"Not an EC_MS pickle: \n\t{measurement.old_data_path}\n\tError = {e}")
        return False
    else:
        return True
    finally:
        print("made it to the finally clause!")  # test
        del measurement.dataset  # to SAVE memory


def main():
    pickle_paths = []
    for data_directory in OLD_DATA_DIRECTORIES:
        pickle_paths += get_pickle_paths(data_directory)

    measurement_counter = MeasurementCounter()
    m_id = measurement_counter.id

    non_dataset_pickles = []

    for path in pickle_paths:
        specs = read_metadata_from_path(path)

        measurement = Measurement(
            m_id=m_id,
            old_data_path=str(path),
            technique="ECMS",
            **specs,
        )
        if check_if_EC_MS_pickle(measurement):
            measurement.save()
        else:
            non_dataset_pickles += [path]

        m_id = measurement_counter.id

    with open(NON_DATASETS_FILE, "w") as f:
        f.writelines([line + "\n" for line in non_dataset_pickles])


if __name__ == "__main__":
    main()
