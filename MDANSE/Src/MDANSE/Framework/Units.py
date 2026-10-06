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
from collections import ChainMap, defaultdict
from collections.abc import Callable, Generator, Iterable, Mapping, MutableMapping
from functools import reduce, singledispatchmethod
from numbers import Complex, Real
from operator import add, mul, sub
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Generic,
    Literal,
    NamedTuple,
    Self,
    TypedDict,
    TypeVar,
)

from more_itertools import one

from MDANSE.Chemistry.Databases import _Database
from MDANSE.Core.Platform import PLATFORM
from MDANSE.Core.Singleton import Singleton
from MDANSE.IO.IOUtils import get_trailing_digits, head_tail
from MDANSE.MLogging import LOG


class Dims(NamedTuple):
    """Unit dimension container for comparisons."""

    mass: float = 0  # kg
    length: float = 0  # m
    time: float = 0  # s
    temperature: float = 0  # K
    mols: float = 0  # Mol
    current: float = 0  # A
    luminosity: float = 0  # cd
    angle: float = 0  # rad
    solid_angle: float = 0  # steradian

    _UNAMES = ["kg", "m", "s", "K", "mol", "A", "cd", "rad", "sr"]

    def __pow__(self, amt) -> Self:
        if not isinstance(amt, (float, int)):
            return NotImplemented

        return type(self)(*(dim * amt for dim in self))

    def __sub__(self, other) -> Self:
        if not isinstance(other, Dims):
            return NotImplemented

        return type(self)(*map(sub, self, other))

    def __add__(self, other) -> Self:
        if not isinstance(other, Dims):
            return NotImplemented

        return type(self)(*map(add, self, other))

    @property
    def with_units(self) -> Generator[tuple[str, float]]:
        yield from zip(self._UNAMES, self, strict=True)


_COMMON_DIMS = {
    "au": Dims(),
    "mass": Dims(mass=1),
    "time": Dims(time=1),
    "frequency": Dims(time=-1),
    "length": Dims(length=1),
    "recip": Dims(length=-1),
    "temperature": Dims(temperature=1),
    "energy": Dims(mass=1, length=2, time=-2),
    "velocities": Dims(length=1, time=-1),
    "gradients": Dims(mass=1, length=1, time=-2),
    "ang_velocity": Dims(angle=1, time=-1),
}

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

    class DBInput(TypedDict):
        factor: float
        dimension: tuple[int, int, int, int, int, int, int, int, int]

    _EQUIVALENCES: ClassVar[MutableMapping[Dims, dict[Dims, float]]] = defaultdict(dict)

    def __init__(
        self,
        uname: str,
        factor: float,
        dims: Dims = _COMMON_DIMS["au"],
        *,
        format: str = "g",
        **dim_overrides,
    ):
        self._factor = factor
        self._dimension: Dims = dims._replace(**dim_overrides)
        self.format = format
        self._uname = uname
        self._ounit = None
        self._out_factor = None
        self.equivalent = False

    def __add__(self, other: _Unit) -> Self:
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
        elif self.equivalent:
            equivalence_factor = u.get_equivalence_factor(other)
            if equivalence_factor is None:
                raise UnitError("The units are not equivalent")

            u._factor += other._factor / equivalence_factor
        else:
            raise UnitError("Incompatible units.")

        return u

    def __sub__(self, other: _Unit) -> Self:
        """Subtract _Unit instances.

        To be subtracted, the units have to be analog or equivalent.

        >>> print(measure(20, 'km') + measure(10, 'm'))
        20.01 km
        """
        u = copy.deepcopy(self)

        if u.is_analog(other):
            u._factor -= other._factor
        elif u.equivalent:
            equivalence_factor = u.get_equivalence_factor(other)
            if equivalence_factor is None:
                raise UnitError("The units are not equivalent")

            u._factor -= other._factor / equivalence_factor
        else:
            raise UnitError("Incompatible units")

        return u

    def __truediv__(self, other: Complex | Real | _Unit) -> Self:
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
        if isinstance(other, (Complex, Real)):
            u._factor /= other
        elif isinstance(other, _Unit):
            u._div_by(other)
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

        return u

    def __floordiv__(self, other: Real | _Unit) -> Self:
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
        if isinstance(other, Real):
            u._factor //= other
        elif isinstance(other, _Unit):
            u._div_by(other)

            if u._factor.imag:
                raise TypeError("Cannot floor complex number")

            u._factor = math.floor(u._factor)
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

        return u

    def __mul__(self, other: Real | Complex | _Unit) -> Self:
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
        if isinstance(other, (Real, Complex)):
            u._factor *= other
        elif isinstance(other, _Unit):
            u._mult_by(other)
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

        return u

    def __pow__(self, n: float) -> Self:
        """Raise a _Unit to a factor.

        Examples
        --------
        >>> print(measure(10.5, 'm/s')**2)
        110.25 m2 / s2
        """
        output_unit = copy.copy(self)
        output_unit._ounit = None
        output_unit._out_factor = None
        output_unit._factor = output_unit._factor**n
        output_unit._dimension = output_unit._dimension**n

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

    def __ceil__(self) -> _Unit:
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

        if r._factor.imag:
            raise TypeError("Cannot ceil complex number.")

        if r._ounit is not None:
            val = math.ceil(r.toval(r._ounit))
            newu = _Unit("au", val)
            newu *= _Unit.from_str(r._ounit)
            return newu.ounit(r._ounit)
        else:
            r._factor = math.ceil(r._factor)
            return r

    def __floor__(self) -> _Unit:
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

        if r._factor.imag:
            raise TypeError("Cannot floor complex number.")

        if r._ounit is not None:
            val = math.floor(r.toval(r._ounit))
            newu = _Unit("au", val)
            newu *= _Unit.from_str(r._ounit)
            return newu.ounit(r._ounit)
        else:
            r._factor = math.floor(r._factor)
            return r

    def __round__(self, ndigits: int | None = None) -> _Unit:
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

        if r._factor.imag:
            raise TypeError("Cannot round complex number.")

        if r._ounit is not None:
            val = round(r.toval(r._ounit), ndigits)
            newu = _Unit("au", val)
            newu *= _Unit.from_str(r._ounit)
            return newu.ounit(r._ounit)
        else:
            r._factor = round(r._factor, ndigits)
            return r

    ceiling = __ceil__
    floor = __floor__
    round = __round__

    def __iadd__(self, other: _Unit) -> Self:
        """Add _Unit instances.

        See Also
        --------
        __add__
        """

        if self.is_analog(other):
            self._factor += other._factor
        elif self.equivalent:
            equivalence_factor = self.get_equivalence_factor(other)
            if equivalence_factor is None:
                raise UnitError("The units are not equivalent")
            self._factor += other._factor / equivalence_factor

        else:
            raise UnitError("Incompatible units")

        return self

    def __itruediv__(self, other: Complex | Real | Self):
        """Divide _Unit instances.

        See Also
        --------
        __div__
        """

        if isinstance(other, (Real, Complex)):
            self._factor /= other
        elif isinstance(other, _Unit):
            self._div_by(other)
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

        return self

    def __ifloordiv__(self, other):
        """Divide _Unit instances and truncate.

        See Also
        --------
        __truediv__
        """
        self._div_by(other)
        self._factor = math.floor(self._factor)
        return self

    def __imul__(self, other: Real | Complex | _Unit) -> Self:
        """
        Multiply _Unit instances.

        See Also
        --------
        __mul__
        """

        if isinstance(other, (Real, Complex)):
            self._factor *= other
        elif isinstance(other, _Unit):
            self._mult_by(other)
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

        return self

    def __ipow__(self, n: float) -> Self:
        self._factor = self._factor**n
        self._dimension = self._dimension**n

        self._ounit = None
        self._out_factor = None

        return self

    def __isub__(self, other: _Unit) -> Self:
        """Subtract _Unit instances.  See __sub__."""

        if self.is_analog(other):
            self._factor -= other._factor
        elif self.equivalent:
            equivalence_factor = self.get_equivalence_factor(other)
            if equivalence_factor is None:
                raise UnitError("The units are not equivalent")
            self._factor -= other._factor / equivalence_factor
        else:
            raise UnitError("Incompatible units")

        return self

    def __radd__(self, other: _Unit) -> Self:
        """Add _Unit instances.

        See Also
        --------
        __add__
        """
        return self.__add__(other)

    def __rdiv__(self, other: Real | Complex | _Unit) -> Self:
        u = copy.deepcopy(self)
        if isinstance(other, (Real, Complex)):
            u._factor /= other
        elif isinstance(other, _Unit):
            u._div_by(other)
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

        return u

    def __rmul__(self, other: Real | Complex | _Unit) -> Self:
        """Multiply _Unit instances.  See __mul__."""

        u = copy.deepcopy(self)
        if isinstance(other, (Real, Complex)):
            u._factor *= other
        elif isinstance(other, _Unit):
            u._mult_by(other)
        else:
            raise UnitError(f"Invalid operand {other} with type {type(other)}")

        return u

    def __rsub__(self, other: _Unit) -> _Unit:
        """Subtract _Unit instances.  See __sub__."""

        return other.__sub__(self)

    def __str__(self) -> str:
        unit = copy.copy(self)

        if self._ounit is not None and self._out_factor is not None:
            u = copy.deepcopy(self)
            u._div_by(self._out_factor)

            return f"{u._factor:{self.format}} {self._ounit}"

        s = format(unit._factor, self.format)

        positive_units = []
        negative_units = []
        for uname, uval in unit._dimension.with_units:
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

        return s

    def _div_by(self, other: _Unit) -> None:
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
            self._dimension = Dims()
        elif self.equivalent:
            equivalence_factor = self.get_equivalence_factor(other)
            if equivalence_factor is None:
                raise UnitError(
                    f"The units {self._uname} and {other._uname} are not equivalent"
                )
            self._factor /= other._factor / equivalence_factor
            self._dimension = Dims()

        else:
            self._factor /= other._factor
            self._dimension -= other._dimension

        self._ounit = None
        self._out_factor = None

    def _mult_by(self, other: _Unit) -> None:
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
            self._dimension = self._dimension**2
        elif self.equivalent:
            equivalence_factor = self.get_equivalence_factor(other)
            if equivalence_factor is None:
                raise UnitError(
                    f"The units {self._uname} and {other._uname} are not equivalent"
                )

            self._factor *= other._factor / equivalence_factor
            self._dimension = self._dimension**2
            return
        else:
            self._factor *= other._factor
            self._dimension = self._dimension + other._dimension

        self._ounit = None
        self._out_factor = None

    @property
    def dimension(self) -> Dims:
        """Getter for _dimension attribute. Returns a copy."""

        return self._dimension

    @property
    def factor(self) -> complex | float:
        """Getter for _factor attribute."""

        return self._factor

    def is_analog(self, other: _Unit) -> bool:
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

    def get_equivalence_factor(self, other: _Unit) -> float | None:
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
        dimension = self._dimension ** (1 / upower)

        if dimension not in self._EQUIVALENCES:
            return None

        powerized_equivalences = {
            k**upower: v**upower for k, v in self._EQUIVALENCES[dimension].items()
        }
        return powerized_equivalences.get(other._dimension)

    def ounit(self, ounit: str) -> Self:
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

        out_factor = _Unit.from_str(ounit)

        if not self.is_analog(out_factor) and not self.equivalent:
            raise UnitError(f"The units {self._uname} and {ounit} are not compatible.")

        if (
            not self.is_analog(out_factor)
            and self.equivalent
            and self.get_equivalence_factor(out_factor) is None
        ):
            raise UnitError(f"The units {self._uname} and {ounit} are not equivalents")

        self._ounit = ounit
        self._out_factor = out_factor
        return self

    def sqrt(self) -> Self:
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

    def toval(self, ounit: str | None = "") -> complex | float:
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

        if ounit is None:
            return newu._factor

        out_factor = _Unit.from_str(ounit)

        if newu.is_analog(out_factor):
            newu._div_by(out_factor)
        elif newu.equivalent:
            if newu.get_equivalence_factor(out_factor) is None:
                raise UnitError("The units are not equivalents")

            newu._div_by(out_factor)
        else:
            raise UnitError(f"The units {newu} and {ounit} are not compatible")

        return newu._factor

    @classmethod
    def _au(cls) -> Self:
        """Null unit."""
        return cls("au", 1.0)

    @classmethod
    def _parse_component(cls, in_unit: str) -> Self:
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
        iunit = in_unit.strip()

        iunit, upower = get_trailing_digits(iunit)

        if not iunit:
            raise UnitError(f"Invalid unit ({in_unit}).")

        trial = (
            (_PREFIXES.get(pref, 1.0), unit)
            for pref, sunit in head_tail(iunit)
            if (not pref or pref in _PREFIXES)
            and (unit := UNITS_MANAGER.get_unit(sunit))
        )
        prefix_mult, unit = one(
            trial,
            too_long=UnitError(f"More than one possible unit for {in_unit}."),
            too_short=UnitError(f"The unit {iunit} is unknown"),
        )

        return cls(iunit, prefix_mult * unit._factor, unit.dimension) ** upower

    @classmethod
    def _parse_unit(cls, s: str) -> Self:
        return reduce(mul, map(cls._parse_component, s.split(" ")), cls._au())

    @classmethod
    def from_str(cls, s: str) -> _Unit:
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
        if unit := UNITS_MANAGER.get_unit(s):
            return copy.deepcopy(unit)

        match list(map(str.strip, s.split("/"))):
            case [value]:
                unit = _Unit._parse_unit(value)
            case ["1", den]:
                unit = _Unit._au() / _Unit._parse_unit(den)
            case [num, den]:
                unit = _Unit._parse_unit(num) / _Unit._parse_unit(den)
            case _:
                raise UnitError(f"Invalid unit: {s}")

        unit._uname = s

        return unit

    @classmethod
    def add_equivalence(cls, dim1: Dims, dim2: Dims, factor: float) -> None:
        cls._EQUIVALENCES[dim1][dim2] = factor
        cls._EQUIVALENCES[dim2][dim1] = 1.0 / factor


class UnitsManager(_Database):
    """Database dictionary for handling units."""

    _UNITS: ClassVar[ChainMap[str, _Unit]] = ChainMap()

    _DEFAULT_DATABASE = PLATFORM.base_directory / "MDANSE" / "Framework" / "units.json"
    _LOCAL_PATH = "units.json"

    class Encoder(json.JSONEncoder):
        """Custom encoder for writing units."""

        def default(self, o):
            match o:
                case UnitsManager():
                    return {
                        k: {"factor": v.factor, "dimension": v.dimension}
                        for k, v in o.units
                    }
                case _Unit(factor=fac, dimension=dim):
                    return {"factor": fac, "dimension": tuple(dim)}
                case _:
                    return json.JSONEncoder.default(self, o)

    def __init__(self):
        self._load()

    def add_unit(
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
        UnitsManager._UNITS[uname] = _Unit(
            uname, factor, Dims(kg, m, s, K, mol, A, cd, rad, sr)
        )

    def delete_unit(self, uname: str) -> None:
        if uname in UnitsManager._UNITS:
            del UnitsManager._UNITS[uname]

    def get_unit(self, uname: str) -> _Unit | None:
        return UnitsManager._UNITS.get(uname, None)

    def has_unit(self, uname: str) -> bool:
        return uname in UnitsManager._UNITS

    @staticmethod
    def with_prefixes(bases: Iterable[str]) -> set[str]:
        return {f"{pref}{unit}" for pref in _PREFIXES for unit in bases}

    @property
    def possible_units(self) -> set[str]:
        """All possible combined units."""
        return self.with_prefixes(UnitsManager._UNITS)

    def has_conflict(
        self, uname: str, alldefaults: set[str] | None = None
    ) -> set[str] | None:
        """Catch conflicts between added units."""
        if alldefaults is None:
            alldefaults = self.possible_units

        units = {f"{pref}{uname}" for pref in _PREFIXES}
        if conflict := units & alldefaults:
            return conflict
        return None

    def _load(
        self,
        user_database: Path | str | None = None,
        default_database: Path | str | None = None,
    ) -> None:
        """Load units from databases.

        Fill self with unit infomration.
        """
        super()._load(user_database, default_database)

        defaults = {
            name: decode_from_json(name, udict)
            for name, udict in self._default_data.items()
        }
        custom = {
            name: decode_from_json(name, udict) for name, udict in self._data.items()
        }

        alldefaults = self.with_prefixes(defaults)
        for unit in list(custom):
            if unit in defaults or unit == "kg":
                LOG.warning(
                    f'Skipping custom unit {unit} due to conflict. This is likely due to an old "units.json". No action should be necessary.'
                )
                del custom[unit]

            if conflict := self.has_conflict(unit, alldefaults):
                raise UnitError(
                    f'Custom unit ({unit}) potentially ambiguous with ({" and ".join(conflict)}). To fix this error remove "{unit}" from {self._USER_DATABASE}.'
                )

        UnitsManager._UNITS = ChainMap(custom, defaults)
        self.data = UnitsManager._UNITS

    def save(self):
        """Write self to custom user database."""
        with open(self._user_database, "w") as fout:
            json.dump(UnitsManager._UNITS.maps[0], fout, indent=4, cls=self.Encoder)

    @property
    def units(self) -> MutableMapping[str, _Unit]:
        """Direct access to unit database."""
        return UnitsManager._UNITS

    @classmethod
    def filter_by_dimension(cls, dims: Dims) -> dict[str, _Unit]:
        return {
            name: unit for name, unit in cls._UNITS.items() if unit.dimension == dims
        }

    @classmethod
    def filter_by_common_dimension(
        cls,
        dim: Literal[
            "energy", "velocities", "gradients", "time", "length", "reciprocal", "mass"
        ],
    ) -> dict[str, _Unit]:
        return cls.filter_by_dimension(_COMMON_DIMS[dim])


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
        unit = _Unit.from_str(iunit)
        unit *= val
    else:
        unit = _Unit("au", val)

    unit.equivalent = equivalent

    if not ounit:
        ounit = iunit

    unit.ounit(ounit)

    return unit


def decode_from_json(uname: str, udict: _Unit.DBInput) -> _Unit:
    """Read Unit from json database."""
    factor = udict.get("factor", 1.0)
    dim = udict.get("dimension", (0, 0, 0, 0, 0, 0, 0, 0, 0))
    return _Unit(uname, factor, Dims(*dim))


UNITS_MANAGER = UnitsManager()

for a, b, factor in (
    (Dims(), Dims(), 1.0),  # au --> au
    (
        _COMMON_DIMS["energy"],
        _COMMON_DIMS["frequency"],
        1.50919031167677e33,
    ),  # 1J -> 1Hz
    (
        _COMMON_DIMS["energy"],
        _COMMON_DIMS["temperature"],
        7.242971666663e22,
    ),  # 1J --> 1K
    (_COMMON_DIMS["energy"], _COMMON_DIMS["mass"], 1.112650055999e-17),  # 1J --> 1kg
    (_COMMON_DIMS["energy"], _COMMON_DIMS["recip"], 5.034117012218e24),  # 1J --> 1/m
    (
        _COMMON_DIMS["energy"],
        _COMMON_DIMS["energy"] - Dims(mols=1),
        6.02214076e23,
    ),  # 1J --> 1J/mol
    (
        _COMMON_DIMS["energy"],
        _COMMON_DIMS["ang_velocity"],
        9.482522392065263e33,
    ),  # 1J --> 1rad/s
    (
        _COMMON_DIMS["frequency"],
        _COMMON_DIMS["temperature"],
        4.79924341590788e-11,
    ),  # 1Hz --> 1K
    (
        _COMMON_DIMS["frequency"],
        _COMMON_DIMS["mass"],
        7.37249667845648e-51,
    ),  # 1Hz --> 1kg
    (
        _COMMON_DIMS["frequency"],
        _COMMON_DIMS["recip"],
        3.33564095480276e-09,
    ),  # 1Hz --> 1/m
    (
        _COMMON_DIMS["frequency"],
        _COMMON_DIMS["energy"] - Dims(mols=1),
        3.9903124e-10,
    ),  # 1Hz --> 1J/mol
    (
        _COMMON_DIMS["frequency"],
        _COMMON_DIMS["ang_velocity"],
        6.283185307179586,
    ),  # 1Hz --> 1rad/s
    (
        _COMMON_DIMS["temperature"],
        _COMMON_DIMS["mass"],
        1.53617894312656e-40,
    ),  # 1K --> 1kg
    (
        _COMMON_DIMS["temperature"],
        _COMMON_DIMS["recip"],
        6.95034751466497e01,
    ),  # 1K --> 1/m
    (
        _COMMON_DIMS["temperature"],
        _COMMON_DIMS["energy"] - Dims(mols=1),
        8.31435,
    ),  # 1K --> 1J/mol
    (
        _COMMON_DIMS["temperature"],
        _COMMON_DIMS["ang_velocity"],
        130920329782.73508,
    ),  # 1K --> 1rad/s
    (_COMMON_DIMS["mass"], _COMMON_DIMS["recip"], 4.52443873532014e41),  # 1kg --> 1/m
    (_COMMON_DIMS["mass"], _COMMON_DIMS["energy"] - Dims(mols=1), 5.412430195397762e40),
    (  # 1kg --> 1J/mol
        _COMMON_DIMS["mass"],
        _COMMON_DIMS["ang_velocity"],
        8.522466107774846e50,
    ),  # 1kg --> 1rad/s
    (
        _COMMON_DIMS["recip"],
        _COMMON_DIMS["energy"] - Dims(mols=1),
        0.119627,
    ),  # 1/m --> 1J/mol
    (
        _COMMON_DIMS["recip"],
        _COMMON_DIMS["ang_velocity"],
        1883651565.7166505,
    ),  # 1/m --> 1rad/s
    (
        _COMMON_DIMS["energy"] - Dims(mols=1),
        _COMMON_DIMS["ang_velocity"],
        15746098887.375164,
    ),  # 1J/mol --> 1rad/s
    (
        _COMMON_DIMS["energy"] + Dims(length=-1),
        _COMMON_DIMS["energy"] + Dims(mols=-1, length=-1),
        6.02214076e23,
    ),  # J/m --> J/m mol
):
    _Unit.add_equivalence(a, b, factor)
