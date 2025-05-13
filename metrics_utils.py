import re
import streamlit as st

def calculate_advanced_metrics(content: str, basic_metrics: dict) -> dict:
    try:
        method_count = basic_metrics.get("total_methods", 0)
        lcom = min(0.1 * method_count, 1.0) if method_count > 0 else 0
        cbo = len(re.findall(r'import\s+[\w.]+;', content)) + len(re.findall(r'new\s+\w+\(', content))
        inheritance_chain = re.findall(r'extends\s+\w+', content)
        dit = len(inheritance_chain)
        cc = len(re.findall(r'\b(if|for|while|case|catch)\b', content))
        rfc = len(re.findall(r'(\w+\s+\w+\s*\([^)]*\)\s*{|\w+\.[a-zA-Z_]\w*\s*\([^)]*\))', content))
        metrics = {
            "lcom": {"value": round(lcom, 2), "threshold": 0.7, "status": "high" if lcom > 0.7 else "medium" if lcom > 0.4 else "low", "icon": "🧩", "help": "Lack of Cohesion of Methods (0-1). Lower is better."},
            "cbo": {"value": cbo, "threshold": 5, "status": "high" if cbo > 5 else "medium" if cbo > 3 else "low", "icon": "🔗", "help": "Coupling Between Objects. Lower is better."},
            "dit": {"value": dit, "threshold": 3, "status": "high" if dit > 3 else "medium" if dit > 2 else "low", "icon": "📐", "help": "Depth of Inheritance Tree. Lower is better."},
            "cc": {"value": cc, "threshold": 10, "status": "high" if cc > 10 else "medium" if cc > 7 else "low", "icon": "🔄", "help": "Cyclomatic Complexity. Lower is better."},
            "rfc": {"value": rfc, "threshold": 20, "status": "high" if rfc > 20 else "medium" if rfc > 15 else "low", "icon": "📡", "help": "Response For Class (methods + calls). Lower is better."}
        }
        num_fields = len(re.findall(r'(public|private|protected)?\s+\w+\s+\w+\s*(=|;)', content))
        method_bodies = re.findall(r'(public|private|protected)?\s+(static\s+)?(\w+)\s+(\w+)\s*\([^)]*\)\s*{([\s\S]*?)}', content)
        method_lengths = [len(m[4].split('\n')) for m in method_bodies if m[4].strip()]
        avg_method_length = round(sum(method_lengths) / len(method_lengths), 2) if method_lengths else 0
        max_method_length = max(method_lengths) if method_lengths else 0
        total_lines = len(content.split('\n'))
        comment_lines = len([l for l in content.split('\n') if l.strip().startswith('//') or l.strip().startswith('/*') or l.strip().startswith('*')])
        comment_density = round((comment_lines / total_lines) * 100, 1) if total_lines > 0 else 0

        # Count public methods
        public_method_pattern = r'public\s+(static\s+)?[\w<>\[\],\s]+\s+\w+\s*\([^)]*\)\s*\{'
        num_public_methods = len(re.findall(public_method_pattern, content))
        # Count public fields
        public_field_pattern = r'public\s+(static\s+)?[\w<>\[\],\s]+\s+\w+\s*;'
        num_public_fields = len(re.findall(public_field_pattern, content))

        metrics.update({
            "num_fields": {"value": num_fields, "status": "low", "icon": "🔢"},
            "loc": {"value": basic_metrics.get("loc", total_lines), "status": "low", "icon": "📏"},
            "loc_per_method": {"value": avg_method_length, "status": "low", "icon": "📏"},
            "max_method_length": {"value": max_method_length, "status": "low", "icon": "📏"},
            "comment_density": {"value": comment_density, "status": "low", "icon": "💬"},
            "num_methods": {"value": basic_metrics.get("total_methods", 0), "status": "low", "icon": "🔧"},
            "num_public_methods": {"value": num_public_methods, "status": "low", "icon": "🔓"},
            "num_public_fields": {"value": num_public_fields, "status": "low", "icon": "🔓"},
        })
        return metrics
    except Exception as e:
        st.error(f"Error calculating advanced metrics: {str(e)}")
        return {
            "lcom": {"value": 0, "threshold": 0.7, "status": "low", "icon": "🧩", "help": "Calculation error"},
            "cbo": {"value": 0, "threshold": 5, "status": "low", "icon": "🔗", "help": "Calculation error"},
            "dit": {"value": 0, "threshold": 3, "status": "low", "icon": "📐", "help": "Calculation error"},
            "cc": {"value": 0, "threshold": 10, "status": "low", "icon": "🔄", "help": "Calculation error"},
            "rfc": {"value": 0, "threshold": 20, "status": "low", "icon": "📡", "help": "Calculation error"},
            "num_fields": {"value": 0, "status": "low", "icon": "🔢"},
            "loc": {"value": 0, "status": "low", "icon": "📏"},
            "loc_per_method": {"value": 0, "status": "low", "icon": "📏"},
            "max_method_length": {"value": 0, "status": "low", "icon": "📏"},
            "comment_density": {"value": 0, "status": "low", "icon": "💬"},
            "num_methods": {"value": 0, "status": "low", "icon": "🔧"},
            "num_public_methods": {"value": 0, "status": "low", "icon": "🔓"},
            "num_public_fields": {"value": 0, "status": "low", "icon": "🔓"},
        }

def normalize_metrics(metrics: dict) -> dict:
    max_values = {
        "lcom": 1.0,
        "cbo": 10.0,
        "dit": 5.0,
        "cc": 15.0,
        "rfc": 30.0
    }
    return {
        k: min(v["value"] / max_values[k], 1.0)
        for k, v in metrics.items() if k in max_values
    }

def calculate_health_score(metrics: dict) -> int:
    # Penalize for each high/medium status
    score = 100
    for m in metrics.values():
        if m.get("status") == "high":
            score -= 20
        elif m.get("status") == "medium":
            score -= 10
    return max(score, 0) 