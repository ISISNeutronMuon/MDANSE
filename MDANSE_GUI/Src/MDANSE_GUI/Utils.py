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
"""Core utilities for the MDANSE GUI."""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from enum import Enum
from typing import TYPE_CHECKING, Any, overload

from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QSpinBox,
    QWidget,
)

if TYPE_CHECKING:
    from qtpy.QtCore import QObject


@contextmanager
def block_signals(*objs: QObject):
    """Block a QObject's signals

    Parameters
    ----------
    *objs : QObject
        Objects to block
    """
    for obj in objs:
        obj.blockSignals(True)

    try:
        yield
    finally:
        for obj in objs:
            obj.blockSignals(False)


@overload
def from_param(name: str, typ: type[float]) -> tuple[QLabel, QDoubleSpinBox]: ...
@overload
def from_param(name: str, typ: type[int]) -> tuple[QLabel, QSpinBox]: ...
@overload
def from_param(name: str, typ: type[bool]) -> tuple[QLabel, QCheckBox]: ...
@overload
def from_param(name: str, typ: type[Enum]) -> tuple[QLabel, QComboBox]: ...
@overload
def from_param(name: str, typ: type[str]) -> tuple[QLabel, QLineEdit]: ...
def from_param(name: str, typ: type) -> tuple[QLabel, QWidget]:
    """Get a Widget to set a param.

    Parameters
    ----------
    name : str
        Name of parameter for label.
    typ : type
        Type of data in parameter.

    Returns
    -------
    tuple[QLabel, QWidget]
        Label and Widget entities.

    Raises
    ------
    TypeError
        No widget assigned for type.
    """
    label = QLabel(f"{name.title()}:")
    if typ is float:
        val_widget = QDoubleSpinBox()
        val_widget.setRange(-1e6, 1e6)
        val_widget.setDecimals(6)
    elif typ is int:
        val_widget = QSpinBox()
        val_widget.setRange(-1_000_000, 1_000_000)
    elif typ is bool:
        val_widget = QCheckBox()
    elif issubclass(typ, Enum):
        val_widget = QComboBox()
        val_widget.addItems([x.name for x in typ])
    elif typ is str:
        val_widget = QLineEdit()
    else:
        raise TypeError(f"Cannot process {typ.__name__}.")

    val_widget.setObjectName(name)
    return label, val_widget


@overload
def get_value(widget: QDoubleSpinBox) -> float: ...
@overload
def get_value(widget: QSpinBox) -> int: ...
@overload
def get_value(widget: QCheckBox) -> bool: ...
@overload
def get_value(widget: QComboBox) -> str: ...
@overload
def get_value(widget: QLineEdit) -> str: ...
def get_value(widget: QWidget) -> Any:
    """Get a value from a widget.

    Parameters
    ----------
    widget : QWidget
        Widget to pull value from.

    Returns
    -------
    Any
        Data in Python type.

    Raises
    ------
    TypeError
        No defined way to extract value.
    """
    match widget:
        case QDoubleSpinBox() | QSpinBox():
            return widget.value()
        case QCheckBox():
            return widget.isChecked()
        case QComboBox():
            return widget.currentText()
        case QLineEdit():
            return widget.text()
        case _:
            raise TypeError(f"Cannot handle {type(widget).__name__} widget.")


def get_main_signal(widget: QWidget) -> Signal:
    """Get main value change signal from a widget.

    Parameters
    ----------
    widget : QWidget
        Widget to pull signal from.

    Returns
    -------
    Signal
        Main signal associated with value change.

    Raises
    ------
    TypeError
        No defined way to extract value.
    """
    match widget:
        case QDoubleSpinBox() | QSpinBox():
            return widget.valueChanged
        case QCheckBox():
            return widget.checkStateChanged
        case QComboBox():
            return widget.currentTextChanged
        case QLineEdit():
            return widget.textChanged
        case _:
            raise TypeError(f"Cannot handle {type(widget).__name__} widget.")


def parse_token(token: str, max_len: int) -> Iterable[int]:
    """Parse a slice token component into an appropriate value for dimension slicing.

    Parameters
    ----------
    token : str
        Token to parse.
    max_len : int
        Size of array for un-ended slices.

    Returns
    -------
    Iterable[int]
        Parsed values.

    Examples
    --------
    >>> parse_token("3:5", 10)
    range(3, 5)
    >>> parse_token("3:60:2", 5)
    range(3, 5, 2)
    >>> parse_token("8", 10)
    (8, )
    >>> parse_token("6-8", 10)
    range(6, 8)
    """
    if ":" in token:
        slice_parts = map(int, token.split(":"))
        slc = slice(*slice_parts).indices(max_len)
        return range(*slc)

    if "-" in token:
        start, stop = map(int, token.split("-"))
        return range(start, stop + 1)

    return (int(token),)


def HTML_wrap(tag: str, content: str, **kwargs) -> str:
    kw = " ".join(f"{k}={v}" for k, v in kwargs.items())
    return f"<{tag} {kw}>{content}</{tag}>"
