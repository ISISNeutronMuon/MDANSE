from MDANSE import REGISTRY
from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MolecularDynamics.Trajectory import find_atoms_in_molecule

class BasisSelection(IConfigurator):
    """
    This configurator allows to define a local basis per molecule. 
    
    For each molecule, the basis is defined using the coordinates of three atoms of the molecule. 
    These coordinates will respectively define the origin, the X axis and y axis of the basis, the 
    Z axis being latter defined in such a way that the basis is direct.     
    """
        
    _default = None

    def configure(self, value):
        '''
        Configure an input value. 
        
        The value can be:
        
        #. a dict with *'molecule'*, *'origin'*, *'x_axis'* and *'y_axis'* keys. *'molecule'* key is \
        the name of the molecule for which the axis selection will be performed and *'origin'*, *'x_axis'* and *'y_axis'* \
        keys are the names of three atoms of the molecule that will be used to define respectively the origin, the X and Y axis of the basis  
        #. str: the axis selection will be performed by reading the corresponding user definition.
        
        :param value: the input value
        :type value: tuple or str 

        :note: this configurator depends on 'trajectory' configurator to be configured
        '''

        trajConfig = self._configurable[self._dependencies['trajectory']]
            
        if UD_STORE.has_definition(trajConfig["basename"],"basis_selection",value): 
            ud = UD_STORE.get_definition(trajConfig["basename"],"basis_selection",value)
            self.update(ud)
        else:
            self.update(value)
                
        e1 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['origin'], True)
        e2 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['x_axis'], True)
        e3 = find_atoms_in_molecule(trajConfig['instance'].universe,self['molecule'], self['y_axis'], True)
        
        self["value"] = value
        
        self['basis'] = zip(e1,e2,e3)      
        
        self['n_basis'] = len(self['basis'])

    def get_information(self):
        '''
        Returns some informations about this configurator.
        
        :return: the information about this configurator
        :rtype: str
        '''
        
        return "Basis vector:%s" % self["value"]
    
REGISTRY["basis_selection"] = BasisSelection
