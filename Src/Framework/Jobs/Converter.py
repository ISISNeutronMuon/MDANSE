# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Jobs/Converter.py
# @brief     Implements module/class/test Converter
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from abc import ABCMeta, abstractmethod, abstractclassmethod

import netCDF4

from MDANSE.Framework.Jobs.IJob import IJob


class InteractiveConverter(IJob, metaclass = ABCMeta):

    _converter_registry = {}
    _next_number = 1

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        newkey = getattr('label', None)
        if newkey is not None:
            cls._converter_registry[newkey] = cls

    @classmethod
    def __getitem__(cls, name):
        converter_class = cls._converter_registry[name]
        return converter_class
    
    @classmethod
    def converters(cls):
        return list(cls._converter_registry.keys())

    @abstractmethod
    def createInputs(self):
        raise NotImplementedError
    
    @abstractmethod
    def parseConfigFile(self):
        raise NotImplementedError
    
    @abstractmethod
    def takeCorrectedValues(self):
        raise NotImplementedError
    
    @abstractmethod
    def readTrajectoryFile(self):
        raise NotImplementedError
    
    @abstractmethod
    def readAFrame(self):
        raise NotImplementedError
    
    @abstractmethod
    def createOutput(self):
        raise NotImplementedError
    
    @abstractmethod
    def finalise(self):
        raise NotImplementedError
    
    




class Converter(IJob,metaclass=ABCMeta):
    
    category = ('Converters',)
    
    ancestor = ['empty_data']

    @abstractmethod
    def run_step(self,index):
        pass

    def finalize(self):

        if not hasattr(self,'_trajectory'):
            return

        try:
            f = netCDF4.Dataset(self._trajectory.filename,'a')
        except:
            return
        
        try:
            if 'time' in f.variables:
                f.variables['time'].units = 'ps'
                f.variables['time'].axis = 'time'
                f.variables['time'].name = 'time'

            if 'box_size' in f.variables:
                f.variables['box_size'].units = 'ps'
                f.variables['box_size'].axis = 'time'
                f.variables['box_size'].name = 'box_size'

            if 'configuration' in f.variables:
                f.variables['configuration'].units = 'nm'
                f.variables['configuration'].axis = 'time'
                f.variables['configuration'].name = 'configuration'

            if 'velocities' in f.variables:
                f.variables['velocities'].units = 'nm/ps'
                f.variables['velocities'].axis = 'time'
                f.variables['velocities'].name = 'velocities'

            if 'gradients' in f.variables:
                f.variables['gradients'].units = 'amu*nm/ps'
                f.variables['gradients'].axis = 'time'
                f.variables['gradients'].name = 'gradients'
        finally:
            f.close()

