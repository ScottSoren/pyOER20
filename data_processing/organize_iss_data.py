"""This module goes through all the ISS data in the shared folder and
saves it in a more organized manner (as pickles).
"""
import pathlib
import time
import datetime
import pickle
import re
import json

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

# Create folder for organized data and metadata (json)
data_dest = (DATA_DIR / 'Data' / 'ISS' / 'organized_pickles')
data_dest.mkdir(parents=True, exist_ok=True)

cwd = pathlib.Path.cwd()
json_dest = cwd.parent / 'tables' / 'leis'
json_dest.mkdir(parents=True, exist_ok=True)

# Import data from the THETAPROBE setup
names = []
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

    # Plot data
    iss.plot_all_scans()

    # Time data
    tformat_old = '%d/%m/%Y  %H:%M:%S'
    dtime = datetime.datetime.strptime(iss.date, tformat_old)
    utime = time.mktime(dtime.timetuple())
    ftime = datetime.datetime.strftime(dtime, tformat_new)
    iss.date = dtime

    # Name data
    name = pathlib.Path(iss.filename)
    iss.sample = name.parent.name.split('_')[0]
    extra_comment = iss.sample.split(' ')
    if len(extra_comment) > 1:
        iss.sample = extra_comment[0]
        extra_comment = ' '.join(extra_comment[1:])
    else:
        extra_comment = ''
    iss.comment = str.join('-', name.parent.name.split('_')[1:])
    if extra_comment:
        iss.comment += extra_comment
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

    # Generate or update JSON information
    json_dict = {
        'raw_data_path': iss.filename,
        'pickle_name': filepath.name,
        'recorded_on': iss.setup,
        'datetime': ftime,
        'timestamp': utime,
        'comment': iss.comment,
        'note': iss.note[0], # iss.note
        'num_of_datasets': 1, # iss.scans
        }
    json_name = json_dest / f'{iss.sample}.json'
    if json_name.exists():
        # Update existing data
        with open(json_name, "r") as f:
            dict_contents = json.load(f)
        existing_keys = [int(s) for s in dict_contents['data'].keys()]
        existing_keys.sort()

        # Experiment exists as JSON
        exists = False
        for key in existing_keys:
            if dict_contents['data'][str(key)]['pickle_name'] == filepath.name:
                # Experiment exists as JSON
                exists = True
                break
        if exists:
            # This is where we would update existing data if such
            # was needed.
            continue

        # Add dataset to sample
        new_key = str(key + 1)
        dict_contents['data'][new_key] = json_dict
        with open(json_name, 'w') as f:
            print(f'Adding index {new_key} to file: {json_name}')
            json.dump(dict_contents, f, indent=4)
    else:
        # Create entry
        dict_contents = {
            'data': {
                '0': json_dict
                },
            'custom': {
                'results': {},
                'measurements': {},
                },
            }
        with open(json_name, 'w') as f:
            print(f'Creating file: {json_name}')
            json.dump(dict_contents, f, indent=4)

iss.add_mass_lines([16, 18, 101, 192, 195, 197], offset=10)

# Import data from the OMICRON setup
print('Searching for Omicron data')
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

    # Plot data
    iss.plot_all_scans()

    # Save data (overwriting any existing matches?)
    names.append(new_name)
    filepath = data_dest / (new_name + '.pickle')
    if not filepath.exists() or overwrite:
        with open(filepath, 'wb') as f:
            pickle.dump(iss, f, pickle.HIGHEST_PROTOCOL)
        print('Writing data to: "{}"'.format(filepath))
    else:
        print('Not overwriting: "{}"'.format(filepath))

    # Generate or update JSON information
    json_dict = {
        'raw_data_path': iss.filename,
        'pickle_name': filepath.name,
        'recorded_on': 'omicron',
        'datetime': ftime,
        'timestamp': utime,
        'comment': iss.comment,
        'note': iss.note,
        'num_of_datasets': iss.scans,
        }
    json_name = json_dest / f'{iss.sample}.json'
    if json_name.exists():
        # Update existing data
        with open(json_name, "r") as f:
            dict_contents = json.load(f)
        existing_keys = [int(s) for s in dict_contents['data'].keys()]
        existing_keys.sort()
        exists = False
        for key in existing_keys:
            if dict_contents['data'][str(key)]['pickle_name'] == filepath.name:
                # Experiment exists as JSON
                exists = True
                break
        if exists:
            # This is where we would update existing data if such
            # was needed.
            continue

        # Add dataset to sample
        new_key = str(key + 1)
        dict_contents['data'][new_key] = json_dict
        with open(json_name, 'w') as f:
            print(f'Adding index {new_key} to file: {json_name}')
            json.dump(dict_contents, f, indent=4)
    else:
        # Create first entry
        dict_contents = {
            'data': {
                '0': json_dict
                },
            'custom': {
                'results': {},
                'measurements': {},
                },
            }
        with open(json_name, 'w') as f:
            print(f'Creating file: {json_name}')
            json.dump(dict_contents, f, indent=4)

iss.add_mass_lines([16, 18, 101, 192, 195, 197], offset=10)

print(f'Total number of data sets found: {len(names)}')

plt.show()
