"""This top-level module will organize all EC_MS data
I don't actually think it's necessary to copy it.
"""

from pathlib import Path
from pyOER import Measurement
from pyOER.measurement import all_measurements
from data_processing.generate_measurements import (
    get_pickle_paths,
    read_metadata_from_path,
    check_if_EC_MS_pickle,
)

MEASUREMENT_DIR = Path("../measurements")

KNOWN_PICKLES = {m.old_data_path: m.id for m in all_measurements()}

elog_entries = {"20E13 Mette": 330}


def known_elog_from_path(path):
    for key, n_elog in elog_entries.items():
        if key in str(path):
            return n_elog


def add_folder(path, technique="ECMS"):
    pickle_paths = get_pickle_paths(path)
    non_dataset_pickles = []
    m_id = None
    for path in pickle_paths:
        if path in KNOWN_PICKLES:
            print(f"Skipping already-known pickle in m{KNOWN_PICKLES[path]}:\n\t{path}")
            continue
        specs = read_metadata_from_path(path)
        if technique:
            specs.update(technique=technique)
        n_elog = known_elog_from_path(path)
        if n_elog:
            specs.update(elog_number=n_elog)

        measurement = Measurement(
            old_data_path=path,
            m_id=m_id,
            **specs,
        )
        if check_if_EC_MS_pickle(measurement):
            measurement.save_with_rename()
            m_id = None
        else:
            non_dataset_pickles += [path]
            m_id = measurement.id  # SAVE that id for the next one


def main():
    new_data_dir = Path(
        r"C:\Users\scott\Dropbox (Spectro Inlets)\Soren_DTU\DTU-MIT RuO2\Choongman"
    )
    add_folder(new_data_dir)


if __name__ == "__main__":
    main()
