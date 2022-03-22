# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/InputData/IInputData.py
# @brief     Implements module/class/test IInputData
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE.Core.Error import Error

class InputDataError(Error):
    '''
    This class handles exception related to ``IInputData`` interface.
    '''

class IInputData(object):
    '''
    This is the base class for handling MDANSE input data.    
    '''
        
    _registry = "input_data"

    def __init__(self,name, *args):
        '''
        Builds an ``IInputData`` object.
        '''

        self._name = name
        
        self._data = None

    @property
    def name(self):
        '''
        Returns the name associated with the input data.
        
        :return: the name associated with the input data.
        :rtype: str
        '''
        
        return self._name
    
    @property
    def shortname(self):
        
        return self._name
            
    @property
    def data(self):
        '''
        Return the input data.
        
        :return: the input data.
        :rtype: depends on the concrete ``IInputData`` subclass
        '''
        
        return self._data

    def info(self):
        '''
        Returns information as a string about the input data.
        
        :return:
        :rtype: str
        '''

        return "No information available"
