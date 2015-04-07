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

import time

class UserDefinable(dict):
    '''
    Base class for user definable objects. User definable objects are objects used in MDANSE for 
    storing information that can be reused later when setting up jobs (e.g. k-vectors defintion, 
    atom selection ...). A user definable object is a dictionary with a predefined set of keys that 
    depends on the user definable object. Object serialization is the underlying mechanism used to 
    save those objets and is done using cPickle module. 
    '''

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

    @property
    def creationTime(self):
        
        return self._creationTime
    
    @property
    def definition(self):
        
        return self._definition
        
    def __str__(self):
        '''
        Return the informal representation of a user definable object
        '''
        
        if not self._definition:
            return "Not yet defined"
        
        info = ["Created on: %s\n" % self._creationTime] + ["%s:\n%s\n" % (k,v) for k,v in self._definition.iteritems()] 
        
        return "".join(info)
            