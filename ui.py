import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QComboBox, QPushButton, QLabel, QGraphicsDropShadowEffect, QFrame,
    QCheckBox, QStackedWidget
)
from PyQt6.QtCore import Qt, QPoint, QThread, pyqtSignal, QSize, QTimer
from PyQt6.QtGui import QColor, QFont, QCursor, QIcon, QGuiApplication, QKeySequence

# Import configuration helpers
from settings_manager import load_config, save_config, apply_shortcut, apply_autostart

# Import the translation function
from translator import translate_text

# Supported languages list (code, display name)
LANGUAGES = [
    ("auto", "Auto Detect"),
    ("vi", "Vietnamese"),
    ("en", "English"),
    ("ja", "Japanese"),
    ("zh-CN", "Chinese (Simplified)"),
    ("ko", "Korean"),
    ("fr", "French"),
    ("de", "German"),
    ("es", "Spanish"),
    ("ru", "Russian"),
]

class TranslationWorker(QThread):
    """
    Worker thread to perform translation asynchronously 
    so the UI remains responsive during network requests.
    """
    finished = pyqtSignal(str)

    def __init__(self, text, source, target):
        super().__init__()
        self.text = text
        self.source = source
        self.target = target

    def run(self):
        result = translate_text(self.text, self.source, self.target)
        self.finished.emit(result)


class TranslationPopup(QWidget):
    def __init__(self, text_to_translate: str):
        super().__init__()
        self.original_text = text_to_translate
        
        # Default translation settings
        self.source_lang = "auto"
        self.target_lang = "vi"
        self.worker = None
        self.recording_shortcut = False

        # Setup window properties
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.init_ui()
        self.position_near_cursor()
        
        # Start initial translation
        self.trigger_translation()


    def init_ui(self):
        # Set base geometry (wider popup with initial height)
        self.setFixedWidth(650)
        self.resize(650, 360)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # Margins for the drop shadow
        
        # Container Widget for the actual UI (so we can apply style & shadow)
        self.container = QFrame(self)
        self.container.setObjectName("Container")
        
        # Premium CSS Styling (Catppuccin Mocha Dark Theme style with glass opacity)
        self.container.setStyleSheet("""
            QFrame#Container {
                background-color: rgba(30, 30, 46, 0.70);
                border-radius: 12px;
                border: 1px solid rgba(49, 50, 68, 0.5);
            }
            QPushButton#SettingsBtn {
                background-color: transparent;
                color: #a6adc8;
                font-size: 16px;
                padding: 2px 8px;
            }
            QPushButton#SettingsBtn:hover {
                background-color: #45475a;
                color: #89b4fa;
            }
            QPushButton#ShortcutRecBtn {
                background-color: rgba(24, 24, 37, 0.50);
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 6px;
                font-family: 'Segoe UI', 'DejaVu Sans', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#ShortcutRecBtn:hover {
                background-color: #313244;
                border: 1px solid #89b4fa;
            }
            QLabel {
                color: #cdd6f4;
                font-family: 'Segoe UI', 'DejaVu Sans', sans-serif;
            }
            QComboBox {
                background-color: rgba(24, 24, 37, 0.50);
                color: #cdd6f4;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 4px 8px;
                font-family: 'Segoe UI', 'DejaVu Sans', sans-serif;
                font-size: 11px;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: #181825;
                color: #cdd6f4;
                selection-background-color: #89b4fa;
                selection-color: #11111b;
                border: 1px solid #313244;
            }
            QTextEdit {
                background-color: rgba(24, 24, 37, 0.50);
                color: #cdd6f4;
                border: 1px solid rgba(24, 24, 37, 0.50);
                border-radius: 6px;
                font-family: 'Segoe UI', 'DejaVu Sans', sans-serif;
                font-size: 13px;
                padding: 6px;
            }
            QTextEdit:focus {
                border: 1px solid #89b4fa;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-family: 'Segoe UI', 'DejaVu Sans', sans-serif;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton:pressed {
                background-color: #89b4fa;
                color: #11111b;
            }
            QPushButton#TranslateBtn {
                background-color: #89b4fa;
                color: #11111b;
            }
            QPushButton#TranslateBtn:hover {
                background-color: #b4befe;
            }
            QPushButton#TranslateBtn:pressed {
                background-color: #a6e3a1;
            }
            QPushButton#TranslateBtn:disabled {
                background-color: rgba(24, 24, 37, 0.5);
                color: #585b70;
                border: 1px solid #313244;
            }
            QPushButton#CloseBtn {
                background-color: transparent;
                color: #a6adc8;
                font-size: 14px;
                padding: 2px 8px;
            }
            QPushButton#CloseBtn:hover {
                background-color: #f38ba8;
                color: #11111b;
            }
            QScrollBar:vertical {
                border: none;
                background-color: rgba(24, 24, 37, 0.3);
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(137, 180, 250, 0.5);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(137, 180, 250, 0.8);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        # Apply Shadow Effect to Container
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)
        
        # Container Layout
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(12, 12, 12, 12)
        container_layout.setSpacing(10)
        
        # Use QStackedWidget to support switching between Translation and Settings pages
        self.stacked_widget = QStackedWidget()
        container_layout.addWidget(self.stacked_widget)
        
        # --- Page 0: Translation Page ---
        self.translation_page = QWidget()
        trans_page_layout = QVBoxLayout(self.translation_page)
        trans_page_layout.setContentsMargins(0, 0, 0, 0)
        trans_page_layout.setSpacing(10)
        
        # 1. Header (Language selectors & Settings & Close button)
        header_layout = QHBoxLayout()
        
        self.src_combo = QComboBox()
        self.dest_combo = QComboBox()
        
        # Populate combos
        for code, name in LANGUAGES:
            self.src_combo.addItem(name, code)
            if code != "auto":
                self.dest_combo.addItem(name, code)
        
        # Set default selection
        self.src_combo.setCurrentIndex(0)  # Auto Detect
        self.dest_combo.setCurrentIndex(0)  # Vietnamese
        
        # Arrow label
        arrow_label = QLabel("→")
        arrow_label.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 14px;")
        
        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("SettingsBtn")
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self.go_to_settings)
        
        close_btn = QPushButton("×")
        close_btn.setObjectName("CloseBtn")
        close_btn.setToolTip("Close (or click outside)")
        close_btn.clicked.connect(self.close)
        
        header_layout.addWidget(self.src_combo)
        header_layout.addWidget(arrow_label)
        header_layout.addWidget(self.dest_combo)
        header_layout.addStretch()
        header_layout.addWidget(settings_btn)
        header_layout.addWidget(close_btn)
        
        # 2. Text Areas
        self.src_text_edit = QTextEdit()
        self.src_text_edit.setPlaceholderText("Type text to translate...")
        self.src_text_edit.setPlainText(self.original_text)
        self.src_text_edit.setFixedHeight(100)
        
        self.dest_text_edit = QTextEdit()
        self.dest_text_edit.setPlaceholderText("Translation will appear here...")
        self.dest_text_edit.setReadOnly(True)
        self.dest_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dest_text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 3. Footer (Action buttons)
        footer_layout = QHBoxLayout()
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
        
        self.copy_src_btn = QPushButton("Copy Src")
        self.copy_src_btn.setToolTip("Copy source text to clipboard")
        self.copy_src_btn.clicked.connect(self.copy_source)
        
        self.copy_dest_btn = QPushButton("Copy Translation")
        self.copy_dest_btn.setToolTip("Copy translated text to clipboard")
        self.copy_dest_btn.clicked.connect(self.copy_translation)
        
        self.trans_btn = QPushButton("Translate")
        self.trans_btn.setObjectName("TranslateBtn")
        self.trans_btn.clicked.connect(self.trigger_translation)
        
        footer_layout.addWidget(self.status_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.copy_src_btn)
        footer_layout.addWidget(self.copy_dest_btn)
        footer_layout.addWidget(self.trans_btn)
        
        # Assemble Translation Page
        trans_page_layout.addLayout(header_layout)
        trans_page_layout.addWidget(self.src_text_edit)
        trans_page_layout.addWidget(self.dest_text_edit)
        trans_page_layout.addLayout(footer_layout)
        
        self.stacked_widget.addWidget(self.translation_page)
        
        # --- Page 1: Settings Page ---
        self.settings_page = QWidget()
        settings_page_layout = QVBoxLayout(self.settings_page)
        settings_page_layout.setContentsMargins(0, 0, 0, 0)
        settings_page_layout.setSpacing(15)
        
        # Settings Header
        settings_header_layout = QHBoxLayout()
        settings_title = QLabel("Settings")
        settings_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #89b4fa;")
        
        settings_close_btn = QPushButton("×")
        settings_close_btn.setObjectName("CloseBtn")
        settings_close_btn.setToolTip("Close Settings")
        settings_close_btn.clicked.connect(self.go_to_translation)
        
        settings_header_layout.addWidget(settings_title)
        settings_header_layout.addStretch()
        settings_header_layout.addWidget(settings_close_btn)
        
        # Settings Body
        settings_body = QVBoxLayout()
        settings_body.setSpacing(12)
        
        # Shortcut Recording Row
        shortcut_row = QHBoxLayout()
        shortcut_label = QLabel("Global Shortcut:")
        shortcut_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        
        self.shortcut_rec_btn = QPushButton("Ctrl+Q")
        self.shortcut_rec_btn.setObjectName("ShortcutRecBtn")
        self.shortcut_rec_btn.setToolTip("Click to record a new global shortcut")
        self.shortcut_rec_btn.setFixedWidth(180)
        self.shortcut_rec_btn.clicked.connect(self.start_recording_shortcut)
        
        shortcut_row.addWidget(shortcut_label)
        shortcut_row.addWidget(self.shortcut_rec_btn)
        shortcut_row.addStretch()
        
        # Autostart Checkbox Row
        autostart_row = QHBoxLayout()
        self.autostart_checkbox = QCheckBox("Start application automatically on boot")
        self.autostart_checkbox.setStyleSheet("""
            QCheckBox {
                color: #cdd6f4;
                font-family: 'Segoe UI', 'DejaVu Sans', sans-serif;
                font-size: 13px;
                font-weight: bold;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                background-color: rgba(24, 24, 37, 0.50);
                border: 1px solid #313244;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #89b4fa;
                border: 1px solid #89b4fa;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #89b4fa;
            }
        """)
        autostart_row.addWidget(self.autostart_checkbox)
        autostart_row.addStretch()
        
        # Conflict Warning Label
        self.shortcut_warning = QLabel("Note: Common browser shortcuts (e.g. Ctrl+Q) might conflict when the browser is active.")
        self.shortcut_warning.setStyleSheet("color: #f38ba8; font-size: 11px; font-style: italic;")
        self.shortcut_warning.setWordWrap(True)
        
        settings_body.addLayout(shortcut_row)
        settings_body.addLayout(autostart_row)
        settings_body.addWidget(self.shortcut_warning)
        settings_body.addStretch()
        
        # Settings Footer
        settings_footer_layout = QHBoxLayout()
        
        self.settings_status = QLabel("")
        self.settings_status.setStyleSheet("color: #a6adc8; font-size: 11px;")
        
        settings_back_btn = QPushButton("Back")
        settings_back_btn.clicked.connect(self.go_to_translation)
        
        settings_save_btn = QPushButton("Save Settings")
        settings_save_btn.setObjectName("TranslateBtn")
        settings_save_btn.clicked.connect(self.save_settings)
        
        settings_footer_layout.addWidget(self.settings_status)
        settings_footer_layout.addStretch()
        settings_footer_layout.addWidget(settings_back_btn)
        settings_footer_layout.addWidget(settings_save_btn)
        
        # Assemble Settings Page
        settings_page_layout.addLayout(settings_header_layout)
        settings_page_layout.addLayout(settings_body)
        settings_page_layout.addLayout(settings_footer_layout)
        
        self.stacked_widget.addWidget(self.settings_page)
        
        main_layout.addWidget(self.container)
        
        # Connect signals
        self.src_combo.currentIndexChanged.connect(self.on_language_changed)
        self.dest_combo.currentIndexChanged.connect(self.on_language_changed)
        self.src_text_edit.textChanged.connect(self.on_source_text_changed)
        # Re-translate when user changes source text and presses Enter or leaves focus (we trigger via the Translate button or manual shortcut, let's keep it simple)

    def position_near_cursor(self):
        """Positions the popup near the cursor, ensuring it stays on screen."""
        cursor_pos = QCursor.pos()
        
        # Get screen geometry where the cursor resides
        screen = QGuiApplication.screenAt(cursor_pos)
        if not screen:
            screen = QGuiApplication.primaryScreen()
        screen_geo = screen.geometry()
        
        # Offsets
        x_offset = 12
        y_offset = 12
        
        target_x = cursor_pos.x() + x_offset
        target_y = cursor_pos.y() + y_offset
        
        # Boundary checks
        window_width = self.width()
        window_height = self.height()
        
        # If it goes beyond right screen edge, place it to the left of the cursor
        if target_x + window_width > screen_geo.right():
            target_x = cursor_pos.x() - window_width - x_offset
            
        # If it goes beyond bottom screen edge, place it above the cursor
        if target_y + window_height > screen_geo.bottom():
            target_y = cursor_pos.y() - window_height - y_offset
            
        # Clamp to screen boundaries just in case
        target_x = max(screen_geo.left(), min(target_x, screen_geo.right() - window_width))
        target_y = max(screen_geo.top(), min(target_y, screen_geo.bottom() - window_height))
        
        self.move(target_x, target_y)

    def keep_on_screen_after_resize(self):
        """Ensures the window stays fully on screen after its height changes, without jumping back to the cursor."""
        pos = self.pos()
        window_width = self.width()
        window_height = self.height()
        
        # Get screen geometry where the window resides
        screen = QGuiApplication.screenAt(pos)
        if not screen:
            screen = QGuiApplication.primaryScreen()
        screen_geo = screen.geometry()
        
        target_y = pos.y()
        # If the bottom of the window goes off-screen, shift it up
        if target_y + window_height > screen_geo.bottom():
            target_y = screen_geo.bottom() - window_height
            # Make sure we don't push it off the top edge
            target_y = max(screen_geo.top(), target_y)
            
        self.move(pos.x(), target_y)

    def on_source_text_changed(self):
        # Enable the translate button when the source text changes
        self.trans_btn.setEnabled(True)

    def trigger_translation(self):
        text = self.src_text_edit.toPlainText().strip()
        if not text:
            self.dest_text_edit.setPlainText("")
            return

        # Cancel existing worker if running
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()

        # Update UI state
        self.status_label.setText("Translating...")
        self.dest_text_edit.setPlaceholderText("Translating...")
        self.trans_btn.setEnabled(False)
        
        # Get selected language codes
        src_code = self.src_combo.currentData()
        dest_code = self.dest_combo.currentData()

        # Start background translation worker
        self.worker = TranslationWorker(text, src_code, dest_code)
        self.worker.finished.connect(self.on_translation_finished)
        self.worker.start()

    def on_translation_finished(self, translated_text):
        self.dest_text_edit.setPlainText(translated_text)
        self.status_label.setText("")
        # Keep button disabled if translation succeeds, enable on error for retry
        if translated_text.startswith("Error:") or translated_text.startswith("Network Error:") or translated_text.startswith("Unexpected Error:"):
            self.trans_btn.setEnabled(True)
        else:
            self.trans_btn.setEnabled(False)
        # Adjust height of translation output dynamically to display it fully
        self.adjust_translation_height()

    def adjust_translation_height(self):
        # Set text width of document to match QTextEdit width minus standard scrollbar/padding offsets
        width = self.dest_text_edit.width()
        if width > 0:
            self.dest_text_edit.document().setTextWidth(width - 12)
        doc_height = int(self.dest_text_edit.document().size().height())
        calculated_height = doc_height + 16
        
        max_height = 250  # Limit the height of the translation box
        
        if calculated_height > max_height:
            new_height = max_height
            self.dest_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            new_height = max(100, calculated_height)
            self.dest_text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
        self.dest_text_edit.setFixedHeight(new_height)
        self.adjustSize()
        # Keep the popup within screen bounds without snapping back to the mouse
        self.keep_on_screen_after_resize()

    def on_language_changed(self):
        # Automatically re-translate when language selection changes
        self.trigger_translation()

    def copy_source(self):
        source_text = self.src_text_edit.toPlainText()
        if source_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(source_text)
            self.status_label.setText("Copied source text!")
            QTimer.singleShot(2000, lambda: self.status_label.setText(""))

    def copy_translation(self):
        translated_text = self.dest_text_edit.toPlainText()
        if translated_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(translated_text)
            self.status_label.setText("Copied translation!")
            QTimer.singleShot(2000, lambda: self.status_label.setText(""))

    def showEvent(self, event):
        """Record the time when the window was shown to prevent premature closing."""
        super().showEvent(event)
        import time
        self.show_time = time.time()
        # Force window to top and activate focus
        self.raise_()
        self.activateWindow()

    def changeEvent(self, event):
        """Detect when window loses focus and close it automatically."""
        super().changeEvent(event)
        if event.type() == event.Type.ActivationChange:
            if self.isActiveWindow():
                self.has_been_active = True
            elif not self.isActiveWindow():
                # Only check and close if it has been active at least once
                if hasattr(self, 'has_been_active') and self.has_been_active:
                    # Delay slightly to prevent closing when interacting with dropdowns
                    QTimer.singleShot(150, self.check_focus_and_close)

    def check_focus_and_close(self):
        """Checks if the window or application has lost focus, and closes if so."""
        if not hasattr(self, 'show_time'):
            return

        import time
        # Do not close within the first 500ms of showing to allow window manager to focus
        if time.time() - self.show_time < 0.5:
            return

        if not self.isActiveWindow() and QApplication.activeWindow() is None:
            # Check if one of the combos has the active popup list
            active_popup = False
            for widget in QApplication.topLevelWidgets():
                if widget != self and widget.isVisible():
                    if widget.inherits("QAbstractPopup") or (widget.windowFlags() & Qt.WindowType.Popup):
                        active_popup = True
                        break
            
            if not active_popup:
                self.close()
                QApplication.quit()
                
    def go_to_settings(self):
        self.recording_shortcut = False
        config = load_config()
        self.shortcut_rec_btn.setText(config.get("shortcut", "Ctrl+Q"))
        self.autostart_checkbox.setChecked(config.get("autostart", False))
        self.stacked_widget.setCurrentIndex(1)
        self.resize(650, 250)
        self.adjustSize()

    def go_to_translation(self):
        self.recording_shortcut = False
        self.stacked_widget.setCurrentIndex(0)
        self.adjust_translation_height()

    def start_recording_shortcut(self):
        self.recording_shortcut = True
        self.shortcut_rec_btn.setText("Press keys...")
        self.shortcut_rec_btn.setStyleSheet("""
            QPushButton#ShortcutRecBtn {
                border: 2px solid #89b4fa;
                background-color: rgba(137, 180, 250, 0.15);
                color: #89b4fa;
            }
        """)

    def save_settings(self):
        shortcut = self.shortcut_rec_btn.text()
        autostart = self.autostart_checkbox.isChecked()
        
        if shortcut == "Press keys..." or shortcut == "Listening...":
            self.settings_status.setText("Please press a valid shortcut first")
            return
            
        self.settings_status.setText("Saving...")
        QApplication.processEvents()
        
        # 1. Apply global shortcut in system settings
        success_shortcut, msg_shortcut = apply_shortcut(shortcut)
        if not success_shortcut:
            self.settings_status.setText(f"Error: {msg_shortcut}")
            return
            
        # 2. Apply autostart entry
        success_autostart, msg_autostart = apply_autostart(autostart)
        if not success_autostart:
            self.settings_status.setText(f"Error: {msg_autostart}")
            return
            
        # 3. Save configuration JSON
        config = {
            "shortcut": shortcut,
            "autostart": autostart
        }
        save_config(config)
        
        self.settings_status.setText("Settings saved!")
        QTimer.singleShot(1000, self.go_to_translation)

    def keyPressEvent(self, event):
        """Handle key presses including global shortcut recording and escape key."""
        if hasattr(self, 'recording_shortcut') and self.recording_shortcut:
            is_modifier = event.key() in [
                Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, 
                Qt.Key.Key_Meta, Qt.Key.Key_Super
            ]
            
            modifiers = event.modifiers()
            keys = []
            
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                keys.append("Ctrl")
            if modifiers & Qt.KeyboardModifier.AltModifier:
                keys.append("Alt")
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                keys.append("Shift")
            if modifiers & Qt.KeyboardModifier.MetaModifier:
                keys.append("Super")
                
            if not is_modifier:
                key_text = QKeySequence(event.key()).toString()
                if key_text:
                    if len(key_text) == 1:
                        key_text = key_text.upper()
                    keys.append(key_text)
                
                shortcut_str = "+".join(keys)
                self.shortcut_rec_btn.setText(shortcut_str)
                self.recording_shortcut = False
                self.shortcut_rec_btn.setStyleSheet("")  # Reset stylesheet
            else:
                shortcut_str = "+".join(keys) + "+..." if keys else "Press keys..."
                self.shortcut_rec_btn.setText(shortcut_str)
                
            event.accept()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
            QApplication.quit()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Record coordinates of mouse press to support window dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Move the window based on mouse drag."""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Test with dummy text
    popup = TranslationPopup("Testing this amazing Linux translator application.")
    popup.show()
    sys.exit(app.exec())
