import re
import plotly.graph_objects as go
import networkx as nx

def find_java_dependencies(java_code: str):
    """
    Very basic static analysis: finds imported classes and used class names.
    Returns a set of class names that this file depends on.
    """
    imports = set(re.findall(r'import\s+([\w\.]+);', java_code))
    used_classes = set(re.findall(r'new\s+(\w+)\s*\(', java_code))
    return imports.union(used_classes)

def dependency_bar_chart(dependencies):
    """
    Visualize dependencies as a horizontal bar chart.
    """
    if not dependencies:
        return None
    dep_names = sorted(list(dependencies))
    values = [1] * len(dep_names)  # All bars same height, just for visualization
    fig = go.Figure(go.Bar(
        x=values,
        y=dep_names,
        orientation='h',
        marker_color='lightskyblue'
    ))
    fig.update_layout(
        title="File Dependencies",
        xaxis_title="Depends On",
        yaxis_title="Dependency",
        height=300 + 20 * len(dep_names)
    )
    return fig

def dependency_network_chart(current_file, dependencies):
    G = nx.DiGraph()
    G.add_node(current_file)
    for dep in dependencies:
        G.add_node(dep)
        G.add_edge(current_file, dep)
    pos = nx.spring_layout(G)
    edge_x, edge_y = [], []
    for src, dst in G.edges():
        x0, y0 = pos[src]
        x1, y1 = pos[dst]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    node_x, node_y, node_text = [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color='#888'), mode='lines'))
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode='markers+text', text=node_text, textposition='top center',
        marker=dict(size=20, color=['red' if n == current_file else 'skyblue' for n in G.nodes()])
    ))
    fig.update_layout(title="Dependency Network", showlegend=False, margin=dict(l=20, r=20, t=40, b=20))
    return fig 