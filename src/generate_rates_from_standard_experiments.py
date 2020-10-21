from matplotlib import pyplot as plt
from pyOER import all_standard_experiments, TurnOverFrequency

plt.interactive(False)

tof_diss = None

response = "start!"
for se in all_standard_experiments():
    while not response == "q":
        ax = se.plot_EC_MS_ICPMS()
        ax[1].set_title(se.measurement)
        se.measurement.print_notes()
        print("close the plot when you're ready to enter tspan and electrolysis time")
        plt.show()
        response = input(
            "enter the tspan as two numbers separated by a comma, "
            "or 'c' to continue to next experiment or 'q' to quit"
        )
        if response == "c":
            break
        if response == "q":
            break
        tspan = [float(t_str) for t_str in response.split(",")]
        response = input(
            "enter the electrolysis time represented by the ICPMS sample "
            "as a number in sif applicable"
        )
        if response:
            rate_calc_kwargs = dict(t_electrolysis=float(response))
        else:
            rate_calc_kwargs = {}

        description = input("enter description")

        tof_act = TurnOverFrequency(
            e_id=se.id, tspan=tspan, tof_type="activity", description=description
        )
        print(f"activity = {tof_act.rate} [mol/s]")
        tof_exc = TurnOverFrequency(
            e_id=se.id, tspan=tspan, tof_type="exchange", description=description,
        )
        print(f"exchange = {tof_exc.rate} [mol/s]")

        has_icpms = bool(se.icpms_points)

        if has_icpms:
            tof_diss = TurnOverFrequency(
                e_id=se.id,
                tspan=tspan,
                tof_type="dissolution",
                description=description,
                rate_calc_kwargs=rate_calc_kwargs,
            )
            print(f"dissolution = {tof_diss.rate} [mol/s]")

        response = input(
            "enter 's' to skip, 'q' to quit, 'c' to save and continue to next "
            "experiment, or anything else to save and stay on this experiment"
        )
        if response == "s":
            continue
        if response == "q":
            break
        tof_act.save()
        tof_exc.save()
        if has_icpms:
            tof_diss.save()
        if response == "c":
            break

    if response == "q":
        break
