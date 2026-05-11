from gbs_analyzer import __version__


def test_package_exposes_dev_version() -> None:
    assert __version__ == "0.5.0-dev"
