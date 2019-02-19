import pytest


@pytest.fixture(name="hello")
def fixture_hello():
    return "hello"
