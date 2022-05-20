import abc
import sys

def compatibleabstractproperty(func):

    if sys.version_info > (3, 3):             
        return property(abc.abstractmethod(func))
    else:
        return abc.abstractproperty(func)