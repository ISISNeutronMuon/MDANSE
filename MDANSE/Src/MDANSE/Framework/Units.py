#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
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
from __future__ import annotations

import copy
import json
import math
import numbers
from collections import defaultdict
from functools import singledispatchmethod

from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.Singleton import Singleton

_UNAMES = ["kg", "m", "s", "K", "mol", "A", "cd", "rad", "sr"]
_PREFIXES = {
    "y": 1e-24,  # yocto
    "z": 1e-21,  # zepto
    "a": 1e-18,  # atto
    "f": 1e-15,  # femto
    "p": 1e-12,  # pico
    "n": 1e-9,  # nano
    "u": 1e-6,  # micro
    "m": 1e-3,  # mili
    "c": 1e-2,  # centi
    "d": 1e-1,  # deci
    "da": 1e1,  # deka
    "h": 1e2,  # hecto
    "k": 1e3,  # kilo
    "M": 1e6,  # mega
    "G": 1e9,  # giga
    "T": 1e12,  # tera
    "P": 1e15,  # peta
    "E": 1e18,  # exa
    "Z": 1e21,  # zetta
    "Y": 1e24,  # yotta
}

unit_lookup = {
    "rad/ps": "energy",
    "meV": "energy",
    "1/cm": "energy",
    "THz": "energy",
    "J_per_mole": "energy",
    "cal_per_mole": "energy",
    "nm": "distance",
    "ang": "distance",
    "pm": "distance",
    "Bohr": "distance",
    "ps": "time",
    "fs": "time",
    "ns": "time",
    "1/nm": "reciprocal",
    "1/ang": "reciprocal",
    "N/A": "arbitrary",
}

INTERNAL_UNITS = {
    "energy": "Da nm2 / ps2",
    "velocities": "nm/ps",
    "gradients": "Da nm / ps2",
    "time": "ps",
    "length": "nm",
}


class UnitError(Exception):
    pass


def get_trailing_digits(string: str) -> tuple[str, int]:
    """Get digits from the end of a string.

    Always returns ``1`` if no digits.

    Parameters
    ----------
    string : str
        String to parse.

    Returns
    -------
    str
        String with digits stripped.
    int
        Digits from end of string as ``int``.

    Examples
    --------
    >>> get_trailing_digits("str123")
    ('str', 123)
    >>> get_trailing_digits("nodigits")
    ('nodigits', 1)
    >>> get_trailing_digits("123preceding")
    ('123preceding', 1)
    """
    for i in range(len(string)):
        if string[i:].isdigit():
            return string[:i], int(string[i:])

    return string, 1


class _Unit:
    """Unit handler.

    Handles all basic functions of units with correct dimensionality
    and string printing.

    Parameters
    ----------
    uname : str
        Name of the unit.
    factor : float
        Factor relative to internal units.

    Extra Parameters
    ----------------
    kg : int
        Mass dimension.
    m : int
        Length dimension.
    s : int
        Time dimension.
    K : int
        Temperature dimension.
    mol : int
        Count dimension.
    A : int
        Current dimension.
    cd : int
        Luminous intensity dimension.
    rad : int
        Angular dimension.
    sr : int
        Solid angular dimension.
    """

    def __init__(
        self,
        uname: str,
        factor: float,
        kg: int = 0,
        m: int = 0,
        s: int = 0,
        K: int = 0,
        mol: int = 0,
        A: int = 0,
        cd: int = 0,
        rad: int = 0,
        sr: int = 0,
    ):
        self._factor = factor
        self._dimension = [kg, m, s, K, mol, A, cd, rad, sr]
        self._format = "g"
        self._uname = uname
        self._ounit = None
        self._out_factor = None
        self._equivalent = False

    def __add__(self, other):
        """Add two _Unit instances.

        To be added, the units have to be analog or equivalent.

        Parameters
        ----------
        other : _Unit
           Unit to add.

        Raises
        ------
        UnitError
            Units are not equivalent or incompatible.

        Examples
        --------
        >>> print(measure(10, 'm') + measure(20, 'km'))
        20010 m
        """
        u = copy.deepcopy(self)

        if u.is_analog(other):
            u._factor += other._factor
        elif self._equivalent:
            equivalence_factor = u.get_equivalence_factor(other)
            if equivalence_factor is None:
                raise UnitError("The units are not equivalent")

            u._factor += other._factor / equivalence_factor
        else:
            raise UnitError("Incompatible units.")

        return u

    def __sub__(self, other):
        """Subtract _Unit instances.

        To be subtracted, the units have to be analog or equivalent.

        >>> print(measure(20, 'km') + measure(10, 'm'))
        20.01 km
        """
        u = copy.deepcopy(self)

        if u.is_analog(other):
            u._factor -= other._factor
        elif u._equivalent:
            equivalence_factor = u.get_equivalence_factor(other)
            if equivalence_factor is None:
                raise UnitError("The units are not equivalent")

            u._factor -= other._factor / equivalence_factor
        else:
            raise UnitError("Incompatible units")

        return u

    def __truediv__(self, other):
        """Divide two _Unit instances.

        To be divided, the units have to be analog or equivalent.

        Parameters
        ----------
        other : _Unit
           Unit to add.

        Raises
        ------
        UnitError
            Units are not equivalent or incompatible.

        Examples
        --------
        >>> print(measure(100, 'V') / measure(10, 'kohm'))
        0.01 A1
        >>> print(measure(100, 'V') / 10)
        10 V
        """
        u = copy.deepcopy(self)
        if isinstance(other, (numbers.Number, numbers.Complex)):
            u._factor /= other
        elif isinstance(other, _Unit):
            u._div_by(other)
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

        return u

    def __floordiv__(self, other):
        """Divide two _Unit instances and truncate.

        To be divided, the units have to be analog or equivalent.

        Parameters
        ----------
        other : _Unit
           Unit to add.

        Raises
        ------
        UnitError
            Units are not equivalent or incompatible.

        Examples
        --------
        >>> print(measure(10, 'kohm') // measure(10, 'V'))
        1000 1 / A1
        >>> print(measure(15, 'ohm') // 10)
        1 ohm
        """
        u = copy.deepcopy(self)
        if isinstance(other, numbers.Number):
            u._factor //= other
        elif isinstance(other, _Unit):
            u._div_by(other)
            u._factor = math.floor(u._factor)
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

        return u

    def __mul__(self, other):
        """Multiply _Unit instances or scaling factors.

        Examples
        --------
        >>> print(measure(10, 'm/s') * measure(10, 's'))
        100 m1
        >>> print(measure(10, 'm') * measure(10, 's'))
        100 m1 s1
        >>> print(measure(10, 'm') * 10)
        100 m
        """

        u = copy.deepcopy(self)
        if isinstance(other, (numbers.Number, numbers.Complex)):
            u._factor *= other
            return u
        elif isinstance(other, _Unit):
            u._mult_by(other)
            return u
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

    def __pow__(self, n: float):
        """Raise a _Unit to a factor.

        Examples
        --------
        >>> print(measure(10.5, 'm/s')**2)
        110.25 m2 / s2
        """
        output_unit = copy.copy(self)
        output_unit._ounit = None
        output_unit._out_factor = None
        output_unit._factor = pow(output_unit._factor, n)
        for i in range(len(output_unit._dimension)):
            output_unit._dimension[i] *= n

        return output_unit

    def __float__(self) -> float:
        """Return the value of a _Unit coerced to float.

        Examples
        --------
        >>> float(measure(10.5, 'm/s'))
        10.5

        See Also
        --------
        __int__ : Truncate value.
        """
        return float(self.toval())

    def __int__(self) -> int:
        """Return the value of a _Unit coerced to integer.

        Notes
        ------
        This will happen to the value in the default output unit:

        Examples
        --------
        >>> int(measure(10.5, 'm/s'))
        10
        """
        return int(self.toval())

    def __ceil__(self):
        """Ceil of a _Unit value in canonical units.

        Examples
        --------
        >>> print(measure(10.2, 'm/s').ceiling())
        11 m/s
        >>> print(measure(3.6, 'm/s').ounit('km/h').ceiling())
        13 km/h
        >>> print(measure(50.3, 'km/h').ceiling())
        51 km/h
        """

        r = copy.deepcopy(self)

        if r._ounit is not None:
            val = math.ceil(r.toval(r._ounit))
            newu = _Unit("au", val)
            newu *= _str_to_unit(r._ounit)
            return newu.ounit(r._ounit)
        else:
            r._factor = math.ceil(r._factor)
            return r

    def __floor__(self):
        """Floor of a _Unit value in canonical units.

        Examples
        --------
        >>> print(measure(10.2, 'm/s').floor())
        10 m/s
        >>> print(measure(3.6, 'm/s').ounit('km/h').floor())
        12 km/h
        >>> print(measure(50.3, 'km/h').floor())
        50 km/h
        """

        r = copy.deepcopy(self)

        if r._ounit is not None:
            val = math.floor(r.toval(r._ounit))
            newu = _Unit("au", val)
            newu *= _str_to_unit(r._ounit)
            return newu.ounit(r._ounit)
        else:
            r._factor = math.floor(r._factor)
            return r

    def __round__(self, ndigits=None):
        """Round of a _Unit value in canonical units.

        Examples
        --------
        >>> print(measure(10.2, 'm/s').round())
        10 m/s
        >>> print(measure(3.6, 'm/s').ounit('km/h').round())
        13 km/h
        >>> print(measure(50.3, 'km/h').round())
        50 km/h
        """

        r = copy.deepcopy(self)

        if r._ounit is not None:
            val = round(r.toval(r._ounit), ndigits)
            newu = _Unit("au", val)
            newu *= _str_to_unit(r._ounit)
            return newu.ounit(r._ounit)
        else:
            r._factor = round(r._factor, ndigits)
            return r

    ceiling = __ceil__
    floor = __floor__
    round = __round__

    def __iadd__(self, other):
        """Add _Unit instances.

        See Also
        --------
        __add__
        """

        if self.is_analog(other):
            self._factor += other._factor
            return self
        elif self._equivalent:
            equivalence_factor = self.get_equivalence_factor(other)
            if equivalence_factor is not None:
                self._factor += other._factor / equivalence_factor
                return self
            else:
                raise UnitError("The units are not equivalent")
        else:
            raise UnitError("Incompatible units")

    def __itruediv__(self, other):
        """Divide _Unit instances.

        See Also
        --------
        __div__
        """

        if isinstance(other, numbers.Number):
            self._factor /= other
            return self
        elif isinstance(other, numbers.Complex):
            self._factor /= other
            return self
        elif isinstance(other, _Unit):
            self._div_by(other)
            return self
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

    def __ifloordiv__(self, other):
        """Divide _Unit instances and truncate.

        See Also
        --------
        __truediv__
        """
        self._div_by(other)
        self._factor = math.floor(self._factor)
        return self

    def __imul__(self, other):
        """
        Multiply _Unit instances.

        See Also
        --------
        __mul__
        """

        if isinstance(other, numbers.Number):
            self._factor *= other
            return self
        elif isinstance(other, numbers.Complex):
            self._factor *= other
            return self
        elif isinstance(other, _Unit):
            self._mult_by(other)
            return self
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

    def __ipow__(self, n):
        self._factor = pow(self._factor, n)
        for i in range(len(self._dimension)):
            self._dimension[i] *= n

        self._ounit = None
        self._out_factor = None

        return self

    def __isub__(self, other):
        """Subtract _Unit instances.  See __sub__."""

        if self.is_analog(other):
            self._factor -= other._factor
            return self
        elif self._equivalent:
            equivalence_factor = self.get_equivalence_factor(other)
            if equivalence_factor is not None:
                self._factor -= other._factor / equivalence_factor
                return self
            else:
                raise UnitError("The units are not equivalent")
        else:
            raise UnitError("Incompatible units")

    def __radd__(self, other):
        """Add _Unit instances.

        See Also
        --------
        __add__
        """
        return self.__add__(other)

    def __rdiv__(self, other):
        u = copy.deepcopy(self)
        if isinstance(other, numbers.Number):
            u._factor /= other
            return u
        elif isinstance(other, numbers.Complex):
            u._factor /= other
            return u
        elif isinstance(other, _Unit):
            u._div_by(other)
            return u
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

    def __rmul__(self, other):
        """Multiply _Unit instances.  See __mul__."""

        u = copy.deepcopy(self)
        if isinstance(other, numbers.Number):
            u._factor *= other
            return u
        elif isinstance(other, numbers.Complex):
            u._factor *= other
            return u
        elif isinstance(other, _Unit):
            u._mult_by(other)
            return u
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

    def __rsub__(self, other):
        """Subtract _Unit instances.  See __sub__."""

        return other.__sub__(self)

    def __str__(self):
        unit = copy.copy(self)

        if self._ounit is None:
            s = format(unit._factor, self._format)

            positive_units = []
            negative_units = []
            for uname, uval in zip(_UNAMES, unit._dimension):
                if uval == 0:
                    continue

                ref = positive_units if uval > 0 else negative_units
                unit = str(uname) + (
                    format(abs(uval), "d") if isinstance(uval, int) else str(uval)
                )
                ref.append(unit)

            positive_units_str = " ".join(positive_units)
            negative_units_str = " ".join(negative_units)

            if positive_units_str:
                s += f" {positive_units_str}"

            if negative_units_str:
                if not positive_units_str:
                    s += " 1"
                s += f" / {negative_units_str}"

        else:
            u = copy.deepcopy(self)
            u._div_by(self._out_factor)

            s = f"{u._factor:{self._format}} {self._ounit}"

        return s

    def _div_by(self, other) -> None:
        """Compute divided unit including new dimensionality.

        Parameters
        ----------
        other : _Unit
            Factor to divide by.

        Raises
        ------
        UnitError
            If other is not compatible.

        Examples
        --------
        >>> a = measure(2., "ang")
        >>> a._div_by(measure(4., "s"))
        >>> print(a)
        5e-11 m1 / s1
        """
        if self.is_analog(other):
            self._factor /= other._factor
            self._dimension = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif self._equivalent:
            equivalence_factor = self.get_equivalence_factor(other)
            if equivalence_factor is not None:
                self._factor /= other._factor / equivalence_factor
                self._dimension = [0, 0, 0, 0, 0, 0, 0, 0, 0]
            else:
                raise UnitError("The units are not equivalent")
        else:
            self._factor /= other._factor
            for i in range(len(self._dimension)):
                self._dimension[i] = self._dimension[i] - other._dimension[i]

        self._ounit = None
        self._out_factor = None

    def _mult_by(self, other) -> None:
        """Compute multiplied unit including new dimensionality.

        Parameters
        ----------
        other : _Unit
            Factor to multiply by.

        Raises
        ------
        UnitError
            If other is not compatible.

        Examples
        --------
        >>> a = measure(1., "ang")
        >>> a._mult_by(measure(3., "s"))
        >>> print(a)
        3e-10 m1 s1
        """
        if self.is_analog(other):
            self._factor *= other._factor
            for i in range(len(self._dimension)):
                self._dimension[i] = 2.0 * self._dimension[i]
        elif self._equivalent:
            equivalence_factor = self.get_equivalence_factor(other)
            if equivalence_factor is None:
                raise UnitError("The units are not equivalent")

            self._factor *= other._factor / equivalence_factor
            for i in range(len(self._dimension)):
                self._dimension[i] = 2 * self._dimension[i]
            return
        else:
            self._factor *= other._factor
            for i in range(len(self._dimension)):
                self._dimension[i] = self._dimension[i] + other._dimension[i]

        self._ounit = None
        self._out_factor = None

    @property
    def dimension(self):
        """Getter for _dimension attribute. Returns a copy."""

        return copy.copy(self._dimension)

    @property
    def equivalent(self) -> bool:
        """Getter for _equivalent attribute."""

        return self._equivalent

    @equivalent.setter
    def equivalent(self, equivalent):
        self._equivalent = equivalent

    @property
    def factor(self):
        """Getter for _factor attribute."""

        return self._factor

    @property
    def format(self):
        """Getter for the output format."""

        return self._format

    @format.setter
    def format(self, fmt):
        self._format = fmt

    def is_analog(self, other) -> bool:
        """Whether two units are analog.

        Analog units are units whose dimension vector exactly matches.

        Parameters
        ----------
        other : _Unit
            Unit to test.

        Returns
        -------
        bool
            Whether two units are "analog".

        Examples
        --------
        >>> a, b = measure(1., "km"), measure(1., "ang")
        >>> a.is_analog(b)
        True
        >>> a, b = measure(1., "km"), measure(1., "ohm")
        >>> a.is_analog(b)
        False
        """
        return self._dimension == other._dimension

    def get_equivalence_factor(self, other) -> float | None:
        """Returns the equivalence factor if other unit is equivalent.

        Equivalent units are units whose dimension are related through a constant
        (e.g. energy and mass, or frequency and temperature).

        Parameters
        ----------
        other : _Unit
            Potentially equivalent unit.

        Returns
        -------
        Optional[float]
            Equivalence factor to transform from one to the other
            or ``None`` if not equivalent.

        See Also
        --------
        _EQUIVALENCES : Dict of equivalent units.
        add_equivalence : Add new equivalence to dict.

        Examples
        --------
        >>> a = measure(1., "1/m")
        >>> a.get_equivalence_factor(measure(1., "J/mol"))
        0.000119627
        >>> print(a.get_equivalence_factor(measure(1., "ang")))
        None
        """

        _, upower = get_trailing_digits(self._uname)
        dimension = tuple(d / upower for d in self._dimension)

        if dimension not in _EQUIVALENCES:
            return None

        powerized_equivalences = {}
        for k, v in _EQUIVALENCES[dimension].items():
            pk = tuple(d * upower for d in k)
            powerized_equivalences[pk] = pow(v, upower)

        odimension = tuple(other._dimension)
        if odimension in powerized_equivalences:
            return powerized_equivalences[odimension]

        return None

    def ounit(self, ounit: str):
        """Set the preferred unit for output.

        Parameters
        ----------
        ounit : str
            Preferred output unit.

        Raises
        ------
        UnitError
            Units are incompatible.

        Notes
        -----
        Returns a modified reference to self not a new object.

        Examples
        --------
        >>> a = measure(1, 'kg m2 / s2')
        >>> print(a)
        1 kg m2 / s2
        >>> print(a.ounit('J'))
        1 J
        """

        out_factor = _str_to_unit(ounit)

        if self.is_analog(out_factor):
            self._ounit = ounit
            self._out_factor = out_factor
            return self

        elif self._equivalent:
            if self.get_equivalence_factor(out_factor) is None:
                raise UnitError("The units are not equivalents")

            self._ounit = ounit
            self._out_factor = out_factor
            return self

        else:
            raise UnitError("The units are not compatible")

    def sqrt(self):
        """Square root of a _Unit.

        Returns
        -------
        _Unit
            New unit which is sqrt of original.

        Examples
        --------
        >>> print(measure(4, 'm2/s2').sqrt())
        2 m1.0 / s-1.0
        """

        return self**0.5

    def toval(self, ounit: str = "") -> float:
        """Returns the numeric value of a unit.

        The value is given in ounit or in the default output unit.

        Parameters
        ----------
        ounit : str
            Unit to convert to.

        Returns
        -------
        float
            Value in output unit.

        Examples
        --------
        >>> v = measure(100, 'km/h')
        >>> v.toval()
        100.0
        >>> v.toval(ounit='m/s')
        27.77777777777778
        """

        newu = copy.deepcopy(self)
        if not ounit:
            ounit = self._ounit

        if ounit is not None:
            out_factor = _str_to_unit(ounit)

            if newu.is_analog(out_factor):
                newu._div_by(out_factor)
                return newu._factor
            elif newu._equivalent:
                if newu.get_equivalence_factor(out_factor) is not None:
                    newu._div_by(out_factor)
                    return newu._factor
                else:
                    raise UnitError("The units are not equivalents")
            else:
                raise UnitError("The units are not compatible")
        else:
            return newu._factor


def _parse_unit(iunit: str) -> _Unit:
    """Parse single unit as a string into a Unit type.

    Parameters
    ----------
    iunit : str
        String to parse.

    Returns
    -------
    _Unit
        Expected unit.

    Raises
    ------
    UnitError
        If string does not contain valid unit.
    """

    max_prefix_length = 0
    for p in _PREFIXES:
        max_prefix_length = max(max_prefix_length, len(p))

    iunit = iunit.strip()

    iunit, upower = get_trailing_digits(iunit)
    if not iunit:
        raise UnitError("Invalid unit")

    for i in range(len(iunit)):
        if UNITS_MANAGER.has_unit(iunit[i:]):
            prefix = iunit[:i]
            iunit = iunit[i:]
            break
    else:
        raise UnitError(f"The unit {iunit} is unknown")

    if prefix:
        if prefix not in _PREFIXES:
            raise UnitError(f"The prefix {prefix} is unknown")
        prefix = _PREFIXES[prefix]
    else:
        prefix = 1.0

    unit = UNITS_MANAGER.get_unit(iunit)

    unit = _Unit(iunit, prefix * unit._factor, *unit._dimension)

    unit **= upower

    return unit


def _str_to_unit(s: str) -> _Unit:
    """Parse general string into unit description.

    Parameters
    ----------
    s : str
        String to parse.

    Returns
    -------
    _Unit
        Parsed unit.

    Raises
    ------
    UnitError
        String is not a valid unit specification.
    """
    if UNITS_MANAGER.has_unit(s):
        unit = UNITS_MANAGER.get_unit(s)
        return copy.deepcopy(unit)

    else:
        unit = _Unit("au", 1.0)

        splitted_units = s.split("/")

        if len(splitted_units) == 1:
            units = splitted_units[0].split(" ")
            for u in units:
                unit *= _parse_unit(u.strip())
            unit._uname = s

        elif len(splitted_units) == 2:
            numerator = splitted_units[0].strip()
            if numerator != "1":
                numerator = numerator.split(" ")
                for u in numerator:
                    unit *= _parse_unit(u.strip())

            denominator = splitted_units[1].strip().split(" ")
            for u in denominator:
                unit /= _parse_unit(u.strip())

            unit._uname = s

        else:
            raise UnitError(f"Invalid unit: {s}")

    return unit


class UnitsManager(metaclass=Singleton):
    """Database dictionary for handling units."""

    _UNITS = {}

    _DEFAULT_DATABASE = (
        PLATFORM.base_directory() / "MDANSE" / "Framework" / "units.json"
    )

    _USER_DATABASE = PLATFORM.application_directory() / "units.json"

    def __init__(self):
        self.load()

    def add_unit(
        self, uname, factor, kg=0, m=0, s=0, K=0, mol=0, A=0, cd=0, rad=0, sr=0
    ):
        UnitsManager._UNITS[uname] = _Unit(
            uname, factor, kg, m, s, K, mol, A, cd, rad, sr
        )

    def delete_unit(self, uname) -> None:
        if uname in UnitsManager._UNITS:
            del UnitsManager._UNITS[uname]

    def get_unit(self, uname) -> _Unit | None:
        return UnitsManager._UNITS.get(uname, None)

    def has_unit(self, uname) -> bool:
        return uname in UnitsManager._UNITS

    def load(self) -> None:
        """Load units from databases.

        Fill self with unit infomration.
        """
        UnitsManager._UNITS.clear()

        d = {}

        with open(UnitsManager._DEFAULT_DATABASE, encoding="utf-8") as fin:
            d.update(json.load(fin))

        try:
            with open(UnitsManager._USER_DATABASE, encoding="utf-8") as fin:
                d.update(json.load(fin))

        except FileNotFoundError:
            self.save()

        finally:
            for uname, udict in d.items():
                factor = udict.get("factor", 1.0)
                dim = udict.get("dimension", [0, 0, 0, 0, 0, 0, 0, 0, 0])
                UnitsManager._UNITS[uname] = _Unit(uname, factor, *dim)

    def save(self):
        """Write self to custom user database."""
        with open(UnitsManager._USER_DATABASE, "w") as fout:
            json.dump(UnitsManager._UNITS, fout, indent=4, cls=UnitsManagerEncoder)

    @property
    def units(self):
        """Direct access to unit database."""
        return UnitsManager._UNITS

    @units.setter
    def units(self, units):
        UnitsManager._UNITS = units


class UnitsManagerEncoder(json.JSONEncoder):
    """Custom encoder for writing units."""

    @singledispatchmethod
    def default(self, obj):
        return json.JSONEncoder.default(self, obj)

    @default.register(UnitsManager)
    def _(self, obj):
        return {k: {"factor": v.factor, "dimension": v.dimension} for k, v in obj.units}

    @default.register(_Unit)
    def _(self, obj):
        return {"factor": obj.factor, "dimension": obj.dimension}


#: Set of units considered directly or indirectly equivalent.
_EQUIVALENCES = defaultdict(dict)


def add_equivalence(dim1, dim2, factor):
    _EQUIVALENCES[dim1][dim2] = factor
    _EQUIVALENCES[dim2][dim1] = 1.0 / factor


def measure(
    val: float, iunit: str = "au", ounit: str = "", *, equivalent: bool = False
) -> _Unit:
    """Create a unit bearing object.

    Parses i/ounits and returns the relevant data object.

    Parameters
    ----------
    val : float
        Value for unit.
    iunit : str
        Input unit.
    ounit : str
        Desired output unit.
    equivalent : bool
        Whether the unit is to be considered "equivalent".

    Returns
    -------
    _Unit
        Desired unit.

    Examples
    --------
    >>> print(measure(1., 'ang'))
    1 ang
    """
    if iunit:
        unit = _str_to_unit(iunit)
        unit *= val
    else:
        unit = _Unit("au", val)

    unit.equivalent = equivalent

    if not ounit:
        ounit = iunit

    unit.ounit(ounit)

    return unit


UNITS_MANAGER = UnitsManager()
# au --> au
add_equivalence((0, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0, 0), 1.0)
# 1J --> 1Hz
add_equivalence(
    (1, 2, -2, 0, 0, 0, 0, 0, 0), (0, 0, -1, 0, 0, 0, 0, 0, 0), 1.50919031167677e33
)
# 1J --> 1K
add_equivalence(
    (1, 2, -2, 0, 0, 0, 0, 0, 0), (0, 0, 0, 1, 0, 0, 0, 0, 0), 7.242971666663e22
)
# 1J --> 1kg
add_equivalence(
    (1, 2, -2, 0, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0, 0, 0, 0), 1.112650055999e-17
)
# 1J --> 1/m
add_equivalence(
    (1, 2, -2, 0, 0, 0, 0, 0, 0), (0, -1, 0, 0, 0, 0, 0, 0, 0), 5.034117012218e24
)
# 1J --> 1J/mol
add_equivalence(
    (1, 2, -2, 0, 0, 0, 0, 0, 0), (1, 2, -2, 0, -1, 0, 0, 0, 0), 6.02214076e23
)
# 1J --> 1rad/s
add_equivalence(
    (1, 2, -2, 0, 0, 0, 0, 0, 0), (0, 0, -1, 0, 0, 0, 0, 1, 0), 9.482522392065263e33
)
# 1Hz --> 1K
add_equivalence(
    (0, 0, -1, 0, 0, 0, 0, 0, 0), (0, 0, 0, 1, 0, 0, 0, 0, 0), 4.79924341590788e-11
)
# 1Hz --> 1kg
add_equivalence(
    (0, 0, -1, 0, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0, 0, 0, 0), 7.37249667845648e-51
)
# 1Hz --> 1/m
add_equivalence(
    (0, 0, -1, 0, 0, 0, 0, 0, 0), (0, -1, 0, 0, 0, 0, 0, 0, 0), 3.33564095480276e-09
)
# 1Hz --> 1J/mol
add_equivalence(
    (0, 0, -1, 0, 0, 0, 0, 0, 0), (1, 2, -2, 0, -1, 0, 0, 0, 0), 3.9903124e-10
)
# 1Hz --> 1rad/s
add_equivalence(
    (0, 0, -1, 0, 0, 0, 0, 0, 0), (0, 0, -1, 0, 0, 0, 0, 1, 0), 6.283185307179586
)
# 1K --> 1kg
add_equivalence(
    (0, 0, 0, 1, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0, 0, 0, 0), 1.53617894312656e-40
)
# 1K --> 1/m
add_equivalence(
    (0, 0, 0, 1, 0, 0, 0, 0, 0), (0, -1, 0, 0, 0, 0, 0, 0, 0), 6.95034751466497e01
)
# 1K --> 1J/mol
add_equivalence((0, 0, 0, 1, 0, 0, 0, 0, 0), (1, 2, -2, 0, -1, 0, 0, 0, 0), 8.31435)
# 1K --> 1rad/s
add_equivalence(
    (0, 0, 0, 1, 0, 0, 0, 0, 0), (0, 0, -1, 0, 0, 0, 0, 1, 0), 130920329782.73508
)
# 1kg --> 1/m
add_equivalence(
    (1, 0, 0, 0, 0, 0, 0, 0, 0), (0, -1, 0, 0, 0, 0, 0, 0, 0), 4.52443873532014e41
)
# 1kg --> 1J/mol
add_equivalence(
    (1, 0, 0, 0, 0, 0, 0, 0, 0), (0, -1, 0, 0, 0, 0, 0, 0, 0), 5.412430195397762e40
)
# 1kg --> 1rad/s
add_equivalence(
    (1, 0, 0, 0, 0, 0, 0, 0, 0), (0, 0, -1, 0, 0, 0, 0, 1, 0), 8.522466107774846e50
)
# 1/m --> 1J/mol
add_equivalence((0, -1, 0, 0, 0, 0, 0, 0, 0), (1, 2, -2, 0, -1, 0, 0, 0, 0), 0.119627)
# 1/m --> 1rad/s
add_equivalence(
    (0, -1, 0, 0, 0, 0, 0, 0, 0), (0, 0, -1, 0, 0, 0, 0, 1, 0), 1883651565.7166505
)
# 1J/mol --> 1rad/s
add_equivalence(
    (1, 2, -2, 0, -1, 0, 0, 0, 0), (0, 0, -1, 0, 0, 0, 0, 1, 0), 15746098887.375164
)
# J/m --> J/m mol
add_equivalence(
    (1, 1, -2, 0, 0, 0, 0, 0, 0), (1, 1, -2, 0, -1, 0, 0, 0, 0), 6.02214076e23
)

if __name__ == "__main__":
    m = measure(1.0, "m")
    m **= 3
