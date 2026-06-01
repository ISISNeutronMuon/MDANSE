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

import math
from typing import TYPE_CHECKING, Any, Literal, NamedTuple, SupportsInt

import numpy as np
from typing_extensions import TypeVar

from MDANSE.Framework.Parameters.BaseTypes import Integer, NumericRange, Range
from MDANSE.Framework.Parameters.Choices import SingleChoice
from MDANSE.Framework.Parameters.Parameters import ConfigError
from MDANSE.Framework.Parameters.UtilTypes import Depends, DescID, PredictionResult

if TYPE_CHECKING:
    from collections.abc import Iterator

    from MDANSE.MolecularDynamics.Trajectory import Trajectory


class Frame(NamedTuple):
    time: float
    loc_index: int
    ind: int


class Frames:
    def __init__(self, traj: Trajectory, samples: range | NumericRange[int] | Frames):
        if isinstance(samples, Frames):
            self.samples = samples.samples
        else:
            self.samples = samples

        if any(time := traj.time()):
            a, b = self.samples[:2]
            step = time[b] - time[a]
            self.times = NumericRange(
                time[self.samples[0]],
                time[self.samples[-1]] + (step / 2),
                step,
            )
        else:
            self.times = self.samples

    def __getitem__(self, value: int) -> Frame:
        return Frame(
            time=self.times[value],
            loc_index=value,
            ind=self.index_start + (value * self.index_step),
        )

    def __hash__(self) -> int:
        return hash((self.time_start, self.time_stop, self.time_step))

    def __eq__(self, other) -> bool:
        if not isinstance(other, Frames):
            return NotImplemented
        return self.times == other.times

    def __len__(self) -> int:
        return len(self.samples)

    @property
    def index_start(self) -> int:
        return self.samples[0]

    @property
    def index_stop(self) -> int:
        return self.samples[-1]

    @property
    def index_step(self) -> int:
        return self.samples.step

    @property
    def time_start(self) -> float:
        return self.times[0]

    @property
    def time_stop(self) -> float:
        return self.times[-1]

    @property
    def time_step(self) -> float:
        return self.times.step

    @property
    def duration(self) -> float:
        return self.time_stop - self.time_start

    @property
    def indices(self) -> NumericRange:
        return self.samples

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.index_start}, {self.index_stop}, {self.index_step})"


FrameInput = Frames | range | tuple[int, ...] | None | Literal["all"]


class FrameWindow:
    def __init__(self, window: int, frames: Frames):
        self.window = window
        self._frames = frames

    @property
    def n_frames(self) -> int:
        return self.window

    @property
    def n_configs(self) -> int:
        return len(self._frames) - self.window + 1

    @property
    def times(self) -> NumericRange[float]:
        return self._frames.times[: self.window]

    @property
    def duration(self) -> list[float]:
        return [time - self.times[0] for time in self.times]

    def __int__(self) -> int:
        return self.window

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.window})"


class FrameSelect(Range[int, Frames]):
    default_tooltip = "Select which frames are to be included."
    default_label = "Frames to include in correlation."

    def __init__(
        self,
        *args,
        default: FrameInput = "all",
        dtype: None = None,
        include_last: None = None,
        **kwargs,
    ):
        super().__init__(*args, default=default, dtype=int, **kwargs)

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("trajectory")}

    def get_ranges(self, deps: Depends) -> tuple[int, int]:
        return (0, len(deps["trajectory"]) + 1)

    def __set__(self, owner: object, value: tuple[SupportsInt, ...]):
        # Support legacy
        corr = [x for x in self.dependents if isinstance(x, CorrelationWindow)]
        window = None

        if value and isinstance(value, (tuple, list)) and len(value) == 4 and corr:
            value, window = value[:3], value[3]

        super().__set__(owner, value)

        if corr and window:
            corr[0].__set__(owner, window)

    def validate(
        self,
        value: FrameInput,
        deps: dict[str, Any],
        /,
    ) -> Frames:
        if isinstance(value, Frames):
            value = value.samples

        trajectory: Trajectory = deps["trajectory"]
        nsteps = len(trajectory)

        if value is None or value == "all":
            value = (0, nsteps, 1)

        ranges = super().validate(value, deps)

        return Frames(trajectory, ranges)

    def preview_output_axis(self, value, raw) -> Iterator[PredictionResult]:
        yield PredictionResult("Time step (ps)", value.times, "ps")


class CorrelationWindow(Integer[FrameWindow]):
    default_label = "Correlation window"
    default_tooltip = "Number of frames in correlation window."

    def __init__(
        self,
        *args,
        default: int | None = None,
        optional: bool = True,
        optional_label: str = "Default (n_frames / 2)",
        **kwargs,
    ):
        super().__init__(
            *args,
            default=default,
            optional=optional,
            optional_label=optional_label,
            **kwargs,
        )

    def validate(self, value: SupportsInt, deps: Depends):
        if isinstance(value, FrameWindow):
            value = value.window
        elif value is None:
            value = math.ceil(len(deps["frames"]) / 2)

        value = super().validate(value, deps)

        return FrameWindow(value, deps["frames"])

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("frames")}

    def get_ranges(self, deps: Depends):
        return (2, len(deps["frames"]))

    def preview_output_axis(self, value, raw) -> Iterator[PredictionResult]:
        yield PredictionResult("Time step (dt)", value.times, "ps")


CB = TypeVar("CB", default=int)


class InterpOrder(SingleChoice[int | str, int, CB]):
    default_label = "Velocity interpolation order."
    default_tooltip = (
        "Select velocity interpolation order, "
        "if the file contains velocities use 0 to use those."
    )

    base_aliases = {
        "no interpolation": 0,
        "1st order": 1,
        "2nd order": 2,
        "3rd order": 3,
        "4th order": 4,
        "5th order": 5,
    }

    def __init__(
        self,
        *args,
        default: int = 3,
        aliases: None = None,
        choices: None = None,
        optional: bool = False,
        **kwargs,
    ):
        if aliases is not None:
            raise ConfigError("aliases may not be non-None")
        if choices is not None:
            raise ConfigError("choices may not be non-None")

        super().__init__(
            *args,
            choices=(),
            aliases=self.base_aliases,
            default=default,
            optional=optional,
            **kwargs,
        )
        self.last_choices = ()

    @property
    def choices(self) -> list[int]:
        return sorted(self.last_choices)

    @choices.setter
    def choices(self, value) -> None: ...

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("trajectory"), DescID("frames")}

    def get_choices(self, deps: Depends) -> set[int]:
        maxi = min(6, len(deps["frames"]))
        mini = 0 if "velocities" in deps["trajectory"].variables() else 1
        return set(range(mini, maxi))
