"""Core utilities for the MDANSE GUI."""

from __future__ import annotations

from contextlib import contextmanager

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
