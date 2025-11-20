"""
P3.6 Visualization Tools

Diagrams, charts, and visualization generation.
"""

from typing import Any, Dict, List, Optional


class DiagramResult:
    """Result of diagram generation."""
    def __init__(self, code: str, format: str):
        self.code = code
        self.format = format


class ChartResult:
    """Result of chart generation."""
    def __init__(self, success: bool, path: str, message: str):
        self.success = success
        self.path = path
        self.message = message


class Step:
    """A step in a flowchart."""
    def __init__(self, id: str, label: str, next_steps: List[str] = None):
        self.id = id
        self.label = label
        self.next_steps = next_steps or []


class Component:
    """A component in an architecture diagram."""
    def __init__(self, id: str, name: str, type: str, connections: List[str] = None):
        self.id = id
        self.name = name
        self.type = type
        self.connections = connections or []


class VisualizationTools:
    """Visualization and diagram generation tools."""

    def generate_mermaid(
        self,
        diagram_type: str,
        content: Dict[str, Any]
    ) -> str:
        """
        Generate Mermaid diagram code.

        Args:
            diagram_type: Type of diagram (flowchart, sequence, class, etc.)
            content: Diagram content definition
        """
        if diagram_type == "flowchart":
            return self._generate_flowchart_mermaid(content)
        elif diagram_type == "sequence":
            return self._generate_sequence_mermaid(content)
        elif diagram_type == "class":
            return self._generate_class_mermaid(content)
        elif diagram_type == "er":
            return self._generate_er_mermaid(content)
        elif diagram_type == "gantt":
            return self._generate_gantt_mermaid(content)
        else:
            return f"graph TD\n    A[Unsupported diagram type: {diagram_type}]"

    def _generate_flowchart_mermaid(self, content: Dict) -> str:
        """Generate flowchart Mermaid code."""
        direction = content.get("direction", "TD")
        nodes = content.get("nodes", [])
        edges = content.get("edges", [])

        lines = [f"graph {direction}"]

        for node in nodes:
            node_id = node.get("id", "A")
            label = node.get("label", "Node")
            shape = node.get("shape", "rect")

            if shape == "rect":
                lines.append(f"    {node_id}[{label}]")
            elif shape == "round":
                lines.append(f"    {node_id}({label})")
            elif shape == "diamond":
                lines.append(f"    {node_id}{{{label}}}")
            elif shape == "circle":
                lines.append(f"    {node_id}(({label}))")

        for edge in edges:
            from_node = edge.get("from", "A")
            to_node = edge.get("to", "B")
            label = edge.get("label", "")

            if label:
                lines.append(f"    {from_node} -->|{label}| {to_node}")
            else:
                lines.append(f"    {from_node} --> {to_node}")

        return "\n".join(lines)

    def _generate_sequence_mermaid(self, content: Dict) -> str:
        """Generate sequence diagram Mermaid code."""
        participants = content.get("participants", [])
        messages = content.get("messages", [])

        lines = ["sequenceDiagram"]

        for p in participants:
            lines.append(f"    participant {p}")

        for msg in messages:
            from_p = msg.get("from", "A")
            to_p = msg.get("to", "B")
            text = msg.get("text", "")
            arrow = msg.get("arrow", "->>")

            lines.append(f"    {from_p}{arrow}{to_p}: {text}")

        return "\n".join(lines)

    def _generate_class_mermaid(self, content: Dict) -> str:
        """Generate class diagram Mermaid code."""
        classes = content.get("classes", [])
        relations = content.get("relations", [])

        lines = ["classDiagram"]

        for cls in classes:
            name = cls.get("name", "Class")
            methods = cls.get("methods", [])
            attributes = cls.get("attributes", [])

            lines.append(f"    class {name} {{")
            for attr in attributes:
                lines.append(f"        {attr}")
            for method in methods:
                lines.append(f"        {method}()")
            lines.append("    }")

        for rel in relations:
            from_cls = rel.get("from", "A")
            to_cls = rel.get("to", "B")
            rel_type = rel.get("type", "-->")
            lines.append(f"    {from_cls} {rel_type} {to_cls}")

        return "\n".join(lines)

    def _generate_er_mermaid(self, content: Dict) -> str:
        """Generate ER diagram Mermaid code."""
        entities = content.get("entities", [])
        relations = content.get("relations", [])

        lines = ["erDiagram"]

        for rel in relations:
            from_e = rel.get("from", "A")
            to_e = rel.get("to", "B")
            label = rel.get("label", "")
            cardinality = rel.get("cardinality", "||--||")

            lines.append(f"    {from_e} {cardinality} {to_e} : {label}")

        return "\n".join(lines)

    def _generate_gantt_mermaid(self, content: Dict) -> str:
        """Generate Gantt chart Mermaid code."""
        title = content.get("title", "Project Timeline")
        tasks = content.get("tasks", [])

        lines = [
            "gantt",
            f"    title {title}",
            "    dateFormat YYYY-MM-DD"
        ]

        current_section = None
        for task in tasks:
            section = task.get("section")
            if section and section != current_section:
                lines.append(f"    section {section}")
                current_section = section

            name = task.get("name", "Task")
            start = task.get("start", "2024-01-01")
            duration = task.get("duration", "1d")

            lines.append(f"    {name} : {start}, {duration}")

        return "\n".join(lines)

    def plot_chart(
        self,
        data: List[Dict],
        chart_type: str,
        options: Dict[str, Any]
    ) -> ChartResult:
        """
        Create a chart (requires matplotlib).

        Args:
            data: Chart data
            chart_type: Type of chart (line, bar, pie, scatter)
            options: Chart options
        """
        try:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 6))

            title = options.get("title", "Chart")
            x_label = options.get("x_label", "X")
            y_label = options.get("y_label", "Y")
            output = options.get("output", "chart.png")

            if chart_type == "line":
                x = [d.get("x", i) for i, d in enumerate(data)]
                y = [d.get("y", 0) for d in data]
                ax.plot(x, y)

            elif chart_type == "bar":
                x = [d.get("label", str(i)) for i, d in enumerate(data)]
                y = [d.get("value", 0) for d in data]
                ax.bar(x, y)

            elif chart_type == "pie":
                labels = [d.get("label", "") for d in data]
                values = [d.get("value", 0) for d in data]
                ax.pie(values, labels=labels, autopct='%1.1f%%')

            elif chart_type == "scatter":
                x = [d.get("x", 0) for d in data]
                y = [d.get("y", 0) for d in data]
                ax.scatter(x, y)

            ax.set_title(title)
            if chart_type != "pie":
                ax.set_xlabel(x_label)
                ax.set_ylabel(y_label)

            plt.tight_layout()
            plt.savefig(output)
            plt.close()

            return ChartResult(True, output, "Chart generated")

        except ImportError:
            return ChartResult(False, "", "matplotlib not installed")
        except Exception as e:
            return ChartResult(False, "", str(e))

    def generate_flowchart(self, steps: List[Step]) -> str:
        """
        Generate flowchart from steps.

        Args:
            steps: List of Step objects
        """
        content = {
            "direction": "TD",
            "nodes": [{"id": s.id, "label": s.label} for s in steps],
            "edges": []
        }

        for step in steps:
            for next_id in step.next_steps:
                content["edges"].append({"from": step.id, "to": next_id})

        return self.generate_mermaid("flowchart", content)

    def create_architecture_diagram(self, components: List[Component]) -> str:
        """
        Create architecture diagram from components.

        Args:
            components: List of Component objects
        """
        content = {
            "direction": "TB",
            "nodes": [],
            "edges": []
        }

        for comp in components:
            shape = "rect"
            if comp.type == "database":
                shape = "cylinder"
            elif comp.type == "service":
                shape = "round"
            elif comp.type == "external":
                shape = "hexagon"

            content["nodes"].append({
                "id": comp.id,
                "label": comp.name,
                "shape": shape
            })

            for conn in comp.connections:
                content["edges"].append({
                    "from": comp.id,
                    "to": conn
                })

        return self.generate_mermaid("flowchart", content)

    def render_markdown(self, content: str) -> str:
        """
        Render Markdown to HTML.

        Args:
            content: Markdown content
        """
        try:
            import markdown
            return markdown.markdown(content, extensions=['fenced_code', 'tables'])
        except ImportError:
            # Basic conversion
            html = content.replace('\n\n', '</p><p>')
            html = f"<p>{html}</p>"
            return html

    def export_diagram(
        self,
        diagram: str,
        format: str = "svg"
    ) -> str:
        """
        Export diagram to image format.

        Note: Requires mermaid-cli for actual rendering.
        Returns the diagram code for now.
        """
        return diagram
