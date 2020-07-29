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

if __name__ == "__main__":
    elog_entries = read_elog_html(ELOG_FILE)
    for elog_entry in elog_entries:
        number = elog_entry.number
        try:
            elog_entry_0 = ElogEntry.open(number)
        except FileNotFoundError:
            pass
        else:
            elog_entry.update_with(elog_entry_0)
        elog_entry.save()
