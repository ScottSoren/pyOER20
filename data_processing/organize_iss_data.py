"""This module goes through all the ISS data in the shared folder and
saves it in a more organized manner (as pickles).
"""
import pathlib
import time
import datetime
import pickle
import re

import matplotlib.pyplot as plt

#import ISS # github:Ejler/DataTreatment
from ejler_iss import Experiment # changed from above
from pyOER.settings import DATA_DIR, OMICRON_DIR
if not DATA_DIR.exists() or not OMICRON_DIR.exists():
    raise ImportError(
        "DATA_DIR and OMICRON_DIR in pyOER/settings.py must point to valid" \
        " paths for this script to be run."
        )

ALL_SAMPLES = [
    'Nancy',
    'Easter',
    'Taiwan',
    'Reshma',
    'Stoff',
    'John',
    'Evans',
    'Bernie',
    'Melih',
    'Trimi',
    'Jazz',
    'Folk',
    'Goof',
    'Legend',
    'Decade',
    ]

# Overwrite existing data
overwrite = False

# samplename_datetime_setup_comment.pickle
tformat_new = '%Y-%m-%d %H:%M:%S'
file_format_string = '{}__{}__{}__{}'

# Create folder for organized data and metadata
data_dest = (DATA_DIR / 'Data' / 'ISS' / 'organized_pickles')
data_dest.mkdir(parents=True, exist_ok=True)

cwd = pathlib.Path.cwd()
meta_dest = cwd.parent / 'tables' / 'leis'
meta_dest.mkdir(parents=True, exist_ok=True)


names = []
file_counter = 0
plt.figure('Thetaprobe')
datapath = DATA_DIR / 'Thetaprobe'
all_files = datapath.rglob('He ISS.avg')
for file_ in all_files:
    try:
        # Load data
        iss = Experiment(file_, theta=135, E0=980)
    except ImportError as msg:
        print('*** ', msg, ' ***')
        continue
    
    # Time data
    tformat_old = '%d/%m/%Y  %H:%M:%S'
    dtime = datetime.datetime.strptime(iss.date, tformat_old)
    utime = time.mktime(dtime.timetuple())
    ftime = datetime.datetime.strftime(dtime, tformat_new)
    iss.date = dtime

    # Name data
    name = pathlib.Path(iss.filename)
    iss.sample = name.parent.name.split('_')[0]
    iss.comment = str.join('-', name.parent.name.split('_')[1:])
    new_name = file_format_string.format(
        iss.sample,
        ftime,
        iss.setup,
        iss.comment,
        )
    names.append(new_name)

    # Save data (overwriting any existing matches?)
    filepath = data_dest / (new_name + '.pickle')
    if not filepath.exists() or overwrite:
        with open(filepath, 'wb') as f:
            pickle.dump(iss, f, pickle.HIGHEST_PROTOCOL)
        print('Writing data to: "{}"'.format(filepath))
    else:
        print('Not overwriting: "{}"'.format(filepath))

    # Plot data
    iss.plot_all_scans()
    file_counter += 1
iss.add_mass_lines([16, 18, 101, 192, 195, 197], offset=10)

print('Searching for Omicron data')
file_counter = 0
plt.figure('Omicron')
datapath = OMICRON_DIR
all_files = datapath.rglob('*ISS*.vms')
for file_ in all_files:
    # Filename must contain a reference to the family of samples
    if not [sample for sample in ALL_SAMPLES if (sample in str(file_.name))]:
        continue

    # Name data
    name_list = re.split('_', str(file_.name))
    comment, sample, _ = re.split('-', name_list[1])
    sample = sample.replace(' ', '')
    
    # Time data
    date = name_list[0]
    tformat_old = '%Y%m%d-%H%M%S'
    dtime = datetime.datetime.strptime(date, tformat_old)
    utime = time.mktime(dtime.timetuple())
    ftime = datetime.datetime.strftime(dtime, tformat_new)

    new_name = file_format_string.format(
        sample,
        ftime,
        'omicron',
        comment,
        )

    # Don't bother reloading dublicates
    if new_name in names:
        continue

    try:
        # Load data
        iss = Experiment(file_, theta=146.7, E0=1000)
        iss.date = dtime
        iss.comment = comment
        iss.sample = sample
    except ImportError as msg:
        print('*** ', msg, ' ***')
        continue

    names.append(new_name)

    # Save data (overwriting any existing matches?)
    filepath = data_dest / (new_name + '.pickle')
    if not filepath.exists() or overwrite:
        with open(filepath, 'wb') as f:
            pickle.dump(iss, f, pickle.HIGHEST_PROTOCOL)
        print('Writing data to: "{}"'.format(filepath))
    else:
        print('Not overwriting: "{}"'.format(filepath))

    # Plot data
    iss.plot_all_scans()
    file_counter += 1
iss.add_mass_lines([16, 18, 101, 192, 195, 197], offset=10)

print(f'Total number of data sets found: {len(names)}')

plt.show()
