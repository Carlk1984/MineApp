"""
Heap Leaching – Key Controls Module Metadata

Defines the module purpose, scope, and constraints for registration
within the Klusetic Mining SaaS platform.
"""

from typing import Dict, List, Any
from enum import Enum


class ModuleType(str, Enum):
    """Module classification types."""
    ENGINEERING_CONTROL = "engineering_control"
    REPORTING = "reporting"
    ANALYTICS = "analytics"


class LogicType(str, Enum):
    """Logic implementation types."""
    RULE_BASED = "rule_based"
    AI_INFERENCE = "ai_inference"
    HYBRID = "hybrid"


MODULE_METADATA: Dict[str, Any] = {
    "module_id": "heap_leaching_key_controls",
    "name": "Heap Leaching – Key Controls",
    "version": "0.1.0",
    "status": "registered",
    
    "classification": {
        "type": ModuleType.ENGINEERING_CONTROL.value,
        "logic_type": LogicType.RULE_BASED.value,
        "is_deterministic": True,
    },
    
    "purpose": (
        "Engineering control module for gold heap leaching operations. "
        "Provides rule-based, deterministic controls for operational, safety, "
        "and economic aspects of heap leaching processes."
    ),
    
    "scope": {
        "operation_type": "gold_heap_leaching",
        "process_stage": "leaching_only",
        "heap_configuration": "single_heap_per_instance",
        "target_heap_size_tonnes": 1000,
        "platform": "klusetic_mining_saas",
    },
    
    "design_constraints": {
        "rule_based_only": True,
        "no_ai_inference": True,
        "no_prediction": True,
        "no_optimisation": True,
        "no_dashboards": True,
        "no_ui": True,
    },
    
    "excluded_functionality": [
        "mining",
        "stacking",
        "crushing",
        "haulage",
    ],
    
    "control_focus_areas": [
        "operational_controls",
        "safety_controls",
        "economic_controls",
    ],
    
    "engineering_assumptions": {
        "ore_type": "oxide_gold",
        "recovery_method": "solution_based_pls_reporting",
        "gold_recovery_formula": "pls_volume * pls_grade",
        "defaults_editable": True,
    },
    
    "data_state": {
        "accepts_configuration": True,
        "has_operational_data": False,
        "data_models_defined": False,
    },
    
    "dependencies": [],
    
    "api_prefix": "/api/v1/modules/heap-leaching",
}


def get_module_summary() -> Dict[str, Any]:
    """Return a summary of the module for registration purposes."""
    return {
        "module_id": MODULE_METADATA["module_id"],
        "name": MODULE_METADATA["name"],
        "version": MODULE_METADATA["version"],
        "status": MODULE_METADATA["status"],
        "type": MODULE_METADATA["classification"]["type"],
        "purpose": MODULE_METADATA["purpose"],
        "accepts_configuration": MODULE_METADATA["data_state"]["accepts_configuration"],
        "has_operational_data": MODULE_METADATA["data_state"]["has_operational_data"],
    }
