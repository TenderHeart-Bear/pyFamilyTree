"""
Relationship model representing connections between people in the family tree
"""
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import date
from enum import Enum, auto

class RelationType(Enum):
    """Types of relationships between people"""
    PARENT = auto()
    CHILD = auto()
    SPOUSE = auto()
    SIBLING = auto()

@dataclass
class Relationship:
    """
    Represents a relationship between two people in the family tree
    """
    id: str
    person1_id: str
    person2_id: str
    relationship_type: RelationType
    start_date: Optional[date] = None  # Marriage date for spouses, birth date for parent-child
    end_date: Optional[date] = None    # Divorce/death date for spouses
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert relationship to dictionary representation"""
        return {
            'id': self.id,
            'person1_id': self.person1_id,
            'person2_id': self.person2_id,
            'relationship_type': self.relationship_type.name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Relationship':
        """Create relationship from dictionary representation"""
        # Convert date strings to date objects if they exist
        start_date = date.fromisoformat(data['start_date']) if data.get('start_date') else None
        end_date = date.fromisoformat(data['end_date']) if data.get('end_date') else None
        
        return cls(
            id=data['id'],
            person1_id=data['person1_id'],
            person2_id=data['person2_id'],
            relationship_type=RelationType[data['relationship_type']],
            start_date=start_date,
            end_date=end_date,
            notes=data.get('notes')
        ) 