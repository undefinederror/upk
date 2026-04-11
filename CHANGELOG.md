# Changelog

All notable changes to this project will be documented in this file.

## [1.2.2] - 2026-04-10

### Added
- **Smart Pacstall Deduplication**: Added metadata parsing for `gives`, `provides`, and `replaces` fields. `upk` now correctly identifies Pacstall packages (like `bitwarden-deb`) as aliasing standard system packages, preventing duplicate entries and prioritizing clean removals.

## [1.2.1] - 2026-03-18

### Refactored
- **Project Structure**: Completely reorganized into a standard Python package format.
- **Packaging**: Switched to `pyproject.toml` and declarative metadata.
- **Infrastructure**: Simplified `setup.py`, `build.sh`, and `pacscript` logic.

## [1.2.0] - 2026-03-14

### Added
- **UI Enhancements**: Combined Version and Installed columns for a cleaner look.
- **Live Progress**: Added backend-specific progress tracking for installed status checks.
- **Description Column**: Added a dedicated description column to the search and list views.

## [1.1.1] - 2026-03-12

### Fixed
- **Pipeline**: Fixed compilation on github actions.

## [1.1.0] - 2026-03-12

### Added
- **Terminal Autocomplete**: Full Bash completion support is now included in the `.deb` package.

### Fixed
- Resolved a `TypeError` when handling local file installations with certain flags.

## [1.0.1] - 2026-03-11
- Initial stable release with multi-backend support (APT, Snap, Flatpak, Pacstall, am).
