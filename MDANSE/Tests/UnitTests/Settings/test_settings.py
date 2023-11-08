import sys
import tempfile
import os
from os import path

import pytest
from icecream import ic
import numpy as np
import h5py

from MDANSE import REGISTRY
from MDANSE.Framework.Session.Settings import CascadingSettings

sys.setrecursionlimit(100000)
ic.disable()

@pytest.fixture(scope="module")
def settings_filename():
    temp_name = tempfile.mktemp()
    yield temp_name
    os.remove(temp_name)

def test_equality():
    left = CascadingSettings()
    right = CascadingSettings()
    # assignment is applied in reverse order
    left['dummy'] = 12
    left['drone'] = 'brake'
    right['drone'] = 'brake'
    right['dummy'] = 12
    # they should still be equal in the end
    assert right == left

def test_saveload(settings_filename):
    start = CascadingSettings()
    start['energy'] = 'meV'
    # save
    start.serialize(settings_filename)
    # load
    end = CascadingSettings()
    end.load_from_file(settings_filename)
    assert start == end

def test_inheritance():
    original = CascadingSettings()
    original['energy'] = 'meV'
    descendant = original.produce_child()
    assert not original == descendant
    assert original['energy'] == descendant['energy']
