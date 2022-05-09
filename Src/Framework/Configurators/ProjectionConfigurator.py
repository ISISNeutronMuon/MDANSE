# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/ProjectionConfigurator.py
# @brief     Implements module/class/test ProjectionConfigurator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator, ConfiguratorError
        
class ProjectionConfigurator(IConfigurator):
    '''
    This configurator allows to define a projector for atomic coordinates.
    
    Planar and axial projections are supported by MDANSE while a null projector, that does not project the coordinates, has been introduced 
    in MDANSE.Framework.Projectors.IProjector.IProjector for the sake of homogeneity.
    '''

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

REGISTRY['projection'] = ProjectionConfigurator
