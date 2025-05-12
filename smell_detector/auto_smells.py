"""
Automatically Detectable Code Smells for RefactAI

This module provides modular detection functions for common code smells that can be detected via static analysis and code metrics.
"""

import re
from typing import List, Dict, Any

# Thresholds for various smells (can be tuned)
THRESHOLDS = {
    "god_class": {"loc": 500, "wmc": 47, "methods": 15, "fields": 15},
    "large_class": {"loc": 500, "methods": 15, "fields": 15},
    "long_method": {"lines": 30, "complexity": 10},
    "complex_class": {"wmc": 47, "branches": 30},
    "too_many_fields": 15,
    "too_many_methods": 15,
    "long_parameter_list": 5,
    "large_constructor": {"lines": 20, "params": 5},
    "duplicate_code": 3,  # lines
    "lazy_class": {"loc": 50, "methods": 3},
    "feature_envy": 4,
    "data_class": {"accessor_ratio": 0.7},
    "middle_man": 0.5,
    "inappropriate_intimacy": 3,
    "message_chains": 3,
    "data_clumps": 3,
    "switch_statements": 1,
    "conditional_complexity": 5,
    "control_flag": 1,
    "refused_bequest": 0.33,
    "uncommunicative_name": 2,
    "magic_number": 2,
    "primitive_obsession": 3,
    "temporary_field": 1,
    "excessive_getters_setters": 0.7,
    "excessive_static_methods": 0.7,
}

def detect_god_class(metrics: Dict) -> bool:
    return (
        metrics.get("loc", 0) > THRESHOLDS["god_class"]["loc"] or
        metrics.get("wmc", 0) > THRESHOLDS["god_class"]["wmc"] or
        metrics.get("total_methods", 0) > THRESHOLDS["god_class"]["methods"]
    )

def detect_large_class(metrics: Dict) -> bool:
    return (
        metrics.get("loc", 0) > THRESHOLDS["large_class"]["loc"] or
        metrics.get("total_methods", 0) > THRESHOLDS["large_class"]["methods"] or
        metrics.get("total_fields", 0) > THRESHOLDS["large_class"]["fields"]
    )

def detect_long_method(method: Dict) -> bool:
    return (
        method.get("lines", 0) > THRESHOLDS["long_method"]["lines"] or
        method.get("complexity", 0) > THRESHOLDS["long_method"]["complexity"]
    )

def detect_complex_class(metrics: Dict) -> bool:
    return (
        metrics.get("wmc", 0) > THRESHOLDS["complex_class"]["wmc"] or
        metrics.get("branches", 0) > THRESHOLDS["complex_class"]["branches"]
    )

def detect_too_many_fields(metrics: Dict) -> bool:
    return metrics.get("total_fields", 0) > THRESHOLDS["too_many_fields"]

def detect_too_many_methods(metrics: Dict) -> bool:
    return metrics.get("total_methods", 0) > THRESHOLDS["too_many_methods"]

def detect_long_parameter_list(method: Dict) -> bool:
    return len(method.get("params", [])) > THRESHOLDS["long_parameter_list"]

def detect_large_constructor(method: Dict) -> bool:
    return (
        method.get("lines", 0) > THRESHOLDS["large_constructor"]["lines"] or
        len(method.get("params", [])) > THRESHOLDS["large_constructor"]["params"]
    )

def detect_duplicate_code(content: str) -> list:
    # Find blocks of 3+ consecutive duplicate lines
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    seen = {}
    duplicates = []
    for i in range(len(lines) - 2):
        block = '\n'.join(lines[i:i+3])
        if block in seen:
            duplicates.append((i, block))
        else:
            seen[block] = i
    return duplicates

def detect_lazy_class(metrics: Dict) -> bool:
    return (
        metrics.get("loc", 0) < THRESHOLDS["lazy_class"]["loc"] and
        metrics.get("total_methods", 0) < THRESHOLDS["lazy_class"]["methods"]
    )

def detect_feature_envy(metrics: Dict) -> bool:
    return metrics.get("external_method_calls", 0) > THRESHOLDS["feature_envy"]

def detect_data_class(metrics: Dict) -> bool:
    if metrics.get("total_methods", 0) == 0:
        return False
    ratio = metrics.get("getters_setters", 0) / metrics.get("total_methods", 1)
    return ratio > THRESHOLDS["data_class"]["accessor_ratio"]

def detect_middle_man(metrics: Dict) -> bool:
    # Placeholder: needs delegation analysis
    return False

def detect_inappropriate_intimacy(metrics: Dict) -> bool:
    # Placeholder: needs field access analysis
    return False

def detect_message_chains(content: str) -> bool:
    return len(re.findall(r'\w+\.\w+\.\w+', content)) > THRESHOLDS["message_chains"]

def detect_data_clumps(content: str) -> bool:
    # Placeholder: needs parameter grouping analysis
    return False

def detect_switch_statements(content: str) -> bool:
    return len(re.findall(r'switch\s*\(', content)) >= THRESHOLDS["switch_statements"]

def detect_conditional_complexity(content: str) -> bool:
    return len(re.findall(r'if\s*\(|else if\s*\(|for\s*\(|while\s*\(', content)) > THRESHOLDS["conditional_complexity"]

def detect_control_flag(content: str) -> bool:
    # Placeholder: needs control flag variable analysis
    return False

def detect_refused_bequest(metrics: Dict) -> bool:
    # Placeholder: needs inheritance usage analysis
    return False

def detect_uncommunicative_name(names: List[str]) -> bool:
    return any(len(n) < THRESHOLDS["uncommunicative_name"] for n in names)

def detect_magic_numbers(content: str) -> list:
    # Ignore common values like 0, 1, -1
    matches = re.findall(r'[^\w](-?\d+)[^\w]', content)
    return [m for m in matches if m not in ('0', '1', '-1')]

def detect_primitive_obsession(content: str) -> bool:
    # Placeholder: needs type usage analysis
    return False

def detect_temporary_field(content: str) -> bool:
    # Placeholder: needs field usage analysis
    return False

def detect_excessive_getters_setters(metrics: Dict) -> bool:
    if metrics.get("total_methods", 0) == 0:
        return False
    ratio = metrics.get("getters_setters", 0) / metrics.get("total_methods", 1)
    return ratio > THRESHOLDS["excessive_getters_setters"]

def detect_excessive_static_methods(content: str) -> bool:
    static_methods = len(re.findall(r'static\s+[\w<>\[\],\s]+\s+\w+\s*\(', content))
    total_methods = len(re.findall(r'(?:public|private|protected)\s+[\w<>\[\],\s]+\s+\w+\s*\(', content))
    if total_methods == 0:
        return False
    return static_methods / total_methods > THRESHOLDS["excessive_static_methods"]

def detect_auto_smells(content: str, metrics: Dict, method_metrics: List[Dict], class_names: List[str]) -> Dict[str, Any]:
    """
    Run all automatically detectable code smell detectors and return a dict of detected smells.
    """
    smells = {}
    if detect_god_class(metrics):
        smells["God Class"] = {
            "reason": f"LOC={metrics.get('loc', 0)}, WMC={metrics.get('wmc', 0)}, Methods={metrics.get('total_methods', 0)}",
            "severity": "High"
        }
    if detect_large_class(metrics):
        smells["Large Class"] = {
            "reason": f"LOC={metrics.get('loc', 0)}, Methods={metrics.get('total_methods', 0)}, Fields={metrics.get('total_fields', 0)}",
            "severity": "Medium"
        }
    for m in method_metrics:
        if detect_long_method(m):
            smells.setdefault("Long Method", []).append({
                "name": m["name"],
                "lines": m["lines"],
                "complexity": m["complexity"],
                "severity": "High",
                "reason": f"Method '{m['name']}' has {m['lines']} lines and complexity {m['complexity']}"
            })
    if detect_complex_class(metrics):
        smells["Complex Class"] = "Class has high complexity or many branches."
    if detect_too_many_fields(metrics):
        smells["Too Many Fields"] = "Class has too many fields."
    if detect_too_many_methods(metrics):
        smells["Too Many Methods"] = "Class has too many methods."
    for m in method_metrics:
        if detect_long_parameter_list(m):
            smells.setdefault("Long Parameter List", []).append(m["name"])
    for m in method_metrics:
        if detect_large_constructor(m):
            smells.setdefault("Large Constructor", []).append(m["name"])
    dups = detect_duplicate_code(content)
    if dups:
        smells["Duplicate Code"] = {
            "reason": f"{len(dups)} duplicate code blocks found.",
            "severity": "High",
            "examples": [block for _, block in dups[:2]]
        }
    if detect_lazy_class(metrics):
        smells["Lazy Class"] = "Class does too little."
    if detect_feature_envy(metrics):
        smells["Feature Envy"] = "Methods use more features of other classes."
    if detect_data_class(metrics):
        smells["Data Class"] = "Class mainly contains data and accessors."
    if detect_middle_man(metrics):
        smells["Middle Man"] = "Class delegates most of its work."
    if detect_inappropriate_intimacy(metrics):
        smells["Inappropriate Intimacy"] = "Class knows too much about another."
    if detect_message_chains(content):
        smells["Message Chains"] = "Chained method calls detected."
    if detect_data_clumps(content):
        smells["Data Clumps"] = "Groups of variables always used together."
    if detect_switch_statements(content):
        smells["Switch Statements"] = "Switch/case statements detected."
    if detect_conditional_complexity(content):
        smells["Conditional Complexity"] = "Complex/nested conditionals detected."
    if detect_control_flag(content):
        smells["Control Flag"] = "Boolean control flag detected."
    if detect_refused_bequest(metrics):
        smells["Refused Bequest"] = "Subclass does not use inherited behavior."
    if detect_uncommunicative_name(class_names):
        smells["Uncommunicative Name"] = "Poorly named class/method/variable."
    magics = detect_magic_numbers(content)
    if magics:
        smells["Magic Numbers"] = {
            "reason": f"Magic numbers found: {', '.join(magics[:5])}",
            "severity": "Medium"
        }
    if detect_primitive_obsession(content):
        smells["Primitive Obsession"] = "Overuse of primitive types."
    if detect_temporary_field(content):
        smells["Temporary Field"] = "Field only used in some methods."
    if detect_excessive_getters_setters(metrics):
        smells["Excessive Getters/Setters"] = "Too many public accessors."
    if detect_excessive_static_methods(content):
        smells["Excessive Static Methods"] = "Too many static methods."
    return smells 