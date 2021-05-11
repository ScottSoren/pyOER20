"""Analyze sensitivity factors based on measurements categorized as calibration.

Turns out that these calibration.pkl files are not EC_MS mdicts like I thought they w
ere. They in fact seem to be almost exact copies of each other and rather useless :(
"""
# import time
import numpy as np
from matplotlib import pyplot as plt

from pyOER.measurement import all_measurements
from pyOER import Calibration, all_calibrations
from pyOER.calibration import CalibrationSeries, CALIBRATION_DIR

plt.interactive(False)

# equal to, at the time of writing this script, now minus 2 years plus 20 days:
# tPROJECT_START_TIMESTAMP = time.time() - 2 * 365 * 24 * 60 * 60 + 20 * 24 * 60 * 60


def generate_calibrations():
    """Generates mostly-empty calibration files based on measurement categorization"""
    for measurement in all_measurements():
        if "calibration" not in measurement.make_name():
            # ^ using make_name() because measurement.category can be str or list :(
            print(f"skipping {measurement.make_name()}")
            continue

        calibration = Calibration(
            m_id=measurement.id,
        )
        calibration.save()


def add_calibration(m_id):
    """Create a calibration json file referencing measurement with given id"""
    calibration = Calibration(
        m_id=m_id,
    )
    calibration.save()


def analyze_this_calibration(cal, criteria="uncategorized"):
    """Return whether to analyze the calibration based on the criteria"""
    if criteria == "uncategorized":  # only categorize uncategorized
        return not cal.category
    elif isinstance("criteria", str):
        return cal.category == criteria
    return True


category_names = {
    "g": "good",
    "b": "bad",
    "d": "duplicate",
}


def input_timestamps_and_categorize(cal):
    print(
        f"\n\n#################################################\n"
        f"add tspan and tspans in the json file in pyOER20 for:\n{cal.name}"
        f"\n#####################################################\n\n"
    )

    # sys.stdout = open(os.devnull, "w")
    ax = cal.measurement.plot_experiment(verbose=False)
    # sys.stdout = sys.__stdout__

    ax[1].set_title(cal.name)
    print("close the plot when ready to re-load the calibration")
    plt.show()  # script hangs here until plot is closed.

    # re-open the calibration to catch what they filled in in the file
    c_id = cal.id
    cal = Calibration.open(c_id)
    if cal.cal_tspans:
        cal.calibration_curve(ax="new", t_int=60)
    elif cal.tspan:
        cal.cal_F_O2()
    if cal.tspan:
        cal.cal_alpha()

    plt.show()
    print(f"Close the plot when ready to categorize. \nShortcuts = {category_names}")
    category = input("Enter category or just enter to skip")
    category = category_names[category] if category in category_names else category
    if not category:
        category = None
    cal.category = category
    cal.save_with_rename()


def reanalyze_without_input(cal):
    print(f"reanalyzing:\n\t{cal.name}")
    if cal.cal_tspans:
        cal.calibration_curve(ax="new", t_int=60)
    elif cal.tspan:
        cal.cal_F_O2()
    if cal.tspan:
        cal.cal_alpha()
    cal.save_with_rename()


if __name__ == "__main__":
    # generate_calibrations()  # only run this the calibration dir has been emptied.
    # add_calibration(m_id=175)

    for calibration in all_calibrations():
        if analyze_this_calibration(calibration):
            input_timestamps_and_categorize(calibration)

    cal_series = CalibrationSeries()
    cal_series.fit_exponential(ax="new")
    plt.savefig(CALIBRATION_DIR / "calibrations over time.png")
    plt.show()
    F_today = cal_series.F_of_tstamp(1596666000)
    print(f"predicted sensitivity factor for Aug 6 2020 = {F_today} C/mol")
    cal_series.save()
