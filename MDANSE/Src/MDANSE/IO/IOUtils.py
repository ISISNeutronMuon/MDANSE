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
from collections.abc import Iterable, Iterator, Sequence
from enum import Enum
from functools import singledispatch
from itertools import filterfalse
from pathlib import Path
from typing import Any

import numpy as np
from more_itertools import first_true, value_chain

from MDANSE.MLogging import LOG

MAX_FILE_COUNT = 2048


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


def summarise_array(array: Sequence, *, maxlen: int = 6, show: int = 3) -> str:
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
    """
    if len(array) <= maxlen or len(array) < show + 1:
        return ", ".join(map(str, array))

    return ", ".join(map(str, value_chain(array[:show], "...", array[-1])))


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
    temp_name_generator = (
        path_stem.with_name("".join((job_name, extra_text, str(number + 1))))
        for number in range(MAX_FILE_COUNT)
    )
    return first_true(
        temp_name_generator, pred=lambda x: not x.with_suffix(extension).exists()
    )
