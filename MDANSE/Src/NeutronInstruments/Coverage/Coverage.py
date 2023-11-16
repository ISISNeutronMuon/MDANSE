# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/NeutronInstruments/Coverage/Coverage.py
# @brief     Base class for neutron instrument coverage
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   RSE Group at ISIS (see AUTHORS)
#
# **************************************************************************


class Coverage:
    _registered_subclasses = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        regkey = cls.__name__
        cls._registered_subclasses[regkey] = cls

    @classmethod
    def create(cls, name: str, *args, **kwargs) -> "Coverage":
        specific_class = cls._registered_subclasses[name]
        return specific_class(*args, **kwargs)

    @classmethod
    def subclasses(cls):
        return list(cls._registered_subclasses.keys())
