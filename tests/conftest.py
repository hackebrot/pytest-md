import enum
import datetime
import textwrap

import freezegun
import pytest

pytest_plugins = ["pytester"]


@pytest.fixture(name="emoji_tests", autouse=True)
def fixture_emoji_tests(testdir):
    """Create a test module with several tests that produce all the different
    pytest test outcomes.
    """
    emoji_tests = textwrap.dedent(
        """\
        import pytest


        def test_failed():
            assert "emoji" == "hello world"


        @pytest.mark.xfail
        def test_xfailed():
            assert 1234 == 100


        @pytest.mark.xfail
        def test_xpass():
            assert 1234 == 1234


        @pytest.mark.skip(reason="don't run this test")
        def test_skipped():
            assert "pytest-emoji" != ""


        @pytest.mark.parametrize(
            "name, expected",
            [
                ("Sara", "Hello Sara!"),
                ("Mat", "Hello Mat!"),
                ("Annie", "Hello Annie!"),
            ],
        )
        def test_passed(name, expected):
            assert f"Hello {name}!" == expected


        @pytest.fixture
        def number():
            return 1234 / 0


        def test_error(number):
            assert number == number
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
            return "🤓 ", "XFAILED 🤓 "


        def pytest_emoji_xpassed(config):
            return "😜 ", "XPASSED 😜 "
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
        Mode.VERBOSE: ["--verbose"],
        Mode.EMOJI_NORMAL: ["--emoji"],
        Mode.EMOJI_VERBOSE: ["--verbose", "--emoji"],
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

            8 tests ran in 0.00 seconds ⏱

            - 1 😿
            - 3 🦊
            - 1 🙈
            - 1 🤓
            - 1 😜
            - 1 💩"""
        )

    if mode is Mode.EMOJI_VERBOSE:
        return textwrap.dedent(
            f"""\
            # Test Report

            *Report generated on {report_date} at {report_time} by [pytest-md]* 📝

            [pytest-md]: https://github.com/hackebrot/pytest-md

            ## Summary

            12 tests ran in 0.10 seconds ⏱

                - 2 error 😡
                - 1 failed 😰
                - 3 passed 😃
                - 2 skipped 🙄
                - 2 xfail 😞
                - 2 xpass 😲

            ## 2 error 😡

            ### test_example1.py

            0.02 s ⏱ `ERROR at setup of test_error`

            ```
                @pytest.fixture
                def number():
            >       return 1234 / 0
            E       ZeroDivisionError: division by zero

            test_example1.py:34: ZeroDivisionError
            ```

            ### test_example2.py

            0.02 s ⏱ `ERROR at setup of test_nope`

            ```
                @pytest.fixture
                def number():
            >       return 1234 / 0
            E       ZeroDivisionError: division by zero

            test_example2.py:23: ZeroDivisionError
            ```

            ## 1 failed 😰

            0.22 s ⏱ `test_failed`

            ```
                def test_failed():
            >       assert "emoji" == "hello world"
            E       AssertionError: assert 'emoji' == 'hello world'
            E         - emoji
            E         + hello world

            test_example1.py:6: AssertionError
            ```

            ## 3 passed 😃

            ### test_example1.py

            0.08 s ⏱ `test_passed[Sara-Hello Sara!]`
            0.07 s ⏱ `test_passed[Mat-Hello Mat!]`
            0.08 s ⏱ `test_passed[Annie-Hello Annie!]`

            ## 2 skipped 🙄

            ### test_example1.py

            0.00 s ⏱ `test_skipped`

            ### test_example2.py

            0.00 s ⏱ `test_skipped`

            ## 2 xfail 😞

            ### test_example1.py

            0.40 s ⏱ `test_xfail`

            ### test_example2.py

            0.20 s ⏱ `test_xfail`

            ## xpass 😲

            ### test_example1.py

            0.42 s ⏱ `test_xpass`

            ### test_example2.py

            0.22 s ⏱ `test_xpass`
"""
        )

    if mode is Mode.VERBOSE:
        return textwrap.dedent(
            f"""\
            # Test Report

            *Report generated on {report_date} at {report_time} by [pytest-md]*

            [pytest-md]: https://github.com/hackebrot/pytest-md

            ## Summary

            8 tests ran in 0.00 seconds

            - 1 failed
            - 3 passed
            - 1 skipped
            - 1 xfailed
            - 1 xpassed
            - 1 error"""
        )

    # Return the default report for Mode.NORMAL
    return textwrap.dedent(
        f"""\
        # Test Report

        *Report generated on {report_date} at {report_time} by [pytest-md]*

        [pytest-md]: https://github.com/hackebrot/pytest-md

        ## Summary

        8 tests ran in 0.00 seconds

        - 1 failed
        - 3 passed
        - 1 skipped
        - 1 xfailed
        - 1 xpassed
        - 1 error"""
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


def pytest_generate_tests(metafunc):
    """Generate several values for the "mode" fixture and add the "emoji"
    marker for certain test scenarios.
    """
    if "mode" not in metafunc.fixturenames:
        return

    metafunc.parametrize(
        "mode",
        [
            Mode.NORMAL,
            Mode.VERBOSE,
            pytest.param(Mode.EMOJI_NORMAL, marks=pytest.mark.emoji),
            pytest.param(Mode.EMOJI_VERBOSE, marks=pytest.mark.emoji),
        ],
    )


def pytest_collection_modifyitems(items, config):
    """Skip tests marked with "emoji" if pytest-emoji is not installed."""
    if config.pluginmanager.hasplugin("emoji"):
        return

    for item in items:
        if item.get_closest_marker("emoji"):
            item.add_marker(pytest.mark.skip(reason="pytest-emoji is not installed"))
