"""This module goes through all the ISS data in the shared folder and
saves it in a more organized manner (as pickles)"""
import pathlib
import time, datetime
import pickle
import ISS
from pyOER.settings import DATA_DIR

datapath = DATA_DIR / 'Thetaprobe'
all_files = datapath.rglob('He ISS.avg')

tformat_old = '%d/%m/%Y  %H:%M:%S'
tformat_new = '%Y-%m-%d %H:%M:%S'
# New filename:
# samplename_datetime_setup_comment.pickle
file_format_string = '{}__{}__{}__{}.pickle'

# Create folder for data
cwd = pathlib.Path.cwd()
destination = cwd.parent / 'tables' / 'iss_data'
print('Creating folder: {}'.format(destination))
try:
    pathlib.os.mkdir(destination)
    print('Folder created.')
except FileExistsError:
    print('Folder already exists.')


names = []
file_counter = 0
for file_ in all_files:
    try:
        # Load data
        iss = ISS.Experiment(file_, theta=135, E0=980)

        # Time data
        dtime = datetime.datetime.strptime(iss.date, tformat_old)
        utime = time.mktime(dtime.timetuple())
        ftime = datetime.datetime.strftime(dtime, tformat_new)
        iss.date = dtime

        # Name data
        name = pathlib.Path(iss.filename)
        iss.sample = name.parent.name.split('_')[0]
        iss.comment = str.join('-', name.parent.name.split('_')[1:])
        new_name = file_format_string.format(iss.sample, ftime, iss.setup, iss.comment)
        names.append(new_name)

        # Save data (overwriting any existing matches)
        with open(destination / new_name, 'wb') as f:
            pickle.dump(iss, f, pickle.HIGHEST_PROTOCOL)

        # Plot data
        iss.PlotAllScans()
    except ImportError as msg:
        print('*** ', msg, ' ***')
    file_counter += 1


iss.AddMassLines([16, 18, 101, 192, 195, 197], offset=10)
ISS.plt.show()
