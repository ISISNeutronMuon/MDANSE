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
    # speed unit conversions
    ((1., "m/s"), False, "km/h", nullcontext(3.6)),

    # energy unit conversion
    ((1., "eV"), False, "THz", pytest.raises(UnitError)),
    ((1., "eV"), True, "THz", nullcontext(241.799)),
    ((1., "eV"), True, "K", nullcontext(11604.52)),
    # energy unit conversion values taken from
    # https://wild.life.nctu.edu.tw/class/common/energy-unit-conv-table-detail.html
    ((1., "eV"), True, "eV", nullcontext(1)),
    ((1., "eV"), True, "1/cm", nullcontext(8065.54)),
    ((1., "eV"), True, "kcal/mol", nullcontext(23.060548)),
    ((1., "eV"), True, "kJ/mol", nullcontext(96.485332)),
    ((1., "eV"), True, "K", nullcontext(11604.51)),  # actual value from reference is 11604.5
    ((1., "eV"), True, "J", nullcontext(1.60217663e-19)),
    ((1., "eV"), True, "Hz", nullcontext(2.41798924e14)),
    ((1., "1/cm"), True, "eV", nullcontext(1.23984198e-4)),
    ((1., "1/cm"), True, "1/cm", nullcontext(1)),
    ((1., "1/cm"), True, "kcal/mol", nullcontext(0.002859153)), # actual value from reference is 0.00285914
    ((1., "1/cm"), True, "kJ/mol", nullcontext(0.0119627)),
    ((1., "1/cm"), True, "K", nullcontext(1.438777)),
    ((1., "1/cm"), True, "J", nullcontext(1.98644586e-23)),
    ((1., "1/cm"), True, "Hz", nullcontext(2.99792458e10)),
    ((1., "kcal/mol"), True, "eV", nullcontext(0.0433641)),
    ((1., "kcal/mol"), True, "1/cm", nullcontext(349.7538)), # actual value from reference is 349.755
    ((1., "kcal/mol"), True, "kcal/mol", nullcontext(1)),
    ((1., "kcal/mol"), True, "kJ/mol", nullcontext(4.184)),
    ((1., "kcal/mol"), True, "K", nullcontext(503.226)), # actual value from reference is 503.220
    ((1., "kcal/mol"), True, "J", nullcontext(6.94769546e-21)),
    ((1., "kcal/mol"), True, "Hz", nullcontext(1.04853938e+13)),
    ((1., "kJ/mol"), True, "eV", nullcontext(0.01036427)), # actual value from reference is 0.0103643
    ((1., "kJ/mol"), True, "1/cm", nullcontext(83.5931)), # actual value from reference is 83.59347
    ((1., "kJ/mol"), True, "kcal/mol", nullcontext(0.2390057)), # actual value from reference is 0.239006
    ((1., "kJ/mol"), True, "kJ/mol", nullcontext(1)),
    ((1., "kJ/mol"), True, "K", nullcontext(120.2739)), # actual value from reference is 120.2724
    ((1., "kJ/mol"), True, "J", nullcontext(1.66053907e-21)),
    ((1., "kJ/mol"), True, "Hz", nullcontext(2.5060692e12)),
    ((1., "K"), True, "eV", nullcontext(0.0000861733)),
    ((1., "K"), True, "1/cm", nullcontext(0.695035)),
    ((1., "K"), True, "kcal/mol", nullcontext(0.001987177)), # actual value from reference is 0.00198720
    ((1., "K"), True, "kJ/mol", nullcontext(0.00831435)), # actual value from reference is 0.00831446
    ((1., "K"), True, "K", nullcontext(1)),
    ((1., "K"), True, "J", nullcontext(1.38064900e-23)),
    ((1., "K"), True, "Hz", nullcontext(2.08366191e10)),
    ((1., "J"), True, "eV", nullcontext(6.24150907e18)),
    ((1., "J"), True, "1/cm", nullcontext(5.03411657e22)),
    ((1., "J"), True, "kcal/mol", nullcontext(1.43932619e20)),
    ((1., "J"), True, "kJ/mol", nullcontext(6.02214076e20)),
    ((1., "J"), True, "K", nullcontext(7.24297052e22)),
    ((1., "J"), True, "J", nullcontext(1)),
    ((1., "J"), True, "Hz", nullcontext(1.50919018e33)),
    ((1., "Hz"), True, "eV", nullcontext(4.13566770e-15)),
    ((1., "Hz"), True, "1/cm", nullcontext(3.33564095e-11)),
    ((1., "Hz"), True, "kcal/mol", nullcontext(9.53707627e-14)),
    ((1., "Hz"), True, "kJ/mol", nullcontext(3.99031271e-13)),
    ((1., "Hz"), True, "K", nullcontext(4.79924307e-11)),
    ((1., "Hz"), True, "J", nullcontext(6.62607015e-34)),
    ((1., "Hz"), True, "Hz", nullcontext(1)),

    # named unit conversions
    ((1., "kcal/mol"), True, "kcal_per_mole", nullcontext(1)),
    ((1., "kJ/mol"), True, "kJ_per_mole", nullcontext(1)),
    ((1., "1/nm"), True, "inv_nm", nullcontext(1)),

    # force unit conversions
    ((1., "kJ/ang mol"), True, "J/m", nullcontext(1.66053892103219e-11)),
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
