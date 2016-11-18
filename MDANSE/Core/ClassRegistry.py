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

:author: Eric C. Pellegrini
'''

import glob
import imp
import inspect
import os
import sys

from MDANSE.Core.Singleton import Singleton
    
class ClassRegistry(object):
    '''
    Metaclass that registers the classes that make the MDANSE framework.

    The MDANSE framework is based on a set of interfaces that covers different aspects of the framework such 
    as the analysis, the input data, the output file formats ... By metaclassing each base class of these interfaces 
    with :py:class:`~MDANSE.Core.ClassRegistry.ClassRegistry` object, their respective concrete class instances will be 
    automatically registered at import time in a data structure that can be further used all over the framework.
        
    The data structure used to store the concrete classes is a nested dictionary whose primary key 
    is the :py:attr:`type` class attribute of the base class they are inheriting from and secondary key is 
    their own :py:attr:`type` class attribute. Any concrete class of those interfaces that does not define the :py:attr:`type` 
    class attribute will not be registered.    
    '''
    
    __metaclass__ = Singleton

    def __init__(self):
        
        self._registry = {}
        
        self._sections = {}
        
    def __setitem__(self,name,cls):

        # The class to be registered must have a class attribute "_registry" to be registered, otherwise return       
        clsRegistry = getattr(cls,"_registry")
        if clsRegistry is None:
            return
        
        # And this attribute must be a string for the class to be registerable otherwise return
        if not isinstance(clsRegistry,basestring):
            return
        
        # Fetch the branch of the registry corresponding the one of the class to be registred, otherwise create a new branch        
        d = self._registry.setdefault(clsRegistry,{})
        
        # If a class has already been registered with that name return
        if d.has_key(name):
            return

        setattr(cls,"_type",name)
        
        d[name] = cls
                
    def __getitem__(self,name):
        
        return self._registry.get(name,{})

    def update(self,packageDir):
        '''
        Update the classes registry by importing all the modules contained in a given package.
        
        Only the classes metaclassed by :py:class:`~MDANSE.Core.ClassRegistry.ClassRegistry` will be registered.
        
        :param packageDir: the package for which all modules should be imported
        :type packageDir: str
        '''
                
        for module in glob.glob(os.path.join(packageDir,'*.py')):
                                             
            moduleDir, moduleFile = os.path.split(module)
     
            if moduleFile == '__init__.py':
                continue
     
            moduleName, _ = os.path.splitext(moduleFile)
            
            # Any error that may occur here has to be caught. In such case the module is skipped.    
            try:
                filehandler,path,description = imp.find_module(moduleName, [moduleDir])
                mod = imp.load_module(moduleName,filehandler,path,description)
            except:
                continue
            else:
                if os.path.abspath(os.path.dirname(mod.__file__)) != os.path.abspath(moduleDir):                    
                    print "A module with name %s is already present in your distribution with %s path." % (moduleName,moduleDir)
    
    def info(self, interface):
        '''
        Returns informations about the subclasses of a given base class stored in the registry.
        
        :param interface: the name of base class of whom information about its subclasses is requested
        :type interface: str
        
        :return: return the stringified list of subclasses of a given registered interface.
        :rtype: str
        '''
                
        if not self._registry.has_key(interface):
            return "The interface " + interface + " is not registered"

        words = ["Name", "Class","File"]

        contents = []
        contents.append("="*130)
        contents.append("{1:{0}s} {2:50s} {3}")
        contents.append("="*130)
        
        maxlength = -1
        
        # Loop over the registry items.
        for i, (k, v) in enumerate(sorted(self._registry[interface].items())):
            
            # Get the module corresponding to the job class.
            mod = inspect.getmodule(v)

            words.extend([k, v.__name__,mod.__file__])

            contents.append("{%d:{0}s} {%d:50} {%d}" % (3*i+4,3*i+5,3*i+6))
            
            maxlength = max(len(k),maxlength)
                        
        contents.append('-' * 130)
        
        contents = "\n".join(contents)        
                    
        return contents.format(maxlength,*words)

    @property
    def interfaces(self):
        '''
        Returns the interfaces that are currently registered.
        
        :return: the interfaces currently registered.
        :rtype: list of str
        '''
        
        return sorted(self._registry.keys())
        
REGISTRY = ClassRegistry()

                
