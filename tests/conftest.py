import pytest

import os
from kivy.config import Config

from main import Home


os.environ.setdefault("KIVY_NO_ARGS", "1")

Config.set("graphics", "headless", "1")
Config.set("kivy", "log_level", "error")
Config.write()


@pytest.fixture
def home():
    return Home()
