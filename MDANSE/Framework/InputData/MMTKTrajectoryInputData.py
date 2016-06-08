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
Created on Mar 27, 2015

:author: Eric C. Pellegrini
'''

import numpy

from MDANSE.Framework.InputData.IInputData import InputDataError
from MDANSE.Framework.InputData.InputFileData import InputFileData
from MDANSE.MolecularDynamics.Trajectory import get_chemical_objects_size, get_chemical_objects_number, MMTKTrajectory

class MMTKTrajectoryInputData(InputFileData):
    
    type = "mmtk_trajectory"
    
    extension = "nc"
    
    def load(self):
        
        try:
            traj = MMTKTrajectory(None, self._name, "r")
            
        except IOError as e:        
            raise InputDataError(str(e))
        except ValueError as e:
            raise InputDataError(str(e))            
        
        self._data = traj
        
    def close(self):
        self._data.close()
        
    def info(self):
        
        val = []
        
        val.append("Path:")
        val.append("%s\n" % self._name)
        val.append("Number of steps:")
        val.append("%s\n" % len(self._data))
        val.append("Universe:")
        val.append("%s\n" % self._data.universe)
        
        if self._data.universe.is_periodic:
            val.append("Direct cell:")
            val.append("%s\n" % str(numpy.round(self._data.universe.basisVectors(),4)))

            val.append("Reciprocal cell:")
            val.append("%s\n" % str(numpy.round(self._data.universe.reciprocalBasisVectors(),4)))
            
        val.append("Molecular types found:")
        
        molSize = get_chemical_objects_size(self._data.universe)
        molNumber = get_chemical_objects_number(self._data.universe)
        
        for k,v in molSize.items():
            val.append('\t- %d molecule(s) of %s (%d atoms)' % (molNumber[k],k,v))
        val.append('\n')            
        val = "\n".join(val)
        
        return val

    @property
    def trajectory(self):
        
        return self._data
    
    @property
    def universe(self):
        return self._data.universe
    
    @property
    def netcdf(self):
        return self._data.trajectory.file
