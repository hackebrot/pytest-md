# pytest-md

Plugin for generating Markdown reports for pytest results 📝

## Usage

The following example code produces the different pytest test outcomes.

```python
import random
import pytest


def test_passed():
    assert "emoji" == "hello world"


def test_failed():
    assert "emoji" == "hello world"


@pytest.mark.xfail
def test_xfail():
    assert random.random() == 1.0


@pytest.mark.xfail
def test_xpass():
    assert 0.0 < random.random() < 1.0


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
```

With **pytest-md** installed, you can now generate a Markdown test report as
follows:

```text
$ pytest --md report.md
```

```Markdown
# Test Report

*Report generated on 25-Feb-2019 at 15:18:42 by [pytest-md]*

[pytest-md]: https://github.com/hackebrot/pytest-md

## Summary

8 tests ran in 0.11 seconds

- 1 failed
- 3 passed
- 1 skipped
- 1 xfailed
- 1 xpassed
- 1 error
```

## pytest-emoji

**pytest-md** also integrates with [pytest-emoji], which allows us to include
emojis in the generated Markdown test report:

```text
$ pytest --emoji -v --md report.md
```

```Markdown
# Test Report

*Report generated on 25-Feb-2019 at 15:18:42 by [pytest-md]* 📝

[pytest-md]: https://github.com/hackebrot/pytest-md

## Summary

8 tests ran in 0.07 seconds ⏱

- 1 failed 😰
- 3 passed 😃
- 1 skipped 🙄
- 1 xfail 😞
- 1 xpass 😲
- 1 error 😡
```

[pytest-emoji]: https://github.com/hackebrot/pytest-emoji

## Community

Please note that **pytest-md** is released with a [Contributor Code of
Conduct][code of conduct]. By participating in this project you agree to abide
by its terms.

[code of conduct]: https://github.com/hackebrot/pytest-md/blob/master/CODE_OF_CONDUCT.md

## License

Distributed under the terms of the MIT license, **pytest-md** is free and open
source software.

## Credits

This project is inspired by the fantastic [pytest-html] plugin!

[pytest-html]: https://github.com/pytest-dev/pytest-html
