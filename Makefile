# Makefile for ai_utilities testing and coverage

.PHONY: test test-fast cov help

# Default target
help:
	@echo "Available targets:"
	@echo "  test      - Run full test suite with coverage (pytest.ini adds --cov)"
	@echo "  test-fast - Run tests quietly"
	@echo "  cov       - Run tests with coverage reports (term + html)"
	@echo "  help      - Show this help"

# Run full test suite with coverage (pytest.ini already adds --cov)
test:
	python -m pytest

# Run tests quietly
test-fast:
	python -m pytest -q

# Run tests with explicit coverage reports
cov:
	python -m pytest --cov=ai_utilities --cov-report=term-missing --cov-report=html:coverage_reports/html
