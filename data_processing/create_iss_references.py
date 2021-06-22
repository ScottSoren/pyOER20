"""Modify the references used to fit ISS data"""
import pathlib
import pickle

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import simps

#import ejler_iss as ISS
from ejler_iss import Experiment
from pyOER import iss
from pyOER.settings import DATA_DIR, OMICRON_DIR
if not DATA_DIR.exists() or not OMICRON_DIR.exists():
    raise ImportError((
        "DATA_DIR and OMICRON_DIR in pyOER/settings.py must point to valid"
        + " paths for this script to be run."
        ))

# Overwrite existing files
overwrite = False

# Datasets
datapath = DATA_DIR / 'Thetaprobe'
# Moved to .settings:
#omicronpath = pathlib.Path('/home/jejsor/Dropbox/Characterizations/Ruthenium')

# Reference
filename = 'iss_reference'

# Create folder for organized data and metadata
data_dest = (DATA_DIR / 'Data' / 'ISS' / 'organized_pickles')
data_dest.mkdir(parents=True, exist_ok=True)

cwd = pathlib.Path.cwd()
meta_dest = cwd.parent / 'tables' / 'leis'
meta_dest.mkdir(parents=True, exist_ok=True)

# Selected datasets:
ref_regions = {
    'omicron': {
        'oxygen': [342, 470],
        'ruthenium': [760, 895],
        },
    'thetaprobe': {
        'oxygen': [350, 520],
        'ruthenium': [800, 880],
        },
    }
datasets = {# setup: {peak: (path_to_file, default_scan)}
    'thetaprobe': {
        'oxygen_16': (
            (
                datapath
                / 'All_data_and_text_files'
                / '19J20_before_new_tests'
                / '19J20_ISS'
                / 'Mono 400µm'
                / 'Reshma4F'
                / 'He ISS.avg'
                ),
            0),
        'oxygen_18': (
            (
                datapath
                / 'All_data_and_text_files'
                / '19D23_labeled_RuO2_and_Ir'
                / '19D23_ISS_depth_profile'
                / 'Mono 400µm'
                / 'Easter1A_new_spot_5min_He'
                / 'He ISS.avg'
                ),
            0),
        'ruthenium': (
            (
                datapath
                / 'All_data_and_text_files'
                / '19J20_before_new_tests'
                / '19J20_ISS'
                / 'Mono 400µm'
                / 'Reshma4F'
                / 'He ISS.avg'
                ),
            0),
    },
    'omicron': {
        'oxygen_16': (
            (
                OMICRON_DIR
                / 'Melih2'
                / '20190224-232058_As prepared-Melih 2-ESpHybrid_NanoSAM_ISS--1_1-Detector_Region.vms'
                ),
            5),
        'oxygen_18': (
            (
                OMICRON_DIR
                / 'Melih2'
                / '20190226-043610_Treated 05-Melih 2-ESpHybrid_NanoSAM_ISS--1_1-Detector_Region.vms'
                ),
            1),
        'ruthenium': (
            (
                OMICRON_DIR
                / 'Melih2'
                / '20190225-014442_Treated 02-Melih 2-ESpHybrid_NanoSAM_ISS--1_1-Detector_Region.vms'
                ),
            1),
    },
}

# Load experiments and save as references
ref_data = {key: {} for key in ref_regions}
for setup, info in datasets.items():
    for key, (path, default_scan) in info.items():
        # Load data with parameters depending on the parent setup
        if setup == 'omicron':
            data = Experiment(path, default_scan=default_scan, theta=146.7, E0=1000)
        elif setup == 'thetaprobe':
            data = Experiment(path, default_scan=default_scan, theta=135, E0=980)

        # Define parameters based on region of interest (key)
        if key.startswith('oxygen'):
            label = 'oxygen'
            mass = int(key[-2:])
            masses = [16, 18]
        elif key.startswith('ruthenium'):
            label = 'ruthenium'
            mass = 101
            masses = [101]
        else:
            raise ValueError(f'Key "{key}" doesn\'t fit into predefined categories')

        # Get peaks
        xy_aligned = iss.align_spectra(
            [data],
            limits = ref_regions[setup][label],
            masses = masses,
            key = label,
            )
        background = iss.subtract_single_background(
            xy_aligned,
            ranges = [ref_regions[setup][label]],
            )
        peak = xy_aligned[:, 1] - background

        # Save information in a dictionary, which will be dumped to a file for
        # future reference/use.
        ref_data[setup][mass] = {
            'xy': xy_aligned,
            'background': background,
            'peak': peak,
            'area': simps(peak[np.isfinite(peak)]),
            'region': ref_regions[setup][label],
            'file': data.filename,
            'iss': data,
            }

# Plots
plt.figure('Reference 18-O')
O16 = ref_data['thetaprobe'][16]
O18 = ref_data['thetaprobe'][18]
factor = 0.20 # manually subtract the O16 from O18 reference
plt.plot(
    O18['xy'][:, 0],
    O18['xy'][:, 1] - O16['peak']*factor,
    'm',
    label = f'O(18) - {factor}*O(16)',
    )
plt.plot(
    O18['xy'][:, 0],
    O18['xy'][:, 1],
    'g-',
    label = 'O(18)',
    )
plt.plot(
    O18['xy'][:, 0],
    O18['background'],
    'g-',
    )
plt.plot(
    O16['xy'][:, 0],
    O16['peak'],
    label = 'O(16) peak',
    )

# Correct for O-16 in thetaprobe reference
area = ref_data['thetaprobe'][18]['area']
print(f'Area before correcting for O-16: {area}')
peak = ref_data['thetaprobe'][18]['peak']
peak -= factor * ref_data['thetaprobe'][16]['peak']
ref_data['thetaprobe'][18]['area'] = simps(peak[np.isfinite(peak)])
area = ref_data['thetaprobe'][18]['area']
print(f'Area after (1): {area}')

# Correction check
plt.figure('Verify correction step - O(18)')
plt.plot(
    O18['xy'][:, 0],
    O18['xy'][:, 1],
    'g-',
    label = 'Reference',
    )
plt.plot(
    O18['xy'][:, 0],
    O18['background'],
    'g-',
    )
# Components

# Compute sum from components
plt.plot(
    O18['xy'][:, 0],
    O18['background'] + O18['peak'],
    'g-',
    label = 'O(18)',
    )
plt.plot(
    O18['xy'][:, 0],
    O18['background'] + factor*O16['peak'],
    'r-',
    label = 'O(16)',
    )
plt.plot(
    O18['xy'][:, 0],
    O18['background'] + O18['peak'] + factor*O16['peak'],
    'k:',
    label = 'Sum',
    )

plt.legend()
plt.show()

#1/0 ### EXIT without saving ###

# Save data
filepath = data_dest / (filename + '.pickle')
if not filepath.exists() or overwrite:
    with open(filepath, 'wb') as f:
        pickle.dump(ref_data, f, pickle.HIGHEST_PROTOCOL)
        print('Wrote ref_data to file')
else:
    print('File already exists. Not overwriting.')
