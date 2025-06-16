"""
pytest configuration for the test suite.
"""
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