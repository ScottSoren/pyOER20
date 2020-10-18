from pathlib import Path
import json

from pyOER.standard_experiment import all_standard_experiments

working_range = [0, 100]

for se in all_standard_experiments():
    if se.id < working_range[0]:
        continue
    elif se.id > working_range[-1]:
        break

    ax = se.plot_EC_MS_ICPMS()
    ax[1].set_title(str(se.measurement))

    fig = ax[0].get_figure()
    fig.savefig(f"plot of {se}.png")
    fig.savefig(f"plot of {se}.svg")
