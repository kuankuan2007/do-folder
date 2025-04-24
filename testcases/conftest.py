def pytest_addoption(parser):
    parser.addoption(
        "--no-install",
        action="store_true",
        default=False,
        help="Do not use the installed package, use the local package instead",
    )