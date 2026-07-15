"""Pytest bootstrap for source-layout imports.

Ensures repository root is on sys.path so imports like ``src.main`` work
even when tests are collected from within the tests directory.
"""

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
repo_root_str = str(REPO_ROOT)
if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)
