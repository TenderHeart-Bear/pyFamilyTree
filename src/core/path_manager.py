"""
Centralized path management for the Family Tree application.
"""
import os
import datetime
import json
from typing import Optional, Dict, Any

class PathManager:
    """Centralized path management for consistent file handling"""
    
    def __init__(self):
        self.base_dir = os.getcwd()
        self.assets_dir = os.path.join(self.base_dir, "assets")
        self.config_dir = os.path.join(self.base_dir, "config")
        self.output_base_dir = os.path.join(self.base_dir, "out")
        
        # Ensure base directories exist
        os.makedirs(self.assets_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.output_base_dir, exist_ok=True)
        
        # Current session info
        self.current_session_id: Optional[str] = None
        self.current_output_dir: Optional[str] = None
    
    def create_session(self, session_name: Optional[str] = None) -> str:
        """Create a new session with timestamped directory"""
        if not session_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            session_name = f"session_{timestamp}"
        
        self.current_session_id = session_name
        self.current_output_dir = os.path.join(self.output_base_dir, session_name)
        os.makedirs(self.current_output_dir, exist_ok=True)
        
        print(f"DEBUG: Created session '{session_name}' at {self.current_output_dir}")
        return self.current_output_dir
    
    def get_session_dir(self) -> str:
        """Get current session directory"""
        if not self.current_output_dir:
            return self.create_session()
        return self.current_output_dir
    
    def get_graph_file_path(self, graph_name: str = "family_tree", extension: str = "svg") -> str:
        """Get the full path for a graph file"""
        session_dir = self.get_session_dir()
        filename = f"{graph_name}.{extension}"
        return os.path.join(session_dir, filename)
    
    def get_graph_base_path(self, graph_name: str = "family_tree") -> str:
        """Get the base path for a graph file (without extension)"""
        session_dir = self.get_session_dir()
        return os.path.join(session_dir, graph_name)
    
    def get_settings_file_path(self) -> str:
        """Get the settings file path"""
        return os.path.join(self.config_dir, "settings.json")
    
    def get_xml_data_dir(self, excel_name: str, sheet_name: str) -> str:
        """Get XML data directory for a specific Excel file and sheet"""
        return os.path.join(self.assets_dir, excel_name, sheet_name)
    
    def cleanup_old_sessions(self, keep_count: int = 5):
        """Clean up old session directories, keeping only the most recent ones"""
        try:
            if not os.path.exists(self.output_base_dir):
                return
            
            # Get all session directories
            session_dirs = []
            for item in os.listdir(self.output_base_dir):
                item_path = os.path.join(self.output_base_dir, item)
                if os.path.isdir(item_path) and item.startswith("session_"):
                    session_dirs.append((item, item_path, os.path.getctime(item_path)))
            
            # Sort by creation time (newest first)
            session_dirs.sort(key=lambda x: x[2], reverse=True)
            
            # Remove old sessions
            for i, (name, path, _) in enumerate(session_dirs):
                if i >= keep_count:
                    print(f"DEBUG: Cleaning up old session: {name}")
                    import shutil
                    shutil.rmtree(path, ignore_errors=True)
                    
        except Exception as e:
            print(f"DEBUG: Error cleaning up old sessions: {e}")
    
    def list_sessions(self) -> list:
        """List all available sessions"""
        sessions = []
        if os.path.exists(self.output_base_dir):
            for item in os.listdir(self.output_base_dir):
                item_path = os.path.join(self.output_base_dir, item)
                if os.path.isdir(item_path):
                    sessions.append({
                        'name': item,
                        'path': item_path,
                        'created': datetime.datetime.fromtimestamp(os.path.getctime(item_path))
                    })
        return sorted(sessions, key=lambda x: x['created'], reverse=True)

    def save_last_dataset(self, dataset_info: Dict[str, Any]):
        """Save information about the last loaded dataset"""
        try:
            last_dataset_file = os.path.join(self.config_dir, "last_dataset.json")
            with open(last_dataset_file, 'w') as f:
                json.dump(dataset_info, f, indent=4)
            print(f"DEBUG: Saved last dataset info to {last_dataset_file}")
        except Exception as e:
            print(f"DEBUG ERROR: Error saving last dataset info: {str(e)}")
    
    def get_last_dataset(self) -> Optional[Dict[str, Any]]:
        """Get information about the last loaded dataset"""
        try:
            last_dataset_file = os.path.join(self.config_dir, "last_dataset.json")
            if os.path.exists(last_dataset_file):
                with open(last_dataset_file, 'r') as f:
                    dataset_info = json.load(f)
                print(f"DEBUG: Loaded last dataset info from {last_dataset_file}")
                return dataset_info
            return None
        except Exception as e:
            print(f"DEBUG ERROR: Error loading last dataset info: {str(e)}")
            return None

# Global instance
path_manager = PathManager() 