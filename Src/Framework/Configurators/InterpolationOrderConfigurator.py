# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/InterpolationOrderConfigurator.py
# @brief     Implements module/class/test InterpolationOrderConfigurator
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Configurators.SingleChoiceConfigurator import SingleChoiceConfigurator
            
class InterpolationOrderConfigurator(SingleChoiceConfigurator):
    """
    This configurator allows to input the interpolation order to be applied when deriving velocities from atomic coordinates.

    The allowed value are *'no interpolation'*,*'1st order'*,*'2nd order'*,*'3rd order'*,*'4th order'* or *'5th order'*, the 
    former one will not interpolate the velocities from atomic coordinates but will directly use the velocities stored in the trajectory file.
    
    :attention: it is of paramount importance for the trajectory to be sampled with a very low time \
    step to get accurate velocities interpolated from atomic coordinates. 

    :note: this configurator depends on 'trajectory' configurator to be configured.
    """
        
    _default = "no interpolation"
        
    def __init__(self, name, orders=None,**kwargs):
        '''
        Initializes the configurator.
        
        :param name: the name of the configurator as it will appear in the configuration.
        :type name: str.
        '''

        if orders is None:
            orders = ["no interpolation","1st order","2nd order","3rd order","4th order","5th order"] 
                
        SingleChoiceConfigurator.__init__(self, name, choices=orders, **kwargs)

    def configure(self, value):
        '''
        Configure the input interpolation order.
                
        :param value: the interpolation order to be configured.
        :type value: str one of *'no interpolation'*,*'1st order'*,*'2nd order'*,*'3rd order'*,*'4th order'* or *'5th order'*.
        '''

        if not value:
            value = self._default

        SingleChoiceConfigurator.configure(self, value)
        
        if value == "no interpolation":

            trajConfig = self._configurable[self._dependencies['trajectory']]

            if not "velocities" in trajConfig['instance'].variables():
                raise ConfiguratorError("the trajectory does not contain any velocities. Use an interpolation order higher than 0", self)
            
            self["variable"] = "velocities"
            
        else:

            self["variable"] = "configuration"
            
REGISTRY["interpolation_order"] = InterpolationOrderConfigurator
