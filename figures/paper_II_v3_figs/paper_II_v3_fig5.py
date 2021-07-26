import json
import numpy as np
from matplotlib import pyplot as plt
from pyOER import StabilityResultsCollection
from pyOER.constants import (
    FARADAY_CONSTANT,
    STANDARD_SPECIFIC_CAPACITANCE,
    STANDARD_SITE_DENSITY,
)

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

fig5_sample_type = "RT-RuO2"
fig5_sample_name = "Reshma1"

if True:  # fig 5a, with stability numbers plotted against total current density.
    fig5a, ax5a = plt.subplots()
    current_positions = {"0.05": 1, "0.15": 2, "0.5": 3, "1.0": 4}
    number_specs = {
        "S_number": {"marker": "^", "color": "k"},
        "S_number_lattice": {"marker": "v", "color": "#54bdebff"},
    }
    for current_point, position in current_positions.items():
        stats = results_collection.get_stats(fig5_sample_type, current_point, "steady")
        for number_name, specs in number_specs.items():
            number, sigma_number = stats[number_name]
            ax5a.plot(position, number, **specs)
            if sigma_number:
                error_specs = specs.copy()
                error_specs.update(marker="_")
                ax5a.plot(
                    [position, position],
                    [number - sigma_number, number + sigma_number],
                    **error_specs,
                )

    ax5a.set_yscale("log")

    ticklabels = ["0.05", "0.15", "0.5", "1.0"]
    ax5a.set_xticks([current_positions[c] for c in ticklabels])
    ax5a.set_xticklabels(ticklabels)
    ax5a.set_ylabel("stability number")
    ax5a.set_xlabel("current density / (mA cm$^{-2}_{geo}$)")
    ax_r = ax5a.twinx()
    ax_r.set_yscale("log")
    ax_r.set_ylim([1 / y for y in ax5a.get_ylim()])
    ax_r.set_ylabel("atoms per O$_2$")

    if forpublication:
        fig5a.savefig("paper_II_v3_fig5a.png")
        fig5a.savefig("paper_II_v3_fig5a.svg")

if True:  # fig 5b, with norm. activity, exchange, and diss. plotted against potential!
    import sys
    from pathlib import Path

    paper_I_figs_path = Path("../paper_I_v5_figs").absolute().resolve()
    sys.path.append(str(paper_I_figs_path))
    from paper_I_v5_fig3 import plot_all_activity_results
    from paper_I_v5_fig5 import get_model_j_norm

    if False:  # calculate mean capacitance of Reshma1 samples.
        cap_exp_list = [
            exp
            for exp in all_activity_experiments()
            if fig5_sample_name in exp.sample_name
        ]
        cap = np.mean([exp.cap for exp in cap_exp_list])
    else:
        cap = 0.0017  # mean capacitance of Reshma1 samples in [F]

    with open("../paper_I_v5_figs/fit_results.json") as f:
        fit_results = json.load(f)
    u_model = np.linspace(1.28, 1.5, 100)
    j_model = get_model_j_norm(u=u_model, **fit_results)  # [A/F
    n_dot_model = j_model / (4 * FARADAY_CONSTANT) * 1e9  # [nmol/s/F]

    fig5b, ax5b = plt.subplots()
    # a factor to convert from TOF in [s^-1] to norm flux in [nmol/s/F]
    factor = STANDARD_SITE_DENSITY / STANDARD_SPECIFIC_CAPACITANCE * 1e9
    plt.rc("lines", markersize=3)
    plot_all_activity_results(ax=ax5b, for_model=True, result="tof", factor=factor)
    plt.rc("lines", markersize=6)
    ax5b.plot(u_model, n_dot_model, "k--")

    current_point_mapping = {
        s: float(s) for s in ["1.0", "0.5", "0.25", "0.15", "0.05"]
    }
    for current_point, j_mA_cm2 in current_point_mapping.items():
        j_norm = j_mA_cm2 * 0.196 * 1e-3 / cap  # [mA/cm^2] --> [A/F]
        n_dot_norm = j_norm / (4 * FARADAY_CONSTANT) * 1e9  # [nmol/s/F]
        u = np.interp(n_dot_norm, n_dot_model, u_model)
        stats = results_collection.get_stats(fig5_sample_type, current_point, "steady")
        for number_name, specs in number_specs.items():
            number, sigma_number = stats[number_name]
            ax5b.plot(u, n_dot_norm / number, **specs)
            if sigma_number:
                error_specs = specs.copy()
                error_specs.update(marker="_")
                ax5b.plot(
                    [u, u],
                    [
                        n_dot_norm / (number - sigma_number),
                        n_dot_norm / (number + sigma_number),
                    ],
                    **error_specs,
                )

    ax5b.set_yscale("log")
    ax5b.set_xlabel("E vs RHE / (V)")
    ax5b.set_ylabel("norm. rate / (pmol s$^{-1}$ F$^{-1}$)")
    ax_r = ax5b.twinx()
    ax_r.set_ylim([l / factor for l in ax5b.get_ylim()])
    ax_r.set_yscale("log")
    ax_r.set_ylabel("turn-over frequency / (s$^{-1}$)")

    if forpublication:
        fig5b.savefig("paper_II_v3_fig5b.png")
        fig5b.savefig("paper_II_v3_fig5b.svg")
