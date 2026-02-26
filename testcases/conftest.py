"""
pytest configuration for the test suite.
"""
import os

def pytest_addoption(parser):
    """
    Add options to the pytest command line.
    """
    parser.addoption(
        "--no-install",
        action="store_true",
        default=False,
        help="Do not use the installed package, use the local package instead",
    )
    parser.addoption(
        "--keep-temp",
        action="store_true",
        default=False,
        help="Do not delete temporary files after test runs",
    )
    parser.addoption(
        "--show-detail",
        action="store_true",
        default=False,
        help="Show detailed output for each test",
    )


def pytest_configure(config):
    """
    Export pytest options to environment variables so test modules can read them
    at import time without inspecting sys.argv.
    """
    
    if config.getoption("--no-install"):
        os.environ["DOFOLDER_TEST_NO_INSTALL"] = "1"

    if config.getoption("--keep-temp"):
        os.environ["DOFOLDER_TEST_KEEP_TEMP"] = "1"

    if config.getoption("--show-detail"):
        os.environ["DOFOLDER_TEST_SHOW_DETAIL"] = "1"

