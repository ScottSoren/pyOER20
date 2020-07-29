"""This module defines the ElogEntry and functions for parsing elog html
See: https://elog.psi.ch/elog/

Made for DTU SurfCat's cinfelog by Soren B. Scott on July 29, 2020
"""
from pathlib import Path
import json

ELOG_DIR = Path("../../elog")
SETUP = "ECMS"


def read_elog_html(path_to_elog_file):
    with open(path_to_elog_file) as f:
        lines = f.readlines()


class ElogEntry:
    """simple data class summarizing contents of an elog entry"""

    def __init__(
        self,
        setup,
        number,
        date=None,
        field_metadata=None,
        sample_measurements=None,
        notes=None,
    ):
        self.setup = setup
        self.number = number
        self.date = date
        self.field_metadata = field_metadata
        self.notes = notes
        self.sample_measurements = sample_measurements

    @classmethod
    def load(cls, file_name, measurement_dir=ELOG_DIR):
        """Load the elog entry given its file name and dir"""
        path_to_file = Path(measurement_dir) / file_name
        with open(path_to_file, "r") as f:
            self_as_dict = json.load(f)
        return cls(**self_as_dict)

    @classmethod
    def open(cls, e_id, setup=SETUP, measurement_dir=ELOG_DIR):
        """Open the elog entry given its id"""
        path_to_file = next(
            path
            for path in Path(measurement_dir).iterdir()
            if path.stem.startswith(f"{setup} e{e_id}")
        )
        return cls.load(path_to_file)

    def save(self, file_name=None, elog_dir=ELOG_DIR):
        """Save the elog entry, uses self.get_name for file name by default"""
        self_as_dict = self.as_dict()
        if not file_name:
            file_name = self.get_name
        path_to_json = (Path(elog_dir) / file_name).with_suffix(".json")
        with open(path_to_json, "w") as f:
            json.dump(self_as_dict, f, indent=4)

    def as_dict(self):
        """Return a dictionary representation of the elog entry"""
        self_as_dict = dict(
            setup=self.setup,
            number=self.number,
            date=self.date,
            field_metadata=self.field_metadata,
            notes=self.notes,
            sample_measurements=self.sample_measurements,
        )
        return self_as_dict

    def get_name(self):
        return f"{self.setup} e{self.number} {self.date}"
