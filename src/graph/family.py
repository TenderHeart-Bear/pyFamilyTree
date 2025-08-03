"""
Family tree specific graph implementation
"""
import os
import datetime
import re
from typing import Dict, Any, Set, Optional, List
import graphviz
from .base import RelGraph
from ..data.xml_parser import FamilyTreeData
from ..core.path_manager import path_manager

class FamilyTreeGraph(RelGraph):
    def __init__(self, xml_data_dir: str, output_dir: Optional[str] = None,
                 start_person_name: Optional[str] = None,
                 generations_back: int = 0, generations_forward: int = 0,
                 output_format: str = "svg"):
        """
        Initialize the family tree graph.
        
        Args:
            xml_data_dir: Directory containing XML data files
            output_dir: Directory to save the generated graph (uses path_manager if not provided)
            start_person_name: Optional name of person to start from
            generations_back: Number of generations to show going back
            generations_forward: Number of generations to show going forward
            output_format: Output format (svg, pdf, png)
        """
        # Initialize base class (it will handle path management)
        super().__init__("family_tree", output_dir)
        
        # Store parameters
        self.xml_data_dir = xml_data_dir
        self.output_format = output_format
        
        # Initialize data provider
        self.data_provider = FamilyTreeData(xml_data_dir)
        
        # Get all characters
        self.all_characters = self.data_provider.get_all_characters()
        self.all_id_to_name_map = self.data_provider.get_id_name_map()
        
        # Initialize selected characters
        if start_person_name:
            self._select_relevant_characters(start_person_name, generations_back, generations_forward)
        else:
            self.characters = self.all_characters
            self.id_to_name_map = self.all_id_to_name_map

    def _create_node_info(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates node information from character data.
        
        Args:
            character: Dictionary containing character information
            
        Returns:
            Dict[str, Any]: Dictionary containing node information
        """
        # Get the name
        name = character.get("name", "Unknown")
        
        # Create label with all available information
        label_parts = [name]
        
        # Add birthday if available
        if character.get("birthday"):
            label_parts.append(f"b. {character['birthday']}")
        
        # Add marriage date if available (use correct field name from XML)
        if character.get("marriage_date"):
            label_parts.append(f"m. {character['marriage_date']}")
        
        # Add death information - check multiple possible fields
        if character.get("date_of_death"):
            label_parts.append(f"d. {character['date_of_death']}")
        elif character.get("death"):
            label_parts.append(f"d. {character['death']}")
        elif character.get("died"):
            # Check died field - if it's not "L" (Living), show as deceased
            died_status = character.get("died", "").strip().upper()
            if died_status and died_status != "L":
                # If it contains a date, show it; otherwise show "deceased"
                if any(char.isdigit() for char in died_status):
                    label_parts.append(f"d. {died_status}")
                else:
                    label_parts.append("deceased")
        
        label = "\\n".join(label_parts)
        
        return {
            "name": character["id"],  # Use ID as node name
            "label": label,
            "URL": None
        }

    def _add_relationship_edges(self, dot: graphviz.Graph):
        """Add relationship edges using the simple relationships approach"""
        # Call the simple relationships method that this class uses
        self._add_simple_relationships(dot)

    def _select_relevant_characters(self, start_person_name: str, generations_back: int, generations_forward: int) -> None:
        """Select characters relevant to the visualization based on parameters."""
        print(f"DEBUG: Looking for person named '{start_person_name}'")
        print(f"DEBUG: Available names: {list(self.all_id_to_name_map.values())[:10]}...")  # Show first 10 names
        
        # Find starting person's ID - try exact match first, then partial match
        start_id = None
        potential_matches = []
        
        # Try exact match first
        for char_id, name in self.all_id_to_name_map.items():
            if name.lower() == start_person_name.lower():
                start_id = char_id
                print(f"DEBUG: Found exact matching person - ID: {char_id}, Name: {name}")
                break
        
        # If no exact match, try partial match (search name contains the input)
        if not start_id:
            for char_id, name in self.all_id_to_name_map.items():
                if start_person_name.lower() in name.lower():
                    potential_matches.append((char_id, name))
            
            # If we have potential matches, use the first one
            if potential_matches:
                start_id, matched_name = potential_matches[0]
                print(f"DEBUG: Found partial matching person - ID: {start_id}, Name: {matched_name}")
                if len(potential_matches) > 1:
                    print(f"DEBUG: Multiple potential matches found:")
                    for char_id, name in potential_matches:
                        print(f"  - {char_id}: {name}")
                    print(f"DEBUG: Using first match: {matched_name}")
        
        if not start_id:
            print(f"ERROR: Could not find person named '{start_person_name}'")
            print(f"DEBUG: Exact matches attempted with:")
            for char_id, name in self.all_id_to_name_map.items():
                if start_person_name.lower() in name.lower():
                    print(f"  - Partial match: {name} (ID: {char_id})")
            return
        
        # Collect relevant character IDs
        relevant_ids = {start_id}
        print(f"DEBUG: Starting from person {start_id} - {self.all_id_to_name_map[start_id]}")
        
        # Get ancestors if requested
        if generations_back > 0:
            print(f"DEBUG: Getting {generations_back} generations back")
            self._get_ancestors(start_id, generations_back, relevant_ids)
        
        # Get descendants if requested
        if generations_forward > 0:
            print(f"DEBUG: Getting {generations_forward} generations forward")
            self._get_descendants(start_id, generations_forward, relevant_ids)
        
        print(f"DEBUG: Found {len(relevant_ids)} relevant characters: {relevant_ids}")
        
        # Filter characters to only include relevant ones
        self.characters = {id: self.all_characters[id] for id in relevant_ids if id in self.all_characters}
        self.id_to_name_map = {id: self.all_id_to_name_map[id] for id in relevant_ids if id in self.all_id_to_name_map}
        
        print(f"DEBUG: Final character count: {len(self.characters)}")
        if len(self.characters) == 0:
            print("WARNING: No characters found for visualization!")

    def _get_ancestors(self, person_id: str, remaining_generations: int, collected_ids: Set[str]) -> None:
        """Recursively collect ancestor IDs."""
        if remaining_generations <= 0:
            return
        
        person = self.all_characters.get(person_id)
        if not person:
            print(f"DEBUG: Person {person_id} not found in all_characters")
            return
        
        # Check for parents
        father_id = person.get('father_id')
        mother_id = person.get('mother_id')
        
        print(f"DEBUG: Person {person_id} has father_id={father_id}, mother_id={mother_id}")
        
        # Add parents to collection and recurse
        if father_id and father_id in self.all_characters:
            collected_ids.add(father_id)
            print(f"DEBUG: Added father {father_id} ({self.all_id_to_name_map.get(father_id, 'Unknown')})")
            self._get_ancestors(father_id, remaining_generations - 1, collected_ids)
        
        if mother_id and mother_id in self.all_characters:
            collected_ids.add(mother_id)
            print(f"DEBUG: Added mother {mother_id} ({self.all_id_to_name_map.get(mother_id, 'Unknown')})")
            self._get_ancestors(mother_id, remaining_generations - 1, collected_ids)

    def _get_descendants(self, person_id: str, remaining_generations: int, collected_ids: Set[str]) -> None:
        """Recursively collect descendant IDs."""
        if remaining_generations <= 0:
            return
        
        children_found = 0
        # Find all characters that have this person as a parent
        for char_id, char_data in self.all_characters.items():
            if (char_data.get('father_id') == person_id or 
                char_data.get('mother_id') == person_id):
                collected_ids.add(char_id)
                children_found += 1
                print(f"DEBUG: Added child {char_id} ({self.all_id_to_name_map.get(char_id, 'Unknown')}) of {person_id}")
                self._get_descendants(char_id, remaining_generations - 1, collected_ids)
        
        if children_found == 0:
            print(f"DEBUG: No children found for {person_id} ({self.all_id_to_name_map.get(person_id, 'Unknown')})")

    def _generate_svg(self) -> str:
        """Generate the SVG file with optimized family tree layout"""
        # Create a new directed graph with optimized layout for smaller size
        self.dot = graphviz.Digraph(
            self.name,
            filename=self.dot_path,
            format='svg',
            engine='dot'
        )
        
        # Configure graph for complete content display
        self.dot.attr(rankdir='TB')          # Top to bottom layout
        self.dot.attr(nodesep='0.5')         # Reduced horizontal spacing
        self.dot.attr(ranksep='0.8')         # Reduced vertical spacing
        self.dot.attr(concentrate='true')    # Merge edges where possible
        # Removed size constraint to allow full content to be displayed
        self.dot.attr(dpi='72')              # Lower DPI to prevent over-scaling
        self.dot.attr(ratio='fill')          # Fill the available space
        self.dot.attr(overlap='false')       # Prevent node overlap
        
        # Node styling - smaller nodes
        self.dot.attr('node', 
                      shape='box',
                      style='rounded,filled',
                      fillcolor='lightgray',
                      fontname='Arial',
                      fontsize='10',
                      margin='0.2,0.1',
                      width='1.5',
                      height='0.8',
                      class_='node')  # Add class for JavaScript
        
        # Edge styling
        self.dot.attr('edge',
                      color='black',
                      fontsize='8',
                      arrowsize='0.5')
        
        # Add all person nodes
        for person_id, person_data in self.characters.items():
            node_info = self._create_node_info(person_data)
            # Add HTML-compatible attributes for interactivity
            self.dot.node(node_info["name"], 
                          label=node_info["label"],
                          tooltip=f"Click to view details for {person_data.get('name', person_id)}")
        
        # Add relationship edges
        self._add_simple_relationships()
        
        # Generate the output file
        try:
            self.dot.render(cleanup=True)
            output_path = self.get_output_file_path('svg')
            print(f"DEBUG: Generated simple family tree SVG: {output_path}")
            print(f"DEBUG: File exists: {os.path.exists(output_path)}")
            return output_path
        except Exception as e:
            print(f"ERROR: Error generating graph: {str(e)}")
            # Try to save just the DOT file as fallback
            try:
                dot_file = self.dot_path
                self.dot.save(dot_file)
                print(f"WARNING: Could not render, but DOT file saved at: {dot_file}")
                return dot_file
            except Exception as e2:
                print(f"ERROR: Could not save DOT file either: {str(e2)}")
            raise e

    def _add_simple_relationships(self, dot=None):
        """Add relationship edges using diamond union nodes for clean family structure"""
        # Use the passed dot parameter or fall back to self.dot for backward compatibility
        if dot is None:
            dot = self.dot
        processed_unions = set()
        
        # First, create diamond union nodes for marriages and connect parents
        for person_id, person_data in self.characters.items():
            spouse_id = person_data.get('spouse_id')
            if spouse_id and spouse_id in self.characters:
                union_key = tuple(sorted([person_id, spouse_id]))
                if union_key not in processed_unions:
                    processed_unions.add(union_key)
                    
                    # Create diamond union node with consistent ID
                    union_id = f"union_{union_key[0]}_{union_key[1]}"
                    dot.node(union_id, 
                                 label="", 
                                 shape="diamond", 
                                 width="0.2", 
                                 height="0.2",
                                 style="filled",
                                 fillcolor="lightcoral")
                    
                    # Create invisible spacer node to force spouses to be adjacent
                    spacer_id = f"spacer_{union_key[0]}_{union_key[1]}"
                    dot.node(spacer_id,
                                 label="",
                                 shape="point",
                                 width="0.01",
                                 height="0.01",
                                 style="invis")
                    
                    # Create cluster to group spouses together
                    cluster_name = f"cluster_marriage_{union_key[0]}_{union_key[1]}"
                    with dot.subgraph(name=cluster_name) as marriage_cluster:
                        marriage_cluster.attr(style="invis")
                        marriage_cluster.attr(rank="same")
                        
                        # Add spouses and spacer to cluster
                        marriage_cluster.node(union_key[0])
                        marriage_cluster.node(spacer_id)
                        marriage_cluster.node(union_key[1])
                        
                        # Force ordering with invisible edges
                        marriage_cluster.edge(union_key[0], spacer_id, style="invis")
                        marriage_cluster.edge(spacer_id, union_key[1], style="invis")
                    
                    # Connect spouses to diamond (Parent1 -- Diamond -- Parent2)
                    dot.edge(union_key[0], union_id, arrowhead="none")
                    dot.edge(union_key[1], union_id, arrowhead="none")
        
        # Second, find children groups and create circle nodes
        union_children = {}  # Maps union_id to list of children
        
        for person_id, person_data in self.characters.items():
            father_id = person_data.get('father_id')
            mother_id = person_data.get('mother_id')
            
            if father_id and mother_id and father_id in self.characters and mother_id in self.characters:
                # Find the union for these parents
                union_key = tuple(sorted([father_id, mother_id]))
                union_id = f"union_{union_key[0]}_{union_key[1]}"
                
                if union_id not in union_children:
                    union_children[union_id] = []
                union_children[union_id].append(person_id)
        
        # Third, create circle nodes for children groups and connect them
        for union_id, children in union_children.items():
            if children:  # Only if there are children
                children_id = f"children_{union_id}"
                
                # Create circle node for children group
                dot.node(children_id,
                             label="",
                             shape="circle",
                             width="0.1",
                             height="0.1",
                             style="filled",
                             fillcolor="lightblue")
                
                # Connect union diamond to children circle
                dot.edge(union_id, children_id, arrowhead="none", color="darkblue")
                
                # Create cluster for children to keep them together
                children_cluster_name = f"cluster_children_{union_id}"
                with dot.subgraph(name=children_cluster_name) as children_cluster:
                    children_cluster.attr(style="invis")
                    children_cluster.attr(rank="same")
                    
                    # Add all children to the cluster
                    for child_id in children:
                        children_cluster.node(child_id)
                    
                    # Connect children circle to each child (green lines to top of child nodes)
                    for child_id in children:
                        dot.edge(children_id, child_id, headport="n", color="green")
        
        # Handle single-parent children (if any)
        for person_id, person_data in self.characters.items():
            father_id = person_data.get('father_id')
            mother_id = person_data.get('mother_id')
            
            # Single parent cases
            if (father_id and father_id in self.characters and 
                (not mother_id or mother_id not in self.characters)):
                # Father only
                dot.edge(father_id, person_id, style="dashed", color="gray")
            elif (mother_id and mother_id in self.characters and 
                  (not father_id or father_id not in self.characters)):
                # Mother only
                dot.edge(mother_id, person_id, style="dashed", color="gray")

    def _add_person_node(self, graph: graphviz.Digraph, char_id: str, generation: int):
        """Add a person node to the graph - simplified version"""
        if char_id not in self.characters:
            return
        
        char_data = self.characters[char_id]
        node_info = self._create_node_info(char_data)
        
        # Create the node with simple styling
        graph.node(
            node_info["name"],
            label=node_info["label"]
        )

    def _group_spouses_in_generation(self, chars_in_gen: list) -> list:
        """Deprecated - using simple approach now"""
        return [[char_id] for char_id in chars_in_gen]

    def _add_family_connections(self):
        """Deprecated - using simple relationships now"""
        pass

    def _add_simple_parent_child_connections(self):
        """Deprecated - merged into _add_simple_relationships"""
        pass

    def _add_parent_child_connections(self):
        """Deprecated - using simple approach now"""
        pass

    def _calculate_generations(self) -> Dict[str, int]:
        """
        Deprecated - moved to future enhancement.
        For now, return empty dict to maintain compatibility.
        """
        return {}

    def addNode(self, dot: graphviz.Graph, character: Dict[str, Any]) -> str:
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
        
        # Skip if node already exists
        if f'\t"{node_id}"' in dot.body:
            return node_id
        
        # Create node with proper styling
        dot.node(
            node_id,
            label=node_label,
            shape='box',
            style='rounded,filled',
            fillcolor='white',
            color='black',
            fontname='Arial',
            fontsize='10',
            height='0.5',
            width='1.5'
        )
        
        return node_id

    def _format_node_label(self, char_data):
        """Format the label for a person node."""
        name = char_data.get('name', 'Unknown')
        birth = char_data.get('birth', '')
        marriage = char_data.get('marriage', '')
        death = char_data.get('death', '')
        
        # Format dates
        birth_str = f"b. {birth}" if birth else ""
        marriage_str = f"m. {marriage}" if marriage else ""
        death_str = f"d. {death}" if death else ""
        
        # Combine dates if both exist
        dates = ""
        if birth_str and death_str and marriage_str:
            dates = f"\\n{birth_str}\\n{marriage_str}\\n{death_str}"
        elif birth_str:
            dates = f"\\n{birth_str}"
        elif marriage_str:
            dates = f"\\n{marriage_str}"
        elif death_str:
            dates = f"\\n{death_str}"
        
        return f"{name}{dates}"

    def generate_high_quality_png(self) -> str:
        """
        Generate a high-quality PNG version of the family tree for better zoom quality.
        
        Returns:
            str: Path to the generated PNG file
        """
        # Create a copy of the graph with higher DPI settings
        high_dpi_dot = graphviz.Digraph(
            self.name + "_hq",
            filename=self.dot_path.replace('.dot', '_hq.dot'),
            format='png',
            engine='dot'
        )
        
        # Copy all attributes from the main graph
        for attr_name, attr_value in self.dot.graph_attr.items():
            high_dpi_dot.attr(attr_name, attr_value)
        
        # Override DPI for high quality
        high_dpi_dot.attr(dpi='600')  # Very high DPI for crisp text
        high_dpi_dot.attr(resolution='600')
        
        # Copy node attributes
        for attr_name, attr_value in self.dot.node_attr.items():
            high_dpi_dot.attr('node', **{attr_name: attr_value})
        
        # Copy edge attributes  
        for attr_name, attr_value in self.dot.edge_attr.items():
            high_dpi_dot.attr('edge', **{attr_name: attr_value})
        
        # Copy all nodes
        for node in self.dot.body:
            if '\t' in node and '->' not in node and '--' not in node:
                high_dpi_dot.body.append(node)
        
        # Copy all edges
        for edge in self.dot.body:
            if '->' in edge or '--' in edge:
                high_dpi_dot.body.append(edge)
        
        # Generate high-quality PNG
        try:
            high_dpi_dot.render(cleanup=True)
            hq_output_path = self.get_output_file_path('png').replace('.png', '_hq.png')
            print(f"DEBUG: Generated high-quality PNG: {hq_output_path}")
            return hq_output_path
        except Exception as e:
            print(f"ERROR: Error generating high-quality PNG: {str(e)}")
            raise e

    def _configure_graph_attributes(self):
        """Configure graph layout attributes for optimal size and layout"""
        # Set graph layout direction and spacing
        self.dot.attr(rankdir='TB')  # Top to bottom
        self.dot.attr(nodesep='0.5')  # Reduced node separation
        self.dot.attr(ranksep='0.8')  # Reduced rank separation
        self.dot.attr(concentrate='true')  # Merge edges where possible
        
        # Removed size constraint to allow full content to be displayed
        self.dot.attr(dpi='72')  # Lower DPI to prevent over-scaling
        self.dot.attr(ratio='fill')  # Fill the available space
        self.dot.attr(overlap='false')  # Prevent node overlap
        self.dot.attr(splines='ortho')  # Use orthogonal edges for cleaner layout
        
        # Configure node defaults for smaller, cleaner appearance
        self.dot.attr('node', 
                     shape='box',
                     style='rounded,filled',
                     fillcolor='lightgray',
                     fontname='Arial',
                     fontsize='10',
                     margin='0.2,0.1',  # Reduced margin
                     width='1.5',  # Fixed smaller width
                     height='0.8')  # Fixed smaller height
        
        # Configure edge defaults
        self.dot.attr('edge', 
                     fontsize='8',
                     fontname='Arial')

 