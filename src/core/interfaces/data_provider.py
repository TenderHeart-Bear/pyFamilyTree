"""
Abstract interfaces for data providers in the Family Tree application.
These interfaces ensure consistency across different data sources (local files, future web API, etc.)
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class DataProvider(ABC):
    """Abstract base class for data providers"""
    
    @abstractmethod
    def get_person(self, person_id: str) -> Dict[str, Any]:
        """Retrieve person data by ID"""
        pass
    
    @abstractmethod
    def get_family(self, family_id: str) -> Dict[str, Any]:
        """Retrieve family data by ID"""
        pass
    
    @abstractmethod
    def get_relationships(self, person_id: str) -> List[Dict[str, Any]]:
        """Retrieve all relationships for a person"""
        pass
    
    @abstractmethod
    def save_person(self, person_data: Dict[str, Any]) -> str:
        """Save person data and return the ID"""
        pass
    
    @abstractmethod
    def save_family(self, family_data: Dict[str, Any]) -> str:
        """Save family data and return the ID"""
        pass
    
    @abstractmethod
    def update_person(self, person_id: str, person_data: Dict[str, Any]) -> bool:
        """Update person data"""
        pass
    
    @abstractmethod
    def update_family(self, family_id: str, family_data: Dict[str, Any]) -> bool:
        """Update family data"""
        pass
    
    @abstractmethod
    def delete_person(self, person_id: str) -> bool:
        """Delete person data"""
        pass
    
    @abstractmethod
    def delete_family(self, family_id: str) -> bool:
        """Delete family data"""
        pass
    
    @abstractmethod
    def search_people(self, query: str) -> List[Dict[str, Any]]:
        """Search for people matching the query"""
        pass

class TreeProcessor(ABC):
    """Abstract base class for tree processing operations"""
    
    @abstractmethod
    def get_ancestors(self, person_id: str, generations: int) -> Dict[str, Any]:
        """Get ancestors for a person up to specified generations"""
        pass
    
    @abstractmethod
    def get_descendants(self, person_id: str, generations: int) -> Dict[str, Any]:
        """Get descendants for a person up to specified generations"""
        pass
    
    @abstractmethod
    def get_family_tree(self, person_id: str, generations_up: int, generations_down: int) -> Dict[str, Any]:
        """Get complete family tree for a person"""
        pass
    
    @abstractmethod
    def validate_tree(self, tree_data: Dict[str, Any]) -> List[str]:
        """Validate tree data and return list of errors if any"""
        pass 