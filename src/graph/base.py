"""
Base class for relationship graphs
"""
import os
from graphviz import Graph
from abc import ABC, abstractmethod
from typing import Dict, Any, Set, Optional, Tuple
import xml.etree.ElementTree as ET
from ..data.xml_parser import FamilyTreeData
from ..core.path_manager import path_manager

class RelGraph(ABC):
    """Abstract base class for relationship graphs"""
    
    def __init__(self, name: str, output_dir: Optional[str] = None):
        """
        Initialize the relationship graph.
        
        Args:
            name: Name of the graph (used for file naming)
            output_dir: Optional output directory (will use path_manager if not provided)
        """
        self.name = name
        
        # Use centralized path manager
        if output_dir:
            self.output_dir = output_dir
            os.makedirs(self.output_dir, exist_ok=True)
            self.dot_path = os.path.join(self.output_dir, name)
        else:
            self.output_dir = path_manager.get_session_dir()
            self.dot_path = path_manager.get_graph_base_path(name)
        
        print(f"DEBUG: RelGraph initialized with output_dir: {self.output_dir}")
        print(f"DEBUG: RelGraph dot_path: {self.dot_path}")
        
        # Initialize data storage
        self.all_characters: Dict = {}
        self.all_id_to_name_map: Dict = {}
        self.characters: Dict = {}
        self.id_to_name_map: Dict = {}

    def _configure_graph(self, dot: Graph):
        """Configure the graph's visual properties."""
        # Basic graph settings
        dot.attr(rankdir='TB')  # Top to bottom layout
        dot.attr('node', shape='box', style='rounded')
        
        # SVG-specific settings for interactivity
        if self.output_format == 'svg':
            dot.attr('node', id='node-%(name)s')  # Add IDs to nodes for JavaScript
            dot.attr(overlap='false', splines='ortho')
            # Add CSS classes for styling
            dot.attr('node', class_='family-node')
            dot.attr('edge', class_='family-edge')

    def _add_node(self, dot: Graph, char_id: str, char_data: Dict):
        """Add a node to the graph with proper styling."""
        name = char_data.get('name', 'Unknown')
        birth_date = char_data.get('birth_date', '')
        death_date = char_data.get('death_date', '')
        
        # Create label with basic info
        label = f"{name}\\n{birth_date or '?'} - {death_date or ''}"
        
        # Node attributes
        attrs = {
            'label': label,
            'tooltip': name,  # Hover text
            'fontname': 'Arial',
            'style': 'rounded,filled',
            'fillcolor': 'white',
        }
        
        # Add data attributes for SVG interactivity
        if self.output_format == 'svg':
            attrs.update({
                'data-id': char_id,
                'data-name': name,
                'data-birth': birth_date or '',
                'data-death': death_date or '',
                'onclick': f"showDetails('{char_id}')"  # JavaScript function call
            })
        
        dot.node(char_id, **attrs)

    @abstractmethod
    def _add_relationship_edges(self, dot: Graph):
        """Add edges for family relationships."""
        pass

    def generate_graph(self) -> str:
        """
        Generate the family tree visualization.
        
        Returns:
            str: Path to the generated output file
        """
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize graph
        dot = Graph(comment='Family Tree', format=self.output_format)
        self._configure_graph(dot)
        
        # Add nodes and edges
        for char_id, char_data in self.characters.items():
            self._add_node(dot, char_id, char_data)
        self._add_relationship_edges(dot)
        
        # Generate the graph
        output_path = os.path.join(self.output_dir, f"{self.name}.{self.output_format}")
        dot.render(output_path, cleanup=True)
        return output_path

    @property
    def dot_path(self) -> str:
        """Get the path to the dot file."""
        return self._dot_path

    @dot_path.setter
    def dot_path(self, value: str) -> None:
        """Set the path to the dot file."""
        self._dot_path = value

    @abstractmethod
    def _create_node_info(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create node information from character data.
        
        Args:
            character: Dictionary containing character information
            
        Returns:
            Dict[str, Any]: Dictionary containing node information
        """
        pass

    def _load_all_characters(self):
        """Load all character data from XML files."""
        for filename in os.listdir(self.xml_data_dir):
            if filename.endswith('.xml'):
                file_path = os.path.join(self.xml_data_dir, filename)
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    char_data = {}
                    
                    # Extract character ID from filename
                    char_id = os.path.splitext(filename)[0]
                    
                    # Parse XML data
                    for child in root:
                        char_data[child.tag] = child.text
                    
                    # Store character data
                    self.all_characters[char_id] = char_data
                    if 'name' in char_data:
                        self.all_id_to_name_map[char_id] = char_data['name']
                        
                except ET.ParseError as e:
                    print(f"Error parsing {filename}: {e}")
                except Exception as e:
                    print(f"Error processing {filename}: {e}")

    def _select_relevant_characters(self, start_person_name: str, generations_back: int, generations_forward: int):
        """Select characters relevant to the visualization based on parameters."""
        # Find starting person's ID
        start_id = None
        for char_id, name in self.all_id_to_name_map.items():
            if name.lower() == start_person_name.lower():
                start_id = char_id
                break
        
        if not start_id:
            print(f"Could not find person named '{start_person_name}'")
            return
        
        # Collect relevant character IDs
        relevant_ids = {start_id}
        
        # Get ancestors if requested
        if generations_back > 0:
            self._get_ancestors(start_id, generations_back, relevant_ids)
        
        # Get descendants if requested
        if generations_forward > 0:
            self._get_descendants(start_id, generations_forward, relevant_ids)
        
        # Filter characters to only include relevant ones
        self.characters = {id: self.all_characters[id] for id in relevant_ids if id in self.all_characters}
        self.id_to_name_map = {id: self.all_id_to_name_map[id] for id in relevant_ids if id in self.all_id_to_name_map}

    def _get_ancestors(self, person_id: str, remaining_generations: int, collected_ids: Set[str]):
        """Recursively collect ancestor IDs."""
        if remaining_generations <= 0:
            return
        
        person = self.all_characters.get(person_id)
        if not person:
            return
        
        # Check for parents
        father_id = person.get('father_id')
        mother_id = person.get('mother_id')
        
        # Add parents to collection and recurse
        if father_id and father_id in self.all_characters:
            collected_ids.add(father_id)
            self._get_ancestors(father_id, remaining_generations - 1, collected_ids)
        
        if mother_id and mother_id in self.all_characters:
            collected_ids.add(mother_id)
            self._get_ancestors(mother_id, remaining_generations - 1, collected_ids)

    def _get_descendants(self, person_id: str, remaining_generations: int, collected_ids: Set[str]):
        """Recursively collect descendant IDs."""
        if remaining_generations <= 0:
            return
        
        # Find all characters that have this person as a parent
        for char_id, char_data in self.all_characters.items():
            if (char_data.get('father_id') == person_id or 
                char_data.get('mother_id') == person_id):
                collected_ids.add(char_id)
                self._get_descendants(char_id, remaining_generations - 1, collected_ids)

    def _configure_graph_style(self, dot: Graph) -> None:
        """
        Configures the basic style of the graph.
        """
        dot.attr(rankdir='TB')
        dot.attr('node', shape='box')
        dot.attr('edge')

    def addNode(self, dot: Graph, character: Dict[str, Any]) -> str:
        """
        Adds a node to the graph.
        
        Args:
            dot: The graphviz Graph object
            character: Dictionary containing character information
            
        Returns:
            str: The node ID that was added
        """
        node_info = self._create_node_info(character)
        node_id = node_info["name"]
        node_label = node_info["label"]
        color = "black"  # Default color

        if('\t%s' % node_id in dot.body):
            return node_id

        if(character.get("image") == None):
            dot.node(node_id, color=color, label=node_label, URL=node_info.get("URL"))
        else:
            dot.node(node_id, color=color, label=f'<<table cellspacing="0" \
                            border="0" cellborder="1"><tr><td><img src="{character["image"]}" scale="true"/></td></tr> \
                            <tr><td>{node_label}</td></tr></table>>', headport="n", URL=node_info.get("URL"))
        return node_id

    def hasChar(self, dot: Graph, character: Dict[str, Any]) -> bool:
        """
        Checks if a character already exists in the graph.
        
        Args:
            dot: The graphviz Graph object
            character: Dictionary containing character information
            
        Returns:
            bool: True if character exists in graph, False otherwise
        """
        if('\t%s' % character["id"] in dot.body):
            return True
        return False

    def get_output_file_path(self, extension: str = "svg") -> str:
        """Get the output file path with the specified extension"""
        return f"{self.dot_path}.{extension}"
    
    def get_svg_path(self) -> str:
        """Get the SVG output file path"""
        return self.get_output_file_path("svg")
    
    def get_png_path(self) -> str:
        """Get the PNG output file path"""
        return self.get_output_file_path("png") 