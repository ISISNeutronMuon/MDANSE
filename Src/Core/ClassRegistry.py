# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Core/ClassRegistry.py
# @brief     Implements module/class/test ClassRegistry
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import glob
import imp
import inspect
import os

from MDANSE.Core.Singleton import Singleton
    
def path_to_module(path,stop=""):
    
    path, _ = os.path.splitext(path)
    
    splittedPath = path.split(os.sep)
        
    try:
        idx = splittedPath[::-1].index(stop)
    except ValueError:
        idx = 0
    finally:
        module = ".".join(splittedPath[len(splittedPath)-1-idx:])
            
    return module
        
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

    def update(self,packageDir, macros=False):
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

            # Any error that may occur here has to be caught. In such case the module is skipped.    
            try:
                if macros:
                    moduleName,_ = os.path.splitext(moduleFile)
                    filehandler,path,description = imp.find_module(moduleName, [moduleDir])
                    imp.load_module(moduleName,filehandler,path,description)
                    filehandler.close()
                else:
                    moduleName, _ = os.path.splitext(moduleFile)
                    module = path_to_module(module,stop="MDANSE")
                    __import__(module)
            except:
                continue
        
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

                
