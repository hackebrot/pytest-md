import textwrap
import pytest


@pytest.fixture(name="use_custom_emoji", autouse=True)
def fixture_use_custom_emoji(testdir):
    """Create a conftest.py file for tests in this module, which implements
    pytest-emoji hooks.
    """
    testdir.makeconftest(
        textwrap.dedent(
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
    )


@pytest.fixture(name="report_project_link")
def fixture_report_project_link(now):
    """Return the report project link text with pytest-emoji enabled."""

    report_date = now.strftime("%d-%b-%Y")
    report_time = now.strftime("%H:%M:%S")

    return textwrap.dedent(
        f"""\
        *Report generated on {report_date} at {report_time} by [pytest-md]* 📝

        [pytest-md]: https://github.com/hackebrot/pytest-md"""
    )


@pytest.fixture(name="report_summary")
def fixture_report_summary(request):
    """Return the report summary for normal mode and verbose mode."""

    summaries = {
        "normal": textwrap.dedent(
            f"""\
            ## Summary

            7 tests ran in 0.00 seconds ⏱

            - 1 😿
            - 2 🦊
            - 1 🙈
            - 1 🤓
            - 1 😜
            - 1 💩
        """
        ),
        "verbose": textwrap.dedent(
            f"""\
            ## Summary

            7 tests ran in 0.00 seconds ⏱

            - 1 failed 😿
            - 2 passed 🦊
            - 1 skipped 🙈
            - 1 xfail 🤓
            - 1 xpass 😜
            - 1 error 💩
        """
        ),
    }

    return summaries[request.param]


@pytest.mark.emoji
@pytest.mark.parametrize(
    "extra_options, report_summary",
    [([], "normal"), (["--verbose"], "verbose")],
    indirect=["report_summary"],
    ids=["normal", "verbose"],
)
def test_generate_markdown_report_with_emoji(
    testdir, emoji_tests, report_path, report_content, extra_options
):
    """Test the generated markdown report for verbose and normal mode."""

    # create a temporary pytest test module
    testdir.makepyfile(emoji_tests)

    # run pytest with the following cmd args
    result = testdir.runpytest(*extra_options, "--emoji", "--md", f"{report_path}")

    # make sure that that we get a '1' exit code
    # as we have at least one failure
    assert result.ret == 1

    # Check the generated Markdown report
    assert report_path.read_text() == report_content
