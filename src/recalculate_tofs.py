from pyOER.tof import all_tofs

for tof in all_tofs():
    print(f"-------- Working on: '{tof}' ----------")
    tof.calc_rate()
    if tof.tof_type == "activity":
        tof.calc_tof()
    tof.save()
