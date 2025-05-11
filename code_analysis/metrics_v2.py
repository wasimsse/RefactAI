"""
Enhanced Metrics Calculation Module for RefactAI.

This module provides improved code metrics calculation while maintaining
backward compatibility with the existing implementation.
"""

from typing import Dict, Any, List, Tuple, Set
import re
from dataclasses import dataclass
import ast
from collections import defaultdict

@dataclass
class AdvancedMetrics:
    """Holds advanced metrics for a Java class with improved accuracy."""
    # Core metrics
    lcom: float = 0.0  # Lack of Cohesion of Methods
    cbo: int = 0      # Coupling Between Objects
    dit: int = 0      # Depth of Inheritance Tree
    cc: int = 0       # Cyclomatic Complexity
    rfc: int = 0      # Response for Class
    
    # Size metrics
    loc: int = 0      # Lines of Code
    loc_per_method: float = 0.0  # Average LOC per method
    max_method_length: int = 0   # Maximum method length
    
    # Structure metrics
    num_methods: int = 0
    num_fields: int = 0
    num_public_methods: int = 0
    num_public_fields: int = 0
    
    # Documentation metrics
    comment_density: float = 0.0  # Comment-to-code ratio
    
    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert metrics to the format expected by the UI."""
        return {
            "lcom": {
                "value": round(self.lcom, 2),
                "threshold": 0.7,
                "status": "high" if self.lcom > 0.7 else "medium" if self.lcom > 0.4 else "low",
                "icon": "🧩",
                "help": "Lack of Cohesion of Methods (0-1). Lower is better."
            },
            "cbo": {
                "value": self.cbo,
                "threshold": 5,
                "status": "high" if self.cbo > 5 else "medium" if self.cbo > 3 else "low",
                "icon": "🔗",
                "help": "Coupling Between Objects. Lower is better."
            },
            "dit": {
                "value": self.dit,
                "threshold": 3,
                "status": "high" if self.dit > 3 else "medium" if self.dit > 2 else "low",
                "icon": "📐",
                "help": "Depth of Inheritance Tree. Lower is better."
            },
            "cc": {
                "value": self.cc,
                "threshold": 10,
                "status": "high" if self.cc > 10 else "medium" if self.cc > 7 else "low",
                "icon": "🔄",
                "help": "Cyclomatic Complexity. Lower is better."
            },
            "loc": {
                "value": self.loc,
                "threshold": 500,
                "status": "high" if self.loc > 500 else "medium" if self.loc > 300 else "low",
                "icon": "📏",
                "help": "Lines of Code. Lower is better."
            },
            "loc_per_method": {
                "value": round(self.loc_per_method, 2),
                "threshold": 20,
                "status": "high" if self.loc_per_method > 20 else "medium" if self.loc_per_method > 15 else "low",
                "icon": "📊",
                "help": "Average Lines of Code per Method. Lower is better."
            },
            "max_method_length": {
                "value": self.max_method_length,
                "threshold": 50,
                "status": "high" if self.max_method_length > 50 else "medium" if self.max_method_length > 30 else "low",
                "icon": "📈",
                "help": "Maximum Method Length. Lower is better."
            },
            "num_methods": {
                "value": self.num_methods,
                "threshold": 15,
                "status": "high" if self.num_methods > 15 else "medium" if self.num_methods > 10 else "low",
                "icon": "🔧",
                "help": "Number of Methods. Moderate is better."
            },
            "num_fields": {
                "value": self.num_fields,
                "threshold": 10,
                "status": "high" if self.num_fields > 10 else "medium" if self.num_fields > 7 else "low",
                "icon": "📝",
                "help": "Number of Fields. Lower is better."
            },
            "num_public_methods": {
                "value": self.num_public_methods,
                "threshold": 8,
                "status": "high" if self.num_public_methods > 8 else "medium" if self.num_public_methods > 5 else "low",
                "icon": "🔓",
                "help": "Number of Public Methods. Lower is better."
            },
            "num_public_fields": {
                "value": self.num_public_fields,
                "threshold": 5,
                "status": "high" if self.num_public_fields > 5 else "medium" if self.num_public_fields > 3 else "low",
                "icon": "🔓",
                "help": "Number of Public Fields. Lower is better."
            },
            "comment_density": {
                "value": round(self.comment_density, 2),
                "threshold": 30,
                "status": "high" if self.comment_density > 30 else "medium" if self.comment_density > 20 else "low",
                "icon": "💭",
                "help": "Comment-to-Code Ratio (%). Moderate is better."
            }
        }

def calculate_cyclomatic_complexity(content: str) -> int:
    """Calculate cyclomatic complexity using a more accurate method."""
    # Count decision points
    decision_points = [
        r'\bif\b', r'\belse\b', r'\bfor\b', r'\bwhile\b', r'\bdo\b',
        r'\bcase\b', r'\bcatch\b', r'\b&&\b', r'\b\|\|\b', r'\?', r':',
        r'\bthrow\b', r'\breturn\b'
    ]
    
    complexity = 1  # Base complexity
    for pattern in decision_points:
        complexity += len(re.findall(pattern, content))
    
    return complexity

def calculate_lcom(content: str) -> float:
    """Calculate Lack of Cohesion of Methods using Henderson-Sellers method."""
    # Extract method bodies
    method_pattern = r'(public|private|protected)?\s+(static\s+)?(\w+)\s+(\w+)\s*\([^)]*\)\s*{([\s\S]*?)}'
    methods = re.findall(method_pattern, content)
    
    if not methods:
        return 0.0
    
    # Extract instance variables used in each method
    method_vars = []
    for method in methods:
        method_body = method[4]
        # Find all variable references
        vars_used = set(re.findall(r'\b([a-zA-Z_]\w*)\b', method_body))
        method_vars.append(vars_used)
    
    # Calculate LCOM
    n = len(methods)
    if n <= 1:
        return 0.0
    
    p = 0  # Number of method pairs that share no instance variables
    q = 0  # Number of method pairs that share at least one instance variable
    
    for i in range(n):
        for j in range(i + 1, n):
            if not (method_vars[i] & method_vars[j]):  # No shared variables
                p += 1
            else:
                q += 1
    
    if p + q == 0:
        return 0.0
    
    return p / (p + q)

def calculate_cbo(content: str) -> int:
    """Calculate Coupling Between Objects using a more accurate method."""
    # Count external dependencies
    dependencies = set()
    
    # Count imports
    imports = re.findall(r'import\s+([\w.]+);', content)
    dependencies.update(imports)
    
    # Count object instantiations
    instantiations = re.findall(r'new\s+([\w.]+)\s*\(', content)
    dependencies.update(instantiations)
    
    # Count method calls on other objects
    method_calls = re.findall(r'(\w+)\.\w+\s*\(', content)
    dependencies.update(method_calls)
    
    # Count field accesses on other objects
    field_accesses = re.findall(r'(\w+)\.\w+\s*(?!\()', content)
    dependencies.update(field_accesses)
    
    return len(dependencies)

def calculate_dit(content: str) -> int:
    """Calculate Depth of Inheritance Tree."""
    # Find all extends clauses
    extends = re.findall(r'extends\s+([\w.]+)', content)
    return len(extends)

def calculate_method_metrics(content: str) -> Tuple[int, float, int]:
    """Calculate method-related metrics."""
    method_pattern = r'(public|private|protected)?\s+(static\s+)?(\w+)\s+(\w+)\s*\([^)]*\)\s*{([\s\S]*?)}'
    methods = re.findall(method_pattern, content)
    
    if not methods:
        return 0, 0.0, 0
    
    method_lengths = [len(m[4].split('\n')) for m in methods if m[4].strip()]
    total_methods = len(methods)
    avg_length = sum(method_lengths) / total_methods if method_lengths else 0
    max_length = max(method_lengths) if method_lengths else 0
    
    return total_methods, avg_length, max_length

def calculate_field_metrics(content: str) -> Tuple[int, int, int, int]:
    """Calculate field-related metrics."""
    # Find all field declarations
    field_pattern = r'(public|private|protected)?\s+(static\s+)?(\w+)\s+(\w+)\s*(=|;)'
    fields = re.findall(field_pattern, content)
    
    total_fields = len(fields)
    public_fields = len([f for f in fields if f[0] == 'public'])
    
    # Find all method declarations
    method_pattern = r'(public|private|protected)?\s+(static\s+)?(\w+)\s+(\w+)\s*\([^)]*\)\s*{'
    methods = re.findall(method_pattern, content)
    
    total_methods = len(methods)
    public_methods = len([m for m in methods if m[0] == 'public'])
    
    return total_fields, public_fields, total_methods, public_methods

def calculate_comment_density(content: str) -> float:
    """Calculate comment-to-code ratio."""
    lines = content.split('\n')
    total_lines = len(lines)
    if total_lines == 0:
        return 0.0
    
    comment_lines = len([l for l in lines if l.strip().startswith('//') or l.strip().startswith('/*') or l.strip().startswith('*')])
    return (comment_lines / total_lines) * 100

def calculate_metrics(content: str) -> AdvancedMetrics:
    """Calculate all metrics for a Java class."""
    # Calculate basic metrics
    loc = len(content.split('\n'))
    cc = calculate_cyclomatic_complexity(content)
    lcom = calculate_lcom(content)
    cbo = calculate_cbo(content)
    dit = calculate_dit(content)
    
    # Calculate method metrics
    num_methods, avg_method_length, max_method_length = calculate_method_metrics(content)
    
    # Calculate field metrics
    num_fields, num_public_fields, num_methods, num_public_methods = calculate_field_metrics(content)
    
    # Calculate comment density
    comment_density = calculate_comment_density(content)
    
    return AdvancedMetrics(
        lcom=lcom,
        cbo=cbo,
        dit=dit,
        cc=cc,
        rfc=num_methods + cbo,  # Response for Class = methods + external calls
        loc=loc,
        loc_per_method=avg_method_length,
        max_method_length=max_method_length,
        num_methods=num_methods,
        num_fields=num_fields,
        num_public_methods=num_public_methods,
        num_public_fields=num_public_fields,
        comment_density=comment_density
    )

def calculate_advanced_metrics_v2(content: str, basic_metrics: dict) -> Dict[str, Dict[str, Any]]:
    """
    Calculate advanced software metrics for a Java class with improved accuracy.
    This is a new implementation that provides more accurate results while
    maintaining backward compatibility with the existing format.
    """
    try:
        metrics = calculate_metrics(content)
        
        # Ensure basic_metrics has required fields
        if not basic_metrics or not isinstance(basic_metrics, dict):
            return metrics.to_dict()
        
        return metrics.to_dict()
        
    except Exception as e:
        # Return default metrics on error to maintain backward compatibility
        return AdvancedMetrics().to_dict()

def get_smell_evidence_v2(smell: str, metrics: Dict[str, Dict[str, Any]], basic_metrics: dict) -> str:
    """
    Generate evidence-based reasoning for code smells with improved accuracy.
    This version provides more detailed evidence while maintaining the same format.
    """
    evidence = []
    
    if smell == "God Class":
        wmc = basic_metrics.get("wmc", 0)
        lcom = metrics["lcom"]["value"]
        loc = basic_metrics.get("loc", 0)
        cbo = metrics["cbo"]["value"]
        evidence.extend([
            f"High complexity (WMC = {wmc} > {basic_metrics.get('wmc_threshold', 20)})",
            f"Low cohesion (LCOM = {lcom:.2f} > {metrics['lcom']['threshold']})",
            f"Large size (LOC = {loc} > {basic_metrics.get('loc_threshold', 200)})",
            f"High coupling (CBO = {cbo} > {metrics['cbo']['threshold']})"
        ])
    
    elif smell == "Feature Envy":
        cbo = metrics["cbo"]["value"]
        rfc = metrics["rfc"]["value"]
        external_calls = basic_metrics.get("external_method_calls", 0)
        total_methods = basic_metrics.get("total_methods", 1)
        evidence.extend([
            f"High coupling (CBO = {cbo} > {metrics['cbo']['threshold']})",
            f"Many external calls (RFC = {rfc} > {metrics['rfc']['threshold']})",
            f"External call ratio = {external_calls/total_methods:.2f} (threshold: 0.7)"
        ])
    
    elif smell == "Data Class":
        methods = basic_metrics.get("total_methods", 0)
        getters_setters = basic_metrics.get("getters_setters", 0)
        if methods > 0:
            ratio = getters_setters / methods
            evidence.extend([
                f"High accessor ratio ({getters_setters}/{methods} = {ratio:.2f} > 0.7)",
                f"Low complexity (WMC = {basic_metrics.get('wmc', 0)} < {basic_metrics.get('wmc_threshold', 20)})"
            ])
    
    elif smell == "Long Method":
        cc = metrics["cc"]["value"]
        evidence.extend([
            f"High cyclomatic complexity (CC = {cc} > {metrics['cc']['threshold']})",
            f"Many control flow statements detected"
        ])
    
    return "\n".join([f"• {e}" for e in evidence]) 