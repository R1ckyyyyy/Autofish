from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from qfluentwidgets import Theme, qconfig

# 定义品质颜色 (亮色主题, 暗色主题)
QUALITY_COLORS = {
    "标准": (QColor("#606060"), QColor("#D0D0D0")),      # Standard: Grey
    "非凡": (QColor("#1E9E00"), QColor("#2ECC71")),      # Uncommon: Green
    "稀有": (QColor("#007ACC"), QColor("#3498DB")),      # Rare: Blue
    "史诗": (QColor("#8A2BE2"), QColor("#9B59B6")),      # Epic: Purple
    "传说": (QColor("#FF8C00"), QColor("#F39C12"))       # Legendary: Orange
}


class KeyBindingWidget(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Click and press keys")
        self.setAlignment(Qt.AlignCenter)
        self.setReadOnly(True) # Prevent manual typing
        self.is_capturing = False
        self.original_text = ""

    def mousePressEvent(self, event):
        if not self.is_capturing:
            self.start_capture()
        super().mousePressEvent(event)

    def start_capture(self):
        self.is_capturing = True
        self.original_text = self.text()
        self.setText("请按下按键...")
        self.setProperty("isCapturing", True)
        self.update_style()

    def stop_capture(self):
        self.is_capturing = False
        self.setProperty("isCapturing", False)
        self.update_style()

    def update_style(self):
        # Apply custom style based on capturing state
        color = qconfig.themeColor.name
        if self.property("isCapturing"):
            self.setStyleSheet(f"border: 2px solid {color}; background-color: rgba(0, 159, 227, 0.1);")
        else:
            self.setStyleSheet("")
        self.style().unpolish(self)
        self.style().polish(self)

    def keyPressEvent(self, event):
        if not self.is_capturing:
            return

        key = event.key()
        
        # Modifier keys alone should not be the full hotkey
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return

        modifiers = event.modifiers()
        parts = []

        if modifiers & Qt.ControlModifier:
            parts.append("Ctrl")
        if modifiers & Qt.AltModifier:
            parts.append("Alt")
        if modifiers & Qt.ShiftModifier:
            parts.append("Shift")
        
        key_name = self.get_key_name(key)
        if key_name:
            parts.append(key_name)
            hotkey_str = "+".join(parts)
            self.setText(hotkey_str)
            self.stop_capture()
            self.editingFinished.emit()
        elif key == Qt.Key_Escape:
            self.setText(self.original_text)
            self.stop_capture()

    def focusOutEvent(self, event):
        if self.is_capturing:
            self.setText(self.original_text)
            self.stop_capture()
        super().focusOutEvent(event)

    def get_key_name(self, key):
        if Qt.Key_F1 <= key <= Qt.Key_F12:
            return f"F{key - Qt.Key_F1 + 1}"
        
        # Mapping for other common keys
        key_map = {
            Qt.Key_Space: "Space",
            Qt.Key_Tab: "Tab",
            Qt.Key_Enter: "Enter",
            Qt.Key_Return: "Enter",
            Qt.Key_Escape: "Esc",
            Qt.Key_Backspace: "Backspace",
            Qt.Key_Delete: "Delete",
            Qt.Key_Insert: "Insert",
            Qt.Key_Home: "Home",
            Qt.Key_End: "End",
            Qt.Key_PageUp: "PgUp",
            Qt.Key_PageDown: "PgDn",
        }
        
        if key in key_map:
            return key_map[key]
        
        # Handle regular letters/numbers
        if Qt.Key_0 <= key <= Qt.Key_9 or Qt.Key_A <= key <= Qt.Key_Z:
            return chr(key).upper()
            
        return None
