import json
import numpy as np

from pyOER import Measurement


with open("notes/systematic_measurements.json", "r") as f:
    systematic_m_ids = {int(key): value for key, value in json.load(f).items()}

sample_types = {
    "Reshma1": "RT (amorphous) RuO2",
    "Reshma2": "200C RuO2",
    "Reshma3": "300C RuO2",
    "Reshma4": "400C (rutile) RuO2",
    "Nancy": "(EC-treated) amorphous RuO2",
    "Evans": "Ru foam",
    "Maundy": "rutile Ru^{18}O2",
    "Easter": "amorphous Ru^{18}O2",
    "Bernie": "(EC-treated) metallic Ru",
    "Melih": "(treated) metallic Ru",
    "Taiwan": "amorphous Ru^{18}O2",
    "Stoff": "rutile Ru^{18}O2",
    "John": "rutile Ru^{18}O2",
    "Sofie": "rutile Ru^{18}O2",
    "Mette": "rutile Ru^{18}O2",
    "Jazz": "(EC-treated) metallic Ir",
    "Folk": "(EC-treated) rutile IrO2",
    "Emil": "(EC-treated) rutile IrO2",
    "Ben": "(EC-treated) metallic Ir",
    "Goof": "RT Ir^{18}O2",
    "Champ": "400C Ir^{18}O2",
    "Decade": "RT Ir^{18}O2",
    "Legend": "400C Ir^{18}O2",
    "Trimi": "Pt",
}


def get_sample_type(sample):
    for key, sample_type in sample_types.items():
        if sample.startswith(key):
            return sample_type
    return "UNKNOWN"


iss_lines = ["Sample,\tType,\tm_id,\tECMS Date,\tECMS tstamp,\t30 min systematic?\n"]
icpms_operando_lines = [
    "Sample,\tType,\tm_id,\tECMS Date,\tECMS tstamp\t,"
    + "i_id,\tdescription,\tamount [pmol],\t"
    + "Electrolysis interval [s],\trate [pmol/s],\t"
    + "avg current density[mA],\tavg potential [VRHE]\n"
]

description_list = ["2 min", "10 min", "20 min", "30 min"]

for m_id, tag in systematic_m_ids.items():
    if tag in ["n", "f"]:
        continue
    m = Measurement.open(m_id)
    sample = m.sample_name
    date = m.date
    dataset = m.meas
    tstamp = dataset.tstamp
    sample_type = get_sample_type(sample)

    iss_lines += [
        f"{sample},\t{sample_type},\t{m_id},\t{date},\t{tstamp},\t{tag=='y'}\n"
    ]

    ips = m.get_icpms_points()
    if not ips:
        continue

    RE_vs_RHE = m.RE_vs_RHE
    if RE_vs_RHE is None:
        if m.id < 184:
            RE_vs_RHE = 0.715
            print("assuming RE_vs_RHE = 0.715, characteristic of 0.1 M HClO4")
        else:
            RE_vs_RHE = 0.66
            print("assuming RE_vs_RHE = 0.66, characteristic of 1.0 M HClO4")

    dataset.sync_metadata(RE_vs_RHE=RE_vs_RHE)

    useful_ips = {}

    for ip in ips:
        description = ip.description
        for d in description_list:
            if description.startswith(d):
                break
        else:
            print(f"don't know how to use '{ip}' of '{m}'.")
            continue
        amount = ip.amount
        t = ip.sampling_time
        useful_ips[d] = ip

    for d, ip in useful_ips.items():
        try:
            if d == "2 min":
                tspan = [ip.sampling_time - 120, ip.sampling_time]  # I don't like this
                # This gives problems (misses some electrolysis or includes some rest)
                # ... if the sample wasn't taken at exactly 2 minutes
            elif d == "10 min":
                tspan = [useful_ips["2 min"].sampling_time, ip.sampling_time]
            elif d == "20 min":
                tspan = [useful_ips["10 min"].sampling_time, ip.sampling_time]
            elif d == "30 min":
                tspan = [useful_ips["20 min"].sampling_time, ip.sampling_time]
            else:
                raise KeyError(f"don't know how to use '{ip}'")
        except KeyError as e:
            print(e)
            print("skipping that.")
            continue

        amount = ip.amount
        rate = ip.amount / [tspan[-1] - tspan[0]]

        t, I = dataset.get_current(tspan=tspan, unit="A")
        I_avg = np.mean(I) * 1e3  # [mA -> A]
        t, U = dataset.get_potential(tspan=tspan)
        U_avg = np.mean(U)
        # icpms_operando_lines = [
        #     "Sample,\tType,\tm_id,\tECMS Date,\tECMS tstamp\t,"
        #     + "i_id,\tdescription,\tamount [pmol],\t"
        #     + "Electrolysis interval [s],\trate [pmol/s],\t"
        #     + "avg current density[mA],\tavg potential [VRHE]\n"
        # ]
        icpms_operando_lines += [
            f"{sample},\t{sample_type},\t{m_id},\t{date},\t{tstamp},\t"
            + f"{ip.id},\t{ip.description},\t{amount*1e12},\t"
            + f"{tspan},\t{rate*1e12},\t"
            + f"{I_avg},\t{U_avg}\n"
        ]

    with open("notes/ecms_measurements_hopefully_iss_before_and_after.txt", "w") as f:
        f.writelines(iss_lines)

    with open("notes/icpms_results_from_operando_ecms.txt", "w") as f:
        f.writelines(icpms_operando_lines)
