"""This script updates measurements with the metadata I manually read from elog"""

import re
from pathlib import Path
from pyOER import Measurement
from pyOER.elog import ElogEntry, read_elog_html

ELOG_FILE = Path("../elog/full_NOTES_cinfelog.html")
METADATA_DOC = Path("../notes/metadata_from_elog.txt")

MATCHERS = {  # regular expressions to match things from the metadata file
    "sample": r"([A-Z][a-z]+[0-9]+[A-Z]?)",
    "elog_and_date": r"([0-9]+), ([0-9]{2}[A-L][0-9]{2})",
    "measurement_id": r"m([0-9]+)",
    "EC_tag": r"^\s*([0-9]+\.\.\.)",
}


def map_elog_sample_measurement():
    """Return a list of ElogEntry objects based on the elog measurement summary file"""

    with open(METADATA_DOC, "r") as f:
        metadata_lines = f.readlines()
    metadata_lines += ["9999, 99L99"]  # to make sure the last elog entry gets saved
    n_elog = None  # the elog number
    date = None
    sample = None  # the sample name
    EC_tag = None  # the prefix of the file names of the EC-Lab file set
    sample_measurements = {}  # will be populated by {sample: measurement_id_list}
    measurement_EC_tags = {}  # will be populated by {measurement_id: EC_tag}
    elog_entry_list = []

    for metadata_line in metadata_lines:
        elog_and_date_match = re.search(MATCHERS["elog_and_date"], metadata_line)
        if elog_and_date_match:
            if n_elog is not None:  # then it's time to store the previous elog
                elog_entry = ElogEntry(
                    setup="ECMS",
                    number=n_elog,
                    date=date,
                    sample_measurements=sample_measurements,
                    measurement_EC_tags=measurement_EC_tags,
                )
                try:
                    print(f"opening {n_elog}.")
                    elog_entry_0 = ElogEntry.open(n_elog)
                except FileNotFoundError:
                    pass
                else:
                    # elog_entry_0.update_with(elog_entry)
                    elog_entry_0.date = elog_entry.date
                    elog_entry_0.sample_measurements = elog_entry.sample_measurements
                    elog_entry_0.measurement_EC_tags = elog_entry.measurement_EC_tags
                    elog_entry = elog_entry_0
                elog_entry_list += [elog_entry]
            n_elog, date = elog_and_date_match.groups()
            sample_measurements = {}
            measurement_EC_tags = {}
            sample = None  # the sample is always specified after the elog number line

        elif sample:  # if we know the sample, then we just need to get the measurements
            if not sample in sample_measurements:
                sample_measurements[sample] = []
            m_id_strings = metadata_line.split(",")
            for m_id_string in m_id_strings:
                m_id_match = re.search(MATCHERS["measurement_id"], m_id_string)
                if m_id_match:
                    m_id = int(m_id_match.group(1))
                    sample_measurements[sample] += [m_id]
                    if EC_tag:
                        measurement_EC_tags[m_id] = EC_tag
            sample = None  # sample must be specified before every line of m_id's
            EC_tag = None  # there's no such thing as one EC tag with multiple samples

        EC_tag_match = re.search(MATCHERS["EC_tag"], metadata_line)
        if EC_tag_match:
            EC_tag = EC_tag_match.group(1)
        elif metadata_line.strip().startswith("#"):
            # commented lines seem to mean we're not sure, so they void the EC tag
            EC_tag = None

        sample_match = re.search(MATCHERS["sample"], metadata_line)
        if sample_match:
            sample = sample_match.group(1)
        elif re.search(r"[^#]*MS_data", metadata_line):
            sample = "_MS_data"

    return elog_entry_list


if __name__ == "__main__":
    elog_entries = map_elog_sample_measurement()

    for elog_entry in elog_entries:
        elog_entry.SAVE()
        date = elog_entry.date
        elog_number = elog_entry.number
        measurement_EC_tags = elog_entry.measurement_EC_tags
        for sample, m_ids in elog_entry.sample_measurements.items():
            for m_id in m_ids:
                measurement = Measurement.open(m_id)
                measurement.sample_name = sample
                measurement.date = date
                measurement.elog_number = elog_number
                if measurement_EC_tags and m_id in measurement_EC_tags:
                    measurement.EC_tag = measurement_EC_tags[m_id]
                measurement.make_name()
                measurement.save_with_rename()  # removes original file
