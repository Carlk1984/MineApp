"""
Klusetic Mining SaaS Platform - Modules Package

This package contains all registered SaaS modules for the mining platform.
Each module is self-contained with its own metadata, configuration, and API routes.
"""

from typing import Dict, Any

# Module registry - all registered modules are listed here
REGISTERED_MODULES: Dict[str, Any] = {}


def register_module(module_id: str, module_info: Dict[str, Any]) -> None:
    """Register a module in the platform registry."""
    REGISTERED_MODULES[module_id] = module_info


def get_module(module_id: str) -> Dict[str, Any]:
    """Get module information by ID."""
    return REGISTERED_MODULES.get(module_id)


def list_modules() -> Dict[str, Any]:
    """List all registered modules."""
    return REGISTERED_MODULES
