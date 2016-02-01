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
Created on May 21, 2015

:author: Eric C. Pellegrini
'''


from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
        
class ProjectionConfigurator(IConfigurator):
    '''
    This configurator allows to define a projector for atomic coordinates.
    
    Planar and axial projections are supported by MDANSE while a null projector, that does not project the coordinates, has been introduced 
    in MDANSE.Framework.Projectors.IProjector.IProjector for the sake of homogeneity.
    '''

    type = 'projection'

    _default = None
                        
    def configure(self, value):
        '''
        Configure a projector. 
                
        :param value: the input projector definition. It can be a 2-tuple whose 1st element if the name \
        of the projector (one of *'null'*,*'axial'* or *'planar'*) and the 2nd element the parameters for the selected \
        projector (None for *'null'*, a Scientific.Vector for *'axial'* and a list of two Scientific.Vector for *'planar'*) \
        or ``None`` in the case where no projection is needed.
        :type value: 2-tuple
        '''
        
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
        '''
        Returns string information about this configurator.
        
        :return: the information about this configurator.
        :rtype: str
        '''
        
        if self["axis"] is not None:        
            return "No projection performed\n"
        else: 
            return "Projection along %r axis\n" % self["axis"]
