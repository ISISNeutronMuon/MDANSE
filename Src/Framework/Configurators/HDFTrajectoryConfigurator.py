# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/HDFTrajectoryConfigurator.py
# @brief     Implements module/class/test HDFTrajectoryConfigurator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

from MDANSE import PLATFORM, REGISTRY

from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator

class HDFTrajectoryConfigurator(InputFileConfigurator):
    '''
    This configurator allow to input a HDF trajectory file.
    
    HDF trajectory file is the format used in MDANSE to store Molecular Dynamics trajectories. It is a NetCDF file 
    that store various data related to the molecular dynamics : atomic positions, velocities, energies, energy gradients etc...
    
    To use trajectories derived from MD packages different from HDF, it is compulsory to convert them before to a 
    HDF trajectory file.
    
    :attention: once configured, the HDF trajectory file will be opened for reading.    
    '''
        
    _default = os.path.join('..','..','..','Data','Trajectories','HDF','waterbox.h5')
                        
    def configure(self, value):
        '''
        Configure a HDF trajectory file. 
                
        :param value: the path for the HDF trajectory file.
        :type value: str 
        '''
                
        InputFileConfigurator.configure(self, value)
        
        inputTraj = REGISTRY["input_data"]["hdf_trajectory"](self['value'])
        
        self['instance'] = inputTraj.trajectory
                
        self["filename"] = PLATFORM.get_path(inputTraj.filename)

        self["basename"] = os.path.basename(self["filename"])

        self['length'] = len(self['instance'])

        try:
            self['md_time_step'] = self['instance'].file['/time'][1] - self['instance'].file['/time'][0]
        except IndexError:
            self['md_time_step'] = 1.0
            
        self["chemical_system"] = inputTraj.chemical_system

        self['has_velocities'] = 'velocities' in self['instance'].file['/configuration']
                
    def get_information(self):
        '''
        Returns some basic informations about the contents of the HDF trajectory file.
        
        :return: the informations about the contents of the HDF trajectory file.
        :rtype: str
        '''
                
        info = ["HDF input trajectory: %r\n" % self["filename"]]
        info.append("Number of steps: %d\n" % self["length"])
        info.append("Size of the chemical system: %d\n" % self["chemical_system"].number_of_atoms())
        if (self['has_velocities']):
            info.append("The trajectory contains atomic velocities\n")
        else:
            info.append("The trajectory does not contain atomic velocities\n")
        
        return "".join(info)
    
REGISTRY['hdf_trajectory'] = HDFTrajectoryConfigurator
