"""This module groups TurnOverFrequency's for plotting and analysis"""

import json
import numpy as np
from .experiment import all_standard_experiments


def nested_update_with_layers(new_dict, old_dict, layers, **kwargs):

    for layer_name in kwargs:
        if layer_name not in layers:
            key = kwargs.pop(layer_name)
            print(f"Can't filter based in {layer_name}={key} "
                  f"because {key} is not in layers={layers}. This will be ignored.")
    if layers[0] in kwargs:
        new_kwargs = kwargs.copy()
        key = new_kwargs.pop(layers[0])
        nested_update_with_layers(new_dict, old_dict[key], layers[1:], **new_kwargs)
    for key, value in new_dict:
        if key in old_dict and isinstance(old_dict, dict):
            nested_update_with_layers(
                new_dict[key], old_dict[key], layers[1:], **kwargs
            )
        else:
            new_dict[key] = value


def get_sample_type(sample, sample_mapping):
    """Return the key in sample_mapping that has a match to the start of sample

    If two sample types include a sample name base in their sample name list that match
    the start of sample, then return the one matching sample more specificically, i.e.
    that with the longest match.
    """
    possibilities = {
        s: s_type
        for (s_type, s_list) in sample_mapping.items()
        for s in s_list
        if sample.startswith(s)
    }
    return possibilities[max(possibilities.keys(), key=len)]  # woa, funky code :D


def get_current_point(tof, current_point_mapping):
    """Return a string which is the nearest current in mA/cm2"""
    j = tof.current * 1e3 / tof.measurement.A_el  # current in uA/cm^2
    errs = list(zip(*[(s, np.abs(f - j)) for s, f in current_point_mapping.items()]))
    index = int(np.argmin(errs[1]))
    current_point = errs[0][index]
    return current_point


class StabilityResultsCollection:

    def __init__(
            self,
            tof_collection,
            layers=("sample_type", "current_point", "result_time", "result_type"),
            sample_mapping=None,
            current_point_mapping=None
    ):
        # okay, hold your horses, four-layer nested dictionary here.
        # Layers are (in the order that you'd index the dictionary):
        #   1. sample_type (RT-RuO2, ..., IrOx/Ir, ...).
        #   2. current_point (0.5 mA/cm^2, ... 0.05 mA/cm^2)
        #   3. Timespan: start of electrolysis or steady-state
        #   4. rate_type (activity, dissolution, or exchange)
        # Having all of this connected in a relational way with the raw data is why
        # pyOER is such a big package. But it will be done better with ixdat.

        # tof_collection will have a list of tof_id's (remember tof is the
        # unfortunate name given to the main results table in pyOER)
        self.tof_collection = tof_collection
        self.layers = layers
        if not tof_collection:
            self.generate_tof_collection(sample_mapping, current_point_mapping)

    def generate_tof_collection(self, sample_mapping, current_point_mapping):
        tof_collection = {
            sample_type: {
                current_point: {
                    tof_time: {
                        rate_type: []
                        for rate_type in ["activity", "dissolution", "exchange"]
                    }
                    for tof_time in ["start", "steady"]
                }
                for current_point in current_point_mapping.keys()
            }
            for sample_type in sample_mapping.keys()
        }

        for e in all_standard_experiments():
            try:
                sample_type = get_sample_type(e.sample_name, sample_mapping)
            except ValueError:
                print(f"couldn't find a sample type match for {e}. Skipping.")
                continue
            tofs = e.get_tofs()
            for tof in tofs:
                rate_type = tof.tof_type
                current_point = get_current_point(tof, current_point_mapping)
                if "steady" in tof.description or "composite" in tof.description:
                    rate_time = "steady"
                elif "start" in tof.description or "first" in tof.description:
                    rate_time = "start"
                else:
                    print(
                        f"{tof} with description = '{tof.description}' as "
                        f"it seems to be neither start nor steady"
                    )
                    continue
                tof_collection[sample_type][current_point][rate_time][rate_type].append(
                    tof.id
                )

        self.tof_collection = tof_collection

    def __getitem__(self, key):
        return StabilityResultsCollection(
            tof_collection=self.tof_collection[key],
            layers=self.layers[1:]
        )

    def get_sub_collection(self, **kwargs):
        new_tof_collection = {}
        old_tof_collection = self.tof_collection.copy()

        new_layers = []
        for i, layer in enumerate(self.layers):
            if layer not in kwargs:
                new_layers.append(layer)

        nested_update_with_layers(
            new_tof_collection, old_tof_collection, self.layers, **kwargs
        )
        return StabilityResultsCollection(
            tof_collection=new_tof_collection, layers=tuple(new_layers)
        )

    def as_dict(self):
        return {"tof_collection": self.tof_collection, "layers": self.layers}

    def save(self, path_to_file):
        with open(path_to_file, "w") as f:
            json.dump(self.as_dict(), f)

    @classmethod
    def read(cls, path_to_file):
        with open(path_to_file, "r") as f:
            self_as_dict = json.load(f)
        return cls(**self_as_dict)

