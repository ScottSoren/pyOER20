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


if True:  # fig 3a
    fig3a, ax3a = plt.subplots()
    fig3a_sample_type = "RT-RuO2"
    current_positions = {"0.05": 1, "0.15": 2, "0.5": 3, "1.0": 4}
    number_specs = {
        "S_number": {"marker": "^", "color": "k"},
        "S_number_lattice": {"marker": "v", "color": "#54bdebff"},
    }
    for current_point, position in current_positions.items():
        stats = results_collection.get_stats(fig3a_sample_type, current_point, "steady")
        for number_name, specs in number_specs.items():
            number, sigma_number = stats[number_name]
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
