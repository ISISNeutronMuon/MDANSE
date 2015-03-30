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

@author: pellegrini
'''

import os

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
                
class OutputFilesConfigurator(IConfigurator):
    """
    The output file configurator allow to select : the output directory, 
    the basename, and the format of the file resulting from the analysis.
    """
    
    type = 'output_files'
    
    _default = (os.getcwd(), "output", ["netcdf"])
                    
    def __init__(self, name, formats=None, **kwargs):
                        
        IConfigurator.__init__(self, name, **kwargs)

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