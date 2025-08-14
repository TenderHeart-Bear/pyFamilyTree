"""
D3.js-based interactive family tree viewer
Handles large family trees with proper zoom, pan, and fit-to-window capabilities
"""
import os
import json
import webbrowser
from typing import Dict, Any, Optional
from pathlib import Path

class D3FamilyTreeViewer:
    """
    Generates interactive D3.js-based family tree viewer
    Better handling of large trees with proper zoom and pan
    """
    
    def __init__(self, character_data: Dict[str, Dict[str, Any]], output_dir: str):
        """
        Initialize the D3.js viewer
        
        Args:
            character_data: Dictionary mapping person IDs to their data
            output_dir: Directory to save the HTML file
        """
        self.character_data = character_data
        self.output_dir = Path(output_dir)
        self.html_path = self.output_dir / "d3_family_tree.html"
        
    def generate_html(self) -> str:
        """
        Generate the interactive D3.js HTML file
        
        Returns:
            str: Path to the generated HTML file
        """
        # Convert character data to JSON for JavaScript
        character_json = json.dumps(self.character_data, indent=2)
        
        # Generate HTML template
        html_content = self._create_d3_template(character_json)
        
        # Write HTML file
        with open(self.html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(self.html_path)
    
    def _create_d3_template(self, character_json: str) -> str:
        """Create the D3.js HTML template"""
        
        # Load simplified template from external file
        template_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'templates', 'd3_tree_template_simple.html')
        script_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'templates', 'd3_tree_script.js')
        
        print(f"DEBUG: Looking for template at: {template_path}")
        print(f"DEBUG: Template exists: {os.path.exists(template_path)}")
        print(f"DEBUG: Looking for script at: {script_path}")
        print(f"DEBUG: Script exists: {os.path.exists(script_path)}")
        
        try:
            try:
            # Load simplified template
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Replace the placeholder with actual character data
            html_content = template_content.replace('{CHARACTER_DATA}', character_json)
            
            # Copy the JavaScript file to the output directory
            script_output_path = os.path.join(os.path.dirname(self.html_path), 'd3_tree_script.js')
            
            # Use a single context manager for both read and write operations
            with open(script_path, 'r', encoding='utf-8') as src, \
                 open(script_output_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
            
            print(f"DEBUG: JavaScript file copied to: {script_output_path}")
            
            return html_content
            
        except FileNotFoundError as e:
            print(f"DEBUG: Template file not found: {e}")
            # Fallback to a simple template if the file is not found
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Family Tree - D3.js</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
        #tree-svg {{ width: 100%; height: 80vh; border: 1px solid #ccc; }}
        .node {{ cursor: pointer; }}
        .node:hover {{ stroke: #3498db; stroke-width: 3px; }}
        .link {{ fill: none; stroke: #95a5a6; stroke-width: 2px; }}
        .spouse-link {{ fill: none; stroke: #e74c3c; stroke-width: 2px; stroke-dasharray: 5,5; }}
    </style>
</head>
<body>
    <h1>Family Tree Visualization</h1>
    <div id="tree-svg"></div>
    
    <script>
        const characterData = {character_json};
        
        // Simple D3.js tree visualization
        const svg = d3.select("#tree-svg").append("svg").attr("width", "100%").attr("height", "100%");
        const g = svg.append("g");
        
        // Create a simple tree layout
        const treeLayout = d3.tree().size([800, 600]);
        
        // Build tree data (simplified)
        const root = d3.hierarchy({{ id: "root", name: "Family Tree", children: [] }});
        
        // Apply layout
        treeLayout(root);
        
        // Draw links
        g.selectAll(".link")
            .data(root.links())
            .enter().append("path")
            .attr("class", "link")
            .attr("d", d3.linkVertical().x(d => d.x).y(d => d.y));
        
        // Draw nodes
        const nodes = g.selectAll(".node")
            .data(root.descendants())
            .enter().append("g")
            .attr("class", "node")
            .attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        
        nodes.append("circle").attr("r", 10).attr("fill", "#3498db");
        nodes.append("text").attr("dy", "0.35em").attr("y", 15).text(d => d.data.name);
        
        // Add zoom
        const zoom = d3.zoom().on("zoom", (event) => g.attr("transform", event.transform));
        svg.call(zoom);
    </script>
</body>
</html>
            """
    
    def open_in_browser(self) -> None:
        """Open the generated HTML file in the default web browser"""
        if self.html_path.exists():
            webbrowser.open(f"file://{self.html_path.absolute()}")
        else:
            raise FileNotFoundError(f"HTML file not found: {self.html_path}") 