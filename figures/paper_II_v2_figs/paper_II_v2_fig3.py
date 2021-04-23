from pyOER import StandardExperiment
import numpy as np
from matplotlib import pyplot as plt

forpublication = False
if forpublication:  # for the publication figure
    import matplotlib as mpl

    mpl.rcParams["figure.figsize"] = (3.25, 2.75)
    # plt.rc('text', usetex=True)  # crashingly slow
    plt.rc("font", family="sans-serif")
    plt.rc("font", size=6)
    plt.rc("lines", linewidth=0.5)
else:
    plt.style.use("default")

lines = []

for e_id in [33, 5, 39, 41]:

    e = StandardExperiment.open(e_id)

    axes = e.plot_EC_MS_ICPMS()
    ylim_left = np.array([-1, 10])
    axes[0].set_ylim(ylim_left)
    axes[3].set_ylim(ylim_left / e.beta)

    if e_id in [33, 5]:
        axes[-1].set_ylim([0, 25])
    if e_id in [39, 41]:
        axes[-1].set_ylim([0, 2.5])

    fig = axes[0].get_figure()
    if forpublication:
        fig.set_figwidth(3.25)
        fig.set_figheight(2.75)
        fig.savefig(f"{e}.png")
        fig.savefig(f"{e}.svg")

    lines += ["\n", f"----- {e}:\n"]
    tofs = e.get_tofs()

    for tof in tofs:
        lines += [
            f"{tof.tof_type} rate at {tof.description} = {tof.rate} [mol/s] \n",
            (
                f"\t= {tof.amount * 1e12 / 0.196} [pmol/cm^2] "
                + f"in the {tof.t_interval} [s] interval\n"
            ),
            f"\twith average potential = {tof.potential} [V] vs RHE.\n",
        ]


with open("for_annotation.txt", "w") as f:
    f.writelines(lines)
