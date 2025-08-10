"""
main.py
Main entry point for the family tree visualization tool.
"""
import os
import datetime
from src.graph.family import FamilyTreeGraph
from src.graph.embedded_family import EmbeddedFamilyTreeGraph
from src.graph.d3_family import D3FamilyTreeGraph
from src.data.excel_converter import create_xml_from_excel_sheet, select_excel_file_and_sheet
from src.data.xml_parser import FamilyTreeData
from typing import Optional
import subprocess

# Default output format is now SVG for interactivity
DEFAULT_OUTPUT_FORMAT = "svg"

def main():
    """Main function to run the family tree visualization tool."""
    # Get data directory
    print("\nChoose data source:")
    print("1. FamilyTree_TestData/TenGen (test data)")
    print("2. Family Records-MasterV2/Kearnan Family (real family data)")
    
    data_choice = input("Enter your choice (1 or 2): ").strip()
    if data_choice == "1":
        xml_data_dir = "assets/FamilyTree_TestData/TenGen"
    elif data_choice == "2":
        xml_data_dir = "assets/Family Records-MasterV2/Kearnan Family"
    else:
        print("Invalid data choice. Using Kearnan Family data by default.")
        xml_data_dir = "assets/Family Records-MasterV2/Kearnan Family"

    # Create output directory
    output_dir = f"out/family_tree_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if XML data already exists
    if not os.path.exists(xml_data_dir):
        print(f"XML data directory not found: {xml_data_dir}")
        print("Please ensure the data directory exists and contains XML files.")
        return
    
    print(f"\nUsing existing XML data from: {xml_data_dir}")
    
    # Get visualization style
    print("\nChoose visualization style:")
    print("1. Classic (dotted lines between spouses)")
    print("2. Embedded (spouses connected with diamond nodes)")
    print("3. D3.js Interactive (best for large trees)")
    
    style_choice = input("Enter your choice (1, 2, or 3): ").strip()
    if style_choice not in ["1", "2", "3"]:
        print("Invalid style choice. Please enter 1, 2, or 3. Exiting.")
        return

    # Get output format
    print("\nChoose output format:")
    print("1. SVG (interactive, recommended)")
    print("2. PDF")
    print("3. PNG")
    
    format_choice = input("Enter your choice (1-3) [default: 1]: ").strip() or "1"
    if format_choice not in ["1", "2", "3"]:
        print("Invalid format choice. Defaulting to SVG.")
        format_choice = "1"
    
    output_format = {
        "1": "svg",
        "2": "pdf",
        "3": "png"
    }[format_choice]

    # Initialize the family tree data
    family_data = FamilyTreeData(xml_data_dir)
    if not family_data.characters_by_id:
        print("No character data found. Exiting.")
        return
    
    # Get visualization parameters from user
    visualization_params = get_visualization_parameters()
    if not visualization_params:
        return

    start_person, generations_back, generations_forward, style_choice, output_format = visualization_params

    # Initialize and generate the family tree based on chosen style
    family_tree = create_family_tree(
        xml_data_dir=xml_data_dir,
        output_dir=output_dir,
        start_person=start_person,
        generations_back=generations_back,
        generations_forward=generations_forward,
        style_choice=style_choice,
        output_format=output_format
    )
    
    if family_tree:
        # The original code had a check for family_tree.characters, but the new create_family_tree
        # does not return a graph instance with a 'characters' attribute.
        # The new code returns the output_path.
        # Assuming the intent was to check if the output_path was generated.
        # Since the new code returns the output_path, we can check if it's not None.
        if family_tree:
            print(f"\nFamily tree visualization saved to: {family_tree}")
            if output_format == "svg":
                print("SVG file generated successfully. You can now open it in a web browser for interactive features.")
    else:
        print("No characters to graph. Exiting.")

def get_visualization_parameters():
    """
    Get visualization parameters from user input.
    
    Returns:
        tuple: (start_person, generations_back, generations_forward, style_choice, output_format)
        or None if input is invalid
    """
    # Get starting person
    start_person = input("\nEnter the name of the person to start from (or press Enter for complete tree): ").strip()
    
    # Get generation limits if starting from a specific person
    generations_back = 0
    generations_forward = 0
    if start_person:
        try:
            generations_back = int(input("How many generations back? "))
            generations_forward = int(input("How many generations forward? "))
            if generations_back < 0 or generations_forward < 0:
                print("Generations cannot be negative. Exiting.")
                return None
        except ValueError:
            print("Invalid input for generations. Please enter numbers only. Exiting.")
            return None

    # Get visualization style
    print("\nChoose visualization style:")
    print("1. Classic (dotted lines between spouses)")
    print("2. Embedded (spouses connected with diamond nodes)")
    print("3. D3.js Interactive (best for large trees)")
    
    style_choice = input("Enter your choice (1, 2, or 3): ").strip()
    if style_choice not in ["1", "2", "3"]:
        print("Invalid style choice. Please enter 1, 2, or 3. Exiting.")
        return None

    # Get output format
    print("\nChoose output format:")
    print("1. SVG (interactive, recommended)")
    print("2. PDF")
    print("3. PNG")
    
    format_choice = input("Enter your choice (1-3) [default: 1]: ").strip() or "1"
    if format_choice not in ["1", "2", "3"]:
        print("Invalid format choice. Defaulting to SVG.")
        format_choice = "1"
    
    output_format = {
        "1": "svg",
        "2": "pdf",
        "3": "png"
    }[format_choice]

    return start_person, generations_back, generations_forward, style_choice, output_format

def create_family_tree(xml_data_dir: str, output_dir: str, start_person: Optional[str], 
                      generations_back: int, generations_forward: int, 
                      style_choice: str, output_format: str) -> Optional[str]:
    """
    Create a family tree visualization based on the chosen style.
    
    Args:
        xml_data_dir: Directory containing XML data files
        output_dir: Directory to save output files
        start_person: Optional name of person to start from
        generations_back: Number of generations to show going back
        generations_forward: Number of generations to show going forward
        style_choice: Visualization style choice ("1", "2", or "3")
        output_format: Output format (svg, pdf, png, html)
        
    Returns:
        Optional[str]: Path to the generated output file, or None if failed
    """
    
    # Choose graph class based on style
    if style_choice == "2":
        graph_class = EmbeddedFamilyTreeGraph
    elif style_choice == "3":
        graph_class = D3FamilyTreeGraph
    else:
        graph_class = FamilyTreeGraph
    
    # Create graph instance
    try:
        graph = graph_class(
            xml_data_dir=xml_data_dir,
            output_dir=output_dir,
            start_person_name=start_person,
            generations_back=generations_back,
            generations_forward=generations_forward,
            output_format=output_format
        )
        
        # Generate the visualization
        output_path = graph.generate_visualization(output_format=output_format)
        
        print(f"\n✅ Family tree generated successfully!")
        print(f"📁 Output file: {output_path}")
        
        # Open the result
        if output_format == "html":
            graph.open_in_browser()
        else:
            print(f"🌐 Opening {output_path}...")
            os.startfile(output_path) if os.name == 'nt' else subprocess.run(['open', output_path])
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error creating family tree: {e}")
        import traceback
        traceback.print_exc()
        return None
    
if __name__ == "__main__":
    main()
