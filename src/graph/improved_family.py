"""
Improved family tree implementation with better handling of large trees
Uses Graphviz with optimized settings to prevent cutting off
"""
import os
import datetime
from typing import Dict, Any, Set, Optional, Tuple
import graphviz
from .base import RelGraph
from ..data.xml_parser import FamilyTreeData
from ..core.path_manager import path_manager

class ImprovedFamilyTreeGraph(RelGraph):
    """
    An improved family tree graph implementation with better layout for large trees
    """
    
    def __init__(self, xml_data_dir: str, output_dir: Optional[str] = None,
                 start_person_name: Optional[str] = None, generations_back: int = 0,
                 generations_forward: int = 0, output_format: str = "svg"):
        """
        Initialize the improved family tree graph.
        
        Args:
            xml_data_dir: Directory containing XML data files
            output_dir: Directory to save output files (uses path_manager if not provided)
            start_person_name: Optional name of person to start from
            generations_back: Number of generations to show going back
            generations_forward: Number of generations to show going forward
            output_format: Output format (svg, pdf, png)
        """
        # Initialize base class (it will handle path management)
        super().__init__("improved_family_tree", output_dir)
        
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
    
    def generate_graph(self, file_format: str = "svg") -> str:
        """
        Generate the improved family tree graph with optimized layout.
        
        Args:
            file_format: Output format (default: svg)
            
        Returns:
            str: Path to the generated graph file
        """
        # Create a new directed graph with optimized layout
        self.dot = graphviz.Digraph(
            self.name,
            filename=self.dot_path,
            format=file_format,
            engine='dot'
        )
        
        # Configure graph for optimal layout and size
        self._configure_optimized_layout()
        
        # Add nodes and edges
        self._add_optimized_nodes()
        self._add_optimized_relationships()
        
        # Generate the output file
        try:
            self.dot.render(cleanup=True)
            output_path = self.get_output_file_path(file_format)
            print(f"DEBUG: Generated improved family tree: {output_path}")
            return output_path
        except Exception as e:
            print(f"ERROR: Error generating graph: {str(e)}")
            raise e
    
    def _configure_optimized_layout(self):
        """Configure graph with optimized layout settings for large trees"""
        # Basic layout settings
        self.dot.attr(rankdir='TB')  # Top to bottom
        self.dot.attr(splines='ortho')  # Orthogonal lines for cleaner look
        self.dot.attr(ordering='out')  # Order nodes by outgoing edges
        
        # Spacing settings optimized for large trees
        self.dot.attr(nodesep='0.8')  # Horizontal spacing between nodes
        self.dot.attr(ranksep='1.5')  # Vertical spacing between generations
        self.dot.attr(concentrate='false')  # Don't merge edges to avoid confusion
        
        # Size and scaling settings
        self.dot.attr(dpi='150')  # Higher DPI for better quality
        self.dot.attr(ratio='auto')  # Let graphviz choose ratio
        self.dot.attr(size='24,18')  # Larger size limit (24x18 inches)
        
        # Node styling for better readability
        self.dot.attr('node', 
                      shape='box',
                      style='rounded,filled',
                      fillcolor='lightblue',
                      fontname='Arial',
                      fontsize='10',
                      margin='0.3,0.2',
                      width='1.8',
                      height='1.0',
                      color='black',
                      penwidth='1',
                      class_='node')
        
        # Edge styling
        self.dot.attr('edge',
                      color='black',
                      fontsize='8',
                      arrowsize='0.8',
                      penwidth='1.5')
    
    def _add_optimized_nodes(self):
        """Add nodes with optimized information display"""
        for person_id, person_data in self.characters.items():
            node_info = self._create_optimized_node_info(person_data)
            
            # Add node with HTML-compatible attributes
            self.dot.node(person_id, 
                          label=node_info["label"],
                          tooltip=f"Click to view details for {person_data.get('name', person_id)}",
                          id=f"node-{person_id}")
    
    def _create_optimized_node_info(self, person_data: Dict[str, Any]) -> Dict[str, str]:
        """Create optimized node information for better display"""
        name = person_data.get('name', 'Unknown')
        birth_date = person_data.get('birth_date', '')
        death_date = person_data.get('death_date', '')
        marriage_date = person_data.get('marriage_date', '')
        
        # Build compact label
        label_parts = [name]
        
        if birth_date:
            label_parts.append(f"b. {birth_date}")
        
        if death_date:
            label_parts.append(f"d. {death_date}")
        elif person_data.get('died', '').strip().upper() not in ['L', '']:
            label_parts.append("deceased")
            
        if marriage_date:
            label_parts.append(f"m. {marriage_date}")
        
        # Use HTML-like label for better formatting
        label = "\\n".join(label_parts)
        
        return {
            "name": person_data.get('name', 'Unknown'),
            "label": label
        }
    
    def _add_optimized_relationships(self):
        """Add relationships with optimized layout"""
        # Track processed relationships to avoid duplicates
        processed_relationships = set()
        
        # Add parent-child relationships
        for person_id, person_data in self.characters.items():
            father_id = person_data.get('father_id')
            mother_id = person_data.get('mother_id')
            
            # Add father relationship
            if father_id and father_id in self.characters:
                relationship_key = f"{father_id}->{person_id}"
                if relationship_key not in processed_relationships:
                    self.dot.edge(father_id, person_id, color="blue", style="solid")
                    processed_relationships.add(relationship_key)
            
            # Add mother relationship
            if mother_id and mother_id in self.characters:
                relationship_key = f"{mother_id}->{person_id}"
                if relationship_key not in processed_relationships:
                    self.dot.edge(mother_id, person_id, color="red", style="solid")
                    processed_relationships.add(relationship_key)
        
        # Add spouse relationships
        for person_id, person_data in self.characters.items():
            spouse_id = person_data.get('spouse_id')
            if spouse_id and spouse_id in self.characters:
                # Only add one direction to avoid duplicate edges
                if person_id < spouse_id:
                    relationship_key = f"{person_id}--{spouse_id}"
                    if relationship_key not in processed_relationships:
                        self.dot.edge(person_id, spouse_id, 
                                     color="purple", style="dashed", 
                                     constraint="false")
                        processed_relationships.add(relationship_key)
    
    def generate_visualization(self, output_format: str = "svg", 
                             output_dir: Optional[str] = None) -> str:
        """
        Generate the family tree visualization.

        Args:
            output_format: Output format (svg, html, pdf, png)
            output_dir: Optional output directory
        Returns:
            str: Path to the generated output file
        """
        self.output_format = output_format
        if output_dir:
            self.output_dir = output_dir

        try:
            # Generate graph
            svg_path = self.generate_graph('svg')

            # If HTML format requested, generate HTML
            if output_format.lower() == 'html':
                return self._generate_html(svg_path)

            return svg_path
        except Exception as e:
            print(f"Error generating visualization: {e}")
            raise
    
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
    
    def get_output_file_path(self, format_extension: str) -> str:
        """Get the path to the output file."""
        return os.path.join(self.output_dir, f"{self.name}.{format_extension}")
    
    def get_svg_path(self) -> str:
        """Get the path to the SVG file."""
        return self.get_output_file_path('svg')
    
    def _add_relationship_edges(self, dot):
        """Add relationship edges to the graph."""
        # This method is required by the abstract base class
        # The actual relationship edges are added in _add_optimized_relationships
        pass
    
    def _create_node_info(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """Create node information for the character."""
        return self._create_optimized_node_info(character) 