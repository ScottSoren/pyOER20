from pathlib import Path
import json

from pyOER.experiment import all_activity_experiments

working_range = [0, 500]

for exp in all_activity_experiments():
    if exp.id < working_range[0]:
        continue
    elif exp.id > working_range[-1]:
        break

    if "o" in exp.experiment_type:
        ax = exp.measurement.plot(
            tspan="all",
            mols=[[exp.mdict["O2_M34"], exp.mdict["O2_M36"]], [exp.mdict["O2_M32"]]],
            logplot=False,
        )
        ax[1].set_title(str(exp.measurement))
        fig = ax[0].get_figure()
        fig.savefig(f"full plot of {exp}.png")
        fig.savefig(f"full plot of {exp}.svg")

    elif "l" in exp.experiment_type:
        exp.meas.reset()
        ax = exp.plot(tspan="all")
        ax[1].set_title(str(exp.measurement))
        fig = ax[0].get_figure()
        fig.savefig(f"full plot of {exp}.png")
        fig.savefig(f"full plot of {exp}.svg")

    else:
        ax = exp.plot()
        ax[1].set_title(str(exp.measurement))

        fig = ax[0].get_figure()
        fig.savefig(f"plot of {exp}.png")
        fig.savefig(f"plot of {exp}.svg")
