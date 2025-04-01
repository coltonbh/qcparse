set -xe
# Run tests
uv run pytest --cov-report=term-missing --cov-report html:htmlcov --cov-config=pyproject.toml --cov=qccodec --cov=tests .
