"""
XML parser for family tree data.
Handles parsing XML files into character dictionaries and manages character data.
"""
import os
import xml.etree.ElementTree as et
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..core.models.person import Person
from ..core.models.relationship import Relationship, RelationType

class CharacterData:
    """Class to handle character data parsing and management"""
    
    @staticmethod
    def parse_xml(tree: et.ElementTree) -> Dict[str, Any]:
        """
        Converts an XML ElementTree into a Character dictionary.
        
        Args:
            tree: ElementTree containing character data
            
        Returns:
            Dict[str, Any]: Dictionary containing parsed character data
        """
        if tree is None:
            print("Warning: Received None ElementTree")
            return {}
        
        root = tree.getroot()
        if root is None:
            print("Warning: XML tree has no root element")
            return {}
        
        character_data = {}

        # Extract all elements
        for child in root:
            if child is not None and child.text is not None and child.text.strip():
                key = child.tag.lower()
                value = child.text.strip()
                character_data[key] = value

        # Ensure critical fields exist
        critical_fields = [
            'id', 'name', 'middle_name', 'birthday', 'birth_place',
            'died', 'date_of_death', 'place_of_burial',
            'marital_status', 'marriage_date', 'place_of_marriage',
            'spouse', 'spouse_id',
            'father', 'father_id',
            'mother', 'mother_id'
        ]
        
        for field in critical_fields:
            if field not in character_data:
                character_data[field] = None
            elif character_data[field] == "":
                character_data[field] = None

        return character_data

class FamilyTreeData:
    """Class to manage the family tree data collection"""
    
    def __init__(self, root_folder: str):
        """
        Initialize the family tree data manager.
        
        Args:
            root_folder: Directory containing XML character files
        """
        self.root_folder = root_folder
        os.makedirs(root_folder, exist_ok=True)
        self.characters_by_id: Dict[str, Dict[str, Any]] = {}
        self.id_to_name_map: Dict[str, str] = {}
        self._load_characters()

    def _load_characters(self) -> None:
        """Load all character data from XML files in the root folder"""
        print("--- Loading character data ---")
        
        if not os.path.exists(self.root_folder):
            print(f"Warning: Directory {self.root_folder} does not exist")
            return
            
        xml_files = [f for f in os.listdir(self.root_folder) if f.endswith(".xml")]
        
        for item in sorted(xml_files):  # Sort for consistent loading order
            file_path = os.path.join(self.root_folder, item)
            if os.path.isfile(file_path):
                self._process_xml_file(file_path)
                    
        print(f"--- Loaded {len(self.characters_by_id)} characters and {len(self.id_to_name_map)} ID-to-name mappings ---")

    def _process_xml_file(self, file_path: str) -> None:
        """
        Process a single XML file and add its data to the collections.
        
        Args:
            file_path: Path to the XML file to process
        """
        if not file_path or not os.path.exists(file_path):
            print(f"Warning: XML file '{file_path}' does not exist")
            return
        
        try:
            tree = et.parse(file_path)
            character_dict = CharacterData.parse_xml(tree)
            
            char_id = character_dict.get("id")
            if not char_id:
                print(f"Warning: XML file '{file_path}' resulted in a character with no 'id'. Skipping.")
                return

            # Build display name from first and middle name
            name_parts = []
            if character_dict.get("name"):
                name_parts.append(character_dict["name"])
            if character_dict.get("middle_name"):
                name_parts.append(character_dict["middle_name"])
            display_name = " ".join(name_parts) if name_parts else None

            # Store character data
            self.characters_by_id[char_id] = character_dict
            
            # Update name mapping
            if display_name:
                self.id_to_name_map[char_id] = display_name
            else:
                self.id_to_name_map[char_id] = f"Unnamed Character ({char_id})"
                print(f"Warning: Character ID {char_id} from '{file_path}' has no name specified.")
        
        except et.ParseError as e:
            print(f"Error parsing XML file '{file_path}': {e}")
        except Exception as e:
            print(f"An unexpected error occurred while processing '{file_path}': {e}")

    def get_character(self, char_id: str) -> Optional[Dict[str, Any]]:
        """
        Get character data by ID.
        
        Args:
            char_id: ID of the character to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Character data or None if not found
        """
        if not char_id:
            return None
        return self.characters_by_id.get(char_id)

    def get_name(self, char_id: str) -> str:
        """
        Get character name by ID.
        
        Args:
            char_id: ID of the character
            
        Returns:
            str: Character name or a default string if not found
        """
        if not char_id:
            return "Unknown Character (No ID)"
        return self.id_to_name_map.get(char_id, f"Unknown Character ({char_id})")

    def get_all_characters(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all character data.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of all characters keyed by ID
        """
        return self.characters_by_id

    def get_id_name_map(self) -> Dict[str, str]:
        """
        Get the ID to name mapping.
        
        Returns:
            Dict[str, str]: Dictionary mapping character IDs to names
        """
        return self.id_to_name_map 