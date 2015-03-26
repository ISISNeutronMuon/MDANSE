'''
MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
------------------------------------------------------------------------------------------
Copyright (C)
2015- Eric C. Pellegrini Institut Laue-Langevin
BP 156
6, rue Jules Horowitz
38042 Grenoble Cedex 9
France
pellegrini[at]ill.fr

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 
Created on Mar 23, 2015

@author: pellegrini
'''

import abc
import os
import collections

import numpy

from Scientific.IO.NetCDF import NetCDFFile

from MDANSE.Core.ClassRegistry import ClassRegistry
from MDANSE.Core.Error import Error
from nMOLDYN.Utilities.MolecularDynamics import get_chemical_objects_number, get_chemical_objects_size, MMTKTrajectory

class InputDataError(Error):
    pass

class InputData(object):
    
    __metaclass__ = ClassRegistry

    def __init__(self, *args, **kwargs):
        self._data = None
        
        self._filename = None

    @property
    def filename(self):
        return self._filename
        
    @property
    def basename(self):
        return self._basename    

    @property
    def data(self):
        return self._data

    def info(self):

        return "No information available"
            
class EmptyData(InputData):

    type = "empty_data"

    extension = None
    
    count = 0
    
    def __init__(self, filename, *args, **kwargs):

        InputData.__init__(self, filename, *args, **kwargs)
        
        self._data = None

        if filename is None:
            self._filename = self._basename = 'empty_' + str(EmptyData.count)
            EmptyData.count +=  1
        else:
            self._filename = self._basename = filename
            

class InputFileData(InputData):
    
    def __init__(self, filename, *args, **kwargs):
        
        super(InputFileData, self).__init__()
        
        self._filename = filename
        self._dirname = os.path.dirname(self._filename)
        self._basename = os.path.basename(self._filename)
        self._data = None
    
        self.load()

    @property
    def dirname(self):
        return self._dirname    

    @abc.abstractmethod
    def load(self):
        pass   

    @abc.abstractmethod
    def close(self):
        pass    

class MMTKTrajectoryInputData(InputFileData):
    
    type = "mmtk_trajectory"
    
    extension = "nc"
    
    def load(self):
        
        try:
            traj = MMTKTrajectory(None, self._filename, "r")
            
        except IOError:        
            raise InputDataError("The MMTK trajectory %r could not be loaded property." % self._filename)
        
        self._data = traj

    def close(self):
        self._data.close()
        
    def info(self):
        
        val = []
        
        val.append("Path:")
        val.append("%s\n" % self._filename)
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
    
class NetCDFInputData(InputFileData):
    
    type = "netcdf_data"
    
    extension = "nc"
    
    def load(self):
        
        try:
            self._netcdf = NetCDFFile(self._filename,"r")
            
        except IOError:
            raise InputDataError("The data stored in %r filename could not be loaded property." % self._filename)

        else:
            self._data = collections.OrderedDict()
            variables = self._netcdf.variables
            for k in variables:
                self._data[k]={}
                try :
                    if vars[k].axis:
                        self._data[k]['axis'] =  variables[k].axis.split('|')
                    else:
                        self._data[k]['axis'] = []
                except:
                    self._data[k]['axis'] = []
                self._data[k]['data'] = variables[k].getValue()
                self._data[k]['units'] = getattr(variables[k], 'units', 'au')

    def close(self):
        self._netcdf.close()
        
    @property
    def netcdf(self):
        
        return self._netcdf
    
class MviTraceInputData(InputFileData):
    
    type = "mvi_trace"
    
    extension = "mvi"
    
    def load(self):
        pass
        
    def close(self):
        pass   
        

class PeriodicTableData(InputData):
    
    type = "periodic_table"
    
    extension = None
    
    def load(self):
        pass
    
    def close(self):
        pass