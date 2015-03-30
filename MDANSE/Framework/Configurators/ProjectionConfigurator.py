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
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
        
class ProjectionConfigurator(IConfigurator):
    """
    This configurator allows to define a projection axis. 
    """

    type = 'projection'

    _default = None
                        
    def configure(self, configuration, value):
        
        if value is None:
            value = ('null',None)

        try:
            mode, axis = value
        except (TypeError,ValueError) as e:
            raise ConfiguratorError(e)

        if not isinstance(mode,basestring):
            raise ConfiguratorError("invalid type for projection mode: must be a string")            
        
        mode = mode.lower()
                            
        try:
            self["projector"] = REGISTRY['projector'][mode]()
        except KeyError:
            raise ConfiguratorError("the projector %r is unknown" % mode)
        else:
            self["projector"].set_axis(axis)
            self["axis"] = self["projector"].axis

    def get_information(self):
        
        return "Projection along %r axis:" % self["axis"] 