"""Correlate the electrocatalytic measurements with the leis data and record
it as metadata (json)."""
import pathlib
import json
import datetime
import numpy as np
import matplotlib.pyplot as plt
import pyOER

log_file = 'sample_overview.txt'
state_of_samples = {
    'uncorrelated': {},
    'correlated': {},
    'to_handle': {},
}

handle = pyOER.ISS()

# See if we have measurements with no LEIS data
all_leis = handle.all_leis()
for sample in pyOER.Sample.all_samples():
    if sample not in all_leis:
        state_of_samples['uncorrelated'][sample] = 'No LEIS available'

# Go through every LEIS sample
for sample in all_leis:

    # Load references
    try:
        s = pyOER.Sample(sample).open(sample)
    except FileNotFoundError:
        msg = 'LEIS sample not present in tables/samples/'
        state_of_samples['uncorrelated'][sample] = msg
        continue

    # Try to correlate sample
    print(f'\n*** {sample} ***')
    m_raw = np.unique(s.measurement_ids)
    m_raw.sort()
    #print(m_raw)
    m_sample = []
    for m_id, item in s.history.items():
        id_ = int(m_id[1:])
        m_sample.append(id_)
        measurement = pyOER.Measurement.open(id_)
        date = str(datetime.datetime.fromtimestamp(measurement.tstamp))
        tstamp = measurement.tstamp
        #print(m_id, date)
    print('\nid\t date\t\t\t\t   note')
    all_measurements = []
    for id_ in m_raw:
        measurement = pyOER.Measurement.open(id_)
        date = str(datetime.datetime.fromtimestamp(measurement.tstamp))
        tstamp = measurement.tstamp
        if id_ in m_sample:
            note = '<-- in Sample.history'
        else:
            note = ''
        
        all_measurements.append((f'm_{id_}', date, tstamp, note))

    handle.get_sample(sample)
    for data in handle:
        id_ = f'leis_{handle.active}'
        date = handle.meta('datetime')
        tstamp = handle.meta('timestamp')
        note = data.scans
        all_measurements.append((id_, date, tstamp, note))

    all_measurements.sort(key=lambda x: x[2])
    for id_, date, tstamp, note in all_measurements:
        print(f'{id_}\t {date}\t\t\t {note}')

    # Save in JSON (tmp)
    state_of_samples['to_handle'][sample] = all_measurements


# Save log
with open(handle.json_path / log_file, 'w') as f:
    json.dump(state_of_samples, f, indent=4)
