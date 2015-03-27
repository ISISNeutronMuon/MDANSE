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
                           
        from MDANSE.Framework.Configurables.UserDefinable import UserDefinable               
        if not isinstance(value,UserDefinable):
            raise UserDefinitionsError("Invalid value for user definition: must be a user definable object")
        
        super(UserDefinitions,self).__setitem__(item,value)
                
    def filter(self, basename,typ):
        
        return [k for k,v in self.iteritems() if (v.target==basename and v.type==typ)]

USER_DEFINITIONS = UserDefinitions()