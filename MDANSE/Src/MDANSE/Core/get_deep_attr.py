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

from typing import Any


def get_deep_attr(obj: Any, key: str) -> Any:
    """Get attribute from nested objects.

    Parameters
    ----------
    obj : Any
        Object to get elements from.
    key : str
        "." separated string indexing into object.

        "[x]" and "(x, y)" elements are evaluated.

    Returns
    -------
    Any
        Element at path given by key.
    """

    parts = key.split(".")

    new = obj
    for part_in in parts:
        part, *method = part_in.split("(", 1)
        part, *getter = part.split("[", 1)
        new = getattr(new, part)
        if method:
            args = method[0].strip("()")
            if args:
                args = args.split(",")

            new = new(*map(eval, args))
        if getter:
            args = getter[0].strip("[]")
            new = new[eval(args)]

    return new
