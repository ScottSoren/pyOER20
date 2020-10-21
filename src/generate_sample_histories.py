from pyOER import Sample, all_standard_experiments
from matplotlib import pyplot as plt

plt.interactive(False)


sample_name_set = set([se.measurement.sample_name for se in all_standard_experiments()])


def generate_history(sample):
    measurements = sample.measurements
    N = len(measurements)
    for (i, m) in enumerate(measurements):
        se = m.get_standard_experiment()
        if se:
            ax = se.plot_EC_MS_ICPMS()
        else:
            ax = m.plot_experiment()
        ax[1].set_title(m)

        m_str = "m" + str(m.id)
        m.print_notes()
        print(f"\n\nNotes of Measurement {i} of {N}, {m}, are above.")
        if m_str in sample.history:
            print(f"\tCurrent history to overwrite: '{sample.history[m_str]}'")
        print(
            f"Close the plot when ready to describe {sample.name} "
            f"at the START of measurement {i} of {N}!"
        )

        plt.show()

        description = input(
            f"Please describe {sample.name} at the START of this measurement! "
            f"'q'=quit"
        )
        if description == "q":
            break
        elif description:
            sample.history[m_str] = description


for sample_name in sample_name_set:
    print(f"\n\n### ----- Working on {sample_name} ------- ###")
    try:
        sample = Sample.open(sample_name)
    except FileNotFoundError:
        sample = Sample(sample_name)
    for i, m in enumerate(sample.measurements):
        print(f"measurement {i}: {m}")
    print(f"\nKnown history: synthesis on {sample.synthesis_date}\n{sample.history}")
    date = input(
        "Enter the first synthesis if date is known, nothing if not, or 'q' to skip"
    )
    if date == "q":
        continue
    elif date:
        sample.synthesis_date = date
    generate_history(sample)
    sample.save()
