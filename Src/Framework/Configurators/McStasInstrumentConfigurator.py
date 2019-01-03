from MDANSE import REGISTRY
from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator
           
class McStasInstrumentConfigurator(InputFileConfigurator):
    """
    This configurator allows to input a McStas executable file
    """

    pass

REGISTRY["mcstas_instrument"] = McStasInstrumentConfigurator
