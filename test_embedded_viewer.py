#!/usr/bin/env python3
"""
Test the embedded HTML viewer to ensure it displays family tree content directly within the application
"""

import os
import sys
import tempfile
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_test_html():
    """Create a test HTML file with embedded family tree"""
    
    # Sample character data
    character_data = {
        'K001': {
            'name': 'John Doe',
            'birth_date': '1970-01-15',
            'death_date': '',
            'spouse_id': 'K002',
            'father_id': 'K003',
            'mother_id': 'K004'
        },
        'K002': {
            'name': 'Jane Doe',
            'birth_date': '1972-05-20',
            'death_date': '',
            'spouse_id': 'K001'
        },
        'K003': {
            'name': 'Robert Doe',
            'birth_date': '1945-03-10',
            'death_date': '2020-12-25',
            'spouse_id': 'K004'
        },
        'K004': {
            'name': 'Mary Doe',
            'birth_date': '1947-08-05',
            'death_date': '',
            'spouse_id': 'K003'
        }
    }
    
    # Create SVG content
    svg_content = '''<svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
        <!-- John Doe -->
        <g id="node1" class="node">
            <title>K001</title>
            <polygon fill="lightgray" stroke="black" points="100,50 250,50 250,120 100,120"/>
            <text x="175" y="75" text-anchor="middle" font-family="Arial" font-size="12">John Doe</text>
            <text x="175" y="90" text-anchor="middle" font-family="Arial" font-size="10">b. 1970-01-15</text>
            <text x="175" y="105" text-anchor="middle" font-family="Arial" font-size="10">m. Jane Doe</text>
        </g>
        
        <!-- Jane Doe -->
        <g id="node2" class="node">
            <title>K002</title>
            <polygon fill="lightgray" stroke="black" points="300,50 450,50 450,120 300,120"/>
            <text x="375" y="75" text-anchor="middle" font-family="Arial" font-size="12">Jane Doe</text>
            <text x="375" y="90" text-anchor="middle" font-family="Arial" font-size="10">b. 1972-05-20</text>
            <text x="375" y="105" text-anchor="middle" font-family="Arial" font-size="10">m. John Doe</text>
        </g>
        
        <!-- Robert Doe -->
        <g id="node3" class="node">
            <title>K003</title>
            <polygon fill="lightgray" stroke="black" points="50,200 200,200 200,270 50,270"/>
            <text x="125" y="225" text-anchor="middle" font-family="Arial" font-size="12">Robert Doe</text>
            <text x="125" y="240" text-anchor="middle" font-family="Arial" font-size="10">b. 1945-03-10</text>
            <text x="125" y="255" text-anchor="middle" font-family="Arial" font-size="10">d. 2020-12-25</text>
        </g>
        
        <!-- Mary Doe -->
        <g id="node4" class="node">
            <title>K004</title>
            <polygon fill="lightgray" stroke="black" points="250,200 400,200 400,270 250,270"/>
            <text x="325" y="225" text-anchor="middle" font-family="Arial" font-size="12">Mary Doe</text>
            <text x="325" y="240" text-anchor="middle" font-family="Arial" font-size="10">b. 1947-08-05</text>
            <text x="325" y="255" text-anchor="middle" font-family="Arial" font-size="10">m. Robert Doe</text>
        </g>
        
        <!-- Connection lines -->
        <line x1="175" y1="120" x2="175" y2="150" stroke="black" stroke-width="2"/>
        <line x1="375" y1="120" x2="375" y2="150" stroke="black" stroke-width="2"/>
        <line x1="175" y1="150" x2="375" y2="150" stroke="black" stroke-width="2"/>
        <line x1="275" y1="150" x2="275" y2="200" stroke="black" stroke-width="2"/>
        <line x1="125" y1="200" x2="325" y2="200" stroke="black" stroke-width="2"/>
    </svg>'''
    
    # Create HTML template
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test Family Tree</title>
    <style>
        body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; }}
        .container {{ display: flex; gap: 20px; }}
        .svg-container {{ flex: 1; }}
        .details {{ width: 300px; background: #f5f5f5; padding: 15px; border-radius: 8px; }}
        .node {{ cursor: pointer; }}
        .node:hover polygon {{ stroke: orange; stroke-width: 2; }}
        .node.selected polygon {{ stroke: #3498db; stroke-width: 3; }}
    </style>
</head>
<body>
    <h1>Test Family Tree</h1>
    <div class="container">
        <div class="svg-container">
            {svg_content}
        </div>
        <div class="details" id="details">
            <h3>Person Details</h3>
            <p>Click on a person in the family tree to see their details here.</p>
        </div>
    </div>
    
    <script>
        const characterData = {json.dumps(character_data, indent=2)};
        let selectedNode = null;
        
        document.addEventListener('DOMContentLoaded', function() {{
            const nodes = document.querySelectorAll('g.node');
            nodes.forEach(node => {{
                node.addEventListener('click', handleNodeClick);
            }});
        }});
        
        function handleNodeClick(event) {{
            // Remove previous selection
            if (selectedNode) {{
                selectedNode.classList.remove('selected');
            }}
            
            // Select new node
            selectedNode = event.currentTarget;
            selectedNode.classList.add('selected');
            
            // Get person ID
            const titleElement = selectedNode.querySelector('title');
            if (titleElement) {{
                const personId = titleElement.textContent.trim();
                showPersonDetails(personId);
            }}
        }}
        
        function showPersonDetails(personId) {{
            const personData = characterData[personId];
            const detailsDiv = document.getElementById('details');
            
            if (!personData) {{
                detailsDiv.innerHTML = `<h3>Person Not Found</h3><p>No data for ${{personId}}</p>`;
                return;
            }}
            
            const name = personData.name || 'Unknown';
            const birth = personData.birth_date || 'Unknown';
            const death = personData.death_date || '';
            const spouse = personData.spouse_id ? characterData[personData.spouse_id]?.name || personData.spouse_id : '';
            
            detailsDiv.innerHTML = `
                <h3>${{name}}</h3>
                <p><strong>ID:</strong> ${{personId}}</p>
                <p><strong>Birth:</strong> ${{birth}}</p>
                ${{death ? `<p><strong>Death:</strong> ${{death}}</p>` : ''}}
                ${{spouse ? `<p><strong>Spouse:</strong> ${{spouse}}</p>` : ''}}
            `;
        }}
    </script>
</body>
</html>'''
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        return f.name

def test_embedded_viewer():
    """Test the embedded HTML viewer with a simple family tree"""
    print("🧪 Testing Embedded HTML Viewer")
    print("=" * 40)
    
    try:
        # Create test HTML file
        html_path = create_test_html()
        print(f"✅ Created test HTML file: {html_path}")
        
        # Try to import the embedded HTML viewer
        from src.ui.widgets.embedded_html_viewer import EmbeddedHTMLViewer
        print("✅ Successfully imported EmbeddedHTMLViewer")
        
        # Test tkinter availability
        import tkinter as tk
        import customtkinter as ctk
        print("✅ Tkinter and CustomTkinter available")
        
        # Create a test window
        print("\n🚀 Creating test window...")
        print("This will open a window with the embedded family tree.")
        print("Try clicking on the people in the tree to see their details!")
        print("Close the window when done testing.")
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        root = ctk.CTk()
        root.title("Test Embedded HTML Viewer")
        root.geometry("900x600")
        
        # Create embedded viewer
        viewer = EmbeddedHTMLViewer(root)
        viewer.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Load the test HTML
        viewer.load_html_file(html_path)
        
        # Run the test
        root.mainloop()
        
        # Clean up
        os.unlink(html_path)
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_embedded_viewer() 