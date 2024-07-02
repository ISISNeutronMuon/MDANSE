import pytest
import tempfile

from MDANSE_GUI.Tabs.Models.JobHolder import JobEntry


@pytest.fixture(scope="module")
def temporary_jobentry() -> JobEntry:
    return JobEntry()


def test_start(temporary_jobentry: JobEntry):
    temporary_jobentry._current_state.start()
    assert temporary_jobentry._current_state._label == "Running"


def test_fail(temporary_jobentry: JobEntry):
    temporary_jobentry._current_state.fail()
    assert temporary_jobentry._current_state._label == "Failed"
