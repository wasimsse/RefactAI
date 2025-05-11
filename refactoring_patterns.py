import streamlit as st
from typing import Dict, List, Set, Tuple

# Pattern categories and their descriptions
PATTERN_CATEGORIES = {
    "Structural": {
        "icon": "🏗️",
        "description": "Patterns that help organize code structure and relationships between classes"
    },
    "Behavioral": {
        "icon": "🔄",
        "description": "Patterns that focus on object behavior and method organization"
    },
    "Simplification": {
        "icon": "✨",
        "description": "Patterns that simplify code and reduce complexity"
    },
    "Encapsulation": {
        "icon": "📦",
        "description": "Patterns that improve data hiding and encapsulation"
    }
}

# Enhanced pattern metadata with categories, severity, and complexity
ALL_PATTERNS = {
    "Extract Method": {
        "icon": "🔨",
        "category": "Behavioral",
        "description": "Break long methods into smaller ones.",
        "severity": "High",
        "complexity": "Low",
        "when_to_use": "When a method is too long or does multiple things",
        "benefits": ["Improved readability", "Better maintainability", "Easier testing"]
    },
    "Move Method": {
        "icon": "🚚",
        "category": "Structural",
        "description": "Move method to a more appropriate class.",
        "severity": "Medium",
        "complexity": "Medium",
        "when_to_use": "When a method uses more features of another class",
        "benefits": ["Better encapsulation", "Reduced coupling", "Improved cohesion"]
    },
    "Extract Class": {
        "icon": "🏗️",
        "category": "Structural",
        "description": "Split large classes into smaller ones.",
        "severity": "High",
        "complexity": "High",
        "when_to_use": "When a class has too many responsibilities",
        "benefits": ["Single Responsibility", "Better organization", "Easier maintenance"]
    },
    "Inline Method": {
        "icon": "🔗",
        "category": "Simplification",
        "description": "Replace trivial methods with their content.",
        "severity": "Low",
        "complexity": "Low",
        "when_to_use": "When a method is too simple to justify its existence",
        "benefits": ["Reduced complexity", "Better readability", "Simpler code"]
    },
    "Replace Temp with Query": {
        "icon": "🔍",
        "category": "Simplification",
        "description": "Replace temp variables with queries.",
        "severity": "Low",
        "complexity": "Low",
        "when_to_use": "When temporary variables make code harder to understand",
        "benefits": ["Cleaner code", "Better readability", "Reduced variables"]
    },
    "Introduce Parameter Object": {
        "icon": "📦",
        "category": "Encapsulation",
        "description": "Group long parameter lists into objects.",
        "severity": "Medium",
        "complexity": "Medium",
        "when_to_use": "When methods have too many parameters",
        "benefits": ["Better organization", "Improved maintainability", "Clearer intent"]
    },
    "Remove Middle Man": {
        "icon": "🚪",
        "category": "Structural",
        "description": "Remove unnecessary delegation.",
        "severity": "Medium",
        "complexity": "Medium",
        "when_to_use": "When a class delegates most of its work",
        "benefits": ["Simpler design", "Reduced complexity", "Better performance"]
    },
    "Replace Conditional with Polymorphism": {
        "icon": "🔄",
        "category": "Behavioral",
        "description": "Use polymorphism instead of conditionals.",
        "severity": "High",
        "complexity": "High",
        "when_to_use": "When complex conditionals make code hard to maintain",
        "benefits": ["Better extensibility", "Cleaner code", "Easier maintenance"]
    },
    "Decompose Conditional": {
        "icon": "🧩",
        "category": "Simplification",
        "description": "Break complex conditionals into simpler ones.",
        "severity": "Medium",
        "complexity": "Low",
        "when_to_use": "When conditionals are complex and hard to understand",
        "benefits": ["Better readability", "Easier maintenance", "Clearer logic"]
    },
    "Pull Up Method": {
        "icon": "⬆️",
        "category": "Structural",
        "description": "Move method to superclass.",
        "severity": "Medium",
        "complexity": "Medium",
        "when_to_use": "When duplicate code exists in subclasses",
        "benefits": ["Code reuse", "Better inheritance", "Reduced duplication"]
    },
    "Push Down Method": {
        "icon": "⬇️",
        "category": "Structural",
        "description": "Move method to subclass.",
        "severity": "Medium",
        "complexity": "Medium",
        "when_to_use": "When a method is only used by some subclasses",
        "benefits": ["Better organization", "Clearer hierarchy", "Improved cohesion"]
    },
    "Remove Duplicate Code": {
        "icon": "🧹",
        "category": "Simplification",
        "description": "Eliminate duplicate code blocks.",
        "severity": "High",
        "complexity": "Medium",
        "when_to_use": "When similar code appears in multiple places",
        "benefits": ["Better maintainability", "Reduced bugs", "Easier updates"]
    }
}

# Enhanced mapping from code smells to patterns with explanations
SMELL_TO_PATTERNS = {
    "God Class": {
        "patterns": ["Extract Class", "Extract Method"],
        "description": "A class that has grown too large and handles too many responsibilities",
        "impact": "High",
        "detection_criteria": ["High LOC", "Many methods", "Multiple responsibilities"]
    },
    "Long Method": {
        "patterns": ["Extract Method", "Inline Method"],
        "description": "A method that has grown too large and does too many things",
        "impact": "High",
        "detection_criteria": ["High cyclomatic complexity", "Many lines of code", "Multiple responsibilities"]
    },
    "Feature Envy": {
        "patterns": ["Move Method"],
        "description": "A method that uses more features of another class than its own",
        "impact": "Medium",
        "detection_criteria": ["High coupling", "Low cohesion", "Many external calls"]
    },
    "Data Class": {
        "patterns": ["Encapsulate Field", "Add Behavior"],
        "description": "A class that only contains data and no behavior",
        "impact": "Medium",
        "detection_criteria": ["Only fields and getters/setters", "No business logic", "High coupling"]
    },
    "Duplicate Code": {
        "patterns": ["Remove Duplicate Code", "Extract Method"],
        "description": "Similar code blocks that appear in multiple places",
        "impact": "High",
        "detection_criteria": ["Identical or similar code blocks", "Copy-pasted code", "Similar logic"]
    },
    "Complex Class": {
        "patterns": ["Decompose Conditional", "Replace Conditional with Polymorphism"],
        "description": "A class with high cyclomatic complexity",
        "impact": "High",
        "detection_criteria": ["High WMC", "Many branches", "Complex logic"]
    },
    "Long Parameter List": {
        "patterns": ["Introduce Parameter Object"],
        "description": "Methods with too many parameters",
        "impact": "Medium",
        "detection_criteria": ["Many parameters", "Related parameters", "Frequent changes"]
    },
    "Middle Man": {
        "patterns": ["Remove Middle Man"],
        "description": "A class that delegates most of its work to another class",
        "impact": "Medium",
        "detection_criteria": ["Most methods delegate", "Low added value", "Unnecessary abstraction"]
    },
    "Switch Statements": {
        "patterns": ["Replace Conditional with Polymorphism"],
        "description": "Complex switch statements that could be replaced with polymorphism",
        "impact": "Medium",
        "detection_criteria": ["Large switch statements", "Frequent changes", "Similar cases"]
    },
    "Too Many Fields": {
        "patterns": ["Extract Class"],
        "description": "A class with too many instance variables",
        "impact": "Medium",
        "detection_criteria": ["Many fields", "Unrelated fields", "High coupling"]
    },
    "Lazy Class": {
        "patterns": ["Inline Method", "Remove Middle Man"],
        "description": "A class that does too little to justify its existence",
        "impact": "Low",
        "detection_criteria": ["Few methods", "Low complexity", "Little responsibility"]
    },
    "Message Chains": {
        "patterns": ["Extract Method", "Move Method"],
        "description": "Long chains of method calls that create tight coupling",
        "impact": "High",
        "detection_criteria": ["Long call chains", "High coupling", "Brittle code"]
    }
}

def get_enabled_patterns(detected_smells: List[str]) -> Set[str]:
    """Return a set of enabled patterns based on detected smells."""
    enabled = set()
    for smell in detected_smells:
        if smell in SMELL_TO_PATTERNS:
            enabled.update(SMELL_TO_PATTERNS[smell]["patterns"])
    return enabled

def render_pattern_selection_ui(detected_smells: List[str], user_instructions_default: str = "") -> Tuple[List[str], str, bool]:
    """
    Render the pattern selection UI. Returns (selected_patterns, user_instructions, detect_more_smells).
    Only patterns relevant to detected smells are enabled.
    """
    enabled_patterns = get_enabled_patterns(detected_smells)
    
    # Add option to detect more smells
    st.markdown("#### 🔍 Additional Analysis")
    detect_more_smells = st.checkbox(
        "Request LLM to detect additional code smells",
        help="Ask the LLM to analyze the code for additional smells beyond the automated detection"
    )
    
    # User instructions
    st.markdown("#### 📝 Special Instructions")
    user_instructions = st.text_area(
        "Add any specific instructions for the LLM (optional):",
        user_instructions_default,
        help="Provide additional context or requirements for the refactoring process"
    )
    
    # Pattern selection by category
    st.markdown("#### 🎯 Choose Refactoring Patterns")
    selected_patterns = []
    
    for category, category_info in PATTERN_CATEGORIES.items():
        st.markdown(f"##### {category_info['icon']} {category}")
        st.caption(category_info['description'])
        
        # Get patterns for this category
        category_patterns = {
            name: info for name, info in ALL_PATTERNS.items()
            if info['category'] == category
        }
        
        for pattern, info in category_patterns.items():
            enabled = pattern in enabled_patterns
            checked = enabled
            
            # Create a detailed tooltip
            tooltip = f"""
            **Description:** {info['description']}
            **Severity:** {info['severity']}
            **Complexity:** {info['complexity']}
            **When to use:** {info['when_to_use']}
            **Benefits:** {', '.join(info['benefits'])}
            """
            
            if enabled:
                tooltip += f"\n**Enabled due to:** {', '.join([s for s in detected_smells if pattern in SMELL_TO_PATTERNS.get(s, {}).get('patterns', [])])}"
            
            cb = st.checkbox(
                f"{info['icon']} {pattern}",
                value=checked,
                disabled=not enabled,
                help=tooltip
            )
            
            if cb and enabled:
                selected_patterns.append(pattern)
    
    return selected_patterns, user_instructions, detect_more_smells 