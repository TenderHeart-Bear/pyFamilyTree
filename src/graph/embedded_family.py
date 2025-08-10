"""
Family tree implementation with embedded spouse relationships - box style
"""
import os
import datetime
from typing import Dict, Any, Set, Optional, Tuple
import graphviz
from .base import RelGraph
from ..data.xml_parser import FamilyTreeData
from ..core.path_manager import path_manager

class EmbeddedFamilyTreeGraph(RelGraph):
    """
    A family tree graph implementation that embeds spouse relationships
    using diamond nodes instead of dotted lines.
    """
    
    def __init__(self, xml_data_dir: str, output_dir: Optional[str] = None,
                 start_person_name: Optional[str] = None, generations_back: int = 0,
                 generations_forward: int = 0, output_format: str = "svg"):
        """
        Initialize the embedded family tree graph.
        
        Args:
            xml_data_dir: Directory containing XML data files
            output_dir: Directory to save output files (uses path_manager if not provided)
            start_person_name: Optional name of person to start from
            generations_back: Number of generations to show going back
            generations_forward: Number of generations to show going forward
            output_format: Output format (svg, pdf, png)
        """
        # Initialize base class (it will handle path management)
        super().__init__("embedded_family_tree", output_dir)
        
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
        
        # Initialize selected characters
        if start_person_name:
            self._select_relevant_characters(start_person_name, generations_back, generations_forward)
        else:
            self.characters = self.all_characters
            self.id_to_name_map = self.all_id_to_name_map
        
        # Pre-process spouse relationships
        self._process_spouse_relationships()

    def _create_node_info(self, character: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create node information from character data without middle names.
        
        Args:
            character: Dictionary containing character information
            
        Returns:
            Dict[str, Any]: Dictionary containing node information
        """
        # Get only the first name (no middle names)
        name = character.get("name", "Unknown")
        
        # Create label with birth and death dates only
        label_parts = [name]
        if character.get("birthday"):
            label_parts.append(f"b. {character['birthday']}")
        if character.get("date_of_death"):
            label_parts.append(f"d. {character['date_of_death']}")
            
        label = "\\n".join(label_parts)
        
        return {
            "name": character["id"],  # Use ID as node name
            "label": label,
            "URL": None
        }

    def _process_spouse_relationships(self) -> None:
        """Pre-process all spouse relationships to determine which nodes to display."""
        for person_id, person in self.characters.items():
            spouse_id = person.get('spouse_id')
            if spouse_id and spouse_id in self.characters:
                spouse_pair = tuple(sorted([person_id, spouse_id]))
                
                if spouse_pair not in self.processed_pairs:
                    # For now, always use the first ID as primary
                    self.processed_pairs[spouse_pair] = spouse_pair[0]
                    self.skip_nodes.add(spouse_pair[1])

    def _add_relationship_edges(self, dot: graphviz.Graph) -> None:
        """Add edges for family relationships."""
        completed_unions = set()
        
        # First pass: Create union nodes for parent relationships
        for person_id, person in self.characters.items():
            if person_id in self.skip_nodes:
                continue
                
            spouse_id = person.get('spouse_id')
            if spouse_id and spouse_id in self.characters:
                # Skip if this union has already been processed
                union_key = tuple(sorted([person_id, spouse_id]))
                if union_key in completed_unions:
                    continue
                
                completed_unions.add(union_key)
                
                # Create a diamond node for the spouse union
                union_id = f"{person_id}-x-{spouse_id}"
                
                # Create spouse cluster to keep them at same rank
                with dot.subgraph(name=f'cluster_spouse_{person_id}_{spouse_id}') as sp_cluster:
                    sp_cluster.attr(rank='same')
                    # Add invisible edge to maintain horizontal alignment
                    dot.edge(person_id, spouse_id, style='invis', constraint='false')
                    # Create the union node
                    sp_cluster.node(
                        union_id,
                        shape="diamond",
                        width="0.15",
                        height="0.15",
                        style="filled",
                        fillcolor="black",
                        label=""
                    )
                
                # Create edges to diamond node with tighter dotted style
                print(f"\tCreated spouse edge: {person_id} ({person.get('name', 'Unknown')})")
                dot.edge(person_id, union_id, style='dotted', dir='none', len='0.75', constraint='false')
                dot.edge(spouse_id, union_id, style='dotted', dir='none', len='0.75', constraint='false')

    def _select_relevant_characters(self, start_person_name: str, generations_back: int, generations_forward: int) -> None:
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

    def _get_ancestors(self, person_id: str, remaining_generations: int, collected_ids: Set[str]) -> None:
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

    def _get_descendants(self, person_id: str, remaining_generations: int, collected_ids: Set[str]) -> None:
        """Recursively collect descendant IDs."""
        if remaining_generations <= 0:
            return
        
        # Find all characters that have this person as a parent
        for char_id, char_data in self.all_characters.items():
            if (char_data.get('father_id') == person_id or 
                char_data.get('mother_id') == person_id):
                collected_ids.add(char_id)
                self._get_descendants(char_id, remaining_generations - 1, collected_ids)

    def generate_graph(self, file_format: str = "svg") -> str:
        """
        Generate the embedded family tree graph with proper hierarchical layout.
        
        Args:
            file_format: Output format (default: svg)
            
        Returns:
            str: Path to the generated graph file
        """
        # Create a new directed graph
        self.dot = graphviz.Digraph(
            self.name,
            filename=self.dot_path,
            format=file_format,
            engine='dot'
        )
        
        # Configure graph for hierarchical family tree layout
        self.dot.attr(rankdir='TB')  # Top to bottom (oldest to newest)
        self.dot.attr(splines='false')  # Use straight lines for cleaner look
        self.dot.attr(nodesep='0.5')  # Horizontal spacing between nodes
        self.dot.attr(ranksep='1.2')  # Vertical spacing between generations
        self.dot.attr(ordering='out')  # Order nodes by outgoing edges
        self.dot.attr(concentrate='true')  # Merge edges where possible
        self.dot.attr(dpi='300')  # High DPI for better zoom quality
        
        # Node styling for family tree
        self.dot.attr('node', 
                      shape='box',
                      style='rounded,filled',
                      fillcolor='white',
                      fontname='Arial',
                      fontsize='12',
                      margin='0.3,0.2',
                      width='2.0',
                      height='1.2',
                      color='black',
                      penwidth='1',
                      class_='node')  # Add class for JavaScript
        
        # Edge styling - clean black lines
        self.dot.attr('edge',
                      color='black',
                      fontsize='8',
                      arrowsize='0.8',
                      penwidth='1')
        
        # Calculate generations and organize by hierarchy
        generations = self._calculate_generations()
        
        # Find the root generation (oldest) and adjust
        if generations:
            min_gen = min(generations.values())
            max_gen = max(generations.values())
            print(f"DEBUG: Embedded tree generation range: {min_gen} to {max_gen}")
            
            # Adjust generations so oldest is 0
            adjusted_generations = {}
            for char_id, gen in generations.items():
                adjusted_generations[char_id] = gen - min_gen
            generations = adjusted_generations
            
            # Group characters by generation level
            gen_groups = {}
            for char_id, gen_level in generations.items():
                if char_id not in self.skip_nodes:  # Only include visible nodes
                    if gen_level not in gen_groups:
                        gen_groups[gen_level] = []
                    gen_groups[gen_level].append(char_id)
            
            print(f"DEBUG: Embedded generation groups: {[(gen, len(chars)) for gen, chars in gen_groups.items()]}")
            
            # Create subgraphs for each generation
            for gen_level in sorted(gen_groups.keys()):
                chars_in_gen = gen_groups[gen_level]
                
                with self.dot.subgraph(name=f'cluster_gen_{gen_level}') as gen_subgraph:
                    gen_subgraph.attr(rank='same')
                    gen_subgraph.attr(style='invis')
                    
                    # Add nodes for this generation
                    for char_id in chars_in_gen:
                        if char_id in self.characters and char_id not in self.skip_nodes:
                            self._add_embedded_person_node(gen_subgraph, char_id, gen_level)
        
        # Add family relationship edges
        self._add_embedded_family_edges()
        
        # Generate the output file
        try:
            self.dot.render(cleanup=True)
            output_path = self.get_output_file_path(file_format)
            print(f"DEBUG: Generated hierarchical embedded family tree: {output_path}")
            print(f"DEBUG: File exists: {os.path.exists(output_path)}")
            return output_path
        except Exception as e:
            print(f"ERROR: Error generating embedded graph: {str(e)}")
            raise e

    def _add_embedded_person_node(self, graph: graphviz.Digraph, char_id: str, generation: int):
        """Add a person node with embedded spouse information"""
        if char_id not in self.characters or char_id in self.skip_nodes:
            return
        
        char_data = self.characters[char_id]
        
        # Check if this person has a spouse that should be embedded
        spouse_id = char_data.get('spouse_id')
        if spouse_id and spouse_id in self.characters and spouse_id not in self.skip_nodes:
            # Create combined node for spouse pair
            spouse_data = self.characters[spouse_id]
            combined_label = self._create_combined_spouse_label(char_data, spouse_data)
            
            # Use the first person's ID as the node ID
            node_id = char_id
            
            graph.node(
                node_id,
                label=combined_label,
                fillcolor='white',
                tooltip=f"Generation {generation} - Married Couple",
                width='2.5',  # Wider for couple
                height='1.2'
            )
            
            # Mark spouse as processed so it doesn't get its own node
            self.skip_nodes.add(spouse_id)
        else:
            # Single person node
            node_info = self._create_node_info(char_data)
            
            graph.node(
                node_info["name"],
                label=node_info["label"],
                fillcolor='white',
                tooltip=f"Generation {generation}"
            )

    def _create_combined_spouse_label(self, person1_data: Dict[str, Any], person2_data: Dict[str, Any]) -> str:
        """Create a combined label for a married couple without middle names"""
        # Get only first names (no middle names)
        name1 = person1_data.get('name', 'Unknown')
        name2 = person2_data.get('name', 'Unknown')
        
        # Get birth dates
        birth1 = person1_data.get('birthday', '')
        birth2 = person2_data.get('birthday', '')
        
        # Get death dates
        death1 = person1_data.get('date_of_death', '')
        death2 = person2_data.get('date_of_death', '')
        
        # Create combined label
        label_parts = [f"{name1} & {name2}"]
        
        if birth1:
            label_parts.append(f"{name1}: b. {birth1}")
        if birth2:
            label_parts.append(f"{name2}: b. {birth2}")
        
        if death1:
            label_parts.append(f"{name1}: d. {death1}")
        if death2:
            label_parts.append(f"{name2}: d. {death2}")
        
        return "\\n".join(label_parts)

    def _add_embedded_family_edges(self):
        """Add simple family relationship edges for embedded family tree"""
        # Add simple parent-child relationships
        for char_id, char_data in self.characters.items():
            if char_id in self.skip_nodes:
                continue
            
            # Find the actual node ID for this child (might be embedded with spouse)
            child_node_id = self._get_node_id_for_person(char_id)
            if not child_node_id:
                continue
            
            # Get parent information
            father_id = char_data.get('father_id')
            mother_id = char_data.get('mother_id')
            
            # Add direct connection from father to child
            if father_id and father_id in self.characters:
                parent_node_id = self._get_node_id_for_person(father_id)
                if parent_node_id:
                    self.dot.edge(parent_node_id, child_node_id,
                                 color='black',
                                 arrowhead='normal',
                                 weight='10')
            
            # Add direct connection from mother to child (only if no father connection)
            elif mother_id and mother_id in self.characters:
                parent_node_id = self._get_node_id_for_person(mother_id)
                if parent_node_id:
                    self.dot.edge(parent_node_id, child_node_id,
                                 color='black',
                                 arrowhead='normal',
                                 weight='10')

    def _get_node_id_for_person(self, person_id: str) -> Optional[str]:
        """Get the actual node ID for a person (considering embedded spouses)"""
        if person_id in self.skip_nodes:
            # This person is embedded in their spouse's node
            # Find the spouse whose node contains this person
            for char_id, char_data in self.characters.items():
                if char_data.get('spouse_id') == person_id and char_id not in self.skip_nodes:
                    return char_id
            return None
        else:
            return person_id

    def _calculate_generations(self) -> Dict[str, int]:
        """Calculate generation numbers for all characters"""
        generations = {}
        
        def calculate_gen(char_id: str, visited: set, depth: int = 0) -> int:
            # Prevent infinite recursion
            if depth > 20:
                return 0
            
            if char_id in generations:
                return generations[char_id]
            
            if char_id in visited:
                return 0  # Handle cycles
            
            visited.add(char_id)
            char = self.characters.get(char_id)
            if not char:
                return 0
            
            # Get parent IDs
            father_id = char.get('father_id')
            mother_id = char.get('mother_id')
            
            # If no parents, this person is in the root generation
            if not father_id and not mother_id:
                gen = 0
            else:
                # Calculate parent generations
                parent_gens = []
                if father_id and father_id in self.characters:
                    parent_gens.append(calculate_gen(father_id, visited.copy(), depth + 1))
                if mother_id and mother_id in self.characters:
                    parent_gens.append(calculate_gen(mother_id, visited.copy(), depth + 1))
                
                # This generation is one more than the maximum parent generation
                gen = max(parent_gens) + 1 if parent_gens else 0
            
            generations[char_id] = gen
            return gen
        
        # Calculate generations for all characters
        for char_id in self.characters:
            if char_id not in generations:
                calculate_gen(char_id, set())
        
        return generations
    
    def generate_visualization(self, output_format: str = "svg", output_dir: Optional[str] = None) -> str:
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