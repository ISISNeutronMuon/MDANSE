
import pytest
from icecream import ic
import numpy as np

from MDANSE.NeutronInstruments.NeutronInstrument import NeutronInstrument
from MDANSE.NeutronInstruments.IdealInstrument import IdealInstrument

def test_blank_instrument():
    print(NeutronInstrument.subclasses())
    instance = NeutronInstrument.create("IdealInstrument")
    assert issubclass(instance.__class__, NeutronInstrument)
    assert isinstance(instance, IdealInstrument)
