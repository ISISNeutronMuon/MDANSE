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
Created on Mar 30, 2015

@author: pellegrini
'''

import abc
import collections
import ConfigParser
import os

from MDANSE.Core.Platform import PLATFORM, PlatformError
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton

class PreferencesError(Error):
    '''
    This class handles the errors that occurs in Preferences.
    '''
    
    pass

class PreferencesItem(object):
    '''
    This is the base class for defining a preferences item.
    
    A preferences item implements is a light object used to check preferences before setting them
    but also classify preferences according to their section for a further use in MDANSE GUI.
    '''
    
    __metaclass__ = abc.ABCMeta

    def __init__(self, name, section, default, *args, **kwargs):
        '''
        Constructor a new prferences item.
        
        :param name: the name of the preference item
        :type name: str 
        :param section: the section of the preferences item
        :type section: str
        :param default: the default value for the preferences item
        :type default: str
        '''
        
        self._name = name
        
        self._section = section
        
        self._default = default
        
        self._value = self._default
                
    @property
    def default(self):
        '''
        Returns the default value of the preferences item.
        
        :return: the default value of the preferences item
        :rtype: str
        '''
        
        return self._default
    
    def get_default(self):
        '''
        Returns the default value of the preferences item.
        
        :return: the default value of the preferences item
        :rtype: str
        '''
        
        return self._default
        
    @property
    def name(self):
        '''
        Returns the name of the preferences item.
        
        :return: the name of the preferences item
        :rtype: str
        '''

        return self._name

    def get_name(self):
        '''
        Returns the name of the preferences item.
        
        :return: the name of the preferences item
        :rtype: str
        '''

        return self._name
        
    @property
    def section(self):
        '''
        Returns the section of the preferences item.
        
        :return: the section of the preferences item
        :rtype: str
        '''

        return self._section
    
    def get_section(self):
        '''
        Returns the section of the preferences item.
        
        :return: the section of the preferences item
        :rtype: str
        '''
        
        return self._section
    
    def reset(self):
        '''
        Reset the preferences item to its default value
        '''
        
        self._value = self._default
        
    @property
    def value(self):
        '''
        Returns the value of the preferences item.
        
        :return: the value of the preferences item
        :rtype: str
        '''

        return self._value

    def get_value(self):
        '''
        Returns the value of the preferences item.
        
        :return: the value of the preferences item
        :rtype: str
        '''

        return self._value

    @abc.abstractmethod
    def set_value(self,value):
        '''
        Set the value of the preferences item.
        
        :param value: the value of the preferences item
        :type value: str
        '''
        
        pass

class InputDirectory(PreferencesItem):
    '''
    This class implements a preferences item that handles an input directory.
    
    When set to a given input directory, if this one does not exists, it will be be created.
    '''
    
    type = "input_directory"


    def set_value(self, value):
        '''
        Set the value of the input directory preferences item.
        
        :param value: the input directory
        :type value: str
        '''
        
        value = PLATFORM.get_path(value)
        
        try:
            PLATFORM.create_directory(value)
        except PlatformError:
            raise PreferencesError('Error when setting input directory %r' % value)
        
        self._value = value

class LoggingLevel(PreferencesItem):
    
    type = "logging_level"
    
    LOGGING_LEVELS = ["debug","info","warning","error","critical","fatal"]
    
    def set_value(self, value):
        '''
        Set the value of the logging level preferences item.
        
        :param value: the logging level
        :type value: str
        '''
                
        value = value.lower()
        
        if not value in LoggingLevel.LOGGING_LEVELS:
            raise PreferencesError("Invalid logging level")
                
        self._value = value
                
class Preferences(collections.OrderedDict):
    '''
    This class implements the MDANSE preferences.
    
    Preferences are defined using the ConfigParser python module that allows to read and write 
    preferences stored in a formatted INI file (RFC822).
    '''
    
    __metaclass__ = Singleton
    
    def __init__(self):
        '''
        Constructs the preferences
        '''
        
        collections.OrderedDict.__init__(self)
        
        self["working_directory"] = InputDirectory("working_directory", "paths", PLATFORM.home_directory())
        self["macros_directory"] = InputDirectory("macros_directory", "paths", os.path.join(PLATFORM.home_directory(), "mdanse_macros"))
                
        self._parser = ConfigParser.ConfigParser()

        for s in self.values():
            try:
                self._parser.add_section(s.section)
            except ConfigParser.DuplicateSectionError:
                pass
                                                                    
        # Overwrite the default preferences with the user defined loaded ones.
        try:
            self.load()
        except PreferencesError:
            pass
        
    @property
    def parser(self):
        '''
        Returns the configuration parser object used to serialize the preferences.
        
        :return: the configuration parser bound to the preferences
        :rtype: ConfigParser.ConfigParser
        '''
        return self._parser
    
    def __getitem__(self, item):
        '''
        Get the value of a selected preferences item.
        
        :param item: the preferences item
        :type item: str

        :return: the values of the preferences item.
        :rtype: str
        '''
        
        try:
            value = self[item].value
        except KeyError:
            raise PreferencesError("The preferences item %r is not valid" % item)
        else:
            return value
                
    def __setitem__(self, item, value):
        '''
        Set the value of a preferences item.
        
        :param item: the preferences item
        :type item: str
        
        :param value: the value to set for the preferences item.
        :type value: any
        '''
        
        if not self.has_key(item):
            return

        try:
            self[item].value = value

        except KeyError:
            raise PreferencesError("The preferences item %r is not valid" % item)
        
    def load(self):
        '''
        Load the preferences from a preferences file.
        '''
                    
        path = PLATFORM.preferences_file()

        if not isinstance(path,basestring):
            raise PreferencesError("Invalid type for preferences filename: %s" % path)
        
        if not os.path.exists(path):
            raise PreferencesError("The preferences files %s does not exists. nMolDyn will use the default preferences." % path)
                
        try:
            # Read the preferences and overwrites the nmoldyn default preferences.
            self._parser.read(path)
        except ConfigParser.ParsingError as e:
            raise PreferencesError(e)
        
        for s in self._parser.sections():
            for k, v in self._parser.items(s):
                self[k] = v 
                         
    def save(self):
        '''
        Save the preferences to a file.        
        '''
        
        path = PLATFORM.preferences_file()
            
        try:
            f = open(path, "w")
        except (IOError,TypeError) as e:
            raise PreferencesError(e)

        for v in self.values():
            self._parser.set(v.section,v.name,v.value)
                
        # Write the preferences.
        self._parser.write(f)
        
        # Closes the preferences file.
        f.close()
        
PREFERENCES = Preferences()