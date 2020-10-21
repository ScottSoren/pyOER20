"""ISS handler module for pyOER.

Simple usage:
You have ISS of samples, "Reshma1" and "Reshma2". You can load all these samples by
loading "Reshma" without a postfix. The following piece of code will load ISS
experiments for both sample series, create a plot of the isotopic oxygen ratios for
every spectrum, and opening a plot verifying how accurate the peak decomposition is.

---- Code begin ----
import pyOER

# Load samples
experiment_chain = pyOER.ISS('Reshma')

# Plot isotopic oxygen ratios
experiment_chain.plot_fit_ratios(True)

# Spectrum number 7 appears to be the only outlier, so compare spectrum 6 and 7:
experiment_chain.plot_fit(6)
experiment_chain.plot_fit(7)

# The 5% O-18 could be explained by improper background subtraction and is therefore
# seemingly within the fitting error.
---- Code end ----
"""
import pickle
import pathlib
import numpy as np

import common_toolbox as ct

class ISS:
    def __init__(self, sample=None, fit=None):
        """ """
        self.path = pathlib.Path(__file__).absolute().parent.parent.parent / 'tables' / 'iss_data'
        self.files = self.get_list()
        self._active = None
        self._relative = None
        self._set_active = None
        self.plot_list = []
        if sample is not None:
            self.get_sample(sample)
        # All reference data
        self._ref = pickle.load(open(self.path / 'iss_reference.pickle', 'rb'))
        self.fit_ratios = {}
        self.fit_coeffs = {}
        if fit is not None:
            self.fit_with_reference(peaks=fit, plot=False)

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
            print(i, filename)
        print('load_set ', iss_dict)
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

    # Maybe a @classmethod ?
    def fit_with_reference(self, selection=None, peaks=[], plot=False, align=True):
        """Fit reference data to selected datasets.

Input  :
    selection (list) where each element is an integer representing a key in
        self._active. Each of these ISS objects will be fit to the reference
        data. Defaults to all datasets.
    peaks (list) where each element is an integer representing the mass of the
        elements to fit. If elements should be compared group-wise, as in O-16
        or O-18 to total oxygen signal, nest them in a list of their own, e.g.
        peaks=[[16, 18], 40]. No sensitivity factors are applied.
    plot (bool): whether or not to autoplot results. Default False.
    align (bool) has to be True (default) for now.

Output :
    ratios (dict) which will contain the ratio of peak-to-peak(s) for every
        combination of peak in ´peaks´.

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
        'region': the [low, high] delimiter used for the peak identification/
               background subtraction
        'file': full path to original spectrum on host computer
        'iss': original ISS object

FITTING METHOD:
    for each spectrum in ´selection´:
        for each peak in ´peaks´:
            subtract background from spectrum using same region as ref;
            for each nested peak (if any):
                add scaled nested peaks to background subtracted data for
                best fit;
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

        # Initialize constants
        if selection is None:
            selection = self.keys
        coeffs = {i: {} for i in selection}
        ratios = {i: {} for i in selection}
        if align is True:
            align_spectra(self._active.values(),
                limits=[350, 520],
                masses=[16, 18],
                key='oxygen',
                plot=plot,
        )

        # Main loop
        self.background = {}
        for selected in selection:
            if plot is True:
                import matplotlib.pyplot as plt
                plt.figure(f'Fitting: {selected}')
            data_set = self._active[selected]
            if data_set.good is False:
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

                # Subtract background and make accessible afterwards
                background = subtract_single_background(np.vstack((data_set.shifted['oxygen'], data_set.smoothed['oxygen'])).T, ranges=[region])
                self.background[selected] = background
                isolated_peak = data_set.y - background
                isolated_peak[np.isnan(isolated_peak)] = 0.1
                if plot is True:
                    plt.plot(data_set.x, background, 'k:', label='Background')
                    plt.plot(data_set.x, data_set.y, 'k-', label='Data')
                    plt.plot(data_set.shifted['oxygen'], background, 'r:', label='Background 1')
                    plt.plot(data_set.shifted['oxygen'], data_set.y, 'r-', label='Data 1')

                import common_toolbox as ct
                mask_dat = ct.get_range(data_set.shifted['oxygen'], *region)
                mask_ref = {}
                mask_ref[16] = ct.get_range(ref[16]['xy'][:, 0], *region)
                mask_ref[18] = ct.get_range(ref[18]['xy'][:, 0], *region)

                def func(x, *args):
                    """Fitting function"""
                    signal = x*0
                    for arg, i in list(zip(args, peak)):
                        signal += arg*ref[i]['peak'][mask_ref[i]]
                    return signal

                # Fit reference to data
                fit, _ = curve_fit(
                    func,
                    data_set.shifted['oxygen'][mask_dat],
                    isolated_peak[mask_dat],
                    p0=[2.]*N,
                    bounds=(0, 3),
                )
                for i in range(len(peak)):
                    coeffs[selected][peak[i]] = fit[i]

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
                    ratios[selected][f'{peak1}/{peak2}'] = coeffs[selected][peak1] * \
ref[peak1]['area'] / coeffs[selected][peak2] / ref[peak2]['area']
            # Group ratios
            for peak in peaks:
                if not isinstance(peak, list):
                    continue
                total = 0
                for peak_ in peak:
                    coefficient = coeffs[selected][peak_]
                    total += ref[peak_]['area']*coefficient
                    ratios[selected][f'{peak_}'] = ref[peak_]['area']*coefficient
                for peak_ in peak:
                    ratios[selected][f'{peak_}'] /= total
            if plot is True:
                plt.legend()
            # Save in object
            self.fit_ratios[selected] = ratios[selected]
            self.fit_coeffs[selected] = coeffs[selected]
        return ratios, coeffs

    def plot_fit_ratios(self, show_plot=False):
        """Make a plot of O16/18 ratios for instance"""
        # Make sure references have been fitted
        if len(self.fit_ratios.keys()) == 0:
            print('Calling method "fit_with_reference(peaks=[[16, 18]])')
            self.fit_with_reference(peaks=[[16, 18]])

        # Prepare plot
        import matplotlib.pyplot as plt
        fig = plt.figure('Fit ratios plot title')
        ax = fig.add_axes([0.05, 0.15, 0.9, 0.6])
        colors = ['k', 'r', 'g', 'b', 'm']*10

        # Plot all O-16 ratios
        plot_data = []
        counter = 0

        for i in self.keys:
            # Skip bad data
            if self._active[i].good is False:
                continue
            # Plot good data
            plt.plot(counter, self.fit_ratios[i]['16']*100, 'o', color=colors[0])
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
        xticks = [i for (gen_name, data_object, name, date, i, r1, r2) in plot_data]
        dates = [date_formatter(date) for (gen_name, data_object, name, date, i, r1, r2) in plot_data]
        xlabels = [f'{gen_name} {name.lstrip(gen_name)} - {i}' for (gen_name, data_object, name, date, i, r1, r2) in plot_data]

        secaxx = ax.secondary_xaxis('top')
        secaxy = ax.secondary_yaxis('right')

        # Update canvas
        fig.canvas.draw()

        secaxy.set_ylabel('O-18 ratio (%)')
        yticks = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        ax.set_yticks(yticks)
        ax.set_yticklabels(yticks)
        secaxy.set_yticks(yticks)
        yticks.reverse()
        secaxy.set_yticklabels(yticks)
        secaxx.set_xticks(xticks)
        secaxx.set_xticklabels(dates, rotation=90, fontsize=12)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xlabels, rotation=90, fontsize=12)
        ax.set_ylabel('O-16 ratio (%)')
        plt.grid(True)
        if show_plot is True:
            plt.show()

    def plot_fit(self, index=0):
        """Visually verify the automatic fit to reference data"""

        # Make sure references have been fitted
        if len(self.fit_ratios.keys()) == 0:
            print('Calling method "fit_with_reference(peaks=[[16, 18]])')
            self.fit_with_reference(peaks=[[16, 18]])

        # Initialize figure
        import matplotlib.pyplot as plt
        plt.figure(f'Peak Deconvolution _ {self._active[index].sample} - {index}')

        setup = self._active[index].setup
        ref1 = self._ref[setup][16]['peak']
        ref2 = self._ref[setup][18]['peak']

        # Raw + background
        plt.plot(self._active[index].shifted['oxygen'], self._active[index].y, 'b-', label='Raw')
        plt.plot(self._active[index].shifted['oxygen'], self.background[index], 'b:', label='Background')

        # Total fit
        plt.plot(self._active[index].shifted['oxygen'], self.background[index] + ref1*self.fit_coeffs[index][16] + ref2*self.fit_coeffs[index][18], 'y-', label='Sum of components')
        # A bit uncertain whether the reference data is properly aligned with the measured data during
        # the fits. But the results seem close enough.
        #plt.plot(self._ref[setup][16]['xy'][:, 0], self.background[index] + ref1*self.fit_coeffs[index][16] + ref2*self.fit_coeffs[index][18], 'm-')

        # Individual components
        plt.plot(self._ref[setup][16]['xy'][:, 0], ref1*self.fit_coeffs[index][16], 'r-', label='O-16 component')
        plt.plot(self._ref[setup][18]['xy'][:, 0], ref2*self.fit_coeffs[index][18], 'g-', label='O-18 component')
        self._active[index].AddMassLines([16, 18, 101])

        # Show
        plt.legend()
        plt.show()

def date_formatter(date):
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
    string = r"$\bf{" + f"{YY}{translate[M].upper()}{DD}" + r"}$" + f"   {hh}:{mm}:{ss}"
    return string

def subtract_single_background(xy, ranges=[], avg=3):
    """Subtract the background from a single spectrum"""
    import common_toolbox as ct
    x, y = xy[:, 0], xy[:, 1]
    background = np.copy(y)
    for limit in ranges:
        indice = ct.get_range(x, *limit)
        # if first index is chosen
        # OR
        # if last ten indice are included
        if indice[0] == 0 or indice[-1] > len(x) - 10:
            print('Uhh', indice[0], indice[-1], limit)
            background[indice] = 0
        elif len(indice) == 0:
            print('Did not find data within limit: {}'.format(limit))
        else:
            y1 = np.average(y[indice[0]-avg:indice[0]+avg])
            y2 = np.average(y[indice[-1]-avg:indice[-1]+avg])
            a_coeff = (y2-y1)/(limit[1]-limit[0])
            b_coeff = y1 - a_coeff*limit[0]
            background[indice] = x[indice]*a_coeff + b_coeff
    return background

def align_spectra(iss_data, limits=[350, 520], masses=[16, 18], key='oxygen', plot=False):
    """Shift the iss data within 'limits' region to snap maximum signal
unto nearest mass in list 'masses'."""

    if plot is True:
        import matplotlib.pyplot as plt
        plt.figure('aligned')
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
        index = ct.get_range(data.x, *limits)
        # Find maximum in region
        ys = ct.smooth(data.y, width=4)
        data.smoothed[key] = ys
        maximum = max(ys[index])
        if not np.isfinite(maximum):
            data.good = False
            continue # "Broken" dataset
        data.good = True
        i_max = np.where(ys == maximum)[0]
        x_max = data.x[i_max]

        # Find difference from reference
        energies = data.ConvertEnergy(np.array(masses))
        try:
            distance = np.abs(x_max - energies)
        except ValueError:
            print('ValueError')
            print(data.filename)
            print(data.x)
            print(data.y[np.isfinite(data.y)])
            print(data.smoothed[key])
            print(maximum)
            print(x_max)
            print(energies)
            if plot is True:
                plt.figure()
                plt.plot(data.x, data.y)
                plt.show()
            raise

        # Snap to nearest line
        data.shifted[key] = data.x - (x_max - energies)[np.where(distance == min(distance))[0]]
        if plot is True:
            plt.plot(data.shifted[key], data.y)
            plt.plot(data.shifted[key], ys)
    if plot is True:
        data.AddMassLines(masses)

    # Return a nd.array of modified xy data
    return np.vstack((data.shifted[key], data.smoothed[key])).T

