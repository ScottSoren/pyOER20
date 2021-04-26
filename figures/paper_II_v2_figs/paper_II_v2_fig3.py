import json
import numpy as np
from matplotlib import pyplot as plt
from pyOER import all_standard_experiments, TurnOverFrequency

forpublication = True
if forpublication:  # for the publication figure
    import matplotlib as mpl

    mpl.rcParams["figure.figsize"] = (3.25, 2.75)
    # plt.rc('text', usetex=True)  # crashingly slow
    plt.rc("font", family="sans-serif")
    plt.rc("font", size=6)
    plt.rc("lines", linewidth=0.5)
else:
    plt.style.use("default")

if False:  # generate tof collection
    sample_mapping = {
        "RT-RuO2": ["Taiwan", "Easter"],
        "400C-RuO2": ["Maundy", "Stoff", "Sofie", "Mette", "John"],
        "cycled RuO2": [
            "Taiwan1G",
        ],
        "RuOx/Ru": [
            "Bernie",
        ],
        "Ru foam": [
            "Evans12",
        ],
        "RT-IrO2": ["Goof", "Decade"],
        "400C-IrO2": ["Legend", "Champ"],
        "cycled IrO2": ["Decade1G", "Legend4C"],
        "IrOx/Ir": [
            "Jazz",
        ],
    }

    def get_sample_type(sample):
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
        return possibilities[max(possibilities.keys(), key=len)]

    tof_collection = {
        sample_type: {
            rate_type: {"start": [], "steady": []}
            for rate_type in ["activity", "dissolution", "exchange"]
        }
        for sample_type in sample_mapping.keys()
    }

    for e in all_standard_experiments():
        try:
            sample_type = get_sample_type(e.sample_name)
        except ValueError:
            print(f"couldn't find a sample type match for {e}. Skipping.")
            continue
        tofs = e.get_tofs()
        for tof in tofs:
            rate_type = tof.tof_type
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
            tof_collection[sample_type][rate_type][rate_time].append(tof.id)

    with open("tof_collection.json", "w") as f:
        json.dump(tof_collection, f, indent=4)

else:  # load tof collection
    with open("tof_collection.json", "r") as f:
        tof_collection = json.load(f)


sample_plot_specs = {
    "RT-RuO2": {"color": "#54bdebff", "marker": "o"},
    "400C-RuO2": {"color": "#163854ff", "marker": "o"},
    "cycled RuO2": {"color": "b", "marker": "*"},
    "RuOx/Ru": {"color": "b", "marker": "s"},
    "Ru foam": {"color": "m", "marker": "s"},
    "RT-IrO2": {"color": "#54ebbdff", "marker": "o"},
    "400C-IrO2": {"color": "#165438ff", "marker": "o"},
    "cycled IrO2": {"color": "g", "marker": "*"},
    "IrOx/Ir": {"color": "g", "marker": "s"},
}


fig, ax = plt.subplots()
results_collection = {}
for sample_type, tof_subset in tof_collection.items():
    specs = sample_plot_specs[sample_type]
    results_collection[sample_type] = {
        tof_type: {} for tof_type in ["activity", "exchange", "dissolution"]
    }
    for tof_time in ["start", "steady"]:
        specs["markerfacecolor"] = "w" if tof_time == "start" else specs["color"]
        diss = np.array(
            [
                TurnOverFrequency.open(t_id).rate
                for t_id in tof_subset["dissolution"][tof_time]
            ]
        )
        diss = diss[~np.isnan(diss)]
        diss = diss[~np.isinf(diss)]
        exc = np.array(
            [
                TurnOverFrequency.open(t_id).rate
                for t_id in tof_subset["exchange"][tof_time]
            ]
        )
        exc = exc[~np.isnan(exc)]
        exc = exc[~np.isinf(exc)]
        act = np.array(
            [
                TurnOverFrequency.open(t_id).rate
                for t_id in tof_subset["activity"][tof_time]
            ]
        )
        act = act[~np.isnan(act)]
        act = act[~np.isinf(act)]
        results_collection[sample_type]["dissolution"][tof_time] = diss
        results_collection[sample_type]["exchange"][tof_time] = exc
        results_collection[sample_type]["activity"][tof_time] = act

        S_number = np.mean(act) / np.mean(diss)
        S_number_lattice = np.mean(act) / np.mean(exc)
        ax.plot(S_number_lattice, S_number, **specs)

ax.set_xlabel("lattice stability number")
ax.set_ylabel("stability number")
ax.set_xscale("log")
ax.set_yscale("log")
lims = [5, 1e5]
ax.set_xlim(lims)
ax.set_ylim(lims)
ax.plot(lims, lims, "k--")

if forpublication:
    fig.savefig("paper_II_fig_3b.png")
    fig.savefig("paper_II_fig_3b.svg")
