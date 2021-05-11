from pyOER import Measurement, all_measurements
from EC_MS import Chem, colorax


all_data_specs = {
    m.name: {"m_id": m.id, "tspan": None, "tspan_ref": None}
    for m in all_measurements()
    if "activity" in m.category and "failed" not in m.category
}
A_el = 0.196

data_specs = {
    "Reshma4": {
        "m_id": 135,
        "tspan": [2300, 2500],
        "tspan_ref": [7400, 7430],
        "tspan_bg": [5000, 5100],
    },
    # "Reshma1A": {"m_id": 10, "tspan": [2430, 2600], "tspan_ref": [3500, 3550]},
    "Reshma1A": {
        "m_id": 10,
        "tspan": [2600, 2800],
        "tspan_ref": [3500, 3550],
        "tspan_bg": [2810, 2840],
    },
    "Evans10": {
        "m_id": 132,
        "tspan": [3800, 4100],
        "tspan_ref": [8500, 8550],
        "tspan_bg": [5600, 5700],
    },
}

for name, spec in data_specs.items():
    m_id = spec["m_id"]
    tspan = spec["tspan"]
    tspan_ref = spec["tspan_ref"]
    tspan_bg = spec["tspan_bg"]

    m = Measurement.open(m_id)
    dataset = m.dataset
    dataset.sync_metadata(RE_vs_RHE=0.715, A_el=A_el)

    O2 = dataset.point_calibration(
        mol="O2", mass="M32", n_el=4, tspan=tspan_ref, tspan_bg=tspan_bg
    )

    dataset.set_background(t_bg=tspan_bg)

    subset = dataset.cut(tspan=tspan, t_zero="start")

    t_I, I = subset.get_current(unit="A")
    I = I * 1e6 / A_el  # A to uA/cm^2

    ax = subset.plot_experiment(
        mols=[[], [O2]],
        unit="pmol/s/cm^2",
        plotcurrent=False,
        logplot=False,
    )

    factor = 1e-12 * 4 * Chem.Far * 1e6

    ax[0].plot(t_I, I, color="r")
    ax[0].set_ylabel("(partial) J / [$\mu$A cm$^{-2}$]")
    ax[-1].set_ylabel("(implied) O$_2$ / [pmol s$^{-1}$cm$^{-2}$]")
    colorax(ax[0], "r")
    ax[0].set_ylim([-5, 50])
    ax[-1].set_ylim([lim / factor for lim in ax[0].get_ylim()])

    ax[0].get_figure().savefig(name + ".png")

    if True:
        ax = m.plot_experiment()
        ax[1].set_title(name)
