def test_generate_markdown_report(testdir, emoji_tests, report_path, report_content):
    # create a temporary pytest test module
    testdir.makepyfile(emoji_tests)

    # run pytest with the following cmd args
    result = testdir.runpytest("--md", f"{report_path}")

    # make sure that that we get a '1' exit code
    # as we have at least one failure
    assert result.ret == 1

    # Check the generated Markdown report
    assert report_path.read_text() == report_content
