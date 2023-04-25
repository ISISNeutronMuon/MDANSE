# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/InputData/MMTKTrajectoryInputData.py
# @brief     Implements module/class/test MMTKTrajectoryInputData
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import numpy

from MDANSE import REGISTRY
from MDANSE.Framework.InputData.IInputData import InputDataError
from MDANSE.Framework.InputData.InputFileData import InputFileData
from MDANSE.MolecularDynamics.Trajectory import get_chemical_objects_size, get_chemical_objects_number, MMTKTrajectory

class MMTKTrajectoryInputData(InputFileData):
        
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

        val.append("\nVariables found in trajectory:")
        variables = self._data.variables()
        for v in variables:
            try:
                shape = getattr(self._data,v).var.shape
            except AttributeError:
                shape = getattr(self._data,v).shape
            val.append('\t- %s: %s' % (v,shape))

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

REGISTRY["mmtk_trajectory"] = MMTKTrajectoryInputData    
