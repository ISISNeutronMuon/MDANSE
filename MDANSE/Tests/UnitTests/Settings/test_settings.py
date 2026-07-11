from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import tomlkit
from tomlkit.toml_file import TOMLFile

from MDANSE.Core.Settings import Option, Settings

TEST_LABELS = ("test", "blam", "blob")


@pytest.fixture
def settings_file(tmp_path) -> Iterator[Path]:
    out_file = tmp_path / "my_test.toml"

    settings = Settings
    with settings.temporary():
        settings.init(None, save=False)

        for i, key in enumerate(TEST_LABELS, 1):
            settings.set_item(Option(None, key, "test"))
            settings.set_opt("test", key, i)

        settings.save(out_file)

    yield out_file
    out_file.unlink()


@pytest.fixture
def settings() -> Iterator[type[Settings]]:
    with Settings.temporary():
        Settings.clear()
        yield Settings


def test_save(tmp_path: Path, settings: type[Settings]):
    settings.set_item(Option(4, "a", "a"))
    settings.set_item(Option(3, "a", "b"))
    settings.set_item(Option("hi", "b", "b"))

    pth = tmp_path / "trial.toml"
    settings.save(pth)

    # Don't write defaults.
    assert not TOMLFile(pth).read()

    settings.set_opt("a", "a", 17)
    settings.set_opt("b", "b", "hello")
    settings.save(pth)

    assert TOMLFile(pth).read() == {"a": {"a": 17}, "b": {"b": "hello"}}



def test_load(settings: type[Settings], settings_file: Path):
    for trial in TEST_LABELS:
        assert not settings.contains("test", trial)

    settings.init(settings_file)

    for i, trial in enumerate(TEST_LABELS, 1):
        assert settings.get_opt("test", trial) == i


@pytest.mark.parametrize(
    "grp,key,value",
    [
        ("test", "tim", 15),  # New value
        ("trouble", "amount", "double"),  # New group
        ("test", "blob", 15),  # Overwrite
    ],
)
def test_set(
    settings: type[Settings], settings_file: Path, grp: str, key: str, value: Any
):
    settings.init(settings_file)

    if key != "blob":
        assert not settings.contains(grp, key)
    settings.set_opt(grp, key, value)
    assert settings.contains(grp, key)
    assert settings.get_opt(grp, key) == value
    # Check we're getting it from settings
    assert settings._settings[grp][key].value == value


def test_contains(settings: type[Settings]):
    settings.clear()  # Just to be sure. Cleared from fixture.

    assert not settings.contains("bob", "height")
    settings.set_opt("a", "b", "c")
    settings.set_item(Option("a", name="c", group="b"))

    assert settings.contains("a", "b")
    assert settings.contains("b", "c")
    assert not settings.contains("bob", "height")

    # Manual override
    settings._defaults["b"]["u"] = Option(1, "u", "b")
    assert settings.contains("b", "u")


def test_clear(settings: type[Settings], settings_file: Path):
    settings.init(settings_file)
    settings.set_opt("a", "b", "c")

    assert any(settings._defaults.values())
    assert any(settings._settings.values())
    assert any(settings.settings.values())

    settings.clear()

    assert not any(settings._defaults.values())
    assert not any(settings._settings.values())
    assert not any(settings.settings.values())


def test_temporary(settings: type[Settings]):
    settings.set_item(Option("l", "b", "a"))
    default = settings._defaults["a"]["b"]
    settings.set_opt("a", "b", "c")
    setting = settings._settings["a"]["b"]

    with settings.temporary(
        q=6, p=Option(name="p", group="letters", value=4, comment="hi")
    ):
        assert settings._settings["a"]["b"] is setting
        assert settings._defaults["a"]["b"] is default

        settings.set_opt("a", "b", 3)
        assert settings.get_opt("a", "b") == 3
        assert settings.get_opt("temp", "q") == 6
        assert settings.get_opt("letters", "p") == 4

    assert settings._settings["a"]["b"] is setting
    assert settings._defaults["a"]["b"] is default
    assert settings.get_opt("a", "b") == "c"
    assert not settings.contains("temp") and not settings.contains("temp", "q")
    assert not settings.contains("letters", "p")


def test_get_w_default(settings: type[Settings]):

    default = Option("l", "b", "a")
    settings.set_item(default)

    assert settings.get_opt_w_default("a", "b", 4) == "l"

    settings.set_opt("a", "b", "c")

    # Check we haven't overriden the default
    assert settings._defaults["a"]["b"] is default
    # Check we're getting the setting
    assert settings.get_opt_w_default("a", "b", 4) == "c"

    assert settings.get_opt_w_default("q", "j", default=4) == 4
    assert settings.contains("q", "j")
    assert settings._defaults["q"]["j"].value == 4
    # Check now has setting.
    assert settings.get_opt_w_default("q", "j", default=17) == 4


def test_parametrise(settings: type[Settings]):

    @settings.parametrise(favourite=Option("pike", group="fish"))
    class Florp:
        def __init__(self) -> None: ...

        def update(self) -> None:
            self.favourite = "trout"

    assert not settings.settings

    assert Option(value="pike", name="favourite", group="fish") in settings._parameters
    # Need to initialise to instance parameters
    settings.init()

    # Sync'd on parametrise
    assert settings.contains("fish", "favourite")
    assert settings.get_opt("fish", "favourite") == "pike"
    t = Florp()

    # Check instance
    assert t.favourite == "pike"

    # Change through assignment
    t.update()
    assert settings.get_opt("fish", "favourite") == "trout"
    assert t.favourite == "trout"

    # Change through settings
    settings.set_opt("fish", "favourite", "bream")
    assert t.favourite == "bream"
