.PHONY: install dev test lint clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ --cov=deeporra --cov-report=term-missing

lint:
	python -m flake8 deeporra/ tests/
	python -m mypy deeporra/ --ignore-missing-imports

clean:
	rm -rf __pycache__ */__pycache__ */*/__pycache__
	rm -rf .pytest_cache .coverage htmlcov
	rm -rf *.egg-info dist build
	rm -rf deeporra_data
