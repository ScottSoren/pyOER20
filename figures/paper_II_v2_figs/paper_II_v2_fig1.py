from pyOER import Experiment
from matplotlib import pyplot as plt

forpublication = True
if forpublication:  # for the publication figure
    import matplotlib as mpl

    mpl.rcParams['figure.figsize'] = (3.25, 2.75)
    # plt.rc('text', usetex=True)  # crashingly slow
    plt.rc('font', family='sans-serif')
    plt.rc('font', size=6)
    plt.rc('lines', linewidth=0.5)
else:
    plt.style.use("default")

e1 = Experiment.open(33)

e1.measurement.dataset.sync_metadata(
    RE_vs_RHE=e1.measurement.RE_vs_RHE,
    A_el=0.196,
)

axes_a = e1.measurement.plot_experiment(
    tspan="all",
    masses=["M4", "M28", "M18", "M32", "M34", "M36", "M44", "M46", "M48"],
    unit="A",
)

axes_a[0].set_ylim([1e-13, 1e-7])

fig_a = axes_a[0].get_figure()
fig_a.savefig("Taiwan1C_raw.png")
fig_a.savefig("Taiwan1C_raw.svg")
