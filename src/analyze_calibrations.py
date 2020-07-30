"""Imports all the "calibration.pkl" files in the data directories.

Turns out that these calibration.pkl files are not EC_MS mdicts like I thought they w
ere. They in fact seem to be almost exact copies of each other and rather useless :(
"""


from pathlib import Path
import re
import pickle
from EC_MS import load_calibration_results

MEASUREMENT_DIR = Path("../measurements").absolute().resolve()
DATE_MATCH = "[0-9]{2}[A-L][0-9]{2}"

with open(MEASUREMENT_DIR / "non_ECMS_dataset_pickles.txt") as f:
    non_ECMS_pkls = [line.strip() for line in f.readlines()]

calibration_list = []

calibration_files = [file for file in non_ECMS_pkls if "calibration" in file]

for file in calibration_files:
    date_match = re.search(DATE_MATCH, str(file))
    date = date_match.group() if date_match else None
    try:
        mdict = load_calibration_results(file)
    except (AttributeError, FileNotFoundError) as e:
        print(f"could not load_calibration_results from {file} due to error =\n\t{e}")
        with open(file, "rb") as f:
            misc_cal_data = pickle.load(f)
        calibration_list += [{"date": date, "misc_cal_data": misc_cal_data}]

    else:
        calibration_list += [{"date": date, "mdict": mdict}]
