import pytest

from MDANSE.Framework.Jobs.IJob import IJob


job_list = IJob.indirect_subclasses()


@pytest.mark.parametrize("job_name", job_list)
def test_documentation_building(job_name):
    instance = IJob.create(job_name)
    docs = instance.build_doc()
    assert len(docs) > 0
