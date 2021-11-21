import re
from pyOER.tof import all_tofs, TurnOverFrequency
import numpy as np
import json
from matplotlib import pyplot as plt

from pyOER.constants import (
    STANDARD_SPECIFIC_CAPACITANCE,
    STANDARD_SITE_DENSITY,
    STANDARD_ELECTRODE_AREA,
    FARADAY_CONSTANT,
)

forpublication = True

# plt.interactive(False)  # show the plot when I tell you to show() it!

if forpublication:  # for the publication figure
    import matplotlib as mpl

    mpl.rcParams["figure.figsize"] = (3.25, 2.75)
    # plt.rc('text', usetex=True)  # crashingly slow
    plt.rc("font", family="sans-serif")
    plt.rc("font", size=6)
    plt.rc("lines", linewidth=0.5)
    plt.rc("lines", markersize=3)
else:
    plt.style.use("default")


colors = {  # from Reshma's Figure 1.
    "1": "#54bdebff",
    "2": "#308ab2ff",
    "3": "#2e7094ff",
    "4": "#163854ff",
    "5": "m",
}
colors_soren = {"1": "k", "2": "b", "3": "g"}
# colors = colors_soren
markers = {"16": "o", "18": "s"}
number_finder = "([0-4])"


def plot_all_activity_results(
    ax=None,
    result="rate",
    factor=1,
    takelog=False,
    for_model=False,
):

    to_export = {}
    for tof in all_tofs():
        sample_name = tof.sample_name
        if not (
            tof.tof_type in ("activity", "ec_activity")
            and tof.id > 239
            and (
                "Reshma" in sample_name
                or "Rao" in sample_name
                or "Evans" in sample_name
                or "Melih" in sample_name
            )
        ):
            continue

        if sample_name not in to_export:
            to_export[sample_name] = {
                "U_vs_RHE / [V]": [],
                "O2_rate / [nmol/s/cm^2]": [],
                "norm_O2_current / [A/F]": [],
            }
        color = get_color(sample_name)
        rate = tof.rate  # rate in [mol/s]
        potential = tof.potential
        f = tof.tof  # tof in [s^-1]

        if (f > 7e-5 and potential < 1.32) or potential < 1.28:
            try:
                rate, f, potential = fix_bad_tof(tof)
            except FileNotFoundError:
                continue
        if for_model:
            if (
                (potential > 1.45 and not tof.tof_type == "ec_activity")
                or "Rao" in tof.sample_name
                or "Melih" in tof.sample_name
            ):
                continue

        if tof.tof_type == "ec_activity":
            marker = "^"
        else:
            marker = markers.get(tof.measurement.isotope, "o")
        # marker = "o"

        to_export[sample_name]["U_vs_RHE / [V]"].append(potential)
        to_export[sample_name]["O2_rate / [nmol/s/cm^2]"].append(
            rate * 1e9 / STANDARD_ELECTRODE_AREA
        )
        to_export[sample_name]["norm_O2_current / [A/F]"].append(
            f
            * 4
            * FARADAY_CONSTANT
            * STANDARD_SITE_DENSITY
            / STANDARD_SPECIFIC_CAPACITANCE
        )

        to_plot = None
        if result == "rate":
            to_plot = rate * 1e9 * factor / STANDARD_ELECTRODE_AREA
        elif result == "tof":
            to_plot = f * factor

        if not to_plot:
            print(f"Don't know what {result} is. Not plotting.")

        if takelog:
            to_plot = np.log10(to_plot)
        if ax:
            ax.plot(potential, to_plot, color=color, marker=marker, fillstyle="none")
    return to_export


def fix_bad_tof(tof):
    i = tof.id
    tof.experiment.plot()
    print(f"please fix or delete '{tof}' with tspan={tof.tspan}")
    plt.show()
    try:
        tof = TurnOverFrequency.open(i)
    except FileNotFoundError:
        raise
    rate = tof.calc_rate()  # needs to be updated.
    f = tof.calc_tof()
    potential = tof.calc_potential()
    tof.save()  # save updates.
    return rate, f, potential


def get_color(sample_name):
    if "Reshma" in sample_name:
        try:
            T_number = re.search(number_finder, sample_name).group(1)
        except AttributeError:
            return "y"
        else:
            return colors[T_number]
    elif "Evans" in sample_name:
        return "g"
    elif "Melih" in sample_name:
        return "m"
    elif "Rao" in sample_name:
        return "orange"
    else:
        return "y"


fig1, ax1 = plt.subplots()
fig2, ax2b = plt.subplots()
ax2 = ax2b.twinx()

to_export = plot_all_activity_results(ax=ax1, result="rate")
plot_all_activity_results(ax=ax2, result="tof")

with open("results_json.txt", "w") as f:
    json.dump(to_export, f, indent=4)

ax1.set_ylabel("rate / (nmol s$^{-1}$cm$^{-2}_{geo}$)")
ax1.set_xlabel("E vs RHE / (V)")
ax1.set_yscale("log")
ax1b = ax1.twinx()
ax1b.set_yscale("log")
ax1b.set_ylim([l * 4 * FARADAY_CONSTANT * 1e-6 for l in ax1.get_ylim()])
ax1b.set_ylabel("$j_{O2}$ / (mA cm$^{-2}_{geo}$)")


ax2.set_xlabel("E vs RHE / (V)")
ax2.set_yscale("log")

tof_lim = ax2.get_ylim()
norm_flux_lim = [
    lim * STANDARD_SITE_DENSITY / STANDARD_SPECIFIC_CAPACITANCE * 4 * FARADAY_CONSTANT
    for lim in tof_lim
]
ax2b.set_ylim(norm_flux_lim)
ax2b.set_xlabel("E vs RHE / (V)")
ax2b.set_yscale("log")
ax2b.set_ylabel("OER current$_{cap}$ / (A F$^{-1}$)")

if True:  # a TOF axis
    ax2.set_ylabel("TOF / (s$^{-1}$)")
else:  # no TOF axis
    ax2.set_yticks([])
    ax2.yaxis.set_tick_params(which="both", right=False)
    ax2.set_ylabel("")

#  [1/s] * [mol/cm^2] / [F/cm^2] * [C/mol] = [A/F]


if forpublication or True:
    # fig1.subplots_adjust(left=0.15, right=0.85)
    fig1.savefig("all_Ru_rates.png")
    fig1.savefig("all_Ru_rates.svg")
    fig2.subplots_adjust(left=0.15, right=0.85)
    fig2.savefig("all_Ru_tofs.png")
    fig2.savefig("all_Ru_tofs.svg")
