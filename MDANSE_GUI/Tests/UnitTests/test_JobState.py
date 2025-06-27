import pytest

from MDANSE.Framework.Jobs.JobStatus import JobStates
from MDANSE_GUI.Tabs.Models.JobHolder import JobEntry


@pytest.fixture(scope="module")
def temporary_jobentry() -> JobEntry:
    return JobEntry()


def test_start(temporary_jobentry: JobEntry):
    temporary_jobentry.start_job()
    assert temporary_jobentry.job.state is JobStates.RUNNING


def test_fail(temporary_jobentry: JobEntry):
    temporary_jobentry.fail_job()
    assert temporary_jobentry.job.state is JobStates.FAILED
