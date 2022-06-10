# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Data/ElementsDatabase.py
# @brief     Implements module/class/test ElementsDatabase
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import copy
import csv
import numbers
import os
import sys
import xml.etree.ElementTree as etree

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.Error import Error
from MDANSE.Core.Singleton import Singleton

class ElementsDatabaseError(Error):
    '''
    This class handles the exceptions related to ElementsDatabase
    '''
    pass

def indent(elem, level=0):
    """
    Produces a pretty indented XML tree.
    
    :param elem: the element tree to indent.
    :type elem: xml.etree.ElementTree.Element
    
    :param level: the level of indentation
    :type level: int
    """
    
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

class ElementsDatabase(object):
    '''
    This class implements the elements database of MDANSE.
    
    Storing all the chemical elements (and their isotopes) is necessary for any analysis based 
    on molecular dynamics trajectories. Indeed, most of them use atomic physico-chemical 
    properties such as atomic weight, neutron scattering length, atomic radius ...
    
    The first time the user launches MDANSE, the database is initially loaded though a csv file stored 
    in a MDANSE defsault database path. Once modified, the user can save the database to a new csv file that
    will be stored in its MDANSE application directory (OS dependent). This is this file that will be loaded 
    thereafter when starting MDANSE again. 
    
    Once loaded, the database is stored internally in a nested dictionary whose primary keys are the name of the 
    elements and secondary keys the names of its associated properties.
        
    :Example:
    
    >>> # Import the database
    >>> from MDANSE import ELEMENTS
    >>> 
    >>> # Fetch the hydrogen natural element --> get a deep-copy of the its properties
    >>> hydrogen = ELEMENTS["H"]
    >>> 
    >>> # Fetch the hydrogen H[1] isotope --> get a deep-copy of the its properties
    >>> h1 = ELEMENTS["H[1]"]
    >>> 
    >>> # Return a list of the properties stored in the database
    >>> l = ELEMENTS.get_properties()
    >>> 
    >>> # Return the atomic weight of U[235] element
    >>> w = ELEMENTS["U[235]","atomic_weight"]
    >>> 
    >>> # Returns the elements stored currently in the database
    >>> elements = ELEMENTS.get_elements()
    '''
    
    __metaclass__ = Singleton
    
    _DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__),"elements_database.csv")
    
    # The user path
    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), "elements_database.csv")
    
    # The python types supported by the database
    _TYPES = {"str" : str, "int" : int, "float" : float}

    def __init__(self):
        '''
        Constructor
        '''

        self._data = collections.OrderedDict()

        self._properties = collections.OrderedDict()

        self._reset()

        # Load the user database. If any problem occurs while loading it, loads the default one
        self._load(ElementsDatabase._USER_DATABASE)
                
    def __contains__(self,ename):
        '''
        Return True if the database contains a given element.
        
        :param ename: the name of the element to search in the database
        :type ename: str
        
        :return: True if the database contains a given element
        :rtype: bool
        '''
        
        ename = ename.lower()

        return ename in self._data

    def __getitem__(self,item):
        '''
        Return an entry of the database.
        
        If the item is a basestring, then the return value will be the list of properties 
        related to element of the databse base that matches this item. If the item is a 
        2-tuple then the return value will the property of the databse whose element and property match
        respectively the first and second elements of the tuple.
        
        :param item: the item to get from the database
        :type item: str or tuple
        '''

        if isinstance(item,basestring):
            item = item.lower()
            return copy.deepcopy(self._data[item])

        try:            
            ename,pname = item
            ename = ename.lower()
            pname = pname.lower()
        except ValueError:
            raise ElementsDatabaseError("Invalid database entry")
                
        try:
            element = self._data[ename]
        except KeyError:
            raise ElementsDatabaseError("The element %r is not registered in the database." % ename)
        else:
            try:
                return element[pname]
            except KeyError:
                raise ElementsDatabaseError("The property %r is not registered in the database." % pname)

    def __setitem__(self,item,value):
        '''
        Set an entry of the database.
        
        The item must be a 2-tuple whose elements are respectively the name of the element and the name of the property.
        
        :param item: the entry to be set
        :type item: 2-tuple
        
        :param value: the value to set.
        :type: one of 'str', 'int', 'float'
        '''

        try:            
            ename,pname = item
            ename = ename.lower()
            pname = pname.lower()
        except ValueError:
            raise ElementsDatabaseError("Invalid database entry")
        
        # Any error has to be caught here
        try:
            self._data[ename][pname] = self._properties[pname](value)
        except:
            raise ElementsDatabaseError("Invalid value for database entry")

    def __iter__(self):
        '''
        Return a generator over the elements stored in the database.
        '''
                        
        for v in self._data.itervalues():
            yield copy.deepcopy(v)
                
    def _export_csv(self, filename, delimiter=',', lineterminator='\n', restval='undefined'):
        '''
        Export the database in CSV file format.
        
        :param filename: the path of the CSV file in which the database will be exported 
        :type filename: str
        :param delimiter: the CSV delimiter
        :type delimiter: str
        :param lineterminator: the CSV line terminator
        :type lineterminator: str
        :param restval: the string used for missing values 
        :type restval: str
        '''

        f = open(filename, 'w')

        propNames = ["id"] + list(self._properties.keys())
                
        # Return a csv writer object.            
        databaseWriter = csv.DictWriter(f, propNames, delimiter=delimiter, lineterminator=lineterminator, restval=restval)
        databaseWriter.writeheader()
        
        rtypes = dict([(v,k) for k,v in ElementsDatabase._TYPES.items()])
        ptypes = {'id':'type'}
        ptypes.update(dict([(k,rtypes[v]) for k,v in self._properties.items()]))
        databaseWriter.writerow(ptypes)
        for ename, props in self._data.items():
            p = {"id":ename}
            p.update(dict([(pname,props.get(pname,prop())) for pname,prop in self._properties.items()]))
            databaseWriter.writerow(p)
                                                 
        # Closes the csv file. 
        f.close()

    def _export_xml(self, filename):
        '''
        Export the database in XML file format.
        
        :param filename: the path of the XML file in which the database will be exported 
        :type filename: str
        '''

        f = open(filename, 'w')      
                                
        # Create the ElementTree root node.                         
        root = etree.Element('elements_database')
    
        # Write all the elements.
        for ename,props in self._data.iteritems():
                        
            # Create a XML node for the element.
            node = etree.Element('element')
            
            node.attrib["id"] = ename
                        
            for pname,prop in self._properties.iteritems():
                        
                # Creates a XML node for the property.      
                subnode = etree.Element(pname)
                # Set its value with the element current property.
                subnode.text = str(props.get(pname,prop()))
                # And append the property node to the current element node.
                node.append(subnode)
                
            # Append the element node to the root node.
            root.append(node)
            
        # Produce a nice-looking indented output in the XML file.
        indent(root)
        
        etree.ElementTree(root).write(f)

        f.close()

    # These are the currently supported export formats for the database
    exporters = {"csv" : _export_csv, "xml" : _export_xml}
            
    def _load(self, filename):
        '''
        Load the elements database
        
        :param filename: the path of the elements database to be loaded
        :type filename: str
        '''

        # Try to open the input file
        try:
            f = open(filename, "r")
        
            # Open a CSV reader object from the input file object
            reader = csv.reader(f, delimiter=',')
            
            line = ["#"]
            while line[0].strip().startswith("#"):
                line = reader.next()
                
            properties = line        
            if properties.pop(0).lower() != "id":
                return
            
            for pname,ptype in zip(properties,reader.next()[1:]):
                
                pname = pname.lower()
                
                if pname in self._properties:
                    continue
                
                self._properties[pname] = self._TYPES[ptype]
                                        
            # Reads the next lines of the CSV that correspond to the database entries
            for r in reader:
                ename = r.pop(0).lower()
                props = collections.OrderedDict()
                # Loop over the contents of the current line
                for i,v in enumerate(r):
                    pname = properties[i].lower()
                    try:
                        props[pname] = self._properties[pname](v)
                    except ValueError:
                        props[pname] = self._properties[pname]()
                    
                self._data[ename] = props
                        
            f.close()

        # If any error occurs, load the default database
        except:
            self._load(ElementsDatabase._DEFAULT_DATABASE)
        
    def add_element(self, ename):
        '''
        Add a new element in the elements database.
        
        :param ename: the name of the element to add
        :type ename: str
        '''
        
        ename = ename.lower()

        if ename not in self._data:
            self._data[ename] = collections.OrderedDict([(pname,prop()) for pname,prop in self._properties.iteritems()])
            
    def add_property(self, pname, typ):
        '''
        Add a new property to the elements database.
        
        When added, the property will be set with a default value to all the elements of the database.
        
        :param pname: the name of the property to add
        :type pname: str
        :param typ: the type of the property
        :type typ: one of "str","int" or "float"
        :param save: if True the elements database will be saved
        :type save: bool
        '''
        
        pname = pname.lower()

        if pname in self._properties:
            raise ElementsDatabaseError("The property %r is already registered in the database." % pname)

        if typ not in self._TYPES.keys():
            raise ElementsDatabaseError("Invalid type for %r property" % pname)

        self._properties[pname] = self._TYPES[typ]
        
        for v in self._data.values():
            v[pname] = self._properties[pname]()
                        
    @property
    def elements(self):
        '''
        Returns the name of the elements of the database.

        :return: the name of the elements stored in the database
        :rtype: list
        '''
        
        return list(self._data.keys())

    def export(self, fmt, filename, *args, **kwargs):
        '''
        Export the database.
        
        The database can be exported in XML or CSV format, the latter being the one used internally.
        
        :param fmt: the output file format for the exported database
        :type fmt: one of 'csv' or "xml"
        :param filename: the path of the file in which the database will be exported 
        :type filename: str
        '''

        try:
            exporter = ElementsDatabase.exporters[fmt]
            filename = os.path.splitext(filename)[0] + "." + fmt
            exporter(self, filename, *args, **kwargs)
        except KeyError:
            raise ElementsDatabaseError("%r format is not a valid export format." % fmt)
            
    def get_element(self,ename):
        '''
        Get a deep-copy of the properties for a given element.
        
        :param ename: the element for which the properties are required
        :type ename: str

        :return: a dictionary of the properties for the selected element
        :rtype: dict
        '''
        
        ename = ename.lower()
        
        return copy.deepcopy(self._data[ename])

    def get_elements(self):
        '''
        Returns the name of the elements of the database.
        
        :return: the name of the elements stored in the database
        :rtype: list
        '''
        
        return list(self._data.keys())

    def get_isotopes(self,ename):
        '''
        Get the name of the isotopes of a given element.
        
        :param ename: the name of the element for which isotopes are searched
        :type ename: str

        :return: the name of the isotopes corresponding to the selected element
        :rtype: list
        '''
        
        ename = ename.lower()

        # The isotopes are searched according to |symbol| property
        symbol = self._data[ename]["symbol"]

        return [iname for iname,props in self._data.iteritems() if props["symbol"] == symbol]

    def get_properties(self):
        '''
        Return the names of the properties stored in the elements database.

        :return: the name of the properties stored in the elements database
        :rtype: list
        '''

        return list(self._properties.keys())
        
    def get_property(self,pname):
        '''
        Returns a dictionary of the value of a given property for all the elements of the database.
        
        :param pname: the name of the property to search in the database
        :type pname: str
        
        :return: a dictionary of the value of a given property for all the elements of the database
        :rtype: MDANSE.Data.ElementsDatabase.SortedDict
        '''
        
        pname = pname.lower()
        
        if pname not in self._properties:
            raise ElementsDatabaseError("The property %r is not registered in the elements database" % pname)
        
        return collections.OrderedDict([(k,self[k,pname]) for k in self._data.keys()])

    def get_property_type(self,pname):
        '''
        Returns the type of a given property stored in the elements database.
        
        :param pname: the property for which the type is required
        :type pname: str
        
        :return: the type of the selected property
        :rtype: one of str, int or float
        '''
        
        pname = pname.lower()

        return copy.deepcopy(self._properties[pname])
                
    def get_numeric_properties(self):
        '''
        Return the names of the numeric properties stored in the elements database.

        :return: the name of the numeric properties stored in the elements database
        :rtype: list
        '''

        return [name for name,typ in self._properties.items() if issubclass(typ,numbers.Number)]

    def has_element(self,ename):
        '''
        Return True if the elements database contains a given element.
        
        :param ename: the name of the element searched in the elements database
        :type ename: str
        
        :return: True if the elements database contains the selected element
        :rtype: bool
        '''
        
        ename = ename.lower()

        return ename in self._data

    def has_property(self,pname):
        '''
        Return True if the elements database contains a given property.
        
        :param pname: the name of the property searched in the elements database
        :type pname: str

        :return: True if the elements database contains the selected property
        :rtype: bool
        '''
        
        pname = pname.lower()

        return pname in self._properties

    def info(self, ename):
        '''
        Return a formatted string that contains all the informations about a given element.
        
        :param element: the name of the element for which the property is required
        :type element: str
        
        :return: the information about a selected element
        :rype: str
        '''
        
        ename = ename.lower()
        
        # A delimiter line.
        delimiter = "-"*70

        # The list that will contain the informations.
        info = []

        # Append a delimiter.                
        info.append(delimiter)

        # The name of the entry is centered in a centered-string.
        info.append("%s" % ename.center(70))
                        
        # The 'property' and 'value' columns names.
        info.append("%s" % " {0:<20}{1:>50}".format('property', 'value'))
                                
        # Append a delimiter.                
        info.append(delimiter)
                        
        # The values for all element's properties
        for pname in self._properties.keys():
            info.append("%s" % " {0:<20}{1:>50}".format(pname,self[ename,pname]))

        # Append a delimiter.                
        info.append(delimiter)
                
        # The list is joined to a string.
        info = "\n".join(info)
                            
        # And returned.        
        return info

    def match_numeric_property(self, pname, value, tolerance=0.0):
        '''
        Return the names of the elements that match a given numeric property within a given tolerance
        
        :param pname: the name of the property to to match
        :type pname: str
        :param value: the matching value
        :type value: one of int, float
        :param tolerance: the matching tolerance
        :type tolerance: float
        
        :return: the names of the elements that matched the property with the selected value within the selected tolerance
        :rtype: list
        '''
        
        pname = pname.lower()

        tolerance = abs(tolerance)

        pvalues = self.get_property(pname)

        return [ename for ename,pval in pvalues.items() if abs(pval-value)<tolerance]
           
    @property
    def nElements(self):
        '''
        Return the number of elements stored in the elements database.
        
        :return: the number of elements stored in the elements database
        :rtype: int
        '''

        return len(self._data)

    @property
    def nProperties(self):
        '''
        Return the number of properties stored in the elements database.
        
        :return: the number of properties stored in the elements database
        :rtype: int
        '''
        
        return len(self._properties)

    def number_of_elements(self):
        '''
        Return the number of elements stored in the elements database.
        
        :return: the number of elements stored in the elements database
        :rtype: int
        '''

        return len(self._data)

    def number_of_properties(self):
        '''
        Return the number of properties stored in the elements database.
        
        :return: the number of properties stored in the elements database
        :rtype: int
        '''

        return len(self._properties)
    
    @property
    def numericProperties(self):
        '''
        Return the names of the numeric properties stored in the elements database.

        :return: the name of the numeric properties stored in the elements database
        :rtype: list
        '''

        return self.get_numeric_properties()    
        
    @property
    def properties(self):
        '''
        Return the names of the properties stored in the elements database.

        :return: the name of the properties stored in the elements database
        :rtype: list
        '''
        
        return list(self._properties.keys())
    
    def _reset(self):
        '''
        Reset the elements database
        '''
        
        self._data.clear()

        self._properties.clear()
        
    def save(self):
        '''
        Save a copy of the elements database to MDANSE application directory. 
        '''
        
        self.export("csv",ElementsDatabase._USER_DATABASE)
            
ELEMENTS = ElementsDatabase()
