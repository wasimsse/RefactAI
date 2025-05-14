from typing import Set

def get_pattern_safety(pattern: str, dependencies: Set[str], dependents: Set[str]) -> str:
    """
    Returns 'safe', 'risky', or 'unsafe' for a given pattern based on dependencies and dependents.
    - 'safe': No ripple effect expected.
    - 'risky': May affect other files/classes (has dependents or dependencies).
    - 'unsafe': Will break dependents (e.g., public API used elsewhere).
    """
    # Patterns that are always safe (internal refactoring)
    always_safe = {"Extract Method", "Extract Class", "Inline Method", "Remove Duplicate Code", "Decompose Conditional", "Replace Temp with Query"}
    # Patterns that are risky if there are dependents (e.g., Move Method, Rename Method)
    risky_if_dependents = {"Move Method", "Rename Method", "Pull Up Method", "Push Down Method", "Replace Conditional with Polymorphism", "Introduce Parameter Object"}
    # Patterns that are unsafe if there are dependents (e.g., Remove Method, Change Signature)
    unsafe_if_dependents = {"Remove Middle Man", "Encapsulate Field"}

    if pattern in always_safe:
        return "safe"
    if pattern in risky_if_dependents:
        if dependents:
            return "risky"
        else:
            return "safe"
    if pattern in unsafe_if_dependents:
        if dependents:
            return "unsafe"
        else:
            return "safe"
    # Default: risky if there are dependents or dependencies
    if dependents or dependencies:
        return "risky"
    return "safe" 