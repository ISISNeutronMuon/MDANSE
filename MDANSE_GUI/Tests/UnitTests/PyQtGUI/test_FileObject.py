import pytest
import tempfile

from MDANSE_GUI.DataViewModel.TrajectoryHolder import FileObject

reference_bytes = b"TeStCaSeFoRtHeCaChEfuNcTiOn"
reference_hash = "7105425fa73f3e6a31b72ae2ee36235bcf1f4883b16e674b80a04d6587d995ec"


@pytest.fixture(scope="module")
def temporary_fileobject():
    fdesc, fname = tempfile.mkstemp()
    with open(fname, "wb") as target:
        target.write(reference_bytes)
    fob = FileObject()
    fob.setFilename(fname)
    return fob


def test_hash_value(temporary_fileobject):
    hash = temporary_fileobject.hash
    print(hash)
    assert hash == reference_hash
