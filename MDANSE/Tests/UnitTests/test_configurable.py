#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import pytest
from MDANSE.Framework.Configurable import Configurable


@pytest.mark.parametrize("opt, val, success", [
    ({}, 20, True),
    ({}, 20.2, True),
    ({}, "30", True),
    ({}, "30.2", True),
    ({}, "xxxx", False),
    ({}, [1, 2], False),

    ({"maxi": 10}, 10, True),
    ({"mini": 10}, 10, True),
    ({"maxi": 10}, 20, False),
    ({"mini": 10}, 0, False),

    ({"choices": [0, 10]}, 0, True),
    ({"choices": [0, 10]}, 13, False),
])
def test_float_configurator(opt, val, success):
    conf = Configurable()
    conf.set_settings({"test_val": ("FloatConfigurator", opt)})

    parameters = {"test_val": val}
    conf.setup(parameters)
    assert conf._configured == success

    if success:
        assert conf["test_val"]["value"] == float(val)

@pytest.mark.parametrize("opt, val, success", [
    ({}, 20, True),
    ({}, 20.2, True),
    ({}, "30", True),
    ({}, "30.2", False),
    ({}, "xxxx", False),
    ({}, [1, 2], False),

    ({"maxi": 10}, 10, True),
    ({"mini": 10}, 10, True),
    ({"maxi": 10}, 20, False),
    ({"mini": 10}, 0, False),

    ({"choices": [0, 10]}, 0, True),
    ({"choices": [0, 10]}, 13, False),
    ({"exclude": (0,)}, 0, False),

])
def test_integer_configurator(opt, val, success):
    conf = Configurable()
    conf.set_settings({"test_val": ("IntegerConfigurator", opt)})

    parameters = {"test_val": val}
    conf.setup(parameters)
    assert conf._configured == success

    if success:
        assert conf["test_val"]["value"] == int(val)
