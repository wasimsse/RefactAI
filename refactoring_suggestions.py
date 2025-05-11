import streamlit as st

def get_refactoring_suggestion(smell: str) -> str:
    """
    Return a refactoring suggestion string for a given code smell.
    """
    suggestions = {
        "God Class": "Consider splitting the class into smaller, more focused classes.",
        "Long Method": "Extract smaller methods from this long method.",
        "Feature Envy": "Move the method to the class it is most interested in.",
        "Data Class": "Add behavior to the class or refactor responsibilities.",
        "Duplicate Code": "Refactor to remove duplication, possibly by extracting methods.",
        "Too Many Fields": "Split the class or reduce the number of fields.",
        "Lazy Class": "Remove or merge the class with another.",
        "Message Chains": "Refactor to reduce message chains, possibly by introducing intermediary methods.",
        "Switch Statements": "Consider using polymorphism or the strategy pattern.",
        "Middle Man": "Remove unnecessary delegation from the class.",
        "Long Parameter List": "Refactor to use parameter objects."
    }
    return suggestions.get(smell, "No specific suggestion available.")

def render_quick_fix_button(smell: str, on_click=None):
    """
    Render a Quick Fix button for a given code smell. Calls on_click if provided.
    """
    label = f"💡 Quick Fix: {smell}"
    if st.button(label, key=f"quick_fix_{smell}"):
        if on_click:
            on_click(smell)
        else:
            st.info(f"Quick Fix for '{smell}' would be applied here (demo mode).") 