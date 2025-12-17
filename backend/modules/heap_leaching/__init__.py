"""
Heap Leaching – Key Controls Module

This module provides engineering controls for gold heap leaching operations.
It is a rule-based, deterministic control module (not reporting or analytics).

Scope:
- Gold heap leaching operations
- Leaching-only (heap already stacked)
- Single heap per instance
- Target heap size: approximately 1,000 tonnes

Design Constraints:
- Rule-based, deterministic logic only
- No AI inference, prediction, or optimisation
- No dashboards or UI at this stage
- No mining, stacking, crushing, or haulage functionality
- Focus only on operational, safety, and economic controls
"""

from modules.heap_leaching.metadata import MODULE_METADATA
from modules.heap_leaching.config import HeapLeachingConfig
from modules.heap_leaching.router import router

__all__ = ["MODULE_METADATA", "HeapLeachingConfig", "router"]
