import cPickle
import os

from MDANSE import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton

class UserDefinitionsStoreError(Error):
    pass

class UnicodeDict(dict):
    '''
    This class implements a specification of a python dict that converts automatically any string key in unicode.
    
    This kind of object is useful when exposed to package such as wxPython that implements string as unicode.
    '''

    def __contains__(self, item):
        '''
        Returns True if a given key is found in the dictionary.
        
        If the key is basestring then it will be searched as a unicode string. 
        
        :param item: the key to search in the dictionary
        :type item: any valid key
        '''

        if isinstance(item,basestring):
            return super(UnicodeDict,self).__contains__(unicode(item))

        else:
            return super(UnicodeDict,self).__contains__(item)

    def __setitem__(self, item, value):
        '''
        Sets the value of a given key.
        
        If the key is a basestring, it will be converted internally in a unicode objet.
        
        :param item: the key to set in the dictionary
        :type item: any valid key
        :param value: the value to associate with the key
        :type value: any python object
        '''

        if isinstance(item,basestring):
            dict.__setitem__(self, unicode(item),value)

        else:
            raise KeyError("Invalid key type")

class UserDefinitionsStore(UnicodeDict):
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
        
        UnicodeDict.__init__(self)
        
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
            UnicodeDict.update(self,UD)
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
                                    
    def __getitem__(self, item):
        '''
        Returns a user definition given its target, category and its name.
                
        :return: the user definition if it found or None otherwise
        :rtype: a MDANSE.Framework.UserDefinitions.IUserDefinition.IUserDefinition derived class
        '''

        try:
            target, typ, name = item
        except ValueError:
            raise UserDefinitionsStoreError("Invalid key value: must be a 3-tuple")
            
        try:
            ud = UnicodeDict.__getitem__(name)
            
        except (KeyError,TypeError):
            raise UserDefinitionsStoreError('The item %r could not be found' % str(name))
            
        else:
            
            if ud.target != target:
                raise UserDefinitionsStoreError('Target mismatch between %r and %r' % (target,ud.target))
        
            if ud.type != typ:
                raise UserDefinitionsStoreError('Type mismatch between %r and %r' % (typ,ud.type))
            
            return ud
                                                   
    def __setitem__(self, item, value):
                                          
        
        UnicodeDict.__setitem__(self, item,value)

    def filter(self,target,typ):
        
        return [k for k,v in self.iteritems() if (v.target==target and v.type==typ)]
        
UD_STORE = UserDefinitionsStore()
