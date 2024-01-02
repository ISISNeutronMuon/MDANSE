# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Core/SubclassFactory.py
# @brief     Metaclass creating classes with subclass registry
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   RSE Group at ISIS (see AUTHORS)
#
# **************************************************************************

from typing import TypeVar


Self = TypeVar("Self", bound="SubclassFactory")

def single_search(parent_class: type, name: str):
    if name in parent_class._registered_subclasses.keys():
        return parent_class._registered_subclasses[name]
    else:
        return None
    
def recursive_search(parent_class: type, name: str):
    return_type = single_search(parent_class, name)
    if return_type is not None:
        return return_type
    else:
        for child in parent_class._registered_subclasses.keys():
            return_type = recursive_search(parent_class._registered_subclasses[child], name)
            if return_type is not None:
                return return_type


class SubclassFactory(type):
    """A metaclass which gives a class the ability to keep track of
    its subclasses, and to work as a factory.
    """

    def __init__(cls, name, base, dct, **kwargs):
        super().__init__(name, base, dct)
        # Add the registry attribute to the each new child class.
        # It is not needed in the terminal children though.
        cls._registered_subclasses = {}

        @classmethod
        def __init_subclass__(cls, **kwargs):
            regkey = cls.__name__
            super().__init_subclass__(**kwargs)
            cls._registered_subclasses[regkey] = cls

        # Assign the nested classmethod to the "__init_subclass__" attribute
        # of each child class.
        # It isn't needed in the terminal children too.
        # May be there is a way to avoid adding these needless attributes
        # (registry, __init_subclass__) to there. I don't think about it yet.
        cls.__init_subclass__ = __init_subclass__

    def create(cls, name: str, *args, **kwargs) -> Self:
        try:
            specific_class = cls._registered_subclasses[name]
        except KeyError:
            specific_class = recursive_search(cls, name)
        return specific_class(*args, **kwargs)

    def subclasses(cls):
        return list(cls._registered_subclasses.keys())
