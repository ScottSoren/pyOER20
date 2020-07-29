"""This script updates measurements with the metadata I manually read from elog"""

import re
from pathlib import Path
from pyOER import Measurement
from pyOER.elog import ElogEntry, read_elog_html

ELOG_FILE = Path("../elog/full_NOTES_cinfelog.html")
METADATA_DOC = Path("../descriptions/metadata_from_elog.txt")

MATCHERS = {  # regular expressions to match things from the metadata file
    "sample": r"([A-Z][a-z]+[0-9]+[A-Z]?)",
    "elog_and_date": r"([0-9]+), ([0-9]{2}[A-L][0-9]{2})",
    "measurement_ids": r"(m[0-9]+)(?:, (m[0-9]+))*",
}


def map_elog_sample_measurement():
    """Return a-layer dictionary with d[<elog_number>][<sample_name>] = <m_ids tuple>"""

    with open(METADATA_DOC, "r") as f:
        metadata_lines = f.readlines()

    n_elog = None  # the elog number
    date = None
    sample = None  # the sample name

    d = {}  # elog_sample_measurement

    for metadata_line in metadata_lines:
        elog_and_date_match = re.search(MATCHERS["elog_and_date"], metadata_line)
        if elog_and_date_match:
            n_elog, date = elog_and_date_match.groups()
            d[n_elog] = {}
            sample = None  # the sample is always specified after the elog number line
            continue

        if sample:  # if we know the sample, then we just need to get the measurements
            m_ids_match = re.search(MATCHERS["measurement_ids"], metadata_line)
            m_ids = m_ids_match.groups()
            d[n_elog][sample] = m_ids
            sample = None


if __name__ == "__main__":

    elog_entries = read_elog_html(ELOG_FILE, setup="ECMS")
    # elog_sample_measuremnts = map_elog_sample_measurement()
