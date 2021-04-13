from pyOER import StandardExperiment
import numpy as np
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


for e_id in [33, 5, 39, 41]:

    e = StandardExperiment.open(e_id)

    axes = e.plot_EC_MS_ICPMS()
    ylim_left = np.array([-0.2, 2])
    axes[0].set_ylim(ylim_left)
    axes[3].set_ylim(ylim_left / e.beta)

    fig = axes[0].get_figure()
    fig.savefig(f"{e}.png")
    fig.savefig(f"{e}.svg")
