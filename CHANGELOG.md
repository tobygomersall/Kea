# Changelog
All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.10.0 - 2026-02-27

### Changed

- Added a `signal_out_valid` signal to `kea.hdl.signal_handling.synchronous.synchronous_saturating_rounding_slicer`.

### Added

- Added interface checks so blocks can check ports are correct.

## 0.9.3 - 2026-01-21

### Changed

- Added `xvlog.pb` to `.gitignore`. Newer versions of Vivado output an `xvlog.pb` but we don't want it in version control.

## 0.9.2 - 2026-01-13

### Fixed

- Fixed `kea/xilinx/vivado_utils/cosimulation.py` so it is compatible with Vivado 2025.2.

## 0.9.1 - 2026-01-07

### Fixed

- Fixed a syntax warning in `kea.testing.myhdl.cosimulation`.

## 0.9.0 - 2025-12-19

The changes here document all the changes since version 0.8.0.

### Changed

- Updated the python requirement to compatible with 3.12.3.
    - Fixed all deprecation warnings.
- Updated MyHDL to the latest.
- Updated all packages.

### Added

- Added setuptools as a dependency because they are no longer included by default in venvs.
