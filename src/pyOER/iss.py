"""ISS handler module for pyOER.
"""
import pickle
import pathlib

class ISS:
    def __init__(self, sample=None):
        """ """
        self.path = pathlib.Path(__file__).absolute().parent.parent.parent / 'tables' / 'iss_data'
        self.files = self.get_list()
        self._active = None
        self._relative = None
        self._set_active = None
        self.plot_list = []
        if sample is not None:
            self.get_sample(sample)

    @property
    def keys(self):
        if self._active is None:
            print('Use get_sample(name) to select datasets')
            return
        return [key for key in self._active.keys()]

    @property
    def labels(self, print_=True):
        if self._active is None:
            print('Use get_sample(name) to select datasets')
            return
        if print_ is True:
            for key in self.keys:
                print(f'Key: {key}')
                print(f'\tSample: {self._active[key].sample}')
                print(f'\tComment: {self._active[key].comment}')
                print(f'\tRecorded: {self._active[key].date}')
                print(f'\tPath: {self._active[key].filename}')
                #print(f'
        #return [key for key in self._active.keys()]

    @property
    def active(self):
        """Return active selection in a pretty way"""
        if self._set_active is None:
            pass # do something on all data
        else: # return selected dataset
            return self._set_active

    @active.setter
    def active(self, value):
        """Set active selection to a key or list of keys.
Set to None for certain effect."""
        ###
        # do some check of value here
        ###
        self._set_active = value

    def get_list(self):
        """Return a list of all iss pickles in data folder"""
        list_ = [filename for filename in pathlib.os.listdir(self.path) if filename.endswith('.pickle')]
        list_.sort()
        return list_

    def relative_to(self, timestamp, print_info=True):
        """Take active list and return sorted relative to timestamp
'timestamp' must be either datetime object or string of type 20A31"""
        import datetime
        a_to_1 = {'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6,
                  'g': 7, 'h': 8, 'i': 9, 'j': 10, 'k': 11, 'l': 12}
        if isinstance(timestamp, str):
            if len(timestamp) == 5:
                year = 2000 + int(timestamp[:2])
                month = a_to_1[timestamp[2].lower()]
                day = int(timestamp[-2:])
                timestamp = datetime.datetime(year, month, day)
        elif isinstance(timestamp, type(datetime.datetime.now())):
            pass
        else:
            print('Timestamp type not understood')
            return
        list_ = [(key, self._active[key].date) for key in self.keys]
        print(list_)
        list_.sort(key=lambda x: x[1])
        print(list_)
        for i, (key, date) in enumerate(list_):
            if timestamp < date:
                break
        return {
            'match': timestamp,
            'before': list_[:i],
            'after': list_[i:],
        }

    def get_sample(self, name):
        """Get all ISS data involving sample_name"""
        subset = [filename for filename in self.files if name in filename]
        self._active = self.load_set(subset)

    def load_set(self, filenames):
        """Take list of filenames and load it into sorted dictionary"""
        iss_dict = dict()
        for i, filename in enumerate(filenames):
            with open(self.path / filename, 'rb') as f:
                iss_dict[i] = pickle.load(f)
        return iss_dict

    def plot(self, selection=[], show=True):
        """Plot selected spectra.
'selection' must be a list of keys matching 'iss_dict' returned by self.load_set"""
        import matplotlib.pyplot as plt
        if len(selection) == 0:
            selection = self.keys
        plt.figure('iss autoplot')
        self.labels
        for key in selection:
            data = self._active[key]
            plt.plot(data.x, data.y, label=f'{key} - {data.sample}')
            print(key, data.date, data.filename)
        plt.legend()
        plt.xlabel('Energy (eV)')
        plt.ylabel('Counts per second')
        if show is True:
            plt.show()

    def show(self):
        """Show figures"""
        import matplotlib.pyplot as plt
        plt.show()
