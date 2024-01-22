import os
import pytest
import tempfile
from MDANSE.Framework.Jobs.IJob import IJob


def test_create_template_with_the_wrong_jobname_raises_error():
    temp_name = tempfile.mktemp()
    with pytest.raises(Exception):
        IJob.create("QWERTY").save(temp_name)


@pytest.mark.parametrize(
    "jobname", IJob.indirect_subclasses(),
)
def test_create_template_with_correct_jobname(jobname):
    temp_name = tempfile.mktemp()
    IJob.create(jobname).save(temp_name)
    assert os.path.exists(temp_name)
    assert os.path.isfile(temp_name)
    os.remove(temp_name)
