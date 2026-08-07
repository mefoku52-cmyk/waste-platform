# Load Testing

This document describes load testing for the Circular Materials Exchange Platform using k6.

## Available tests
- `tests/load/k6/smoke-test.js`
- `tests/load/k6/load-test.js`
- `tests/load/k6/breakpoint-test.js`

## Run tests locally
```bash
BASE_URL=http://localhost:8000 ./scripts/load-test.sh smoke
BASE_URL=http://localhost:8000 ./scripts/load-test.sh load
BASE_URL=http://localhost:8000 ./scripts/load-test.sh breakpoint
