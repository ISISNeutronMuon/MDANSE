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


class SubclassFactory(type):
    """A metaclass which gives a class the ability to keep track of
    its subclasses, and to work as a factory.
    """

    def __init__(cls, *args, **kwargs):
        super().__init__(cls, *args, **kwargs)
        registry = {}
        setattr(cls, "_registered_subclasses", registry)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        regkey = cls.__name__
        cls._registered_subclasses[regkey] = cls

    def create(cls, name: str, *args, **kwargs):
        specific_class = cls._registered_subclasses[name]
        return specific_class(*args, **kwargs)

    def subclasses(cls):
        return list(cls._registered_subclasses.keys())
