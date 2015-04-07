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

from MDANSE import REGISTRY
from MDANSE.Framework.UserDefinables.UserDefinitions import USER_DEFINITIONS
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError

class QVectorsConfigurator(IConfigurator):
    """
    This Configurator allows to set reciprocal vectors for a given system.
    """
    
    type = "q_vectors"
    
    _default = ("spherical_lattice",{"shells":(0,5,0.1), "width" : 0.1, "n_vectors" : 50})

    def configure(self, configuration, value):

        trajConfig = configuration[self._dependencies['trajectory']]

        ud = USER_DEFINITIONS.get(trajConfig["basename"],"q_vectors",value)        
        if ud is not None:
            
            self["parameters"] = ud['parameters']
            self["type"] = ud['generator']
            self["is_lattice"] = ud['is_lattice']
            self["q_vectors"] = ud['q_vectors']
        
        else:                        
            generator, parameters = value
            generator = REGISTRY["q_vectors"][generator](trajConfig["instance"])
            generator.setup(parameters)
            data = generator.generate()
                        
            if not data:
                raise ConfiguratorError("no Q vectors could be generated", self)

            self["parameters"] = parameters
            self["type"] = generator.type
            self["is_lattice"] = generator.is_lattice
            self["q_vectors"] = data
                                                
        self["shells"] = self["q_vectors"].keys()
        self["n_shells"] = len(self["q_vectors"])    
        self["value"] = self["q_vectors"]

    def get_information(self):
        
        info = ["%d Q shells generated\n" % self["n_shells"]]
        for (qValue,qVectors) in self["q_vectors"].items():
            info.append("Shell %s: %d Q vectors generated\n" % (qValue,len(qVectors)))
        
        return "".join(info)