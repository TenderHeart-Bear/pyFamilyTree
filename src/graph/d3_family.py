"""
D3.js-based family tree implementation
Better handling of large family trees with proper zoom and pan
"""
import os
import datetime
from typing import Dict, Any, Set, Optional, Tuple
from .base import RelGraph
from ..data.xml_parser import FamilyTreeData
from ..core.path_manager import path_manager
from ..ui.widgets.d3_tree_viewer import D3FamilyTreeViewer

class D3FamilyTreeGraph(RelGraph):
    """
    A family tree graph implementation using D3.js for better handling of large trees
    """
    
    def __init__(self, xml_data_dir: str, output_dir: Optional[str] = None,
                 start_person_name: Optional[str] = None, generations_back: int = 0,
                 generations_forward: int = 0, output_format: str = "html"):
        """
        Initialize the D3.js family tree graph.
        
        Args:
            xml_data_dir: Directory containing XML data files
            output_dir: Directory to save output files (uses path_manager if not provided)
            start_person_name: Optional name of person to start from
            generations_back: Number of generations to show going back
            generations_forward: Number of generations to show going forward
            output_format: Output format (html, svg, pdf, png)
        """
        # Initialize base class (it will handle path management)
        super().__init__("d3_family_tree", output_dir)
        
        # Store parameters
        self.xml_data_dir = xml_data_dir
        self.output_format = output_format
        
        # Initialize data storage
        self.processed_pairs = {}  # Track which ID to use for each spouse pair
        self.skip_nodes = set()    # Track nodes that should not be displayed
        
        # Initialize data provider and load data
        self.data_provider = FamilyTreeData(xml_data_dir)
        self.all_characters = self.data_provider.get_all_characters()
        self.all_id_to_name_map = self.data_provider.get_id_name_map()
        
        # Select relevant characters
        if start_person_name:
            self._select_relevant_characters(start_person_name, generations_back, generations_forward)
        else:
            self.characters = self.all_characters
            self.id_to_name_map = self.all_id_to_name_map
    
    def _select_relevant_characters(self, start_person_name: str, 
                                  generations_back: int, generations_forward: int):
        """Select characters based on starting person and generation limits"""
        # Find the starting person
        start_person_id = None
        for char_id, char_data in self.all_characters.items():
            if char_data.get('name', '').lower() == start_person_name.lower():
                start_person_id = char_id
                break
        
        if not start_person_id:
            print(f"Warning: Could not find person '{start_person_name}'")
            self.characters = self.all_characters
            self.id_to_name_map = self.all_id_to_name_map
            return
        
        # Build the family tree starting from this person
        self.characters = {}
        self.id_to_name_map = {}
        
        # Add the starting person
        self._add_person_and_relatives(start_person_id, generations_back, generations_forward, set())
    
    def _add_person_and_relatives(self, person_id: str, generations_back: int, 
                                 generations_forward: int, processed: Set[str]):
        """Recursively add person and their relatives"""
        if person_id in processed or person_id not in self.all_characters:
            return
        
        processed.add(person_id)
        person_data = self.all_characters[person_id]
        
        # Add this person
        self.characters[person_id] = person_data
        self.id_to_name_map[person_id] = person_data.get('name', person_id)
        
        # Add parents if we haven't reached the generation limit
        if generations_back > 0:
            father_id = person_data.get('father_id')
            mother_id = person_data.get('mother_id')
            
            if father_id and father_id in self.all_characters:
                self._add_person_and_relatives(father_id, generations_back - 1, 
                                             generations_forward, processed)
            
            if mother_id and mother_id in self.all_characters:
                self._add_person_and_relatives(mother_id, generations_back - 1, 
                                             generations_forward, processed)
        
        # Add children if we haven't reached the generation limit
        if generations_forward > 0:
            for char_id, char_data in self.all_characters.items():
                if (char_data.get('father_id') == person_id or 
                    char_data.get('mother_id') == person_id):
                    self._add_person_and_relatives(char_id, generations_back, 
                                                 generations_forward - 1, processed)
    
    def generate_graph(self, file_format: str = "html") -> str:
        """
        Generate the D3.js family tree graph.
        
        Args:
            file_format: Output format (default: html)
            
        Returns:
            str: Path to the generated graph file
        """
        try:
            # Create D3.js viewer
            d3_viewer = D3FamilyTreeViewer(self.characters, self.output_dir)
            
            # Generate HTML file
            html_path = d3_viewer.generate_html()
            
            print(f"DEBUG: Generated D3.js family tree: {html_path}")
            return html_path
            
        except Exception as e:
            print(f"ERROR: Error generating D3.js graph: {str(e)}")
            raise e
    
    def generate_visualization(self, output_format: str = "html", 
                             output_dir: Optional[str] = None) -> str:
        """
        Generate the family tree visualization.

        Args:
            output_format: Output format (html, svg, pdf, png)
            output_dir: Optional output directory
        Returns:
            str: Path to the generated output file
        """
        self.output_format = output_format
        if output_dir:
            self.output_dir = output_dir

        try:
            # Generate D3.js HTML
            return self.generate_graph('html')
        except Exception as e:
            print(f"Error generating visualization: {e}")
            raise
    
    def open_in_browser(self) -> None:
        """Open the D3.js family tree in the default web browser"""
        try:
            # Generate HTML if it doesn't exist
            html_path = self.generate_graph('html')
            
            # Open in browser
            d3_viewer = D3FamilyTreeViewer(self.characters, self.output_dir)
            d3_viewer.open_in_browser()
            
        except Exception as e:
            print(f"ERROR: Could not open in browser: {e}")
    
    def get_output_file_path(self, format_extension: str) -> str:
        """Get the path to the output file."""
        return os.path.join(self.output_dir, f"{self.name}.{format_extension}")
    
    def get_svg_path(self) -> str:
        """Get the path to the SVG file (not used for D3.js)."""
        return self.get_output_file_path('html')  # Return HTML path instead
    
    def _add_relationship_edges(self, dot):
        """Add relationship edges to the graph (not used for D3.js)."""
        # This method is required by the abstract base class but not used for D3.js
        # since D3.js handles relationships in JavaScript
        pass
    
    def _create_node_info(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Create node information for the character (not used for D3.js)."""
        # This method is required by the abstract base class but not used for D3.js
        # since D3.js handles node creation in JavaScript
        return {
            "name": character.get('name', 'Unknown'),
            "id": character.get('id', ''),
            "birth_date": character.get('birth_date', ''),
            "death_date": character.get('death_date', ''),
            "marriage_date": character.get('marriage_date', '')
        } 