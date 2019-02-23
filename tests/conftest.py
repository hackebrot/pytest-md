import datetime
import textwrap

import freezegun
import pytest

pytest_plugins = "pytester"


@pytest.fixture(name="now")
def fixture_now():
    freezer = freezegun.freeze_time("2019-01-21 18:30:40")
    freezer.start()
    yield datetime.datetime(2019, 1, 21, 18, 30, 40)
    freezer.stop()


@pytest.fixture(name="emoji_tests")
def fixture_emoji_tests():
    return textwrap.dedent(
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


@pytest.fixture(name="report_header")
def fixture_report_header():
    return "# Test Report"


@pytest.fixture(name="report_project_link")
def fixture_report_project_link(now):
    report_date = now.strftime("%d-%b-%Y")
    report_time = now.strftime("%H:%M:%S")
    return textwrap.dedent(
        f"""\
        *Report generated on {report_date} at {report_time} by [pytest-md]*

        [pytest-md]: https://github.com/hackebrot/pytest-md"""
    )


@pytest.fixture(name="report_summary")
def fixture_report_summary():
    # The session duration should always be 0.00 seconds
    # since we patched time.time() with freezegun
    return textwrap.dedent(
        f"""\
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


@pytest.fixture(name="report_content")
def fixture_report_content(report_header, report_project_link, report_summary):
    report = ""
    report += f"{report_header}\n\n"
    report += f"{report_project_link}\n\n"
    report += f"{report_summary}"
    return report


@pytest.fixture(name="report_path")
def fixture_report_path(tmp_path):
    return tmp_path / "emoji_report.md"
