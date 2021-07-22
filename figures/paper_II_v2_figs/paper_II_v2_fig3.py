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


current_point_map = {s: float(s) for s in ["1.0", "0.5", "0.25", "0.15", "0.05"]}
#  The name of each current point and the value of the current


def get_current_point(tof):
    """Return a string which is the nearest current in mA/cm2"""
    j = tof.current * 1e3 / tof.measurement.A_el  # current in uA/cm^2
    errs = list(zip(*[(s, np.abs(f - j)) for s, f in current_point_map.items()]))
    index = int(np.argmin(errs[1]))
    current_point = errs[0][index]
    return current_point


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
        return possibilities[max(possibilities.keys(), key=len)]  # woa, funky

    # okay, hold your horses, four-layer nested dictionary here.
    # Layers are:
    #   1. sample_type (RT-RuO2, ..., IrOx/Ir, ...)
    #   2. current_point (0.5 mA/cm^2, ... 0.05 mA/cm^2)
    #   4. rate_type (activity, dissolution, or exchange)
    #   3. Timespan: start of electrolysis or steady-state
    # Having all of this connected in a relational way with the raw data is why
    # pyOER is such a big package. But it will be done better with ixdat.

    tof_collection = {
        sample_type: {
            current_point: {
                rate_type: {"start": [], "steady": []}
                for rate_type in ["activity", "dissolution", "exchange"]
            }
            for current_point in current_point_map.keys()
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
            current_point = get_current_point(tof)
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
            tof_collection[sample_type][current_point][rate_type][rate_time].append(
                tof.id
            )

    with open("tof_collection.json", "w") as f:
        json.dump(tof_collection, f, indent=4)

else:  # load tof collection
    with open("tof_collection.json", "r") as f:
        tof_collection = json.load(f)


sample_plot_specs = {
    "RT-RuO2": {"color": "#54bdebff", "marker": "o"},
    "400C-RuO2": {"color": "#163854ff", "marker": "o"},
    "cycled RuO2": {"color": "b", "marker": "*", "markersize": 8},
    "RuOx/Ru": {"color": "b", "marker": "s"},
    "Ru foam": {"color": "m", "marker": "s"},
    "RT-IrO2": {"color": "#54ebbdff", "marker": "o"},
    "400C-IrO2": {"color": "#165438ff", "marker": "o"},
    "cycled IrO2": {"color": "g", "marker": "*", "markersize": 8},
    "IrOx/Ir": {"color": "g", "marker": "s"},
}


def nested_update(dict_1, dict_2):
    for key, value in dict_2.items():
        if key in dict_1 and isinstance(dict_1[key], dict):
            nested_update(dict_1[key], dict_2[key])
        else:
            dict_1[key] = value


def get_stats(sample_type, current_point, tof_time):
    stats = {sample_type: {current_point: {"S_number": {}, "S_number_lattice": {}}}}
    diss = np.array(
        [
            TurnOverFrequency.open(t_id).rate
            for t_id in tof_collection[sample_type][current_point]["dissolution"][
                tof_time
            ]
        ]
    )
    diss = diss[~np.isnan(diss)]
    diss = diss[~np.isinf(diss)]
    exc = np.array(
        [
            TurnOverFrequency.open(t_id).rate
            for t_id in tof_collection[sample_type][current_point]["exchange"][tof_time]
        ]
    )
    exc = exc[~np.isnan(exc)]
    exc = exc[~np.isinf(exc)]
    act = np.array(
        [
            TurnOverFrequency.open(t_id).rate
            for t_id in tof_collection[sample_type][current_point]["activity"][tof_time]
        ]
    )
    act = act[~np.isnan(act)]
    act = act[~np.isinf(act)]

    S_number = np.mean(act) / np.mean(diss)
    S_number_lattice = np.mean(act) / np.mean(exc)
    if len(diss) > 1:
        sigma_S = S_number * np.sqrt(
            (np.std(act) / np.mean(act)) ** 2 + (np.std(diss) / np.mean(diss)) ** 2
        )
        stats[sample_type][current_point]["S_number"][tof_time] = [S_number, sigma_S]
    else:
        stats[sample_type][current_point]["S_number"][tof_time] = [S_number, None]
    if len(exc) > 1:
        sigma_S_lattice = S_number_lattice * np.sqrt(
            (np.std(act) / np.mean(act)) ** 2 + (np.std(exc) / np.mean(exc)) ** 2
        )
        stats[sample_type][current_point]["S_number_lattice"][tof_time] = [
            S_number_lattice,
            sigma_S_lattice,
        ]
    else:
        stats[sample_type][current_point]["S_number_lattice"][tof_time] = [
            S_number_lattice,
            None,
        ]

    return stats


if True:  # fig 3a
    fig3a, ax3a = plt.subplots()
    fig3a_sample_type = "RT-RuO2"
    current_positions = {"0.05": 1, "0.15": 2, "0.5": 3, "1.0": 4}
    number_specs = {
        "S_number": {"marker": "^", "color": "k"},
        "S_number_lattice": {"marker": "v", "color": "#54bdebff"},
    }
    for current_point, position in current_positions.items():
        for tof_time in ["steady"]:  # "start",
            stats = get_stats(fig3a_sample_type, current_point, tof_time)
            for number_name, specs in number_specs.items():
                specs["markerfacecolor"] = (
                    "w" if tof_time == "start" else specs["color"]
                )
                number, sigma_number = stats[fig3a_sample_type][current_point][
                    number_name
                ][tof_time]
                ax3a.plot(position, number, **specs)
                if sigma_number:
                    error_specs = specs.copy()
                    error_specs.update(marker="_")
                    ax3a.plot(
                        [position, position],
                        [number - sigma_number, number + sigma_number],
                        **error_specs,
                    )
    ax3a.set_yscale("log")

    ticklabels = ["0.05", "0.15", "0.5", "1.0"]
    ax3a.set_xticks([current_positions[c] for c in ticklabels])
    ax3a.set_xticklabels(ticklabels)
    ax3a.set_ylabel("stability number")
    ax3a.set_xlabel("current density / (mA cm$^{-2}_{geo}$)")
    ax_r = ax3a.twinx()
    ax_r.set_yscale("log")
    ax_r.set_ylim([1 / y for y in ax3a.get_ylim()])
    ax_r.set_ylabel("atoms per O$_2$")

    if forpublication:
        fig3a.savefig("paper_II_fig_3a.png")
        fig3a.savefig("paper_II_fig_3a.svg")


if True:  # fig 3b
    fig3b, ax3b = plt.subplots()
    stats_collection = {}
    fig3b_current_point = "0.5"
    for sample_type, tof_subset in tof_collection.items():
        specs = sample_plot_specs[sample_type]
        for tof_time in ["start", "steady"]:
            stats = get_stats(
                sample_type=sample_type,
                current_point=fig3b_current_point,
                tof_time=tof_time,
            )
            nested_update(stats_collection, stats)
            specs["markerfacecolor"] = "w" if tof_time == "start" else specs["color"]

            S_number, sigma_S = stats_collection[sample_type][fig3b_current_point][
                "S_number"
            ][tof_time]
            S_number_lattice, sigma_S_lattice = stats_collection[sample_type][
                fig3b_current_point
            ]["S_number_lattice"][tof_time]

            ax3b.plot(S_number_lattice, S_number, **specs)

            if sigma_S:
                diss_error_specs = specs.copy()
                diss_error_specs.update(marker="_", linestyle="-", markersize=5)
                ax3b.plot(
                    [S_number_lattice, S_number_lattice],
                    [S_number - sigma_S, S_number + sigma_S],
                    **diss_error_specs,
                )
            if sigma_S_lattice:
                exc_error_specs = specs.copy()
                exc_error_specs.update(marker="|", linestyle="-", markersize=5)
                ax3b.plot(
                    [
                        S_number_lattice - sigma_S_lattice,
                        S_number_lattice + sigma_S_lattice,
                    ],
                    [S_number, S_number],
                    **exc_error_specs,
                )

    lims = [5, 1e5]
    ax3b.set_xlim(lims)
    ax3b.set_ylim(lims)
    ax3b.plot(lims, lims, "k--")

    ax3b.set_xlabel("lattice oxygen stability number")
    ax3b.set_ylabel("metal stability number")
    ax3b.set_xscale("log")
    ax3b.set_yscale("log")

    ax_r = ax3b.twinx()
    ax_r.set_yscale("log")
    ax_r.set_ylim([1 / y for y in ax3b.get_ylim()])
    ax_r.set_ylabel("dissolved metal ions per O$_2$")
    ax_t = ax3b.twiny()
    ax_t.set_xlim([1 / x for x in ax3b.get_xlim()])
    ax_t.set_xscale("log")
    ax_t.set_xlabel("lattice O per O$_2$")

    if forpublication:
        fig3b.savefig("paper_II_fig_3b.png")
        fig3b.savefig("paper_II_fig_3b.svg")
