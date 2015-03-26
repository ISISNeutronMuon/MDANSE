import _abcoll
import ast
import copy
import csv
import numbers
import os
import xml.etree.ElementTree as etree

from MMTK import Atom

from nMOLDYN import PLATFORM
from nMOLDYN.Core.Error import Error
from nMOLDYN.Core.Singleton import Singleton

class ElementsDatabaseError(Error):
    pass

def create_mmtk_database_entry(directory,name, symbol=None,mass=0.0):
    
    if symbol is None:
        symbol = name

    filename = os.path.join(PLATFORM.local_mmtk_database_directory(),directory, name)
    f = open(filename, 'w')
    f.write('name = "%s"\n\n' % name)
    f.write('symbol = "%s"\n\n' % name)
    f.write('mass = %s' % mass)
    f.close()
    
    return filename

def indent(elem, level=0):
    """
    Produces a pretty indented XML tree.
    
    @param elem: the element tree to indent.
    @type elem: Element instance.
    
    @param level: the level of indentation.
    @type level: int.
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

class SortedCaselessDict(dict):

    def __init__(self, *args, **kwds):

        self._keys = []

        self.__update(*args, **kwds)

    def __contains__(self,item):

        return self.has_key(item.lower())

    def __deepcopy__(self,memo):

	return SortedCaselessDict(copy.deepcopy(dict(self)))
    
    def __getitem__(self,item):
                
        return dict.__getitem__(self,item.lower())

    def __setitem__(self,item,value):

        item = item.lower()

        dict.__setitem__(self,item,value)

        if not item in self._keys:
            self._keys.append(item)
            self._keys.sort()
            
    def __update(*args, **kwds):
        if len(args) > 2:
            raise TypeError("update() takes at most 2 positional arguments ({} given)".format(len(args)))
        elif not args:
            raise TypeError("update() takes at least 1 argument (0 given)")
        
        self = args[0]

        other = args[1] if len(args) >= 2 else ()

        if isinstance(other, _abcoll.Mapping):
            for key in other:
                self[key.lower()] = other[key]
        elif hasattr(other, "keys"):
            for key in other.keys():
                self[key.lower()] = other[key]
        else:
            for key, value in other:
                self[key] = value
        for key, value in kwds.items():
            self[key.lower()] = value
            
    def clear(self):
        
        dict.clear(self)
        
        self._keys = []

    def has_key(self, item):
        
        return dict.has_key(self,item.lower())

    def items(self):
        return [(key, self[key]) for key in self._keys]

    def keys(self):
        return self._keys

    def iteritems(self):
        for k in self._keys:
            yield (k, self[k])

    def iterkeys(self):
        return iter(self._keys)

    def itervalues(self):
        for k in self._keys:
            yield self[k]        

    def values(self):
        return [self[key] for key in self._keys]

class ElementsDatabase(object):
    
    _DEFAULT_DATABASE = os.path.join(os.path.dirname(__file__), "elements_database.csv")

    _USER_DATABASE = os.path.join(PLATFORM.application_directory(), "elements_database.csv")
    
    _TYPES = {"str" : str, "int" : int, "float" : float}

    def __init__(self):

        self._data = SortedCaselessDict()

        self._properties = SortedCaselessDict()

        self.reset()

        # Load the user database. If any problem occurs while loading it, loads the default one
        self._load(ElementsDatabase._USER_DATABASE)
                
    def __contains__(self,ename):

        return self._data.has_key(ename)

    def __getitem__(self,item):

        ename,pname = item
                
        try:
            element = self._data[ename]
        except KeyError:
            raise ElementsDatabaseError("The element %r is not registered in the database." % ename)
        else:
            try:
                return element[pname]
            except KeyError:
                try:
                    return self._properties[pname]["default"]
                except KeyError:
                    raise ElementsDatabaseError("The property %r is not registered in the database." % pname)

    def __iter__(self):
                        
        for v in self._data.itervalues():
            yield copy.deepcopy(v)
                
    def __setitem__(self,item,value):

        ename,pname = item
                
        self._data[ename][pname] = self._properties[pname]['type'](value)

        # If one of those properties is changed then the corresponding mmtk entry has to be updated
        if pname in ["name","symbol","atomic_weight"]:
            create_mmtk_database_entry("Atoms",ename,symbol=self._data[ename]["symbol"],mass=self._data[ename]["atomic_weight"])

    def _export_csv(self, filename, delimiter=',', lineterminator='\n', restval='undefined'):

        f = open(filename, 'w')

        propNames = ["id"] + self._properties.keys()
                
        # Return a csv writer object.            
        databaseWriter = csv.DictWriter(f, propNames, delimiter=delimiter, lineterminator=lineterminator, restval=restval)
        databaseWriter.writeheader()
        default = {"id":"''"}
        default.update(dict([(pname,repr(prop['default'])) for pname,prop in self._properties.items()]))
        databaseWriter.writerow(default)
        for ename, props in self._data.items():
            p = {"id":ename}
            p.update(dict([(pname,props.get(pname,prop["default"])) for pname,prop in self._properties.items()]))
            databaseWriter.writerow(p)
                                                 
        # Closes the csv file. 
        f.close()

    def _export_xml(self, filename):

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
                subnode.text = str(props.get(pname,prop["default"]))
                # And append the property node to the current element node.
                node.append(subnode)
                
            # Append the element node to the root node.
            root.append(node)
            
        # Produce a nice-looking indented output in the XML file.
        indent(root)
        
        etree.ElementTree(root).write(f)

        f.close()

    exporters = {"csv" : _export_csv, "xml" : _export_xml}
            
    def _load(self, filename):

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
                
                if self._properties.has_key(pname):
                    continue
                
                ptype=self._TYPES[ptype]
                                
                self._properties[pname] = {"type":ptype,"default":ptype()}
                                        
            # Reads the next lines of the CSV that correspond to the database entries
            for r in reader:
                ename = r.pop(0)
                props = SortedCaselessDict()
                # Loop over the contents of the current line
                for i,v in enumerate(r):
                    pname = properties[i]
                    try:
                        props[pname] = self._properties[pname]["type"](v)
                    except ValueError:
                        props[pname] = self._properties[pname]["default"]
                    
                self._data[ename] = props
                        
            f.close()

        # If any error occurs, load the default database
        except:
            self._load(ElementsDatabase._DEFAULT_DATABASE)
        
    def add_element(self, ename, save=False):

        if not self._data.has_key(ename):
            self._data[ename] = SortedCaselessDict([(pname,prop["default"]) for pname,prop in self._properties.iteritems()])
        
        # Create the corresponding MMTK entry
        create_mmtk_database_entry("Atoms",ename,symbol=self._data[ename]["symbol"],mass=self._data[ename]["atomic_weight"])

        if save:
            self.save()

    def add_property(self, pname, default, save=False):

        if self._properties.has_key(pname):
            raise ElementsDatabaseError("The property %r is already registered in the database." % pname)

        self._properties[pname] = {"type":type(default),"default":default}

        if save:
            self.save()
                
    @property
    def elements(self):
        
        return self._data.keys()

    def export(self, fmt, filename, *args, **kwargs):

        try:
            exporter = ElementsDatabase.exporters[fmt]
            filename = os.path.splitext(filename)[0] + "." + fmt
            exporter(self, filename, *args, **kwargs)
        except KeyError:
            raise ElementsDatabaseError("%r format is not a valid export format." % fmt)
            
    def get_element(self,ename):
        
        return copy.deepcopy(self._data[ename])

    def get_elements(self):
        
        return self._data.keys()

    def get_isotopes(self,ename):

        symbol = self._data[ename]["symbol"]

        return [ename for ename,props in self._data.iteritems() if props["symbol"] == symbol]

    def get_properties(self):

        return self._properties.keys()
        
    def get_property(self,pname):
        
        return SortedCaselessDict([(k,self[k,pname]) for k in self._data.iterkeys()])

    def get_property(self,pname):
        
        return SortedCaselessDict([(k,self[k,pname]) for k in self._data.iterkeys()])

    def get_property_settings(self,pname):

        return copy.deepcopy(self._properties[pname])
                
    def get_numeric_properties(self):

        return [pname for pname,prop in self._properties.iteritems() if isinstance(prop['default'],numbers.Number)]

    def has_element(self,ename):

        return self._data.has_key(ename)

    def has_property(self,pname):

        return self._properties.has_key(pname)

    def info(self, ename):
        '''
        Return a formatted string that contains all the informations about a given element.
        
        @param element: the element symbol.
        @type element: string
        '''
        
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

        tolerance = abs(tolerance)

        pvalues = self.get_property(pname)

        return [ename for ename,pval in pvalues.items() if abs(pval-value)<tolerance]
           
    @property
    def nElements(self):
        return len(self._data)

    @property
    def nProperties(self):
        return len(self._properties)

    def number_of_elements(self):
        return len(self._data)

    def number_of_properties(self):
        return len(self._properties)
    
    @property
    def numericProperties(self):

        return self.get_numeric_properties()    
        
    @property
    def properties(self):
        
        return self._properties.keys()
    
    def reset(self):
        
        self._data.clear()

        self._properties.clear()
        
    def save(self):
        
        self.export("csv",ElementsDatabase._USER_DATABASE)
        
    def regenerate_mmtk_database(self):
        
        for name,props in self._data.items():
            filename = os.path.join(PLATFORM.local_mmtk_database_directory(),"Atoms", name)
            f = open(filename, 'w')
            f.write('name = "%s"\n\n' % props["name"])
            f.write('symbol = "%s"\n\n' % name)
            f.write('mass = %s' % props["atomic_weight"])
            f.close()
            
