import collections
import datetime
import enum
import pathlib
import time


class Outcome(enum.Enum):
    """Enum for the different pytest outcomes."""

    ERROR = "error"
    FAILED = "failed"
    PASSED = "passed"
    SKIPPED = "skipped"
    XFAILED = "xfailed"
    XPASSED = "xpassed"


class MarkdownPlugin:
    """Plugin for generating Markdown reports."""

    def __init__(self, config, report_path):
        self.config = config
        self.report_path = report_path
        self.reports = collections.defaultdict(list)
        self.emojis_enabled = self._emojis_enabled()
        self._emoji_repr = None

    def _emojis_enabled(self):
        """Check if pytest-emoji is installed and enabled."""

        if not self.config.pluginmanager.hasplugin("emoji"):
            return False
        return self.config.option.emoji is True

    @property
    def emoji_repr(self):
        """Return a mapping from report Outcome to an emoji text."""

        if self._emoji_repr is not None:
            return self._emoji_repr

        def emoji_repr(short, verbose):
            """Return the short or verbose emoji repr based on self.config."""

            if self.config.option.verbose > 0:
                return verbose

            return short

        self._emoji_repr = {
            outcome: emoji_repr(*emoji_hook(config=self.config))
            for outcome, emoji_hook in (
                (Outcome.PASSED, self.config.hook.pytest_emoji_passed),
                (Outcome.ERROR, self.config.hook.pytest_emoji_error),
                (Outcome.SKIPPED, self.config.hook.pytest_emoji_skipped),
                (Outcome.FAILED, self.config.hook.pytest_emoji_failed),
                (Outcome.XFAILED, self.config.hook.pytest_emoji_xfailed),
                (Outcome.XPASSED, self.config.hook.pytest_emoji_xpassed),
            )
        }

        return self._emoji_repr

    def pytest_runtest_logreport(self, report):
        """Hook implementation that collects test reports by outcome."""

        if report.when in ("setup", "teardown"):
            if report.failed:
                self.reports[Outcome.ERROR].append(report)
                return
            elif report.skipped:
                self.reports[Outcome.SKIPPED].append(report)
                return

        if hasattr(report, "wasxfail"):
            if report.skipped:
                self.reports[Outcome.XFAILED].append(report)
                return
            elif report.passed:
                self.reports[Outcome.XPASSED].append(report)
                return
            else:
                return

        if report.when == "call":
            if report.passed:
                self.reports[Outcome.PASSED].append(report)
                return
            elif report.skipped:
                self.reports[Outcome.SKIPPED].append(report)
                return
            elif report.failed:
                self.reports[Outcome.FAILED].append(report)
                return

    def pytest_terminal_summary(self, terminalreporter):
        """Hook implementation that writes the path to the generated report to
        the terminal.
        """

        terminalreporter.write_sep(
            "-", f"generated Markdown report: {self.report_path}"
        )

    def pytest_sessionstart(self, session):
        """Hook implementation to store the time when the session started."""

        self.session_start = time.time()

    def create_header(self):
        """Create a header for the Markdown report."""
        return "# Test Report"

    def create_project_link(self):
        """Create a project link for the Markdown report."""

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

    def create_summary(self):
        """Create a summary for the Markdown report."""

        outcome_text = ""
        total_count = 0

        for outcome in (o for o in Outcome if o in self.reports):
            count = len(self.reports[outcome])
            total_count += count

            text = outcome.value
            if self.emojis_enabled:
                text = self.emoji_repr[outcome].strip()

            outcome_text += f"- {count} {text}\n".lower()

        summary = ""
        summary += f"## Summary\n\n"
        summary += f"{total_count} tests ran in {self.session_duration:.2f} seconds"

        if self.emojis_enabled:
            summary = f"{summary} ⏱"

        return summary + "\n\n" + outcome_text

    def create_results(self):
        """Create results for the individual tests for the Markdown report."""

        outcomes = collections.OrderedDict()

        for outcome in [*Outcome]:
            if outcome not in self.reports:
                continue
            file_reports = collections.OrderedDict()
            for report in self.reports[outcome]:
                filesystempath = report.location[0]
                file_reports.setdefault(filesystempath, [])
                file_reports[filesystempath].append(report)
            outcomes[outcome] = file_reports

        results = ""

        for outcome, file_reports in outcomes.items():
            outcome_text = outcome.value
            if self.emojis_enabled:
                outcome_text = self.emoji_repr[outcome].strip()

            results += f"## {len(self.reports[outcome])} {outcome_text}\n\n"

            for filesystempath, file_reports in file_reports.items():
                results += f"### {filesystempath}\n\n"
                for report in file_reports:
                    domaininfo = report.location[2]
                    results += f"{report.duration:.2f}s"
                    if self.emojis_enabled:
                        results += " ⏱ "

                    if outcome is Outcome.ERROR:
                        results += (
                            f" `{outcome.value} at {report.when} of {domaininfo}`\n"
                        )
                    else:
                        results += f" `{domaininfo}`\n"

                    if outcome in (Outcome.ERROR, Outcome.FAILED):
                        results += f"\n```\n{report.longreprtext}\n```\n"
            results += "\n"
        return results

    def pytest_sessionfinish(self, session):
        """Hook implementation that generates a Markdown report and writes it
        to disk.
        """

        self.session_finish = time.time()
        self.session_duration = self.session_finish - self.session_start

        header = self.create_header()
        project_link = self.create_project_link()
        summary = self.create_summary()

        report = ""
        report += f"{header}\n\n"
        report += f"{project_link}\n\n"
        report += f"{summary}\n"

        if self.config.option.verbose > 0:
            results = self.create_results()
            report += f"{results}"

        # Cleanup trailing lines
        report = f"{report.rstrip()}\n"
        self.report_path.write_text(report, encoding="utf-8")


def pytest_addoption(parser):
    """Hook implementation that adds a "--md" CLI flag."""

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
    """Hook implementation that registers the plugin if "--md" is specified."""

    mdpath = config.getoption("mdpath")

    if not mdpath:
        return

    config._md = MarkdownPlugin(config, pathlib.Path(mdpath).expanduser().resolve())
    config.pluginmanager.register(config._md)


def pytest_unconfigure(config):
    """Hook implementation that unregisters the plugin."""

    md = getattr(config, "_md", None)

    if not md:
        return

    del config._md
    config.pluginmanager.unregister(md)
