"""
File-level code analysis module for detecting potential issues in Java source files.
"""
from typing import Dict, List, Optional
import os
import re
from dataclasses import dataclass
from pathlib import Path

@dataclass
class FileAnalysisResult:
    """Data class to hold file analysis results."""
    file_path: str
    file_size: int
    line_count: int
    global_variables: List[str]
    class_count: int
    method_count: int
    import_count: int
    issues: Dict[str, Dict[str, any]]

class FileAnalyzer:
    """Analyzes Java source files for potential code quality issues."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {
            'max_file_length': 1000,  # Maximum acceptable lines in a file
            'max_global_vars': 5,     # Maximum acceptable global variables
            'max_file_size': 100000,  # Maximum file size in bytes (100KB)
            'max_class_per_file': 1,  # Preferred maximum classes per file
        }
    
    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        """
        Analyze a Java source file for potential issues.
        
        Args:
            file_path: Path to the Java source file
            
        Returns:
            FileAnalysisResult object containing analysis results
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Basic file metrics
        file_size = os.path.getsize(file_path)
        lines = content.splitlines()
        line_count = len([line for line in lines if line.strip()])
        
        # Analysis results
        issues = {}
        
        # Check file length
        if line_count > self.config['max_file_length']:
            issues['excessive_length'] = {
                'severity': 'high',
                'message': f'File has {line_count} lines (max: {self.config["max_file_length"]})',
                'suggestion': 'Consider splitting the file into multiple files'
            }
        
        # Check file size
        if file_size > self.config['max_file_size']:
            issues['large_file_size'] = {
                'severity': 'medium',
                'message': f'File size is {file_size/1024:.1f}KB (max: {self.config["max_file_size"]/1024:.1f}KB)',
                'suggestion': 'Consider refactoring or splitting the file'
            }
        
        # Analyze global variables
        global_vars = self._find_global_variables(content)
        if len(global_vars) > self.config['max_global_vars']:
            issues['excessive_globals'] = {
                'severity': 'high',
                'message': f'Found {len(global_vars)} global variables',
                'suggestion': 'Consider encapsulating globals within classes'
            }
        
        # Count classes and check for multiple class definitions
        classes = self._count_classes(content)
        if classes > self.config['max_class_per_file']:
            issues['multiple_classes'] = {
                'severity': 'medium',
                'message': f'File contains {classes} classes',
                'suggestion': 'Consider moving each class to its own file'
            }
        
        # Analyze imports and package structure
        imports = self._analyze_imports(content)
        if len(imports) > 20:  # Arbitrary threshold for demonstration
            issues['many_imports'] = {
                'severity': 'low',
                'message': f'File has {len(imports)} imports',
                'suggestion': 'Consider grouping related functionality'
            }
        
        # Check for modular design issues
        modular_issues = self._check_modular_design(content)
        issues.update(modular_issues)
        
        return FileAnalysisResult(
            file_path=file_path,
            file_size=file_size,
            line_count=line_count,
            global_variables=global_vars,
            class_count=classes,
            method_count=self._count_methods(content),
            import_count=len(imports),
            issues=issues
        )
    
    def _find_global_variables(self, content: str) -> List[str]:
        """Find global variable declarations in the file."""
        # Match static and instance variables declared at class level
        pattern = r'(?:private|public|protected)?\s+(?:static\s+)?(?:final\s+)?\w+\s+(\w+)\s*[=;]'
        matches = re.finditer(pattern, content)
        return [match.group(1) for match in matches]
    
    def _count_classes(self, content: str) -> int:
        """Count the number of class definitions in the file."""
        class_pattern = r'\b(?:public\s+|private\s+|protected\s+)?(?:abstract\s+)?class\s+\w+'
        return len(re.findall(class_pattern, content))
    
    def _count_methods(self, content: str) -> int:
        """Count the number of method definitions in the file."""
        method_pattern = r'(?:public|private|protected)\s+(?:static\s+)?[\w<>[\],\s]+\s+\w+\s*\([^)]*\)\s*[{;]'
        return len(re.findall(method_pattern, content))
    
    def _analyze_imports(self, content: str) -> List[str]:
        """Analyze import statements in the file."""
        import_pattern = r'import\s+([^;]+);'
        return re.findall(import_pattern, content)
    
    def _check_modular_design(self, content: str) -> Dict[str, Dict]:
        """Check for modular design issues."""
        issues = {}
        
        # Check for long methods (potential modularity issue)
        method_bodies = re.finditer(r'(?:public|private|protected)\s+(?:static\s+)?[\w<>[\],\s]+\s+(\w+)\s*\([^)]*\)\s*{([^}]*)}', content)
        for method in method_bodies:
            method_name = method.group(1)
            method_body = method.group(2)
            lines = method_body.count('\n')
            
            if lines > 50:  # Arbitrary threshold for demonstration
                issues[f'long_method_{method_name}'] = {
                    'severity': 'medium',
                    'message': f'Method {method_name} is {lines} lines long',
                    'suggestion': 'Consider breaking down into smaller methods'
                }
        
        # Check for responsibility encapsulation
        if self._has_mixed_responsibilities(content):
            issues['mixed_responsibilities'] = {
                'severity': 'high',
                'message': 'File appears to handle multiple responsibilities',
                'suggestion': 'Consider splitting into separate classes by responsibility'
            }
        
        return issues
    
    def _has_mixed_responsibilities(self, content: str) -> bool:
        """
        Check if the file handles multiple responsibilities.
        This is a simplified check based on method naming patterns.
        """
        # Look for methods that seem to handle different concerns
        patterns = {
            'data_access': r'\b(?:get|set|load|save|fetch|store)\w+',
            'business_logic': r'\b(?:calculate|process|validate|check)\w+',
            'ui': r'\b(?:display|show|render|draw|paint)\w+',
            'network': r'\b(?:send|receive|connect|disconnect)\w+',
        }
        
        responsibility_count = 0
        for category, pattern in patterns.items():
            if re.search(pattern, content):
                responsibility_count += 1
        
        return responsibility_count > 2  # If handling more than 2 types of responsibilities 