"""
schema.py
---------
Defines the structure/validation rules for every setting in the app.
This is the single source of truth the ConfigManager uses for validation
and the GUI uses to auto-generate the right widget for each field.

Supported "type" values: "str", "int", "float", "bool", "choice"

Field options:
    type      : one of the types above (required)
    label     : human-readable label shown in the GUI (required)
    default   : default value used when key is missing (required)
    required  : if True, value cannot be empty/None (default False)
    min       : minimum value (int/float only)
    max       : maximum value (int/float only)
    choices   : list of allowed values (choice type only)
    help      : short tooltip text (optional)
"""

SETTINGS_SCHEMA = {
    "app_name": {
        "type": "str",
        "label": "Application Name",
        "default": "My App",
        "required": True,
        "help": "Name shown in the title bar.",
    },
    "username": {
        "type": "str",
        "label": "Username",
        "default": "",
        "required": True,
        "help": "Your display name.",
    },
    "volume": {
        "type": "int",
        "label": "Volume",
        "default": 50,
        "min": 0,
        "max": 100,
        "help": "System volume percentage.",
    },
    "opacity": {
        "type": "float",
        "label": "Window Opacity",
        "default": 1.0,
        "min": 0.1,
        "max": 1.0,
        "help": "Window transparency (0.1 - 1.0).",
    },
    "theme": {
        "type": "choice",
        "label": "Theme",
        "default": "Light",
        "choices": ["Light", "Dark", "System"],
        "help": "Application color theme.",
    },
    "autosave": {
        "type": "bool",
        "label": "Enable Autosave",
        "default": True,
        "help": "Automatically save changes.",
    },
    "max_recent_files": {
        "type": "int",
        "label": "Max Recent Files",
        "default": 10,
        "min": 0,
        "max": 50,
        "help": "Number of recent files to remember.",
    },
}
