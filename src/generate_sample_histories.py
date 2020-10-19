from pyOER import Sample, all_standard_experiments
from matplotlib import pyplot as plt

plt.interactive(False)


sample_name_set = set([se.measurement.sample_name for se in all_standard_experiments()])

for sample_name in sample_name_set:
    print(f"\n\n### ----- Working on {sample_name} ------- ###")
    try:
        sample = Sample.open(sample_name)
    except FileNotFoundError:
        sample = Sample(sample_name)
    for i, m in enumerate(sample.measurements):
        print(f"measurement {i}: {m}")
    print(f"\nKnown history: {sample.history}")
    q = input("press enter when ready to fill in sample history or q to skip")
    if q == "q":
        continue
    sample.generate_history()
    sample.save()
