# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Core/Singleton.py
# @brief     Implements module/class/test Singleton
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************


class Singleton(type):
    """
    Metaclass that implements the singleton pattern.
    """

    __instances = {}

    def __call__(self, *args, **kwargs):
        """
        Creates (or returns if it has already been instanciated) an instance of the class.
        """

        if self.__name__ not in self.__instances:
            self.__instances[self.__name__] = super(Singleton, self).__call__(
                *args, **kwargs
            )

        return self.__instances[self.__name__]
