import pytest

from nws_wwa import get_all, get_hazards, get_warnings


@pytest.mark.vcr()
def test_all():
    get_all()


@pytest.mark.vcr()
def test_hazards():
    get_hazards()


@pytest.mark.vcr()
def test_warnings():
    get_warnings()
