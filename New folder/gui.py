"""
gui.py
------
PyQt5 GUI that dynamically builds a settings form from SETTINGS_SCHEMA,
validates input live, and saves through ConfigManager.
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QFormLayout, QVBoxLayout, QHBoxLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox,
    QPushButton, QLabel, QMessageBox
)

from config_manager import ConfigManager, ValidationError


class SettingsWindow(QWidget):
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager
        self.fields = {}  # key -> widget

        self.setWindowTitle(self.config.get("app_name") + " - Settings")
        self.resize(420, 400)

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setLabelAlignment(0x0001)  # Qt.AlignLeft

        for key, rules in self.config.schema.items():
            widget = self._make_widget(key, rules)
            self.fields[key] = widget

            label_text = rules["label"]
            if rules.get("required"):
                label_text += " *"
            label = QLabel(label_text)
            if rules.get("help"):
                label.setToolTip(rules["help"])
                widget.setToolTip(rules["help"])

            form.addRow(label, widget)

        main_layout.addLayout(form)

        # Status / error message
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red;")
        main_layout.addWidget(self.status_label)

        # Buttons
        button_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        reset_btn = QPushButton("Reset to Defaults")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.on_save)
        reset_btn.clicked.connect(self.on_reset)
        cancel_btn.clicked.connect(self.close)

        button_row.addWidget(reset_btn)
        button_row.addStretch()
        button_row.addWidget(cancel_btn)
        button_row.addWidget(save_btn)

        main_layout.addLayout(button_row)

    def _make_widget(self, key, rules):
        """Create the right widget type based on the schema field type."""
        value = self.config.get(key)
        field_type = rules["type"]

        if field_type == "str":
            w = QLineEdit(str(value))
            return w

        if field_type == "int":
            w = QSpinBox()
            w.setMinimum(rules.get("min", -1_000_000))
            w.setMaximum(rules.get("max", 1_000_000))
            w.setValue(value)
            return w

        if field_type == "float":
            w = QDoubleSpinBox()
            w.setDecimals(2)
            w.setSingleStep(0.05)
            w.setMinimum(rules.get("min", -1_000_000.0))
            w.setMaximum(rules.get("max", 1_000_000.0))
            w.setValue(value)
            return w

        if field_type == "bool":
            w = QCheckBox()
            w.setChecked(bool(value))
            return w

        if field_type == "choice":
            w = QComboBox()
            w.addItems(rules["choices"])
            if value in rules["choices"]:
                w.setCurrentText(value)
            return w

        raise ValueError(f"Unsupported field type: {field_type}")

    # ------------------------------------------------------------------
    # Reading widget values
    # ------------------------------------------------------------------
    def _read_widget(self, key, rules):
        widget = self.fields[key]
        field_type = rules["type"]

        if field_type == "str":
            return widget.text()
        if field_type == "int":
            return widget.value()
        if field_type == "float":
            return float(widget.value())
        if field_type == "bool":
            return widget.isChecked()
        if field_type == "choice":
            return widget.currentText()

        raise ValueError(f"Unsupported field type: {field_type}")

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------
    def on_save(self):
        self.status_label.setText("")
        new_values = {}

        # Validate every field first, collecting the first error found.
        for key, rules in self.config.schema.items():
            value = self._read_widget(key, rules)
            try:
                self.config.validate_value(key, value)
            except ValidationError as e:
                self.status_label.setText(str(e))
                return
            new_values[key] = value

        # All valid -> apply and persist
        for key, value in new_values.items():
            self.config.set(key, value)

        try:
            self.config.save()
        except ValidationError as e:
            self.status_label.setText(str(e))
            return

        QMessageBox.information(self, "Saved", "Settings saved successfully.")

    def on_reset(self):
        confirm = QMessageBox.question(
            self, "Reset Settings",
            "Reset all settings to their default values?",
        )
        if confirm == QMessageBox.Yes:
            self.config.reset_to_defaults()
            for key, rules in self.config.schema.items():
                self._set_widget(key, rules, self.config.get(key))
            self.status_label.setText("")

    def _set_widget(self, key, rules, value):
        widget = self.fields[key]
        field_type = rules["type"]

        if field_type == "str":
            widget.setText(str(value))
        elif field_type == "int":
            widget.setValue(value)
        elif field_type == "float":
            widget.setValue(value)
        elif field_type == "bool":
            widget.setChecked(bool(value))
        elif field_type == "choice":
            widget.setCurrentText(value)


def run_app():
    app = QApplication(sys.argv)
    config = ConfigManager(config_path="config.json")
    window = SettingsWindow(config)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()
