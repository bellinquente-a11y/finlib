# CHANGELOG.md

## [0.6.3] - 2026-07-28

### Added

    - feat: enhance release script to support tagging and improved version handling

## [0.6.2] - 2026-07-28

### Added

    - Sample trades data in JSONL
    - CONTRIBUTING.md guide
    - Release update script to automate versioning and changelog verification

### Changed

    - Enhanced output formatting and improve market summary display in pipeline CLI
    - Simplied README.md for non dev user

### Fixed

    - Updated repository URL in installation instructions

## [0.6.1] - 2026-07-24

### Added

- add: CODEOWNERS file; pull request template

### Changed

- increase pytest coverage threshold from 85 to 90 in CI configuration
- enhance CI configuration with concurrency and Python version matrix

### Fixed

- update CI badge in README to reflect new repository owner

## [0.6.0] - 2026-07-22

### Added

- conftest fixtures
- property-based suite (Hypothesis)
- Kelly sizer
- pre-commit hooks
- expanded ruff rule set
- missing raise tests

### Changed

- CI coverage gate raised to 85% (corrected from 90% in the tag)
- improved code quality following implementation of pre-commit hooks and expanded ruff rule set

### Fixed

- correct query construction in InMemoryOHLCVRepository and FileOHLCVRepository to use last_timestamp variable directly

## [0.5.0] - 2026-07-16

### Added

- validated fetch functionality for Binance data
- add hypothesis library as a dependency in pyproject.toml; update poetry.lock with new package details
- add maximum drawdown calculation function to historic analytics; enhance tests for maximum drawdown scenarios

### Changed

- optimize timestamp retrieval in OHLCV repositories by avoiding O(n^2) search

## [0.4.2] - 2026-07-07

### Fixed

- correct invalid row count increment in async fetch

## [0.4.1] - 2026-07-07

### Changed

- update LEARNING_LOG with week retrospectives and deliverables; enhance structure for clarity

## [0.4.0] - 2026-07-07

### Added

- Implemented a pipeline for portfolio marking-to-market analysis
- Adopted the repository framework for improved testability
- Pipeline tests
- Add historic position, cost basis, market value, and PnL calculations to Portfolio class

### Changed

- Enhance Binance data fetching with improved data validation, support for multiple rows, and conversion to DataFrame
- Extend add_intervals_batch method to support column mapping for batch input in OHLCVRepo

## [0.3.0] - 2026-07-01

### Added

- Context managers and decorators for timing and retry functionality
- Integrate structlog for structured logging
- Concurrency benchmark script
- Implement in-file trade repository

### Fixed

- Update poetry installation to require version 2.0 or higher
- Update CI workflow to install development dependencies with Poetry


## [0.2.1] - 2026-06-26

### Fixed

- Bug fix in validation history fetch

## [0.2.0] - 2026-06-26

### Added

- Utility functions for trade grouping and summary
- Improve portfolio class methods
- Introduce input validation decorator
- Async price fetcher with aiohttp and pydantic validation - source: Binance
- Portfolio service class
- Pydantic library settings

## [0.1.0] - 2026-06-21

### Added

- Trade model with pydantic validation
- pytest -cov
- github workflows (CI): ruff, mypy, pytest
