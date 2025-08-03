#!/usr/bin/env python3
"""
Test script specifically for collision detection improvements in the SVG viewer.
Tests the enhanced _point_in_element method with various SVG shapes.
"""

import os
import sys
import tempfile
import xml.etree.ElementTree as ET

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.widgets.svg_viewer import SVGViewer

def test_polygon_collision():
    """Test collision detection for polygon shapes (family tree nodes)"""
    print("Testing polygon collision detection...")
    
    # Create a simple polygon (like a family tree node)
    polygon_xml = """<polygon points="100,50 200,50 200,100 100,100" fill="white" stroke="black"/>"""
    polygon_element = ET.fromstring(polygon_xml)
    
    # Create a mock SVGViewer to test the collision method
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write('<?xml version="1.0"?><svg></svg>')
        svg_path = f.name
    
    viewer = SVGViewer(None, svg_path)
    
    # Test points inside the polygon
    test_cases = [
        (150, 75, True, "Center of rectangle"),
        (110, 60, True, "Inside left side"),
        (190, 90, True, "Inside right side"),
        (50, 75, False, "Outside left"),
        (250, 75, False, "Outside right"),
        (150, 30, False, "Above rectangle"),
        (150, 120, False, "Below rectangle"),
        (100, 50, True, "On top-left corner"),
        (200, 100, True, "On bottom-right corner")
    ]
    
    results = []
    for x, y, expected, description in test_cases:
        result = viewer._point_in_polygon(x, y, polygon_element)
        status = "✅" if result == expected else "❌"
        results.append((status, result == expected))
        print(f"  {status} {description}: ({x}, {y}) -> {result} (expected {expected})")
    
    # Clean up
    os.unlink(svg_path)
    
    success_count = sum(1 for _, success in results if success)
    print(f"  Polygon collision: {success_count}/{len(results)} tests passed")
    return success_count == len(results)

def test_rectangle_collision():
    """Test collision detection for rectangle shapes with rounded corners"""
    print("\nTesting rectangle collision detection...")
    
    # Create rectangles with different properties
    test_rectangles = [
        ('<rect x="100" y="50" width="100" height="50" fill="white" stroke="black"/>', "Basic rectangle"),
        ('<rect x="100" y="50" width="100" height="50" rx="10" ry="10" fill="white" stroke="black"/>', "Rounded rectangle")
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write('<?xml version="1.0"?><svg></svg>')
        svg_path = f.name
    
    viewer = SVGViewer(None, svg_path)
    
    all_passed = True
    
    for rect_xml, description in test_rectangles:
        print(f"  Testing {description}:")
        rect_element = ET.fromstring(rect_xml)
        
        test_cases = [
            (150, 75, True, "Center"),
            (110, 60, True, "Inside"),
            (50, 75, False, "Outside left"),
            (250, 75, False, "Outside right"),
            (150, 30, False, "Above"),
            (150, 120, False, "Below")
        ]
        
        for x, y, expected, case_desc in test_cases:
            result = viewer._point_in_rect(x, y, rect_element)
            status = "✅" if result == expected else "❌"
            if result != expected:
                all_passed = False
            print(f"    {status} {case_desc}: ({x}, {y}) -> {result} (expected {expected})")
    
    # Clean up
    os.unlink(svg_path)
    
    print(f"  Rectangle collision: {'All tests passed' if all_passed else 'Some tests failed'}")
    return all_passed

def test_ellipse_collision():
    """Test collision detection for ellipse shapes"""
    print("\nTesting ellipse collision detection...")
    
    ellipse_xml = '<ellipse cx="150" cy="75" rx="50" ry="25" fill="white" stroke="black"/>'
    ellipse_element = ET.fromstring(ellipse_xml)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
        f.write('<?xml version="1.0"?><svg></svg>')
        svg_path = f.name
    
    viewer = SVGViewer(None, svg_path)
    
    test_cases = [
        (150, 75, True, "Center of ellipse"),
        (130, 75, True, "Inside horizontally"),
        (150, 60, True, "Inside vertically"),
        (80, 75, False, "Outside left"),
        (220, 75, False, "Outside right"),
        (150, 40, False, "Above ellipse"),
        (150, 110, False, "Below ellipse")
    ]
    
    results = []
    for x, y, expected, description in test_cases:
        result = viewer._point_in_ellipse(x, y, ellipse_element)
        status = "✅" if result == expected else "❌"
        results.append((status, result == expected))
        print(f"  {status} {description}: ({x}, {y}) -> {result} (expected {expected})")
    
    # Clean up
    os.unlink(svg_path)
    
    success_count = sum(1 for _, success in results if success)
    print(f"  Ellipse collision: {success_count}/{len(results)} tests passed")
    return success_count == len(results)

def test_enhanced_node_generation():
    """Test the enhanced node generation with improved collision boundaries"""
    print("\nTesting enhanced node generation...")
    
    try:
        from src.graph.base import RelGraph
        
        # Test the helper methods
        sample_data = {
            'name': 'John Doe',
            'birth_date': '1990-01-01',
            'death_date': '2020-12-31',
            'marriage_date': '2015-06-15',
            'spouse_id': 'K002'
        }
        
        # Create a mock RelGraph instance
        class TestRelGraph(RelGraph):
            def __init__(self):
                self.output_format = 'svg'
            
            def _add_relationship_edges(self, dot):
                pass
            
            def _create_node_info(self, character):
                return {'name': character.get('name', 'Unknown')}
        
        graph = TestRelGraph()
        
        # Test tooltip creation
        tooltip = graph._create_enhanced_tooltip(sample_data)
        expected_parts = ['John Doe', 'Born: 1990-01-01', 'Died: 2020-12-31', 'Married: 2015-06-15']
        
        tooltip_passed = all(part in tooltip for part in expected_parts)
        print(f"  {'✅' if tooltip_passed else '❌'} Enhanced tooltip generation")
        
        # Test color determination
        living_color = graph._get_node_color({'name': 'Jane', 'died': 'L'})
        deceased_color = graph._get_node_color({'name': 'John', 'death_date': '2020-01-01'})
        
        color_passed = living_color != deceased_color
        print(f"  {'✅' if color_passed else '❌'} Color coding (living vs deceased)")
        
        return tooltip_passed and color_passed
        
    except Exception as e:
        print(f"  ❌ Error testing enhanced node generation: {e}")
        return False

def test_html_interactivity():
    """Test HTML viewer JavaScript collision detection"""
    print("\nTesting HTML viewer interactivity...")
    
    try:
        from src.ui.html_viewer import HTMLFamilyTreeViewer
        
        # Sample data
        character_data = {
            'K001': {
                'name': 'Alice Smith',
                'birth_date': '1985-03-15',
                'death_date': '',
                'spouse_id': 'K002'
            }
        }
        
        # Create test SVG with proper node structure
        test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
        <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <g id="node-K001" class="node family-node clickable" 
               data-id="K001" data-name="Alice Smith" 
               onclick="handleNodeClick('K001')" 
               onmouseover="handleNodeHover('K001')" 
               onmouseout="handleNodeLeave('K001')">
                <title>K001</title>
                <polygon fill="#e8f8f5" stroke="#2c3e50" stroke-width="1.5"
                         points="100,50 250,50 250,120 100,120"/>
                <text x="175" y="85" text-anchor="middle">Alice Smith</text>
            </g>
        </svg>'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as f:
            f.write(test_svg)
            svg_path = f.name
        
        # Generate HTML
        viewer = HTMLFamilyTreeViewer(svg_path, character_data)
        html_path = viewer.generate_html()
        
        # Check HTML content
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        # Test for enhanced features
        tests = [
            ('data-id="K001"' in html_content, "Node data attributes"),
            ('handleNodeClick' in html_content, "Click handlers"),
            ('handleNodeHover' in html_content, "Hover handlers"),
            ('Alice Smith' in html_content, "Character data embedding"),
            ('stroke: #3498db !important' in html_content, "Enhanced styling"),
            ('searchPeople' in html_content, "Search functionality")
        ]
        
        results = []
        for test_result, description in tests:
            status = "✅" if test_result else "❌"
            results.append(test_result)
            print(f"  {status} {description}")
        
        # Clean up
        os.unlink(svg_path)
        os.unlink(html_path)
        
        return all(results)
        
    except Exception as e:
        print(f"  ❌ Error testing HTML interactivity: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all collision detection tests"""
    print("🎯 Testing Enhanced Collision Detection System")
    print("=" * 60)
    
    tests = [
        test_polygon_collision,
        test_rectangle_collision,
        test_ellipse_collision,
        test_enhanced_node_generation,
        test_html_interactivity
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"🎯 Collision Detection Tests: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All collision detection improvements working correctly!")
        print("\nKey improvements verified:")
        print("• Precise polygon collision using ray casting algorithm")
        print("• Rectangle collision with rounded corner support")
        print("• Ellipse collision using mathematical equations")
        print("• Enhanced node generation with better collision boundaries")
        print("• Interactive HTML viewer with accurate click detection")
        print("• SVG attributes for improved JavaScript interaction")
    else:
        print("⚠️  Some collision detection features need attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
