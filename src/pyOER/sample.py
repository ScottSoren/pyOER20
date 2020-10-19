"""this module will define the sample object grouping experiments and results"""

import json

from .constants import SAMPLE_DIR
from .measurement import Measurement, all_measurements

SAMPLE_TYPES = {
    "Ru": {
        "hydrous": ["Taiwan1G",],
        "metallic": ["Melih", "Bernie"],
        "foam": "Evans",
        "rutile": ["Reshma4", "Maundy", "Stoff", "Sofie", "Mette", "John"],
        "amorphous": ["Reshma1", "Nancy", "Easter", "Taiwan"],
    },
    "Ir": {
        "hydrous": ["Legend1C", "Decade1G"],
        "metallic": "Jazz",
        "rutile": ["Folk", "Champ", "Legend"],
        "amorphous": ["Goof", "Decade"],
    },
    "Pt": {"metallic": "Trimi"},
}

SAMPLE_ISOTOPES = {
    "16": ["Reshma", "Folk"],
    "18": [
        "Maundy",
        "Stoff",
        "Sofie",
        "Mette",
        "John",
        "Easter",
        "Taiwan",
        "Champ",
        "Legend",
        "Goof",
        "Decade",
    ],
    "(check!)": ["Melih", "Bernie", "Evans", "Nancy", "Jazz", "Trimi"],
}


def get_element_and_type(name, get="both"):
    for element, oxide_types in SAMPLE_TYPES.items():
        for oxide_type, sample_names in oxide_types.items():
            for sample_name in (
                [sample_names] if isinstance(sample_names, str) else sample_names
            ):
                if name.startswith(sample_name):
                    if get == "element":
                        return element
                    elif get in ["type", "crystallinity", "oxide_type"]:
                        return oxide_type
                    return element, oxide_type
    return "unknown"


def get_isotope(name):
    for isotope, sample_names in SAMPLE_ISOTOPES:
        for sample in [sample_names] if isinstance(sample_names, str) else sample_names:
            if name.startswith(sample):
                return isotope
    return "unknown"


class Sample:
    def __init__(self, name, history=None):
        self.name = name
        self.history = history or {}

    def as_dict(self):
        return dict(name=self.name, history=self.history)

    def save(self):
        file = SAMPLE_DIR / (self.name + ".json")
        self_as_dict = self.as_dict()
        with open(file, "w") as f:
            json.dump(self_as_dict, f)

    @classmethod
    def load(cls, path_to_file):
        with open(path_to_file, "w") as f:
            self_as_dict = json.load(f)
        return cls(**self_as_dict)

    @classmethod
    def open(cls, name):
        path_to_file = SAMPLE_DIR / (name + ".json")
        return cls.load(path_to_file)

    def __repr__(self):
        return f"{self.__class__}({self.name})"

    @property
    def isotope(self):
        return get_isotope(self.name)

    @property
    def element(self):
        return get_element_and_type(self.name, get="element")

    @property
    def oxide_type(self):
        return get_element_and_type(self.name, get="oxide_type")

    def describe(self):
        return f"{self.name} is {self.element} {self.oxide_type} with oxygen {self.isotope}"

    @property
    def description(self):
        return self.describe()

    @property
    def measurement_ids(self):
        ml = []
        for m in all_measurements():
            if m.sample_name == self.name:
                ml += [m]
        return ml

    @property
    def measurements(self):
        m_ids = self.measurement_ids
        ms = [Measurement.open(m_id) for m_id in m_ids]
        # sort by tstamp:
        ms, _ = zip(*sorted([(m.tstamp, m) for m in ms]))
        return ms

    def generate_history(self):
        measurements = self.measurements
        N = len(measurements)
        for (i, m) in enumerate(measurements):
            m_str = "m" + str(m.id)
            m.print_notes()
            print(f"\n\nNotes of Measurement {i} of {N}, {m}, are above.")
            if m_str in self.history:
                print(f"Current history to overwrite: '{self.history[m_str]}'")
            print(
                f"Close the plot when ready to describe {self.name} "
                f"at the START of measurement {i} of {N}!"
            )
            ax = m.plot_experiment()
            ax[1].set_title(m)
            ax.show()
            description = input(
                f"Please describe {self.name} at the START of this measurement! "
                f"'q'=quit"
            )
            if description == "q":
                break
            elif description:
                self.history[m_str] = description
