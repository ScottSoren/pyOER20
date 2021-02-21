from pathlib import Path
import json

from pyOER.experiment import all_activity_experiments

working_range = [0, 500]

for exp in all_activity_experiments():
    if exp.id < working_range[0]:
        continue
    elif exp.id > working_range[-1]:
        break

    ax = exp.plot_experiment()
    ax[1].set_title(str(exp.measurement))

    fig = ax[0].get_figure()
    fig.savefig(f"plot of {exp}.png")
    fig.savefig(f"plot of {exp}.svg")
