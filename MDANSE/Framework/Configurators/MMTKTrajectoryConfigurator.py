#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on Mar 30, 2015

@author: Eric C. Pellegrini
'''

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
    
    type = 'mmtk_trajectory'
    
    _default = 'waterbox_in_periodic_universe.nc'
                        
    def configure(self, configuration, value):
        '''
        Configure a MMTK trajectory file. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the path for the MMTK trajectory file.
        :type value: str 
        '''
                
        InputFileConfigurator.configure(self, configuration, value)
        
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