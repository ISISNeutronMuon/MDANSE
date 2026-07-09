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

import json
import re
import time
from collections import UserDict
from collections.abc import Callable, Collection, Iterable, Iterator, Sequence
from enum import Enum
from functools import singledispatch
from itertools import count, filterfalse, islice
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, overload

import numpy as np
from more_itertools import first_true, last, take, value_chain

from MDANSE.MLogging import LOG

if TYPE_CHECKING:
    from MDANSE.Framework.Jobs.JobStatus import JobInfo

K = TypeVar("K", str, bytes)
V = TypeVar("V")

MAX_FILE_COUNT = 2048


class SupportsStr(Protocol):
    """Any class which supports __str__ method"""

    def __str__(self) -> str: ...


class SupportsRepr(Protocol):
    """Any class which supports __repr__ method"""

    def __repr__(self) -> str: ...


SupportsFormat = SupportsStr | SupportsRepr


class UCDict(UserDict[K, V]):
    """Case insensitive dictionary where all keys are uppercase."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._raw = {}

    def __setitem__(self, key: K, item: V) -> None:
        super().__setitem__(key.upper(), item)
        self._raw[key.upper()] = key

    def __getitem__(self, key: K) -> V:
        return super().__getitem__(key.upper())

    def __contains__(self, key: K) -> bool:
        return super().__contains__(key.upper())

    @property
    def raw_mapping(self) -> dict[K, K]:
        return self._raw.copy()

    @property
    def raw_dict(self) -> dict[K, V]:
        return {key: self[key] for key in self._raw.values()}


class UCEnum(Enum):
    """Uppercase enumerated type.

    Parses unknown strings as uppercase underscore separated params.
    """

    @classmethod
    def _missing_(cls, value):
        if not isinstance(value, str):
            return NotImplemented

        value = "_".join(value.split())
        return vars(cls).get(value.upper())


class MDANSEEncoder(json.JSONEncoder):
    """Custom JSON encoder to encode paths as strings."""

    def default(self, obj):
        if isinstance(obj, Path | complex):
            return str(obj)
        elif isinstance(obj, np.ndarray):
            return "\n".join(map(str, obj))
        return super().default(obj)


@singledispatch
def json_handler(value) -> dict[Any, Any]:
    if not value:
        return {}

    raise TypeError(f"Do not know how to process {type(value).__name__} as JSON")


@json_handler.register(dict)
def _(value: dict[Any, Any]) -> dict[Any, Any]:
    # Already a dict
    return value


@json_handler.register(str)
def _(value: str) -> dict[Any, Any]:
    try:
        return json.loads(value)
    except json.decoder.JSONDecodeError:
        LOG.warning("Cannot process string as json, trying as file path.")
        return json_handler(Path(value))


@json_handler.register(Path)
def _(value: Path) -> dict[Any, Any]:
    try:
        with value.open(encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Unable to open ({value}) as json file .") from _
    except Exception as err:
        raise ValueError("Unable to load JSON string.") from err


def standardise_name(
    name: str, transform: Callable[[str], str] = str.capitalize
) -> str:
    """Standardise dictionary keys to display name.

    Parameters
    ----------
    name : str
        String to standardise.
    transform : Callable
        String transformation function.

    Returns
    -------
    str
        Standardised name.

    Examples
    --------
    >>> standardise_name("a_key")
    'A key'
    >>> standardise_name("another_key", transform=str.title)
    'Another Key'
    """
    return transform(name.replace("_", " "))


def destandardise_name(name: str) -> str:
    """Returns key-like name (all lower, underscore-separated)

    Parameters
    ----------
    name : str
        Name to make key-like.

    Returns
    -------
    str
        Key-like name.

    Examples
    --------
    >>> destandardise_name("My name")
    'my_name'
    >>> destandardise_name("a_string")
    'a_string'
    >>> destandardise_name("AaaAa")
    'aaaaa'
    """
    return "_".join(map(str.lower, name.split()))


def _strip_inline_comments(
    data: Iterable[str],
    *,
    comment_char: set[str],
) -> Iterator[str]:
    r"""
    Strip all comments from provided data.

    Parameters
    ----------
    data
        Data to strip comments from.
    comment_char
        Characters to interpret as comments.

    Yields
    ------
    str
        Data with line-initial comments stripped.

    Notes
    -----
    Also strips trailing, but not leading whitespace to clean up comment blocks.

    Also strips empty lines.

    Examples
    --------
    >>> from io import StringIO
    >>> inp = StringIO('''
    ... Hello
    ... # Initial line comment
    ... End of line # comment
    ... ''')
    >>> '|'.join(_strip_inline_comments(inp, comment_char={"#",}))
    'Hello|End of line'
    """
    comment_re = re.compile(f"({'|'.join(comment_char)})")

    for line in data:
        new_line = comment_re.split(line, maxsplit=1)[0].rstrip()
        if not new_line:
            continue

        yield new_line


def _strip_initial_comments(
    data: Iterable[str],
    *,
    comment_char: set[str],
) -> Iterator[str]:
    r"""
    Strip line-initial comments from provided data.

    Parameters
    ----------
    data
        Data to strip comments from.
    comment_char
        Characters to interpret as comments.

    Yields
    ------
    str
        Data with line-initial comments stripped.

    Notes
    -----
    Also strips trailing, but not leading whitespace to clean up comment blocks.

    Also strips empty lines.

    Examples
    --------
    >>> from io import StringIO
    >>> inp = StringIO('''
    ... Hello
    ... # Initial line comment
    ... End of line # comment
    ... ''')
    >>> '|'.join(_strip_initial_comments(inp, comment_char={"#",}))
    'Hello|End of line # comment'
    """
    comment_re = re.compile(rf"^\s*({'|'.join(comment_char)})")
    data = filterfalse(comment_re.match, data)
    data = map(str.rstrip, data)
    data = filter(None, data)
    yield from data


def strip_comments(
    data: Iterable[str],
    *,
    comment_char: str | set[str] = "#!",
    remove_inline: bool = True,
) -> Iterator[str]:
    r"""
    Strip comments from data.

    Parameters
    ----------
    data
        Data to strip comments from.
    remove_inline
        Whether to remove inline comments or just line initial.
    comment_char
        Character sets to read as comments and remove.

        .. note::

            If the chars are passed as a string, it is assumed that
            each character is a comment character.

            To match a multicharacter comment you **must** pass this
            as a set or sequence of strings.

    Returns
    -------
    Iterable[str]
        Block of data without comments.

    Notes
    -----
    Also strips trailing, but not leading whitespace to clean up comment blocks.

    Also strips empty lines.

    Examples
    --------
    >>> from io import StringIO
    >>> inp = StringIO('''
    ... Hello
    ... # Initial line comment
    ... End of line # comment
    ... // C-style
    ... ''')
    >>> x = strip_comments(inp, remove_inline=False)
    >>> '|'.join(x)
    'Hello|End of line # comment|// C-style'
    >>> _ = inp.seek(0)
    >>> x = strip_comments(inp, remove_inline=True)
    >>> '|'.join(x)
    'Hello|End of line|// C-style'
    >>> _ = inp.seek(0)
    >>> x = strip_comments(inp, comment_char={"//", "#"})
    >>> '|'.join(x)
    'Hello|End of line'
    """
    if not isinstance(comment_char, set):
        comment_char = set(comment_char)

    strip_function = (
        _strip_inline_comments if remove_inline else _strip_initial_comments
    )

    return strip_function(data, comment_char=comment_char)


def summarise_array(
    array: Sequence, *, maxlen: int = 6, show: int = 3, arr_fmt: str | None = None
) -> str:
    """
    Return a summarised string of the array.

    Long arrays are elided with ``...``.
    Short arrays are left as-is.

    Parameters
    ----------
    array : Sequence
        Array to summarise.
    maxlen : int
        Maximum length before elision (min 4).
    show : int
        Number of elements to show.
    arr_fmt : str, optional
        Format values in array before printing.

    Returns
    -------
    str
        Summarised array.

    Examples
    --------
    >>> summarise_array(range(10))
    '0, 1, 2, ..., 9'
    >>> summarise_array(range(4))
    '0, 1, 2, 3'
    >>> summarise_array(range(10), maxlen=15)
    '0, 1, 2, 3, 4, 5, 6, 7, 8, 9'
    >>> summarise_array(range(10), show=6)
    '0, 1, 2, 3, 4, 5, ..., 9'
    >>> summarise_array([x / 3 for x in range(10)], arr_fmt="3.1f")
    '0.0, 0.3, 0.7, ..., 3.0'
    """
    fmt = str if arr_fmt is None else lambda x: format(x, arr_fmt)
    arr = map(fmt, array)

    if len(array) <= maxlen or len(array) < show + 1:
        return ", ".join(arr)

    return ", ".join(value_chain(take(show, arr), "...", last(arr)))


@overload
def get_next_name(
    template: str,
    *,
    exists: Collection[str] | Callable[[str], bool],
    trial: Iterable[SupportsFormat] | None = ...,
    max_tries: int | None = ...,
    default: None = ...,
    **kwargs: SupportsFormat,
) -> str | None: ...
@overload
def get_next_name(
    template: str,
    *,
    exists: Collection[str] | Callable[[str], bool],
    trial: Iterable[SupportsFormat] | None = ...,
    max_tries: int | None = ...,
    default: str = ...,
    **kwargs: SupportsFormat,
) -> str: ...
def get_next_name(
    template: str,
    *,
    exists: Collection[str] | Callable[[str], bool],
    trial: Iterable[SupportsFormat] | None = None,
    max_tries: int | None = None,
    default: str | None = None,
    **kwargs: SupportsFormat,
) -> str | None:
    """Return the first unused name given rules for next in sequence and invalid values.

    Parameters
    ----------
    template : str
        Base format string to modify, must contain ``trial`` field.
    exists : Collection[str] | Callable[[str], bool]
        Set of existing values to skip or :ref:`Callable` determining existance.
    trial : Iterable[SupportsFormat], optional
        Set/Generator of trial values to use. If ``None`` defaults to :ref:`itertools.count`.
    max_tries : int, optional
        Number of attempts to generate, unlimited if ``None``.
    default : str, optional
        Default to return if ``max_tries`` reached or ``trial`` exhausted.
    **kwargs : SupportsFormat
        Extra substitutions to pass into template.

    Returns
    -------
    str | None
        Next unused name.

    Notes
    -----
    The special value which is substituted is named "trial".

    Examples
    --------
    >>> tpl = "hello_{trial}"
    >>> get_next_name(tpl, exists=())
    'hello_1'
    >>> get_next_name(tpl, exists=lambda x: x[-1] != "6")
    'hello_6'
    >>> get_next_name(tpl, exists={"hello_1", "hello_2"})
    'hello_3'
    >>> get_next_name(tpl, exists={"hello_1", "hello_2"}, max_tries=1, default="Argh!")
    'Argh!'
    >>> get_next_name("{a}_hello_{trial}", exists=(), a="big")
    'big_hello_1'
    """
    if trial is None:
        trial = count(1)

    if isinstance(exists, Collection):
        exists = exists.__contains__

    gen = (template.format(trial=elem, **kwargs) for elem in trial)
    return first_true(
        islice(gen, max_tries), pred=lambda x: not exists(x), default=default
    )


def unused_standard_output_filename(
    path_stem: Path, job_name: str, extra_text: str = "_result", extension: str = ".mda"
) -> Path | None:
    """Return the first unused output file name following the default naming pattern.

    This function suggests the filename given as:
    /directory/of/input/trajectory/JobName_resultN
    where N is a positive integer number.

    Parameters
    ----------
    path_stem : Path
        Output directory with a placeholder name.
    job_name : str
        Name of the analysis that will produce this output file.
    extra_text : str, optional
        Additional text before the file number, by default "_result".
    extension : str, optional
        File name extension, by default ".mda".

    Returns
    -------
    Path | None
        The first file name which does not exist. None if all names are taken.
    """
    name = get_next_name(
        f"{path_stem / job_name}{extra_text}{{trial}}",
        max_tries=MAX_FILE_COUNT,
        exists=lambda x: Path(x).with_suffix(extension).exists(),
    )

    return Path(name) if name else None


def sec_fmt(time: float) -> str:
    """Format a time in seconds sensibly."""
    if not isinstance(time, float):
        return "N/A"

    hr, min = divmod(time, 3600)
    min, sec = divmod(min, 60)

    if hr:
        return f"{hr:.0f}hr {min:.0f}m {sec:.0f}s"
    if min:
        return f"{min:.0f}m {sec:.0f}s"

    return f"{sec:.0f}s"


def job_status_text_summary(jobinf: JobInfo, *, for_output_file: bool = False) -> str:
    """Return run details as a formatted string.

    When writing the run information into an output file, the for_output_file
    can be used to skip the parts of the output that are not relevant
    to a completed task (e.g. estimated remaining time.)"""
    try:
        comp_time = (jobinf.n_steps - jobinf.current_step) / jobinf.rate
    except (TypeError, ZeroDivisionError):
        comp_time = "N/A"

    elapsed_time = (
        jobinf.end - jobinf.start if jobinf.end else time.time() - jobinf.start
    )
    if for_output_file:
        return f"""
Status:
  Percent complete: {jobinf.progress}
  Percent rate: {jobinf.pct_rate} %/s
  Steps: {jobinf.current_step}/{jobinf.n_steps}
  Step rate: {jobinf.rate} steps/s
  Elapsed time: {sec_fmt(elapsed_time)}
"""
    else:
        return f"""
Status:
  Current state: {jobinf.state.name.title()}
  Percent complete: {jobinf.progress}
  Percent rate: {jobinf.pct_rate} %/s
  Steps: {jobinf.current_step}/{jobinf.n_steps}
  Step rate: {jobinf.rate} steps/s
  Elapsed time: {sec_fmt(elapsed_time)}
  Estimated remaining time: {sec_fmt(comp_time)}
"""
