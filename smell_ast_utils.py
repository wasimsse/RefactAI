import javalang

def detect_long_methods_ast(java_code, length_threshold=40):
    """
    Detects long methods in Java code using AST parsing.
    Returns a list of dicts with method name, length, threshold, location, and description.
    """
    smells = []
    try:
        tree = javalang.parse.parse(java_code)
        for _, node in tree.filter(javalang.tree.MethodDeclaration):
            if node.body:
                start = node.position.line if node.position else 0
                end = max((stmt.position.line for stmt in node.body if stmt.position), default=start)
                method_length = end - start + 1
                if method_length > length_threshold:
                    smells.append({
                        "type": "Long Method",
                        "name": node.name,
                        "length": method_length,
                        "threshold": length_threshold,
                        "location": f"Line {start}",
                        "description": f"Method '{node.name}' is {method_length} lines (threshold: {length_threshold})"
                    })
    except Exception as e:
        print(f"AST parsing error (Long Method): {e}")
    return smells

def detect_large_classes_ast(java_code, loc_threshold=200, method_threshold=10):
    smells = []
    try:
        tree = javalang.parse.parse(java_code)
        for _, node in tree.filter(javalang.tree.ClassDeclaration):
            class_name = node.name
            methods = [m for m in node.methods]
            method_count = len(methods)
            # Estimate LOC by using the last method's end line or the class' end line
            start = node.position.line if node.position else 0
            end = start
            for m in methods:
                if m.body:
                    mend = max((stmt.position.line for stmt in m.body if stmt.position), default=m.position.line if m.position else start)
                    end = max(end, mend)
            loc = end - start + 1
            if loc > loc_threshold and method_count > method_threshold:
                smells.append({
                    "type": "God Class",
                    "name": class_name,
                    "loc": loc,
                    "methods": method_count,
                    "loc_threshold": loc_threshold,
                    "method_threshold": method_threshold,
                    "location": f"Line {start}",
                    "description": f"Class '{class_name}' is {loc} lines and has {method_count} methods (thresholds: {loc_threshold} LOC, {method_threshold} methods)"
                })
    except Exception as e:
        print(f"AST parsing error (God Class): {e}")
    return smells

def detect_data_classes_ast(java_code, accessor_ratio_threshold=0.7):
    smells = []
    try:
        tree = javalang.parse.parse(java_code)
        for _, node in tree.filter(javalang.tree.ClassDeclaration):
            class_name = node.name
            methods = [m for m in node.methods]
            total_methods = len(methods)
            accessors = [m for m in methods if m.name.startswith('get') or m.name.startswith('set')]
            accessor_count = len(accessors)
            ratio = accessor_count / total_methods if total_methods > 0 else 0
            if total_methods > 0 and ratio > accessor_ratio_threshold:
                smells.append({
                    "type": "Data Class",
                    "name": class_name,
                    "accessor_ratio": ratio,
                    "accessor_count": accessor_count,
                    "total_methods": total_methods,
                    "threshold": accessor_ratio_threshold,
                    "location": f"Line {node.position.line if node.position else '?'}",
                    "description": f"Class '{class_name}' has accessor ratio {ratio:.2f} (threshold: {accessor_ratio_threshold})"
                })
    except Exception as e:
        print(f"AST parsing error (Data Class): {e}")
    return smells

def detect_feature_envy_ast(java_code, external_access_threshold=10):
    smells = []
    try:
        tree = javalang.parse.parse(java_code)
        for _, node in tree.filter(javalang.tree.MethodDeclaration):
            if node.body:
                external_accesses = 0
                for path, member in node:
                    if isinstance(member, javalang.tree.MethodInvocation):
                        if member.qualifier and member.qualifier != 'this':
                            external_accesses += 1
                if external_accesses > external_access_threshold:
                    smells.append({
                        "type": "Feature Envy",
                        "name": node.name,
                        "external_accesses": external_accesses,
                        "threshold": external_access_threshold,
                        "location": f"Line {node.position.line if node.position else '?'}",
                        "description": f"Method '{node.name}' accesses {external_accesses} members of other classes (threshold: {external_access_threshold})"
                    })
    except Exception as e:
        print(f"AST parsing error (Feature Envy): {e}")
    return smells

def detect_switch_statements_ast(java_code):
    smells = []
    try:
        tree = javalang.parse.parse(java_code)
        for _, node in tree.filter(javalang.tree.SwitchStatement):
            smells.append({
                "type": "Switch Statement",
                "location": f"Line {node.position.line if node.position else '?'}",
                "description": "Switch statement detected. Consider polymorphism or strategy pattern."
            })
    except Exception as e:
        print(f"AST parsing error (Switch Statement): {e}")
    return smells

def detect_ast_smells(java_code, thresholds=None):
    if thresholds is None:
        thresholds = {}
    results = {}
    # Long Method
    long_methods = detect_long_methods_ast(java_code, length_threshold=thresholds.get('long_method', 40))
    for m in long_methods:
        results[f"Long Method: {m['name']}"] = m
    # God Class
    god_classes = detect_large_classes_ast(
        java_code,
        loc_threshold=thresholds.get('god_class_loc', 200),
        method_threshold=thresholds.get('god_class_methods', 10)
    )
    for g in god_classes:
        results[f"God Class: {g['name']}"] = g
    # Data Class
    data_classes = detect_data_classes_ast(java_code, accessor_ratio_threshold=thresholds.get('data_class_accessor_ratio', 0.7))
    for d in data_classes:
        results[f"Data Class: {d['name']}"] = d
    # Feature Envy
    feature_envy = detect_feature_envy_ast(java_code, external_access_threshold=thresholds.get('feature_envy', 10))
    for f in feature_envy:
        results[f"Feature Envy: {f['name']}"] = f
    # Switch Statements
    switches = detect_switch_statements_ast(java_code)
    for sidx, s in enumerate(switches):
        results[f"Switch Statement {sidx+1}"] = s
    return results 