from matplotlib import pyplot as plt

from pyOER import Measurement
from pyOER.calibration import CalibrationSeries
from EC_MS import Molecule, save_as_text


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

cal_series = CalibrationSeries.load()
cal_series.make_F_of_tstamp()

measurements_to_plot = {
    10: {
        "name": "RT RuO2, H2(16)O",
        "tspan": [1700, 5400],
        "R_Ohm": 500,
        "tspan_cal": [1800, 1850],
        "tspan_bg": [3240, 3260],
    },
    # 14: {"name": "400C RuO2, H2(16)O", "tspan": [],},
    32: {
        "name": "RT RuO2, H2(18)O",
        "tspan": [1100, 4800],
        "tspan_cal": [1750, 1800],
        "tspan_bg": [3550, 3600],
    },
    # 53: {"name": "400C RuO2, H2(18)O", "tspan": [],},
}

mess = {}

for m_id, specs in measurements_to_plot.items():
    name = specs["name"]
    tspan = specs["tspan"]
    m = Measurement.open(m_id)
    if tspan:
        m.cut_dataset(tspan=tspan, t_zero=tspan[0])

    if False:  # plot raw data
        ax = m.plot_experiment()
        ax[1].set_title(m.make_name())

    if "tspan_cal" in specs:
        F_cal = 0
        for mass in ["M32", "M34", "M36"]:
            F_cal += m.dataset.point_calibration(
                tspan=specs["tspan_cal"],
                t_bg=specs["tspan_bg"],
                mol="O2",
                mass=mass,
                n_el=4,
            ).F_cal
    else:
        F_cal = cal_series.F_of_tstamp(m.dataset.tstamp)

    mols = {}
    for mass in ["M32", "M34", "M36"]:
        molecule = Molecule("O2", primary=mass)
        molecule.name = "O2_" + mass
        molecule.F_cal = F_cal
        mols[mass] = molecule

    V_str, J_str = m.dataset.calibrate_EC(
        RE_vs_RHE=float(m.elog.field_data["RE_vs_RHE"]),
        A_el=0.196,
    )
    if "R_Ohm" in specs:
        m.dataset.correct_ohmic_drop(specs["R_Ohm"])

    mess[name] = m

    ax = m.plot_experiment(mols=mols, unit="pmol/cm^2")
    # ax[1].set_title(name)
    ax[0].set_ylim([5e-1, 3e3])
    ax[0].set_ylabel("O$_2$ / [pmol s$^{-1}$cm$^{-2}]$")
    ax[1].set_ylabel("U vs RHE / [V]")
    if False:  # figure saving
        ax[0].get_figure().savefig(f"fig_act_ECMS {name}.png")
        ax[0].get_figure().savefig(f"fig_act_ECMS {name}.svg")
    if False:  # text export
        save_as_text(
            f"fig_act_ECMS {name}.csv",
            dataset=m.dataset.data,
            mols=list(mols.values()),
            cols=[V_str, J_str],
        )

if True:  # inset to part b
    tspan_inset = [3140, 3320]
    m = mess["RT RuO2, H2(18)O"]
    ax = m.dataset.plot_flux(
        mols["M36"], tspan=tspan_inset, unit="pmol/s/cm^2", logplot=False
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([])
    inset = ax.get_figure()
    inset.set_figwidth(inset.get_figwidth() / 5)
    inset.set_figheight(inset.get_figheight() / 5)
    inset.savefig("inset to H2(18)O.svg")
    inset.savefig("inset to H2(18)O.png")
