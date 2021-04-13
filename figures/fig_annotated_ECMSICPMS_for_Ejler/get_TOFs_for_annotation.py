from pyOER import Sample

lines = []

for sample_name in ["John4A", "John4C", "Decade1G", "Taiwan1C"]:
    lines += ["\n --- ",
              sample_name + " ---\n"]

    sample = Sample.open(sample_name)
    measurements = sample.measurements
    experiment = next(
        m.get_standard_experiment() for m in measurements
        if m.get_standard_experiment() is not None
    )
    tofs = experiment.get_tofs()
    for tof in tofs:
        lines += [f"{tof.tof_type} rate at {tof.description} = {tof.rate} [mol/s] \n",
                  f"\tor {tof.amount} [mol] over the {tof.t_interval} [s] interval\n",
                  f"\twith average potential = {tof.potential} [V] vs RHE.\n"]


with open("for_ejler.txt", "w") as f:
    f.writelines(lines)