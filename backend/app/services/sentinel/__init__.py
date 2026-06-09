"""
Package sentinel - Modular Sentinel-2 acquisition service.

Exports:
    SentinelService: Main orchestrator service
"""

from .sentinel_service import SentinelService

__all__ = ["SentinelService"]
