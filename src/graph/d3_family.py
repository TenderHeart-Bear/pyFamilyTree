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
# UI components are handled separately

class D3FamilyTreeGraph(RelGraph):
    """
    A family tree graph implementation using D3.js for better handling of large trees
    """
    
    def __init__(self, xml_data_dir: str, output_dir: Optional[str] = None,
                 start_person_id: Optional[str] = None, generations_back: int = 0,
                 generations_forward: int = 0, output_format: str = "html",
                 characters: Optional[Dict[str, Dict[str, Any]]] = None,
                 id_to_name_map: Optional[Dict[str, str]] = None):
        """
        Initialize the D3.js family tree graph.
        
        Args:
            xml_data_dir: Directory containing XML data files
            output_dir: Directory to save output files (uses path_manager if not provided)
            start_person_id: Optional ID of person to start from
            generations_back: Number of generations to show going back
            generations_forward: Number of generations to show going forward
            output_format: Output format (html, svg, pdf, png)
            characters: Optional pre-loaded character data
            id_to_name_map: Optional pre-loaded ID to name mapping
        """
        # Initialize base class (it will handle path management)
        super().__init__("d3_family_tree", output_dir)
        
        # Store parameters
        self.xml_data_dir = xml_data_dir
        self.output_format = output_format
        
        # Initialize data storage
        self.processed_pairs = {}  # Track which ID to use for each spouse pair
        self.skip_nodes = set()    # Track nodes that should not be displayed
        
        # D3FamilyTreeGraph initialized
        
        # Use provided data or load from files
        if characters is not None and id_to_name_map is not None:
            # Using provided character data
            self.all_characters = characters
            self.all_id_to_name_map = id_to_name_map
        else:
            # Loading data from files (fallback)
            self.data_provider = FamilyTreeData(xml_data_dir)
            self.all_characters = self.data_provider.get_all_characters()
            self.all_id_to_name_map = self.data_provider.get_id_name_map()
        
        # Data loaded and ready for tree generation
        
        # Initialize tree with specified parameters
        
        # Select relevant characters
        if start_person_id:
            # Specific person view
            self._select_relevant_characters(start_person_id, generations_back, generations_forward)
        elif generations_back == 0 and generations_forward == 0:
            # Complete tree view - need to build relationship structure
            # Generating complete tree view with relationship building
            self._build_complete_tree_structure()
        else:
            # Invalid state - no start person but has generation limits
            # Invalid state - no start person but has generation limits
            self.characters = {}
            self.id_to_name_map = {}
    
    def _select_relevant_characters(self, start_person_id: str, 
                                  generations_back: int, generations_forward: int):
        """Select characters based on starting person and generation limits"""
        
        # Looking for specified person ID
        if not start_person_id:
            # No start person ID provided
            self.characters = {}
            self.id_to_name_map = {}
            return
            
        if start_person_id not in self.all_characters:
            self.characters = {}
            self.id_to_name_map = {}
            return
        
        # Build the family tree starting from this person
        self.characters = {}
        self.id_to_name_map = {}
        
        # Add the starting person and their spouse
        processed = set()
        self._add_person_and_relatives(start_person_id, generations_back, generations_forward, processed, is_starting_person=True)
    
    def _add_person_and_relatives(self, person_id: str, generations_back: int, 
                                 generations_forward: int, processed: Set[str], is_starting_person: bool = False):
        """Recursively add person and their relatives"""
        
        # Skip if already processed or not found
        if person_id not in self.all_characters:
            return
            
        # Skip if already processed in this branch
        branch_key = f"{person_id}_{generations_back}_{generations_forward}"
        if branch_key in processed:
            return
        
        # Mark this branch as processed
        processed.add(branch_key)
        person_data = self.all_characters[person_id]
        
        # Add this person
        self.characters[person_id] = person_data
        self.id_to_name_map[person_id] = person_data.get('name', person_id)
        
        # Add spouse if this is the starting person
        if is_starting_person:
            spouse_id = person_data.get('spouse_id')
            if spouse_id and spouse_id in self.all_characters:
                spouse_data = self.all_characters[spouse_id]
                self.characters[spouse_id] = spouse_data
                self.id_to_name_map[spouse_id] = spouse_data.get('name', spouse_id)
        
        # Add parents if we haven't reached the generation limit
        if generations_back > 0:
            father_id = person_data.get('father_id')
            mother_id = person_data.get('mother_id')
            
            # Process parents with reduced generations_back and no generations_forward
            if father_id:
                self._add_person_and_relatives(father_id, generations_back - 1, 0, processed, False)
            
            if mother_id:
                self._add_person_and_relatives(mother_id, generations_back - 1, 0, processed, False)
        
        # Add children if we haven't reached the generation limit
        if generations_forward > 0:
            # Find all children where this person is either the father or mother
            for char_id, char_data in self.all_characters.items():
                if char_data.get('father_id') == person_id or char_data.get('mother_id') == person_id:
                    # Process children with no generations_back and reduced generations_forward
                    self._add_person_and_relatives(char_id, 0, generations_forward - 1, processed, False)
    
    def _build_complete_tree_structure(self):
        """Build complete tree structure by connecting all characters through relationships"""
        self.characters = {}
        self.id_to_name_map = {}
        
        # Find true root ancestors (people with no parents who are not spouses of others with parents)
        root_ancestors = []
        
        # First, identify all people who have parents
        people_with_parents = set()
        for char_id, char_data in self.all_characters.items():
            father_id = char_data.get('father_id')
            mother_id = char_data.get('mother_id')
            
            if father_id and father_id in self.all_characters:
                people_with_parents.add(char_id)
            if mother_id and mother_id in self.all_characters:
                people_with_parents.add(char_id)
        
        # Then find people with no parents who are not spouses of people with parents
        root_family_units = []  # Track root family units to avoid duplicates
        
        for char_id, char_data in self.all_characters.items():
            father_id = char_data.get('father_id')
            mother_id = char_data.get('mother_id')
            
            # Check if parents exist in the data
            has_father = father_id and father_id in self.all_characters
            has_mother = mother_id and mother_id in self.all_characters
            
            # Only consider as root ancestor if no parents in the data
            if not has_father and not has_mother:
                # Check if this person is a spouse of someone with parents
                spouse_id = char_data.get('spouse_id')
                is_spouse_of_person_with_parents = False
                
                if spouse_id and spouse_id in people_with_parents:
                    is_spouse_of_person_with_parents = True
                
                # Only add if not a spouse of someone with parents
                if not is_spouse_of_person_with_parents:
                    # Check if we already have someone from this root family unit
                    spouse_id = char_data.get('spouse_id')
                    family_unit_key = tuple(sorted([char_id, spouse_id])) if spouse_id else (char_id,)
                    
                    # Only add if this family unit isn't already represented
                    if not any(family_unit_key == existing_unit for existing_unit in root_family_units):
                        root_ancestors.append(char_id)
                        root_family_units.append(family_unit_key)
        
        # If no root ancestors found, start with the first person
        if not root_ancestors:
            root_ancestors = [list(self.all_characters.keys())[0]]
        
        # Add root ancestor information to the character data for JavaScript to use
        for char_id, char_data in self.all_characters.items():
            if char_id in root_ancestors:
                char_data['is_root_ancestor'] = True
            else:
                char_data['is_root_ancestor'] = False
        
        # Build tree from each root ancestor
        processed = set()
        for root_id in root_ancestors:
            self._build_tree_from_person(root_id, processed)
        
        # Add any remaining unconnected people
        for char_id, char_data in self.all_characters.items():
            if char_id not in self.characters:
                self.characters[char_id] = char_data
                self.id_to_name_map[char_id] = char_data.get('name', char_id)
    
    def _build_tree_from_person(self, person_id: str, processed: Set[str]):
        """Recursively build tree structure from a person"""
        if person_id in processed or person_id not in self.all_characters:
            return
        
        processed.add(person_id)
        person_data = self.all_characters[person_id]
        
        # Add this person
        self.characters[person_id] = person_data
        self.id_to_name_map[person_id] = person_data.get('name', person_id)
        
        # Add spouse
        spouse_id = person_data.get('spouse_id')
        if spouse_id and spouse_id in self.all_characters and spouse_id not in processed:
            spouse_data = self.all_characters[spouse_id]
            self.characters[spouse_id] = spouse_data
            self.id_to_name_map[spouse_id] = spouse_data.get('name', spouse_id)
            processed.add(spouse_id)
        
        # Add children
        for char_id, char_data in self.all_characters.items():
            if (char_data.get('father_id') == person_id or 
                char_data.get('mother_id') == person_id) and char_id not in processed:
                self._build_tree_from_person(char_id, processed)
        
        # Add parents if they exist
        father_id = person_data.get('father_id')
        mother_id = person_data.get('mother_id')
        
        if father_id and father_id in self.all_characters and father_id not in processed:
            self._build_tree_from_person(father_id, processed)
        
        if mother_id and mother_id in self.all_characters and mother_id not in processed:
            self._build_tree_from_person(mother_id, processed)
    
    def generate_graph(self, file_format: str = "html") -> str:
        """
        Generate the D3.js family tree graph.
        
        Args:
            file_format: Output format (default: html)
            
        Returns:
            str: Path to the generated graph file
        """
        try:
            # Import D3FamilyTreeViewer here to avoid circular imports
            from ..ui.widgets.d3_tree_viewer import D3FamilyTreeViewer
            
            # Create D3.js viewer
            d3_viewer = D3FamilyTreeViewer(self.characters, self.output_dir)
            
            # Generate HTML file
            html_path = d3_viewer.generate_html()
            
            return html_path
            
        except Exception as e:
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
            raise
    
    def open_in_browser(self) -> None:
        """Open the D3.js family tree in the default web browser"""
        try:
            # Generate HTML if it doesn't exist
            html_path = self.generate_graph('html')
            
            # Import and open in browser
            from ..ui.widgets.d3_tree_viewer import D3FamilyTreeViewer
            d3_viewer = D3FamilyTreeViewer(self.characters, self.output_dir)
            d3_viewer.open_in_browser()
            
        except Exception as e:
            pass  # Silently handle browser opening errors
    
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