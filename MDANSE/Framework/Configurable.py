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

import _abcoll
import collections

from MDANSE.Core.Error import Error
from MDANSE import REGISTRY

class ConfigurationError(Error):
    '''
    Handles the exception that may occurs when configuring an object that derives from MDANSE.Core.Configurable class.
    '''
    pass

class Configurable(object):
    '''
    This class allows any object that derives from it to be configurable within the MDANSE framework.
    
    Within that framework, to be configurable, a class must:
        #. derive from this class
        #. implement the "configurators"  class attribute as a list of 3-tuple whose:
            #.. 0-value is the type of the configurator that will be used to fetch the corresponding 
                MDANSE.Framework.Configurators.IConfigurator.IConfigurator derived class from the configurators registry
            #.. 1-value is the name of the configurator that will be used as the key of the _configuration attribute.
            #.. 2-value is the dictionary of the keywords used when initializing the configurator.  
    '''
    
    def __init__(self):
        '''
        Constructor
        '''
               
        self._configuration = {}

        configurators = getattr(self,"configurators",{})
        
        if not isinstance(configurators,_abcoll.Mapping):
            raise ConfigurationError("Invalid type for configurators: must be a mapping-like object")

        self._configurators = {}
        for name,(typ,kwds) in configurators.items():
            try:
                self._configurators[name] = REGISTRY["configurator"][typ](name, **kwds)
            # Any kind of error has to be caught
            except:
                raise ConfigurationError("Invalid type for %r configurator" % name)
                        
        self._configured=False
        
    def __getitem__(self, name):
        """
        Returns a configuration item given its name.
        
        :param name: the name of the configuration item
        :type name: str 
        
        If not found raise a ConfigurationError. 
        """
        
        if not self._configurators.has_key(name):
            raise ConfigurationError("The item %r is not valid for this configuration." % name)
        
        return self._configuration.setdefault(name,{})
        
    def setup(self,parameters):
        '''
        Setup the configuration according to a set of input parameters.
        
        :param parameters: the input parameters
        :type parameters: dict
        '''
                
        # Cleans the previous configuration
        self._configuration.clear()

        self._configured=False
                
        # If no configurator has to be configured, just return
        if not self._configurators:
            self._configured=True
            return
        
        if isinstance(parameters,dict):
            # Loop over the configuration items          
            for k,v in self._configurators.items():
                # If no input parameter has been set for this item, use its default value.
                if not parameters.has_key(k):
                    parameters[k] = v.default
        else:
            raise ConfigurationError("Invalid type for configuration parameters")             
                        
        toBeConfigured = set(self._configurators.keys())
        configured = set()
                
        while toBeConfigured != configured:
            
            progress = False

            for name,conf in self._configurators.items():
                                                                                
                if name in configured:
                    continue
                
                if conf.check_dependencies(configured):

                    conf.configure(self,parameters[name])
                    
                    self._configuration[name]=conf
                                                            
                    configured.add(name)
                    
                    progress = True
                    
            if not progress:
                raise ConfigurationError("Circular or unsatisfiable dependencies when setting up configuration.")

        self._configured=True

    def __str__(self):
        '''
        Returns the informations about the current configuration in text form.
        
        :return: the informations about the current configuration in text form
        :rtype: str
        '''
        
        if not self._configured:
            return "Not yet configured"
        
        info = []
        
        for configurator in self._configuration.values():
            
            info.append(configurator.get_information())
            
        return "\n".join(info)
    
    @classmethod
    def build_doc(cls):
        '''
        Return the documentation about a configurable class based on its configurators contents.
        
        :param cls: the configurable class for which documentation should be built
        :type cls: an instance of MDANSE.Framework.Configurable.Configurable derived class
        
        :return: the documnetation about the configurable class
        :rtype: str
        '''
              
        configurators = getattr(cls,"configurators",{})
        
        if not isinstance(configurators,_abcoll.Mapping):
            raise ConfigurationError("Invalid type for configurators: must be a mapping-like object")
                                    
        doclist = []
        
        for name,(typ,kwds) in configurators.items():
            cfg=REGISTRY["configurator"][typ](name, **kwds)
            doclist.append({'Configurator' : name,'Default value' : repr(cfg.default),'Description' : str(cfg.__doc__)})
            
        l = ['Configurator','Default value','Description']
        
        sizes = []  
        sizes.append([len(l[0])]) 
        sizes.append([len(l[1])]) 
        sizes.append([len(l[2])]) 
        
        for v in doclist:
            sizes[0].append(len(v['Configurator']))
            sizes[1].append(len(v['Default value']))
            
            v['Description'] = v['Description'].replace('\n',' ').replace('  ',' ').replace('  ',' ').replace('  ',' ')
            sizes[2].append(len(v['Description']))
            
        maxSizes = [max(s) for s in sizes]
            
        s = (maxSizes[0]+2, maxSizes[1]+2, maxSizes[2]+2)
                        
        docstring = "\n:Example:\n\n"
        docstring += ">>> from MDANSE import REGISTRY\n"
        docstring += ">>> \n"
        docstring += ">>> parameters = {}\n"
        for k,v in cls.get_default_parameters().items():
            docstring += ">>> parameters[%r]=%r\n" % (k,v)
        docstring += ">>> \n"
        docstring += ">>> job = REGISTRY['job'][%r]()\n" % cls.type            
        docstring += ">>> job.setup(parameters)\n"
        docstring += ">>> job.run()\n"
                                   
        docstring += '\n**Job input configurators:** \n\n'
        
        for v in doclist:
            docstring += "#. **%s**\n" % v["Configurator"]
            docstring += "    #. **Description:**\n"
            docstring += "    %s\n" % v["Description"]
            docstring += "    #. **Default value:**\n"
            docstring += "    %s\n" % v["Default value"]
        
#         docstring += '+%s+%s+%s+\n'%(s[0]*'-',s[1]*'-',s[2]*'-')
#         
#         docstring += '| %s%s | %s%s | %s%s |\n' %(l[0], (s[0]-len(l[0])-2)*' ', l[1],(s[1]-len(l[1])-2)*' ', l[2],(s[2]-len(l[2])-2)*' ')            
#         
#         docstring += '+%s+%s+%s+\n'%(s[0]*'=',s[1]*'=',s[2]*'=') 
#         
#         for v in doclist:
#             p = v['Configurator']
#             df = v['Default value']
#             ds = v['Description']
#             docstring += '| %s%s | %s%s | %s%s |\n'%(p,(s[0]-len(p)-2)*' ', df,(s[1]-len(df)-2)*' ', ds,(s[2]-len(ds)-2)*' ')
#             docstring += '+%s+%s+%s+\n'%(s[0]*'-',s[1]*'-',s[2]*'-')
    
        return docstring
    
    @classmethod
    def get_default_parameters(cls):
        '''
        Return the default parameters of a configurable based on its configurators contents.
        
        :param cls: the configurable class for which documentation should be built
        :type cls: an instance of MDANSE.Framework.Configurable.Configurable derived class
        
        :return: a dictionary of the default parameters of the configurable class
        :rtype: dict
        '''
        
        configurators = getattr(cls,"configurators",{})
        
        if not isinstance(configurators,_abcoll.Mapping):
            raise ConfigurationError("Invalid type for configurators: must be a mapping-like object")
                                    
        params = collections.OrderedDict()
        for name,(typ,kwds) in configurators.items():
            cfg=REGISTRY["configurator"][typ](name, **kwds)        
            params[name] = cfg.default
            
        return params    