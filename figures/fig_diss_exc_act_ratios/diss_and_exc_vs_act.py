from matplotlib import pyplot as plt
from pyOER import all_tofs

plt.close("all")

timing_specs = {
    "first": {"markerfacecolor": "w"},
    "next": {"markerfacecolor": "0.5"},
    "steady": {"markerfacecolor": "0.25"},
    "full": {"markerfacecolor": "k"},
}
element_specs = {
    "Ir": {"color": "turquoise"},
    "Ru": {"color": "purple"},
    "Pt": {"color": "0.5"},
}
type_specs = {
    "dissolution": {"marker": "^"},
    "exchange": {"marker": "s"},
}

fig, ax = plt.subplots()

for tof in all_tofs():
    if tof.tof_type == "activity":
        continue
    tof_act = next(
        tof_
        for tof_ in all_tofs()
        if tof_.tof_type == "activity"
        and tof_.date == tof.date
        and tof_.sample_name == tof.sample_name
        and tof_.description == tof.description
    )
    specs = {}
    specs.update(type_specs[tof.tof_type])
    specs.update(element_specs[tof.element])
    try:
        timing_key = next(key for key in timing_specs.keys() if key in tof.description)
    except StopIteration as e:
        print(e)
        print("not showing timing in plot for {tof}")
    else:
        specs.update(timing_specs[timing_key])

    diss_or_exc = tof.rate
    act = tof_act.rate

    ax.plot(act, diss_or_exc, **specs)
