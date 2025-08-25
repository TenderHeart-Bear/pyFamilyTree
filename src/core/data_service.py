"""
Family Tree Data Service Layer
Provides centralized data management with support for:
- XML file loading (current system)
- Offline database (SQLite for private data)
- Online database (PostgreSQL/MySQL for shared data)
- Caching and performance optimization
"""

import os
import sqlite3
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum

from ..data.xml_parser import FamilyTreeData


class DataSource(Enum):
    """Data source types"""
    XML_FILES = "xml"
    OFFLINE_DB = "offline_db"
    ONLINE_DB = "online_db"
    CACHE = "cache"


class FamilyDataService:
    """
    Centralized data service that handles multiple data sources
    and eliminates double loading issues.
    """
    
    def __init__(self, offline_db_path: Optional[str] = None):
        # Cache storage
        self._cached_characters: Optional[Dict[str, Dict[str, Any]]] = None
        self._cached_id_to_name_map: Optional[Dict[str, str]] = None
        self._current_data_source: Optional[str] = None
        self._last_loaded: Optional[datetime] = None
        
        # Data providers
        self._xml_provider: Optional[FamilyTreeData] = None
        self._offline_db_path = offline_db_path or "data/family_tree_offline.db"
        self._online_db_connection = None  # Will be implemented later
        
        # Configuration
        self._prefer_offline = True  # Default to offline-first
        self._auto_sync = False  # Auto-sync to online DB
        
        print("DEBUG: FamilyDataService initialized")
    
    def set_preferences(self, prefer_offline: bool = True, auto_sync: bool = False):
        """Configure data service preferences"""
        self._prefer_offline = prefer_offline
        self._auto_sync = auto_sync
        print(f"DEBUG: Data preferences set - offline_first: {prefer_offline}, auto_sync: {auto_sync}")
    
    def load_from_xml(self, xml_data_dir: str, force_reload: bool = False) -> bool:
        """
        Load data from XML files (current system)
        
        Args:
            xml_data_dir: Path to XML files directory
            force_reload: Force reload even if already cached
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if we need to reload
            if not force_reload and self._current_data_source == xml_data_dir and self._cached_characters:
                print(f"DEBUG: Using cached XML data from {xml_data_dir}")
                return True
            
            print(f"DEBUG: Loading XML data from {xml_data_dir}")
            
            # Load from XML
            self._xml_provider = FamilyTreeData(xml_data_dir)
            self._cached_characters = self._xml_provider.get_all_characters()
            self._cached_id_to_name_map = self._xml_provider.get_id_name_map()
            
            # Update cache metadata
            self._current_data_source = xml_data_dir
            self._last_loaded = datetime.now()
            
            print(f"DEBUG: Successfully loaded {len(self._cached_characters)} characters from XML")
            
            # Auto-save to offline database if enabled
            if self._prefer_offline:
                self._save_to_offline_db()
            
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to load XML data: {str(e)}")
            return False
    
    def load_from_offline_db(self, tree_name: str = "default") -> bool:
        """
        Load data from offline SQLite database
        
        Args:
            tree_name: Name of the family tree to load
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"DEBUG: Loading data from offline database: {tree_name}")
            
            # TODO: Implement SQLite loading
            # This will be implemented in the next phase
            print("DEBUG: Offline database loading not yet implemented")
            return False
            
        except Exception as e:
            print(f"ERROR: Failed to load from offline database: {str(e)}")
            return False
    
    def load_from_online_db(self, tree_id: str, user_token: str) -> bool:
        """
        Load data from online database
        
        Args:
            tree_id: ID of the shared family tree
            user_token: User authentication token
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"DEBUG: Loading data from online database: tree {tree_id}")
            
            # TODO: Implement online database loading
            # This will be implemented when sharing features are added
            print("DEBUG: Online database loading not yet implemented")
            return False
            
        except Exception as e:
            print(f"ERROR: Failed to load from online database: {str(e)}")
            return False
    
    def get_characters(self) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Get all characters from current data source
        
        Returns:
            Dictionary of character data or None if no data loaded
        """
        if self._cached_characters is None:
            print("WARNING: No character data loaded")
            return None
        
        print(f"DEBUG: Returning {len(self._cached_characters)} cached characters")
        return self._cached_characters
    
    def get_id_name_map(self) -> Optional[Dict[str, str]]:
        """
        Get ID to name mapping from current data source
        
        Returns:
            Dictionary mapping IDs to names or None if no data loaded
        """
        if self._cached_id_to_name_map is None:
            print("WARNING: No ID-to-name mapping loaded")
            return None
        
        print(f"DEBUG: Returning {len(self._cached_id_to_name_map)} cached ID mappings")
        return self._cached_id_to_name_map
    
    def get_character_by_id(self, character_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific character by ID
        
        Args:
            character_id: ID of the character to retrieve
            
        Returns:
            Character data or None if not found
        """
        if self._cached_characters is None:
            print("WARNING: No character data loaded")
            return None
        
        return self._cached_characters.get(character_id)
    
    def search_characters(self, query: str, field: str = "name") -> List[Dict[str, Any]]:
        """
        Search characters by field value
        
        Args:
            query: Search query string
            field: Field to search in (name, birthday, etc.)
            
        Returns:
            List of matching characters
        """
        if self._cached_characters is None:
            return []
        
        results = []
        query_lower = query.lower()
        
        for char_id, char_data in self._cached_characters.items():
            field_value = char_data.get(field, "")
            if query_lower in str(field_value).lower():
                results.append({
                    "id": char_id,
                    **char_data
                })
        
        print(f"DEBUG: Found {len(results)} characters matching '{query}' in field '{field}'")
        return results
    
    def is_data_loaded(self) -> bool:
        """Check if any data is currently loaded"""
        return self._cached_characters is not None
    
    def get_data_info(self) -> Dict[str, Any]:
        """
        Get information about currently loaded data
        
        Returns:
            Dictionary with data source info
        """
        return {
            "data_loaded": self.is_data_loaded(),
            "character_count": len(self._cached_characters) if self._cached_characters else 0,
            "data_source": self._current_data_source,
            "last_loaded": self._last_loaded.isoformat() if self._last_loaded else None,
            "prefer_offline": self._prefer_offline,
            "auto_sync": self._auto_sync
        }
    
    def clear_cache(self):
        """Clear all cached data"""
        print("DEBUG: Clearing data cache")
        self._cached_characters = None
        self._cached_id_to_name_map = None
        self._current_data_source = None
        self._last_loaded = None
    
    def _save_to_offline_db(self):
        """
        Save current data to offline SQLite database
        (Internal method - will be implemented in Phase 2)
        """
        print("DEBUG: Offline database saving not yet implemented")
        # TODO: Implement SQLite saving
        pass
    
    def _sync_to_online_db(self):
        """
        Sync current data to online database
        (Internal method - will be implemented in Phase 3)
        """
        print("DEBUG: Online database syncing not yet implemented")
        # TODO: Implement online syncing
        pass


# Global service instance
_family_data_service = None


def get_family_data_service() -> FamilyDataService:
    """
    Get the global family data service instance
    
    Returns:
        FamilyDataService singleton instance
    """
    global _family_data_service
    if _family_data_service is None:
        _family_data_service = FamilyDataService()
    return _family_data_service


def reset_family_data_service():
    """Reset the global service instance (useful for testing)"""
    global _family_data_service
    _family_data_service = None