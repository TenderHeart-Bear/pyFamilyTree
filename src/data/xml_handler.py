"""
XML data provider implementation for the Family Tree application.
Handles reading and writing family tree data from/to XML files.
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from src.core.interfaces.data_provider import DataProvider
from src.core.models.person import Person
from src.core.models.relationship import Relationship, RelationType

class XMLDataProvider(DataProvider):
    """Implementation of DataProvider interface for XML files"""
    
    def __init__(self, data_directory: str):
        """Initialize with the directory containing XML files"""
        self.data_directory = data_directory
        os.makedirs(data_directory, exist_ok=True)
    
    def _get_xml_path(self, file_id: str) -> str:
        """Get full path for an XML file"""
        return os.path.join(self.data_directory, f"{file_id}.xml")
    
    def _parse_person_xml(self, xml_root: ET.Element) -> Dict[str, Any]:
        """Parse person data from XML element"""
        person_data = {
            'id': xml_root.get('id', ''),
            'first_name': xml_root.findtext('firstName', ''),
            'last_name': xml_root.findtext('lastName', ''),
            'birth_date': None,
            'death_date': None,
            'gender': xml_root.findtext('gender', None),
            'birth_place': xml_root.findtext('birthPlace', None),
            'death_place': xml_root.findtext('deathPlace', None),
            'occupation': xml_root.findtext('occupation', None),
            'notes': xml_root.findtext('notes', None)
        }
        
        # Parse dates if they exist
        birth_date = xml_root.findtext('birthDate', None)
        if birth_date:
            try:
                person_data['birth_date'] = datetime.strptime(birth_date, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        death_date = xml_root.findtext('deathDate', None)
        if death_date:
            try:
                person_data['death_date'] = datetime.strptime(death_date, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        return person_data
    
    def _create_person_xml(self, person: Dict[str, Any]) -> ET.Element:
        """Create XML element from person data"""
        root = ET.Element('person', id=person['id'])
        
        # Add basic fields
        ET.SubElement(root, 'firstName').text = person['first_name']
        ET.SubElement(root, 'lastName').text = person['last_name']
        
        # Add optional fields if they exist
        if person.get('birth_date'):
            ET.SubElement(root, 'birthDate').text = person['birth_date']
        if person.get('death_date'):
            ET.SubElement(root, 'deathDate').text = person['death_date']
        if person.get('gender'):
            ET.SubElement(root, 'gender').text = person['gender']
        if person.get('birth_place'):
            ET.SubElement(root, 'birthPlace').text = person['birth_place']
        if person.get('death_place'):
            ET.SubElement(root, 'deathPlace').text = person['death_place']
        if person.get('occupation'):
            ET.SubElement(root, 'occupation').text = person['occupation']
        if person.get('notes'):
            ET.SubElement(root, 'notes').text = person['notes']
            
        return root
    
    def get_person(self, person_id: str) -> Dict[str, Any]:
        """Retrieve person data by ID"""
        file_path = self._get_xml_path(person_id)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Person with ID {person_id} not found")
            
        tree = ET.parse(file_path)
        root = tree.getroot()
        return self._parse_person_xml(root)
    
    def save_person(self, person_data: Dict[str, Any]) -> str:
        """Save person data and return the ID"""
        person_id = person_data['id']
        root = self._create_person_xml(person_data)
        
        tree = ET.ElementTree(root)
        file_path = self._get_xml_path(person_id)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
        
        return person_id
    
    def update_person(self, person_id: str, person_data: Dict[str, Any]) -> bool:
        """Update person data"""
        try:
            person_data['id'] = person_id
            self.save_person(person_data)
            return True
        except Exception:
            return False
    
    def delete_person(self, person_id: str) -> bool:
        """Delete person data"""
        try:
            file_path = self._get_xml_path(person_id)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False
    
    def search_people(self, query: str) -> List[Dict[str, Any]]:
        """Search for people matching the query"""
        results = []
        query = query.lower()
        
        # Search through all XML files in the directory
        for filename in os.listdir(self.data_directory):
            if filename.endswith('.xml'):
                try:
                    file_path = os.path.join(self.data_directory, filename)
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    
                    person_data = self._parse_person_xml(root)
                    # Check if query matches any person fields
                    if (query in person_data['first_name'].lower() or
                        query in person_data['last_name'].lower() or
                        query in person_data.get('notes', '').lower()):
                        results.append(person_data)
                except Exception:
                    continue
                    
        return results
    
    # Note: Family and relationship methods would be implemented similarly
    # For now, returning placeholder implementations
    
    def get_family(self, family_id: str) -> Dict[str, Any]:
        """Retrieve family data by ID"""
        raise NotImplementedError("Family data not yet implemented")
    
    def save_family(self, family_data: Dict[str, Any]) -> str:
        """Save family data and return the ID"""
        raise NotImplementedError("Family data not yet implemented")
    
    def update_family(self, family_id: str, family_data: Dict[str, Any]) -> bool:
        """Update family data"""
        raise NotImplementedError("Family data not yet implemented")
    
    def delete_family(self, family_id: str) -> bool:
        """Delete family data"""
        raise NotImplementedError("Family data not yet implemented")
    
    def get_relationships(self, person_id: str) -> List[Dict[str, Any]]:
        """Retrieve all relationships for a person"""
        raise NotImplementedError("Relationships not yet implemented") 