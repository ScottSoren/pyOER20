import pickle
import numpy as np

from matplotlib import pyplot as plt
from pyOER import all_tof_sets

plt.close("all")

timing_specs = {
    "first": {"markerfacecolor": "w"},
    "next": {"markerfacecolor": "0.75"},
    "steady": {"markerfacecolor": "0.7"},
    "composite": {"markerfacecolor": "0.25"},
    # "full": {"markerfacecolor": "k"},
}
element_specs = {
    "Ir": {"color": "turquoise"},
    "Ru": {"color": "purple"},
    "Pt": {"color": "0.5"},
}
type_specs = {
    "dissolution": {"marker": "^"},
    "exchange": {"marker": "s"},
}
oxide_specs = {
    "rutile": {"color": "k"},
    "amorphous": {"color": "b"},
    "metallic": {"color": "0.5"},
    "hydrous": {"color": "g"},
    "foam": {"color": "c"},
}

fig_Ru, ax_Ru = plt.subplots()
# fig_Ir, ax_Ir = plt.subplots()
# fig_Pt, ax_Pt = plt.subplots()
axes = {
    "Ru": ax_Ru,
    # "Ir": ax_Ir,
    # "Pt": ax_Pt
}

results_sets = {}


def skip_this_sample(sample):
    if "Reshma" in sample.name or "Folk" in sample.name:
        return True  # don't put controls on the plot
    if "John4A" in sample.name:
        return True  # this one seems to have been broken
    if "Nancy" in sample.name:
        return True  # these were diluted a different amount, icpms analysis is wrong.
    if sample.oxide_type in ["hydrous", "metallic", "foam"]:
        return True  # keep it simple for now.


results_file = "results_sets.pkl"

if False:  # go through all the TOFSets (takes a bit)
    for tof_set in all_tof_sets():
        tof_act = tof_set.activity
        experiment = tof_set.experiment
        sample = experiment.sample
        element = sample.element
        oxide_type = sample.oxide_type
        if skip_this_sample(sample):
            continue
        if element not in axes:
            continue

        ax = axes[sample.element]
        if element not in results_sets:
            results_sets[element] = {}
        if oxide_type not in results_sets[element]:
            results_sets[element][oxide_type] = {
                "activity": np.array([]),
                "dissolution": np.array([]),
                "exchange": np.array([]),
            }
        results = results_sets[element][oxide_type]

        specs = {}
        specs.update(oxide_specs[sample.oxide_type])
        try:
            timing_key = next(
                key for key in timing_specs.keys() if key in tof_act.description
            )
        except StopIteration as e:
            print(e)
            print(
                f"not showing timing in plot for {tof_act} because can't "
                f"understand description={tof_act.description}"
            )
            continue
        else:
            if not timing_key in ["steady", "composite"]:
                continue
            #  specs.update(timing_specs[timing_key])

        act_rate = tof_act.rate

        results["activity"] = np.append(results["activity"], act_rate)

        for tof_type in ["dissolution", "exchange"]:
            if tof_type in tof_set:
                tof = tof_set[tof_type]
                rate = tof.rate
                results[tof_type] = np.append(results[tof_type], rate)
                ax.plot(act_rate * 1e12, rate * 1e12, **type_specs[tof_type], **specs)
                ax.annotate(sample.name, xy=[act_rate * 1e12, rate * 1e12])
            else:
                results[tof_type] = np.append(results[tof_type], np.nan)

    with open(results_file, "wb") as f:
        pickle.dump(results_sets, f)

else:
    with open(results_file, "rb") as f:
        results_sets = pickle.load(f)

trends = {}
for element, ax in axes.items():
    ax.set_xlabel("OER rate in [pmol/s]")
    ax.set_ylabel("exchange or dissolution in [pmol/s]")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title(element)

    for oxide_type in ["rutile", "amorphous"]:
        results = results_sets[element][oxide_type]
        act_vec = results["activity"]
        for tof_type in ["exchange", "dissolution"]:
            vec = results[tof_type]
            mask = np.logical_and(
                np.logical_not(np.logical_or(np.isnan(vec), np.isinf(vec))), vec > 0
            )
            log_act = np.log(act_vec[mask])
            log_vec = np.log(vec[mask])
            p = np.polyfit(log_act, log_vec, deg=1)
            trends[(element, oxide_type, tof_type)] = p
            fit_act = np.array([np.min(act_vec[mask]), np.max(act_vec[mask])])
            fit_vec = np.exp(np.log(fit_act) * p[0] + p[1])
            ax.plot(fit_act * 1e12, fit_vec * 1e12, "--", **oxide_specs[oxide_type])
            if True:  # plot the points as well (in case not done above
                ax.plot(
                    act_vec[mask] * 1e12,
                    vec[mask] * 1e12,
                    ".",
                    **oxide_specs[oxide_type],
                    **type_specs[tof_type],
                )
    ax.get_figure().savefig(f"Diss and exc vs act for {element}.png")
    ax.get_figure().savefig(f"Diss and exc vs act for {element}.svg")
