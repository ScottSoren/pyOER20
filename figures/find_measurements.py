from pyOER import all_measurements

ms = [
    m
    for m in all_measurements()
    if m.sample_name and "Reshma1" in m.sample_name and "activity" in m.category
]

for m in ms:
    m.plot_experiment()
