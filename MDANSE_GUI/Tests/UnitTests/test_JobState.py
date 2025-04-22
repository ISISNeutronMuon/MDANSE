import pytest

from MDANSE.Framework.Jobs.JobStatus import JobStates
from MDANSE_GUI.Tabs.Models.JobHolder import JobEntry


@pytest.fixture(scope="module")
def temporary_jobentry() -> JobEntry:
    return JobEntry()


def test_start(temporary_jobentry: JobEntry):
    temporary_jobentry.job.state.start()
    assert temporary_jobentry.job.state._label is JobStates.RUNNING


def test_fail(temporary_jobentry: JobEntry):
    temporary_jobentry.job.state.fail()
    assert temporary_jobentry.job.state._label is JobStates.FAILED
