"""Expose the project's custom modules without shadowing MMSegmentation."""

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent.parent / 'mmseg')]
