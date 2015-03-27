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

import time

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error

class UserDefinableError(Error):
    pass

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

        