"""This module defines some pythony stuff used elsewhere"""


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


class ObjWithJsonData:
    """Not implemented, but will be a base class for the common structure I use:

    A class with:
        an as_dict() method which returns a JSON-serializable representation of itself
        a save() method which saves the as_dict() representation as JSON in a
            default or specified directory
        a load() class_method which loads the JSON and feeds it with "**" to __init__
        an __init__() which is called by load() with the as_dict() representation as
            keyword arguments and does the necessary processing

    see: pyOER.Measurement, pyOER.ElogEntry, pyOER.Calibration, etc...

    Normally this class structure requires a lot of boiler-plate, with the same flat
        list of arguments, plus minimal processing, written three places: the arguments
        in the definition of __init__ (i.e., x=None), in __init__ (i.e., self.x=x), and
        in as_dict (i.e., self_as_dict["x"] = x)

    There must be a base-class way to fix this, so the argument list only needs be
        typed once, but it evades me now.
    """

    as_dict_attrs = []
    not_as_dict_attrs = []

    def __init__(self, **kwargs):
        pass
