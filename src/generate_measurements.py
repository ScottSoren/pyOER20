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
MEASUREMENT_DIR = Path("../measurements")

MATCHERS = {
    "sample": r"([A-Z][a-z]+[0-9]+[A-Z]?)",
    "measurement_date": r"([0-9]{2}[A-L][0-9]{2})",
    "isotope": r"(?:(16|18)O|O(16|18))",
}


def get_pickle_paths(parent_path):
    pps = []  # pickle_paths
    for f in parent_path.iterdir():
        path = parent_path / f
        if path.is_dir():
            pps += get_pickle_paths(path)
        elif path.suffix == ".pkl":
            pps += [path]
    return pps


def main():
    pickle_paths = []
    for data_directory in OLD_DATA_DIRECTORIES:
        pickle_paths += get_pickle_paths(data_directory)

    measurement_counter = MeasurementCounter()
    m_id = measurement_counter.id

    non_dataset_pickles = []

    for path in pickle_paths:
        specs = {}
        for name, matcher in MATCHERS.items():
            match = re.search(matcher, str(path))
            if match:
                specs[name] = match.group(1)

        measurement = Measurement(
            m_id=m_id, old_data_path=str(path), technique="ECMS", **specs,
        )
        try:
            measurement.load_dataset()
        except (IOError, TypeError) as e:
            print(f"Not an EC_MS pickle: \n\t{path}\n\tError = {e}")
            non_dataset_pickles += [str(path)]
            continue
        del measurement.dataset  # to save memory
        measurement.save()

        m_id = measurement_counter.id

    with open(MEASUREMENT_DIR / "non_ECMS_dataset_pickles.txt", "w") as f:
        f.writelines([line + "\n" for line in non_dataset_pickles])


if __name__ == "__main__":
    main()
