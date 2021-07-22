"""ISS handler module for pyOER.

Simple usage:
You have ISS of samples, "Reshma1" and "Reshma2". You can load all
these samples by loading "Reshma" without a postfix. The following
piece of code will load ISS experiments for both sample series,
create a plot of the isotopic oxygen ratios for every spectrum, and
opening a plot verifying how accurate the peak decomposition is.

---- Code begin ----
import pyOER

# Load samples
experiment_chain = pyOER.ISS('Reshma')

# Plot isotopic oxygen ratios
experiment_chain.plot_fit_ratios(True)

# Spectrum number 7 appears to be the only outlier, so compare
# spectrum 6 and spectrum 7:
experiment_chain.plot_fit(6)
experiment_chain.plot_fit(7)

# The 5% O-18 could be explained by improper background subtraction
# and is therefore seemingly within the fitting error.
---- Code end ----
"""
import json
import pickle
import pathlib
import datetime

import numpy as np
import matplotlib.pyplot as plt

from .tools import weighted_smooth as smooth
#from .tools import smooth
from .tools import get_range
from .settings import DATA_DIR

class ISSIterator:
    """Iterator class for ISS"""
    def __init__(self, iss_handler):
        # Reference to main class
        self._handle = iss_handler
        self._index = 0
        # Loop through sets sorted by (earliest) date
        self._items = self._handle.relative_to(datetime.datetime(9999, 1, 1))['before']

    def __next__(self):
        """Return next dataset."""
        if self._index < len(self._handle):
            data = self._handle._active[self._items[self._index][0]]
            self._handle.active = self._items[self._index][0]
            self._index += 1
            return data
        raise StopIteration

class ISS:
    """ISS handler"""
    def __init__(self, sample=None, fit=None, verbose=False):
        """Main interface for the ISS data """
        self.verbose = verbose
        self.json_path = (pathlib.Path(__file__).absolute().parent.parent.parent
                     / 'tables' / 'leis')
        self.data_path = DATA_DIR / 'Data' / 'ISS' / 'organized_pickles'
        #self.files = self.get_list_of_all_pickles()
        self._active = None
        self._relative = None
        self._set_active = None
        self.plot_list = []
        self.sample = sample
        self._meta = None
        if sample is not None:
            self.get_sample(sample)
        # All reference data
        self._ref = pickle.load(open(self.data_path / 'iss_reference.pickle', 'rb'))
        self.fit_ratios = {}
        self.fit_coeffs = {}
        if fit is not None:
            self.fit_with_reference(peaks=fit, plot=False)

    def __iter__(self):
        """Loop through the datasets sorted from earliest to last."""
        return ISSIterator(self)

    def __len__(self):
        """Return the number of datasets currently loaded for sample."""
        return len(self.keys)

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
                print(f'\tComment (filename): {self._active[key].comment}')
                print(f'\tComment (from avg): {self._active[key].note[0]}')
                print(f'\tRecorded: {self._active[key].date}')
                print(f'\tPath: {self._active[key].filename}')

    def get_metadata(self, sample=None):
        """Fetch the JSON metadata corresponding to ´sample´.
If ´None´ (default), fetch JSON corresponding to current sample.
"""
        if sample is None:
            if self.sample is None:
                raise ValueError('You have to choose a sample')
            sample = self.sample
        # TODO: will give an error if not matching an existing file
        with open(self.json_path / (str(sample) + '.json'), 'r') as f:
            metadata = json.load(f)
        # Convert keys from string to integer
        for section in ['data', 'results', 'measurements']:
            swap = []
            if section == 'data':
                dictionary = metadata[section]
            else:
                dictionary = metadata['custom'][section]
            for key, value in dictionary.items():
                try:
                    int(key)
                    swap.append(key)
                except ValueError:
                    pass
            for key in swap:
                dictionary[int(key)] = dictionary[key]
                del dictionary[key]
        # Return
        if sample == self.sample:
            self._meta = metadata
        return metadata

    def save_json(self, metadata=None):
        """Save a metadata dictionary as JSON."""
        if metadata is None:
            if self._meta is None:
                raise ValueError('You have to choose a sample')
            metadata = self._meta
        if not isinstance(metadata, dict):
            # Not checking the contents/structure
            raise TypeError('´metadata´ in ´self.save_json´ must be of type dict')
        with open(self.json_path / metadata['file'], 'w') as f:
            json.dump(metadata, f, indent=4)

    def meta(self, key):
        """Serve the contents from metadata dict"""
        if key is None:
            # TODO: print available keys
            pass
        if key == 'file':
            return self._meta['file']
        if key == 'data':
            return self._meta['data'][self.active]
        if key in self._meta['data'][self.active].keys():
            return self._meta['data'][self.active][key]
        if key == 'custom':
            return self._meta['custom']
        if key == 'results':
            return self._meta['custom']['results'][self.active]
        if key in self._meta['custom']['results'][self.active].keys():
            return self._meta['custom']['results'][self.active][key]
        if key == 'measurements':
            return self._meta['custom']['measurements']
        # TODO: measurements


    def update_meta(self, key, value):
        """Update a field in the metadata dict"""
        if key is None:
            # TODO: print available keys
            pass
        if (
                key == 'file'
                or key == 'data'
                or key in self._meta['data'][self.active].keys()
                ):
            raise KeyError(
                f'The data for {key} is generated from raw data and shouldn\'t be'
                'changed. Use the "custom" data fields instead!'
                )
        if key == 'custom':
            self._meta['custom'] = value
        if key == 'results':
            self._meta['custom']['results'][self.active] = value
        if key in self._meta['custom']['results'][self.active].keys():
            self._meta['custom']['results'][self.active][key] = value
        if key == 'measurements':
            self._meta['custom']['measurements'] = value
        # TODO: measurements

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

    def relative_to(self, timestamp):
        """Take active list and return sorted relative to timestamp
'timestamp' must be either datetime object or string of type 20A31"""
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
        if self.verbose:
            print('Unsorted list of (key, datetime)')
            print(list_)
        list_.sort(key=lambda x: x[1])
        if self.verbose:
            print('Sorted list of (key, datetime)')
            print(list_)
        match = False
        for i, (key, date) in enumerate(list_):
            if timestamp < date:
                match = True
                break
        if not match:
            i += 1
        return {
            'match': timestamp,
            'before': list_[:i],
            'after': list_[i:],
        }

    def get_sample(self, sample):
        """Get all ISS data involving sample_name"""
        self.sample = sample
        try:
            self.get_metadata()
        except ValueError:
            return
        keys = [key for key, data in self._meta['data'].items()]
        filenames = [data['pickle_name'] for key, data in self._meta['data'].items()]
        self._active = self.load_set(filenames, keys)

    def load_set(self, filenames, keys=None):
        """Take list of filenames and load it into sorted dictionary"""
        iss_dict = dict()
        if keys is None:
            iterator = enumerate(filenames)
        else:
            iterator = list(zip(keys, filenames))
        for i, filename in iterator:
            with open(self.data_path / filename, 'rb') as f:
                iss_dict[i] = pickle.load(f)
            if self.verbose:
                print(i, filename)
        return iss_dict

    def plot(self, selection=[], mass_lines=[], show=True):
        """Plot selected spectra.
        'selection' must be a list of keys matching 'iss_dict' returned by
        self.load_set.
        """
        import matplotlib.pyplot as plt
        if len(selection) == 0:
            selection = self.keys
        plt.figure('iss autoplot')
        self.labels
        if len(mass_lines) > 0:
            self._active[0].add_mass_lines(
                mass_lines,
                color='gray',
                labels=False,
                )
        for key in selection:
            data = self._active[key]
            plt.plot(data.x, data.y, label=f'{key} - {data.sample}')
            if self.verbose:
                #TODO format
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

    # Maybe a @classmethod ?
    def fit_with_reference(self, selection=None, peaks=[], plot_result=False,
                           align=True, verbose=self.verbose):
        """Fit reference data to selected datasets.

    Input  :
        selection (list): where each element is an integer representing
            a key in self._active. Each of these ISS objects will be fit
            to the  reference data. Defaults to all datasets.
        peaks (list): where each element is an integer representing the
            mass of the elements to fit. If elements should be compared
            group-wise, as in O-16 or O-18 to total oxygen signal, nest
            them in a list of their own, e.g. peaks=[[16, 18], 40]. No
            sensitivity factors are applied.
        plot_result (bool): whether or not to autoplot results. Default False.
        align (bool): has to be True (default) for now.

    Output :
        ratios (dict): which will contain the ratio of peak-to-peak(s)
            for every combination of peak in ´peaks´.

    Example:
    >>> ratio = self.fit_with_reference(peaks=[[16, 18]])
    >>> print(ratio['16/18'])
    2.917
    >>> print(ratio['16'])
    0.7447
        __________________________________________
    Notes:

    REFERENCE DATA:
        self._ref (nested dict)
        self._ref[setup][peak].keys() =

            'xy': xy-data of original spectrum
            'background': peak-subtracted original spectrum
            'peak': background-subtracted original spectrum
            'area': integrated signal of 'peak'
            'region': the [low, high] delimiter used for the peak
                 identification/background subtraction
            'file': full path to original spectrum on host computer
            'iss': original ISS object

    FITTING METHOD:
        for each spectrum in ´selection´:
            for each peak in ´peaks´:
                subtract background from spectrum using same region as ref;
                for each nested peak (if any):
                    add scaled nested peaks to background subtracted data for best fit;
                save fit result to ´results´ dictionary;

    RETURN METHOD:
        for each result in ´results´:
            for each other result in ´results´:
                if result != other result:
                    save to ´ratios´: (result)/(other result)
        for each nested peak:
            save to ´ratios´:
                'peak1' = peak1 / (peak1 + peak2)
                'peak2' = peak2 / (peak1 + peak2)
    """

        from scipy.optimize import curve_fit
        from scipy.interpolate import interp1d

        # Initialize constants
        if selection is None:
            selection = self.keys
        coeffs = {i: {} for i in selection}
        ratios = {i: {} for i in selection}
        if align: # TODO Consider checking if done already
            align_spectra(
                [val for key, val in self._active.items() if key in selection],
                limits=[350, 520],
                masses=[16, 18],
                key='oxygen',
                plot_result=plot_result,
                verbose=verbose,
        )
        if self.verbose:
            print('\nAlignment done\n--------')

        # Main loop
        self.background = {}
        for selected in selection:
            data_set = self._active[selected]
            if plot_result:
                import matplotlib.pyplot as plt
                plt.figure(f'Fitting: {data_set.sample} - {selected}')
            if not data_set.good:
                continue # skip bad data set
            ref = self._ref[data_set.setup]
            for peak in peaks:
                # Peak is single
                if isinstance(peak, int):
                    region = ref[peak]['region']
                    N = 1
                # Peak is a group
                elif isinstance(peak, list):
                    region = ref[peak[0]]['region']
                    N = len(peak)
                    for _ in peak:
                        if ref[_]['region'] != region:
                            raise ValueError(f'Grouped peaks "{peak}" are not\
defined by the same region'
                            )
                else:
                    raise TypeError(f'Item in kwarg peaks is not understood:\n\
{peak}\nMust be an integer or list of integers.')

                if self.verbose:
                    print('Selected: ', selected)
                    print('Region: ', region)

                # Subtract background and make accessible afterwards
                background = subtract_single_background(
                    np.vstack((data_set.shifted['oxygen'],
                    data_set.smoothed['oxygen'])).T,
                    ranges=[region],
                    )
                self.background[selected] = background
                isolated_peak = data_set.y - background
                isolated_peak[np.isnan(isolated_peak)] = 0.1
                if plot_result:
                    plt.plot(data_set.x, background, 'k:')# label='Background'
                    plt.plot(data_set.x, data_set.y, 'k-', label='Raw data')
                    plt.plot(data_set.shifted['oxygen'],
                             background, 'b:',
                             #label='Background',
                             )
                    plt.plot(data_set.shifted['oxygen'],
                             data_set.y, 'b-',
                             label='Aligned data',
                             )

                # Create a common x-axis for comparisons
                pseudo_x = np.linspace(
                    region[0],
                    region[1],
                    (region[1] - region[0])*10 + 1,
                    )
                interp_dat = interp1d(
                    data_set.shifted['oxygen'],
                    isolated_peak,
                    kind='linear',
                    )
                interp_back = interp1d(
                    data_set.shifted['oxygen'],
                    background,
                    kind='linear',
                    )
                interp_ref = {}
                interp_ref[16] = interp1d(
                    ref[16]['xy'][:, 0],
                    ref[16]['peak'],
                    kind='linear',
                    )
                interp_ref[18] = interp1d(
                    ref[18]['xy'][:, 0],
                    ref[18]['peak'],
                    kind='linear',
                    )
                mask = get_range(pseudo_x, *region)
                dat_x = pseudo_x[mask]
                dat_y = interp_dat(dat_x)
                if plot_result:
                    plt.plot(
                        ref[16]['xy'][:, 0],
                        ref[16]['peak'],
                        'r:',
                        label='O16 ref',
                        )
                    plt.plot(
                        ref[18]['xy'][:, 0],
                        ref[18]['peak'],
                        'g:',
                        label='O18 ref',
                        )

                def func(x, *args):
                    """Fitting function"""
                    signal = x*0
                    for arg, i in list(zip(args, peak)):
                        signal += arg*interp_ref[i](x)
                    return signal

                # Fit reference to data
                fit, _ = curve_fit(
                    func,
                    dat_x,
                    dat_y,
                    p0=[2.]*N,
                    bounds=(0, 3),
                )
                fitted_signal = interp_back(dat_x)
                for i in range(len(peak)):
                    coeffs[selected][peak[i]] = fit[i]
                    fitted_signal += interp_ref[peak[i]](dat_x)*fit[i]
                if plot_result:
                    plt.plot(
                        dat_x,
                        fitted_signal,
                        'y-',
                        label='Best fit',
                        )


            # Calculate output ratios
            total = 0
            all_peaks = []
            for peak in peaks:
                if isinstance(peak, list):
                    for peak_ in peak:
                        all_peaks.append(peak_)
                else:
                    all_peaks.append(peak)
            for peak1 in all_peaks:
                for peak2 in all_peaks:
                    if peak1 == peak2:
                        continue
                    a1 = ref[peak1]['area']
                    a2 = ref[peak2]['area']
                    c1 = coeffs[selected][peak1]
                    c2 = coeffs[selected][peak2]
                    ratios[selected][f'{peak1}/{peak2}'] = (
                        coeffs[selected][peak1]
                        * ref[peak1]['area']
                        / coeffs[selected][peak2]
                        / ref[peak2]['area']
                        )
            # Group ratios
            for peak in peaks:
                if not isinstance(peak, list):
                    continue
                total = 0
                for peak_ in peak:
                    coefficient = coeffs[selected][peak_]
                    total += ref[peak_]['area']*coefficient
                    ratios[selected][f'{peak_}'] = (
                        ref[peak_]['area'] * coefficient
                        )
                for peak_ in peak:
                    ratios[selected][f'{peak_}'] /= total
            if plot_result:
                data_set.add_mass_lines(all_peaks)
                plt.legend()

            # Save in object
            self.fit_ratios[selected] = ratios[selected]
            self.fit_coeffs[selected] = coeffs[selected]
        return ratios, coeffs

    def plot_fit_ratios(self, show_plot=False):
        """Make a plot of O16/18 ratios for instance"""
        # Make sure references have been fitted
        if len(self.fit_ratios.keys()) == 0:
            if self.verbose:
                print('Calling method "fit_with_reference(peaks=[[16, 18]])')
            self.fit_with_reference(peaks=[[16, 18]])

        # Prepare plot
        import matplotlib
        import matplotlib.pyplot as plt
        fig = plt.figure('Fit ratios plot title')
        ax = fig.add_axes([0.05, 0.15, 0.9, 0.6])
        colors = ['k', 'r', 'g', 'b', 'm']*10

        # Plot all O-16 ratios
        plot_data = []
        counter = 0

        for i in self.keys:
            # Skip bad data
            if not self._active[i].good:
                counter += 1
                continue
            # Plot good data
            plt.plot(counter, self.fit_ratios[i]['16']*100,
                     'o', color=colors[0],
                     )
            plot_data.append([
                self._active[i].sample,
                self,
                self._active[i].sample,
                self._active[i].date,
                counter,
                self.fit_ratios[i]['16'],
                self.fit_ratios[i]['18'],
                ])
            counter += 1

        # Plot formatting
        xticks = [i for (gen_name, data_object, name, date, i, r1, r2)
                  in plot_data]
        dates = [date_formatter(date)
                 for (gen_name, data_object, name, date, i, r1, r2)
                 in plot_data]
        xlabels = [f'{gen_name} {name.lstrip(gen_name)} - {i}'
                   for (gen_name, data_object, name, date, i, r1, r2)
                   in plot_data]

        # Some of the following secondary axis methods requires matplotlib > 3.1.x
        secaxx = ax.secondary_xaxis('top')
        secaxy = ax.secondary_yaxis('right')

        # Update canvas
        fig.canvas.draw()

        secaxy.set_ylabel('O-18 ratio (%)')
        yticks = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        ax.set_yticks(yticks)
        ax.set_yticklabels(yticks)
        secaxy.set_ticks(yticks)
        yticks.reverse()
        yticks = [str(i) for i in yticks]
        secaxy.set_yticklabels(yticks)
        secaxx.set_xticks(xticks)
        secaxx.set_xticklabels(dates, rotation=90, fontsize=12)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xlabels, rotation=90, fontsize=12)
        ax.set_ylabel('O-16 ratio (%)')
        plt.grid(True)
        if show_plot is True:
            plt.show()

    def plot_fit(self, index=0, labels=True, show=True):
        """Visually verify the automatic fit to reference data"""

        # Make sure references have been fitted
        if len(self.fit_ratios.keys()) == 0:
            if self.verbose:
                print('Calling method "fit_with_reference(peaks=[[16, 18]])')
            self.fit_with_reference(peaks=[[16, 18]])

        # Initialize figure
        import matplotlib.pyplot as plt
        plt.figure(
            f'Peak Deconvolution _ {self._active[index].sample} - {index}'
            )

        # Compared x arrays are shifted with respect to each other.
        x_common = np.linspace(0, 1000, num=1001)
        num = 4 # repetitions/width for smooth function

        setup = self._active[index].setup
        ref1 = self._ref[setup][16]['peak']
        ref2 = self._ref[setup][18]['peak']

        # Raw + background
        x = self._active[index].shifted['oxygen']
        plt.plot(
            x,
            self._active[index].y,
            'k-', label='Raw aligned',
            )
        raw = np.interp(x_common, x, smooth(self._active[index].y, num), left=0, right=0)
        plt.plot(
            x_common,
            raw,
            'b-', label='Raw smoothed',
            )
        background = np.interp(x_common, x, smooth(self.background[index], 2), left=0, right=0)
        plt.plot(
            x_common,
            background,
            'b:', label='Background',
            )

        x_ref1 = self._ref[setup][16]['xy'][:, 0]
        y_ref1 = ref1 * self.fit_coeffs[index][16]
        y_ref1 = np.interp(x_common, x_ref1, smooth(y_ref1, 2), left=0, right=0)
        x_ref2 = self._ref[setup][18]['xy'][:, 0]
        y_ref2 = ref2 * self.fit_coeffs[index][18]
        y_ref2 = np.interp(x_common, x_ref2, smooth(y_ref2, 2), left=0, right=0)

        # Total fit
        x = self._active[index].shifted['oxygen']
        plt.plot(
            x_common,
            background + y_ref1 + y_ref2,
            'y-', label='Sum of components',
            )
        plt.plot(
            x_common,
            y_ref1,
            'r-',
            label='O-16 component',
            )
        plt.plot(
            x_common,
            y_ref2,
            'g-',
            label='O-18 component',
            )
        self._active[index].add_mass_lines([16, 18, 101], labels=labels)

        # Show
        plt.title(self._active[index].sample)
        plt.xlabel('Energy (eV)')
        plt.ylabel('Counts per second')
        plt.legend()
        if show:
            plt.show()

def date_formatter(date, latex=True):
    """Take datetime object and return string of YYADD"""
    YY = date.year - 2000
    M = date.month
    DD = date.day
    hh = date.hour
    mm = date.minute
    ss = date.second
    translate = {1: 'a', 2: 'b', 3: 'c', 4: 'd', 5: 'e', 6: 'f', 7: 'g',
        8: 'h', 9: 'i', 10: 'j', 11: 'k', 12: 'l'}
    string = f"{YY}{translate[M].upper()}{DD} {hh}:{mm}:{ss}"
    string = ((r"$\bf{" if latex else "")
              + f"{str(YY).zfill(2)}{translate[M].upper()}{str(DD).zfill(2)}"
              + (r"}$" if latex else "")
              + f"   {str(hh).zfill(2)}:{str(mm).zfill(2)}:{str(ss).zfill(2)}"
              )
    return string

def subtract_single_background(xy, ranges=[], avg=3, verbose=False):
    """Subtract the background from a single spectrum"""
    import common_toolbox as ct
    x, y = xy[:, 0], xy[:, 1]
    background = np.copy(y)
    for limit in ranges:
        indice = get_range(x, *limit)
        # if first index is chosen
        # OR
        # if last ten indice are included
        if indice[0] == 0 or indice[-1] > len(x) - 10:
            if verbose:
                print('Uhh', indice[0], indice[-1], limit)
                print(f'Searching for indice within limits: {limit}')
                print(f'First and last index: {indice[0]} and {indice[-1]} out of total {len(x) - 1}')
                print(f'This is x = [{x[indice[0]]} and {x[indice[-1]]}]')
            background[indice] = 0
        elif len(indice) == 0:
            if verbose:
                print('Did not find data within limit: {}'.format(limit))
        else:
            y1 = np.average(y[indice[0]-avg:indice[0]+avg])
            y2 = np.average(y[indice[-1]-avg:indice[-1]+avg])
            a_coeff = (y2-y1)/(limit[1]-limit[0])
            b_coeff = y1 - a_coeff*limit[0]
            background[indice] = x[indice]*a_coeff + b_coeff
    return background

def align_spectra(iss_data, limits=[350, 520], masses=[16, 18], key='oxygen',
                  plot_result=False, verbose=False, func_type='skewed'):
    """Shift the iss data within 'limits' region to snap maximum signal
unto nearest mass in list 'masses'.

    function (str): One of 'parabola', 'gauss' or 'skewed' (default). Determines the
    type of function used to align the spectra. """

    from scipy.optimize import curve_fit
    from scipy.special import erf
    if plot_result:
        import matplotlib.pyplot as plt

    def parabola(x, a, b, c):
        """ 2nd degree polynomial """
        return a*x**2 + b*x + c

    def gauss(x, A, x0, sigma):
        """ Gauss function or normal distribution """
        return A*np.exp(-(x - x0)**2 / 2 / sigma**2)

    def skewed(x, A, x0, sigma, alpha):
        """ Skewed gauss function """
        return 2/sigma * gauss(x, A, x0, sigma) * erf(alpha*(x - x0)/sigma)

    if verbose:
        print('Entering function "align_spectra"')
    for data in iss_data:
        # Initialize attributes
        try:
            data.shifted
        except AttributeError:
            data.shifted = {}
        try:
            data.smoothed
        except AttributeError:
            data.smoothed = {}

        # Get index of region of interest
        index = get_range(data.x, *limits)
        # Find maximum in region
        ys = smooth(data.y, num=4)
        data.smoothed[key] = ys
        maximum = max(ys[index])
        if not np.isfinite(maximum):
            data.good = False
            # TODO: Add more information about data set
            print('Bad data encountered in "align_spectra". Skipping...') # when exactly does this happen?
            continue
        data.good = True
        i_max = np.where(ys == maximum)[0]
        x_max = data.x[i_max][0]

        # Estimate fitting parameters
        width = 20 # Estimate of peak width
        if func_type == 'skewed':
            p0 = [maximum, x_max + 10, width, -1]
            function = skewed
        elif func_type == 'parabola':
            a = -0.5 * maximum / width**2
            b = -2 * a * x_max
            c = maximum + b**2/4/a
            p0 = [a, b, c]
            function = parabola
        elif func_type == 'gauss':
            p0 = [maximum, x_max, width]
            function = gauss
        else:
            raise ValueError(f'func_type {func_type} not a valid option')
        new_index = get_range(data.x, x_max - 15, x_max + 15)
        fit, _ = curve_fit(
            function,
            data.x[new_index],
            data.y[new_index],
            p0=p0,
            maxfev=100000,
            )
        if verbose:
            print('Result of fit: ', fit)
        if plot_result:
            plt.figure((
                f'Aligning {data.sample} {date_formatter(data.date, latex=False)}'
                ' - mass {masses}'
                ))
            plt.plot(
                data.x[index],
                data.y[index],
                'k-',
                label='Raw data',
                )
            plt.plot(
                data.x[new_index],
                function(data.x[new_index], *p0),
                'g-',
                label='Estimated max',
                )
            plt.plot(
                data.x[new_index],
                function(data.x[new_index], *fit),
                'r-',
                label='Best fit max',
                )
        if function == parabola:
            new_x_max = -fit[1]/2/fit[0]
            if verbose:
                print(f'Raw "maximum" x: {x_max}\nFitted x: {new_x_max}')
        elif function == gauss:
            new_x_max = fit[1]
            if verbose:
                print(f'Raw "maximum" x: {x_max}\nFitted x: {new_x_max}')
        elif function == skewed:
            fit_x = np.linspace(min(data.x), max(data.x), num=16000)
            fit_y = skewed(fit_x, *fit)
            fit_i = np.where(fit_y == max(fit_y))[0]
            new_x_max = fit_x[fit_i][0]
            if verbose:
                print(f'Raw "maximum" x: {x_max}\nFitted x: {new_x_max}')
        x_max = new_x_max

        # Find difference from reference
        energies = data.convert_energy(np.array(masses))
        distances = x_max - energies
        distance = distances[np.where(abs(distances) == min(abs(distances)))[0][0]]
        # If distance is too big, something is wrong with the algorithm
        if verbose:
            print(f'Distance between fitted maximum and expected: {distance} eV')
        if abs(distance) > 15:
            distance = 0
            if verbose:
                print('***\nDismissing alignment algorithm !\n***')

        # Snap to nearest line
        data.shifted[key] = data.x - distance
        if plot_result:
            plt.plot(
                data.shifted[key],
                data.y,
                'b-',
                label='Aligned raw data',
                )
            plt.plot(
                data.shifted[key],
                ys,
                'c-',
                label='Aligned and smoothed',
                )
            data.add_mass_lines(masses)
            plt.legend()

    # Return a nd.array of modified xy data
    ret = []
    for data in iss_data:
        if data.good:
            ret.append((np.vstack((data.shifted[key], data.smoothed[key])).T))
        else:
            ret.append((0, 0))
    if len(iss_data) == 1:
        return ret[0]
    else:
        return ret

class Data():
    """Load an ISS experiment exported as text or VAMAS file.

Class loader copied from github.com/Ejler/DataTreatment/ISS.py
Renamed Experiment() -> Data()

Author: Jakob Ejler Sorensen
Version: 5.2
Date: 2021 July 21
    """

    def __init__(self, filename, mass=4, theta=146.7, E0=1000, default_scan=0):
        """Initialize the class"""
        # Constants
        self.settings = dict()
        self.settings['mass'] = mass
        self.settings['theta'] = theta
        self.settings['E0'] = E0
        self.default_scan = default_scan

        # Initialize variables
        self.energy = dict()
        self.cps = dict()
        self.dwell = dict()
        self.mode = dict()
        self.mode_value = dict()
        self.note = dict()
        self.date = ''
        filename = str(filename)
        self.filename = filename

        # Convenience function variables
        self.peak_positions = None
        self.peak_heights_raw = None
        self.peak_heights_bg = None
        self._background = None
        self.background_settings = {
            'type': None,
            'ranges': None,
            'on': False,
            }

        #----------------------------------------------------------------------
        # Read data from textfile:
        if filename.endswith('.txt'):
            # Open filename with ISS data
            f = open(filename, 'r')
            lines = f.readlines()
            f.close()
            self.format = 'Text file'

            start_points = [i for i, line in enumerate(lines) if line == 'Energy\tCounts\r\n']
            self.scans = len(start_points)
            if self.scans == 0:
                raise ImportError('File apparently empty!')

            if lines[0].lower().startswith('note'):
                self.note = lines[0].split('=')[1].lstrip(' ')
            # Copy data points
            counter = 0
            for start in start_points:
                line = lines[start-4].split('\t')
                for i, word in enumerate(line):
                    if word.lower() == 'dwell':
                        self.dwell[counter] = float(lines[start-3].split('\t')[i])
                if not start == start_points[-1]:
                    interval = range(start+1, start_points[counter+1]-4)
                else:
                    interval = range(start+1, len(lines))
                self.energy[counter] = np.zeros(len(interval))
                self.cps[counter] = np.zeros(len(interval))
                counter_inner = 0
                for index in interval:
                    line = lines[index].rstrip().split('\t')
                    self.energy[counter][counter_inner] = float(line[0])
                    self.cps[counter][counter_inner] = float(line[1])
                    counter_inner += 1
                self.cps[counter] = self.cps[counter]/self.dwell[counter]
                counter += 1
        #----------------------------------------------------------------------
        # Read data from old VAMAS block file
        elif filename.endswith('.vms'):
            # Open filename with ISS data
            f = open(filename, 'r')
            lines = f.readlines()
            f.close()
            # Old format:
            if lines[6].lower().startswith('experiment type'):
                self.setup = 'omicron'
                self.format = 'Old VAMAS'
                #print('Loading file: ' + filename)
                blocks_4 = [i for i, line in enumerate(lines) if (line.strip() == '-1') \
and (lines[i+1].lower().strip() == 'kinetic energy')]
                blocks_2_ISS = [i for i, line in enumerate(lines) if (line.strip() == 'ISS') \
and (lines[i+1].strip() == '')]
                print(lines[9].rstrip())
                self.scans = len(blocks_4)
                if len(blocks_4) == int(lines[9].rstrip()) \
and len(blocks_4) == len(blocks_2_ISS):
                    self.scans = len(blocks_4)
                else:
                    msg = 'Error: Identified {} "Block 4", {} "Block 2", but "Block 1" says: {}'
                    msg = msg.format(len(blocks_4), len(blocks_2_ISS), int(lines[9].rstrip()))
                    raise ImportError(msg)

                # Copy data points
                self.note = dict()
                for counter, block in enumerate(blocks_4):
                    if not len(lines[blocks_2_ISS[counter] - 1]) == 5:
                        self.note[counter] = lines[blocks_2_ISS[counter] - 1].rstrip()
                    else:
                        self.note[counter] = ''
                    self.mode[counter] = lines[block-11].rstrip()
                    self.mode_value[counter] = float(lines[block-10].rstrip())
                    self.dwell[counter] = float(lines[block+9].rstrip())
                    data_points = int(lines[block+16])
                    self.cps[counter] = np.zeros(data_points)
                    E_step = float(lines[block+4].rstrip())
                    E_start = float(lines[block+3].rstrip())
                    self.energy[counter] = np.arange(data_points)*E_step + E_start
                    for counter_inner in range(data_points):
                        self.cps[counter][counter_inner] = float(lines[block+19+counter_inner]) \
/self.dwell[counter]
                self.note[counter] = ''
                print(self.energy.keys())
                print('Comments: {}'.format(self.note))
                print('Dwell time: {}'.format(self.dwell))
                print('Modes: {}'.format(self.mode))
                print('Mode values: {}'.format(self.mode_value))
            #----------------------------------------------------------------------
            # New format
            if lines[6].lower().startswith('created with'):
                self.setup = 'omicron'
                self.format = 'New VAMAS'
                ENDING = '_1-Detector_Region.vms'

                # Do a search to find all files with matching name structure
                filename = pathlib.Path(filename)
                path = filename.parent
                filename = filename.name
                filen = filename.split('--')[0]
                search_for = filen + '*.vms'
                list_of_files = list(path.rglob(search_for))
                # Make sure the list is properly sorted
                try:
                    keys = [
                        int(str(name).split('--')[1].split('_')[0])
                        for name
                        in list_of_files
                        ]
                except IndexError:
                    for i in list_of_files:
                        print(i)
                    raise
                keys.sort()
                list_of_files = [
                    f'{filen}--{key}{ENDING}'
                    for key
                    in keys
                    ]
                self.scans = len(list_of_files)
                for counter, filename in enumerate(list_of_files):
                    # Load contents
                    with open(path / filename, 'r') as f:
                        lines = f.readlines()
                        f.close()

                    # Analyze contents
                    blocks_4 = [i for i, line in enumerate(lines) if (line.rstrip() == '-1') \
and (lines[i+1].lower().rstrip() == 'kinetic energy')]
                    if len(blocks_4) > 1:
                        print('*** Interesting! More than 1 scan has been detected in above file!')
                    # Copy data points
                    i = blocks_4[0]
                    ###
                    if counter == 0:
                        _counter = 0
                        while True:
                            if lines[_counter].startswith('CREATION COMMENT START'):
                                comment_start = _counter
                                break
                            else:
                                _counter += 1
                                if _counter > len(lines):
                                    break
                        _counter = 0
                        while True:
                            if lines[_counter].startswith('CREATION COMMENT END'):
                                comment_end = _counter
                                break
                            else:
                                _counter += 1
                                if _counter > len(lines):
                                    break
                    self.note = lines[comment_start+1:comment_end]
                    ###
                    self.mode[counter] = lines[i-11].rstrip()
                    self.mode_value[counter] = float(lines[i-10].rstrip())
                    self.dwell[counter] = float(lines[i+9].rstrip())
                    data_points = int(lines[i+16])
                    self.cps[counter] = np.zeros(data_points)
                    E_step = float(lines[i+4].rstrip())
                    E_start = float(lines[i+3].rstrip())
                    self.energy[counter] = np.arange(data_points)*E_step + E_start
                    for counter_inner in range(data_points):
                        self.cps[counter][counter_inner] = float(lines[i+19+counter_inner]) \
/self.dwell[counter]
        #----------------------------------------------------------------------
        # Import Thetaprobe .avg data
        elif filename.endswith('.avg'):
            self.setup = 'thetaprobe'
            with open(filename, 'r', encoding='latin-1') as f:
                lines = f.readlines()

            # Check for ISS
            info = {line.split(':')[0].strip(): line.split('=')[1].strip() for line in lines if line.startswith('DS_')}
            if info['DS_ANPROPID_LENS_MODE_NAME'] != "'ISS'":
                print('{} does not appear to be an ISS experiment!'.format(self.filename))
                print('Expected \'ISS\', but encountered: {}'.format(info['DS_ANPROPID_LENS_MODE_NAME']))
                raise ImportError('File not an ISS experiment!')
            if info['DS_EXT_SUPROPID_CREATED'] == info['DS_EXT_SUPROPID_SAVED']:
                #print('Created and saved dates are identical - checking for empty dataset...')
                check_empty = True
            else:
                check_empty = False

            # Metadata
            self.note[0] = info['DS_EXT_SUPROPID_SUBJECT']
            self.date = info['DS_EXT_SUPROPID_CREATED']
            self.dwell[0] = float(info['DS_ACPROPID_ACQ_TIME'])
            self.mode[0] = int(info['DS_ANPROPID_MODE'])
            self.mode_value[0] = float(info['DS_ANPROPID_PASS'])
            if info['DS_GEPROPID_VALUE_LABEL'] == "'Counts'":
                normalize = True # normalize to "counts per second"
            else:
                normalize = False

            # Data
            #data_info = {}
            line_number = [i for i, line in enumerate(lines) if line.startswith('$DATAAXES')]
            if len(line_number) > 1:
                print('Reading file: {}'.format(self.filename))
                raise ImportError('Import of multiple dataaxes not implemented yet!')
            else:
                line_number = line_number[0]
            keys = [key.strip() for key in lines[line_number-1].split('=')[1].split(',')]
            values = [key.strip() for key in lines[line_number+1].split('=')[1].split(',')]
            data_info = {key: value for key, value in list(zip(keys, values))}

            start, end = float(data_info['start']), float(data_info['end'])

            #space_info = {}
            line_number = [i for i, line in enumerate(lines) if line.startswith('$SPACEAXES')]
            if len(line_number) > 1:
                print('Reading file: {}'.format(self.filename))
                raise ImportError('Import of multiple dataaxes not implemented yet!')
            else:
                line_number = line_number[0]
            keys = [key.strip() for key in lines[line_number-1].split('=')[1].split(',')]
            values = [key.strip() for key in lines[line_number+1].split('=')[1].split(',')]
            space_info = {key: value for key, value in list(zip(keys, values))}

            num = int(space_info['numPoints'])
            if space_info['linear'] != 'LINEAR':
                print('Reading file: {}'.format(self.filename))
                raise ImportError('Check .avg file if energy axis is linear!')

            # Generate xy-data
            self.energy[0] = np.linspace(start, end, num)
            self.cps[0] = self.energy[0]*np.nan

            line_number = [i for i, line in enumerate(lines) if line.startswith('$DATA=')]
            if len(line_number) > 1:
                msg = 'Reading file: {}'.format(self.filename)
                raise ImportError('Import of multiple dataaxes not implemented yet!')
            else:
                line_number = line_number[0]

            for j in range(num):
                if j%4 == 0: # values are grouped in chunks of 4
                    line_number += 1
                    line = lines[line_number].split('=')[1].split(',')
                try:
                    self.cps[0][j] = float(line[j%4])
                except ValueError:
                    pass # #empty# values
            if check_empty:
                if not np.any(np.isfinite(self.cps[0])):
                    raise ImportError('Dataset from {} is empty!'.format(self.filename))
                else:
                    print('Dataset appeared to be empty from the saved timestamps, but is not empty.')
            if normalize:
                self.cps[0] /= self.dwell[0]
        else:
            raise IOError('File: "{}" not found or fileending not accepted.'.format(self.filename))

        # Print loaded settings
        print('Successfully loaded file: {}'.format(filename))
        string = 'Used settings:\nProbing mass: {} amu\nScatter angle: {}\nPrimary energy: {} eV'
        #print(string.format(*[self.settings[key] for key in ['mass', 'theta', 'E0']]))

    @property
    def x(self):
        return self.energy[self.default_scan]

    @x.setter
    def x(self, var):
        if not var in self.energy.keys():
            print('"{}" not an available key! {}'.format(var, self.energy.keys()))
        self.default_scan = var

    @property
    def y(self):
        return self.cps[self.default_scan]

    @y.setter
    def y(self, var):
        if not var in self.energy.keys():
            print('"{}" not an available key! {}'.format(var, self.energy.keys()))
        self.default_scan = var

    @property
    def xy(self):
        return np.vstack((self.x, self.y)).T

    def get_xy(self, index):
        return np.vstack((self.energy[index], self.cps[index])).T

    @property
    def background(self):
        if self._background is not None:
            return self._background[self.default_scan]
        else:
            return None


    def convert_energy(self, mass):
        """Converts a measured energy to mass of surface atom
corresponding the settings stored in the experiment.
        """
        angle = self.settings['theta'] * np.pi/180
        return self.settings['E0'] * ((self.settings['mass']*np.cos(angle) + \
np.sqrt(mass**2 - self.settings['mass']**2*np.sin(angle)**2))/(mass + self.settings['mass']))**2


    def plot_all_scans(self, exclude=[None], color=None):
        """Plot all elements in file in single figure."""
        selection = [i for i in self.energy.keys() if not i in exclude]
        if not color:
            for i in selection:
                plt.plot(self.energy[i], self.cps[i])
        else:
            for i in selection:
                plt.plot(self.energy[i], self.cps[i], color=color)
        plt.xlabel('Kinetic energy (eV)')
        plt.ylabel('Counts per second')


    def normalize(self, interval='Max', exclude=[None], unit='Mass', delta_e=10):
        """Normalize to highest value in interval=[value1, value2]"""
        self.delta_e = delta_e
        if isinstance(interval, int):
            self.normalization_criteria = interval
        elif isinstance(interval, str):
            if interval == 'Total':
                self.normalization_criteria = 'all'
            elif interval.lower().startswith('max'):
                self.normalization_criteria = 'max'
            elif interval == 'Au':
                self.normalization_criteria = 196.
        if not isinstance(interval, list):
            if self.normalization_criteria == 'all':
                selection = [i for i in range(self.scans) if not i in exclude]
                for __counter in selection:
                    total = simps(self.cps[__counter], self.energy[__counter])
                    self.cps[__counter] /= total
            elif self.normalization_criteria == 'max':
                selection = [i for i in range(self.scans) if not i in exclude]
                for __counter in selection:
                    ydata = ct.smooth(self.cps[__counter], width=2)
                    norm_value = max(ydata)
                    self.cps[__counter] /= norm_value
            else:
                interval = [0, 0]
                if unit.lower() == 'mass':
                    interval[0] = self.convert_energy(self.normalization_criteria) - self.delta_e
                    interval[1] = self.convert_energy(self.normalization_criteria) + self.delta_e
                elif unit.lower() == 'energy':
                    interval[0] = self.normalization_criteria - self.delta_e
                    interval[1] = self.normalization_criteria + self.delta_e
                selection = [i for i in range(self.scans) if (not i in exclude) and \
                             (not interval[0] > max(self.energy[i])) and (not interval[1] < min(self.energy[i]))]
                for __counter in selection:
                    range_1 = np.where(self.energy[__counter] < interval[1])[0]
                    range_2 = np.where(self.energy[__counter] > interval[0])[0]
                    energy_range = np.intersect1d(range_1, range_2)
                    value = max(self.cps[__counter][energy_range])
                    self.cps[__counter] = self.cps[__counter]/value


    def add_mass_lines(self, masses, ax=None, offset=0, color='k', labels=True, linestyle='dotted', **kwargs):
        """Add vertical lines for mass references."""
        energies = self.convert_energy(np.array(masses))
        if ax is None:
            ax = plt.gca()
        [x1, x2, y1, y2] = ax.axis()
        for energy, mass in zip(energies, masses):
            ax.axvline(x=energy-offset, ymin=0, ymax=1, linestyle=linestyle, color=color, **kwargs)
            if labels:
                ax.text(float(energy)/x2, 0.95, 'm-{}'.format(mass), transform=ax.transAxes)


    def add_regions(self):
        """Add regions indicating the whereabouts of 3d, 4d, 5d metals and the
lanthanides and actinides."""
        ax = plt.gca()
        d3 = [45, 65]
        d4 = [89, 112]
        d5 = [178, 201]
        lant = [139, 175]
        act = [227, 260]
        for i in [d3, d4, d5]:
            ax.axvspan(xmin=self.convert_energy(i[0]), xmax=self.convert_energy(i[1]),
                       color='k', alpha=0.2)
        for i in [lant, act]:
            ax.axvspan(xmin=self.convert_energy(i[0]), xmax=self.convert_energy(i[1]),
                       color='y', alpha=0.2)

