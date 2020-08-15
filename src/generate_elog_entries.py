"""This script updates measurements with the metadata I manually read from elog"""

from pathlib import Path
from pyOER.elog import ElogEntry, read_elog_html

ELOG_FILE = Path("../elog/full_NOTES_cinfelog.html")
METADATA_DOC = Path("../descriptions/metadata_from_elog.txt")

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
