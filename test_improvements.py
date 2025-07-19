#!/usr/bin/env python3
"""
Test script to verify the improvements to the family tree application:
1. Embedded web viewer within the application
2. Improved node styling (border instead of red text)
"""

import os
import sys
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_html_viewer():
    """Test the HTML viewer functionality"""
    print("Testing HTML viewer...")
    
    try:
        from src.ui.html_viewer import HTMLFamilyTreeViewer
        
        # Sample character data
        character_data = {
            'K001': {
                'name': 'Test Person',
                'birth_date': '1990-01-01',
                'death_date': '',
                'spouse_id': 'K002',
                'father_id': 'K003',
                'mother_id': 'K004'
            },
            'K002': {
                'name': 'Test Spouse',
                'birth_date': '1992-05-15',
                'death_date': '',
                'spouse_id': 'K001'
            }
        }
        
        # Create a simple SVG for testing
        simple_svg = '''<?xml version="1.0" encoding="UTF-8"?>
        <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <g id="node1" class="node">
                <title>K001</title>
                <polygon fill="white" stroke="black" points="100,50 200,50 200,100 100,100"/>
                <text x="150" y="75" text-anchor="middle">Test Person</text>
            </g>
            <g id="node2" class="node">
                <title>K002</title>
                <polygon fill="white" stroke="black" points="250,50 350,50 350,100 250,100"/>
                <text x="300" y="75" text-anchor="middle">Test Spouse</text>
            </g>
        </svg>'''
        
        # Create temporary SVG file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(simple_svg)
            svg_path = f.name
        
        # Create HTML viewer
        html_viewer = HTMLFamilyTreeViewer(svg_path, character_data)
        html_path = html_viewer.generate_html()
        
        print(f"✅ HTML viewer created successfully")
        print(f"   SVG file: {svg_path}")
        print(f"   HTML file: {html_path}")
        
        # Check if HTML file exists and has content
        if os.path.exists(html_path):
            with open(html_path, 'r') as f:
                content = f.read()
                
            # Check for improved styling
            if 'stroke: #3498db !important' in content:
                print("✅ Improved node styling detected (blue border)")
            else:
                print("❌ Old styling detected (red text)")
                
            # Check for required JavaScript functions
            if 'handleNodeClick' in content and 'searchPeople' in content:
                print("✅ JavaScript interactivity functions present")
            else:
                print("❌ Missing JavaScript functions")
                
            # Check for character data
            if 'Test Person' in content:
                print("✅ Character data embedded correctly")
            else:
                print("❌ Character data not found")
                
        else:
            print("❌ HTML file not created")
            
        # Clean up
        os.unlink(svg_path)
        os.unlink(html_path)
        
    except Exception as e:
        print(f"❌ Error testing HTML viewer: {e}")
        import traceback
        traceback.print_exc()

def test_web_viewer():
    """Test the web viewer widget"""
    print("\nTesting web viewer widget...")
    
    try:
        from src.ui.widgets.web_viewer import SimpleWebViewer
        
        # Try to import tkinter
        import tkinter as tk
        import customtkinter as ctk
        
        print("✅ Web viewer widget imported successfully")
        print("✅ Tkinter and CustomTkinter available")
        
        # Check if pywebview is available
        try:
            import webview
            print("✅ pywebview library available for enhanced embedding")
        except ImportError:
            print("ℹ️  pywebview not available, will use fallback viewer")
            
    except Exception as e:
        print(f"❌ Error testing web viewer: {e}")
        import traceback
        traceback.print_exc()

def test_graph_integration():
    """Test the graph integration with HTML output"""
    print("\nTesting graph integration...")
    
    try:
        from src.graph.base import RelGraph
        from src.graph.family import FamilyTreeGraph
        
        print("✅ Graph classes imported successfully")
        
        # Check if generate_graph method supports HTML format
        import inspect
        sig = inspect.signature(FamilyTreeGraph.generate_graph)
        params = list(sig.parameters.keys())
        
        if 'file_format' in params:
            print("✅ Graph classes support file_format parameter")
        else:
            print("❌ Graph classes missing file_format parameter")
            
    except Exception as e:
        print(f"❌ Error testing graph integration: {e}")

def main():
    """Run all tests"""
    print("🧪 Testing Family Tree Application Improvements")
    print("=" * 50)
    
    test_html_viewer()
    test_web_viewer()
    test_graph_integration()
    
    print("\n" + "=" * 50)
    print("✅ Testing completed!")
    print("\nImprovements Summary:")
    print("• Embedded web viewer within application")
    print("• Improved node styling (blue border instead of red text)")
    print("• Fallback to external browser if embedded viewer fails")
    print("• Enhanced JavaScript interactivity")
    print("• Better user experience with modern web interface")

if __name__ == "__main__":
    main() 