"""
PipeRec - Configuration Management
Handles persistent settings and user preferences.
"""

import os
import json
from typing import Any, Optional
from pathlib import Path


class Config:
    """
    Manages application configuration with persistent storage.
    """
    
    DEFAULT_CONFIG = {
        # Audio settings
        'sample_rate': 44100,
        'block_size': 4096,
        'silent_gate_threshold': -50.0,  # dB
        'normalize_lufs': -16,
        'mp3_bitrate': 192,
        
        # Directories
        'recordings_dir': 'recordings',
        'temp_dir': 'temp',
        
        # Last used devices (names for matching)
        'last_mic_name': None,
        'last_monitor_name': None,
        
        # Hotkeys
        'hotkey_record': '<ctrl>+<shift>+r',
        'hotkey_marker': '<ctrl>+<shift>+m',
        
        # UI
        'window_geometry': None,
        'show_on_startup': True,
        'minimize_to_tray': False,
    }
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory to store config file. Defaults to ~/.config/piperec
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.home() / '.config' / 'piperec'
        
        self.config_file = self.config_dir / 'config.json'
        self.config = self.DEFAULT_CONFIG.copy()
        
        self._ensure_dirs()
        self.load()
    
    def _ensure_dirs(self):
        """Ensure config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.config_file.exists():
            return False
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Merge with defaults (in case new options were added)
                self.config = {**self.DEFAULT_CONFIG, **loaded}
            return True
        except Exception as e:
            print(f"Error loading config: {e}")
            return False
    
    def save(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any, save: bool = True):
        """Set a configuration value."""
        self.config[key] = value
        if save:
            self.save()
    
    def reset(self):
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


if __name__ == "__main__":
    # Test config
    config = get_config()
    print(f"Config file: {config.config_file}")
    print(f"Sample rate: {config.get('sample_rate')}")
    print(f"Hotkey record: {config.get('hotkey_record')}")
    
    # Test save
    config.set('last_mic_name', 'Test Microphone')
    print(f"Saved config: {config.config}")
