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

from pathlib import Path
from typing import TYPE_CHECKING, Any, ParamSpec, cast

from MDANSE.Framework.Parameters.BaseTypes import Dict
from MDANSE.Framework.Parameters.Choices import SingleChoice
from MDANSE.Framework.Parameters.Parameters import (
    ConfigError,
    Configurable,
    CustomConfig,
)
from MDANSE.Framework.Parameters.UtilTypes import Depends, DescID
from MDANSE.IO.IOUtils import json_handler
from MDANSE.Mathematics.Signal import (
    DEFAULT_FILTER,
    FILTER_MAP,
    FILTERS,
    Filter,
    filter_default_attributes,
)

if TYPE_CHECKING:
    from MDANSE.Framework.Parameters import Frames


FilterType = type[Filter]


class Filter(CustomConfig):
    default_tooltip = "Choose trajectory filter."
    default_label = "Trajectory filter"

    filter_type = SingleChoice[str | FilterType, FilterType, FilterType](
        choices=FILTERS,
        aliases=FILTER_MAP,
        default=DEFAULT_FILTER,
    )
    params = Dict(default={"attributes": filter_default_attributes(DEFAULT_FILTER)})

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("frames")}

    @property
    def filter(self) -> Filter:
        frames: Frames = self.last_deps["frames"]
        return self.filter_type(
            time_step_ps=frames.time_step,
            n_steps=len(frames),
            **self.params,
        )

    @filter.setter
    def filter(self, value: dict | str | Path | tuple[str, dict[str, Any]] | Filter):
        if isinstance(value, (dict, str, Path)):
            try:
                value = json_handler(value)
            except Exception as err:
                raise ConfigError("Couldn't set filter from json") from err
            self.filter_type = value.pop("filter")
            self.params = value
        elif isinstance(value, tuple):
            self.filter_type, self.params = value
        elif isinstance(value, Filter):
            self.filter_type = type(value).__name__
            self.params = {
                key: val for key, val in value.__dict__ if key in value.default_settings
            }

    def __set__(
        self,
        owner: Configurable,
        value: dict | str | Path | tuple[str, dict[str, Any]] | Filter,
    ) -> None:
        self.owner = owner
        if isinstance(value, (dict, str, Path, tuple, Filter)):
            self.filter = value
            return

        super().__set__(owner, value)
