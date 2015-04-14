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
Created on Mar 27, 2015

@author: pellegrini
'''

import cPickle
import os
import time

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton

class UserDefinitionError(Error):
    pass

class IUserDefinition(object):
    '''
    Base class for user definable objects. User definable objects are objects used in MDANSE for 
    storing information that can be reused later when setting up jobs (e.g. k-vectors defintion, 
    atom selection ...). A user definable object is a dictionary with a predefined set of keys that 
    depends on the user definable object. Object serialization is the underlying mechanism used to 
    save those objets and is done using cPickle module. 
    '''
    
    # Any user definable object will be registered at MDANSE startup.
    __metaclass__ = REGISTRY

    # The base class has no type (hence it will not be registered)    
    type = "user_definition"
    
    # The base class has no predefined set keywords
    _keywords = []
    
    def __init__(self, target):
        '''
        The constructor
        '''
        
        self._target = target
        
        self._creationTime = time.ctime()
        
        self._definition = {}
                                                                                        
    @property
    def target(self):
        
        return self._target

    @classmethod
    def keywords(self):
        
        return self._keywords

    @property
    def creationTime(self):
        
        return self._creationTime

    def __setitem__(self, keyword, value):

        if keyword in self._keywords:
            self._definition[keyword] = value
        
    def __str__(self):
        '''
        Return the informal representation of a user definable object
        '''
        
        info = ["Created on: %s\n" % self.creationTime] + ["%s:\n%s\n" % (k,self._definition[k]) for k in self._keywords] 
        
        return "".join(info)
            
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

class UserDefinitionStore(UnicodeDict):
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
            self.update(UD)
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
            raise UserDefinitionError("Invalid key value: must be a 3-tuple")
            
        try:
            ud = self[name]
            
        except (KeyError,TypeError):
            raise UserDefinitionError('The item %r could not be found' % str(name))
            
        else:
            
            if ud.target != target:
                raise UserDefinitionError('Target mismatch between %r and %r' % (target,ud.target))
        
            if ud.type != typ:
                raise UserDefinitionError('Type mismatch between %r and %r' % (typ,ud.type))
            
            return ud
                                                   
    def __setitem__(self, item, value):
                                          
        if not isinstance(value,IUserDefinition):
            raise IUserDefinition("Invalid value for user definition: must be a user definable object")
        
        UnicodeDict.__setitem__(self, item,value)

    def filter(self,target,typ):
        
        return [k for k,v in self.iteritems() if (v.target==target and v.type==typ)]
        
UD_STORE = UserDefinitionStore()            