"""
CareerEngine Local Web Studio Package.
Provides a local-first GUI to inspect applications, database metrics, screenshots, and orchestrate CLI runs.
"""

from .server import start_studio_server

__all__ = ["start_studio_server"]
