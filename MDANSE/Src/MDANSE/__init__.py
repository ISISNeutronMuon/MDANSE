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
import importlib.metadata

__version__ = importlib.metadata.version("MDANSE")

import warnings

warnings.filterwarnings("ignore")

from MDANSE.Core.Platform import PLATFORM

import MDANSE.Framework

PLATFORM.create_directory(PLATFORM.macros_directory())

import logging

logging.getLogger("MDANSE").setLevel("INFO")
