from pathlib import Path
import json
from matplotlib import pyplot as plt

plt.interactive(False)

from pyOER import all_measurements

systematic_measurements_file = Path("./systematic_measurements.json")

if systematic_measurements_file.exists():
    with open("notes/systematic_measurements.json", "r") as f:
        systematic_m_ids = {int(key): value for key, value in json.load(f).items()}
else:
    systematic_m_ids = {}


systematic_types = {
    "y": "yes, purely systematic",  # 30 minutes at one current density, taken out at OCP just after, ICPMS samples at ~2, 10, 20 minutes.
    "s": "starts systematic",  # starts with one current density and ICPMS samples at 2 and 10 minutes, but play around after
    "k": "shortened systematic (<30 minutes)",  # systematic but for less than 30 minutes
    "c": "composite systematic",  # short systematic measurements, typically 10 minutes, at different current densities, with ICPMS samples taken interspersed
    "p": "some kind of constant-potential systematic",
    "f": "failed systematic",  # something is wrong.
    "n": "not systematic at all.",
    "d": "duplicate",
    "b": "broken",  # something is wrong with the file
    "q": "[Quit and save progress]",
}


def print_options():
    print(f"options are: ")
    for key, value in systematic_types.items():
        print(f"\t{key} : \t{value}")


for m in all_measurements():
    if m.id in systematic_m_ids:
        continue
    categories = m.category
    if isinstance(categories, str):
        categories = [categories]
    if not "exchange" in categories:
        continue
    m.print_notes()
    m.plot()
    print(
        f"Notes for {m} are above. Close the plot when you know to what degree "
        + "this is a systematic measurement."
    )
    print_options()
    plt.show()
    systematic_type = input("please enter the letter describing the measurement.")
    if systematic_type == "q":
        print("done for now.")
        break
    systematic_m_ids[m.id] = systematic_type
else:
    print("all done.")


with open("notes/systematic_measurements.json", "w") as f:
    json.dump(systematic_m_ids, f, indent=4)
