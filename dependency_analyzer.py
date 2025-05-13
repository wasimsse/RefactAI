import javalang
import os
import networkx as nx
import plotly.graph_objects as go
from typing import Dict, List, Set, Tuple

class DependencyAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.class_to_file: Dict[str, str] = {}
        self.file_to_classes: Dict[str, Set[str]] = {}
        self.dependency_graph = nx.DiGraph()
        
    def analyze_project(self):
        """Analyze all Java files in the project and build dependency graph."""
        java_files = self._find_java_files()
        self._build_class_mappings(java_files)
        self._build_dependency_graph(java_files)
        
    def _find_java_files(self) -> List[str]:
        """Find all Java files in the project."""
        java_files = []
        for root, _, files in os.walk(self.project_root):
            for f in files:
                if f.endswith('.java'):
                    java_files.append(os.path.join(root, f))
        return java_files
    
    def _build_class_mappings(self, java_files: List[str]):
        """Build mappings between classes and files."""
        for file in java_files:
            try:
                with open(file, 'r') as f:
                    code = f.read()
                tree = javalang.parse.parse(code)
                
                # Map classes to files
                for _, node in tree.filter(javalang.tree.ClassDeclaration):
                    self.class_to_file[node.name] = file
                
                # Track classes used in each file
                used_classes = set()
                for _, node in tree.filter(javalang.tree.MethodInvocation):
                    if node.qualifier:
                        used_classes.add(node.qualifier)
                self.file_to_classes[file] = used_classes
                
            except Exception as e:
                print(f"Error parsing {file}: {str(e)}")
                
    def _build_dependency_graph(self, java_files: List[str]):
        """Build a directed graph of file dependencies."""
        for file, used_classes in self.file_to_classes.items():
            for cls in used_classes:
                if cls in self.class_to_file:
                    dependent_file = self.class_to_file[cls]
                    self.dependency_graph.add_edge(file, dependent_file)
    
    def get_direct_dependencies(self, target_file: str) -> List[str]:
        """Get files that the target file directly depends on."""
        return list(self.dependency_graph.successors(target_file))
    
    def get_dependent_files(self, target_file: str) -> List[str]:
        """Get files that depend on the target file."""
        return list(self.dependency_graph.predecessors(target_file))
    
    def visualize_dependencies(self, target_file: str) -> go.Figure:
        """Create an interactive visualization of dependencies."""
        # Get all related files
        direct_deps = self.get_direct_dependencies(target_file)
        dependent_files = self.get_dependent_files(target_file)
        all_files = set([target_file] + direct_deps + dependent_files)
        
        # Create subgraph
        subgraph = self.dependency_graph.subgraph(all_files)
        
        # Create layout
        pos = nx.spring_layout(subgraph)
        
        # Create edge trace
        edge_x = []
        edge_y = []
        for edge in subgraph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_color = []
        
        for node in subgraph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(os.path.basename(node))
            if node == target_file:
                node_color.append('red')
            elif node in direct_deps:
                node_color.append('blue')
            else:
                node_color.append('green')
                
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="top center",
            marker=dict(
                showscale=False,
                color=node_color,
                size=20,
                line_width=2
            )
        )
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Code Dependencies',
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                       )
        
        return fig

def analyze_dependencies(project_root: str, target_file: str) -> Tuple[List[str], List[str], go.Figure]:
    """Convenience function to analyze dependencies for a target file."""
    analyzer = DependencyAnalyzer(project_root)
    analyzer.analyze_project()
    
    direct_deps = analyzer.get_direct_dependencies(target_file)
    dependent_files = analyzer.get_dependent_files(target_file)
    visualization = analyzer.visualize_dependencies(target_file)
    
    return direct_deps, dependent_files, visualization 