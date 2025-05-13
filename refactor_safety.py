import javalang
import difflib
import subprocess
from typing import Dict, List, Tuple, Optional

class RefactorSafety:
    def __init__(self, project_root: str):
        self.project_root = project_root
        
    def check_method_signatures(self, before_code: str, after_code: str) -> List[Dict]:
        """Check if method signatures have changed between before and after code."""
        issues = []
        try:
            before_tree = javalang.parse.parse(before_code)
            after_tree = javalang.parse.parse(after_code)
            
            # Get all method declarations from both trees
            before_methods = {node.name: node for _, node in before_tree.filter(javalang.tree.MethodDeclaration)}
            after_methods = {node.name: node for _, node in after_tree.filter(javalang.tree.MethodDeclaration)}
            
            # Check for removed methods
            for name in before_methods:
                if name not in after_methods:
                    issues.append({
                        'type': 'removed_method',
                        'method': name,
                        'severity': 'high'
                    })
            
            # Check for added methods
            for name in after_methods:
                if name not in before_methods:
                    issues.append({
                        'type': 'added_method',
                        'method': name,
                        'severity': 'low'
                    })
            
            # Check for modified signatures
            for name in before_methods:
                if name in after_methods:
                    before_method = before_methods[name]
                    after_method = after_methods[name]
                    
                    # Check return type
                    if str(before_method.return_type) != str(after_method.return_type):
                        issues.append({
                            'type': 'return_type_changed',
                            'method': name,
                            'before': str(before_method.return_type),
                            'after': str(after_method.return_type),
                            'severity': 'high'
                        })
                    
                    # Check parameters
                    before_params = [(p.type, p.name) for p in before_method.parameters]
                    after_params = [(p.type, p.name) for p in after_method.parameters]
                    if before_params != after_params:
                        issues.append({
                            'type': 'parameters_changed',
                            'method': name,
                            'before': str(before_params),
                            'after': str(after_params),
                            'severity': 'high'
                        })
            
        except Exception as e:
            issues.append({
                'type': 'parsing_error',
                'error': str(e),
                'severity': 'high'
            })
            
        return issues
    
    def check_interface_integrity(self, before_code: str, after_code: str) -> List[Dict]:
        """Check if interface implementations are still valid."""
        issues = []
        try:
            before_tree = javalang.parse.parse(before_code)
            after_tree = javalang.parse.parse(after_code)
            
            # Get all interfaces and their methods
            before_interfaces = {}
            for _, node in before_tree.filter(javalang.tree.InterfaceDeclaration):
                methods = {m.name: m for _, m in node.filter(javalang.tree.MethodDeclaration)}
                before_interfaces[node.name] = methods
            
            # Check if all interface methods are still implemented
            for _, node in after_tree.filter(javalang.tree.ClassDeclaration):
                if node.implements:
                    for interface in node.implements:
                        if interface.name in before_interfaces:
                            class_methods = {m.name: m for _, m in node.filter(javalang.tree.MethodDeclaration)}
                            for method_name, method in before_interfaces[interface.name].items():
                                if method_name not in class_methods:
                                    issues.append({
                                        'type': 'missing_interface_method',
                                        'class': node.name,
                                        'interface': interface.name,
                                        'method': method_name,
                                        'severity': 'high'
                                    })
            
        except Exception as e:
            issues.append({
                'type': 'parsing_error',
                'error': str(e),
                'severity': 'high'
            })
            
        return issues
    
    def generate_semantic_diff(self, before_code: str, after_code: str) -> str:
        """Generate a semantic diff between before and after code."""
        before_lines = before_code.splitlines()
        after_lines = after_code.splitlines()
        diff = difflib.unified_diff(before_lines, after_lines, lineterm='')
        return '\n'.join(diff)
    
    def run_tests(self) -> Tuple[bool, str]:
        """Run tests if they exist in the project."""
        try:
            # Check for test files
            test_files = []
            for root, _, files in os.walk(self.project_root):
                for f in files:
                    if f.endswith('Test.java') or f.endswith('Tests.java'):
                        test_files.append(os.path.join(root, f))
            
            if not test_files:
                return True, "No test files found"
            
            # Run tests using Maven or Gradle
            if os.path.exists(os.path.join(self.project_root, 'pom.xml')):
                result = subprocess.run(['mvn', 'test'], capture_output=True, text=True)
            elif os.path.exists(os.path.join(self.project_root, 'build.gradle')):
                result = subprocess.run(['./gradlew', 'test'], capture_output=True, text=True)
            else:
                return True, "No build system found for running tests"
            
            return result.returncode == 0, result.stdout
            
        except Exception as e:
            return False, f"Error running tests: {str(e)}"
    
    def perform_safety_checks(self, before_code: str, after_code: str) -> Dict:
        """Perform all safety checks and return results."""
        return {
            'method_signatures': self.check_method_signatures(before_code, after_code),
            'interface_integrity': self.check_interface_integrity(before_code, after_code),
            'semantic_diff': self.generate_semantic_diff(before_code, after_code),
            'tests': self.run_tests()
        } 