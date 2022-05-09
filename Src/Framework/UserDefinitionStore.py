# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/UserDefinitionStore.py
# @brief     Implements module/class/test UserDefinitionStore
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import cPickle
import os

from MDANSE import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton

class UserDefinitionStoreError(Error):
    pass


class UserDefinitionStore(object):
    '''
    This class is used to register, save and delete MDANSE user definitions (a.k.a. UD).
    
    Basically, user definitions are used to keep track of definitions made on a given target. The target can 
    be a file or any kind of object that has to be associated with the user definitions.
    This definitions can be selections of atoms, Q vectors definitions, axis definitions ... The 
    user definitions are loaded when MDANSE starts through a cPickle file that will store these definitions.    
    '''
    
    __metaclass__ = Singleton
        
    UD_PATH = os.path.join(PLATFORM.application_directory(),"user_definitions.ud")
    
    def __init__(self):
        
        self._definitions = {}
                
        self.load()
        
    @property
    def definitions(self):
        
        return self._definitions                                               
                       
    def load(self):
        '''
        Load the user definitions.
        '''

        if not os.path.exists(UserDefinitionStore.UD_PATH):
            return

        # Try to open the UD file.
        try:
            f = open(UserDefinitionStore.UD_PATH, "rb")
            UD = cPickle.load(f)
  
        # If for whatever reason the pickle file loading failed do not even try to restore it
        except:
            return
          
        else:
            self._definitions.update(UD)
            f.close()
                                    
    def save(self):
        '''
        Save the user definitions.
        
        :param path: the path of the user definitions file.
        :type path: str
        '''
                    
        try:                        
            f = open(UserDefinitionStore.UD_PATH, "wb")
        except IOError:
            return
        else:
            cPickle.dump(self._definitions, f, protocol=2)
            f.close()
                                    
    def remove_definition(self,*defs):
        
        if self.has_definition(*defs):
            defs = list(defs)
            locald = self._definitions
            while defs:
                val = defs.pop(0)            
                if len(defs)==0:
                    del locald[val]
                    return
                locald = locald[val]
                                                   
    def set_definition(self, target, section, name, value):
                        
        if self.has_definition(target, section, name):
            raise UserDefinitionStoreError('Item %s is already registered as an user definition. You must delete it before setting it.' % (target,section,name))

        self._definitions.setdefault(target,{}).setdefault(section,{})[name] = value                                          

    def filter(self,*defs):
        
        d = self.get_definition(*defs)
        if d is None:
            return [] 
        
        return d.keys()

    def get_definition(self,*defs):
        '''
        Returns a user definition given its target, category and its name.
                
        :return: the user definition if it found or None otherwise
        :rtype: any
        '''
        
        locald = self._definitions
        
        defs = list(defs)    
        while defs:
        
            val = defs.pop(0)            
            locald = locald.get(val,None)
            
            if locald is None:
                return None
                
            if not defs:
                break
                
            if not isinstance(locald,dict):
                return None
                
        return locald
            
    def has_definition(self,*defs):
        
        locald = self._definitions
        
        defs = list(defs)    
        while defs:
        
            val = defs.pop(0)            
            locald = locald.get(val,None)
            
            if locald is None:
                return False
                
            if not defs:
                break
                
            if not isinstance(locald,dict):
                return False
                
        return True
        
UD_STORE = UserDefinitionStore()
