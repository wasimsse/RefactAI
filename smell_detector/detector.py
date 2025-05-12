"""
Code Smell Detection Module for RefactAI.

This module provides functionality to detect various code smells in Java classes
using rule-based analysis. It is designed to be modular and replaceable with
more sophisticated static analysis tools in the future.
"""

from typing import Dict, List, Any, Tuple, Set
from dataclasses import dataclass
import re
from smell_detector.auto_smells import detect_auto_smells

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

def detect_smells(files: List[Dict[str, Any]]) -> Dict[str, Dict]:
    """
    Detect code smells in Java files.
    
    Args:
        files: List of dicts containing class_name, content, and inheritance_data
        
    Returns:
        Dict mapping class names to their smell analysis results
    """
    results = {}
    
    for file_info in files:
        class_name = file_info["class_name"]
        content = file_info["content"]
        inheritance_data = file_info.get("inheritance_data", {})
        
        # Initialize metrics
        metrics = calculate_metrics(content, inheritance_data)
        
        # Detect smells based on metrics
        smells = []
        reasoning = {}
        metrics_evidence = {}
        
        # Long Method Detection
        long_methods = detect_long_methods(content)
        if long_methods:
            smells.append("Long Method")
            reasoning["Long Method"] = "Contains methods that are too long and complex"
            metrics_evidence["Long Method"] = format_method_evidence(long_methods)
        
        # God Class Detection
        if is_god_class(metrics):
            smells.append("God Class")
            reasoning["God Class"] = "Class has too many responsibilities and low cohesion"
            metrics_evidence["God Class"] = format_god_class_evidence(metrics)
        
        # Data Class Detection
        if is_data_class(metrics):
            smells.append("Data Class")
            reasoning["Data Class"] = "Class only contains data and accessors"
            metrics_evidence["Data Class"] = format_data_class_evidence(metrics)
        
        # Feature Envy Detection
        if has_feature_envy(metrics, inheritance_data):
            smells.append("Feature Envy")
            reasoning["Feature Envy"] = "Methods use more features of other classes"
            metrics_evidence["Feature Envy"] = format_feature_envy_evidence(metrics)
        
        # --- Integration: Automatically Detectable Code Smells ---
        # Prepare method metrics for auto_smells
        method_metrics = []
        method_pattern = r'(?:public|private|protected)\s+\w+\s+(\w+)\s*\([^)]*\)\s*\{'
        for match in re.finditer(method_pattern, content):
            method_name = match.group(1)
            method_start = match.start()
            method_end = find_closing_brace(content, method_start)
            method_content = content[method_start:method_end]
            params = re.findall(r'\w+', content[match.start():content.find(')', match.start())])
            method_metrics.append({
                "name": method_name,
                "lines": len(method_content.splitlines()),
                "complexity": calculate_complexity(method_content),
                "params": params
            })
        # Class names for uncommunicative name detection
        class_names = [class_name]
        auto_smells = detect_auto_smells(content, metrics, method_metrics, class_names)
        for smell, detail in auto_smells.items():
            if smell not in smells:
                smells.append(smell)
                reasoning[smell] = detail if isinstance(detail, str) else str(detail)
        
        # Magic Numbers Detection
        if detect_magic_numbers(content):
            smells.append("Magic Numbers")
            reasoning["Magic Numbers"] = "Hardcoded numbers detected."
        
        # Store results
        results[class_name] = {
            "metrics": metrics,
            "smells": smells,
            "reasoning": reasoning,
            "metrics_evidence": metrics_evidence
        }
    
    return results

def calculate_metrics(content: str, inheritance_data: Dict) -> Dict:
    """Calculate code metrics for smell detection."""
    metrics = {
        "loc": len(content.splitlines()),
        "methods": [],
        "total_methods": 0,
        "wmc": 0,  # Weighted Methods per Class
        "getters_setters": 0,
        "external_method_calls": 0,
        "instance_variables": 0
    }
    
    # Method detection
    method_pattern = r'(?:public|private|protected)\s+\w+\s+(\w+)\s*\([^)]*\)\s*\{'
    for match in re.finditer(method_pattern, content):
        method_name = match.group(1)
        method_start = match.start()
        method_end = find_closing_brace(content, method_start)
        method_content = content[method_start:method_end]
        
        # Calculate method metrics
        method_metrics = {
            "name": method_name,
            "length": len(method_content.splitlines()),
            "complexity": calculate_complexity(method_content)
        }
        metrics["methods"].append(method_metrics)
        metrics["wmc"] += method_metrics["complexity"]
    
    metrics["total_methods"] = len(metrics["methods"])
    
    # Count getters and setters
    getter_setter_pattern = r'(?:public|private|protected)\s+\w+\s+(get|set)\w+\s*\('
    metrics["getters_setters"] = len(re.findall(getter_setter_pattern, content))
    
    # Count instance variables
    instance_var_pattern = r'(?:private|protected)\s+\w+\s+\w+\s*;'
    metrics["instance_variables"] = len(re.findall(instance_var_pattern, content))
    
    # Count external method calls
    external_call_pattern = r'\w+\.\w+\('
    metrics["external_method_calls"] = len(re.findall(external_call_pattern, content))
    
    return metrics

def find_closing_brace(content: str, start_pos: int) -> int:
    """Find the position of the closing brace that matches the opening brace."""
    brace_count = 1
    pos = content.find('{', start_pos) + 1
    
    while brace_count > 0 and pos < len(content):
        if content[pos] == '{':
            brace_count += 1
        elif content[pos] == '}':
            brace_count -= 1
        pos += 1
    
    return pos

def calculate_complexity(method_content: str) -> int:
    """Calculate cyclomatic complexity of a method."""
    complexity = 1  # Base complexity
    
    # Count control flow statements
    control_patterns = [
        r'\bif\b',
        r'\belse\s+if\b',
        r'\bfor\b',
        r'\bwhile\b',
        r'\bcase\b',
        r'\bcatch\b'
    ]
    
    for pattern in control_patterns:
        complexity += len(re.findall(pattern, method_content))
    
    return complexity

def detect_long_methods(content: str) -> List[Dict]:
    """Detect long methods in the code."""
    long_methods = []
    method_pattern = r'(?:public|private|protected)\s+\w+\s+(\w+)\s*\([^)]*\)\s*\{'
    
    for match in re.finditer(method_pattern, content):
        method_name = match.group(1)
        method_start = match.start()
        method_end = find_closing_brace(content, method_start)
        method_content = content[method_start:method_end]
        
        lines = len(method_content.splitlines())
        complexity = calculate_complexity(method_content)
        
        if lines > 30 or complexity > 10:
            long_methods.append({
                "name": method_name,
                "lines": lines,
                "complexity": complexity
            })
    
    return long_methods

def is_god_class(metrics: Dict) -> bool:
    """Detect if a class is a God Class."""
    return (
        metrics["wmc"] > 47 or  # High complexity
        metrics["total_methods"] > 15 or  # Too many methods
        metrics["loc"] > 300  # Too many lines
    )

def is_data_class(metrics: Dict) -> bool:
    """Detect if a class is a Data Class."""
    if metrics["total_methods"] == 0:
        return False
    
    getter_setter_ratio = metrics["getters_setters"] / metrics["total_methods"]
    return (
        getter_setter_ratio > 0.7 and  # Mostly getters and setters
        metrics["instance_variables"] > 0  # Has instance variables
    )

def has_feature_envy(metrics: Dict, inheritance_data: Dict) -> bool:
    """Detect Feature Envy smell."""
    if metrics["total_methods"] == 0:
        return False
    
    external_calls_ratio = metrics["external_method_calls"] / metrics["total_methods"]
    return (
        external_calls_ratio > 4 and  # Many external calls
        inheritance_data.get("used_methods", 0) > inheritance_data.get("inherited_methods", 0)  # Uses more than inherits
    )

def format_method_evidence(long_methods: List[Dict]) -> str:
    """Format evidence for long methods."""
    evidence = []
    for method in long_methods:
        evidence.append(
            f"Method '{method['name']}' has {method['lines']} lines "
            f"and complexity of {method['complexity']}"
        )
    return "\n".join(evidence)

def format_god_class_evidence(metrics: Dict) -> str:
    """Format evidence for God Class detection."""
    return (
        f"WMC = {metrics['wmc']} (threshold: 47)\n"
        f"Total Methods = {metrics['total_methods']} (threshold: 15)\n"
        f"LOC = {metrics['loc']} (threshold: 300)"
    )

def format_data_class_evidence(metrics: Dict) -> str:
    """Format evidence for Data Class detection."""
    ratio = metrics["getters_setters"] / metrics["total_methods"] if metrics["total_methods"] > 0 else 0
    return (
        f"Getter/Setter Ratio = {ratio:.2f} (threshold: 0.7)\n"
        f"Instance Variables = {metrics['instance_variables']}"
    )

def format_feature_envy_evidence(metrics: Dict) -> str:
    """Format evidence for Feature Envy detection."""
    ratio = metrics["external_method_calls"] / metrics["total_methods"] if metrics["total_methods"] > 0 else 0
    return (
        f"External Calls Ratio = {ratio:.2f} (threshold: 4.0)\n"
        f"External Method Calls = {metrics['external_method_calls']}"
    )

def detect_magic_numbers(content: str) -> bool:
    return bool(re.search(r'[^\\w]([0-9]{2,})[^\\w]', content)) 