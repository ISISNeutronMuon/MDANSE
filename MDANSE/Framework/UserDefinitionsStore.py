import cPickle
import os

from MDANSE import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton
from MDANSE.Framework.UserDefinitions.IUserDefinition import IUserDefinition

class UserDefinitionsStoreError(Error):
    pass


class UserDefinitionsStore(dict):
    '''
    This class is used to register, save and delete MDANSE user definitions (a.k.a. UD).
    
    Basically, user definitions are used to keep track of definitions made on a given target. The target can 
    be a file or any kind of object that has to be associated with the user definitions.
    This definitions can be selections of atoms, Q vectors definitions, axis definitions ... The 
    user definitions are loaded when MDANSE starts through a cPickle file that will store these definitions.
    
    They are stored internally as MDANSE.Framework.UserDefinition.IUserDefinition derived objects in a nested 
    dictionary whose primary key is the target name, secondary key is the category of the user definition and 
    tertiary key is the name of the user definition.  
    '''
    
    __metaclass__ = Singleton
        
    UD_PATH = os.path.join(PLATFORM.application_directory(),"user_definitions.ud")
    
    def __init__(self):
        
        dict.__init__(self)
        
        self.load()                                               
                       
    def load(self):
        '''
        Load the user definitions.
        '''

        if not os.path.exists(UserDefinitionsStore.UD_PATH):
            return

        # Try to open the UD file.
        try:
            f = open(UserDefinitionsStore.UD_PATH, "rb")
            UD = cPickle.load(f)
  
        # If for whatever reason the pickle file loading failed do not even try to restore it
        except:
            return
          
        else:
            self.update(UD)
            f.close()
                        
    def save(self):
        '''
        Save the user definitions.
        
        :param path: the path of the user definitions file.
        :type path: str
        '''
                    
        try:                        
            f = open(UserDefinitionsStore.UD_PATH, "wb")
        except IOError:
            return
        else:
            cPickle.dump(self, f, protocol=2)
            f.close()
                                    
    def get_definition(self, target, section, name):
        '''
        Returns a user definition given its target, category and its name.
                
        :return: the user definition if it found or None otherwise
        :rtype: a MDANSE.Framework.UserDefinitions.IUserDefinition.IUserDefinition derived class
        '''
            
        if not self.has_definition(target,section,name):
            raise UserDefinitionsStoreError('The item %r could not be found' % (target,section,name))

        ud = self[target][section][name]
                        
        if ud.target != target:
            raise UserDefinitionsStoreError('Target mismatch between %r and %r' % (target,ud.target))
    
        if ud.type != section:
            raise UserDefinitionsStoreError('Type mismatch between %r and %r' % (section,ud.type))
            
        return ud
        
    def remove_definition(self,target,section,name):
        
        if self.has_definition(target, section, name):
            del self[target][section][name]
                                                   
    def set_definition(self, target, section, name, value):
                
        if not isinstance(value,IUserDefinition):
            raise UserDefinitionsStore('The input value is not a User definition.')
        
        if self.has_definition(target, section, name):
            raise UserDefinitionsStoreError('Item %s is already registered as an user definition. You must delete it before setting it.' % (target,section,name))

        self.setdefault(target,{}).setdefault(section,{})[name] = value                                          

    def filter(self,target,section):
        
        return self.get(target,{}).get(section,{}).keys()
            
    def has_definition(self,target,section,name):
        
        if not self.has_key(target):
            return False
                
        if not self[target].has_key(section):
            return False
        
        return self[target][section].has_key(name)
        
UD_STORE = UserDefinitionsStore()
