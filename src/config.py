import ctypes
import json
from pathlib import Path
import sys

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class Config(metaclass=SingletonMeta):
    def __init__(self):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except AttributeError:
            ctypes.windll.user32.SetProcessDPIAware()
            
        # Base resolution
        self.BASE_SCREEN_WIDTH = 2560
        self.BASE_SCREEN_HEIGHT = 1440

        # Get current screen resolution
        try:
            user32 = ctypes.windll.user32
            self.screen_width = user32.GetSystemMetrics(0)
            self.screen_height = user32.GetSystemMetrics(1)
        except Exception:
            self.screen_width = self.BASE_SCREEN_WIDTH
            self.screen_height = self.BASE_SCREEN_HEIGHT

        # Calculate scaling factors
        self.scale_x = self.screen_width / self.BASE_SCREEN_WIDTH
        self.scale_y = self.screen_height / self.BASE_SCREEN_HEIGHT
        self.scale = self.screen_height / self.BASE_SCREEN_HEIGHT

        # Configuration storage
        self.current_preset_name = "路亚轻杆"
        self.presets = {}
        self.global_settings = {}
        self.qfluent_settings = {}

        # Predefined regions based on 2560x1440
        self.REGIONS = {
            "cast_rod":     {"coords": (1092, 1323, 25, 32), "anchor": "bottom_center"},
            "cast_rod_ice": {"coords": (1203, 1323, 25, 32), "anchor": "bottom_center"},
            "wait_bite":    {"coords": (980, 1323, 25, 32), "anchor": "bottom_center"},
            "shangyu":      {"coords": (1146, 1316, 17, 21), "anchor": "bottom_center"},
            "reel_in_star": {"coords": (1172, 165, 34, 34), "anchor": "top_center"},
            "bait_count":   {"coords": (2318, 1296, 30, 22), "anchor": "bottom_right"},
            "jiashi_popup": {"coords": (1244, 676, 27, 28), "anchor": "center"},
            "ocr_area":     {"coords": (915, 75, 725, 150), "anchor": "top_center"},
        }
        
        # Constants
        self.BAIT_CROP_WIDTH1_BASE = 15
        self.BTN_JIASHI_NO = (1175, 778)  # Relative to 2560x1440
        self.BTN_JIASHI_YES = (1390, 778) # Relative to 2560x1440
        
        # This will be set by main.py at startup
        self._base_path = None
        
        self._load_config_from_json()

    def set_base_path(self, path):
        """Sets the base path for the application. Should be called once at startup."""
        self._base_path = path

    def _get_base_path(self):
        """Gets the base path for the application. It's set by main.py."""
        if self._base_path is None:
            # Fallback for cases where set_base_path was not called (e.g., testing)
            if getattr(sys, 'frozen', False):
                return Path(sys.executable).parent
            else:
                return Path(__file__).parent.parent
        return self._base_path

    def get_top_center_rect(self, coords):
        """
        Calculates coordinates for a top-center anchored region.
        Scales based on height (self.scale) to maintain aspect ratio.
        """
        base_x, base_y, base_w, base_h = coords
        
        # Calculate center offset from base resolution center
        base_center_x = base_x + (base_w / 2)
        offset_from_center_x = base_center_x - (self.BASE_SCREEN_WIDTH / 2)
        
        # Calculate new dimensions
        new_w = int(base_w * self.scale)
        new_h = int(base_h * self.scale)
        
        # Calculate new center position
        new_center_x = (self.screen_width / 2) + (offset_from_center_x * self.scale)
        
        # Calculate new top-left position
        new_x = int(new_center_x - (new_w / 2))
        new_y = int(base_y * self.scale)
        
        return (new_x, new_y, new_w, new_h)

    def get_bottom_center_rect(self, coords):
        """
        Calculates coordinates for a bottom-center anchored region.
        """
        base_x, base_y, base_w, base_h = coords
        
        # Calculate center offset from base resolution center
        base_center_x = base_x + (base_w / 2)
        offset_from_center_x = base_center_x - (self.BASE_SCREEN_WIDTH / 2)
        
        # Calculate offset from bottom
        offset_from_bottom = self.BASE_SCREEN_HEIGHT - base_y
        
        # Calculate new dimensions
        new_w = int(base_w * self.scale)
        new_h = int(base_h * self.scale)
        
        # Calculate new center position X
        new_center_x = (self.screen_width / 2) + (offset_from_center_x * self.scale)
        
        # Calculate new Y (from bottom)
        new_y = int(self.screen_height - (offset_from_bottom * self.scale))
        
        # Calculate new top-left X
        new_x = int(new_center_x - (new_w / 2))
        
        return (new_x, new_y, new_w, new_h)

    def get_bottom_right_rect(self, coords):
        """
        Calculates coordinates for a bottom-right anchored region.
        """
        base_x, base_y, base_w, base_h = coords
        
        # Calculate offsets from bottom-right corner
        offset_from_right = self.BASE_SCREEN_WIDTH - base_x
        offset_from_bottom = self.BASE_SCREEN_HEIGHT - base_y
        
        # Calculate new dimensions
        new_w = int(base_w * self.scale)
        new_h = int(base_h * self.scale)
        
        # Calculate new top-left position
        new_x = int(self.screen_width - (offset_from_right * self.scale))
        new_y = int(self.screen_height - (offset_from_bottom * self.scale))
        
        return (new_x, new_y, new_w, new_h)

    def get_center_anchored_rect(self, coords):
        """
        Calculates coordinates for a center-center anchored region.
        """
        base_x, base_y, base_w, base_h = coords
        
        base_center_x = base_x + (base_w / 2)
        base_center_y = base_y + (base_h / 2)
        
        offset_from_center_x = base_center_x - (self.BASE_SCREEN_WIDTH / 2)
        offset_from_center_y = base_center_y - (self.BASE_SCREEN_HEIGHT / 2)
        
        new_w = int(base_w * self.scale)
        new_h = int(base_h * self.scale)
        
        new_center_x = (self.screen_width / 2) + (offset_from_center_x * self.scale)
        new_center_y = (self.screen_height / 2) + (offset_from_center_y * self.scale)
        
        new_x = int(new_center_x - (new_w / 2))
        new_y = int(new_center_y - (new_h / 2))
        
        return (new_x, new_y, new_w, new_h)
    
    def get_center_anchored_pos(self, coords):
        """
        Calculates coordinates for a center-center anchored point (x, y).
        """
        base_x, base_y = coords
        
        offset_from_center_x = base_x - (self.BASE_SCREEN_WIDTH / 2)
        offset_from_center_y = base_y - (self.BASE_SCREEN_HEIGHT / 2)
        
        new_x = int((self.screen_width / 2) + (offset_from_center_x * self.scale_x))
        new_y = int((self.screen_height / 2) + (offset_from_center_y * self.scale_y))
        
        return (new_x, new_y)

    def __getattr__(self, name):
        """
        Dynamically get attributes from the current preset or global settings.
        This ensures backward compatibility with code that uses cfg.attribute.
        """
        # First, try to get from the current preset's settings
        current_preset = self.get_current_preset()
        if current_preset and name in current_preset:
            return current_preset[name]
        
        # If not in preset, try to get from global settings
        if name in self.global_settings:
            return self.global_settings[name]

        # If still not found, raise an AttributeError
        raise AttributeError(f"'Config' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        """
        Allows setting attributes. 
        If the attribute exists in the current preset, update it there.
        If it exists in global_settings, update it there.
        Otherwise, set it as a normal instance attribute.
        """
        # Avoid recursion for instance attributes defined in __init__
        if name in ['BASE_SCREEN_WIDTH', 'BASE_SCREEN_HEIGHT', 'screen_width', 'screen_height', 
                    'scale_x', 'scale_y', 'scale', 'current_preset_name', 'presets', 
                    'global_settings', 'qfluent_settings', 'REGIONS', '_instances']:
            super().__setattr__(name, value)
            return

        # Check if it's a preset setting
        current_preset = self.get_current_preset()
        if current_preset and name in current_preset:
            current_preset[name] = value
            return

        # Check if it's a global setting
        if hasattr(self, 'global_settings') and name in self.global_settings:
            self.global_settings[name] = value
            return
        
        # Default behavior for other attributes
        super().__setattr__(name, value)

    def _get_default_presets(self):
        """Returns a dictionary of default presets."""
        return {
            "路亚轻杆": {"cast_time": 2.0, "reel_in_time": 2.0, "release_time": 1.0, "max_pulls": 20, "cycle_interval": 0.5},
            "路亚重杆": {"cast_time": 3.0, "reel_in_time": 2.5, "release_time": 1.5, "max_pulls": 15, "cycle_interval": 0.5},
            "冰钓轻杆": {"cast_time": 1.5, "reel_in_time": 1.8, "release_time": 0.8, "max_pulls": 25, "cycle_interval": 0.5},
            "冰钓重杆": {"cast_time": 2.5, "reel_in_time": 2.2, "release_time": 1.2, "max_pulls": 18, "cycle_interval": 0.5}
        }

    def _load_config_from_json(self):
        base_path = self._get_base_path()
        config_path = base_path / "config" / "config.json"
        if not config_path.exists():
            # If config file doesn't exist, create it with default values
            self.presets = self._get_default_presets()
            self.global_settings = {"hotkey": "F2", "debug_hotkey": "F10", "enable_jiashi": True, "jitter_range": 0, "theme": "Light"}
            self.qfluent_settings = {"ThemeMode": "Light"}
            self.save()
            return

        with open(config_path, 'r', encoding='utf-8') as f:
            try:
                config_data = json.load(f)
            except json.JSONDecodeError:
                # Handle corrupted JSON file
                self.presets = self._get_default_presets()
                self.global_settings = {"hotkey": "F2", "debug_hotkey": "F10", "enable_jiashi": True, "jitter_range": 0, "theme": "Light"}
                self.qfluent_settings = {"ThemeMode": "Light"}
                self.save()
                return

        self.current_preset_name = config_data.get("current_preset", "路亚轻杆")
        self.presets = config_data.get("presets", self._get_default_presets())
        
        # Load global settings with defaults for missing keys
        default_global_settings = {"hotkey": "F2", "debug_hotkey": "F10", "enable_jiashi": True, "jitter_range": 0, "theme": "Light"}
        loaded_global_settings = config_data.get("global_settings", {})
        default_global_settings.update(loaded_global_settings)
        self.global_settings = default_global_settings
        
        self.qfluent_settings = config_data.get("QFluentWidgets", {"ThemeMode": "Light"})
    
    def save(self):
        """
        Saves the entire configuration structure to config/config.json.
        """
        base_path = self._get_base_path()
        config_path = base_path / "config" / "config.json"
        
        try:
             with open(config_path, 'r', encoding='utf-8') as f:
                 existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
             existing_data = {}
             
        config_data = {
            "current_preset": self.current_preset_name,
            "presets": self.presets,
            "global_settings": self.global_settings,
            "QFluentWidgets": self.qfluent_settings
        }
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)

    def get_current_preset(self):
        """Returns the dictionary for the currently active preset."""
        return self.presets.get(self.current_preset_name)
    
    def load_preset(self, name):
        """Switches the current preset by name."""
        if name in self.presets:
            self.current_preset_name = name
        else:
            raise ValueError(f"Preset '{name}' not found.")

    def get_rect(self, name):
        """
        Calculates the scaled rectangle for a predefined region using an anchor-based dispatcher.
        """
        if name not in self.REGIONS:
            raise KeyError(f"Region '{name}' not defined in Config.")

        region_info = self.REGIONS[name]
        coords = region_info["coords"]
        anchor_type = region_info.get("anchor", "default") # Default to simple scaling

        # Dispatcher to select the correct anchor calculation method
        dispatcher = {
            "top_center": self.get_top_center_rect,
            "bottom_center": self.get_bottom_center_rect,
            "bottom_right": self.get_bottom_right_rect,
            "center": self.get_center_anchored_rect,
        }

        calculation_method = dispatcher.get(anchor_type)

        if calculation_method:
            return calculation_method(coords)
        else: # "default" or any other undefined anchor
            x, y, w, h = coords
            scaled_x = int(x * self.scale_x)
            scaled_y = int(y * self.scale_y)
            scaled_w = int(w * self.scale_x)
            scaled_h = int(h * self.scale_y)
            return (scaled_x, scaled_y, scaled_w, scaled_h)

# Instantiate the singleton
cfg = Config()
