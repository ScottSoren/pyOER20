import pyOER.calc

if True:  # ALL of them!!!
    from pyOER.tof import all_tofs

    for tof in all_tofs():
        print(f"-------- Working on: '{tof}' ----------")
        tof.calc_rate()
        if tof.tof_type == "activity":
            tof.calc_tof()
            tof.calc_faradaic_efficiency()
        tof.save()
        del tof

else:  # something specific:
    from pyOER import ActExperiment

    exp = ActExperiment.open(54)
    for tof in exp.open(54).tofs:
        tof.calc_rate()
        tof.calc_tof()
        tof.calc_current()
        tof.save()
