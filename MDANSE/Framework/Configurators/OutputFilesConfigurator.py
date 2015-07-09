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
Created on May 21, 2015

:author: Eric C. Pellegrini
'''

import os

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
                
class OutputFilesConfigurator(IConfigurator):
    """
    This configurator allows to define the output directory, the basename, and the format(s) of the output file(s) resulting from an 
    analysis.
    
    Once configured, this configurator will provide a list of files built by joining the given output directory, the basename and the 
    extensions corresponding to the input file formats.
    
    Currently MDANSE supports ASCII, NetCDF and SVG file formats. To define a new output file format for an analysis, you must inherit from
    MDANSE.Framework.Formats.IFormat.IFormat interface.   
    """
    
    type = 'output_files'
    
    _default = ('.', "output", ["netcdf"])
                    
    def __init__(self, name, formats=None, **kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str
        :param formats: the list of output file formats suported.  
        :type formats: list of str
        '''
                        
        IConfigurator.__init__(self, name, **kwargs)

        self._formats = formats if formats is not None else OutputFilesConfigurator._default[2]
    
    def configure(self, configuration, value):
        '''
        Configure a set of output files for an analysis. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the output files specifications. Must be a 3-tuple whose 1st element \
        if the output directory, 2nd element the basename and 3rd element a list of file formats.
        :type value: 3-tuple
        '''
        
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
        '''
        Returns the list of output file formats suported.
        
        :return: the list of file formats suported.
        :rtype: list of str
        '''
        return self._formats

    def get_information(self):
        '''
        Returns string information about this configurator.
        
        :return: the information about this configurator.
        :rtype: str
        '''
        
        info = ["Input files:\n"]
        for f in self["files"]:
            info.append(f)
            info.append("\n")
        
        return "".join(info)