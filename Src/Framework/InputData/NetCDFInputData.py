import collections

from Scientific.IO.NetCDF import NetCDFFile

from MDANSE import REGISTRY
from MDANSE.Framework.InputData.IInputData import InputDataError
from MDANSE.Framework.InputData.InputFileData import InputFileData

class NetCDFInputData(InputFileData):
        
    extension = "nc"
    
    def load(self):
        
        try:
            self._netcdf = NetCDFFile(self._name,"r")
            
        except IOError:
            raise InputDataError("The data stored in %r filename could not be loaded properly." % self._name)

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

REGISTRY["netcdf_data"] = NetCDFInputData
