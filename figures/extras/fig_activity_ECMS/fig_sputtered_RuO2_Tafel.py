import re
from pyOER.tof import all_tofs
from matplotlib import pyplot as plt

colors = {  # from Reshma's Figure 1.
    "1": "#54bdebff",
    "2": "#308ab2ff",
    "3": "#2e7094ff",
    "4": "#163854ff",
    "5": "m",
}
colors_soren = {"1": "k", "2": "b", "3": "g", "4": "r"}
# colors = colors_soren
markers = {"16": "o", "18": "s"}
number_finder = "([0-4])"

fig1, ax1 = plt.subplots()
fig2, ax2 = plt.subplots()

for tof in all_tofs():
    if tof.tof_type == "activity" and "Reshma" in tof.measurement.sample_name:
        try:
            T_number = re.search(number_finder, tof.measurement.sample_name).group(1)
        except AttributeError:
            T_number = "5"
        rate = tof.rate
        f = tof.tof
        potential = tof.potential
        color = colors[T_number]
        marker = markers.get(tof.measurement.isotope, ".")

        ax1.plot(potential, rate, color=color, marker=marker)
        ax2.plot(potential, f, color=color, marker=marker)

ax1.set_xlabel("$U_{RHE}$ / [V]")
ax1.set_ylabel("rate / [nmol s$^{-1}$]")
ax1.set_yscale("log")

ax2.set_xlabel("$U_{RHE}$ / [V]")
ax2.set_ylabel("tof / [s$^{-1}$]")
ax2.set_yscale("log")

fig1.savefig("RuO2_rates.png")
fig1.savefig("RuO2_rates.svg")
fig2.savefig("RuO2_tofs.png")
fig2.savefig("RuO2_tofs.svg")
