def pytest_addoption(parser):
    parser.addoption("--run-optional", action="store_true", help="Run optional tests")
