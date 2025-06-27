import pytest

def pytest_addoption(parser):
    parser.addoption(
        "-G",
        "--generate",
        action="store_true",
        help="Generate testing data.",
    )

@pytest.fixture(scope="session")
def generate_benchmarks(request):
    """Whether generating benchmarks."""
    return request.config.getoption("--generate", False)
