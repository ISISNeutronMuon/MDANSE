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
from contextlib import nullcontext
from math import ceil, floor
from operator import (add, iadd, imul, ipow, isub, itruediv, mul, pow, sub,
                      truediv)
from random import random
from typing import TypeVar, Union

import pytest
from MDANSE.Framework.Units import _PREFIXES, UnitError, _Unit, measure

T = TypeVar("T")

def _measure_or_val(m_o_v: T) -> Union[_Unit, T]:
    """Convert a value to a measure or leave if not (val, unit)."""
    if isinstance(m_o_v, (tuple, list)):
        return measure(*m_o_v)
    return m_o_v

@pytest.mark.parametrize("unit", [
    "kg", "m", "s", "K", "mol", "A", "cd", "rad", "sr",
])
def test_basic_units(unit):
    m = measure(1.0, unit)
    assert m.toval() == pytest.approx(1.0)

@pytest.mark.parametrize("prefix", [
    "y", "z", "a", "f", "p", "n", "u", "m", "c", "d",
    "da", "h", "k", "M", "G", "T", "P", "E", "Z", "Y",
])
def test_prefixes(prefix):
    val = random()
    m = measure(val, "s")
    assert m.toval(f"{prefix}s") == pytest.approx(val / _PREFIXES[prefix])

@pytest.mark.parametrize("from_, equivalent, to, expected", [
    ((1., "m/s"), False, "km/h", nullcontext(3.6)),
    ((1., "eV"), False, "THz", pytest.raises(UnitError)),
    ((1., "eV"), True, "THz", nullcontext(241.799)),
    ((1., "eV"), True, "K", nullcontext(11604.52)),
])
def test_conversion(from_, equivalent, to, expected):
    m = measure(*from_, equivalent=equivalent)
    with expected as val:
        assert m.toval(to) == pytest.approx(val)

@pytest.mark.parametrize("in_units, op, out_unit, out_val", [
    (((1., "s"), (1., "ms")), add, "s", 1.001),
    (((1., "s"), (1., "ms")), sub, "s", 0.999),

    (((1., "m"), (5., "hm")), mul, "m2", 500.),
    (((500., "m2"), (10., "cm")), mul, "m3", 50.),
    (((50., "m3"), 20.), mul, "m3", 1000.),

    (((1., "m"), (5., "hm")), truediv, "au", 0.002),
    (((0.002, "au"), 0.0001), truediv, "au", 20.),
    (((20., "au"), (5., "hm")), truediv, "1/m", 4.e-2),

    (((4., "m"), 3), pow, "m3", 64.),

    # In-place
    (((1., "s"), (1., "ms")), iadd, "s", 1.001),
    (((1., "s"), (1., "ms")), isub, "s", 0.999),

    (((1., "m"), (5., "hm")), imul, "m2", 500.),
    (((500., "m2"), (10., "cm")), imul, "m3", 50.),
    (((50., "m3"), 20.), imul, "m3", 1000.),

    (((1., "m"), (5., "hm")), itruediv, "au", 0.002),
    (((0.002, "au"), 0.0001), itruediv, "au", 20.),
    (((20., "au"), (5., "hm")), itruediv, "1/m", 4.e-2),

    (((4., "m"), 3), ipow, "m3", 64.),

    # Other ops
    (((10.2, "m/s"),), floor, None, 10.),
    (((3.6, "m/s"),), floor, None, 3.),
    (((50.3, "km/h"),), floor, None, 50.),

    (((10.2, "m/s"),), ceil, None, 11.),
    (((3.6, "m/s"),), ceil, None, 4.),
    (((50.3, "km/h"),), ceil, None, 51.),

    (((10.2, "m/s"),), round, None, 10.),
    (((3.6, "m/s"),), round, None, 4.),
    (((50.3, "km/h"),), round, None, 50.),

    (((50.3, "km/h"),), round, None, 50.),

])
def test_operators(in_units, op, out_unit, out_val):
    m = op(*map(_measure_or_val, in_units))
    assert m.toval(out_unit) == pytest.approx(out_val)


def test_sqrt():
    m = measure(4.0, "m2/s2")

    m = m.sqrt()

    assert m.toval() == 2.0
    assert m.dimension == [0, 1, -1, 0, 0, 0, 0, 0, 0]
