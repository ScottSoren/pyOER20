import re
from pyOER.tof import all_tofs
from matplotlib import pyplot as plt

from pyOER.constants import STANDARD_SPECIFIC_CAPACITANCE, STANDARD_SITE_DENSITY

forpublication = True

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


markers = {"16": "o", "18": "s"}

fig1, ax1 = plt.subplots()
fig2, ax2b = plt.subplots()
ax2 = ax2b.twinx()

for tof in all_tofs():
    sample_name = tof.measurement.sample_name
    if tof.tof_type == "activity" and (
        "Emil" in sample_name
        or "Folk" in sample_name
        or "Ir" in sample_name
        # or "Jazz" in sample_name
    ):
        if "Jazz" in sample_name:
            color = "r"
        elif "Emil" in sample_name or "Folk" in sample_name:
            color = "b"
        elif "Ir" in sample_name or "Yang" in sample_name:
            color = "g"
        else:
            color = "y"

        rate = tof.rate
        f = tof.tof
        potential = tof.potential
        marker = markers.get(tof.measurement.isotope, ".")

        ax1.plot(potential, rate * 1e9, color=color, marker=marker)
        ax2.plot(potential, f, color=color, marker=marker)

ax1.set_xlabel("$U_{RHE}$ / [V]")
ax1.set_ylabel("rate / [nmol s$^{-1}$]")
ax1.set_yscale("log")

if False:  # axis to indicate geometric current density
    ax1b = ax1.twinx()
    ax1b.set_ylim([lim / 0.196 for lim in ax1.get_ylim()])
    ax1b.set_yscale("log")
    ax1b.set_ylabel("rate$_{geo}$ / [nmol s$^{-1}$cm$^{-1}$]")

ax2b.set_xlabel("$U_{RHE}$ / [V]")
ax2.set_ylabel("tof / [s$^{-1}$]")
ax2.set_yscale("log")
tof_lim = ax2.get_ylim()
norm_flux_lim = [
    lim * STANDARD_SITE_DENSITY / STANDARD_SPECIFIC_CAPACITANCE for lim in tof_lim
]

ax2b.set_ylim(norm_flux_lim)
ax2b.set_yscale("log")
ax2b.set_ylabel("norm. rate / [mol s$^{-1}$F$^{-1}$]")

if forpublication:
    fig1.subplots_adjust(left=0.15, right=0.85)
    fig1.savefig("all_Ir_rates.png")
    fig1.savefig("all_Ir_rates.svg")
    fig2.subplots_adjust(left=0.15, right=0.85)
    fig2.savefig("all_Ir_tofs.png")
    fig2.savefig("all_Ir_tofs.svg")
