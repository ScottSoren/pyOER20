"""This script generates TOF measurements from potential-hold RDE activity measurements

The numbers are copied from Reshma's "RuOx activity.xlsx" on 20F20.
"""
from pathlib import Path
import pandas as pd
from pyOER import TurnOverFrequency
from pyOER import (
    STANDARD_ELECTRODE_AREA,
    STANDARD_SPECIFIC_CAPACITANCE,
    STANDARD_SITE_DENSITY,
    FARADAY_CONSTANT,
)

for sample in ["Reshma1", "Reshma2", "Reshma3", "Reshma4"]:
    file_name = f"ec_{sample}.csv"
    file_path = Path("./data_for_import") / file_name

    df = pd.read_csv(file_path, header=0)

    for i in range(df.shape[0]):
        potential = df["V"][i]  # potential vs RHE / [V]
        j = df["current density (uA/cm2)"][i]
        j_norm = df["Current density (A/F)"][i]

        rate = j * 1e-6 * STANDARD_ELECTRODE_AREA / (4 * FARADAY_CONSTANT)
        tof = (
            j_norm
            / (4 * FARADAY_CONSTANT)
            * STANDARD_SPECIFIC_CAPACITANCE
            / STANDARD_SITE_DENSITY
        )

        result = TurnOverFrequency(
            tof_type="ec_activity",
            potential=potential,
            rate=rate,
            tof=tof,
            sample_name=sample,
        )
        result.save()
