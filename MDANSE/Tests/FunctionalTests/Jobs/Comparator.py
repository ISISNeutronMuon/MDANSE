# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Tests/FunctionalTests/Jobs/Comparator.py
# @brief     Implements module/class/test Comparator
#
# @homepage https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import numpy
import collections

class Comparator():
    def __init__(self):
        self.s1 = ""
        self.s2 = ""
        pass

    def compare(self, res1, res2, array_tolerance=(1e-05, 1e-08)):
        """

        :param res1: dictionary to compare
        :type res1: dict

        :param res2: dictionary to compare
        :type res2: dict

        :param array_tolerance: relative and absolute tolerance for the numpy.allclose() function; allows for the
                                tweaking of how close the elementwise values have to be considered equal. The default
                                values are equal to the defaults of the numpy.allclose() function. The first value in
                                the tuple corresponds to rtol, and the second to atol.
        :type array_tolerance: tuple

        :return: The truth evaluation of if the passed dicts are equal.
        :rtype: bool
        """
        description1 = res1.pop("description", None)
        description2 = res2.pop("description", None)
        
        ret = self.__compareDictionnaries(res1, res2, array_tolerance)
        if not (description1 is None) or not (description2 is None):
            ret = ret and self.__compareDescriptions(description1, description2)
        return ret

    def __compareDescriptions(self, descr1, descr2):
        temp = collections.Counter(descr1)
        return temp == collections.Counter(descr2)
    
    def __compareDictionnaries(self, res1, res2, array_tolerance=(1e-05, 1e-08)):
        ret = True
        # Dictionnary Testing
        if isinstance(res1, dict) and isinstance(res2, dict):
            # Dictionnary case
            if len(res1) == len(res2):
                for key in res1.keys():
                    if key in res2.keys():       
                        ret = ret and self.__compareDictionnaries(res1[key], res2[key], array_tolerance)
                    else:
                        ret = False
            else:
                ret = False
        else:
            # Can be anything, probe array case first
            if hasattr(res1, "__len__") and hasattr(res2, "__len__") and (not isinstance(res1, str)) and (not isinstance(res2, str)) and (not isinstance(res1, unicode)) and (not isinstance(res2, unicode)):
                # Array case:
                try:
                    ret = ret and numpy.allclose(res1, res2, array_tolerance[0], array_tolerance[1])
                except TypeError:
                    # Python list case    
                    if len(res1) == len(res2):
                        for index in range(len(res1)):
                            ret = ret and self.__compareDictionnaries(res1[index], res2[index], array_tolerance)
                    else:
                        ret = False
            else:
                # Single Values case
                ret = ret and (res1==res2)
        return ret