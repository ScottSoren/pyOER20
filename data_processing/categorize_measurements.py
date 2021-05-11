import sys
import os
from matplotlib import pyplot as plt
from pyOER.measurement import all_measurements

plt.interactive(False)


category_names = {
    "a": "activity",
    "c": "calibration",
    "x": "exchange",
    "f": "failed",
    "h": "RHE",
    "b": "broken",
    "l": "labeling",
    "s": "stability"
    # "CO": "CO",  # just type full category
    # "O2": "O2",  # just type full category
}

criteria = "uncategorized"


def categorize_this_measurement(meas, criteria=criteria):
    """Return whether to categorize the measurement based on the criteria"""
    if criteria == "uncategorized":  # only categorize uncategorized
        return not meas.category
    elif criteria == "custom":
        return meas.category not in category_names.values()
    elif isinstance(criteria, dict):
        for key, value in criteria.items():
            if hasattr(meas, key) and getattr(meas, key) == value:
                return True
        return False
    return True


def main():
    for measurement in all_measurements():
        plt.close("all")

        if not categorize_this_measurement(measurement):
            continue

        print(
            "\n\n\n----------------------------- notes begin "
            "---------------------------- "
        )
        measurement.print_notes()
        print("------------------------------ notes end -----------------------------")
        print(f"file = {measurement.old_data_path}\n")
        if measurement.category:
            message_about_default = (
                f"Just press enter to keep current category = {measurement.category}"
            )
        else:
            message_about_default = "Just press enter to leave uncategorized "

        print(
            f"Please describe {measurement.make_name()}. Notes are above. \nUse these "
            f"shortcuts or enter a custom name: \n{category_names}. \nIf multiple, "
            f"separate with comma(s). \n"
            + message_about_default
            + "\nclose plot when ready to categorize."
        )
        try:
            # sys.stdout = open(os.devnull, "w")
            measurement.plot_experiment(verbose=False)
            # sys.stdout = sys.__stdout__
            plt.show()  # script hangs here until plot is closed.
        except (KeyError, SystemExit) as e:
            print(
                f"{measurement.name} broken. plot_experiment failed with error = {e}."
            )
            cat = "b"
        else:
            cat = input(" INPUT ---> enter catagory according to above instructions: ")

        if "," in cat:
            category = []
            for c in cat.split(","):
                c = c.strip()
                category += [category_names[c] if c in category_names else c]
        else:
            category = category_names[cat] if cat in category_names else cat

        if category:
            measurement.category = category
        measurement.make_name()
        measurement.save_with_rename()


if __name__ == "__main__":
    main()
