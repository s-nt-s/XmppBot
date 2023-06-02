import pytest
import tempfile
from xmppbot.configbot import Avatar


def test_avatar_null():
    file = None
    with pytest.raises(TypeError):
        Avatar(file)
    assert Avatar.init(file) is None


def test_avatar_file_not_found():
    with tempfile.NamedTemporaryFile() as tmp:
        file = tmp.name
    with pytest.raises(FileNotFoundError):
        Avatar(file)
    assert Avatar.init(file) is None


def test_avatar_empty_file():
    with tempfile.NamedTemporaryFile() as file:
        with pytest.raises(BytesWarning):
            Avatar(file.name)
    assert Avatar.init(file) is None


def test_avatar_ok():
    a = Avatar("examples/rec/ping.png")
    assert len(a.content) > 0
