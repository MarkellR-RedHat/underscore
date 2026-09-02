# Vendored from rawlslab-core 64f6302 (2026-09-01). Do not edit here; change MarkellRawls/core and re-run scripts/vendor.py.
"""The RawlsLab shared core.

Modules are vendored into each tool by scripts/vendor.py, never installed as a
dependency, so this package intentionally imports nothing at package level: a
tool that vendors only `gates` must not pay for `geometry`.
"""

__version__ = "0.1.0"
