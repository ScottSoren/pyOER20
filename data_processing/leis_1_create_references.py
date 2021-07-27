"""Modify the references used to fit ISS data"""
import pathlib
import pickle

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import simps

from pyOER import iss
from pyOER.settings import DATA_DIR, OMICRON_DIR
if not DATA_DIR.exists() or not OMICRON_DIR.exists():
    raise ImportError((
        "DATA_DIR and OMICRON_DIR in pyOER/settings.py must point to valid"
        " paths for this script to be run."
        ))

# Overwrite existing files
overwrite = False

# Datasets
datapath = DATA_DIR / 'Thetaprobe'

# Reference
filename = 'iss_reference.pickle'

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
ref_data = {setup: {} for setup in ref_regions}
for setup, info in datasets.items():
    for key, (path, default_scan) in info.items():
        # Load data with parameters depending on the parent setup
        if setup == 'omicron':
            data = iss.Data(path, default_scan=default_scan, theta=146.7, E0=1000)
        elif setup == 'thetaprobe':
            data = iss.Data(path, default_scan=default_scan, theta=135, E0=980)

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
        xy_aligned = xy_aligned[default_scan]
        plt.show()
        ranges = ref_regions[setup][label][:]
        # Modify the O16 (thetaprobe) range
        if setup == 'thetaprobe' and key == 'oxygen_16':
            ranges[0] = 330
            ranges[1] = 490
        background = iss.subtract_single_background(
            xy_aligned['xy'],
            ranges = [ranges],
            )
        peak = xy_aligned['y'] - background

        # Save information in a dictionary, which will be dumped to a file for
        # future reference/use.
        ref_data[setup][mass] = {
            'x': xy_aligned['x'],
            'y': xy_aligned['y'],
            'xy': xy_aligned['xy'],
            'background': background,
            'peak': peak,
            'area': simps(peak[np.isfinite(peak)]),
            'region': ref_regions[setup][label],
            'file': data.filename,
            'scan': default_scan,
            'iss': data,
            }

# Correct for O16 in Thetaprobe O18 reference
x_common = np.linspace(0, 1000, num=1001)

O16 = ref_data['thetaprobe'][16]
O18 = ref_data['thetaprobe'][18]
factor = 0.222 # manually subtract the O16 from O18 reference

# Correct for O-16 in thetaprobe reference
area = ref_data['thetaprobe'][18]['area']
peak_18 = ref_data['thetaprobe'][18]['peak'].copy()
peak_18 -= factor * iss.get_common_y(
    O18['x'],
    O16['x'],
    O16['peak'],
    )
peak_18[np.where(O18['x'] < 403)] = 0 # Clean up left edge

# Correct for O-18 in thetaprobe O-16 reference
peak_16 = O16['peak'].copy()
factor_18 = 0.002
peak_16 -= factor_18 * iss.get_common_y(
    O16['x'],
    O18['x'],
    peak_18, # the peak subtracted the O-16 component
    )
peak_16[np.where(O16['x'] < 345)] = 0 # Clean up left edge
peak_16[np.where(peak_16 < 0)] = 0

# Apply corrected peaks
O16['peak'] = peak_16
O18['peak'] -= factor * iss.get_common_y(
    O18['x'],
    O16['x'],
    O16['peak'],
    )
O18['peak'][np.where(O18['x'] < 403)] = 0 # Clean up left edge
O18['peak'][np.where(O18['peak'] < 0)] = 0

# Update integrated areas
O18['area'] = simps(O18['peak'][np.isfinite(O18['peak'])])
O16['area'] = simps(O16['peak'][np.isfinite(O16['peak'])])
print()

# Plots
plt.figure('Thetaprobe: Reference 18-O')
plt.axvline(x=407.5, color='gray', linestyle='dotted')
plt.axvline(x=452., color='gray', linestyle='dotted')
plt.plot(
    O18['x'],
    O18['peak'] + O18['background'],
    'g-',
    label = f'O(18) comp',
    )

plt.plot(
    O16['x'],
    (
        O16['peak'] * factor
        + iss.get_common_y(
            O16['x'],
            O18['x'],
            O18['background'],
            )
        ),
    'r-',
    label = 'O(16) comp',
    )
plt.plot(
    O18['x'],
    O18['y'],
    'k-',
    label = 'O(18) ref',
    )
plt.plot(
    O18['x'],
    O18['background'],
    'k:',
    )
plt.plot(
    x_common,
    (
        iss.get_common_y(
            x_common,
            O16['x'],
            O16['peak'] * factor,
            )
        + iss.get_common_y(
            x_common,
            O18['x'],
            O18['background'],
            )
        + iss.get_common_y(
            x_common,
            O18['x'],
            O18['peak'],
            )
        ),
    'y:',
    label = 'Total',
    linewidth=2,
    )
plt.legend()
a16 = O16['area']*factor
a18 = O18['area']
print('Thetaprobe O18 reference sample consists of:')
print(f'\tO16: {a16/(a16+a18):.1%}')
print(f'\tO18: {a18/(a16+a18):.1%}')
print()

plt.figure('Thetaprobe: Reference 16-O')
plt.axvline(x=407.5, color='gray', linestyle='dotted')
plt.axvline(x=452., color='gray', linestyle='dotted')
plt.plot(
    O16['x'],
    O16['background'] + O16['peak'],
    'r-',
    label='O(16) comp',
    )
plt.plot(
    O16['x'],
    (
        O16['background']
         + iss.get_common_y(
            O16['x'],
            O18['x'],
            O18['peak'] * factor_18,
            )
        ),
    'g-',
    label='O(18) comp',
    )
plt.plot(
    O16['x'],
    O16['y'],
    'k-',
    label = 'O(16) ref',
    )
plt.plot(
    O16['x'],
    O16['background'],
    'k:',
    )
plt.plot(
    O16['x'],
    (
        O16['background']
        + O16['peak']
        + iss.get_common_y(
            O16['x'],
            O18['x'],
            O18['peak'] * factor_18,
            )
        ),
    'y:',
    label='Total',
    linewidth=2,
    )
a16 = O16['area']
a18 = O18['area']*factor_18
print('Thetaprobe O16 reference sample consists of:')
print(f'\tO16: {a16/(a16+a18):.1%}')
print(f'\tO18: {a18/(a16+a18):.1%}')
print()
plt.legend()

# Show plots
plt.show()

#1/0 ### EXIT without saving ###

# Save data
filepath = data_dest / filename
if not filepath.exists() or overwrite:
    with open(filepath, 'wb') as f:
        pickle.dump(ref_data, f, pickle.HIGHEST_PROTOCOL)
        print('Wrote ref_data to file')
else:
    print('File already exists. Not overwriting.')
