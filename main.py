"""
main.py
Main entry point for the family tree visualization tool.
"""
import os
import datetime
from src.graph.family import FamilyTreeGraph
from src.graph.embedded_family import EmbeddedFamilyTreeGraph
from src.data.excel_converter import create_xml_from_excel_sheet, select_excel_file_and_sheet
from src.data.xml_parser import FamilyTreeData

# Default output format is now SVG for interactivity
DEFAULT_OUTPUT_FORMAT = "svg"

def main():
    """Main function to run the family tree visualization tool."""
    # First, let user select the Excel file and sheet
    excel_file_path, sheet_name = select_excel_file_and_sheet()
    if not excel_file_path or not sheet_name:
        print("No file or sheet selected. Exiting.")
        return

    # Create XML directory based on Excel file and sheet names
    excel_base_name = os.path.splitext(os.path.basename(excel_file_path))[0]
    xml_data_dir = os.path.join("assets", excel_base_name, sheet_name)
    os.makedirs(xml_data_dir, exist_ok=True)
    
    print(f"XML files will be stored/read from: {xml_data_dir}")
    create_xml_from_excel_sheet(excel_file_path, sheet_name, xml_data_dir)
    
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

    # Create timestamped output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("out", timestamp)
    os.makedirs(output_dir, exist_ok=True)

    # Initialize and generate the family tree based on chosen style
    family_tree = create_family_tree(
        style_choice=style_choice,
        xml_data_dir=xml_data_dir,
        output_dir=output_dir,
        start_person=start_person,
        generations_back=generations_back,
        generations_forward=generations_forward,
        output_format=output_format
    )
    
    if family_tree and family_tree.characters:
        output_path = family_tree.generate_graph()
        print(f"\nFamily tree visualization saved to: {output_path}")
        
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
    
    style_choice = input("Enter your choice (1 or 2): ").strip()
    if style_choice not in ["1", "2"]:
        print("Invalid style choice. Please enter 1 or 2. Exiting.")
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

def create_family_tree(style_choice: str, xml_data_dir: str, output_dir: str,
                      start_person: str = None, generations_back: int = 0,
                      generations_forward: int = 0, output_format: str = DEFAULT_OUTPUT_FORMAT):
    """
    Create the appropriate family tree visualization based on user choices.
    
    Args:
        style_choice: "1" for classic or "2" for embedded style
        xml_data_dir: Directory containing XML character files
        output_dir: Directory to save output files
        start_person: Name of person to start from (optional)
        generations_back: Number of generations to show going back
        generations_forward: Number of generations to show going forward
        output_format: The desired output format (svg, pdf, png)
        
    Returns:
        FamilyTreeGraph or EmbeddedFamilyTreeGraph instance
    """
    # Create timestamped output directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    graph_name = f"family_tree_{timestamp}"
    
    # Initialize data provider
    data_provider = FamilyTreeData(xml_data_dir)
    
    # Choose graph class based on style
    graph_class = EmbeddedFamilyTreeGraph if style_choice == "2" else FamilyTreeGraph
    
    # Create graph instance
    graph = graph_class(
        xml_data_dir=xml_data_dir,
        output_dir=output_dir,
        start_person_name=start_person if start_person else None,
        generations_back=generations_back,
        generations_forward=generations_forward,
        output_format=output_format
    )
    
    # Initialize data
    graph.data_provider = data_provider
    graph.all_characters = data_provider.get_all_characters()
    graph.all_id_to_name_map = data_provider.get_id_name_map()
    
    # Select relevant characters
    if start_person:
        graph._select_relevant_characters(start_person, generations_back, generations_forward)
    else:
        graph.characters = graph.all_characters
        graph.id_to_name_map = graph.all_id_to_name_map
    
    return graph
    
if __name__ == "__main__":
    main()
