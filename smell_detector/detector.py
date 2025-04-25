"""
Code Smell Detection Module for RefactAI.

This module provides functionality to detect various code smells in Java classes
using rule-based analysis. It is designed to be modular and replaceable with
more sophisticated static analysis tools in the future.
"""

import logging
from typing import Dict, List, Any, Tuple, Set
from dataclasses import dataclass
import re

# Configure logger
logger = logging.getLogger(__name__)

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

def detect_smells(classes: List[Dict]) -> Dict:
    """
    Detect code smells in Java classes.
    Args:
        classes: List of dictionaries containing class information
                Each dict should have 'class_name' and 'content' keys
    Returns:
        Dictionary mapping class names to detected smells and metrics
    """
    results = {}
    
    try:
        for class_data in classes:
            class_name = class_data.get('class_name', '')
            content = class_data.get('content', '')
            
            if not class_name or not content:
                continue
            
            # Initialize results structure
            results[class_name] = {
                'smells': [],
                'metrics': {},
                'reasoning': {},
                'metrics_evidence': {}
            }
            
            # Calculate basic metrics
            metrics = compute_metrics(class_data)
            results[class_name]['metrics'] = metrics
            
            # Check for God Class
            if metrics['wmc'] > 20 and metrics['loc'] > 200:
                results[class_name]['smells'].append('God Class')
                results[class_name]['reasoning']['God Class'] = 'High complexity and large size'
                results[class_name]['metrics_evidence']['God Class'] = f"WMC = {metrics['wmc']} > 20, LOC = {metrics['loc']} > 200"
            
            # Check for Data Class
            if metrics['getters_setters'] / max(metrics['total_methods'], 1) > 0.7:
                results[class_name]['smells'].append('Data Class')
                results[class_name]['reasoning']['Data Class'] = 'Contains mostly getters and setters'
                results[class_name]['metrics_evidence']['Data Class'] = f"Getter/Setter ratio = {metrics['getters_setters']}/{metrics['total_methods']}"
            
            # Check for Lazy Class
            if metrics['wmc'] < 3 and metrics['loc'] < 50:
                results[class_name]['smells'].append('Lazy Class')
                results[class_name]['reasoning']['Lazy Class'] = 'Low complexity and small size'
                results[class_name]['metrics_evidence']['Lazy Class'] = f"WMC = {metrics['wmc']} < 3, LOC = {metrics['loc']} < 50"
            
            # Check for Feature Envy
            if metrics['external_method_calls'] > metrics['internal_method_calls'] * 2:
                results[class_name]['smells'].append('Feature Envy')
                results[class_name]['reasoning']['Feature Envy'] = 'High external coupling'
                results[class_name]['metrics_evidence']['Feature Envy'] = f"External calls = {metrics['external_method_calls']} > 2 * Internal calls = {metrics['internal_method_calls']}"
            
            # Check for Refused Bequest
            if metrics['inherited_methods'] > 0 and metrics['overridden_methods'] / metrics['inherited_methods'] < 0.3:
                results[class_name]['smells'].append('Refused Bequest')
                results[class_name]['reasoning']['Refused Bequest'] = 'Low usage of inherited methods'
                results[class_name]['metrics_evidence']['Refused Bequest'] = f"Overridden/Inherited ratio = {metrics['overridden_methods']}/{metrics['inherited_methods']}"
    
    except Exception as e:
        logger.error(f"Error in detect_smells: {str(e)}")
        # Return empty results for the failed class
        if class_name:
            results[class_name] = {
                'smells': [],
                'metrics': compute_metrics(content) if content else {},
                'reasoning': {},
                'metrics_evidence': {},
                'error': str(e)
            }
    
    return results

def compute_metrics(content: str) -> Dict[str, int]:
    """
    Compute various metrics for a Java class.
    Args:
        content: String containing Java class code
    Returns:
        Dictionary of computed metrics
    """
    try:
        # Initialize metrics
        metrics = {
            'loc': 0,                    # Lines of code
            'wmc': 0,                    # Weighted methods per class
            'total_methods': 0,          # Total number of methods
            'public_methods': 0,         # Number of public methods
            'private_methods': 0,        # Number of private methods
            'getters_setters': 0,        # Number of getters and setters
            'external_method_calls': 0,  # Calls to external methods
            'internal_method_calls': 0,  # Calls to internal methods
            'inherited_methods': 0,      # Number of inherited methods
            'overridden_methods': 0,     # Number of overridden methods
            'used_methods': 0            # Number of used inherited methods
        }
        
        # Count lines of code (excluding comments and blank lines)
        lines = content.split('\n')
        metrics['loc'] = len([line for line in lines if line.strip() and not line.strip().startswith('//')])
        
        # Count methods
        method_pattern = r'(?:public|private|protected)\s+(?:static\s+)?[\w\<\>\[\]]+\s+(\w+)\s*\([^\)]*\)\s*(?:throws\s+[\w\s,]+\s*)?{'
        methods = re.finditer(method_pattern, content)
        
        for method in methods:
            metrics['total_methods'] += 1
            method_name = method.group(1)
            
            # Check method visibility
            if 'public' in method.group(0):
                metrics['public_methods'] += 1
            elif 'private' in method.group(0):
                metrics['private_methods'] += 1
            
            # Check for getters and setters
            if method_name.startswith('get') or method_name.startswith('set'):
                metrics['getters_setters'] += 1
        
        # Calculate WMC (using cyclomatic complexity)
        metrics['wmc'] = len(re.findall(r'\b(if|for|while|case)\b', content))
        
        # Count method calls
        method_calls = re.findall(r'(\w+)\s*\([^\)]*\)', content)
        internal_methods = set(re.findall(method_pattern, content))
        
        for call in method_calls:
            if call in internal_methods:
                metrics['internal_method_calls'] += 1
            else:
                metrics['external_method_calls'] += 1
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error computing metrics: {str(e)}")
        return {
            'loc': 0,
            'wmc': 0,
            'total_methods': 0,
            'public_methods': 0,
            'private_methods': 0,
            'getters_setters': 0,
            'external_method_calls': 0,
            'internal_method_calls': 0,
            'inherited_methods': 0,
            'overridden_methods': 0,
            'used_methods': 0
        } 