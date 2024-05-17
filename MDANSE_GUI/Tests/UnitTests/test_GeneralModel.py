import pytest
import tempfile

from MDANSE_GUI.Tabs.Models.GeneralModel import GeneralModel


@pytest.fixture(scope="module")
def model_instance():
    instance = GeneralModel()
    instance.append_object((5, "number"))
    instance.append_object(([], "something"))
    instance.append_object(("However", "text"))
    return instance


def test_item_access(model_instance: GeneralModel):
    assert model_instance._nodes[0] == 5
    assert model_instance._nodes[1] == []
    assert model_instance._nodes[2] == "However"


def test_labels(model_instance: GeneralModel):
    for num, textval in enumerate(["number", "something", "text"]):
        index = model_instance.index(num, 0)
        std_item = model_instance.itemFromIndex(index)
        label = std_item.text()
        assert label == textval


def test_removal(model_instance: GeneralModel):
    model_instance.removeRow(1)
    assert model_instance._nodes[0] == 5
    assert model_instance._nodes[2] == "However"
    assert len(model_instance._node_numbers) == 2
    assert len(model_instance._nodes) == 2
