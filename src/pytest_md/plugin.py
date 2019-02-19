import datetime
import collections
import pathlib
import time


OUTCOMES = ("failed", "passed", "skipped", "xfailed", "xpassed", "error")


class MarkdownPlugin:
    """Plugin for generating Markdown test result reports."""

    def __init__(self, config, report_path):
        self.config = config
        self.report_path = report_path
        self.reports = collections.defaultdict(list)
        self.emojis_enabled = self._emojis_enabled()
        self._emoji_repr = None

    def _emojis_enabled(self):
        if not self.config.pluginmanager.hasplugin("emoji"):
            return False
        return self.config.option.emoji is True

    @property
    def emoji_repr(self):
        if self._emoji_repr is not None:
            return self._emoji_repr

        emoji_hooks = {
            "passed": self.config.hook.pytest_emoji_passed,
            "error": self.config.hook.pytest_emoji_error,
            "skipped": self.config.hook.pytest_emoji_skipped,
            "failed": self.config.hook.pytest_emoji_failed,
            "xfailed": self.config.hook.pytest_emoji_xfailed,
            "xpassed": self.config.hook.pytest_emoji_xpassed,
        }

        def emoji_repr(short, verbose):
            if self.config.option.verbose > 0:
                return verbose
            return short

        self._emoji_repr = {
            outcome: emoji_repr(*hook(config=self.config))
            for outcome, hook in emoji_hooks.items()
        }
        return self._emoji_repr

    def pytest_runtest_logreport(self, report):
        if report.when in ("setup", "teardown"):
            if report.failed:
                self.reports["error"].append(report)
                return
            elif report.skipped:
                self.reports["skipped"].append(report)
                return

        if hasattr(report, "wasxfail"):
            if report.skipped:
                self.reports["xfailed"].append(report)
                return
            elif report.passed:
                self.reports["xpassed"].append(report)
                return
            else:
                return

        if report.when == "call":
            if report.passed:
                self.reports["passed"].append(report)
                return
            elif report.skipped:
                self.reports["skipped"].append(report)
                return
            elif report.failed:
                self.reports["failed"].append(report)
                return

    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep(
            "-", f"generated Markdown report: {self.report_path}"
        )

    def pytest_sessionstart(self, session):
        self.session_start = time.time()

    def create_summary(self):
        outcomes = collections.OrderedDict(
            (outcome, len(self.reports[outcome]))
            for outcome in OUTCOMES
            if outcome in self.reports
        )
        num_tests = sum(outcomes.values())

        summary = f"{num_tests} tests ran in {self.session_duration:.2f} seconds"

        if self.emojis_enabled:
            summary = f"{summary} ⏱ "

        summary += "\n\n"
        outcome_text = ""

        for outcome, count in outcomes.items():
            text = outcome
            if self.emojis_enabled:
                text = self.emoji_repr[outcome]
            outcome_text += f"- {count} {text}\n".lower()

        return summary + outcome_text

    def create_project_link(self):

        extra = ""

        if self.emojis_enabled:
            extra = " 📝"

        now = datetime.datetime.now()
        report_date = now.strftime("%d-%b-%Y")
        report_time = now.strftime("%H:%M:%S")

        project_link = ""
        project_link += f"*Report generated on {report_date} at {report_time} "
        project_link += f"by [pytest-md]*{extra}\n\n"
        project_link += f"[pytest-md]: https://github.com/hackebrot/pytest-md"
        return project_link

    def pytest_sessionfinish(self, session):
        self.session_finish = time.time()
        self.session_duration = self.session_finish - self.session_start

        summary = self.create_summary()
        project_link = self.create_project_link()

        report = ""
        report += f"# Test Report\n\n"
        report += f"{project_link}\n\n"
        report += f"## Summary\n\n{summary}\n\n"

        self.report_path.write_text(report, encoding="utf-8")


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


def pytest_configure(config):
    mdpath = config.getoption("mdpath")

    if not mdpath:
        return

    config._md = MarkdownPlugin(config, pathlib.Path(mdpath).expanduser().resolve())
    config.pluginmanager.register(config._md)


def pytest_unconfigure(config):
    md = getattr(config, "_md", None)

    if not md:
        return

    del config._md
    config.pluginmanager.unregister(md)
