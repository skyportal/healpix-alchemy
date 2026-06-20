# Changes

## Unreleased

- Support NumPy 2. Drop support for Python 3.10, which is incompatible with
  NumPy 2.4 because the only compatible Astropy release for Python 3.10
  (6.1.x) still references the removed `numpy.in1d`. Run unit tests for
  Python 3.11 through 3.14.

## 1.1.0 (2024-04-16)

- Don't include the unit tests in the installed Python package.

- Drop support for Python 3.9. Add support for, and run unit tests for,
  Python 3.12.

- Update build system for compatibility with the latest version of Poetry.

## 1.0.2 (2023-03-03)

- Track API changes in mocpy.

- Fix compatibility with SQLAlchemy 2.x.

## 1.0.1 (2021-12-08)

- Add benchmarks to unit test suite.

- Update the doctest examples in the README file to match the paper draft.

- Add code coverage analysis with Codecov.io.

## 1.0.0 (2021-11-22)

- First stable release.
