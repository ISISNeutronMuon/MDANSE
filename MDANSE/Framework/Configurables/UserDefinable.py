'''
MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
------------------------------------------------------------------------------------------
Copyright (C)
2015- Eric C. Pellegrini Institut Laue-Langevin
BP 156
6, rue Jules Horowitz
38042 Grenoble Cedex 9
France
pellegrini[at]ill.fr

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 
Created on Mar 23, 2015

@author: pellegrini
'''

import cPickle
import os
import time

from MDANSE import PLATFORM, REGISTRY
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton

class UserDefinableError(Error):
    pass

class UserDefinitionsError(Error):
    pass

class UnicodeDict(dict):

    def __contains__(self, item):

        if isinstance(item,basestring):
            return super(UnicodeDict,self).__contains__(unicode(item))

        else:
            return super(UnicodeDict,self).__contains__(item)

    def __setitem__(self, item, value):

        if isinstance(item,basestring):

            super(UnicodeDict,self).__setitem__(unicode(item),value)

        else:
            super(UnicodeDict,self).__setitem__(item,value)

class UserDefinable(dict):
    '''
    Base class for user definable objects. User definable objects are objects used in nmoldyn for 
    storing information that can be reused later when setting up jobs (e.g. k-vectors defintion, 
    atom selection ...). A user definable object is a dictionary with a predefined set of keys that 
    depends on the user definable object. Object serialization is the underlying mechanism used to 
    save those objets and is done using cPickle module. 
    '''

    # Any user definable object will be registered at nmoldyn startup.
    __metaclass__ = REGISTRY

    # The base class has no type (hence it will not be registered)    
    type = "user-definable"
    
    # The base class has no predefined set keywords
    _keywords = []
    
    def __init__(self, target, **kwargs):
        '''
        The constructor
        '''
        
        self._target = target
        
        self._creationTime = time.ctime()

        self._keywords = self._keywords
        
        for k in self._keywords:
            try:
                self[k] = kwargs[k]
            except KeyError:
                raise UserDefinableError("Incomplete user definable object: missing %r key" % k)
                                                                                
    @property
    def target(self):
        
        return self._target

    @property
    def keywords(self):
        
        return self._keywords

    @property
    def creationTime(self):
        
        return self._creationTime

    def __setitem__(self, item,value):

        # It is not possible to set directly a key of a user definable object
        if item in self._keywords:
            super(UserDefinable,self).__setitem__(item, value)
        
    def __str__(self):
        '''
        Return the informal representation of a user definable object
        '''
        
        info = ["Created on: %s\n" % self.creationTime] + ["%s:\n%s\n" % (k,self[k]) for k in self._keywords] 
        
        return "".join(info)
    
class DefineAtomSelection(UserDefinable):    
    '''
    The user definable object used for storing atom selection.
    '''
    
    type = "atom_selection"
    
    _keywords = ['expression','indexes']
        
class DefineAtomTransmutation(UserDefinable):    
    '''
    The user definable object used for storing atom transmutation.
    '''

    type = "atom_transmutation"
    
    _keywords = ['expression','indexes','element']


class DefineQVectors(UserDefinable):    
    '''
    The user definable object used for storing k vectors.
    '''

    type = "q_vectors"
    
    _keywords = ['generator', 'parameters', 'q_vectors', 'is_lattice']


class DefineAxisSelection(UserDefinable):    
    '''
    The user definable object used for storing axis selection.
    '''

    type = "axis_selection"
    
    _keywords = ['molecule','endpoint1','endpoint2']


class DefineBasisSelection(UserDefinable):    
    '''
    The user definable object used for storing basis selection.
    '''

    type = "basis_selection"
    
    _keywords = ['molecule','origin','x_axis','y_axis']

        
class UserDefinitions(UnicodeDict):
    '''
    This class is used to register, save and delete UD (UD for User Definition).
    
    Basically a UD file is a cPickle file that must store a dictionary of definitions related to a target file. 
    The target file can be any kind of file on which some extra information should be attached.
    For instance, if the target file is a trajectory, the UD file may contains selected atoms, 
    center or axis that can be used for further analysis in new nMolDyn sessions.  
    '''
    
    __metaclass__ = Singleton
        
    _path = os.path.join(PLATFORM.application_directory(),"nmoldyn_user_definitions.ud")                                                      
                       
    def restore_state(self):
        
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
        
        if path is None:
            path = self._path
            
        try:                        
            f = open(path, "wb")
        except IOError:
            return
        else:
            cPickle.dump(self, f, protocol=2)
            f.close()
                        
    def check_and_get(self, target, typ, name):
        
        try:
            ud = self[name]
            
        except (KeyError,TypeError):
            raise UserDefinitionsError('The item %r is not registered in the user definition' % str(name))
            
        else:
            
            if ud.target != target:
                raise UserDefinitionsError('Target mismatch between %r and %r' % (target,ud.target))
        
            if ud.type != typ:
                raise UserDefinitionsError('Type mismatch between %r and %r' % (typ,ud.type))
            
            return ud
                        
    def __setitem__(self, item, value):
                                          
        if not isinstance(value,UserDefinable):
            raise UserDefinitionsError("Invalid value for user definition: must be a user definable object")
        
        super(UserDefinitions,self).__setitem__(item,value)
                
    def filter(self, basename,typ):
        
        return [k for k,v in self.iteritems() if (v.target==basename and v.type==typ)]

USER_DEFINITIONS = UserDefinitions()