"""
Data persistence module for BLD Remote MCP.

This module provides in-memory data persistence across execute_command() calls,
enabling stateful operations and delayed result retrieval.

Based on the global variable pattern from context/hints/howto-persist-data-in-blender.md
"""

from .utils import log_info, log_warning, log_error


class PersistData:
    """In-memory data persistence for BLD Remote MCP.
    
    This class provides a simple interface for storing and retrieving data
    across different command executions within the same Blender session.
    """
    
    def __init__(self):
        """Initialize the persistence storage."""
        self._storage = {}
        log_info("PersistData instance created")
    
    def get_data(self, key, default=None):
        """Safely retrieve a value from the session storage.
        
        Args:
            key (str): The key to retrieve
            default: Default value if key not found
            
        Returns:
            The stored value or default if not found
        """
        log_info(f"PersistData.get_data() called with key='{key}', default='{default}'")
        result = self._storage.get(key, default)
        log_info(f"PersistData.get_data() returning: {type(result)} (length: {len(str(result))})")
        return result
    
    def put_data(self, key, data):
        """Store a value in the session storage.
        
        Args:
            key (str): The key to store under
            data: The data to store (can be any Python object)
        """
        log_info(f"PersistData.put_data() called with key='{key}', data type: {type(data)}")
        self._storage[key] = data
        log_info(f"PersistData.put_data() stored successfully. Storage now has {len(self._storage)} items")
    
    def remove_data(self, key):
        """Remove data by key.
        
        Args:
            key (str): The key to remove
            
        Returns:
            bool: True if the key was found and removed, False otherwise
        """
        log_info(f"PersistData.remove_data() called with key='{key}'")
        if key in self._storage:
            del self._storage[key]
            log_info(f"PersistData.remove_data() removed key '{key}'. Storage now has {len(self._storage)} items")
            return True
        else:
            log_info(f"PersistData.remove_data() key '{key}' not found")
            return False
    
    def clear_data(self):
        """Clear all session storage."""
        log_info("PersistData.clear_data() called")
        old_count = len(self._storage)
        self._storage.clear()
        log_info(f"PersistData.clear_data() cleared {old_count} items from storage")
    
    def get_keys(self):
        """Get all keys in storage.
        
        Returns:
            list: List of all keys in storage
        """
        keys = list(self._storage.keys())
        log_info(f"PersistData.get_keys() returning {len(keys)} keys")
        return keys
    
    def get_storage_info(self):
        """Get information about current storage state.
        
        Returns:
            dict: Dictionary with storage statistics
        """
        info = {
            'key_count': len(self._storage),
            'keys': list(self._storage.keys()),
            'total_size_estimate': sum(len(str(v)) for v in self._storage.values())
        }
        log_info(f"PersistData.get_storage_info() returning: {info}")
        return info


# Global instance - persists for the entire Blender session
# This follows the Method 1 pattern from the reference guide
_persist_instance = None


def get_persist_instance():
    """Get the global persistence instance, creating it if necessary."""
    global _persist_instance
    if _persist_instance is None:
        log_info("Creating new PersistData instance")
        _persist_instance = PersistData()
    return _persist_instance


# Module-level convenience functions that delegate to the global instance
def get_data(key, default=None):
    """Get data by key from global persistence storage."""
    return get_persist_instance().get_data(key, default)


def put_data(key, data):
    """Put data by key into global persistence storage."""
    return get_persist_instance().put_data(key, data)


def remove_data(key):
    """Remove data by key from global persistence storage."""
    return get_persist_instance().remove_data(key)


def clear_data():
    """Clear all data from global persistence storage."""
    return get_persist_instance().clear_data()


def get_keys():
    """Get all keys from global persistence storage."""
    return get_persist_instance().get_keys()


def get_storage_info():
    """Get storage information from global persistence storage."""
    return get_persist_instance().get_storage_info()