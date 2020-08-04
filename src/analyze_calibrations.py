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


category_names = {
    "g": "good",
    "b": "bad",
}

if __name__ == "__main__":
    # generate_calibrations()  # only run this the calibration dir has been emptied.

    for calibration in all_calibrations():
        if not analyze_this_calibration(calibration):
            continue

        # sys.stdout = open(os.devnull, "w")
        calibration.extraction.plot_experiment(verbose=False)
        # sys.stdout = sys.__stdout__
        plt.show()  # script hangs here until plot is closed.

        print("add tspan and tspans in the json file in pyOER20/20")

        c_id = calibration.id
        calibration = Calibration.open(c_id)
        if calibration.tspans:
            calibration.calibration_curve()
            plt.show()
        elif calibration.tspan:
            calibration.cal_F_O2()
        if calibration.tspan:
            calibration.cal_alpha()

        print(
            f"Close the plot when ready to categorize. \nShortcuts = {category_names}"
        )
        category = input("Enter category or just enter to skip")
        category = category_names[category] if category in category_names else category
        calibration.category = category
        calibration.save_with_rename()
