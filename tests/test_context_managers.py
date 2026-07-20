import pytest

from finlib.context_managers import timer


def test_timer_prints_elapsed_without_label(capsys: pytest.CaptureFixture[str]) -> None:
    with timer():
        pass
    out = capsys.readouterr().out
    assert "s" in out

def test_timer_prints_label(capsys: pytest.CaptureFixture[str]) -> None:
    with timer("my operation"):
        pass
    out = capsys.readouterr().out
    assert "my operation" in out

def test_timer_does_not_suppress_exceptions(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(ValueError):
        with timer("failing"):
            raise ValueError("boom")
