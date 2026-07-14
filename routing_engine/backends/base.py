"""Shared v2 artifact contract."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedArtifact:
    relative_path: str
    content: bytes
    media_type: str = "text/plain; charset=utf-8"
