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
from __future__ import annotations

import glob
import os


def path_to_module(path, stop=""):
    path, _ = os.path.splitext(path)

    splitted_path = path.split(os.sep)

    try:
        idx = splitted_path[::-1].index(stop)
    except ValueError:
        idx = 0
    finally:
        module = ".".join(splitted_path[len(splitted_path) - 1 - idx :])

    return module


# # Import all classes in this directory so that classes with @register_reader are registered.
# pwd = os.path.dirname(__file__)
# for x in glob.glob(os.path.join(pwd, '*.py')):
#     mod, _ = os.path.splitext(x)
#     mod = os.path.basename(mod)
#     if mod.startswith('__'):
#         continue

#     module = path_to_module(x, stop="waterstay")
#     __import__(module, globals(), locals())

# __all__ = ['REGISTERED_READERS']
