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
from collections.abc import Iterable, Iterator
from itertools import filterfalse
from pathlib import Path

import numpy as np


class MDANSEEncoder(json.JSONEncoder):
    """Custom JSON encoder to encode paths as strings."""

    def default(self, obj):
        if isinstance(obj, (Path, complex)):
            return str(obj)
        elif isinstance(obj, np.ndarray):
            return "\n".join(map(str, obj))
        return super().default(obj)


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
    'Hello|End of line # comment'
    """
    if not isinstance(comment_char, set):
        comment_char = set(comment_char)

    strip_function = (
        _strip_inline_comments if remove_inline else _strip_initial_comments
    )

    return strip_function(data, comment_char=comment_char)
