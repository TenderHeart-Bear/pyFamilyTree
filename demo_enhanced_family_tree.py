#!/usr/bin/env python3
"""
Comprehensive demonstration of the enhanced pyFamilyTree application.
Shows all the collision detection and interactivity improvements.
"""

import os
import sys
import tempfile
import webbrowser
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def create_sample_family_data():
    """Create sample family data for demonstration"""
    return {
        'K001': {
            'name': 'Robert Smith',
            'birth_date': '1950-05-15',
            'death_date': '2020-03-10',
            'marriage_date': '1975-08-20',
            'spouse_id': 'K002',
            'father_id': 'K005',
            'mother_id': 'K006'
        },
        'K002': {
            'name': 'Mary Johnson',
            'birth_date': '1952-09-03',
            'death_date': '',
            'marriage_date': '1975-08-20',
            'spouse_id': 'K001',
            'father_id': 'K007',
            'mother_id': 'K008'
        },
        'K003': {
            'name': 'John Smith',
            'birth_date': '1976-12-25',
            'death_date': '',
            'marriage_date': '2005-06-15',
            'spouse_id': 'K004',
            'father_id': 'K001',
            'mother_id': 'K002'
        },
        'K004': {
            'name': 'Sarah Williams',
            'birth_date': '1980-02-14',
            'death_date': '',
            'marriage_date': '2005-06-15',
            'spouse_id': 'K003',
            'father_id': 'K009',
            'mother_id': 'K010'
        },
        'K005': {
            'name': 'Thomas Smith',
            'birth_date': '1925-01-01',
            'death_date': '1995-07-20',
            'marriage_date': '1948-05-10',
            'spouse_id': 'K006'
        },
        'K006': {
            'name': 'Helen Brown',
            'birth_date': '1928-11-30',
            'death_date': '2010-12-05',
            'marriage_date': '1948-05-10',
            'spouse_id': 'K005'
        }
    }

def create_enhanced_svg_demo():
    """Create a demo SVG with enhanced collision detection features"""
    
    family_data = create_sample_family_data()
    
    # Create SVG with enhanced nodes
    svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <style>
      .family-node { cursor: pointer; transition: all 0.2s ease; }
      .family-node:hover { filter: brightness(1.1); }
      .family-node.selected { stroke: #3498db; stroke-width: 3px; }
      .living { fill: #e8f8f5; }
      .deceased { fill: #ecf0f1; }
      .edge { stroke: #2c3e50; stroke-width: 2px; fill: none; }
    </style>
  </defs>
  
  <!-- Grandparents Generation -->
  <g id="node-K005" class="family-node" data-id="K005" data-name="Thomas Smith" 
     onclick="handleNodeClick('K005')" onmouseover="handleNodeHover('K005')" onmouseout="handleNodeLeave('K005')">
    <title>K005</title>
    <rect x="50" y="50" width="120" height="80" rx="10" ry="10" 
          class="deceased" stroke="#2c3e50" stroke-width="1.5"/>
    <text x="110" y="75" text-anchor="middle" font-family="Arial" font-size="12">Thomas Smith</text>
    <text x="110" y="90" text-anchor="middle" font-family="Arial" font-size="10">★ 1925</text>
    <text x="110" y="105" text-anchor="middle" font-family="Arial" font-size="10">✝ 1995</text>
  </g>
  
  <g id="node-K006" class="family-node" data-id="K006" data-name="Helen Brown"
     onclick="handleNodeClick('K006')" onmouseover="handleNodeHover('K006')" onmouseout="handleNodeLeave('K006')">
    <title>K006</title>
    <rect x="200" y="50" width="120" height="80" rx="10" ry="10" 
          class="deceased" stroke="#2c3e50" stroke-width="1.5"/>
    <text x="260" y="75" text-anchor="middle" font-family="Arial" font-size="12">Helen Brown</text>
    <text x="260" y="90" text-anchor="middle" font-family="Arial" font-size="10">★ 1928</text>
    <text x="260" y="105" text-anchor="middle" font-family="Arial" font-size="10">✝ 2010</text>
  </g>
  
  <!-- Parents Generation -->
  <g id="node-K001" class="family-node" data-id="K001" data-name="Robert Smith"
     onclick="handleNodeClick('K001')" onmouseover="handleNodeHover('K001')" onmouseout="handleNodeLeave('K001')">
    <title>K001</title>
    <rect x="50" y="200" width="120" height="80" rx="10" ry="10" 
          class="deceased" stroke="#2c3e50" stroke-width="1.5"/>
    <text x="110" y="220" text-anchor="middle" font-family="Arial" font-size="12">Robert Smith</text>
    <text x="110" y="235" text-anchor="middle" font-family="Arial" font-size="10">★ 1950</text>
    <text x="110" y="250" text-anchor="middle" font-family="Arial" font-size="10">✝ 2020</text>
    <text x="110" y="265" text-anchor="middle" font-family="Arial" font-size="10">♥ 1975</text>
  </g>
  
  <g id="node-K002" class="family-node" data-id="K002" data-name="Mary Johnson"
     onclick="handleNodeClick('K002')" onmouseover="handleNodeHover('K002')" onmouseout="handleNodeLeave('K002')">
    <title>K002</title>
    <rect x="200" y="200" width="120" height="80" rx="10" ry="10" 
          class="living" stroke="#2c3e50" stroke-width="1.5"/>
    <text x="260" y="220" text-anchor="middle" font-family="Arial" font-size="12">Mary Johnson</text>
    <text x="260" y="235" text-anchor="middle" font-family="Arial" font-size="10">★ 1952</text>
    <text x="260" y="250" text-anchor="middle" font-family="Arial" font-size="10">♥ 1975</text>
  </g>
  
  <!-- Children Generation -->
  <g id="node-K003" class="family-node" data-id="K003" data-name="John Smith"
     onclick="handleNodeClick('K003')" onmouseover="handleNodeHover('K003')" onmouseout="handleNodeLeave('K003')">
    <title>K003</title>
    <ellipse cx="110" cy="390" rx="60" ry="40" 
             class="living" stroke="#2c3e50" stroke-width="1.5"/>
    <text x="110" y="385" text-anchor="middle" font-family="Arial" font-size="12">John Smith</text>
    <text x="110" y="400" text-anchor="middle" font-family="Arial" font-size="10">★ 1976</text>
  </g>
  
  <g id="node-K004" class="family-node" data-id="K004" data-name="Sarah Williams"
     onclick="handleNodeClick('K004')" onmouseover="handleNodeHover('K004')" onmouseout="handleNodeLeave('K004')">
    <title>K004</title>
    <ellipse cx="260" cy="390" rx="60" ry="40" 
             class="living" stroke="#2c3e50" stroke-width="1.5"/>
    <text x="260" y="385" text-anchor="middle" font-family="Arial" font-size="12">Sarah Williams</text>
    <text x="260" y="400" text-anchor="middle" font-family="Arial" font-size="10">★ 1980</text>
  </g>
  
  <!-- Family Relationships -->
  <line x1="110" y1="130" x2="110" y2="200" class="edge"/>
  <line x1="260" y1="130" x2="260" y2="200" class="edge"/>
  <line x1="170" y1="240" x2="200" y2="240" class="edge"/>
  <line x1="110" y1="280" x2="110" y2="350" class="edge"/>
  <line x1="260" y1="280" x2="260" y2="350" class="edge"/>
  <line x1="170" y1="390" x2="200" y2="390" class="edge"/>
  
  <!-- Marriage indicators -->
  <circle cx="185" cy="240" r="3" fill="#e74c3c"/>
  <circle cx="185" cy="390" r="3" fill="#e74c3c"/>
</svg>'''
    
    return svg_content, family_data

def demo_collision_detection():
    """Demonstrate the collision detection system"""
    print("🎯 Demonstrating Enhanced Collision Detection")
    print("=" * 50)
    
    svg_content, family_data = create_enhanced_svg_demo()
    
    # Save SVG to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write(svg_content)
        svg_path = f.name
    
    print(f"✅ Created enhanced SVG family tree: {svg_path}")
    
    # Test the SVG viewer collision detection
    try:
        from src.ui.widgets.svg_viewer import SVGViewer
        
        print("✅ SVG viewer with precise collision detection loaded")
        print("   • Polygon collision using ray casting algorithm")
        print("   • Rectangle collision with rounded corners")
        print("   • Ellipse collision using mathematical equations")
        print("   • Edge case handling for boundary points")
        
    except Exception as e:
        print(f"❌ Error loading SVG viewer: {e}")
    
    # Create HTML viewer with enhanced interactivity
    try:
        from src.ui.html_viewer import HTMLFamilyTreeViewer
        
        html_viewer = HTMLFamilyTreeViewer(svg_path, family_data)
        html_path = html_viewer.generate_html()
        
        print(f"✅ Generated interactive HTML viewer: {html_path}")
        print("   • Precise click detection on family tree nodes")
        print("   • Enhanced hover effects with tooltips")
        print("   • Search functionality for family members")
        print("   • Zoom and pan with collision-aware interaction")
        
        return html_path, svg_path
        
    except Exception as e:
        print(f"❌ Error creating HTML viewer: {e}")
        return None, svg_path

def demo_enhanced_nodes():
    """Demonstrate enhanced node generation"""
    print("\n🌟 Demonstrating Enhanced Node Generation")
    print("=" * 50)
    
    try:
        from src.graph.base import RelGraph
        
        # Create a mock graph to test node generation
        class DemoRelGraph(RelGraph):
            def __init__(self):
                self.output_format = 'svg'
                self.characters = create_sample_family_data()
            
            def _add_relationship_edges(self, dot):
                pass
            
            def _create_node_info(self, character):
                return {'name': character.get('name', 'Unknown')}
        
        graph = DemoRelGraph()
        
        print("✅ Enhanced node features:")
        
        # Test different node types
        test_cases = [
            ('K001', 'Deceased person with full information'),
            ('K002', 'Living person with marriage info'),
            ('K003', 'Younger generation living person')
        ]
        
        for char_id, description in test_cases:
            char_data = graph.characters[char_id]
            tooltip = graph._create_enhanced_tooltip(char_data)
            color = graph._get_node_color(char_data)
            
            print(f"   • {description}")
            print(f"     - Color: {color}")
            print(f"     - Tooltip: {tooltip[:60]}...")
        
        print("\n✅ Node enhancements include:")
        print("   • Visual symbols: ★ birth, ✝ death, ♥ marriage")
        print("   • Color coding: living (green tint) vs deceased (gray)")
        print("   • Comprehensive tooltips with all available data")
        print("   • Consistent sizing for accurate collision detection")
        print("   • SVG attributes for JavaScript interactivity")
        
    except Exception as e:
        print(f"❌ Error demonstrating enhanced nodes: {e}")

def demo_interactive_features():
    """Demonstrate interactive features"""
    print("\n⚡ Interactive Features Demonstration")
    print("=" * 50)
    
    print("✅ HTML Viewer Interactive Features:")
    print("   • Click Detection: Precise collision detection on all node shapes")
    print("   • Hover Effects: Enhanced tooltips and visual feedback")
    print("   • Search System: Find family members by name instantly")
    print("   • Navigation: Zoom, pan, and center on selected nodes")
    print("   • Responsive Design: Works on different screen sizes")
    print("   • Modern UI: Clean interface with dark sidebar")
    print("   • Detailed Info Panel: Shows comprehensive person details")
    
    print("\n✅ SVG Viewer Features:")
    print("   • Tkinter Integration: Native desktop application support")
    print("   • Precise Collision: Accurate mouse interaction on complex shapes")
    print("   • Zoom Controls: Mathematical scaling with maintained precision")
    print("   • Pan Support: Smooth navigation of large family trees")
    print("   • Info Display: Real-time node information updates")

def main():
    """Run the comprehensive demonstration"""
    print("🌳 pyFamilyTree - Enhanced Collision Detection Demo")
    print("=" * 60)
    print("This demonstration shows all the collision detection and")
    print("interactivity improvements made to the family tree application.")
    print()
    
    # Demo collision detection
    html_path, svg_path = demo_collision_detection()
    
    # Demo enhanced nodes
    demo_enhanced_nodes()
    
    # Demo interactive features
    demo_interactive_features()
    
    print("\n" + "=" * 60)
    print("🎉 Demonstration Complete!")
    
    if html_path:
        print(f"\n📂 Generated Files:")
        print(f"   • Interactive HTML: {html_path}")
        print(f"   • Enhanced SVG: {svg_path}")
        
        print(f"\n🌐 Opening interactive demo in browser...")
        try:
            webbrowser.open(f"file://{Path(html_path).absolute()}")
            print("✅ Demo opened in your default web browser")
            print("\nTry these features in the browser:")
            print("• Click on family members to see detailed information")
            print("• Use the search box to find specific people")
            print("• Zoom in/out and pan around the family tree")
            print("• Notice the precise click detection on all shapes")
            print("• Hover over nodes to see enhanced tooltips")
        except Exception as e:
            print(f"❌ Could not open browser: {e}")
            print(f"Manual opening: Open {html_path} in your browser")
    
    print(f"\n🚀 Key Improvements Summary:")
    print("• Ray casting algorithm for polygon collision detection")
    print("• Mathematical equations for ellipse and rounded rectangle collision")
    print("• Enhanced node generation with visual symbols and color coding")
    print("• Interactive HTML viewer with modern UI and search functionality")
    print("• Precise coordinate mapping between SVG and screen coordinates")
    print("• Edge case handling for boundary points and floating-point precision")
    
    # Clean up
    input("\nPress Enter to clean up temporary files...")
    try:
        if html_path:
            os.unlink(html_path)
        os.unlink(svg_path)
        print("✅ Temporary files cleaned up")
    except Exception as e:
        print(f"⚠️  Could not clean up some files: {e}")

if __name__ == "__main__":
    main()
