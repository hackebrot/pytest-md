import pytest


def pytest_addoption(parser):
    group = parser.getgroup("terminal reporting")
    group.addoption(
        "--md",
        action="store",
        dest="mdpath",
        metavar="path",
        default=None,
        help="create markdown report file at given path.",
    )
