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
import h5py

from MDANSE.Framework.Jobs.IJob import IJob


class InteractiveConverter(IJob, metaclass = ABCMeta):

    _converter_registry = {}
    _next_number = 1

    @classmethod
    def __init_subclass__(cls, regkey = None, **kwargs):
        super().__init_subclass__(**kwargs)
        if regkey is not None:
            cls._converter_registry[regkey] = cls
        else:
            raise ValueError("A regkey keyword parameter is needed in the subclass.")

    @classmethod
    def create(cls, name: str) -> 'InteractiveConverter':
        converter_class = cls._converter_registry[name]
        return converter_class
    
    @classmethod
    def converters(cls):
        return list(cls._converter_registry.keys())
    
    @abstractmethod
    def primaryInputs(self) -> dict:
        """Returns the list of inputs needed for the first page
        of the wizard. These should typically be the names of
        the input files passed to the converter.
        """
        raise NotImplementedError
    
    @abstractmethod
    def secondaryInputs(self) -> dict:
        """Returns the list of inputs needed for the second page
        of the wizard. These should typically be the parameters
        specifying how to read the trajectory: time step, number
        of frames, frame step, etc.
        """
        raise NotImplementedError
    
    @abstractmethod
    def finalInputs(self) -> dict:
        """Normally this should just give the user a chance
        to input the name of the (converted) output trajectory.
        It is done at the last step, since the user may want
        to base the name on the decisions they made for the
        input parameters.
        """
        raise NotImplementedError
    
    @abstractmethod
    def systemSummary(self) -> dict:
        """Returns all the information about the simulation
        that is currently stored by the converter. This will
        allow the users to verify if all the information was
        read correctly (or at all). This function must also
        place default values in the fields related to the
        parameters that could not be read.
        """
        raise NotImplementedError

    @abstractmethod
    def guessFromConfig(self, fname: str):
        """Tries to retrieve as much information as possible
        about the simulation to be converted from a config file.
        
        Arguments
        ---------

        fname (str) - name of the config file to be opened.
        """
        raise NotImplementedError

    @abstractmethod
    def guessFromTrajectory(self, fname: str):
        """Tries to retrieve as much information as possible
        about the simulation to be converted from a trajectory file.
        This will typically mean that the first frame of the trajectory
        will be read and parsed, while the rest of it will be ignored for now.

        Arguments
        ---------

        fname (str) - name of the trajectory file to be opened.
        """
        raise NotImplementedError

    @abstractmethod
    def run_step(self, index: int):
        """This function will be called iteratively in the conversion
        process, until all the requested trajectory frames have been
        converted.

        Arguments:
            index -- number of the next trajectory step to be processed
            by the converter
        """
        pass

    def finalize(self):
        """I am not sure if this function is necessary. The specific converters
        seem to override it with their own version.
        """

        if not hasattr(self,'_trajectory'):
            return

        try:
            output_file = h5py.File(self._trajectory.filename, 'a')
            # f = netCDF4.Dataset(self._trajectory.filename,'a')
        except:
            return
        
        try:
            if 'time' in output_file.variables:
                output_file.variables['time'].units = 'ps'
                output_file.variables['time'].axis = 'time'
                output_file.variables['time'].name = 'time'

            if 'box_size' in output_file.variables:
                output_file.variables['box_size'].units = 'ps'
                output_file.variables['box_size'].axis = 'time'
                output_file.variables['box_size'].name = 'box_size'

            if 'configuration' in output_file.variables:
                output_file.variables['configuration'].units = 'nm'
                output_file.variables['configuration'].axis = 'time'
                output_file.variables['configuration'].name = 'configuration'

            if 'velocities' in output_file.variables:
                output_file.variables['velocities'].units = 'nm/ps'
                output_file.variables['velocities'].axis = 'time'
                output_file.variables['velocities'].name = 'velocities'

            if 'gradients' in output_file.variables:
                output_file.variables['gradients'].units = 'amu*nm/ps'
                output_file.variables['gradients'].axis = 'time'
                output_file.variables['gradients'].name = 'gradients'
        finally:
            output_file.close()





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

