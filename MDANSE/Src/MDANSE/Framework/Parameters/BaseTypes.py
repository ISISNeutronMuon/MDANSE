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

import re
from collections.abc import Callable, Iterable, Iterator, Sequence
from enum import auto
from functools import singledispatchmethod
from math import isclose
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Generic,
    Literal,
    SupportsFloat,
    SupportsIndex,
    SupportsInt,
    cast,
    overload,
)

import numpy as np
import numpy.typing as npt
from more_itertools import always_iterable, numeric_range
from typing_extensions import Never, Self, TypeVar

from MDANSE.Framework.Parameters.Parameters import (
    ConfigError,
    ConfigureDescriptor,
    MinMax,
)
from MDANSE.Framework.Parameters.UtilTypes import (
    Depends,
    EmptyDict,
    K,
    Num,
    SupportsDict,
    V,
)
from MDANSE.IO.IOUtils import UCEnum, json_handler

if TYPE_CHECKING:
    from MDANSE.Framework.Parameters.Parameters import Configurable

cjoin = ", ".join

__all__ = [
    "Array",
    "Boolean",
    "Float",
    "Integer",
    "PathParam",
    "Range",
    "String",
    "Vector",
]


def _nop(x: str) -> str:
    return x


class StrCases(UCEnum):
    """Case settings for string parameters"""

    PRESERVE = _nop
    UPPER = str.upper
    LOWER = str.lower
    TITLE = str.title


class NumericRange(Generic[Num]):
    """Wrapper for :class:`more_itertools.numeric_range` for non-private start stop."""

    def __init__(self, *params: Num):
        try:
            self.iterator = numeric_range(*params)
        except Exception as err:
            raise ConfigError("Unable to build numeric range.") from err

    def __iter__(self) -> Iterator[Num]:
        return iter(self.iterator)

    @overload
    def __getitem__(self, index: slice) -> numeric_range[Num, Num]: ...

    @overload
    def __getitem__(self, index: SupportsIndex) -> Num: ...

    def __getitem__(self, index):
        return self.iterator[index]

    def __len__(self) -> int:
        return len(self.iterator)

    @property
    def start(self) -> Num:
        return self.iterator._start  # type: ignore

    @property
    def stop(self) -> Num:
        return self.iterator._stop  # type: ignore

    @property
    def step(self) -> Num:
        return self.iterator._step  # type: ignore

    def __str__(self) -> str:
        return str(self.iterator)

    def __repr__(self) -> str:
        return repr(self.iterator)

    def __int__(self) -> NumericRange[int]:
        return NumericRange(int(self.start), int(self.stop), int(self.step))


Bools = Literal["true", "false", "yes", "no", "y", "n", "1", "0", 1, 0, True, False]
BCB = TypeVar("BCB", default=bool)


class Boolean(ConfigureDescriptor[Bools, bool, BCB]):
    """
    This Configurator allows to input a Boolean Value (True or False).

    The input value can be directly provided as a Python boolean or by the using the following (standard)
     representation of a boolean: 'true'/'false', 'yes'/'no', 'y'/'n', '1'/'0', 1/0
    """

    _alias = {
        True: True,
        "true": True,
        "yes": True,
        "y": True,
        "1": True,
        False: False,
        "false": False,
        "no": False,
        "n": False,
        "0": False,
    }

    def __init__(
        self,
        default: Bools = False,
        **params,
    ):
        super().__init__(default=default, **params)

    def validate(self, value: Bools, deps: Depends, /) -> bool:
        test = value.lower() if isinstance(value, str) else value

        if test not in self._alias:
            raise ConfigError(f"Unable to convert value ({value!r}) to bool.")

        return self._alias[test]


FCB = TypeVar("FCB", default=float)


class Float(MinMax[float], ConfigureDescriptor[SupportsFloat, float, FCB]):
    """Floating point parameter.

    Parameters
    ----------
    non_zero : float | None
        Whether data should be non-zero.

        If None:
            Vector can be zero.
        Otherwise:
            Tolerance of non-zero.
    optional : bool
        Allows value to be None
    """

    def __init__(
        self,
        non_zero: float | None = None,
        optional: bool = False,
        **params,
    ):
        super().__init__(**params)
        self.optional = optional
        self.non_zero = non_zero

    @overload
    def validate(self, value: None, deps: Depends, /) -> None: ...

    @overload
    def validate(self, value: SupportsFloat, deps: Depends, /) -> float: ...

    def validate(self, value, deps, /):
        if self.optional and value is None:
            return None

        try:
            value = float(value)
        except ValueError as error:
            raise ConfigError(f"Value ({value}) is not a valid float.") from error

        super().validate(value, deps)

        ranges = self.get_ranges(deps)

        self.validate_range(value, ranges)

        if self.non_zero is not None and isclose(value, 0.0, abs_tol=self.non_zero):
            raise ConfigError(f"Non-null val ({value}) is too close to zero.")

        return value


ICB = TypeVar("ICB", default=int)


class Integer(MinMax[int], ConfigureDescriptor[SupportsInt, int, ICB]):
    """Integer parameter."""

    def __init__(
        self,
        optional: bool = False,
        **params,
    ):
        super().__init__(**params)
        self.optional = optional

    @overload
    def validate(self, value: None, deps: Depends, /) -> None: ...

    @overload
    def validate(self, value: SupportsInt, deps: Depends, /) -> int: ...

    def validate(self, value, deps, /):
        if self.optional and value is None:
            return None

        try:
            value = int(value)
        except ValueError as error:
            raise ConfigError(f"Value ({value}) is not a valid integer.") from error

        ranges = self.get_ranges(deps)

        self.validate_range(value, ranges)

        return value


DCB = TypeVar("DCB", default=dict[K, V])


class Dict(
    ConfigureDescriptor[
        Iterable[tuple[K, V]] | dict[K, V] | str | Path,
        dict[K, V],
        DCB,
    ]
):
    """
    Dictionary parameter.

    Notes
    -----
    `choices` are keys which *must* be present in the dict.

    `exclude` are keys which *must not* be present in the dict.
    """

    def __init__(self, *, fixed: bool = False, choices: Sequence[K] = (), **params):
        super().__init__(choices=choices, **params)

        self.fixed = fixed

    def _validate_choices(  # ty: ignore
        self,
        value: dict[K, V],
        choices: set[K] | None = None,
    ) -> bool:
        choice = self.choices if choices is None else choices

        if missing := choice - value.keys():
            raise ConfigError(
                f"Required keys ({cjoin(map(str, missing))}) are missing."
            )
        return True

    @overload
    def validate(self, value: None, deps: Depends, /) -> EmptyDict | None: ...

    @overload
    def validate(
        self, value: SupportsDict | str | Path, deps: Depends, /
    ) -> dict[K, V]: ...

    def validate(
        self,
        value: SupportsDict | str | Path | None,
        deps: Depends,
        /,
    ) -> dict[K, V] | None:
        if self.optional and value is None:
            return None

        if not isinstance(value, (dict, str, Path)) and value is not None:
            value = dict(value)
        else:
            try:
                value = json_handler(value)
            except Exception as err:
                raise ConfigError("Failed to build dict.") from err

        value = super().validate(value, deps)

        if self.fixed and (extraneous := value.keys() - self.choices):
            raise ConfigError(
                f"Extra keys are present ({cjoin(map(str, extraneous))}), "
                f"expected: {cjoin(map(str, self.choices))}."
            )

        return value

    @overload
    def __get__(self, owner: Configurable, objtype: type) -> dict[K, V] | None: ...

    @overload
    def __get__(self, owner: None, objtype: None) -> Self: ...

    # Dict validated on __get__ due to underlying mutable object.
    def __get__(
        self,
        owner: Configurable | None,
        objtype: type,
    ):
        if owner is None:
            return self

        value = super().__get__(owner, objtype)
        deps = self._get_deps(owner)
        return self.validate(value, deps)


SCB = TypeVar("SCB", default=str)


class String(ConfigureDescriptor[str, str, SCB]):
    """String parameter.

    Parameters
    ----------
    case : Callable[[str], str]
        Function to modify case if needed.
    regex : str | re.Pattern | None, optional
        Regular Expression to validate string against.
    """

    def __init__(
        self,
        *,
        case: Callable[[str], str] | StrCases = StrCases.PRESERVE,
        regex: str | re.Pattern | None = None,
        **params,
    ):
        super().__init__(**params)
        self.case = StrCases(case)
        self.regex = regex

    @property
    def regex(self) -> re.Pattern | None:
        """Validation regular expression."""
        return self._regex

    @regex.setter
    def regex(self, value: str | re.Pattern | None) -> None:
        if value is None:
            self._regex = None
            return
        self.regex = re.compile(value)

    def validate(self, value: str, deps: Depends, /) -> str:
        try:
            value = str(value)
        except ValueError as error:
            raise ConfigError(f"Value ({value}) is not a valid str.") from error

        value = self.case.value(value)

        super().validate(value, deps)

        if self.regex is not None and not self.regex.match(value):
            raise ConfigError(
                f"Value ({value}) does not match requirement {self.regex.pattern}."
            )

        return value


PCB = TypeVar("PCB", default=Path)


class PathParam(ConfigureDescriptor[str | Path, Path, PCB]):
    """Path parameter.

    Parameters
    ----------
    mode : FileModes
        Required file status.
    extensions : dict[str, str], optional
        Expected file extensions (for GUI)
    directory : bool (unused)
        Whether path can refer to a directory.
    """

    class FileModes(UCEnum):
        MUST_EXIST = auto()
        MAY_EXIST = auto()
        MUST_NOT_EXIST = auto()

        R = MUST_EXIST
        W = MAY_EXIST
        X = MUST_NOT_EXIST
        A = MUST_EXIST

    def __init__(
        self,
        mode: FileModes | str,
        *,
        optional: bool = False,
        extensions: dict[str, str] | None = None,
        directory: bool = False,
        on_set: Callable[[Self, Path, Depends], PCB] | None = None,
        **params,
    ):
        super().__init__(on_set=on_set, **params)
        self.optional = optional

        self.mode = (
            self.FileModes[mode.upper()]
            if isinstance(mode, str)
            else self.FileModes(mode)
        )

        self.extension = extensions or {}
        self.extension.setdefault("All files", "*")
        self.directory = directory

    def validate(self, value: Path | str, deps: Depends, /) -> Path | None:
        if self.optional and not value:
            return None

        try:
            value = Path(value).expanduser()
        except TypeError as error:
            raise ConfigError(f"Value ({value}) is not a valid Path.") from error

        super().validate(value, deps)

        if self.mode is self.FileModes.MAY_EXIST:
            pass
        elif self.mode is self.FileModes.MUST_EXIST and not value.exists():
            raise ConfigError(f"File at {value!r} does not exist.")
        elif self.mode is self.FileModes.MUST_NOT_EXIST and value.exists():
            raise ConfigError(f"File at {value!r} must not exist.")

        return value


class ManyPath(PathParam[PCB]):
    """Parameter for specifying multiple files simultaneously.

    Files can be defined as either a Sequence of paths or
    a semi-colon separated list of paths.
    """

    def validate(
        self, value: Sequence[Path | str] | Path | str, deps: Depends, /
    ) -> tuple[Path | str | None, ...]:
        if self.optional and not value:
            return ()

        if isinstance(value, str):
            value = value.split(";")

        return tuple(
            super(ManyPath, self).validate(pth, deps)
            for pth in always_iterable(value)
            if pth
        )


RCB = TypeVar("RCB", default=NumericRange[Num])


class Range(
    MinMax[Num],
    ConfigureDescriptor[
        int
        | float
        | list[Num]
        | tuple[Num, ...]
        | range
        | numeric_range
        | NumericRange[Num],
        NumericRange[Num],
        RCB,
    ],
):
    """Range parameter.

    Parameters
    ----------
    include_last : bool
        Whether range is inclusive (True) or exclusive (False).
    dtype : type
        Return value data type.
    """

    def __init__(
        self,
        *args,
        include_last: bool = False,
        dtype: type = float,
        **params,
    ):
        super().__init__(*args, **params)
        self.dtype = dtype
        self.include_last = include_last

    @singledispatchmethod
    def validate(self, value, deps) -> NumericRange:
        raise ConfigError(
            f"Do not know how to convert {type(value).__name__} to NumericRange"
        )

    @validate.register(NumericRange)
    def _(self, value: NumericRange[Num], deps: Depends, /) -> NumericRange[Num]:
        if self.include_last:
            value = NumericRange(value.start, value.stop + value.step, value.step)

        ranges = self.get_ranges(deps)

        self.validate_range(value.start, ranges)
        self.validate_range(value.stop, ranges)

        return value

    @validate.register
    def _(self, value: range, deps: Depends, /) -> NumericRange[int]:
        cls = NumericRange(value.start, value.stop, value.step)
        return self.validate(cls, deps)

    @validate.register(numeric_range)
    def _(self, value: numeric_range[Num, Num], deps: Depends, /) -> NumericRange[Num]:
        cls = NumericRange(value._start, value._stop, value._step)
        return self.validate(cls, deps)

    @validate.register(int)
    @validate.register(float)
    def _(self, value: Num, deps: Depends, /) -> NumericRange[Num]:
        cls = NumericRange(self.dtype(value))
        return self.validate(cls, deps)

    @validate.register(list)
    @validate.register(tuple)
    def _(
        self, value: list[Num] | tuple[Num, ...], deps: Depends, /
    ) -> NumericRange[Num]:
        cls = NumericRange(*map(self.dtype, value))
        return self.validate(cls, deps)


ACB = TypeVar("ACB", default=np.ndarray)


class Array(ConfigureDescriptor[str | npt.ArrayLike, np.ndarray, ACB]):
    """Array parameter.

    Parameters
    ----------
    shape : tuple[int, ...]
        Expected data shape.
    dtype : type
        Array datatype to return.
    non_zero : bool
        Whether array must have a non-zero critical value.
    """

    def __init__(
        self,
        *,
        shape: tuple[int, ...],
        dtype: npt.DTypeLike = np.float64,
        non_zero: bool = False,
        **params,
    ):
        super().__init__(**params)

        self.shape = shape
        self.non_zero = non_zero
        self.dtype = dtype

    @overload
    def validate(self, value: None, deps: Depends, /) -> None: ...

    @overload
    def validate(self, value: str | npt.ArrayLike, deps: Depends, /) -> np.ndarray: ...

    def validate(
        self, value: str | npt.ArrayLike, deps: Depends, /
    ) -> np.ndarray | None:
        if self.optional and value is None:
            return None
        elif isinstance(value, str):
            value = np.fromstring(value, dtype=self.dtype)
        else:
            value = np.array(value, dtype=self.dtype)

        value = super().validate(value, deps)

        assert isinstance(value, np.ndarray)

        if self.non_zero and (
            (value.ndim == 2 and np.isclose(np.linalg.det(value), 0.0))
            or (value.ndim == 1 and np.isclose(np.linalg.norm(value), 0.0))
        ):
            raise ConfigError(
                f"Non-zero {type(self).__name__} has zero critical value."
            )

        return value


class Vector(Array[ACB]):
    """Vector parameter.

    Subset of array type.

    Parameters
    ----------
    length : int
        Length of vector.
    normalise : bool
        Whether vector should be normalised on return.
    """

    def __init__(
        self,
        *,
        length: int = 3,
        shape: None = None,
        normalise: bool = False,
        **params,
    ):
        if shape is not None:
            raise ConfigError("Cannot pass explicit `shape`, use `length`.")

        super().__init__(shape=(length,), **params)
        self.normalise = normalise

    @overload
    def validate(self, value: None, deps: Depends, /) -> None: ...

    @overload
    def validate(self, value: str | npt.ArrayLike, deps: Depends, /) -> np.ndarray: ...

    def validate(self, value, deps: Depends, /) -> np.ndarray | None:
        if self.optional and value is None:
            return None

        value = super().validate(value, deps)

        if self.normalise:
            value /= np.linalg.norm(value)

        return value
