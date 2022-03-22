# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Framework/Configurators/McStasInstrumentConfigurator.py
# @brief     Implements module/class/test McStasInstrumentConfigurator
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator
           
class McStasInstrumentConfigurator(InputFileConfigurator):
    """
    This configurator allows to input a McStas executable file
    """

    pass

REGISTRY["mcstas_instrument"] = McStasInstrumentConfigurator
