"""Analyze sensitivity factors based on measurements categorized as calibration.

Turns out that these calibration.pkl files are not EC_MS mdicts like I thought they w
ere. They in fact seem to be almost exact copies of each other and rather useless :(
"""

from matplotlib import pyplot as plt

from pyOER.measurement import all_measurements
from pyOER import Calibration, all_calibrations

plt.interactive(False)


def generate_calibrations():
    """Generates mostly-empty calibration files based on measurement categorization"""
    for measurement in all_measurements():
        if "calibration" not in measurement.make_name():
            # ^ using make_name() because measurement.category can be str or list :(
            print(f"skipping {measurement.make_name()}")
            continue

        calibration = Calibration(m_id=measurement.id,)
        calibration.save()


def analyze_this_calibration(cal, criteria="uncategorized"):
    """Return whether to analyze the calibration based on the criteria"""
    if criteria == "uncategorized":  # only categorize uncategorized
        return not cal.category
    return True


category_names = {
    "g": "good",
    "b": "bad",
    "d": "duplicate",
}


def input_timestamps_and_categorize(calibration):
    print(
        f"\n\n#################################################\n"
        f"add tspan and tspans in the json file in pyOER20 for:\n{calibration.name}"
        f"\n#####################################################\n\n"
    )

    # sys.stdout = open(os.devnull, "w")
    ax = calibration.measurement.plot_experiment(verbose=False)
    # sys.stdout = sys.__stdout__

    ax[1].set_title(calibration.name)
    print("close the plot when ready to re-load the calibration")
    plt.show()  # script hangs here until plot is closed.

    # re-open the calibration to catch what they filled in in the file
    c_id = calibration.id
    calibration = Calibration.open(c_id)
    if calibration.cal_tspans:
        calibration.calibration_curve(ax="new", t_int=60)
    elif calibration.tspan:
        calibration.cal_F_O2()
    if calibration.tspan:
        calibration.cal_alpha()

    plt.show()
    print(f"Close the plot when ready to categorize. \nShortcuts = {category_names}")
    category = input("Enter category or just enter to skip")
    category = category_names[category] if category in category_names else category
    if not category:
        category = None
    calibration.category = category
    calibration.save_with_rename()


def reanalyze_without_input(calibration):
    print(f"reanalyzing:\n\t{calibration.name}")
    if calibration.cal_tspans:
        calibration.calibration_curve(ax="new", t_int=60)
    elif calibration.tspan:
        calibration.cal_F_O2()
    if calibration.tspan:
        calibration.cal_alpha()
    calibration.save_with_rename()


if __name__ == "__main__":
    # generate_calibrations()  # only run this the calibration dir has been emptied.

    for calibration in all_calibrations():
        if not analyze_this_calibration(calibration,):  # criteria=None
            print(f"skipping: '{calibration.make_name()}'")
            continue
        input_timestamps_and_categorize(calibration)
        # reanalyze_without_input(calibration)
