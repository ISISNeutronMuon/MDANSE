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

import pytest
from more_itertools import iequals
from numpy.testing import assert_allclose
from test_helpers.paths import RESULTS_DIR

from MDANSE.Results.MDAFile import MDAFile


@pytest.fixture
def results_file() -> MDAFile:
    with MDAFile(RESULTS_DIR / "basic_meansquare.mda") as file:
        yield file


def test_basic_props(results_file: MDAFile) -> None:
    assert results_file.filename == str(RESULTS_DIR / "basic_meansquare.mda")
    assert iequals(
        map(str, results_file.all_dataset_paths),
        [
            "msd/Cu",
            "msd/S",
            "msd/Sb",
            "msd/axes/time",
            "msd/total",
            "selected_atoms",
        ],
    )
    assert iequals(
        map(str, results_file.main_dataset_paths),
        [
            "msd/Cu",
            "msd/S",
            "msd/Sb",
            "msd/total",
        ],
    )

    assert "msd/*" in results_file

    assert iequals(results_file.find_paths("msd/*"), results_file.main_dataset_paths)


def test_getitem(results_file: MDAFile) -> None:
    for pth, ds in results_file.items():
        assert_allclose(results_file[pth]._data, ds._data)  # ruff: ignore[PLR1733]


def test_summary(results_file: MDAFile) -> None:
    summary = results_file.summary()
    for attr in results_file._file.attrs.keys() - {"header"}:
        assert f"_name={attr}" in summary
    for pth in results_file.all_dataset_paths:
        assert f"{pth}:" in summary
