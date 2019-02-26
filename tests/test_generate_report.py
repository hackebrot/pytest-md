def test_generate_report(testdir, cli_options, report_path, report_content):
    """Check the contents of a generated Markdown report."""
    # run pytest with the following CLI options
    result = testdir.runpytest(*cli_options, "--md", f"{report_path}")

    # make sure that that we get a '1' exit code
    # as we have at least one failure
    assert result.ret == 1

    # Check the generated Markdown report
    assert report_path.read_text() == report_content
