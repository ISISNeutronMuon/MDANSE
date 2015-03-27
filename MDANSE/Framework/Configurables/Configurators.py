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
import ast
import collections
import operator
import os
import re
import subprocess
import time

import numpy

from Scientific.IO.NetCDF import NetCDFFile
from Scientific.Geometry import Vector

from MDANSE import ELEMENTS, PLATFORM, REGISTRY, USER_DEFINITIONS
from MDANSE.Core.Error import Error
from MDANSE.Framework.Selectors import SelectionParser
from MDANSE.Mathematics.Arithmetic import ComplexNumber
from MDANSE.Mathematics.Signal import INTERPOLATION_ORDER
from MDANSE.MolecularDynamics.Trajectory import find_atoms_in_molecule

LEVELS = collections.OrderedDict()
LEVELS["atom"]     = {"atom" : 0, "atomcluster" : 0, "molecule" : 0, "nucleotidechain" : 0, "peptidechain" : 0, "protein" : 0}
LEVELS["group"]    = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 1, "peptidechain" : 1, "protein" : 1}
LEVELS["residue"]  = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 2, "peptidechain" : 2, "protein" : 2}
LEVELS["chain"]    = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 3, "peptidechain" : 3, "protein" : 3}
LEVELS["molecule"] = {"atom" : 0, "atomcluster" : 1, "molecule" : 1, "nucleotidechain" : 3, "peptidechain" : 3, "protein" : 4}

class ConfiguratorError(Error):
    
    def __init__(self, message, configurator=None):

        self._message = message
        self._configurator = configurator
                
    def __str__(self):
        
        if self._configurator is not None:
            self._message = "Configurator: %r --> %s" % (self._configurator.name,self._message)
        
        return self._message
    
    @property
    def configurator(self):
        return self._configurator

class ConfiguratorsDict(collections.OrderedDict):
    
    def add_item(self, name, typ, *args, **kwargs):
                
        try:
            self[name] = REGISTRY["configurator"][typ](name, *args, **kwargs)
        except KeyError:
            raise ConfiguratorError("invalid type for %r configurator" % name)
                                                
    def build_doc(self):
        
        if not self:
            return ""
                    
        docdict = collections.OrderedDict()
        
        for i, (k,v) in enumerate(self.items()):
            docdict[i] = {'Parameter' : str(k), 
                          'Default' : str(v.default),
                          'Description' : str(v.__doc__)
                          }
            
        l = ['Parameters','Default','Description']
        
        sizes = []  
        sizes.append([len(l[0])]) 
        sizes.append([len(l[1])]) 
        sizes.append([len(l[2])]) 
        
        for k, v in docdict.items():
            sizes[0].append(len(v['Parameter']))
            sizes[1].append(len(v['Default']))
            
            v['Description'] = v['Description'].replace('\n',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ')
            sizes[2].append(len(v['Description']))
            
        maxSizes = [max(s) for s in sizes]
            
        s = (maxSizes[0]+2, maxSizes[1]+2, maxSizes[2]+2)
                
        table = '\n**Job input parameters:** \n\n'
        
        table += '+%s+%s+%s+\n'%(s[0]*'-',s[1]*'-',s[2]*'-')
        
        table += '| %s%s | %s%s | %s%s |\n' %(l[0], (s[0]-len(l[0])-2)*' ', l[1],(s[1]-len(l[1])-2)*' ', l[2],(s[2]-len(l[2])-2)*' ')            
        
        table += '+%s+%s+%s+\n'%(s[0]*'=',s[1]*'=',s[2]*'=') 
        
        for k,v in docdict.items():
            p = v['Parameter']
            df = v['Default']
            ds = v['Description']
            table += '| %s%s | %s%s | %s%s |\n'%(p,(s[0]-len(p)-2)*' ', df,(s[1]-len(df)-2)*' ', ds,(s[2]-len(ds)-2)*' ')
            table += '+%s+%s+%s+\n'%(s[0]*'-',s[1]*'-',s[2]*'-')
    
        return table
    
    def get_default_parameters(self):
        
        params = collections.OrderedDict()
        for k,v in self.items():
            params[k] = v.default
            
        return params
        
                                                
class Configurator(dict):
    
    __metaclass__ = REGISTRY
    
    _default = None
    
    _doc_ = "undocumented"
    
    type = "configurator"
                        
    def __init__(self, name, dependencies=None, default=None, label=None, widget=None):

        self._name = name
        
        self._dependencies = dependencies if dependencies is not None else {}

        self._default = default if default is not None else self.__class__._default

        self._label = label if label is not None else " ".join(name.split('_')).strip()

        self._widget = widget if widget is not None else self.type
            
    @property
    def default(self):
        
        return self._default
    
    @property
    def dependencies(self):
        
        return self._dependencies
        
    @property
    def label(self):
        
        return self._label

    @property
    def name(self):
        
        return self._name

    @property
    def widget(self):
        
        return self._widget
    
    @abc.abstractmethod
    def configure(self, configuration, value):
        pass
                        
    def add_dependency(self, name, conf):
        
        if self._dependencies.has_key(name):
            raise ConfiguratorError("duplicate dependendy for configurator %s" % name, self)
                        
    def check_dependencies(self, configured):
        
        for c in self._dependencies.values():
            if c not in configured:
                return False

        return True
    
    @abc.abstractmethod
    def get_information(self):
        pass
    
class InputDirectoryConfigurator(Configurator):
    """
     This Configurator allows to set as input an (existing) directory.
    """
    
    type = "input_directory"
    
    _default = os.getcwd()

    def configure(self, configuration, value):
        
        value = PLATFORM.get_path(value)
        
        if not os.path.exists(value):
            raise ConfiguratorError('invalid type for input value', self)
                                        
        self['value'] = value        

    def get_information(self):
        
        return "Input directory: %r" % self['value']
        
class OutputDirectoryConfigurator(Configurator):
    """
     This Configurator allows to set an output directory.
    """
    
    type = "output_directory"
    
    _default = os.getcwd()

    def __init__(self, name, new=False, **kwargs):
                
        Configurator.__init__(self, name, **kwargs)
        
        self._new = new

    def configure(self, configuration, value):
        
        value = PLATFORM.get_path(value)
        
        if self._new:
            if os.path.exists(value):
                raise ConfiguratorError("the output directory must not exist", self)
                                                
        self['value'] = value        
        
    @property
    def new(self):
        
        return self._new
    
    def get_information(self):
        
        return "Output directory: %r" % self['value']
        
class PythonObjectConfigurator(Configurator):
    """
    This Configurator allows to input any kind of basic python object.
    """
    
    type = 'python_object'
    
    _default = '""'

    def configure(self, configuration, value):
        
        value = ast.literal_eval(repr(value))
                                
        self['value'] = value

    def get_information(self):
        
        return "Python object: %r" % self['value']
 
class StringConfigurator(Configurator):
    """
    This Configurator allows to input a String Value (sequence of unicode char).
    """
    
    type = 'string'
    
    _default = ""

    def __init__(self, name, evalType=None, acceptNullString=True, **kwargs):
        
        Configurator.__init__(self, name, **kwargs)
        
        self._evalType = evalType
        
        self._acceptNullString = acceptNullString
    
    def configure(self, configuration, value):

        value = str(value)
        
        if not self._acceptNullString:
            if not value:
                raise ConfiguratorError("invalid null string", self)
            
        if self._evalType is not None:
            value = ast.literal_eval(value)
            if not isinstance(value,self._evalType):
                raise ConfiguratorError("the string can not be eval to %r type" % self._evalType.__name__, self)
                        
        self['value'] = value
        
    @property
    def acceptNullString(self):
        
        return self._acceptNullString
    
    @property
    def evalType(self):
        
        return self._evalType
    
    def get_information(self):
        
        return "Value: %r" % self['value']
    
class BooleanConfigurator(Configurator):
    """
    This Configurator allows to input a Boolean Value (True or False).
    """

    type = 'boolean'
    
    _default = False
    
    _shortCuts = {"true" : True, "yes" : True, "y" : True, "t" : True, "1" : True,
                  "false" : False, "no" : False, "n" : False, "f" : False, "0" : False}
    
    def configure(self, configuration, value):

        if hasattr(value,"lower"):
            
            value = value.lower()

            if not self._shortCuts.has_key(value):
                raise ConfiguratorError('invalid boolean string', self)
                        
        value = bool(value)
                        
        self['value'] = value

    def get_information(self):
        
        return "Value: %r" % self['value']

class SingleChoiceConfigurator(Configurator):
    """
     This Configurator allows to select a single item among multiple choices.
    """
    
    type = "single_choice"
    
    _default = []
            
    def __init__(self, name, choices=None, **kwargs):
        
        Configurator.__init__(self, name, **kwargs)
        
        self._choices = choices if choices is not None else []

    def configure(self, configuration, value):

        try:
            self["index"] = self._choices.index(value)
        except ValueError:                        
            raise ConfiguratorError("%r item is not a valid choice" % value, self)
        else:        
            self["value"] = value
            
    @property
    def choices(self):
        
        return self._choices

    def get_information(self):
        
        return "Selected item: %r" % self['value']

class MultipleChoicesConfigurator(Configurator):
    """
     This Configurator allows to select several items among multiple choices.
    """
    
    type = "multiple_choices"
    
    _default = []
            
    def __init__(self, name, choices=None, nChoices=None, **kwargs):
        
        Configurator.__init__(self, name, **kwargs)
        
        self._choices = choices if choices is not None else []
        
        self._nChoices = nChoices

    def configure(self, configuration, value):

        if self._nChoices is not None:
            if len(value) != self._nChoices:
                raise ConfiguratorError("invalid number of choices.", self)

        indexes = []
        for v in value:
            try:
                indexes.append(self._choices.index(v))
            except ValueError:                        
                raise ConfiguratorError("%r item is not a valid choice" % v, self)
            
        self["indexes"] = indexes
        self["choices"] = [self._choices[i] for i in indexes]
        self["value"] = self["choices"]
            
    @property
    def choices(self):
        
        return self._choices
    
    @property
    def nChoices(self):
        
        return self._nChoices

    def get_information(self):
        
        return "Selected items: %r" % self['choices']

class ComplexConfigurator(Configurator):
    """
    This Configurator allows to input a Complex Value a + bi, 
    where a and b are real numbers and i is the imaginary unit.
    """
    
    type = 'complex'
    
    _default = 0
    
    def __init__(self, name, mini=None, maxi=None, choices=None, **kwargs):

        # The base class constructor.
        Configurator.__init__(self, name, **kwargs)
        
        self._mini = ComplexNumber(mini) if mini is not None else None

        self._maxi = ComplexNumber(maxi) if maxi is not None else None
        
        self._choices = choices if choices is not None else []
                    
    def configure(self, configuration, value):
        
        value = ComplexNumber(value)
            
        if self._choices:
            if not value in self._choices:
                raise ConfiguratorError('the input value is not a valid choice.', self)
                        
        if self._mini is not None:
            if value.modulus() < self._mini.modulus():
                raise ConfiguratorError("the input value is lower than %r." % self._mini, self)

        if self._maxi is not None:
            if value.modulus() > self._maxi.modulus():
                raise ConfiguratorError("the input value is higher than %r." % self._maxi, self)

        self['value'] = value
        
    @property
    def mini(self):
        
        return self._mini

    @property
    def maxi(self):
        
        return self._maxi

    @property
    def choices(self):
        
        return self._choices

    def get_information(self):
        
        return "Value: %r" % self['value']

class FloatConfigurator(Configurator):
    """
    This Configurator allows to input a Floating point Value.
    """
    
    type = 'float'
    
    _default = 0
    
    def __init__(self, name, mini=None, maxi=None, choices=None, **kwargs):

        # The base class constructor.
        Configurator.__init__(self, name, **kwargs)
        
        self._mini = float(mini) if mini is not None else None

        self._maxi = float(maxi) if maxi is not None else None
        
        self._choices = choices if choices is not None else []

    def configure(self, configuration, value):
                        
        try:
            value = float(value)
        except (TypeError,ValueError) as e:
            raise ConfiguratorError(e)
            
        if self._choices:
            if not value in self._choices:
                raise ConfiguratorError('the input value is not a valid choice.', self)
                        
        if self._mini is not None:
            if value < self._mini:
                raise ConfiguratorError("the input value is lower than %r." % self._mini, self)

        if self._maxi is not None:
            if value > self._maxi:
                raise ConfiguratorError("the input value is higher than %r." % self._maxi, self)

        self['value'] = value

    @property
    def mini(self):
        
        return self._mini

    @property
    def maxi(self):
        
        return self._maxi

    @property
    def choices(self):
        
        return self._choices

    def get_information(self):
        
        return "Value: %r" % self['value']

class QVectorsConfigurator(Configurator):
    """
    This Configurator allows to set reciprocal vectors for a given system.
    """
    
    type = "q_vectors"
    
    _default = ("spherical_lattice",{"shells":(0,5,0.1), "width" : 0.1, "n_vectors" : 50})

    def configure(self, configuration, value):

        # If the value is a basestring, it will treated as a user definition        
        if isinstance(value,basestring):
            trajConfig = configuration[self._dependencies['trajectory']]
            target = trajConfig["basename"]
            definition = USER_DEFINITIONS.check_and_get(target, "q_vectors", value)            
            self["parameters"] = definition['parameters']
            self["type"] = definition['generator']
            self["is_lattice"] = definition['is_lattice']
            self["q_vectors"] = definition['q_vectors']
        
        else:                        
            generator, parameters = value
            generator = REGISTRY["qvectors"][generator](trajConfig["instance"].universe)
            generator.configure(parameters)
            data = generator.run()
                        
            if not data:
                raise ConfiguratorError("no Q vectors could be generated", self)

            self["parameters"] = parameters
            self["type"] = generator.type
            self["is_lattice"] = generator.is_lattice
            self["q_vectors"] = data
                                                
        self["shells"] = self["q_vectors"].keys()
        self["n_shells"] = len(self["q_vectors"])    
        self["value"] = self["q_vectors"]

    def get_information(self):
        
        info = ["%d Q shells generated\n" % self["n_shells"]]
        for (qValue,qVectors) in self["q_vectors"].items():
            info.append("Shell %s: %d Q vectors generated\n" % (qValue,len(qVectors)))
        
        return "".join(info)

class VectorConfigurator(Configurator):
    """
    This Configurator allows to input a 3D vector, by giving its 3 components
    """
    
    type = "vector"
    
    _default = [1.0,0.0,0.0]
    
    def __init__(self, name, valueType=int, normalize=False, notNull=False, **kwargs):

        # The base class constructor.
        Configurator.__init__(self, name, **kwargs)
        
        self._valueType = valueType
        
        self._normalize = normalize
        
        self._notNull = notNull

    def configure(self, configuration, value):
                
        vector = Vector(numpy.array(value,dtype=self._valueType))

        if self._normalize:
            vector = vector.normal()
            
        if self._notNull:
            if vector.length() == 0.0:
                raise ConfiguratorError("The vector is null", self)

        self['vector'] = vector
        self['value'] = vector
        
    @property
    def valueType(self):
        
        return self._valueType

    @property
    def normalize(self):
        
        return self._normalize

    @property
    def notNull(self):
        
        return self._notNull

    def get_information(self):
        
        return "Value: %r" % self["value"]

class InputFileConfigurator(Configurator):
    """
    This Configurator allows to set as input any existing file.
    """
    
    type = 'input_file'
    
    _default = ""
    
    def __init__(self, name, checkExistence=True, wildcard="All files|*.*", **kwargs):
        
        # The base class constructor.
        Configurator.__init__(self, name, **kwargs)
        
        self._checkExistence = checkExistence
        
        self._wildcard = wildcard
                
    def configure(self, configuration, value):
        if self.checkExistence:
            value = PLATFORM.get_path(value)
                    
            if not os.path.exists(value):
                raise ConfiguratorError("the input file %r does not exist." % value, self)
        
        self["value"] = value 
        self["filename"] = value
        
    @property
    def checkExistence(self):
        
        return self._checkExistence
    
    @property
    def wildcard(self):
        
        return self._wildcard

    def get_information(self):
        
        return "Input file: %r" % self["value"]
    
class IntegerConfigurator(Configurator):
    """
    This Configurator allow to input an Integer Value.
    """
    
    type = 'integer'
    
    _default = 0
    
    def __init__(self, name, mini=None, maxi=None, choices=None, **kwargs):
        
        # The base class constructor.
        Configurator.__init__(self, name, **kwargs)
        
        self._mini = int(mini) if mini is not None else None

        self._maxi = int(maxi) if maxi is not None else None
        
        self._choices = choices if choices is not None else []          
                
    def configure(self, configuration, value):

        try:
            value = int(value)
        except (TypeError,ValueError) as e:
            raise ConfiguratorError(e)
            
        if self._choices:
            if not value in self._choices:
                raise ConfiguratorError('the input value is not a valid choice.', self)
                        
        if self._mini is not None:
            if value < self._mini:
                raise ConfiguratorError("the input value is lower than %r." % self._mini, self)

        if self._maxi is not None:
            if value > self._maxi:
                raise ConfiguratorError("the input value is higher than %r." % self._maxi, self)

        self['value'] = value

    @property
    def mini(self):
        
        return self._mini

    @property
    def maxi(self):
        
        return self._maxi

    @property
    def choices(self):
        
        return self._choices

    def get_information(self):
        
        return "Value: %r" % self["value"]

class NetCDFInputFileConfigurator(InputFileConfigurator):
    """
    This configurator allows to input a NetCDF file.
    """
    
    type = 'netcdf_input_file'
    
    _default = ''
        
    def __init__(self, name, variables=None, **kwargs):
        
        # The base class constructor.
        InputFileConfigurator.__init__(self, name, **kwargs)
        
        self._variables = variables if variables is not None else []
           
    def configure(self, configuration, value):
                
        InputFileConfigurator.configure(self, configuration, value)
        
        if self.checkExistence:
            try:
                self['instance'] = NetCDFFile(self['value'], 'r')
                
            except IOError:
                raise ConfiguratorError("can not open %r NetCDF file for reading" % self['value'])

            for v in self._variables:
                try:                
                    self[v] = self['instance'].variables[v]
                except KeyError:
                    raise ConfiguratorError("the variable %r was not  found in %r NetCDF file" % (v,self["value"]))

    @property
    def variables(self):
        
        return self._variables

    def get_information(self):
        
        return "NetCDF input file: %r" % self["value"]

class MMTKNetCDFTrajectoryConfigurator(InputFileConfigurator):
    """
    MMTK trajectory file is a NetCDF file that store various data related to 
    molecular dynamics : atomic positions, velocities, energies, energy gradients etc. 
    """
    
    type = 'mmtk_trajectory'
    
    _default = ''
                        
    def configure(self, configuration, value):
                
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
                
        info = ["MMTK input trajectory: %r\n" % self["filename"]]
        info.append("Number of steps: %d\n" % self["length"])
        info.append("Size of the universe: %d\n" % self["universe"].numberOfAtoms())
        if (self['has_velocities']):
            info.append("The trajectory contains atomic velocities\n")
        
        return "".join(info)
                
class OutputFilesConfigurator(Configurator):
    """
    The output file configurator allow to select : the output directory, 
    the basename, and the format of the file resulting from the analysis.
    """
    
    type = 'output_files'
    
    _default = (os.getcwd(), "output", ["netcdf"])
                    
    def __init__(self, name, formats=None, **kwargs):
                        
        Configurator.__init__(self, name, **kwargs)

        self._formats = formats if formats is not None else ["netcdf"]
    
    def configure(self, configuration, value):
        
        dirname, basename, formats = value
                
        if not dirname:
            dirname = os.getcwd()
                
        if not basename:
            raise ConfiguratorError("empty basename for the output file.", self)
        
        root = os.path.join(dirname, basename)
        
        try:
            PLATFORM.create_directory(dirname)
        except:
            raise ConfiguratorError("the directory %r is not writable" % dirname)
                    
        if not formats:
            raise ConfiguratorError("no output formats specified", self)

        for fmt in formats:
            
            if not fmt in self._formats:
                raise ConfiguratorError("the output file format %r is not a valid output format" % fmt, self)
            
            if not REGISTRY["format"].has_key(fmt):
                raise ConfiguratorError("the output file format %r is not registered as a valid file format." % fmt, self)

        self["root"] = root
        self["formats"] = formats
        self["files"] = ["%s%s" % (root,REGISTRY["format"][f].extension) for f in formats]

    @property
    def formats(self):
        return self._formats

    def get_information(self):
        
        info = ["Input files:\n"]
        for f in self["files"]:
            info.append(f)
            info.append("\n")
        
        return "".join(info)
        
class ProjectionConfigurator(Configurator):
    """
    This configurator allows to define a projection axis. 
    """

    type = 'projection'

    _default = None
                        
    def configure(self, configuration, value):
        
        if value is None:
            value = ('none',None)

        try:
            mode, axis = value
        except (TypeError,ValueError) as e:
            raise ConfiguratorError(e)

        if not isinstance(mode,basestring):
            raise ConfiguratorError("invalid type for projection mode: must be a string")            
        
        mode = mode.lower()
                            
        try:
            self["projector"] = REGISTRY['projector'][mode]()
        except KeyError:
            raise ConfiguratorError("the projector %r is unknown" % mode)
        else:
            self["projector"].set_axis(axis)
            self["axis"] = self["projector"].axis

    def get_information(self):
        
        return "Projection along %r axis:" % self["axis"] 
            
class InterpolationOrderConfigurator(IntegerConfigurator):
    """
    This configurator allows to set as input the order of the interpolation apply when deriving velocities 
    from atomic coordinates to the atomic trajectories.
    The value should be higher than 0 if velocities are not provided with the trajectory.
    """
    
    type = "interpolation_order"
    
    _default = 0

    def __init__(self, name, **kwargs):
                
        IntegerConfigurator.__init__(self, name, choices=range(-1,len(INTERPOLATION_ORDER)), **kwargs)

    def configure(self, configuration, value):
        
        IntegerConfigurator.configure(self, configuration, value)
        
        if value == -1:

            trajConfig = configuration[self._dependencies['trajectory']]

            if not "velocities" in trajConfig['instance'].variables():
                raise ConfiguratorError("the trajectory does not contain any velocities. Use an interpolation order higher than 0", self)
            
            self["variable"] = "velocities"
            
        else:

            self["variable"] = "configuration"
            
    def get_information(self):
        
        if self["value"] == -1:
            return "No velocities interpolation"
        else:
            return "Velocities interpolated from atomic coordinates"
        
class RangeConfigurator(Configurator):
    """
    This configurator allow to input a range of value given 3 parameters : start, stop, step
    """
    
    type = "range"

    _default = (0,10,1)

    def __init__(self, name, valueType=int, includeLast=False, sort=False, toList=False, mini=None, maxi=None, **kwargs):
                        
        Configurator.__init__(self, name, **kwargs)
        
        self._valueType = valueType
        
        self._includeLast = includeLast
        
        self._sort = sort
        
        self._toList = toList
        
        self._mini = mini
        
        self._maxi = maxi
                        
    def configure(self, configuration, value):
        
        first, last, step = value
        
        if self._includeLast:
            last += step/2.0
            
        value = numpy.arange(first, last, step)
        value = value.astype(self._valueType)
        
        if self._mini is not None:
            value = value[value >= self._mini]

        if self._maxi is not None:
            value = value[value <= self._maxi]
        
        if value.size == 0:
            raise ConfiguratorError("the input range is empty." , self)
        
        if self._sort:
            value = numpy.sort(value)
        
        if self._toList:
            value = value.tolist()
                                                             
        self["value"] = value
        
        self['first'] = self['value'][0]
                
        self['last'] = self['value'][-1]

        self['number'] = len(self['value'])
                
        self['mid_points'] = (value[1:]+value[0:-1])/2.0

        try:
            self["step"] = self['value'][1] - self['value'][0]
        except IndexError:
            self["step"] = 1
                    
    @property
    def valueType(self):
        
        return self._valueType
    
    @property
    def includeLast(self):
        
        return self._includeLast
    
    @property
    def toList(self):
        
        return self._toList
    
    @property
    def sort(self):
        
        return self._sort
    
    @property
    def mini(self):
        
        return self._mini   
    
    @property
    def maxi(self):
        
        return self._maxi   

    def get_information(self):
        
        info = "$d values from %s to %s" % (self['number'],self['first'],self['last'])
        
        if self._includeLast:
            info += ("last value included")
        else:
            info += ("last value excluded")
         
        return info

class FramesConfigurator(RangeConfigurator):
    """
    This frames configurator allow to select as input of the analysis a range of frame 
    given 3 parameters : the first frame, the last frame, and the value of the step 
    """
    
    type = 'frames'
    
    def __init__(self, name, **kwargs):

        RangeConfigurator.__init__(self, name, sort=True, **kwargs)
             
    def configure(self, configuration, value):
                                        
        trajConfig = configuration[self._dependencies['trajectory']]

        if value == "all":
            value = (0, trajConfig['length'], 1)
            
        self._mini = -1
        self._maxi = trajConfig['length']
        
        RangeConfigurator.configure(self, configuration, value)
                                                          
        self["n_frames"] = self["number"]
                                                                                             
        self['time'] = trajConfig['md_time_step']*self['value']

        self['relative_time'] = self['time'] - self['time'][0]
        
        # case of single frame selected
        try:
            self['time_step'] = self['time'][1] - self['time'][0]
        except IndexError:
            self['time_step'] = 1.0

    def get_information(self):
        
        return "%d frames selected (first=%.3f ; last = %.3f ; time step = %.3f)" % \
            (self["n_frames"],self["time"][0],self["time"][-1],self["time_step"])
                        
class RunningModeConfigurator(Configurator):
    """
    This configurator allow to choose the mode use to run the calculation.
    choose among "monoprocessor" or "multiprocessor", 
    and also, in the second case, the number of processors getting involve.
    the option "remote", is not yet available.
    """

    type = 'running_mode'
    
    availablesModes = ["monoprocessor","multiprocessor","remote"]
    
    _default = ("monoprocessor", 1)                

    def configure(self, configuration, value):
                
        mode = value[0].lower()
        
        if not mode in self.availablesModes:
            raise ConfiguratorError("%r is not a valid running mode." % mode, self)

        if mode == "monoprocessor":
            slots = 1

        else:

            import Pyro
            Pyro.config.PYRO_STORAGE=PLATFORM.home_directory()

            slots = int(value[1])
                        
            if mode == "multiprocessor":
                import multiprocessing
                maxSlots = multiprocessing.cpu_count()
                del multiprocessing
                if slots > maxSlots:   
                    raise ConfiguratorError("invalid number of allocated slots.", self)
                      
            if slots <= 0:
                raise ConfiguratorError("invalid number of allocated slots.", self)
               
        self['mode'] = mode
        
        self['slots'] = slots

    def get_information(self):
        
        return "Run in %s mode (%d slots)" % (self["mode"],self["slots"])

class InstrumentResolutionConfigurator(Configurator):
    """
    This configurator allow to set a simulated instrument resolution.
    Clicking on the SET button open a widget allowing to select one function into 
    a set of basics, and to parameterized it, then the resulting kernel will be 
    automatically sampled and convoluted with the signal.
    """
    
    type = "instrument_resolution"
        
    _default = ('gaussian', {'mu': 0.0, 'sigma': 0.0001})
        
    def configure(self, configuration, value):

        framesCfg = configuration[self._dependencies['frames']]
                
        time = framesCfg["time"]
        self["n_frames"] = len(time)                                                                                             

        self._timeStep = framesCfg['time'][1] - framesCfg['time'][0]
        self['time_step'] = self._timeStep
                
        self["frequencies"] = numpy.fft.fftshift(numpy.fft.fftfreq(2*self["n_frames"]-1,self["time_step"]))
        
        df = round(self["frequencies"][1] - self["frequencies"][0],3)
        
        self["n_frequencies"] = len(self["frequencies"])

        kernel, parameters = value
                
        kernelCls = REGISTRY["instrumentresolution"][kernel]
                
        resolution = kernelCls()
        
        resolution.set_kernel(self["frequencies"], self["time_step"], parameters)

        dmax = resolution.timeWindow.max()-1
        
        if dmax > 0.1:
            raise ConfiguratorError('''the resolution function is too sharp for the available frequency step. 
You can change your resolution function settings to make it broader or use "ideal" kernel if you do not want to smooth your signal.
For a gaussian resolution function, this would correspond to a sigma at least equal to the frequency step (%s)''' % df,self)
        elif dmax < -0.1:
            raise ConfiguratorError('''the resolution function is too broad.
You should change your resolution function settings to make it sharper.''',self)
            
        self["frequency_window"] = resolution.frequencyWindow

        self["time_window"] = resolution.timeWindow
        
    def get_information(self):
        
        return "None yet" 
          
class TrajectoryVariableConfigurator(Configurator):
    """
    This configurator allows to get a variable stored in a MMTK trajectory
    """
        
    type = 'trajectory_variable'
    
    _default = "velocities"
        
    def configure(self, configuration, value):
                
        trajConfig = configuration[self._dependencies['trajectory']]
       
        if not value in trajConfig['instance'].variables():
            raise ConfiguratorError("%r is not registered as a trajectory variable." % value, self)
        
        self['value'] = value

    def get_information(self):
        
        return "Selected variable: %r" % self["value"]

class AtomSelectionConfigurator(Configurator):    
    """
    This configurator allow to select among the User Definitions, an atomic selection.
    Without any selection, all the atoms records into the trajectory file will be take into account.
    If a selection is define, the analysis will take into account only those sub-selection.
    
    To Build an atom selection you have to :
    - Create a workspace based on a mmtk_trajectory data,
    - drag a molecular viewer on it,
    - drag into the Molecular Viewer his "Atom selection" plugin
    """

    type = 'atom_selection'
    
    _default = "all"
                    
    def configure(self, configuration, value):
                          
        trajConfig = configuration[self._dependencies['trajectory']]

        target = trajConfig["basename"]
        
        if value is None:
            value = "all"
        
        if not isinstance(value,basestring):
            raise ConfiguratorError("invalid type for atom selection. Must be a string", self)
        
        self["value"] = value
        
        if USER_DEFINITIONS.has_key(value):
            definition = USER_DEFINITIONS.check_and_get(target, "atom_selection", value)
            self.update(definition)
        else:
            parser = SelectionParser(trajConfig["instance"].universe)
            expression, selection = parser(value,True)
            self["expression"] = expression
            self["indexes"] = numpy.array(selection,dtype=numpy.int32)

        self["n_selected_atoms"] = len(self["indexes"])
        atoms = sorted(trajConfig["universe"].atomList(), key = operator.attrgetter('index'))
        selectedAtoms = [atoms[idx] for idx in self["indexes"]]
        self["elements"] = [[at.symbol] for at in selectedAtoms]

        if self._dependencies.has_key("grouping_level"):
            self.group(selectedAtoms, configuration[self._dependencies['grouping_level']]['value'])
        else:
            self.group(selectedAtoms)
                                 
        self.set_contents()
            
    @staticmethod                                                                                                                        
    def find_parent(atom, level):
        
        for _ in range(level):
            atom = atom.parent
            
        return atom
    
    def group(self, selectedAtoms, level="atom"):
                        
        level = level.strip().lower()
                
        groups = collections.OrderedDict()
        
        for i, idx in enumerate(self["indexes"]):
            at = selectedAtoms[i]
            lvl = LEVELS[level][at.topLevelChemicalObject().__class__.__name__.lower()]
            parent = self.find_parent(at,lvl)        
            groups.setdefault(parent,[]).append(idx)
        
        self["groups"] = groups.values()
            
        self["n_groups"] = len(self["groups"])
        
        if level != "atom":
            self["elements"] = [["dummy"]]*self["n_groups"]
                                        
        self["level"] = level
                
        self.set_contents()
                        
    def set_contents(self):
        
        self["contents"] = collections.OrderedDict()
        self['index_to_symbol'] = collections.OrderedDict()
        for i, group in enumerate(self["elements"]):
            for j, el in enumerate(group):
                self["contents"].setdefault(el,[]).append(self["groups"][i][j])
                self['index_to_symbol'][self["groups"][i][j]] = el
                 
        for k,v in self["contents"].items():
            self["contents"][k] = numpy.array(v)
            
        self["n_atoms_per_element"] = dict([(k,len(v)) for k,v in self["contents"].items()])              
                    
        self['n_selected_elements'] = len(self["contents"])
                
    def get_information(self):
        
        info = []
        info.append("Number of selected atoms:%d\n" % self["n_selected_atoms"])
        info.append("Level of selection:%s\n" % self["level"])
        info.append("Number of selected groups:%d\n" % self["n_groups"])
        info.append("Selected elements:%s\n" % self["contents"].keys())
        
        return "".join(info)
        
class AtomTransmutationConfigurator(Configurator):
    """
    This configurator allow to select among the User Definitions, an atomic transmutation.
    Without any transmutation, all the atoms records into the trajectory keep there own types.
    If a transmutation is define, the analysis will consider atoms of a certain type 
    exactly like if they have another type, respectfully to the transmutation definition.
    
    To Build an atomic transmutation definition you have to :
    - Create a workspace based on a mmtk_trajectory data,
    - drag a molecular viewer on it,
    - drag into the Molecular Viewer his "Atom transmutation" plugin
    """
    type = 'atom_transmutation'
                                
    def configure(self, configuration, value):

        self["value"] = value  
        
        if value is None:
            return

        self["atom_selection"] = configuration[self._dependencies['atom_selection']]
        if self["atom_selection"]["level"] != "atom":
            raise ConfiguratorError("the atom transmutation can only be set with a grouping level set to %r" % 'atom', self)

        trajConfig = configuration[self._dependencies['trajectory']]
                                                                
        parser = SelectionParser(trajConfig["universe"])
        
        # If the input value is a dictionary, it must have a selection string or a python script as key and the element 
        # to be transmutated to as value 
        if isinstance(value,dict):
            for expression,element in value.items():
                expression, selection = parser.select(expression, True)                    
                self.transmutate(configuration, selection, element)
          
        # Otherwise, it must be a list of strings that will be found as user-definition keys
        elif isinstance(value,(list,tuple)):
            for definition in value:
                if USER_DEFINITIONS.has_key(definition):
                    ud = USER_DEFINITIONS.check_and_get(trajConfig["basename"], "atom_transmutation", definition)
                    self.transmutate(configuration, ud["indexes"], ud["element"])
                else:
                    raise ConfiguratorError("wrong parameters type:  must be either a dictionary whose keys are an atom selection string and values are the target element \
                    or a list of string that match an user definition",self)
        else:
            raise ConfiguratorError("wrong parameters type:  must be either a dictionary whose keys are an atom selection string and values are the target element \
            or a list of string that match an user definition",self)

    def transmutate(self, configuration, selection, element):
        
        if element not in ELEMENTS:
            raise ConfiguratorError("the element %r is not registered in the database" % element, self)
                
        for idx in selection:
            try:
                pos = self["atom_selection"]["groups"].index([idx])
                
            except ValueError:
                continue
            
            else:
                self["atom_selection"]["elements"][pos] = [element]
                
        configuration.configurators[self._dependencies['atom_selection']].set_contents(configuration)

    def get_information(self):
        
        if self["value"] is None:
            return "No atoms selected for deuteration"
        
        return "Number of selected atoms for deuteration:%d\n" % self["atom_selection"]["n_selected_atoms"]
        
class AxisSelection(Configurator):
    """
    This configurator allow to select  an axis selection among the User Definitions.
    This could be mandatory for the analysis, if not, some generic behavior will be setup.
    An axis selection is defined using two atomic coordinates (or atomic cluster center of mass) 
    
    To Build an axis selection definition you have to :
    - Create a workspace based on a mmtk_trajectory data,
    - drag a molecular viewer on it,
    - drag into the Molecular Viewer his "Axis selection" plugin
    """
    
    type = "axis_selection"
    
    _default = None

    def configure(self, configuration, value):
        
        trajConfig = configuration[self._dependencies['trajectory']]
                
        target = trajConfig["basename"]

        if USER_DEFINITIONS.has_key(value):
            definition = USER_DEFINITIONS.check_and_get(target, "axis_selection", value)
            self.update(definition)
        else:
            self.update(value)

        e1 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['endpoint1'], True)
        e2 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['endpoint2'], True)

        self["value"] = value
          
        self['endpoints'] = zip(e1,e2)      
        
        self['n_axis'] = len(self['endpoints'])

    def get_information(self):
        
        return "Axis vector:%s" % self["value"]
        
class BasisSelection(Configurator):
    """
    This configurator allow to select a basis selection among the User Definitions.
    This could be mandatory for the analysis, if not, some generic behavior will be setup.
    An axis selection is defined using :
    - one origin, 
    - two vector define using the origin and two atomic coordinates (or atomic cluster center of mass),
    - the third direction, automatically taken as the vector product of the two precedent.  
    
    To Build a basis selection definition you have to :
    - Create a workspace based on a mmtk_trajectory data,
    - drag a molecular viewer on it,
    - drag into the Molecular Viewer his "Basis selection" plugin
    """
    
    type = 'basis_selection'
    
    _default = None

    def configure(self, configuration, value):
        trajConfig = configuration[self._dependencies['trajectory']]
                
        target = trajConfig["basename"]

        if USER_DEFINITIONS.has_key(value):
            definition = USER_DEFINITIONS.check_and_get(target, "basis_selection", value)
            self.update(definition)
        else:
            self.update(value)

        e1 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['origin'], True)
        e2 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['x_axis'], True)
        e3 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['y_axis'], True)
        
        self["value"] = value
        
        self['basis'] = zip(e1,e2,e3)      
        
        self['n_basis'] = len(self['basis'])

    def get_information(self):
        
        return "Basis vector:%s" % self["value"]
        
class GroupingLevelConfigurator(SingleChoiceConfigurator):
    """
    This configurator allow to choose the level of coarseness which will be apply into the calculation
    """
    
    type = 'grouping_level'
    
    _default = "atom"
    
    def __init__(self, name, choices=None, **kwargs):
        
        choices = choices if choices is not None else LEVELS.keys()

        SingleChoiceConfigurator.__init__(self, name, choices=choices, **kwargs)
    
    def configure(self, configuration, value):
        
        value = value.lower()
        
        if not value in LEVELS.keys():
            raise ConfiguratorError("%r is not a valid grouping level." % value, self)

        self["value"] = value

    def get_information(self):
        
        return "Grouping level: %r\n" % self["value"]

class WeightsConfigurator(SingleChoiceConfigurator):
    """
    This configurator allows to choose the way the relevant quantities will be weighted during the calculation
    The most frequently used weights are defined as constant into the periodic table database.
    you can access to the table by clicking into the "atom" icon on the main toolbar
    """
    
    type = 'weights'
    
    _default = "equal"
           
    def __init__(self, name, choices=None, **kwargs):
        
        choices = choices if choices is not None else ELEMENTS.numericProperties
        
        SingleChoiceConfigurator.__init__(self, name, choices=choices, **kwargs)

    def configure(self, configuration, value):
        
        value = value.lower()
        
        if not value in ELEMENTS.numericProperties:
            raise ConfiguratorError("weight %r is not registered as a valid numeric property." % value, self)
                                         
        self['property'] = value

    def get_information(self):
        
        return "Weighting scheme:%s" % self["property"]
           
class McStasInstrumentConfigurator(InputFileConfigurator):

    type = "mcstas_instrument"

class McStasOptionsConfigurator(Configurator):

    type = "mcstas_options"
    
    _default = {"ncount" : 10000, "dir" : os.path.join(os.getcwd(),"mcstas_output",time.strftime("%d.%m.%Y-%H:%M:%S", time.localtime()))}
        
    def configure(self, configuration, value):
        
        options = self._default.copy()
        
        for k,v in value.items():
            if k not in options:
                continue
            options[k] = v
            
        tmp = ['']
        for k,v in options.items():     
            if k == "dir":
                if os.path.exists(v):
                    v =  self._default['dir']
                self["mcstas_output_directory"] = v
            tmp.append("--%s=%s" % (k,v))

        dirname = os.path.dirname(self["mcstas_output_directory"])

        try:
            PLATFORM.create_directory(dirname)
        except:
            raise ConfiguratorError("The directory %r is not writable" % dirname)
                           
        self["value"] = tmp

    def get_information(self):
        
        return "McStas command line options:%s" % self["value"]

        
class McStasParametersConfigurator(Configurator):
    """
    This configurator allows to set in a string form the McStas command-line input parameters.
    """

    type = "instrument_parameters"

    _mcStasTypes = {'double' : float, 'int' : int, 'string' : str}
    
    def __init__(self, name, exclude=None, **kwargs):
        
        # The base class constructor.
        Configurator.__init__(self, name, **kwargs)
        
        self._exclude = exclude if exclude is not None else []
        
    def configure(self, configuration, value):
        
        instrConfig = configuration[self._dependencies['instrument']]
        
        exePath = instrConfig['value']
        
        s = subprocess.Popen([exePath,'-h'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
               
        instrParameters = dict([(v[0],[v[1],v[2]]) for v in re.findall("\s*(\w+)\s*\((\w+)\)\s*\[default=\'(\S+)\'\]",s.communicate()[0]) if v[0] not in self._exclude])
                
        val = {}
        for k,v in value.items():
            if k not in instrParameters:
                instrParameters.pop(k)
            val[k] = self._mcStasTypes[instrParameters[k][0]](v)
                                                      
        self["value"] = ["%s=%s" % (k,v) for k,v in val.items()]
        
    @property
    def exclude(self):
        
        return self._exclude

    def get_information(self):
        
        return "McStas command line parameters:%s" % self["value"]
