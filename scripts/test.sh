#!/bin/bash

set -e

echo "Running tests"
echo "=================================================="

echo "Installing dependencies..."
pip install -r requirements-dev.txt

echo "Running tests with coverage..."
pytest --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml -v

echo "Test Coverage Summary:"
coverage report --show-missing

echo "Running Unit Tests..."
pytest tests/test_models/ tests/test_services/ -v -m "not api"

echo "Running API Tests..."
pytest tests/test_api/ -v -m "api"
