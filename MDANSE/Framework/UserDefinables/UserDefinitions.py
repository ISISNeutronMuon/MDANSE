#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#aoun[at]ill.fr
#goret[at]ill.fr
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
Created on Mar 26, 2015

@author: pellegrini
'''

import cPickle
import os

from MDANSE import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton

class UserDefinitionsError(Error):
    '''
    This class handles exception related to UserDefinitions
    '''
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

            super(UnicodeDict,self).__setitem__(unicode(item),value)

        else:
            super(UnicodeDict,self).__setitem__(item,value)

class UserDefinitions(object):
    '''
    This class is used to register, save and delete MDANSE user definitions (a.k.a. UD).
    
    Basically, user definitions are used to keep track of definitions made on a given target. The target can 
    be a file or any kind of object that has to be associated with the user definitions.
    This definitions can be selections of atoms, Q vectors definitions, axis definitions ... The 
    user definitions are loaded when MDANSE starts through a cPickle file that will store these definitions.
    
    They are stored internally as MDANSE.Framework.UserDefinables.IUserDefinable derived objects in a nested 
    dictionary whose primary key is the target name, secondary key is the category of the user definition and 
    tertiary key is the name of the user definition.  
    '''
    
    __metaclass__ = Singleton
        
    _path = os.path.join(PLATFORM.application_directory(),"user_definitions.ud")                                                      
                       
    def load(self):
        '''
        Load the user definitions.
        '''
        
        if not os.path.exists(UserDefinitions._path):
            return

        # Try to open the UD file.
        try:
            f = open(UserDefinitions._path, "rb")
            UD = cPickle.load(f)        

        # If for whatever reason the pickle file loading failed do not even try to restore it
        except:
            return
        
        else:
            self.update(UD)
            f.close()
            
    def save(self, path=None):
        '''
        Save the user definitions.
        
        :param path: the path of the user definitions file.
        :type path: str
        '''
        
        if path is None:
            path = self._path
            
        try:                        
            f = open(path, "wb")
        except IOError:
            return
        else:
            cPickle.dump(self, f, protocol=2)
            f.close()
                                    
    def get(self, target, category, name):
        '''
        Returns a user definition given its target, category and its name.
        
        :param target: the target related to the user definition
        :type target: str
        :param category: the category of the user definition
        :type category: str
        :param name: the name of the user definition
        :type name: str
        
        :return: the user definition if it found or None otherwise
        :rtype: a MDANSE.Framework.UserDefinables.UserDefinables.IUserDefinable derived class
        '''
        
        try:
            ud = self[target][category][name]            
        
        # Any kind of error should be caught here.    
        except:
            return None
            
        else:                
            if ud.target != target:
                raise UserDefinitionsError('Target mismatch between %r and %r' % (target,ud.target))
        
            if ud.type != category:
                raise UserDefinitionsError('Type mismatch between %r and %r' % (category,ud.type))

            return ud
                                           
    def set(self, target, category, name, ud):
        '''
        Sets a new user definition.
        
        :param target: the name of the user definition to set
        :type target: str
        :param category: the category of the user definition to set
        :type category: str
        :param name: the name of the user definition to set
        :type name: str
        :param ud: the user definition to set
        :type ud: MDANSE.Framework.UserDefinables.IUserDefinable derived object
        '''

        from MDANSE.Framework.UserDefinables.IUserDefinable import IUserDefinable               
        if not isinstance(ud,IUserDefinable):
            raise UserDefinitionsError("Invalid user definition: must be a user definable object")

        targets = self.setdefault(unicode(target),{})
        
        categories = targets.setdefault(unicode(category),{})

        categories[unicode(name)] = ud
                
USER_DEFINITIONS = UserDefinitions()