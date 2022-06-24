# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/QVectorsConfigurator.py
# @brief     Implements module/class/test QVectorsConfigurator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class QVectorsConfigurator(IConfigurator):
    """
    This Configurator allows to set reciprocal vectors.
    
    Reciprocal vectors are used in MDANSE for the analysis related to scattering experiments such as dynamic coherent structure 
    or elastic incoherent structure factor analysis. In MDANSE, properties that depends on Q vectors are always scalar regarding 
    Q vectors in the sense that the values of these properties will be computed for a given norm of Q vectors and not for a given Q vectors.
    Hence, the Q vectors generator supported by MDANSE always generates Q vectors on Q-shells, each shell containing a set of Q vectors whose 
    norm match the Q shell value within a given tolerance.
    
    Depending on the generator selected, Q vectors can be generated isotropically or anistropically, on a lattice or randomly.
    
    Q vectors can be saved to a user definition and, as such, can be further reused in another MDANSE session.
    
    To define a new Q vectors generator, you must inherit from MDANSE.Framework.QVectors.QVectors.QVector interface.
    
    :note: this configurator depends on 'trajectory' configurator to be configured.
    """
        
    _default = ("spherical_lattice",{"shells":(0.1,5,0.1), "width" : 0.1, "n_vectors" : 50})

    def configure(self, value):
        '''
        Configure a Q vectors generator. 
                
        :param configuration: the current configuration.
        :type configuration: a MDANSE.Framework.Configurable.Configurable object
        :param value: the Q vectors generator definition. It can be a 2-tuple, whose 1st element is the name of the Q vector generator \
        and 2nd element the parameters for this configurator or a string that matches a Q vectors user definition.
        :type value: 2-tuple or str
        '''

        trajConfig = self._configurable[self._dependencies['trajectory']]
        if isinstance(value,basestring): 
            if UD_STORE.has_definition(trajConfig["basename"],"q_vectors",value):
                ud = UD_STORE.get_definition(trajConfig["basename"],"q_vectors",value)
                self["parameters"] = ud['parameters']
                self["type"] = ud['generator']
                self["is_lattice"] = ud['is_lattice']
                self["q_vectors"] = ud['q_vectors']
            else:
                raise ConfiguratorError("Q vectors user definition %s is not stored on this machine" % value, self)
                
        else:
            if isinstance(value,tuple):
                try:
                    generator, parameters = value
                except ValueError:
                    raise ConfiguratorError("Invalid q vectors settings %s" % value, self)
                generator = REGISTRY["q_vectors"][generator](trajConfig["universe"])
                generator.setup(parameters)
                generator.generate()
                            
                if not generator.configuration['q_vectors']:
                    raise ConfiguratorError("no Q vectors could be generated", self)
    
                self["parameters"] = parameters
                self["type"] = generator._type
                self["is_lattice"] = generator.is_lattice
                self["q_vectors"] = generator.configuration['q_vectors']
            else:
                raise ConfiguratorError("Q vectors setting must be a tuple %s" % value, self)
                                        
        self["shells"] = self["q_vectors"].keys()
        self["n_shells"] = len(self["q_vectors"])    
        self["value"] = self["q_vectors"]

    def get_information(self):
        '''
        Returns string information about this configurator.
        
        :return: the information about this configurator.
        :rtype: str
        '''
        
        info = ["%d Q shells generated\n" % self["n_shells"]]
        for (qValue,qVectors) in self["q_vectors"].items():
            info.append("Shell %s: %d Q vectors generated\n" % (qValue,len(qVectors)))
        
        return "".join(info)
    
REGISTRY["q_vectors"] = QVectorsConfigurator
