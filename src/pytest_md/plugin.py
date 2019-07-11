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

    def __init__(self, config, report_path, emojis_enabled=False):
        self.config = config
        self.report_path = report_path
        self.report = ""
        self.emojis_enabled = emojis_enabled

        self.reports = collections.defaultdict(list)

        if emojis_enabled:
            self.emojis_by_outcome = self._retrieve_emojis()

    def _retrieve_emojis(self):
        """Return a mapping from report Outcome to an emoji text."""

        def emoji(short, verbose):
            """Return the short or verbose emoji based on self.config."""

            if self.config.option.verbose > 0:
                return verbose

            return short

        return {
            outcome: emoji(*emoji_hook(config=self.config))
            for outcome, emoji_hook in (
                (Outcome.PASSED, self.config.hook.pytest_emoji_passed),
                (Outcome.ERROR, self.config.hook.pytest_emoji_error),
                (Outcome.SKIPPED, self.config.hook.pytest_emoji_skipped),
                (Outcome.FAILED, self.config.hook.pytest_emoji_failed),
                (Outcome.XFAILED, self.config.hook.pytest_emoji_xfailed),
                (Outcome.XPASSED, self.config.hook.pytest_emoji_xpassed),
            )
        }

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

        return "# Test Report\n"

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
        project_link += f"[pytest-md]: https://github.com/hackebrot/pytest-md\n"

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
                text = self.emojis_by_outcome[outcome].strip()

            outcome_text += f"- {count} {text}\n".lower()

        summary = ""
        summary += f"## Summary\n\n"
        summary += f"{total_count} tests ran in {self.session_duration:.2f} seconds"

        if self.emojis_enabled:
            summary = f"{summary} ⏱"

        return summary + "\n\n" + outcome_text

    def create_results(self):
        """Create results for the individual tests for the Markdown report."""

        outcomes = {}

        for outcome in (o for o in Outcome if o in self.reports):
            reports_by_file = collections.defaultdict(list)

            for report in self.reports[outcome]:
                test_file = report.location[0]
                reports_by_file[test_file].append(report)

            outcomes[outcome] = reports_by_file

        results = ""

        for outcome, reports_by_file in outcomes.items():
            outcome_text = outcome.value

            if self.emojis_enabled:
                outcome_text = self.emojis_by_outcome[outcome].strip()

            results += f"## {len(self.reports[outcome])} {outcome_text}\n\n".lower()

            for test_file, reports in reports_by_file.items():
                results += f"### {test_file}\n\n"

                for report in reports:
                    test_function = report.location[2]

                    if outcome is Outcome.ERROR:
                        results += (
                            f"`{outcome.value} at {report.when} of {test_function}`"
                        )
                    else:
                        results += f"`{test_function}`"

                    results += f" {report.duration:.2f}s"
                    if self.emojis_enabled:
                        results += " ⏱"

                    results += "\n"

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

        self.report += f"{header}\n"
        self.report += f"{project_link}\n"
        self.report += f"{summary}\n"

        if self.config.option.verbose > 0:
            results = self.create_results()
            self.report += f"{results}"

        self.report_path.write_text(self.report.rstrip() + "\n", encoding="utf-8")


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

    def emojis_enabled():
        """Check if pytest-emoji is installed and enabled."""

        if not config.pluginmanager.hasplugin("emoji"):
            return False

        return config.option.emoji is True

    config._md = MarkdownPlugin(
        config,
        report_path=pathlib.Path(mdpath).expanduser().resolve(),
        emojis_enabled=emojis_enabled(),
    )

    config.pluginmanager.register(config._md, "md_plugin")


def pytest_unconfigure(config):
    """Hook implementation that unregisters the plugin."""

    md = getattr(config, "_md", None)

    if not md:
        return

    del config._md
    config.pluginmanager.unregister(md)
