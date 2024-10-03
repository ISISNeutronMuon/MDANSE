import pytest
import tempfile
import os

import h5py
import numpy as np


from MDANSE_GUI.Session.StructuredSession import SettingsFile, SettingsGroup


@pytest.fixture(scope="module")
def settings_file():
    temp_name = tempfile.mktemp()
    path, name = os.path.split(temp_name)
    sf = SettingsFile(name, path)
    yield sf
    os.remove(temp_name + ".toml")


def test_loading(settings_file: "SettingsFile"):
    new_group = settings_file.group("blam")
    new_group.add("blob", "000", "useless test variable")
    settings_file.save_values()
    settings_file.load_from_file()
    loaded_group = settings_file.group("blam")
    loaded_value = loaded_group.get("blob")
    assert loaded_value == "000"


def test_reloading():
    temp_name = tempfile.mktemp()
    path, name = os.path.split(temp_name)
    settings_file = SettingsFile(name, path)
    new_group = settings_file.group("blam")
    new_group.add("blob", "000", "useless test variable")
    settings_file.save_values()
    settings_file2 = SettingsFile(name, path)
    settings_file2.load_from_file()
    loaded_group = settings_file2.group("blam")
    loaded_value = loaded_group.get("blob")
    assert loaded_value == "000"
