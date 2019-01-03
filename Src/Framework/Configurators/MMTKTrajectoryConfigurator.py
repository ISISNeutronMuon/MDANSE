# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/MMTKTrajectoryConfigurator.py
# @brief     Implements module/class/test MMTKTrajectoryConfigurator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

from MDANSE import PLATFORM, REGISTRY

from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator

class MMTKNetCDFTrajectoryConfigurator(InputFileConfigurator):
    '''
    This configurator allow to input a MMTK trajectory file.
    
    MMTK trajectory file is the format used in MDANSE to store Molecular Dynamics trajectories. It is a NetCDF file 
    that store various data related to the molecular dynamics : atomic positions, velocities, energies, energy gradients etc...
    
    To use trajectories derived from MD packages different from MMTK, it is compulsory to convert them before to a MMTK trajectory file.
    
    :attention: once configured, the MMTK trajectory file will be opened for reading.    
    '''
        
    _default = os.path.join('..','..','..','Data','Trajectories','MMTK','waterbox_in_periodic_universe.nc')
                        
    def configure(self, value):
        '''
        Configure a MMTK trajectory file. 
                
        :param value: the path for the MMTK trajectory file.
        :type value: str 
        '''
                
        InputFileConfigurator.configure(self, value)
        
        inputTraj = REGISTRY["input_data"]["mmtk_trajectory"](self['value'])
        
        self['instance'] = inputTraj.trajectory
                
        self["filename"] = PLATFORM.get_path(inputTraj.filename)

        self["basename"] = os.path.basename(self["filename"])

        self['length'] = len(self['instance'])

        try:
            self['md_time_step'] = self['instance'].time[1] - self['instance'].time[0]
        except IndexError:
            self['md_time_step'] = 1.0
            
        self["universe"] = inputTraj.universe
                        
        self['has_velocities'] = 'velocities' in self['instance'].variables()
                
    def get_information(self):
        '''
        Returns some basic informations about the contents of the MMTK trajectory file.
        
        :return: the informations about the contents of the MMTK trajectory file.
        :rtype: str
        '''
                
        info = ["MMTK input trajectory: %r\n" % self["filename"]]
        info.append("Number of steps: %d\n" % self["length"])
        info.append("Size of the universe: %d\n" % self["universe"].numberOfAtoms())
        if (self['has_velocities']):
            info.append("The trajectory contains atomic velocities\n")
        
        return "".join(info)
    
REGISTRY['mmtk_trajectory'] = MMTKNetCDFTrajectoryConfigurator
