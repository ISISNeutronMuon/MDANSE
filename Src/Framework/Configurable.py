# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurable.py
# @brief     Implements module/class/test Configurable
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

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
    
    def __init__(self,settings=None):
        '''
        Constructor
        '''
               
        self._configuration = collections.OrderedDict()
                                     
        self._configured=False
        
        self._info = []
        
        if settings is not None:
            self.set_settings(settings)
        
    def build_configuration(self):
        
        self._configuration.clear()

        for name,(typ,kwds) in self.settings.items():
            
            try:
                self._configuration[name] = REGISTRY["configurator"][typ](name, configurable=self,**kwds)
            # Any kind of error has to be caught
            except:
                raise ConfigurationError("Invalid type for %r configurator" % name)
            
    def set_settings(self,settings):
        
        self.settings = settings
        
        self.build_configuration()
                
    def __getitem__(self, name):
        """
        Returns a configuration item given its name.
        
        :param name: the name of the configuration item
        :type name: str 
        
        If not found return an empty dictionary. 
        """
                
        return self._configuration.setdefault(name,{})
        
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
                
        self._configured=False
        
        self.build_configuration()
                                
        # If no configurator has to be configured, just return
        if not self._configuration:
            self._configured=True
            return
        
        if isinstance(parameters,dict):
            # Loop over the configuration items          
            for k,v in self._configuration.items():
                # If no input parameter has been set for this item, use its default value.
                if not parameters.has_key(k):
                    parameters[k] = v.default
        else:
            raise ConfigurationError("Invalid type for configuration parameters")             
                        
        toBeConfigured = set(self._configuration.keys())
        configured = set()
                
        while toBeConfigured != configured:
                        
            progress = False

            for name,conf in self._configuration.items():
                                                                                
                if name in configured:
                    continue
                
                if conf.check_dependencies(configured):
                                                            
                    conf.configure(parameters[name])
                    
                    conf.set_configured(True)
                    
                    self._configuration[name]=conf
                    
                    self._info.append(conf.get_information())
                                                            
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
        
        if not self._info:
            return "No information available yet."
                    
        return "\n".join(self._info)
    
    @classmethod
    def build_doc(cls):
        '''
        Return the documentation about a configurable class based on its configurators contents.
        
        :param cls: the configurable class for which documentation should be built
        :type cls: an instance of MDANSE.Framework.Configurable.Configurable derived class
        
        :return: the documentation about the configurable class
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
                                    
        docstring = ":Example:\n\n"
        docstring += ">>> from MDANSE import REGISTRY\n"
        docstring += ">>> \n"
        docstring += ">>> parameters = {}\n"
        for k,v in cls.get_default_parameters().items():
            docstring += ">>> parameters[%r]=%r\n" % (k,v)
        docstring += ">>> \n"
        docstring += ">>> job = REGISTRY['job'][%r]()\n" % cls._type            
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
            try:
                cfg=REGISTRY["configurator"][typ](name, **kwds)
            except KeyError:
                raise KeyError(typ, REGISTRY["configurator"])
            params[name] = cfg.default
            
        return params
