import abc

class _Meta(type):
    '''
    Metaclass that allows to use the __getitem__ method at a class level for the class that has been built.
     
    The class that uses this metaclass must define a class attribute named _registry that will be used
    by the __getitem__ method.
    '''
         
    def __getitem__(self, item):
        """
        Returns a given item stored in the class registry
        """
         
        return self._registry[item]
    
class ClassRegistry(abc.ABCMeta):
    '''
    Metaclass that registers the subclasses of bases classes.

    The internal registry is defined as a nested dictionary whose keys 
    are the |type| class attribute of the base classes and values another dictionary 
    whose keys are the |type| class attribute of the subclasses and values are the corresponding 
    class instances.

    Hence any base or child class that does not define |type| class attribute will not be resgistered.
    '''
    
    __metaclass__ = _Meta

    __interfaces = []

    _registry = {}
                
    def __init__(self, name, bases, namespace):
        '''
        Constructor of a class metaclassed by ClassFactory
        
        :param name: the name of the class to be built by this metaclass
        :param bases: the base classes of the class to be built by this metaclass
        :param namespace: the attributes and methods of the class to be built by this metaclass
        '''
        
        super(ClassRegistry, self).__init__(name, bases, namespace)
        
        # Get the typ of the class
        typ = getattr(self, 'type', None)
                
        if typ is None:
            return

        metaClass = namespace.get("__metaclass__", None)
                       
        if metaClass is ClassRegistry:
            if (ClassRegistry._registry.has_key(typ)):
                return
            ClassRegistry.__interfaces.append(self)
            ClassRegistry._registry[typ] = {}

        else:
                                
            for interface in ClassRegistry.__interfaces:
                if issubclass(self, interface):
                    ClassRegistry._registry[interface.type][typ] = self
                    break

    @classmethod
    def info(cls, interface):
        '''
        Returns informations about the subclasses of a given base class  stored in the registry.
        
        :param cls: the ClassRegsitry instance
        :param interface: the name of base class of whom information about its subclasses is requested
        '''
                
        if not cls._registry.has_key(interface):
            return "The interface " + interface + " is not registered"

        import inspect
        import os

        # Dictionnay whose keys are the package names and values and list of (job name, job path) stored in the corresponding package. 
        packages = {}

        # Loop over the registry items.
        for k, v in cls._registry[interface].items():
            
            # Get the module corresponding to the job class.
            mod = inspect.getmodule(v)

            # The package hosting the module.
            modPackage = mod.__package__
        
            # The module file.
            modFilename = mod.__file__
        
            # If no package could be found, guess a name using the directory name of the module file.
            if modPackage is None:
                modPackage = os.path.split(os.path.dirname(modFilename))[1]
        
            # Update the packages dictionary.
            if packages.has_key(modPackage):
                packages[modPackage].append([k, v.__name__])
            else:
                packages[modPackage] = [[k, v.__name__]]
    
        contents = []
        
        # Print the contents of the packages dictionary.
        contents.append("="*130)
        contents.append("%-50s %-40s %-s" % ("Package", "Name", "Class"))
        contents.append("="*130)
        for k, v in sorted(packages.items()):
            for vv in sorted(v): 
                contents.append("%-50s %-40s %-s" % (k, vv[0], vv[1]))
            contents.append('-' * 130)
        
        contents = "\n".join(contents)
    
        return contents

