from matplotlib import pyplot as plt

from pyOER import all_measurements
from pyOER.experiment import ActExperiment, all_experiments
from pyOER.tof import TurnOverFrequency

plt.interactive(False)

defined_experiments = [
    exp for exp in all_experiments() if exp.experiment_type=="activity"
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
        tspan_bg = [float(t_str) for t_str in tspan_bg_str.split(",")] \
            if tspan_bg_str else None
        m.plot_experiment()
        print("close the plot when ready to enter tspan_F")
        plt.show()
        tspan_F_str = input("enter tspan_F as two numbers separated by a comma.")
        tspan_F = [float(t_str) for t_str in tspan_F_str.split(",")] if tspan_F_str else None
        m.plot_experiment()
        print("close the plot when ready to enter tspan_cap")
        plt.show()
        tspan_cap_str = input("enter tspan_cap as two numbers separated by a comma.")
        tspan_cap = [float(t_str) for t_str in tspan_cap_str.split(",")] \
            if tspan_F_str else None
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
else:  # just use the loaded experiments
    pass

if True:  # get the TOFs
    for exp in defined_experiments:
        exp.plot_experiment()
        print(f"close the plot of {exp} when ready to enter tspan_plot and category")
        plt.show()
        answer = input("enter tspan plot as two numbers separated by a comma "
                       "(defaults to what you see)")
        if answer:
            tspan_plot = [float(t) for t in answer.split(",")]
            exp.tspan_plot = tspan_plot
        answer = input(f"enter the experiment_type of {exp} (defaults to `activity`)")
        if answer:
            exp.experiment_type = answer
        exp.save()
        answer = 1
        while answer:
            exp.plot_experiment()
            print("close the plot when ready to enter a TOF tspan (or blank to go on).")
            plt.show()
            answer = input("Enter a tspan for a TOF or blank to go to next measurement")
            if answer:
                tspan_tof = [float(t) for t in answer.split(",")]
                tof = TurnOverFrequency(
                    tof_type="activity", e_id=exp.id, tspan=tspan_tof,
                )
                tof.calc_rate()
                tof.calc_tof()
                tof.calc_potential()
                tof.save()
