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

import importlib.metadata
import os
import warnings

import MDANSE.Framework
from MDANSE.Core.Platform import PLATFORM

# Limit underlying math libraries (OpenMP, BLAS, MKL, etc.) to use only 1 thread
# to prevent them from creating many worker threads and overloading the CPU.
os.environ.update(
    {
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
    }
)

__version__ = importlib.metadata.version("MDANSE")

warnings.filterwarnings("ignore")

PLATFORM.create_directory(PLATFORM.macros_directory())
