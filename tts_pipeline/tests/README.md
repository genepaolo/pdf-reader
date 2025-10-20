# TTS Pipeline Test Suite

This comprehensive test suite provides robust validation for the TTS pipeline system, ensuring reliability and preventing regressions.

## Test Structure

### Directory Organization
```
tests/
├── README.md                          # This file
├── requirements.txt                   # Test dependencies
├── conftest.py                       # Pytest configuration and fixtures
├── test_data/                        # Sample test data
│   ├── chapters/                     # Sample chapter files
│   ├── configs/                      # Test configuration files
│   ├── audio/                        # Sample audio files
│   └── tracking/                     # Sample tracking data
├── utils/                            # Test utilities and helpers
├── unit/                            # Unit tests
├── integration/                     # Integration tests
├── performance/                     # Performance tests
├── regression/                      # Regression tests
└── reports/                         # Test reports and outputs
```

## Test Categories

### 1. Unit Tests (`unit/`)
- **Purpose**: Test individual components in isolation
- **Scope**: Single functions, classes, or modules
- **Mocking**: Heavy use of mocks for external dependencies
- **Speed**: Fast execution (< 1 second per test)

### 2. Integration Tests (`integration/`)
- **Purpose**: Test component interactions and workflows
- **Scope**: Multiple components working together
- **Mocking**: Limited mocking, real file operations
- **Speed**: Medium execution (1-10 seconds per test)

### 3. Performance Tests (`performance/`)
- **Purpose**: Validate performance characteristics
- **Scope**: Large files, memory usage, API limits
- **Mocking**: Minimal mocking for realistic testing
- **Speed**: Longer execution (10+ seconds per test)

### 4. Regression Tests (`regression/`)
- **Purpose**: Ensure nothing breaks with changes
- **Scope**: Critical functionality verification
- **Mocking**: Mixed approach based on test needs
- **Speed**: Medium execution (1-5 seconds per test)

## Running Tests

### Basic Commands
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/
pytest tests/regression/

# Run with coverage
pytest tests/ --cov=tts_pipeline --cov-report=html

# Run specific test
pytest tests/unit/test_file_organizer.py::test_discover_chapters

# Generate test report
pytest tests/ --html=reports/test_report.html
```

### Test Output Format
All tests provide standardized output:
```python
{
    "test_name": "test_chapter_discovery",
    "status": "PASSED|FAILED|SKIPPED",
    "execution_time": "0.045s",
    "assertions": 5,
    "data_points": {
        "chapters_found": 1432,
        "volumes_discovered": 9,
        "side_stories_included": True
    },
    "timestamp": "2025-01-18T23:30:15Z",
    "details": "Successfully discovered all chapters including Side_Stories"
}
```

## Test Data Management
- **Sample Files**: Minimal but realistic test data
- **Dynamic Generation**: Create test files programmatically when needed
- **Cleanup**: Automatic cleanup after test execution
- **Isolation**: Each test uses its own temporary directory

## Test Naming Convention
- **Files**: `test_[component_name].py`
- **Functions**: `test_[specific_functionality]`
- **Classes**: `Test[ComponentName]`
- **Fixtures**: `[component]_fixture`

## Dependencies
See `requirements.txt` for test-specific dependencies including:
- pytest
- pytest-cov
- pytest-mock
- pytest-html

## Best Practices
1. **Isolation**: Each test should be independent
2. **Cleanup**: Always clean up test data after execution
3. **Mocking**: Use mocks for external dependencies
4. **Assertions**: Use descriptive assertion messages
5. **Documentation**: Document complex test scenarios
6. **Performance**: Monitor test execution time
7. **Coverage**: Maintain high test coverage (>90%)

## Contributing
When adding new tests:
1. Follow the naming conventions
2. Place tests in appropriate category directories
3. Update this README if adding new test categories
4. Ensure tests are deterministic and repeatable
5. Add appropriate fixtures for reusable test data
