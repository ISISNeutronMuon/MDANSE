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

import abc
import glob
import inspect
import os
import sys

class _Meta(type):
    '''
    Metaclass that allows to use the __getitem__ method at a class level for the class that has been built.
     
    The class that uses this metaclass must define a class attribute named _registry that will be used
    by the __getitem__ method.
    '''
         
    def __getitem__(self, item):
        """
        Returns a given item stored in the class registry
        """
         
        return self._registry[item]
    
class ClassRegistry(abc.ABCMeta):
    '''
    Metaclass that registers the subclasses of all the base classes used in MDANSE framework.

    The subclasses are stored internally in a nested dictionary whose primary key 
    is the 'type' class attribute of the base class they are inheriting from and secondary key is 
    their own 'type' class attribute.
    '''
    
    __metaclass__ = _Meta

    __interfaces = []

    _registry = {}
                
    def __init__(self, name, bases, namespace):
        '''
        Constructor of a class metaclassed by ClassFactory
        
        :param name: the name of the class to be built by this metaclass
        :type name: str
        :param bases: the base classes of the class to be built by this metaclass
        :type bases: tuple 
        :param namespace: the attributes and methods of the class to be built by this metaclass
        :type namespace: dict
        '''
        
        super(ClassRegistry, self).__init__(name, bases, namespace)
                
        # Get the typ of the class
        typ = getattr(self, 'type', None)

        if typ is None:
            return

        metaClass = namespace.get("__metaclass__", None)
                              
        if metaClass is ClassRegistry:
            ClassRegistry.__interfaces.append(self)
            if (ClassRegistry._registry.has_key(typ)):
                return
            ClassRegistry._registry[typ] = {}

        else:
                                            
            for interface in ClassRegistry.__interfaces:
                if issubclass(self, interface):
                    ClassRegistry._registry[interface.type][typ] = self
                    break
          
    @classmethod      
    def update_registry(cls,packageDir):
        '''
        Update the classes registry by importing all the modules contained in a given package.
        
        Only the classes that are metaclassed by ClassRegistry will be registered.
        
        :param packageDir: the package for which all modules should be imported
        :type packageDir: str
        '''
                
        for module in glob.glob(os.path.join(packageDir,'*.py')):
                                             
            moduleDir, moduleFile = os.path.split(module)
     
            if moduleFile == '__init__.py':
                continue
     
            moduleName, moduleExt = os.path.splitext(moduleFile)
            
            if moduleDir not in sys.path:        
                sys.path.append(moduleDir)

            # Any error that may occur here has to be caught. In such case the module is skipped.    
            try:
                __import__(moduleName, locals(), globals())
            except:
                continue
    
    @classmethod
    def info(cls, interface):
        '''
        Returns informations about the subclasses of a given base class stored in the registry.
        
        :param interface: the name of base class of whom information about its subclasses is requested
        :type interface: str
        
        :return: return the stringified list of subclasses of a given registered interface.
        :rtype: str
        '''
                
        if not cls._registry.has_key(interface):
            return "The interface " + interface + " is not registered"

        words = ["Name", "Class","File"]

        contents = []
        contents.append("="*130)
        contents.append("{1:{0}s} {2:50s} {3}")
        contents.append("="*130)
        
        maxlength = -1
        
        # Loop over the registry items.
        for i, (k, v) in enumerate(sorted(cls._registry[interface].items())):
            
            # Get the module corresponding to the job class.
            mod = inspect.getmodule(v)

            words.extend([k, v.__name__,mod.__file__])

            contents.append("{%d:{0}s} {%d:50} {%d}" % (3*i+4,3*i+5,3*i+6))
            
            maxlength = max(len(k),maxlength)
                        
        contents.append('-' * 130)
        
        contents = "\n".join(contents)        
                    
        return contents.format(maxlength,*words)

    @classmethod
    def get_interfaces(cls):
        '''
        Returns the interfaces that are currently registered.
        
        :return: the interfaces currently registered.
        :rtype: list of str
        '''
        
        return sorted(cls._registry.keys())