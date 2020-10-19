"""This module adds to pyOER20 all of the ICPMS data Soren previously analyzed

It makes ICPMSPoints and ICPMSCals for all of the data in the ICPMS processing scripts
in the Aanalysis folder.

The data and some of the metadata are taken form the data
"""

import pickle
import re
import numpy as np
from matplotlib import pyplot as plt

plt.interactive(False)

from pyOER.tools import FLOAT_MATCH
from pyOER import Measurement, all_measurements, ICPMSPoint, ICPMSCalibration
from pyOER.settings import DATA_DIR

analysis_dir = DATA_DIR / "Analysis"

# CONTINUE_FROM = {}

CONTINUE_FROM = {
    "19C02": {"i": 9, "ic_ids": {"M102": 2},},
    "19F07": {"i": 16, "ic_ids": {"M102": 5, "M195": 6},},
    "19F09": {"i": 32, "ic_ids": {"M193": 7},},
    "20A05": {"i": 37, "ic_ids": {"M102": 9}},
    "20A06": {"i": 40, "ic_ids": {"M102": 9}},
    "20A15": {"i": 25, "ic_ids": {"M102": 11, "M193": 12}},
}

initial_volume = 2e-9  # 2 ul in m^3
dilution = 1000 / 2 * 10 / 0.1
# 2 ul dilutes to 1 ml, 100 ul of which is diluted to 10 ml.

element_samples = {
    "Ru": (
        "Reshma",
        "Nancy",
        "Evans",
        "Maundy",
        "Easter",
        "Bernie",
        "Melih",
        "Taiwan",
        "Stoff",
        "John",
        "Sofie",
        "Mette",
    ),
    "Ir": ("Jazz", "Folk", "Emil", "Ben", "Goof", "Champ", "Decade", "Legend",),
    "Pt": ("Trimi",),
}

default_M = {
    "Ru": 102,
    "Ir": 193,
    "Pt": 195,
}

SAVE = True


def get_element(sample):
    for e, ss in element_samples.items():
        for s in ss:
            if sample.startswith(s):
                return e


def get_m_id_with_input(result, match_date=True):
    date = result["date"]
    sample = result["sample"]
    print(f"\n\nLet's find the measurement number for ICMPS {sample}")
    if match_date:
        print(f"on {date}")
    print(f" ... so far, we have result={result}.\n")
    for measurement in all_measurements():
        if measurement.sample_name == sample and (
            measurement.date == date or not match_date
        ):
            measurement.plot_experiment()
            print("\n\n------ NOTES -------\n\n")
            measurement.print_notes()
            print(
                f"\nThe ICPMS measurement is {result}. "
                f"\nThis plot is {measurement}. "
                f"Corresponding notes are printed above."
            )
            print("\n\nClose the plot when you know if it's the right measurement.")
            plt.show()
            yn = input(f"Correct ({sample} {result['description']} on {date})? (y/n)")
            if yn == "y":
                result["m_id"] = measurement.id
                return measurement.id
    print("you failed to choose a measurement.")
    if match_date:
        yn = input("maybe the date was wrong. Try other dates? (y/n)")
        if yn == "y":
            return get_m_id_with_input(result, match_date=False)
    yn = input("Could the sample name be wrong? (y/n)")
    if yn == "y":
        corrected_sample = input("enter correct sample name")
        if corrected_sample:
            result["sample"] = corrected_sample
            return get_m_id_with_input(result)
    c = input("To continue without a measurement, enter 'c'")
    if c == "c":
        return c
    print("Well, then, fuck that.")
    return


def make_icpms_calibration(
    icpms_data, date, element, icpms_mass, plotit=True, save=False
):
    wash_signals = icpms_data["wash"][icpms_mass]
    calibration_keys = [key for key in icpms_data.keys() if "ug/l" in key]

    signals = np.array([])
    ppbs = np.array([])

    for key in calibration_keys:
        try:
            number = re.search(FLOAT_MATCH, key).group()
            ppb = float(number)
        except (AttributeError, ValueError):
            print("WARNING: could't match a float in '" + key + "'. skipping.")
            continue
        signals = np.append(signals, icpms_data[key][icpms_mass])
        ppbs = np.append(ppbs, ppb)

    ic_id = None if save else -1  # passing None to ICPMSCalibration iterates the id

    mass = "M" + icpms_mass[: len(icpms_mass) - len(element)]

    icpms_calibration = ICPMSCalibration(
        ic_id=ic_id,
        date=date,
        element=element,
        mass=mass,
        ppbs=ppbs,
        signals=signals,
        wash_signals=wash_signals,
    )
    if plotit:
        icpms_calibration.plot_calibration()
        print(f"calibration for {element} from {measurement_date}. Close when happy.")
        plt.show()
    if save:
        icpms_calibration.save()
    return icpms_calibration


for set, (data_pkl, samples_pkl) in {
    # fmt: off
    # "19A10": ("19F05_ICPMS/19A10_ICPMS_data.pkl", "19F05_ICPMS/19A10_ICPMS_results.pkl"),
    # "19C02": ("19F05_ICPMS/19C02_ICPMS_data.pkl", "19F05_ICPMS/19C02_ICPMS_results.pkl"),
    # "19F07": ("19F05_ICPMS/19F07_ICPMS_data_20I17.pkl", "19F05_ICPMS/19F07_ICPMS_results_20I17.pkl"),
    # "19F09": ("19F05_ICPMS/19F09_ICPMS_data.pkl", "19F05_ICPMS/19F09_ICPMS_results.pkl"),
    # "19K29": ("19J21_Stoff/19K29_ICPMS_data.pkl", "19J21_Stoff/19K29_ICPMS_results.pkl"),
    # "20A05": ("19L08_Taiwan/20A05_ICPMS_data_20I17.pkl", "19L08_Taiwan/20A05_ICPMS_results_20I17.pkl"),
    # "20A06": ( "19L08_Taiwan/20A06_ICPMS_data.pkl", "19L08_Taiwan/20A06_ICPMS_results.pkl"),
    "20A15": ("20A08_Decade_and_friends/20A15_ICPMS_data.pkl", "20A08_Decade_and_friends/20A15_ICPMS_results.pkl"),
    # fmt: on
}.items():

    print(f"\n\n########## WORKING ON {data_pkl} ########### \n\n")

    with open(analysis_dir / data_pkl, "rb") as f:
        data = pickle.load(f)
    with open(analysis_dir / samples_pkl, "rb") as f:
        samples = pickle.load(f)
    if set in CONTINUE_FROM:
        calibrations = {
            mass: ICPMSCalibration.open(ic_id)
            for mass, ic_id in CONTINUE_FROM[set]["ic_ids"].items()
        }
    else:
        calibrations = {}
    results = {}
    sample = None
    date = None
    measurement_date = data_pkl.split("/")[-1][0:5]
    m_id = None
    i = 0
    for number, data_point in data.items():
        i += 1
        try:
            n = int(number)
        except ValueError:
            print(f"skipping {number} because sample numbers should be integers")
            continue
        try:
            sample_dict = samples[n]
        except KeyError:
            print(f"skipping {data_point} because there's no corresponding sample.")
            continue
        if set in CONTINUE_FROM and i < CONTINUE_FROM[set]["i"]:
            print(f"skipping {sample_dict} because i<{CONTINUE_FROM[set]['i']}")
            continue
        print(f"\n\n###### sample # {i} of {data_pkl}, has number={n} ####### \n\n")
        print(sample_dict)
        q = input("Press enter to continue. Enter q to skip.")
        if q == "q":
            continue
        description = sample_dict["description"]
        if date == sample_dict["date"] and sample == sample_dict["electrode"]:
            print(f"This is {sample} on {date}, just like last one.")
            print(f"Assuming m_id={m_id} like the the last one.")
        else:
            date = sample_dict["date"]
            sample = sample_dict["electrode"]
            m_id = None
        element = get_element(sample)
        try:
            M = default_M[element]
        except KeyError:
            input(f"no default mass for {sample}. Skipping. Press Enter.")
            continue
        icpms_mass = str(M) + element
        mass = "M" + str(M)
        if not mass in calibrations:
            calibrations[mass] = make_icpms_calibration(
                data,
                date=measurement_date,
                element=element,
                icpms_mass=icpms_mass,
                plotit=True,
                save=SAVE,
            )
            f"calibration for {element} from {measurement_date}. Close when happy."
            plt.show()
        calibration = calibrations[mass]
        mass = "M" + str(M)

        result = dict(
            ic_id=calibration.id,
            date=date,
            sample=sample,
            element=element,
            mass=mass,
            signal=data_point[icpms_mass],
            dilution=dilution,
            initial_volume=initial_volume,
            description=description,
        )

        if not m_id:
            m_id = get_m_id_with_input(result)
        if not m_id:
            continue

        n_diss = (
            calibration.signal_to_concentration(result["signal"])
            * dilution
            * initial_volume
        )
        sampling_time = None
        while sampling_time is None and m_id and not m_id == "c":
            measurement = Measurement.open(m_id)
            print("\n\n------ NOTES -------\n\n")
            measurement.print_notes()
            measurement.plot_experiment()
            print(
                f"\n\nICPMS point description = '{description}'. "
                + f"Dissolved {element} = {n_diss * 1e12} pmol.\n"
                + f"Close plot when ready to input sampling time"
            )
            plt.show()
            sampling_time_str = input(
                "Enter sampling time as experiment time in [s]. Enter 'm' if it's "
                "the wrong measurement."
            )
            if sampling_time_str == "m":
                m_id = get_m_id_with_input(result)
            else:
                sampling_time = float(sampling_time_str)

        if m_id == "c":
            m_id = None
            description = f"UNKNOWN M_ID {set} # {number} should be {sample} on {date}"

        icpms_point = ICPMSPoint(
            i_id=None if SAVE else -1,
            ic_id=calibration.id,
            m_id=m_id,
            sampling_time=sampling_time,
            element=element,
            mass=mass,
            signal=data_point[icpms_mass],
            dilution=dilution,
            initial_volume=initial_volume,
            description=description,
        )
        if SAVE:
            icpms_point.save()
