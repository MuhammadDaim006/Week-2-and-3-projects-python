"""
config_manager.py
------------------
OOP settings manager: reads/writes a JSON config file and validates
values against the schema defined in schema.py.
"""

import json
import os
import shutil
from schema import SETTINGS_SCHEMA


class ValidationError(Exception):
    """Raised when a setting value fails schema validation."""
    pass


class ConfigManager:
    def __init__(self, config_path="config.json", schema=None):
        self.config_path = config_path
        self.schema = schema if schema is not None else SETTINGS_SCHEMA
        self.data = {}
        self.load()

    # ------------------------------------------------------------------
    # Loading / Saving
    # ------------------------------------------------------------------
    def load(self):
        """Load config from disk. If missing/corrupt, fall back to defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.data = {}
        else:
            self.data = {}

        # Fill in any missing keys with defaults, and drop unknown keys
        # that don't belong to the schema (keeps config file clean).
        clean_data = {}
        for key, rules in self.schema.items():
            if key in self.data:
                clean_data[key] = self.data[key]
            else:
                clean_data[key] = rules["default"]
        self.data = clean_data

    def save(self):
        """Validate everything, back up the old file, then write to disk."""
        self.validate_all()

        if os.path.exists(self.config_path):
            backup_path = self.config_path + ".bak"
            shutil.copyfile(self.config_path, backup_path)

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    # ------------------------------------------------------------------
    # Get / Set
    # ------------------------------------------------------------------
    def get(self, key):
        if key not in self.schema:
            raise KeyError(f"Unknown setting: {key}")
        return self.data.get(key, self.schema[key]["default"])

    def set(self, key, value):
        """Set a value after validating it against the schema."""
        if key not in self.schema:
            raise KeyError(f"Unknown setting: {key}")
        self.validate_value(key, value)
        self.data[key] = value

    def reset_to_defaults(self):
        self.data = {key: rules["default"] for key, rules in self.schema.items()}

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate_value(self, key, value):
        rules = self.schema[key]
        field_type = rules["type"]

        if rules.get("required") and (value is None or value == ""):
            raise ValidationError(f"'{rules['label']}' is required.")

        if field_type == "str":
            if not isinstance(value, str):
                raise ValidationError(f"'{rules['label']}' must be text.")

        elif field_type == "int":
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValidationError(f"'{rules['label']}' must be an integer.")
            self._check_range(rules, value)

        elif field_type == "float":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValidationError(f"'{rules['label']}' must be a number.")
            self._check_range(rules, value)

        elif field_type == "bool":
            if not isinstance(value, bool):
                raise ValidationError(f"'{rules['label']}' must be true/false.")

        elif field_type == "choice":
            if value not in rules["choices"]:
                allowed = ", ".join(str(c) for c in rules["choices"])
                raise ValidationError(
                    f"'{rules['label']}' must be one of: {allowed}."
                )
        else:
            raise ValidationError(f"Unknown field type for '{key}': {field_type}")

    def _check_range(self, rules, value):
        if "min" in rules and value < rules["min"]:
            raise ValidationError(
                f"'{rules['label']}' must be >= {rules['min']}."
            )
        if "max" in rules and value > rules["max"]:
            raise ValidationError(
                f"'{rules['label']}' must be <= {rules['max']}."
            )

    def validate_all(self):
        for key, value in self.data.items():
            if key in self.schema:
                self.validate_value(key, value)
