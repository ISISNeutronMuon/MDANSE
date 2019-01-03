# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Tests/FunctionalTests/Jobs/Comparator.py
# @brief     Implements module/class/test Comparator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
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

    def compare(self, res1, res2):
        description1 = res1.pop("description", None)
        description2 = res2.pop("description", None)
        
        ret = self.__compareDictionnaries(res1, res2)
        if not (description1 is None) or not (description2 is None):
            ret = ret and self.__compareDescriptions(description1, description2)
        return ret

    def __compareDescriptions(self, descr1, descr2):
        temp = collections.Counter(descr1)
        return temp == collections.Counter(descr2)
    
    def __compareDictionnaries(self, res1, res2):
        ret = True
        # Dictionnary Testing
        if isinstance(res1, dict) and isinstance(res2, dict):
            # Dictionnary case
            if len(res1) == len(res2):
                for key in res1.keys():
                    if key in res2.keys():       
                        ret = ret and self.__compareDictionnaries(res1[key], res2[key])
                    else:
                        ret = False
            else:
                ret = False
        else:
            # Can be anything, probe array case first
            if hasattr(res1, "__len__") and hasattr(res2, "__len__") and (not isinstance(res1, str)) and (not isinstance(res2, str)) and (not isinstance(res1, unicode)) and (not isinstance(res2, unicode)):
                # Array case:
                try:
                    ret = ret and numpy.allclose(res1,res2)
                except TypeError:
                    # Python list case    
                    if len(res1) == len(res2):
                        for index in range(len(res1)):
                            ret = ret and self.__compareDictionnaries(res1[index], res2[index])
                    else:
                        ret = False
            else:
                # Single Values case
                ret = ret and (res1==res2)
        return ret