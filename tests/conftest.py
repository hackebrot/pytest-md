import enum
import datetime
import textwrap

import freezegun
import pytest

pytest_plugins = "pytester"


@pytest.fixture(name="emoji_tests", autouse=True)
def fixture_emoji_tests(testdir):
    """Create a test module with several tests that produce all the different
    pytest test outcomes.
    """
    emoji_tests = textwrap.dedent(
        """\
        import pytest

        def test_passed():
            assert "emoji" == "emoji"

        def test_failed():
            assert "emoji" == "hello world"

        @pytest.mark.xfail
        def test_xfailed():
            assert 1234 == 100

        @pytest.mark.xfail
        def test_xpassed():
            assert 1234 == 1234

        def test_fox():
            assert "fox" == "fox"

        @pytest.mark.skipif(True, reason="don't run this test")
        def test_skipped():
            assert "emoji" == "emoji"

        @pytest.fixture
        def name():
            raise RuntimeError

        @pytest.mark.hello
        def test_error(name):
            assert name == "hello"
        """
    )

    testdir.makepyfile(test_emoji_tests=emoji_tests)


@pytest.fixture(name="custom_emojis", autouse=True)
def fixture_custom_emojis(request, testdir):
    """Create a conftest.py file for emoji tests, which implements the
    pytest-emoji hooks.
    """

    if "emoji" not in request.keywords:
        # Only create a conftest.py for emoji tests
        return

    conftest = textwrap.dedent(
        """\
        def pytest_emoji_passed(config):
            return "🦊 ", "PASSED 🦊 "


        def pytest_emoji_failed(config):
            return "😿 ", "FAILED 😿 "


        def pytest_emoji_skipped(config):
            return "🙈 ", "SKIPPED 🙈 "


        def pytest_emoji_error(config):
            return "💩 ", "ERROR 💩 "


        def pytest_emoji_xfailed(config):
            return "🤓 ", "XFAIL 🤓 "


        def pytest_emoji_xpassed(config):
            return "😜 ", "XPASS 😜 "
    """
    )

    testdir.makeconftest(conftest)


class Mode(enum.Enum):
    """Enum for the several test scenarios."""

    NORMAL = "normal"
    VERBOSE = "verbose"
    EMOJI_NORMAL = "emoji_normal"
    EMOJI_VERBOSE = "emoji_verbose"


@pytest.fixture(name="cli_options")
def fixture_cli_options(mode):
    """Return CLI options for the different test scenarios."""
    cli_options = {
        Mode.NORMAL: [],
        Mode.VERBOSE: ["-v"],
        Mode.EMOJI_NORMAL: ["--emoji"],
        Mode.EMOJI_VERBOSE: ["-v", "--emoji"],
    }
    return cli_options[mode]


@pytest.fixture(name="now")
def fixture_now():
    """Patch the current time for reproducable test reports."""
    freezer = freezegun.freeze_time("2019-01-21 18:30:40")
    freezer.start()
    yield datetime.datetime(2019, 1, 21, 18, 30, 40)
    freezer.stop()


@pytest.fixture(name="report_content")
def fixture_report_content(mode, now):
    """Return the expected Markdown report for the different test scenarios."""
    report_date = now.strftime("%d-%b-%Y")
    report_time = now.strftime("%H:%M:%S")

    if mode is Mode.EMOJI_NORMAL:
        return textwrap.dedent(
            f"""\
            # Test Report

            *Report generated on {report_date} at {report_time} by [pytest-md]* 📝

            [pytest-md]: https://github.com/hackebrot/pytest-md

            ## Summary

            7 tests ran in 0.00 seconds ⏱

            - 1 😿
            - 2 🦊
            - 1 🙈
            - 1 🤓
            - 1 😜
            - 1 💩
            """
        )

    if mode is Mode.EMOJI_VERBOSE:
        return textwrap.dedent(
            f"""\
            # Test Report

            *Report generated on {report_date} at {report_time} by [pytest-md]* 📝

            [pytest-md]: https://github.com/hackebrot/pytest-md

            ## Summary

            7 tests ran in 0.00 seconds ⏱

            - 1 failed 😿
            - 2 passed 🦊
            - 1 skipped 🙈
            - 1 xfail 🤓
            - 1 xpass 😜
            - 1 error 💩
            """
        )

    # Return the default report for Mode.NORMAL and Mode.VERBOSE
    return textwrap.dedent(
        f"""\
        # Test Report

        *Report generated on {report_date} at {report_time} by [pytest-md]*

        [pytest-md]: https://github.com/hackebrot/pytest-md

        ## Summary

        7 tests ran in 0.00 seconds

        - 1 failed
        - 2 passed
        - 1 skipped
        - 1 xfailed
        - 1 xpassed
        - 1 error
        """
    )


@pytest.fixture(name="report_path")
def fixture_report_path(tmp_path):
    """Return a temporary path for writing the Markdown report."""
    return tmp_path / "emoji_report.md"


def pytest_make_parametrize_id(config, val):
    """Return a custom test ID for Mode parameters."""
    if isinstance(val, Mode):
        return val.value
    return f"{val!r}"


def pytest_collection_modifyitems(items, config):
    """Skip tests marked with "emoji" if pytest-emoji is not installed."""
    if config.pluginmanager.hasplugin("emoji"):
        return

    for item in items:
        if item.get_closest_marker("emoji"):
            item.add_marker(pytest.mark.skip(reason="pytest-emoji is not installed"))


def pytest_generate_tests(metafunc):
    """Generate several values for the "mode" fixture and add the "emoji"
    marker for certain test scenarios.
    """
    if "mode" in metafunc.fixturenames:
        metafunc.parametrize(
            "mode",
            [
                Mode.NORMAL,
                Mode.VERBOSE,
                pytest.param(Mode.EMOJI_NORMAL, marks=pytest.mark.emoji),
                pytest.param(Mode.EMOJI_VERBOSE, marks=pytest.mark.emoji),
            ],
        )
