from matplotlib import pyplot as plt

from pyOER import Experiment


forpublication = True
if forpublication:  # for the publication figure
    import matplotlib as mpl

    mpl.rcParams["figure.figsize"] = (3.25, 2.75)
    # plt.rc('text', usetex=True)  # crashingly slow
    plt.rc("font", family="sans-serif")
    plt.rc("font", size=6)
    plt.rc("lines", linewidth=0.5)
else:
    plt.style.use("default")

exp_dict = dict(
    exp_Reshma1_16O=Experiment.open(47),
    # exp_Reshma4_16O=Experiment.open(49),  # or 49 or 50 or 73
    exp_Reshma1_18O=Experiment.open(55),  # or 54?
    # exp_Reshma4_18O=Experiment.open(59),  # or 63 or 59 or 75, 76, 77
)
exp_dict["exp_Reshma1_16O"].tspan_plot = [1700, 5400]
exp_dict["exp_Reshma1_18O"].tspan_plot = [1100, 4800]


for name, exp in exp_dict.items():

    if False:  # Faradaic efficiency plot (fig 3c)
        axes = exp.plot_faradaic_efficiency()
        fig = axes[0].get_figure()
        fig.subplots_adjust(right=0.85)
        if forpublication:
            fig.savefig(f"{name}_FE.png")
            fig.savefig(f"{name}_FE.svg")
        else:
            axes[1].set_title(name)

    if True:  # activity plot (fig 3a and 3b)
        exp.correct_current()
        exp.measurement.dataset.reset()
        exp.measurement.cut_dataset(tspan=exp.tspan_plot, t_zero="start")
        axes = exp.measurement.plot_experiment(
            mols=list(exp.mdict.values()), unit="pmol/s/cm^2", removebackground=False
        )
        axes[0].set_ylabel("O$_2$ / [pmol s$^{-1}$cm$^{-2}]$")
        axes[1].set_ylabel("U vs RHE / [V]")
        axes[0].set_yscale("log")
        axes[0].set_ylim([5e-1, 3e3])
        if forpublication:
            axes[0].get_figure().savefig(f"{name}_act.png")
            axes[0].get_figure().savefig(f"{name}_act.svg")
        else:
            axes[1].set_title(name)
