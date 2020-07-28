"""This module implements some things used elsewhere"""


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
