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
    exp_Reshma4_16O=Experiment.open(49),  # or 49 or 50 or 73
    exp_Reshma1_18O=Experiment.open(54),
    exp_Reshma4_18O=Experiment.open(59),  # or 63 or 59 or 75, 76, 77
)
for name, exp in exp_dict.items():
    axes = exp.plot_experiment()
    if forpublication:
        axes[0].get_figure().savefig(f"{name}_act.png")
        axes[0].get_figure().savefig(f"{name}_act.svg")
    else:
        axes[1].set_title(name)

    axes = exp.plot_faradaic_efficiency()
    fig = axes[0].get_figure()
    fig.subplots_adjust(right=0.85)
    if forpublication:
        fig.savefig(f"{name}_FE.png")
        fig.savefig(f"{name}_FE.svg")
    else:
        axes[1].set_title(name)
