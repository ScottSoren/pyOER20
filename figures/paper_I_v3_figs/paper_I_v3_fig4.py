import re
from pyOER.tof import all_tofs, TurnOverFrequency
from matplotlib import pyplot as plt

from pyOER.constants import (
    STANDARD_SPECIFIC_CAPACITANCE,
    STANDARD_SITE_DENSITY,
    FARADAYS_CONSTANT,
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

fig1, ax1 = plt.subplots()
fig2, ax2b = plt.subplots()
ax2 = ax2b.twinx()

for tof in all_tofs():
    sample_name = tof.measurement.sample_name
    if (
        tof.tof_type == "activity"
        and tof.id > 239
        and (
            "Reshma" in sample_name
            or "Rao" in sample_name
            or "Evans" in sample_name
            or "Melih" in sample_name
        )
    ):
        if "Reshma" in sample_name:
            try:
                T_number = re.search(number_finder, tof.measurement.sample_name).group(
                    1
                )
            except AttributeError:
                color = "y"
            else:
                color = colors[T_number]
        elif "Evans" in sample_name:
            color = "g"
        elif "Melih" in sample_name:
            color = "m"
        elif "Rao" in sample_name:
            color = "orange"
        else:
            color = "y"

        rate = tof.rate
        potential = tof.potential
        f = tof.tof

        if (f > 7e-5 and potential < 1.32) or potential < 1.28:
            i = tof.id
            tof.experiment.plot_experiment()
            print(f"please fix or delete '{tof}' with tspan={tof.tspan}")
            plt.show()
            try:
                tof = TurnOverFrequency.open(i)
            except FileNotFoundError:
                continue
            rate = tof.calc_rate()  # needs to be updated.
            f = tof.calc_tof()
            potential = tof.calc_potential()
            tof.save()  # save updates.

        marker = markers.get(tof.measurement.isotope, "o")
        # marker = "o"

        ax1.plot(potential, rate * 1e9, color=color, marker=marker, fillstyle="none")
        ax2.plot(potential, f, color=color, marker=marker, fillstyle="none")

ax2b.set_xlabel("E vs RHE / (V)")
ax1.set_ylabel("rate / (nmol s$^{-1}$)")
ax1.set_yscale("log")

if False:  # axis to indicate geometric current density
    ax1b = ax1.twinx()
    ax1b.set_ylim([lim / 0.196 for lim in ax1.get_ylim()])
    ax1b.set_yscale("log")
    ax1b.set_ylabel("rate / (nmol s$^{-1}$cm$^{-2}_{geo}$)")

ax2.set_xlabel("E vs RHE / (V)")
ax2.set_yscale("log")

tof_lim = ax2.get_ylim()
norm_flux_lim = [
    lim * STANDARD_SITE_DENSITY / STANDARD_SPECIFIC_CAPACITANCE * 4 * FARADAYS_CONSTANT
    for lim in tof_lim
]
ax2b.set_ylim(norm_flux_lim)
ax2b.set_yscale("log")
ax2b.set_ylabel("OER current$_{cap}$ / (A F$^{-1}$)")

if True:  # a TOF axis
    ax2.set_ylabel("TOF / (s$^{-1}$)")
else:  # no TOF axis
    ax2.set_yticks([])
    ax2.yaxis.set_tick_params(which="both", right=False)
    ax2.set_ylabel("")

#  [1/s] * [mol/cm^2] / [F/cm^2] * [C/mol] = [A/F]


if forpublication:
    fig1.subplots_adjust(left=0.15, right=0.85)
    fig1.savefig("all_Ru_rates.png")
    fig1.savefig("all_Ru_rates.svg")
    fig2.subplots_adjust(left=0.15, right=0.85)
    fig2.savefig("all_Ru_tofs.png")
    fig2.savefig("all_Ru_tofs.svg")
