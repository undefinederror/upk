# Changelog

All notable changes to this project will be documented in this file.

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
