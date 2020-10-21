"""This module defines some pythony and mathy stuff used elsewhere"""
import numpy as np
from scipy.optimize import curve_fit


# a regular expression to match floats like '-3.5e4' or '7' or '245.13' or '1e-15':
FLOAT_MATCH = r"[-]?\d+[\.]?\d*(e[-]?\d+)?"
DATE_MATCH = r"[0-9]{2}[A-L][0-9]{2}"  # matches, e.g. 18H25 or 20J01


def singleton_decorator(cls):
    """decorator making cls into a singleton class"""

    class SingletonDecorator:
        def __init__(self, original_class):
            self.original_class = original_class
            self.instance = None

        def __call__(self, *args, **kwargs):
            if not self.instance:
                self.instance = self.original_class(*args, **kwargs)
            return self.instance

    return SingletonDecorator(cls)


class CounterWithFile:
    """A baseclass for counters where the number (the id) is stored in a file.

    Classes that inherit from this must override: _file
    Classes inheriting from this should maybe be decorated with @singleton_decorator
    """

    _id = None
    _file = None

    def last(self):
        """Return the last id"""
        if not self._id:
            with open(self._file, "r") as f:
                self._id = int(f.read())
        return self._id

    @property
    def id(self):
        """Iterate id and return the new id"""
        with open(self._file, "r") as f:
            self._id = int(f.read()) + 1
        with open(self._file, "w") as f:
            f.write(str(self._id))
        return self._id


def fit_exponential(t, y, zero_time_axis=False):
    """Return (tao, y0, y1) for best fit of y = y0 + (y1-y0) * exp(-t/tao)

    Args:
        t (vector): time
        y (vector): values
        zero_time_axix (boolean): whether to subtract t[0] from t. False by default
    """
    if zero_time_axis:
        t = t - t[0]  # zero time axis
    tau_i = t[-1] / 10  # guess at time constant
    # tau_i = t[-1]      #often can't solve with this guess. A smaller tau helps.
    y0_i = y[-1]  # guess at approach value
    y1_i = y[0]  # guess at true initial value
    pars_i = [tau_i, y0_i, y1_i]

    def exp_fun(x, tau, y0, y1):
        z = y0 + (y1 - y0) * np.exp(-x / tau)
        #        print([tau,y0,y1]) #for diagnosing curve_fit problems
        return z

    pars, pcov = curve_fit(exp_fun, t, y, p0=pars_i)
    #    pars = [tau, y0, y1]

    return pars
