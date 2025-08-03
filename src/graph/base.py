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
        
        # Default output format
        self.output_format = "svg"

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
        """Add a node to the graph with enhanced styling and precise collision boundaries."""
        name = char_data.get('name', 'Unknown')
        birth_date = char_data.get('birth_date', '')
        death_date = char_data.get('death_date', '')
        marriage_date = char_data.get('marriage_date', '')
        
        # Build enhanced label with symbols
        label_parts = [name]
        
        if birth_date:
            label_parts.append(f"★ {birth_date}")
        
        if death_date:
            label_parts.append(f"✝ {death_date}")
        elif char_data.get('died', '').strip().upper() not in ['L', '']:
            label_parts.append("✝")  # Deceased indicator
            
        if marriage_date:
            label_parts.append(f"♥ {marriage_date}")
        
        label = "\\n".join(label_parts)
        
        # Enhanced node attributes with better collision boundaries
        attrs = {
            'label': label,
            'tooltip': self._create_enhanced_tooltip(char_data),
            'fontname': 'Arial',
            'fontsize': '10',
            'style': 'rounded,filled',
            'fillcolor': self._get_node_color(char_data),
            'color': '#2c3e50',  # Border color
            'penwidth': '1.5',
            'margin': '0.1,0.05',  # Tighter margins for better collision
            'shape': 'box',
            'width': '1.2',  # Minimum width for consistent collision
            'height': '0.8'  # Minimum height for consistent collision
        }
        
        # Enhanced SVG interactivity attributes
        if self.output_format == 'svg':
            attrs.update({
                'id': f'node-{char_id}',
                'class': 'family-node clickable',
                'data-id': char_id,
                'data-name': name,
                'data-birth': birth_date or '',
                'data-death': death_date or '',
                'data-marriage': marriage_date or '',
                'onclick': f"handleNodeClick('{char_id}')",
                'onmouseover': f"handleNodeHover('{char_id}')",
                'onmouseout': f"handleNodeLeave('{char_id}')"
            })
        
        dot.node(char_id, **attrs)

    @abstractmethod
    def _add_relationship_edges(self, dot: Graph):
        """Add edges for family relationships."""
        pass

    def generate_graph(self, file_format: str = "svg") -> str:
        """
        Generate the family tree visualization.
        
        Args:
            file_format: Output format (svg, html, pdf, png)
            
        Returns:
            str: Path to the generated output file
        """
        # Always generate SVG first
        svg_path = self._generate_svg()
        
        # If HTML format requested, generate HTML with embedded SVG
        if file_format.lower() == 'html':
            return self._generate_html(svg_path)
        
        # For other formats, return SVG path
        return svg_path
    
    def _generate_svg(self) -> str:
        """Generate the SVG file"""
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize graph
        dot = Graph(comment='Family Tree', format='svg')
        self._configure_graph(dot)
        
        # Add nodes and edges
        for char_id, char_data in self.characters.items():
            self._add_node(dot, char_id, char_data)
        self._add_relationship_edges(dot)
        
        # Generate the graph
        svg_path = os.path.join(self.output_dir, f"{self.name}.svg")
        dot.render(svg_path, cleanup=True)
        return svg_path
    
    def _generate_html(self, svg_path: str) -> str:
        """Generate HTML file with embedded SVG and JavaScript interactivity"""
        try:
            from ..ui.html_viewer import HTMLFamilyTreeViewer
            
            # Create HTML viewer
            html_viewer = HTMLFamilyTreeViewer(svg_path, self.characters)
            
            # Generate HTML file
            html_path = html_viewer.generate_html()
            
            print(f"DEBUG: Generated interactive HTML: {html_path}")
            return html_path
            
        except ImportError as e:
            print(f"ERROR: Could not import HTMLFamilyTreeViewer: {e}")
            return svg_path
        except Exception as e:
            print(f"ERROR: Could not generate HTML: {e}")
            return svg_path
    
    def open_in_browser(self) -> None:
        """Open the HTML version in the default web browser"""
        try:
            # Generate HTML if it doesn't exist
            html_path = self.generate_graph('html')
            
            # Open in browser
            from ..ui.html_viewer import HTMLFamilyTreeViewer
            svg_path = self.get_svg_path()
            viewer = HTMLFamilyTreeViewer(svg_path, self.characters)
            viewer.open_in_browser()
            
        except Exception as e:
            print(f"ERROR: Could not open in browser: {e}")

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
    
    def get_html_path(self) -> str:
        """Get the HTML output file path"""
        return self.get_output_file_path("html")
    
    def get_png_path(self) -> str:
        """Get the PNG output file path"""
        return self.get_output_file_path("png")
    
    def _create_enhanced_tooltip(self, char_data: Dict[str, Any]) -> str:
        """Create comprehensive tooltip text for enhanced nodes."""
        name = char_data.get('name', 'Unknown')
        tooltip_parts = [f"Name: {name}"]
        
        if char_data.get('birth_date'):
            tooltip_parts.append(f"Born: {char_data['birth_date']}")
            
        if char_data.get('death_date'):
            tooltip_parts.append(f"Died: {char_data['death_date']}")
        elif char_data.get('died', '').strip().upper() not in ['L', '']:
            tooltip_parts.append("Status: Deceased")
        else:
            tooltip_parts.append("Status: Living")
            
        if char_data.get('marriage_date'):
            tooltip_parts.append(f"Married: {char_data['marriage_date']}")
            
        if char_data.get('spouse_id'):
            tooltip_parts.append(f"Spouse ID: {char_data['spouse_id']}")
            
        return " | ".join(tooltip_parts)
    
    def _get_node_color(self, char_data: Dict[str, Any]) -> str:
        """
        Determine node color based on character data for better visual distinction.
        
        Returns:
            Hex color string
        """
        # Color coding: Living vs deceased
        if char_data.get('death_date') or (
            char_data.get('died', '').strip().upper() not in ['L', '']
        ):
            return '#ecf0f1'  # Light gray for deceased
        else:
            return '#e8f8f5'  # Light green for living
