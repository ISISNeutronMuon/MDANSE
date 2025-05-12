from contextlib import nullcontext as success

import pytest
from MDANSE.Framework.OutputVariables.IOutputVariable import (
    IOutputVariable, OutputVariableError
)

DIM_FAIL = pytest.raises(OutputVariableError, match="Invalid number of dimensions")

@pytest.mark.parametrize("var_type, data_size, extras, expected", [
    ("LineOutputVariable", (), {}, DIM_FAIL),
    ("LineOutputVariable", (1,), {}, success()),
    ("LineOutputVariable", (1,2,), {}, DIM_FAIL),
    ("LineOutputVariable", (1,2,3), {}, DIM_FAIL),
    ("LineOutputVariable", (-1,), {}, pytest.raises(ValueError, match="negative dimension")),

    ("SurfaceOutputVariable", (), {}, DIM_FAIL),
    ("SurfaceOutputVariable", (1,), {}, DIM_FAIL),
    ("SurfaceOutputVariable", (1,2,), {}, success()),
    ("SurfaceOutputVariable", (1,2,3), {}, DIM_FAIL),
    ("SurfaceOutputVariable", (-1,2), {}, pytest.raises(ValueError, match="negative dimension")),

    ("VolumeOutputVariable", (), {}, DIM_FAIL),
    ("VolumeOutputVariable", (1,), {}, DIM_FAIL),
    ("VolumeOutputVariable", (1,2,), {}, DIM_FAIL),
    ("VolumeOutputVariable", (1,2,3), {}, success()),
    ("VolumeOutputVariable", (-1,2,3), {}, pytest.raises(ValueError, match="negative dimension")),

    ("LineOutputVariable", (1,), {"axis": "time"}, success()),
    ("LineOutputVariable", (1,), {"axis": ("time",)}, success()),
    ("LineOutputVariable", (1,), {"axis": "q|omega"}, DIM_FAIL),
    ("LineOutputVariable", (1,), {"axis": ("q", "omega")}, DIM_FAIL),

    ("VolumeOutputVariable", (1,2,3), {"axis": "time"}, DIM_FAIL),
    ("VolumeOutputVariable", (1,2,3), {"axis": ("time",)}, DIM_FAIL),
    ("VolumeOutputVariable", (1,2,3), {"axis": "q|omega|x"}, success()),
    ("VolumeOutputVariable", (1,2,3), {"axis": ("baa", "baa", "baa")}, success()),

])
def test_ioutput_variables(var_type, data_size, extras, expected):
    with expected:
        IOutputVariable.create(var_type, data_size, "test", **extras)
