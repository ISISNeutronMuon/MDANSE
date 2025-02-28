import pytest
from MDANSE.NeutronInstruments.IdealInstrument import IdealInstrument
from MDANSE.NeutronInstruments.NeutronInstrument import NeutronInstrument


@pytest.mark.parametrize("instrument_type", NeutronInstrument.subclasses())
def test_instrument(instrument_type):
    instance = NeutronInstrument.create(instrument_type)
    assert issubclass(instance.__class__, NeutronInstrument)
    assert type(instance).__name__ == instrument_type
