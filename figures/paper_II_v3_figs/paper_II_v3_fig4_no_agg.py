import numpy as np
from matplotlib import pyplot as plt
from pyOER import StabilityResultsCollection


forpublication = True
if forpublication:  # for the publication figure
    import matplotlib as mpl

    mpl.rcParams["figure.figsize"] = (3.25, 2.75)
    # plt.rc('text', usetex=True)  # crashingly slow
    plt.rc("font", family="sans-serif")
    plt.rc("font", size=8)
    plt.rc("lines", linewidth=0.6)
else:
    plt.style.use("default")


results_collection = StabilityResultsCollection.open("results_collection.json")

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

fig, ax = plt.subplots()
stats_collection = {}
current_point = "0.5"
for sample_type in results_collection:
    specs = sample_plot_specs[sample_type]

    start_results = results_collection.get_coherent_results(
        sample_type, current_point, "start"
    )
    start_S_diss = start_results["activity"] / start_results["dissolution"]
    start_S_exc = start_results["activity"] / start_results["exchange"]
    ax.plot(start_S_exc, start_S_diss, markerfacecolor="w", linestyle="", **specs)

    steady_results = results_collection.get_coherent_results(
        sample_type, current_point, "steady"
    )
    steady_S_diss = steady_results["activity"] / steady_results["dissolution"]
    steady_S_exc = steady_results["activity"] / steady_results["exchange"]
    ax.plot(
        steady_S_exc,
        steady_S_diss,
        markerfacecolor=specs["color"],
        linestyle="",
        **specs
    )

lims = [5, 1e5]
ax.set_xlim(lims)
ax.set_ylim(lims)
ax.plot(lims, lims, "k--")

ax.set_xlabel("lattice oxygen stability number")
ax.set_ylabel("metal stability number")
ax.set_xscale("log")
ax.set_yscale("log")

ax_r = ax.twinx()
ax_r.set_yscale("log")
ax_r.set_ylim([1 / y for y in ax.get_ylim()])
ax_r.set_ylabel("dissolved metal ions per O$_2$")
ax_t = ax.twiny()
ax_t.set_xlim([1 / x for x in ax.get_xlim()])
ax_t.set_xscale("log")
ax_t.set_xlabel("lattice O per O$_2$")

if forpublication:
    fig.savefig("paper_II_v3_fig4_no_agg.png")
    fig.savefig("paper_II_v3_fig4_no_agg.svg")
