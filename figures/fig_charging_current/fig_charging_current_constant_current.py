from matplotlib import pyplot as plt

from pyOER import all_standard_experiments
from EC_MS import Chem, colorax

plt.close("all")


se_rutile = next(se for se in all_standard_experiments() if se.sample_name == "Stoff4A")
se_amorphous = next(
    se for se in all_standard_experiments() if se.sample_name == "Taiwan1D"
)
se_foam = next(se for se in all_standard_experiments() if "Evans" in se.sample_name)

fig, axes = plt.subplots(2, 1)
axes = [axes[0], axes[1], axes[0].twinx()]

tspan_0 = [-100, 300]

for se, t_offset, color in (
    (se_rutile, 90, "k"),
    (se_amorphous, 340, "b"),
    (se_foam, 112, "c"),
):
    se.plot_EC_MS_ICPMS()

    tspan = [t + t_offset for t in tspan_0]
    x, y = se.calc_flux("O2_M32", tspan=tspan, unit="pmol/s")
    t_V, V = se.dataset.get_potential(tspan=tspan)
    t_J, J = se.dataset.get_current(tspan=tspan, unit="mA/cm^2")

    axes[0].plot(x - t_offset, y, color=color)
    axes[1].plot(t_V - t_offset, V, color=color)
    axes[2].plot(t_J - t_offset, J, color=color, linestyle="--")

axes[0].tick_params(axis="x", top=True, bottom=False, direction="in")
axes[0].set_ylabel("flux / [pmol/s]")
axes[2].set_ylabel("current / [mA/cm^2]")
axes[1].set_ylabel("U vs RHE / [V]")
axes[1].set_xlabel("time / [s]")
