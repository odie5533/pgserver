# Changelog

## [0.2.0] - 2025-11-07

### Added
- Support for PostgreSQL 17 and 18 (in addition to existing PostgreSQL 16)
- Multi-version architecture with separate binary packages:
  - `pgserver-postgres-16` - PostgreSQL 16.10 binaries
  - `pgserver-postgres-17` - PostgreSQL 17.6 binaries
  - `pgserver-postgres-18` - PostgreSQL 18.0 binaries
- Version selection via pip extras:
  - `pip install pgserver` - installs PostgreSQL 18 (default)
  - `pip install "pgserver[pg16]"` - installs PostgreSQL 16
  - `pip install "pgserver[pg17]"` - installs PostgreSQL 17
- `INSTALLED_POSTGRES_VERSION` constant to check which version is installed

### Changed
- Main `pgserver` package is now a universal wheel (py3-none-any) compatible with all Python 3.9+ versions
- Binary packages are distributed separately from Python code, reducing download size
- Upgraded pgvector extension to v0.8.1 for PostgreSQL 18 compatibility
- PostgreSQL binaries now use RPATH to find bundled libraries, preventing conflicts with system PostgreSQL installations
