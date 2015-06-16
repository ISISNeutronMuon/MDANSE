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
            #.. 0-value is the type of the configurator that will be used to fetch the corresponding \
            MDANSE.Framework.Configurators.IConfigurator.IConfigurator derived class from the configurators registry
            #.. 1-value is the name of the configurator that will be used as the key of the _configuration attribute.
            #.. 2-value is the dictionary of the keywords used when initializing the configurator.  
    '''
    
    settings = collections.OrderedDict()
    
    def __init__(self):
        '''
        Constructor
        '''
               
        self._configuration = {}
        
        if not isinstance(self.settings,dict):
            raise ConfigurationError("Invalid type for settings: must be a mapping-like object")

        self._configurators = {}
        for name,(typ,kwds) in self.settings.items():

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
        
        If not found return an empty dictionary. 
        """
                
        return self._configuration.setdefault(name,{})
    
    @classmethod
    def set_settings(cls, settings):
        
        cls.settings.clear()
        
        if isinstance(settings,dict):
            cls.settings.update(settings)        
    
    @property
    def configuration(self):
        '''
        Return the configuration bound to the Configurable object.
        
        :return: the configuration bound to the Configurable object.
        :rtype: dict
        '''
        
        return self._configuration
    
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
              
        settings = getattr(cls,"settings",{})
        
        if not isinstance(settings,dict):
            raise ConfigurationError("Invalid type for settings: must be a mapping-like object")
                                    
        doclist = []
        
        for name,(typ,kwds) in settings.items():
            cfg=REGISTRY["configurator"][typ](name, **kwds)
            descr = kwds.get("description","")
            descr += "\n"+str(cfg.__doc__)
            doclist.append({'Configurator' : name,'Default value' : repr(cfg.default),'Description' : descr})
                                    
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

        columns = ['Configurator','Default value','Description']
        
        sizes = [len(v) for v in columns]
        
        for v in doclist:
            sizes[0] = max(sizes[0],len(v['Configurator']))
            sizes[1] = max(sizes[1],len(v['Default value']))
            # Case of Description field: has to be splitted and parsed for inserting sphinx "|" keyword for multiline            
            v['Description'] = v['Description'].strip()
            v['Description'] = v["Description"].split("\n")
            v['Description'] = ["| " + vv.strip() for vv in v['Description']]
            sizes[2] = max(sizes[2],max([len(d) for d in v["Description"]]))

        docstring += '+%s+%s+%s+\n'% ("-"*(sizes[0]+1),"-"*(sizes[1]+1),"-"*(sizes[2]+1))
        docstring += '| %-*s| %-*s| %-*s|\n'% (sizes[0],columns[0],sizes[1],columns[1],sizes[2],columns[2])
        docstring += '+%s+%s+%s+\n'% ("="*(sizes[0]+1),"="*(sizes[1]+1),"="*(sizes[2]+1))
        
        for v in doclist:
            docstring += '| %-*s| %-*s| %-*s|\n'% (sizes[0],v["Configurator"],sizes[1],v["Default value"],sizes[2],v["Description"][0])
            if len(v["Description"]) > 1:
                for descr in v["Description"][1:]:
                    docstring += '| %-*s| %-*s| %-*s|\n'% (sizes[0],"",sizes[1],"",sizes[2],descr)
            docstring += '+%s+%s+%s+\n'% ("-"*(sizes[0]+1),"-"*(sizes[1]+1),"-"*(sizes[2]+1))
            
        docstring += "\n"
        
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
        
        settings = getattr(cls,"settings",{})
        
        if not isinstance(settings,dict):
            raise ConfigurationError("Invalid type for settings: must be a mapping-like object")
                                    
        params = collections.OrderedDict()
        for name,(typ,kwds) in settings.items():
            cfg=REGISTRY["configurator"][typ](name, **kwds)        
            params[name] = cfg.default
            
        return params
    
    @property
    def configurators(self):
        '''
        Return the configurator objects of this Configurable object
        
        :return: a mapping between the name of the configurator object and its corresponding IConfigurator instance
        :rtype: dict 
        '''
        
        return self._configurators