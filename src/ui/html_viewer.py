"""
HTML-based family tree viewer with JavaScript interactivity
"""
import os
import json
import webbrowser
from typing import Dict, Any, Optional
from pathlib import Path

class HTMLFamilyTreeViewer:
    """
    Generates interactive HTML family tree viewer with embedded SVG and JavaScript
    """
    
    def __init__(self, svg_path: str, character_data: Dict[str, Dict[str, Any]]):
        """
        Initialize the HTML viewer
        
        Args:
            svg_path: Path to the SVG file
            character_data: Dictionary mapping person IDs to their data
        """
        self.svg_path = Path(svg_path)
        self.character_data = character_data
        self.output_dir = self.svg_path.parent
        self.html_path = self.output_dir / f"{self.svg_path.stem}.html"
        
    def generate_html(self) -> str:
        """
        Generate the interactive HTML file
        
        Returns:
            str: Path to the generated HTML file
        """
        # Read SVG content
        with open(self.svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        
        # Generate HTML template
        html_content = self._create_html_template(svg_content)
        
        # Write HTML file
        with open(self.html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(self.html_path)
    
    def _create_html_template(self, svg_content: str) -> str:
        """Create the HTML template with embedded SVG and JavaScript"""
        
        # Convert character data to JSON for JavaScript
        character_json = json.dumps(self.character_data, indent=2)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Family Tree</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Arial', sans-serif;
            background: #f5f5f5;
            overflow: hidden;
        }}
        
        .container {{
            display: flex;
            height: 100vh;
        }}
        
        .svg-container {{
            flex: 1;
            position: relative;
            overflow: hidden;
            background: white;
        }}
        
        .svg-wrapper {{
            width: 100%;
            height: 100%;
            cursor: grab;
        }}
        
        .svg-wrapper:active {{
            cursor: grabbing;
        }}
        
        .sidebar {{
            width: 300px;
            background: #2c3e50;
            color: white;
            padding: 20px;
            overflow-y: auto;
            box-shadow: -2px 0 5px rgba(0,0,0,0.1);
        }}
        
        .sidebar h2 {{
            margin-top: 0;
            color: #ecf0f1;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        
        .person-info {{
            background: #34495e;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        
        .person-info h3 {{
            margin: 0 0 10px 0;
            color: #3498db;
        }}
        
        .person-info p {{
            margin: 5px 0;
            color: #ecf0f1;
        }}
        
        .toolbar {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 1000;
            background: rgba(52, 73, 94, 0.9);
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        
        .toolbar button {{
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 12px;
            margin: 0 5px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }}
        
        .toolbar button:hover {{
            background: #2980b9;
        }}
        
        .search-container {{
            margin-bottom: 20px;
        }}
        
        .search-input {{
            width: 100%;
            padding: 10px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            background: #34495e;
            color: white;
        }}
        
        .search-input::placeholder {{
            color: #bdc3c7;
        }}
        
        .search-results {{
            margin-top: 10px;
        }}
        
        .search-result {{
            padding: 8px;
            background: #34495e;
            margin: 5px 0;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.3s;
        }}
        
        .search-result:hover {{
            background: #3498db;
        }}
        
        /* SVG node styling */
        .node {{
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        
        .node:hover {{
            opacity: 0.8;
        }}
        
        .node.selected polygon {{
            stroke: #3498db !important;
            stroke-width: 3px !important;
            filter: drop-shadow(0 0 8px rgba(52, 152, 219, 0.6));
        }}
        
        .node.highlighted {{
            stroke: #f39c12 !important;
            stroke-width: 2px !important;
        }}
        
        .status {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(52, 73, 94, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="svg-container">
            <div class="toolbar">
                <button onclick="zoomIn()">Zoom In</button>
                <button onclick="zoomOut()">Zoom Out</button>
                <button onclick="resetView()">Reset View</button>
                <button onclick="fitToWindow()">Fit to Window</button>
            </div>
            
            <div class="svg-wrapper" id="svg-wrapper">
                {svg_content}
            </div>
            
            <div class="status" id="status">
                Click on a person to see details | Drag to pan | Scroll to zoom
            </div>
        </div>
        
        <div class="sidebar">
            <h2>Family Tree Navigator</h2>
            
            <div class="search-container">
                <input type="text" class="search-input" placeholder="Search family members..." 
                       onkeyup="searchPeople(this.value)" id="search-input">
                <div class="search-results" id="search-results"></div>
            </div>
            
            <div id="person-details">
                <div class="person-info">
                    <h3>Welcome!</h3>
                    <p>Click on any person in the family tree to see their details here.</p>
                    <p>Use the search box above to quickly find family members.</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Character data from Python
        const characterData = {character_json};
        
        // SVG and interaction state
        let currentZoom = 1;
        let currentTranslateX = 0;
        let currentTranslateY = 0;
        let isDragging = false;
        let dragStart = {{ x: 0, y: 0 }};
        let selectedNode = null;
        
        // Initialize the viewer
        document.addEventListener('DOMContentLoaded', function() {{
            initializeViewer();
        }});
        
        function initializeViewer() {{
            const svgWrapper = document.getElementById('svg-wrapper');
            const svg = svgWrapper.querySelector('svg');
            
            if (!svg) {{
                console.error('SVG not found');
                return;
            }}
            
            // Add event listeners to all nodes
            const nodes = svg.querySelectorAll('g.node');
            nodes.forEach(node => {{
                node.addEventListener('click', handleNodeClick);
                node.addEventListener('mouseenter', handleNodeHover);
                node.addEventListener('mouseleave', handleNodeLeave);
            }});
            
            // Add pan and zoom functionality
            svgWrapper.addEventListener('mousedown', startDrag);
            svgWrapper.addEventListener('mousemove', doDrag);
            svgWrapper.addEventListener('mouseup', endDrag);
            svgWrapper.addEventListener('wheel', handleWheel);
            
            // Fit to window initially
            setTimeout(() => fitToWindow(), 100);
        }}
        
        function handleNodeClick(event) {{
            event.stopPropagation();
            
            // Remove previous selection
            if (selectedNode) {{
                selectedNode.classList.remove('selected');
            }}
            
            // Select new node
            selectedNode = event.currentTarget;
            selectedNode.classList.add('selected');
            
            // Get person ID from title element
            const titleElement = selectedNode.querySelector('title');
            if (titleElement) {{
                const personId = titleElement.textContent.trim();
                showPersonDetails(personId);
                updateStatus(`Selected: ${{personId}}`);
            }}
        }}
        
        function handleNodeHover(event) {{
            const node = event.currentTarget;
            const titleElement = node.querySelector('title');
            if (titleElement) {{
                const personId = titleElement.textContent.trim();
                const personData = characterData[personId];
                if (personData) {{
                    updateStatus(`${{personData.name || personId}} - Click for details`);
                }}
            }}
        }}
        
        function handleNodeLeave(event) {{
            updateStatus('Click on a person to see details | Drag to pan | Scroll to zoom');
        }}
        
        function showPersonDetails(personId) {{
            const personData = characterData[personId];
            const detailsContainer = document.getElementById('person-details');
            
            if (!personData) {{
                detailsContainer.innerHTML = `
                    <div class="person-info">
                        <h3>Person Not Found</h3>
                        <p>No data available for ID: ${{personId}}</p>
                    </div>
                `;
                return;
            }}
            
            const name = personData.name || 'Unknown';
            const birthDate = personData.birth_date || 'Unknown';
            const deathDate = personData.death_date || '';
            const marriageDate = personData.marriage_date || '';
            const spouseId = personData.spouse_id || '';
            const fatherId = personData.father_id || '';
            const motherId = personData.mother_id || '';
            
            let spouseName = '';
            if (spouseId && characterData[spouseId]) {{
                spouseName = characterData[spouseId].name || spouseId;
            }}
            
            let fatherName = '';
            if (fatherId && characterData[fatherId]) {{
                fatherName = characterData[fatherId].name || fatherId;
            }}
            
            let motherName = '';
            if (motherId && characterData[motherId]) {{
                motherName = characterData[motherId].name || motherId;
            }}
            
            detailsContainer.innerHTML = `
                <div class="person-info">
                    <h3>${{name}}</h3>
                    <p><strong>ID:</strong> ${{personId}}</p>
                    <p><strong>Birth:</strong> ${{birthDate}}</p>
                    ${{deathDate ? `<p><strong>Death:</strong> ${{deathDate}}</p>` : ''}}
                    ${{marriageDate ? `<p><strong>Marriage:</strong> ${{marriageDate}}</p>` : ''}}
                    ${{spouseName ? `<p><strong>Spouse:</strong> ${{spouseName}}</p>` : ''}}
                    ${{fatherName ? `<p><strong>Father:</strong> ${{fatherName}}</p>` : ''}}
                    ${{motherName ? `<p><strong>Mother:</strong> ${{motherName}}</p>` : ''}}
                </div>
            `;
        }}
        
        function searchPeople(query) {{
            const resultsContainer = document.getElementById('search-results');
            
            if (!query.trim()) {{
                resultsContainer.innerHTML = '';
                return;
            }}
            
            const matches = [];
            for (const [id, person] of Object.entries(characterData)) {{
                const name = person.name || '';
                if (name.toLowerCase().includes(query.toLowerCase())) {{
                    matches.push({{ id, name }});
                }}
            }}
            
            if (matches.length === 0) {{
                resultsContainer.innerHTML = '<div class="search-result">No matches found</div>';
                return;
            }}
            
            resultsContainer.innerHTML = matches
                .slice(0, 10) // Limit to first 10 matches
                .map(match => `
                    <div class="search-result" onclick="selectPerson('${{match.id}}')">
                        ${{match.name}} (${{match.id}})
                    </div>
                `)
                .join('');
        }}
        
        function selectPerson(personId) {{
            // Find the node in the SVG
            const svg = document.querySelector('svg');
            const nodes = svg.querySelectorAll('g.node');
            
            for (const node of nodes) {{
                const titleElement = node.querySelector('title');
                if (titleElement && titleElement.textContent.trim() === personId) {{
                    // Simulate click on the node
                    handleNodeClick({{ currentTarget: node, stopPropagation: () => {{}} }});
                    
                    // Center the view on this node
                    centerOnNode(node);
                    break;
                }}
            }}
            
            // Clear search
            document.getElementById('search-input').value = '';
            document.getElementById('search-results').innerHTML = '';
        }}
        
        function centerOnNode(node) {{
            const svg = document.querySelector('svg');
            const svgWrapper = document.getElementById('svg-wrapper');
            const svgRect = svg.getBoundingClientRect();
            const wrapperRect = svgWrapper.getBoundingClientRect();
            
            // Get node bounding box
            const nodeRect = node.getBoundingClientRect();
            
            // Calculate center position
            const nodeCenterX = nodeRect.left + nodeRect.width / 2 - svgRect.left;
            const nodeCenterY = nodeRect.top + nodeRect.height / 2 - svgRect.top;
            
            // Calculate new translate to center the node
            const newTranslateX = (wrapperRect.width / 2) - (nodeCenterX * currentZoom);
            const newTranslateY = (wrapperRect.height / 2) - (nodeCenterY * currentZoom);
            
            currentTranslateX = newTranslateX;
            currentTranslateY = newTranslateY;
            
            applyTransform();
        }}
        
        // Zoom and Pan functionality
        function zoomIn() {{
            currentZoom *= 1.2;
            applyTransform();
            updateStatus(`Zoom: ${{Math.round(currentZoom * 100)}}%`);
        }}
        
        function zoomOut() {{
            currentZoom /= 1.2;
            if (currentZoom < 0.1) currentZoom = 0.1;
            applyTransform();
            updateStatus(`Zoom: ${{Math.round(currentZoom * 100)}}%`);
        }}
        
        function resetView() {{
            currentZoom = 1;
            currentTranslateX = 0;
            currentTranslateY = 0;
            applyTransform();
            updateStatus('View reset');
        }}
        
        function fitToWindow() {{
            const svg = document.querySelector('svg');
            const svgWrapper = document.getElementById('svg-wrapper');
            
            if (!svg) return;
            
            const svgRect = svg.getBoundingClientRect();
            const wrapperRect = svgWrapper.getBoundingClientRect();
            
            // Calculate zoom to fit
            const zoomX = wrapperRect.width / svgRect.width;
            const zoomY = wrapperRect.height / svgRect.height;
            currentZoom = Math.min(zoomX, zoomY, 1) * 0.9; // 90% of available space
            
            // Center the SVG
            const scaledWidth = svgRect.width * currentZoom;
            const scaledHeight = svgRect.height * currentZoom;
            
            currentTranslateX = (wrapperRect.width - scaledWidth) / 2;
            currentTranslateY = (wrapperRect.height - scaledHeight) / 2;
            
            applyTransform();
            updateStatus(`Fitted to window - Zoom: ${{Math.round(currentZoom * 100)}}%`);
        }}
        
        function applyTransform() {{
            const svg = document.querySelector('svg');
            if (svg) {{
                svg.style.transform = `translate(${{currentTranslateX}}px, ${{currentTranslateY}}px) scale(${{currentZoom}})`;
                svg.style.transformOrigin = '0 0';
            }}
        }}
        
        function startDrag(event) {{
            if (event.target.tagName === 'svg' || event.target.tagName === 'g') {{
                isDragging = true;
                dragStart.x = event.clientX;
                dragStart.y = event.clientY;
                event.preventDefault();
            }}
        }}
        
        function doDrag(event) {{
            if (isDragging) {{
                const deltaX = event.clientX - dragStart.x;
                const deltaY = event.clientY - dragStart.y;
                
                currentTranslateX += deltaX;
                currentTranslateY += deltaY;
                
                dragStart.x = event.clientX;
                dragStart.y = event.clientY;
                
                applyTransform();
            }}
        }}
        
        function endDrag(event) {{
            isDragging = false;
        }}
        
        function handleWheel(event) {{
            event.preventDefault();
            
            const zoomFactor = event.deltaY > 0 ? 0.9 : 1.1;
            const newZoom = currentZoom * zoomFactor;
            
            if (newZoom < 0.1 || newZoom > 10) return;
            
            // Zoom relative to mouse position
            const svgWrapper = document.getElementById('svg-wrapper');
            const rect = svgWrapper.getBoundingClientRect();
            const mouseX = event.clientX - rect.left;
            const mouseY = event.clientY - rect.top;
            
            const scaleFactor = newZoom / currentZoom;
            currentTranslateX = mouseX - (mouseX - currentTranslateX) * scaleFactor;
            currentTranslateY = mouseY - (mouseY - currentTranslateY) * scaleFactor;
            currentZoom = newZoom;
            
            applyTransform();
            updateStatus(`Zoom: ${{Math.round(currentZoom * 100)}}%`);
        }}
        
        function updateStatus(message) {{
            const statusElement = document.getElementById('status');
            if (statusElement) {{
                statusElement.textContent = message;
            }}
        }}
    </script>
</body>
</html>
        """
        
        return html_template.strip()
    
    def open_in_browser(self) -> None:
        """Open the generated HTML file in the default web browser"""
        if self.html_path.exists():
            webbrowser.open(f"file://{self.html_path.absolute()}")
        else:
            raise FileNotFoundError(f"HTML file not found: {self.html_path}") 