import pyfive

from importlib.metadata import version


def test_version():
    """Test package version."""
    __version__ = version("pyfive")
    print(__version__)
    assert int(__version__[0]) == 1
    assert pyfive.__version__ == __version__
