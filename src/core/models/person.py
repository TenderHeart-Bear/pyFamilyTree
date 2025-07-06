"""
Person model representing an individual in the family tree
"""
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import date

@dataclass
class Person:
    """
    Represents a person in the family tree
    """
    id: str
    first_name: str
    last_name: str
    birth_date: Optional[date] = None
    death_date: Optional[date] = None
    gender: Optional[str] = None
    birth_place: Optional[str] = None
    death_place: Optional[str] = None
    occupation: Optional[str] = None
    notes: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Get person's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> Optional[int]:
        """Calculate person's age"""
        if not self.birth_date:
            return None
        
        end_date = self.death_date if self.death_date else date.today()
        return end_date.year - self.birth_date.year - (
            (end_date.month, end_date.day) < (self.birth_date.month, self.birth_date.day)
        )
    
    def to_dict(self) -> Dict:
        """Convert person to dictionary representation"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'death_date': self.death_date.isoformat() if self.death_date else None,
            'gender': self.gender,
            'birth_place': self.birth_place,
            'death_place': self.death_place,
            'occupation': self.occupation,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Person':
        """Create person from dictionary representation"""
        # Convert date strings to date objects if they exist
        birth_date = date.fromisoformat(data['birth_date']) if data.get('birth_date') else None
        death_date = date.fromisoformat(data['death_date']) if data.get('death_date') else None
        
        return cls(
            id=data['id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            birth_date=birth_date,
            death_date=death_date,
            gender=data.get('gender'),
            birth_place=data.get('birth_place'),
            death_place=data.get('death_place'),
            occupation=data.get('occupation'),
            notes=data.get('notes')
        ) 