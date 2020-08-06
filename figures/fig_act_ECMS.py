from pyOER import Measurement
from pyOER.calibration import CalibrationSeries
from EC_MS import Molecule, save_as_text

cal_series = CalibrationSeries.load()
cal_series.make_F_of_tstamp()

measurements_to_plot = {
    10: {"name": "RT RuO2, H2(16)O", "tspan": [],},
    14: {"name": "400C RuO2, H2(16)O", "tspan": [],},
    32: {"name": "RT RuO2, H2(18)O", "tspan": [],},
    53: {"name": "400C RuO2, H2(18)O", "tspan": [],},
}

for m_id, specs in measurements_to_plot.items():
    name = specs["name"]
    m = Measurement.open(m_id)

    if False:  # plot raw data
        ax = m.plot_experiment()
        ax[1].set_title(m.make_name())

    F_cal = cal_series.F_of_tstamp(m.dataset.tstamp)

    mols = {}
    for mass in ["M32", "M34", "M36"]:
        molecule = Molecule("O2", primary=mass)
        molecule.name = "O2_" + mass
        molecule.F_cal = F_cal
        mols[mass] = molecule

    V_str, J_str = m.dataset.calibrate_EC(
        RE_vs_RHE=float(m.elog.field_data["RE_vs_RHE"]), A_el=0.196,
    )

    ax = m.plot_experiment(mols=mols)
    ax[1].set_title(name)
    ax[0].get_figure().savefig(f"fig_act_ECMS {name}.png")
    ax[0].get_figure().savefig(f"fig_act_ECMS {name}.svg")

    save_as_text(
        f"fig_act_ECMS {name}.csv",
        dataset=m.dataset.data,
        mols=list(mols.values()),
        cols=[V_str, J_str],
    )
