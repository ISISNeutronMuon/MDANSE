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

from collections.abc import Container, Iterable, Mapping, Sequence
from enum import EnumMeta
from typing import Any, cast

from typing_extensions import TypeVar

from MDANSE.Core.get_deep_attr import get_deep_attr
from MDANSE.Framework.Parameters.Parameters import ConfigError, ConfigureDescriptor
from MDANSE.Framework.Parameters.UtilTypes import CB, SC, Depends, DescID, P, T
from MDANSE.IO.IOUtils import UCDict


class Choice(ConfigureDescriptor[P, T, CB]):
    """Select an option from a multiple choice set.

    Parameters
    ----------
    n_choices : int or None
        Maximum number of valid choices (unlimited if ``None``)
    aliases : dict
        Alternative names/symbols which are allowed.
    """

    def __init__(
        self,
        *,
        choices: Sequence[T],
        n_choices: int | None,
        aliases: dict[Any, P] | None = None,
        **params,
    ):
        super().__init__(choices=choices, **params)

        self.n_choices = n_choices
        self.aliases = aliases if aliases is not None else {}

    @property
    def n_choices(self) -> int:
        """Returns the minimum value allowed for an input float.

        Returns
        -------
        int
            the minimum value allowed for an input value float.
        """
        return self._n_choices if self._n_choices is not None else len(self.choices)

    @n_choices.setter
    def n_choices(self, value: int | None):
        if value is None:
            self._n_choices = value
            return

        if value < 0:
            raise ConfigError(f"Invalid n_choices ({value}) must be >0")
        self._n_choices = int(value)


class MultipleChoice(Choice[Iterable[P], Sequence[T], Sequence[CB]]):
    """Select multiple options from the set of choices."""

    def __init__(self, *args, choices: Iterable[T], n_choices: int | None, **params):
        super().__init__(*args, choices=choices, n_choices=n_choices, **params)

    def _validate_choices(
        self, value: Iterable[T], choices: set[T] | None = None
    ) -> bool:
        choice = self.choices if choices is None else choices
        assert not isinstance(choice, EnumMeta)
        return set(value) <= choice

    def _validate_exclude(
        self, value: Iterable[T], exclude: set[T] | None = None
    ) -> bool:
        excludes = self.exclude if exclude is None else exclude
        return set(value) > excludes

    def validate(self, values: Iterable[P], deps: Depends, /) -> Sequence[T]:
        dealiased = cast(
            "list[P]", [self.aliases.get(value, value) for value in values]
        )
        out = super().validate(dealiased, deps)

        if len(out) > self.n_choices:
            raise ConfigError(f"Too many options selected ({values}).")

        return out


class SingleChoice(Choice[P, T, CB]):
    """Select a single option from the set of choices."""

    def __init__(self, choices: Container[T], n_choices: None = None, **params):
        if n_choices is not None:
            raise ConfigError(f"Cannot define n_choices in {type(self).__name__}")
        super().__init__(choices=choices, n_choices=1, **params)

    def validate(self, value: P, deps: Depends, /) -> T:
        value = self.aliases.get(value, value)
        return super().validate(value, deps)


class DynamicSingleChoice(SingleChoice[P, T, CB]):
    """Select a single option from a set of choices drawn from an object."""

    def __init__(self, choices: str, **params):
        super().__init__(choices=(), **params)
        self.getter = choices
        self.last_choices = set()

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("choices")}

    @property
    def choices(self) -> set[T]:
        return self.last_choices

    @choices.setter
    def choices(self, value: Any) -> None:
        self._choices = set()

    def get_choices(self, deps) -> set[T]:
        choices = set(get_deep_attr(deps["choices"], self.getter))
        if not choices:
            raise ConfigError(f"No valid choices at deps['choices'].{self.getter}")

        return choices


class DynamicMultiChoice(MultipleChoice[Sequence[P], Sequence[T], Sequence[CB]]):
    """Select multiple options form a set of choices drawn from an object."""

    def __init__(self, choices: str, n_choices: int | None, **params):
        super().__init__(choices=(), n_choices=n_choices, **params)
        self.getter = choices
        self.last_choices = set()

    def required_deps(self) -> set[DescID]:
        return super().required_deps() | {DescID("choices")}

    @property
    def choices(self) -> set[T]:
        return self.last_choices

    @choices.setter
    def choices(self, value: Any) -> None:
        self._choices = set()

    def get_choices(self, deps: Depends) -> set[T]:
        if not deps:
            raise ConfigError("Misconfigured deps")

        choices = set(get_deep_attr(deps["choices"], self.getter))
        if not choices:
            raise ConfigError(f"No valid choices at deps['choices'].{self.getter}")

        return choices


SCCB = TypeVar("SCCB", default=SC)


class SubclassChoice(SingleChoice[str | type[SC], SC, SCCB]):
    def __init__(
        self,
        choices: type[SC],
        aliases: dict[str, type[SC]] | None = None,
        default: str | type[SC] | None = None,
        instance_args: Mapping[str, Any] | None = None,
        **kwargs,
    ):
        if aliases is None:
            aliases = {}

        super().__init__(
            choices=choices.indirect_subclass_dictionary().values(),
            aliases=UCDict(choices.indirect_subclass_dictionary()) | aliases,
            default=default,
            **kwargs,
        )
        self.instance_args = instance_args or {}

    def validate(self, value: str | type[SC], deps: Depends) -> SC:
        value = cast("type[SC]", super().validate(value, deps))
        # Instantiate the object.
        return value(
            **{key: deps.get(arg, arg) for key, arg in self.instance_args.items()}
        )
