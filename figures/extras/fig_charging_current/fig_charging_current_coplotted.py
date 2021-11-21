from matplotlib import pyplot as plt

from pyOER import Measurement, all_measurements
from EC_MS import Chem, colorax

plt.close("all")


all_data_specs = {
    m.name: {"m_id": m.id, "tspan": None, "tspan_ref": None}
    for m in all_measurements()
    if "activity" in m.category and "failed" not in m.category
}
A_el = 0.196

data_specs = {
    "Reshma4": {
        "m_id": 135,
        "t_start": 2320,
        "tspan_ref": [7400, 7430],
        "tspan_bg": [5000, 5100],
        "color": "k",
    },
    # "Reshma1A": {"m_id": 10, "tspan": [2430, 2600], "tspan_ref": [3500, 3550]},
    "Reshma1A": {
        "m_id": 10,
        "t_start": 2660,
        "tspan_ref": [3500, 3550],
        "tspan_bg": [2810, 2840],
        "color": "b",
    },
    "Evans10": {
        "m_id": 132,
        "t_start": 3865,
        "tspan_ref": [8500, 8550],
        "tspan_bg": [5600, 5700],
        "color": "r",
    },
}

ax = "new"


for name, spec in data_specs.items():

    m_id = spec["m_id"]
    t_start = spec["t_start"]
    tspan = [t_start - 30, t_start + 120 + 30]
    tspan_ref = spec["tspan_ref"]
    tspan_bg = spec["tspan_bg"]
    color = spec["color"]

    m = Measurement.open(m_id)
    if False:
        ax = m.plot()
        ax[1].set_title(name)

    dataset = m.meas
    dataset.sync_metadata(RE_vs_RHE=0.715, A_el=A_el, E_str="control/V")

    O2 = dataset.point_calibration(
        mol="O2", mass="M32", n_el=4, tspan=tspan_ref, tspan_bg=tspan_bg
    )

    dataset.set_background(t_bg=tspan_bg)

    subset = dataset.cut(tspan=tspan, t_zero=t_start)

    t_I, I = subset.get_current(unit="A")
    I = I * 1e6 / A_el  # A to uA/cm^2

    O2.color = color

    ax = subset.plot(
        mols=[[], [O2]],
        unit="pmol/s/cm^2",
        plotcurrent=False,
        logplot=False,
        V_color=color,
        ax=ax,
    )

    factor = 1e-12 * 4 * Chem.Far * 1e6
    ax[0].plot(t_I, I, color=color, linestyle="--")
    ax[-1].set_ylabel("(implied) O$_2$ / [pmol s$^{-1}$cm$^{-2}$]")
    ax[0].set_ylim([-10, 70])
    ax[-1].set_ylim([lim / factor for lim in ax[0].get_ylim()])


ax[0].set_ylabel("(partial) J / [$\mu$A cm$^{-2}$]")
colorax(ax[1], "k", lr="left")
ax[0].get_figure().savefig("coplotted charging currents.png")
ax[0].get_figure().savefig("coplotted charging currents.svg")
