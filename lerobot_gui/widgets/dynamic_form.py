"""
Dynamic form widget — renders a DeviceSchema as an interactive Qt form.

Supports all FieldTypes, group collapsing, field dependencies,
and emits value changes for real-time validation.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from lerobot_gui.schemas.schema_types import DeviceSchema, FieldSchema, FieldType

logger = logging.getLogger(__name__)


class DynamicFormWidget(QWidget):
    """
    Renders a DeviceSchema as a scrollable form with grouped sections.

    Signals:
        values_changed: Emitted whenever any field value changes.
    """

    values_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._schema: DeviceSchema | None = None
        self._widgets: dict[str, QWidget] = {}
        self._group_boxes: dict[str, QGroupBox] = {}
        self._dep_fields: list[FieldSchema] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._content)
        layout.addWidget(self._scroll)

    def set_schema(self, schema: DeviceSchema | None) -> None:
        """Render a new schema, replacing the current form."""
        self._schema = schema
        self._widgets.clear()
        self._group_boxes.clear()
        self._dep_fields.clear()

        # Clear existing widgets
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if schema is None:
            return

        # Device description header
        if schema.description:
            desc = QLabel(schema.description)
            desc.setStyleSheet("color: #999; font-style: italic; padding: 4px;")
            desc.setWordWrap(True)
            self._content_layout.addWidget(desc)

        # Create groups
        rendered_groups: set[str] = set()
        for group in schema.groups:
            fields = schema.get_fields_by_group(group.name)
            if not fields:
                continue
            gb = QGroupBox(group.label)
            gb.setCheckable(group.collapsed)
            if group.collapsed:
                gb.setChecked(False)
            form = QFormLayout()
            form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
            for f in fields:
                widget = self._create_field_widget(f)
                if widget is None:
                    continue
                self._widgets[f.key] = widget
                label_text = f.label + (" *" if f.required else "")
                label = QLabel(label_text)
                if f.help:
                    label.setToolTip(f.help)
                    widget.setToolTip(f.help)
                form.addRow(label, widget)
                if f.depends_on:
                    self._dep_fields.append(f)
            gb.setLayout(form)
            self._content_layout.addWidget(gb)
            self._group_boxes[group.name] = gb
            rendered_groups.add(group.name)

        self._content_layout.addStretch()
        self._update_dependencies()

    def _create_field_widget(self, field: FieldSchema) -> QWidget | None:
        """Create the appropriate Qt widget for a field type."""
        ft = field.type

        # String-like fields (with optional combo for choices)
        if ft in (FieldType.STRING, FieldType.SERIAL_PORT, FieldType.IP_ADDRESS,
                  FieldType.DEVICE_ID):
            if field.choices:
                w = QComboBox()
                w.setEditable(True)
                for c in field.choices:
                    w.addItem(c)
                if field.default is not None:
                    w.setCurrentText(str(field.default))
                w.currentTextChanged.connect(lambda _: self._on_change())
                return w
            w = QLineEdit()
            if field.default is not None:
                w.setText(str(field.default))
            if field.placeholder:
                w.setPlaceholderText(field.placeholder)
            if field.readonly:
                w.setReadOnly(True)
            w.textChanged.connect(lambda _: self._on_change())
            return w

        if ft == FieldType.CAN_INTERFACE:
            w = QComboBox()
            w.setEditable(True)
            for c in (field.choices or ["can_slave1", "can_master1"]):
                w.addItem(c)
            if field.default:
                w.setCurrentText(str(field.default))
            w.currentTextChanged.connect(lambda _: self._on_change())
            return w

        if ft == FieldType.INT:
            w = QSpinBox()
            w.setRange(int(field.min_val if field.min_val is not None else -999999),
                       int(field.max_val if field.max_val is not None else 999999))
            if field.step:
                w.setSingleStep(int(field.step))
            if field.default is not None:
                w.setValue(int(field.default))
            w.valueChanged.connect(lambda _: self._on_change())
            return w

        if ft == FieldType.FLOAT:
            w = QDoubleSpinBox()
            w.setDecimals(4)
            w.setRange(field.min_val if field.min_val is not None else -999999.0,
                       field.max_val if field.max_val is not None else 999999.0)
            if field.step:
                w.setSingleStep(field.step)
            if field.default is not None:
                w.setValue(float(field.default))
            w.valueChanged.connect(lambda _: self._on_change())
            return w

        if ft == FieldType.BOOL:
            w = QCheckBox()
            if field.default is not None:
                w.setChecked(bool(field.default))
            w.stateChanged.connect(lambda _: self._on_change())
            return w

        if ft == FieldType.ENUM:
            w = QComboBox()
            for c in (field.choices or []):
                w.addItem(str(c))
            if field.default is not None:
                idx = w.findText(str(field.default))
                if idx >= 0:
                    w.setCurrentIndex(idx)
            w.currentTextChanged.connect(lambda _: self._on_change())
            return w

        if ft == FieldType.PATH:
            container = QWidget()
            hl = QHBoxLayout(container)
            hl.setContentsMargins(0, 0, 0, 0)
            le = QLineEdit()
            if field.default:
                le.setText(str(field.default))
            btn = QToolButton()
            btn.setText("...")
            btn.clicked.connect(lambda: self._browse_path(le))
            hl.addWidget(le, 1)
            hl.addWidget(btn)
            le.textChanged.connect(lambda _: self._on_change())
            container._value_widget = le  # type: ignore[attr-defined]
            return container

        if ft in (FieldType.LIST_FLOAT, FieldType.LIST_INT, FieldType.LIST_STR):
            w = QPlainTextEdit()
            w.setMaximumHeight(80)
            if field.default is not None:
                w.setPlainText(json.dumps(field.default))
            else:
                w.setPlaceholderText("JSON array, e.g. [1.0, 2.0, 3.0]")
            w.textChanged.connect(self._on_change)
            return w

        if ft in (FieldType.DICT, FieldType.MOTOR_MAP, FieldType.MOTOR_MAP_NORM,
                  FieldType.MOTOR_CONFIG_DAMIAO, FieldType.JOINT_LIMITS,
                  FieldType.TELEOP_KEYS):
            w = QPlainTextEdit()
            w.setMaximumHeight(100)
            if field.default is not None:
                w.setPlainText(json.dumps(field.default, indent=2, default=str))
            else:
                w.setPlaceholderText("JSON object")
            w.textChanged.connect(self._on_change)
            return w

        if ft == FieldType.CAMERA_DICT:
            w = QPlainTextEdit()
            w.setMaximumHeight(120)
            w.setPlaceholderText(
                'JSON camera dict, e.g.:\n'
                '{"laptop": {"type": "intelrealsense",\n'
                '  "serial_number_or_name": "152222072122",\n'
                '  "width": 640, "height": 480, "fps": 30}}'
            )
            if field.default:
                w.setPlainText(json.dumps(field.default, indent=2, default=str))
            w.textChanged.connect(self._on_change)
            return w

        if ft == FieldType.NESTED_CONFIG:
            lbl = QLabel(f"[Nested config: {field.nested_schema_ref or 'see sub-fields above'}]")
            lbl.setStyleSheet("color: #888;")
            return lbl

        # Fallback: plain text
        w = QLineEdit()
        if field.default is not None:
            w.setText(str(field.default))
        w.textChanged.connect(lambda _: self._on_change())
        return w

    def _browse_path(self, line_edit: QLineEdit):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            line_edit.setText(path)

    def _on_change(self):
        self._update_dependencies()
        self.values_changed.emit(self.get_values())

    def _update_dependencies(self):
        current = self.get_values()
        for f in self._dep_fields:
            w = self._widgets.get(f.key)
            if w is None:
                continue
            parent_val = current.get(f.depends_on)
            visible = (
                (parent_val == f.depends_value)
                if f.depends_value is not None
                else (parent_val is not None)
            )
            w.setVisible(visible)

    def get_values(self) -> dict[str, Any]:
        """Extract current form values as a flat dict."""
        result: dict[str, Any] = {}
        if self._schema is None:
            return result
        for f in self._schema.fields:
            w = self._widgets.get(f.key)
            if w is None:
                continue
            result[f.key] = self._extract_value(f, w)
        return result

    def _extract_value(self, field: FieldSchema, widget: QWidget) -> Any:
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QSpinBox):
            return widget.value()
        if isinstance(widget, QDoubleSpinBox):
            return widget.value()
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if isinstance(widget, QLineEdit):
            text = widget.text()
            return text if text else field.default
        if isinstance(widget, QPlainTextEdit):
            text = widget.toPlainText().strip()
            if not text:
                return field.default
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        # Container (PATH)
        if hasattr(widget, "_value_widget"):
            vw = widget._value_widget  # type: ignore[attr-defined]
            if isinstance(vw, QLineEdit):
                return vw.text() or field.default
            if isinstance(vw, QPlainTextEdit):
                text = vw.toPlainText().strip()
                if not text:
                    return field.default
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        return None

    def set_values(self, values: dict[str, Any]) -> None:
        """Populate form from a dict (e.g. loaded profile)."""
        for key, val in values.items():
            w = self._widgets.get(key)
            if w is None:
                continue
            if isinstance(w, QCheckBox):
                w.setChecked(bool(val))
            elif isinstance(w, QSpinBox):
                w.setValue(int(val))
            elif isinstance(w, QDoubleSpinBox):
                w.setValue(float(val))
            elif isinstance(w, QComboBox):
                w.setCurrentText(str(val))
            elif isinstance(w, QLineEdit):
                w.setText(str(val))
            elif isinstance(w, QPlainTextEdit):
                if isinstance(val, (dict, list)):
                    w.setPlainText(json.dumps(val, indent=2, default=str))
                else:
                    w.setPlainText(str(val))
            elif hasattr(w, "_value_widget"):
                vw = w._value_widget  # type: ignore[attr-defined]
                if isinstance(vw, QLineEdit):
                    vw.setText(str(val))
