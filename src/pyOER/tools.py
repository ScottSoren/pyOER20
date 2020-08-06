"""This module defines some pythony and mathy stuff used elsewhere"""
import numpy as np
from scipy.optimize import curve_fit


PROJECT_START_TIMESTAMP = 1533502800  # August 25, 2018


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


class ObjWithJsonData:
    """Not implemented, but will be a base class for the common structure I use:

    A class with:
        - an as_dict() method which returns a JSON-serializable representation of itself
        - a save() method which saves the as_dict() representation as JSON in a
            default or specified directory, with a generated or specified file name.
        - a load() class method which loads the JSON and feeds it with "**" to __init__
        - an __init__() which is called by load() with the as_dict() representation as
            keyword arguments and does the necessary processing
        - additional methods and (non-serializable) attributes of arbitrary complexity

    see: pyOER.Measurement, pyOER.ElogEntry, pyOER.Calibration, etc...

    Normally this class structure requires a lot of boiler-plate, with the same flat
        list of arguments, plus minimal processing, written three places: the arguments
        in the definition of __init__ (i.e., x=None), in __init__ (i.e., self.x=x), and
        in as_dict (i.e., self_as_dict["x"] = self.x)

    There must be a base-class way to fix this, so the argument list only needs be
        typed once, but it evades me now.
    """

    as_dict_attrs = []
    not_as_dict_attrs = []

    def __init__(self, **kwargs):
        pass


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
