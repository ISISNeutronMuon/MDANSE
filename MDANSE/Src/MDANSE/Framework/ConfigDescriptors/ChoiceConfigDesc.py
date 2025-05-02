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
from collections.abc import Container
from typing import Optional, Set, TypeVar, Sequence

from .AbsConfigDesc import ConfigError, ConfigureDescriptor

T = TypeVar("T")

class ChoiceConfigDesc(ConfigureDescriptor):
    """
    This Configurator allows to input a Float Value.
    """

    @property
    def n_choices(self) -> int:
        """
        Returns the minimum value allowed for an input float.

        :return: the minimum value allowed for an input value float.
        :rtype: int or None
        """
        return self._n_choices

    @n_choices.setter
    def n_choices(self, value: int):
        if value < 0:
            raise ConfigError(f"Invalid n_choices ({value}) must be >0")
        self._n_choices = value

    @property
    def choices(self) -> Set[T]:
        """
        Returns the list of floats allowed for an input float.
        """
        return self._choices

    @choices.setter
    def choices(self, value: Container[T]):
        if value is None:
            self._choices = []
        self._choices = list(value)


def SingleChoiceConfigDesc(ChoiceConfigDesc):

    _old_name = "SingleChoiceConfigurator"

    def __init__(self,
                 choices: Container[T] = None,
                 default: Optional[T] = None,
                 **params):
        super().__init__(choices=choices, n_choices=1, **params)

    def validate(self, value: T, *_) -> T:
        self._original_input = value

        self.index = self._choices.find(value)
        if self.index < 0:
            raise ConfigError(f"{value} is not a valid choice.")

        return value

def MultipleChoiceConfigDesc(ChoiceConfigDesc):

    def __init__(self,
                 choices: Container[T] = None,
                 n_choices: int = 1,
                 default: Optional[T] = None,
                 **params):
        super().__init__(choices=choices, n_choices=n_choices, **params)
        self.choices = choices
        self.n_choices = n_choices

    _old_name = "MultipleChoiceConfigurator"

    def validate(self, values: Sequence[T], *_) -> Sequence[T]:
        self._original_input = values

        if len(values) > self.n_choices:
            raise ConfigError(f"Too many options selected ({values}).")

        self.indices = [self._choices.find(value) for value in values]
        if any(index < 0 for index in self.indices):
            raise ConfigError(f"{', '.join(set(self.choices) - set(values))} are not valid choices.")

        return values
