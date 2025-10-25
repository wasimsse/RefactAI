"""
Code Smell Detection Module for RefactAI.

This module provides functionality to detect various code smells in Java classes
using rule-based analysis. It is designed to be modular and replaceable with
more sophisticated static analysis tools in the future.
"""

from typing import Dict, List, Any, Tuple, Set
from dataclasses import dataclass
import re

# Thresholds for various metrics
THRESHOLDS = {
    "god_class": {
        "loc": 500,  # Lines of code
        "wmc": 47,   # Weighted Method Count
        "atfd": 5,   # Access to Foreign Data
        "tcc": 0.3,  # Tight Class Cohesion (lower is worse)
        "lcom": 0.8  # Lack of Cohesion of Methods (higher is worse)
    },
    "data_class": {
        "accessor_ratio": 0.8,  # Ratio of getters/setters to total methods
        "public_fields_ratio": 0.3  # Ratio of public fields to total fields
    },
    "lazy_class": {
        "loc": 50,  # Minimum lines of code
        "wmc": 10,  # Minimum weighted method count
        "public_methods": 3  # Minimum public methods
    },
    "feature_envy": {
        "atfd": 5,  # Access to Foreign Data
        "laa": 0.33  # Locality of Attribute Accesses
    },
    "refused_bequest": {
        "inherited_methods_used": 0.33,  # Ratio of used inherited methods
        "override_ratio": 0.5  # Ratio of overridden methods
    }
}

@dataclass
class ClassMetrics:
    """Holds computed metrics for a Java class."""
    loc: int = 0
    wmc: int = 0
    atfd: int = 0
    tcc: float = 0.0
    lcom: float = 0.0
    public_methods: int = 0
    total_methods: int = 0
    accessor_methods: int = 0
    public_fields: int = 0
    total_fields: int = 0
    inherited_methods: int = 0
    used_inherited_methods: int = 0
    overridden_methods: int = 0
    foreign_data_accesses: int = 0
    local_attribute_accesses: int = 0

def compute_metrics(class_data: Dict[str, Any]) -> ClassMetrics:
    """
    Compute various metrics for a Java class.
    
    Args:
        class_data: Dictionary containing class information and content
        
    Returns:
        ClassMetrics object with computed metrics
    """
    metrics = ClassMetrics()
    content = class_data["content"]
    
    # Basic metrics
    metrics.loc = len(content.splitlines())
    
    # Method-related metrics
    method_pattern = r"(?:public|private|protected)\s+(?:static\s+)?[\w<>[\],\s]+\s+(\w+)\s*\([^)]*\)\s*\{"
    methods = re.finditer(method_pattern, content)
    metrics.total_methods = len(list(methods))
    
    public_method_pattern = r"public\s+(?:static\s+)?[\w<>[\],\s]+\s+(\w+)\s*\([^)]*\)\s*\{"
    public_methods = re.finditer(public_method_pattern, content)
    metrics.public_methods = len(list(public_methods))
    
    # Accessor methods (getters/setters)
    accessor_pattern = r"public\s+[\w<>[\],\s]+\s+(get|set)\w+\s*\([^)]*\)\s*\{"
    accessors = re.finditer(accessor_pattern, content)
    metrics.accessor_methods = len(list(accessors))
    
    # Field-related metrics
    field_pattern = r"(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?[\w<>[\],\s]+\s+\w+\s*;"
    fields = re.finditer(field_pattern, content)
    metrics.total_fields = len(list(fields))
    
    public_field_pattern = r"public\s+(?:static\s+)?(?:final\s+)?[\w<>[\],\s]+\s+\w+\s*;"
    public_fields = re.finditer(public_field_pattern, content)
    metrics.public_fields = len(list(public_fields))
    
    # Inheritance metrics (if available)
    if "inheritance_data" in class_data:
        inh_data = class_data["inheritance_data"]
        metrics.inherited_methods = inh_data.get("inherited_methods", 0)
        metrics.used_inherited_methods = inh_data.get("used_methods", 0)
        metrics.overridden_methods = inh_data.get("overridden_methods", 0)
    
    # TODO: Implement more sophisticated metric calculations using AST parsing
    # For now, use simplified calculations
    metrics.wmc = metrics.total_methods * 2  # Simplified WMC calculation
    metrics.atfd = metrics.foreign_data_accesses
    metrics.tcc = 0.5  # Placeholder
    metrics.lcom = 0.5  # Placeholder
    
    return metrics

def is_god_class(metrics: ClassMetrics) -> Tuple[bool, str]:
    """Check if a class exhibits God Class characteristics."""
    reasons = []
    
    if metrics.loc > THRESHOLDS["god_class"]["loc"]:
        reasons.append(f"High LOC ({metrics.loc} > {THRESHOLDS['god_class']['loc']})")
    
    if metrics.wmc > THRESHOLDS["god_class"]["wmc"]:
        reasons.append(f"High complexity (WMC: {metrics.wmc} > {THRESHOLDS['god_class']['wmc']})")
    
    if metrics.lcom > THRESHOLDS["god_class"]["lcom"]:
        reasons.append(f"Low cohesion (LCOM: {metrics.lcom:.2f} > {THRESHOLDS['god_class']['lcom']:.2f})")
    
    is_god = len(reasons) >= 2  # Consider it a God Class if it meets at least 2 criteria
    reasoning = " AND ".join(reasons) if reasons else "No God Class indicators found"
    
    return is_god, reasoning

def is_data_class(metrics: ClassMetrics) -> Tuple[bool, str]:
    """Check if a class is a Data Class."""
    reasons = []
    
    if metrics.total_methods > 0:
        accessor_ratio = metrics.accessor_methods / metrics.total_methods
        if accessor_ratio > THRESHOLDS["data_class"]["accessor_ratio"]:
            reasons.append(f"High accessor ratio ({accessor_ratio:.2f} > {THRESHOLDS['data_class']['accessor_ratio']:.2f})")
    
    if metrics.total_fields > 0:
        public_fields_ratio = metrics.public_fields / metrics.total_fields
        if public_fields_ratio > THRESHOLDS["data_class"]["public_fields_ratio"]:
            reasons.append(f"High public fields ratio ({public_fields_ratio:.2f} > {THRESHOLDS['data_class']['public_fields_ratio']:.2f})")
    
    is_data = len(reasons) >= 1
    reasoning = " AND ".join(reasons) if reasons else "No Data Class indicators found"
    
    return is_data, reasoning

def is_lazy_class(metrics: ClassMetrics) -> Tuple[bool, str]:
    """Check if a class is a Lazy Class."""
    reasons = []
    
    if metrics.loc < THRESHOLDS["lazy_class"]["loc"]:
        reasons.append(f"Low LOC ({metrics.loc} < {THRESHOLDS['lazy_class']['loc']})")
    
    if metrics.wmc < THRESHOLDS["lazy_class"]["wmc"]:
        reasons.append(f"Low complexity (WMC: {metrics.wmc} < {THRESHOLDS['lazy_class']['wmc']})")
    
    if metrics.public_methods < THRESHOLDS["lazy_class"]["public_methods"]:
        reasons.append(f"Few public methods ({metrics.public_methods} < {THRESHOLDS['lazy_class']['public_methods']})")
    
    is_lazy = len(reasons) >= 2
    reasoning = " AND ".join(reasons) if reasons else "No Lazy Class indicators found"
    
    return is_lazy, reasoning

def is_feature_envy(metrics: ClassMetrics) -> Tuple[bool, str]:
    """Check if a class exhibits Feature Envy."""
    # TODO: Implement proper feature envy detection using AST analysis
    # Current implementation is a placeholder
    return False, "Feature Envy detection requires AST analysis"

def is_refused_bequest(metrics: ClassMetrics) -> Tuple[bool, str]:
    """Check if a class exhibits Refused Bequest."""
    reasons = []
    
    if metrics.inherited_methods > 0:
        used_ratio = metrics.used_inherited_methods / metrics.inherited_methods
        if used_ratio < THRESHOLDS["refused_bequest"]["inherited_methods_used"]:
            reasons.append(f"Low usage of inherited methods ({used_ratio:.2f} < {THRESHOLDS['refused_bequest']['inherited_methods_used']:.2f})")
    
    if metrics.overridden_methods > 0:
        override_ratio = metrics.overridden_methods / metrics.inherited_methods
        if override_ratio > THRESHOLDS["refused_bequest"]["override_ratio"]:
            reasons.append(f"High override ratio ({override_ratio:.2f} > {THRESHOLDS['refused_bequest']['override_ratio']:.2f})")
    
    is_refused = len(reasons) >= 1 and metrics.inherited_methods > 0
    reasoning = " AND ".join(reasons) if reasons else "No Refused Bequest indicators found"
    
    return is_refused, reasoning

def detect_smells(classes: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Detect code smells in Java classes.
    
    Args:
        classes: List of dictionaries containing class information
        
    Returns:
        Dictionary mapping class names to detected smells and reasoning
    """
    results = {}
    
    for class_data in classes:
        class_name = class_data["class_name"]
        metrics = compute_metrics(class_data)
        
        # Initialize results for this class
        results[class_name] = {
            "smells": [],
            "reasoning": {},
            "metrics": {
                "loc": metrics.loc,
                "wmc": metrics.wmc,
                "public_methods": metrics.public_methods,
                "total_methods": metrics.total_methods,
                "accessor_methods": metrics.accessor_methods
            }
        }
        
        # Check for each type of smell
        smell_checks = [
            ("God Class", is_god_class),
            ("Data Class", is_data_class),
            ("Lazy Class", is_lazy_class),
            ("Feature Envy", is_feature_envy),
            ("Refused Bequest", is_refused_bequest)
        ]
        
        for smell_name, check_func in smell_checks:
            is_smell, reasoning = check_func(metrics)
            if is_smell:
                results[class_name]["smells"].append(smell_name)
                results[class_name]["reasoning"][smell_name] = reasoning
        
        # Add placeholder for future smell types
        results[class_name]["future_smells"] = {
            "Inappropriate Intimacy": "Not implemented - requires dependency analysis",
            "Divergent Change": "Not implemented - requires version history analysis",
            "Shotgun Surgery": "Not implemented - requires impact analysis",
            "Speculative Generality": "Not implemented - requires usage analysis",
            "Data Clumps": "Not implemented - requires field usage analysis"
        }
    
    return results 