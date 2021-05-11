import time
from matplotlib import pyplot as plt

from pyOER import all_measurements
from pyOER.experiment import ActExperiment, all_experiments
from pyOER.tof import TurnOverFrequency
from pyOER.constants import EXPERIMENT_TAGS

plt.interactive(False)

defined_experiments = [
    exp for exp in all_experiments() if exp.experiment_type.startswith("a")
]

if False:  # get the experiments
    activity_measurements = [m for m in all_measurements() if "activity" in m.category]

    for m in activity_measurements:
        if m.id in [exp.m_id for exp in defined_experiments]:
            exp = next(exp for exp in defined_experiments if exp.m_id == m.id)
            input(
                f"{m} is already an experiment {exp}. "
                f"Delete that manually and run again if you want to redo it."
            )
        m.print_notes()
        m.plot_experiment()
        print(f"\n\nclose plot when you can tell if {m} is a good expeirment")
        plt.show()
        yn = input(f"enter 'n' if {m} is not a good experiment")
        if yn == "n":
            continue
        m.plot_experiment()
        print("close the plot when ready to enter tspan_bg")
        plt.show()
        tspan_bg_str = input("enter tspan_bg as two numbers separated by a comma.")
        tspan_bg = (
            [float(t_str) for t_str in tspan_bg_str.split(",")]
            if tspan_bg_str
            else None
        )
        m.plot_experiment()
        print("close the plot when ready to enter tspan_F")
        plt.show()
        tspan_F_str = input("enter tspan_F as two numbers separated by a comma.")
        tspan_F = (
            [float(t_str) for t_str in tspan_F_str.split(",")] if tspan_F_str else None
        )
        m.plot_experiment()
        print("close the plot when ready to enter tspan_cap")
        plt.show()
        tspan_cap_str = input("enter tspan_cap as two numbers separated by a comma.")
        tspan_cap = (
            [float(t_str) for t_str in tspan_cap_str.split(",")]
            if tspan_F_str
            else None
        )
        exp = ActExperiment(
            m_id=m.id,
            experiment_type="activity",
            tspan_plot=None,
            # F=None,
            # alpha=None,
            # cap=None,
            tspan_bg=tspan_bg,
            tspan_F=tspan_F,
            tspan_alpha=tspan_F,
            tspan_cap=tspan_cap,
            V_DL=None,
        )
        exp.save()
        defined_experiments.append(exp)
else:  # just use the loaded experiments
    pass


if False:  # save the tspan_cap's!!! And sub-category and tspan_plot, forgotten above.
    for exp in defined_experiments:
        exp.measurement.print_notes()
        exp.plot_experiment(tspan="all")
        print(
            f"close the plot of '{exp}' (notes above) when ready to enter tspan_cap.\n"
            f"defaults to: {exp.tspan_cap}"
        )
        plt.show()
        answer = input("enter tspan_cap as two numbers separated by a comma.")
        if answer:
            tspan_cap = [float(t) for t in answer.split(",")] if answer else None
            exp.tspan_cap = tspan_cap
        exp.plot_experiment(tspan="all")
        print(
            f"close the plot of '{exp}' when ready to enter tspan_plot.\n"
            f"Defaults to: {exp.tspan_plot}"
        )
        plt.show()
        answer = input(
            "enter tspan plot as two numbers separated by a comma "
            "(defaults to what you see)"
        )
        if answer:
            tspan_plot = [float(t) for t in answer.split(",")]
            exp.tspan_plot = tspan_plot
        exp.plot_experiment()
        print(EXPERIMENT_TAGS)
        print("Close plot when ready to enter experiment category (see above).")
        plt.show()
        answer = input(
            f"Enter the experiment_type of '{exp}'.\n"
            f"Defaults to: {exp.experiment_type}\n"
            f"Should start with 'a'!!! Additional tag components above."
        )
        if answer and answer.startswith("a"):
            exp.experiment_type = answer
        exp.save()


if True:  # get the TOFs
    for exp in defined_experiments:
        if exp.id < 72:
            continue
        exp.measurement.print_notes()
        answer = 1
        if True:  # a chance to edit the plot.
            exp.plot_experiment(tspan="all")
            for item in [
                "experiment_type",
                "tspan_bg",
                "tspan_F",
                "tspan_cap",
                "tspan_plot",
            ]:
                print(f"exp.{item} = {getattr(exp, item)}")
            print(
                f"Check if above is right for '{exp}', edit the .json"
                " file if not, and close the plot."
            )
            plt.show()
            time.sleep(0.5)
            exp = ActExperiment.open(exp.id)  # update the experiment.
        while answer:
            exp.load_tofs()
            exp.plot_experiment()
            print(
                f"close the plot of '{exp}' when ready to enter one or more TOF tspan "
                f"(or blank to go on)."
            )
            plt.show()
            answer = input(
                "Enter one or more tspan for a TOF or blank to go to next measurement"
            )
            if answer:
                if "[" in answer:  # then we assume the user put it in right.
                    tof_tspans = eval(answer)
                else:
                    tof_tspans = [
                        [float(t) for t in answer.split(",")],
                    ]
                for tspan_tof in tof_tspans:
                    tof = TurnOverFrequency(
                        tof_type="activity",
                        e_id=exp.id,
                        tspan=tspan_tof,
                    )
                    tof.calc_rate()
                    tof.calc_tof()
                    tof.calc_potential()
                    print(
                        f"Got tof for {exp}"
                        f" with {tof.rate*1e9} [nmol/s] or {tof.tof} [1/s]"
                        f" at {tof.potential} V vs RHE"
                    )
                    time.sleep(0.5)
                    tof.save()
