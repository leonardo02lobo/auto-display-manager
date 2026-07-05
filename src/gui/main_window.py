"""
Main window for Auto Display Manager GUI
"""

import sys
from typing import Optional
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QComboBox, QPushButton, QListWidget, 
                            QListWidgetItem, QGroupBox, QTextEdit, QCheckBox,
                            QMessageBox, QSplitter, QSystemTrayIcon, QMenu, QStyle)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QAction

from core.display_manager import DisplayManager, DisplayMode
from core.monitor_detector import MonitorDetector
from config.modes import DISPLAY_MODES, get_mode_list


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signal for display changes
    display_changed = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        
        self.display_manager = None
        self.monitor_detector = None
        self.tray_icon = None
        self.refresh_timer = None
        
        self._auto_apply = False
        self._selected_mode = DisplayMode.EXTEND
        
        try:
            self._init_ui()
            self._log("UI inicializada")
        except Exception as e:
            self._log(f"Error inicializando UI: {e}")
            raise
        
        # Initialize display manager (may cause segfault)
        try:
            self._log("Inicializando display manager...")
            self.display_manager = DisplayManager()
            self._log("Display manager inicializado")
        except Exception as e:
            self._log(f"Error inicializando display manager: {e}")
            raise
        
        # Initialize monitor detector
        try:
            self._log("Inicializando monitor detector...")
            self.monitor_detector = MonitorDetector(
                callback=self._on_display_changed,
                poll_interval=2.0
            )
            self.monitor_detector.set_display_manager(self.display_manager)
            self._log("Monitor detector inicializado")
        except Exception as e:
            self._log(f"Error inicializando monitor detector: {e}")
            self.monitor_detector = None
        
        # Initialize system tray
        try:
            self._init_system_tray()
        except Exception as e:
            self._log(f"Error inicializando system tray: {e}")
        
        # Refresh display list
        try:
            self._refresh_display_list()
        except Exception as e:
            self._log(f"Error refrescando display list: {e}")
        
        # Start monitor detection
        if self.monitor_detector:
            try:
                self.monitor_detector.start()
                self._log("Monitor detector iniciado")
            except Exception as e:
                self._log(f"Error iniciando monitor detector: {e}")
        
        # Auto-refresh timer
        try:
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self._refresh_display_list)
            self.refresh_timer.start(5000)  # Refresh every 5 seconds
            self._log("Timer iniciado")
        except Exception as e:
            self._log(f"Error iniciando timer: {e}")
    
    def _init_ui(self) -> None:
        """Initialize the user interface"""
        self.setWindowTitle("Auto Display Manager")
        self.setMinimumSize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("Auto Display Manager")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Display list
        left_panel = self._create_display_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Controls and log
        right_panel = self._create_control_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
    
    def _create_display_panel(self) -> QGroupBox:
        """Create the display list panel"""
        group = QGroupBox("Monitores Detectados")
        layout = QVBoxLayout()
        
        self.display_list = QListWidget()
        self.display_list.itemSelectionChanged.connect(self._on_display_selected)
        layout.addWidget(self.display_list)
        
        # Refresh button
        refresh_btn = QPushButton("Refrescar")
        refresh_btn.clicked.connect(self._refresh_display_list)
        layout.addWidget(refresh_btn)
        
        group.setLayout(layout)
        return group
    
    def _create_control_panel(self) -> QWidget:
        """Create the control panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Mode selection group
        mode_group = QGroupBox("Modo de Pantalla")
        mode_layout = QVBoxLayout()
        
        self.mode_combo = QComboBox()
        for mode_key in get_mode_list():
            mode_config = DISPLAY_MODES[mode_key]
            self.mode_combo.addItem(mode_config.name, mode_key)
        
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)
        
        # Mode description
        self.mode_description = QLabel()
        self.mode_description.setWordWrap(True)
        mode_layout.addWidget(self.mode_description)
        
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Auto-apply checkbox
        self.auto_apply_checkbox = QCheckBox("Aplicar automáticamente al conectar")
        self.auto_apply_checkbox.toggled.connect(self._on_auto_apply_toggled)
        layout.addWidget(self.auto_apply_checkbox)
        
        # Apply button
        self.apply_btn = QPushButton("Aplicar Configuración")
        self.apply_btn.clicked.connect(self._apply_configuration)
        self.apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.apply_btn)
        
        # Log group
        log_group = QGroupBox("Log de Eventos")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        return widget
    
    def _init_system_tray(self) -> None:
        """Initialize system tray icon"""
        self.tray_icon = None
        
        try:
            # Check if system tray is available
            if not QSystemTrayIcon.isSystemTrayAvailable():
                self._log("System tray not available")
                return
            
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(self.style().standardIcon(
                QStyle.StandardPixmap.SP_ComputerIcon
            ))
            
            # Create tray menu
            tray_menu = QMenu()
            
            show_action = QAction("Mostrar", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            quit_action = QAction("Salir", self)
            quit_action.triggered.connect(self.close)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            self._log("System tray initialized")
            
        except Exception as e:
            self._log(f"Error initializing system tray: {e}")
            self.tray_icon = None
    
    def _refresh_display_list(self) -> None:
        """Refresh the display list"""
        self.display_list.clear()
        
        try:
            displays = self.display_manager.get_displays()
            
            for display in displays:
                status = "Conectado" if display.connected else "Desconectado"
                primary = " (Primario)" if display.primary else ""
                resolution = f" - {display.resolution}" if display.resolution else ""
                
                item_text = f"{display.name}: {status}{primary}{resolution}"
                item = QListWidgetItem(item_text)
                
                if display.connected:
                    item.setForeground(Qt.GlobalColor.green)
                else:
                    item.setForeground(Qt.GlobalColor.gray)
                
                self.display_list.addItem(item)
            
            # Update mode description
            self._update_mode_description()
            
        except Exception as e:
            self._log(f"Error al refrescar displays: {e}")
    
    def _update_mode_description(self) -> None:
        """Update the mode description label"""
        mode_key = self.mode_combo.currentData()
        if mode_key:
            mode_config = DISPLAY_MODES[mode_key]
            self.mode_description.setText(mode_config.description)
    
    def _on_display_selected(self) -> None:
        """Handle display selection"""
        pass
    
    def _on_mode_changed(self, index: int) -> None:
        """Handle mode selection change"""
        mode_key = self.mode_combo.currentData()
        if mode_key:
            mode_map = {
                "extend": DisplayMode.EXTEND,
                "mirror": DisplayMode.MIRROR,
                "external-only": DisplayMode.EXTERNAL_ONLY,
                "internal-only": DisplayMode.INTERNAL_ONLY,
                "auto": DisplayMode.AUTO
            }
            self._selected_mode = mode_map.get(mode_key, DisplayMode.EXTEND)
            self._update_mode_description()
    
    def _on_auto_apply_toggled(self, checked: bool) -> None:
        """Handle auto-apply checkbox toggle"""
        self._auto_apply = checked
        self._log(f"Auto-aplicar: {'Activado' if checked else 'Desactivado'}")
    
    def _apply_configuration(self) -> None:
        """Apply the selected display configuration"""
        try:
            external_displays = self.display_manager.get_external_displays()
            external_display = external_displays[0].name if external_displays else None
            
            success = self.display_manager.apply_mode(
                self._selected_mode,
                external_display
            )
            
            if success:
                self._log(f"Configuración aplicada: {self._selected_mode.value}")
                self._refresh_display_list()
            else:
                self._log("Error al aplicar configuración")
                QMessageBox.warning(self, "Error", 
                                   "No se pudo aplicar la configuración")
        
        except Exception as e:
            self._log(f"Error al aplicar configuración: {e}")
            QMessageBox.critical(self, "Error", str(e))
    
    def _on_display_changed(self, connected: bool, display_name: Optional[str]) -> None:
        """Handle display connection/disconnection event"""
        if connected:
            self._log(f"Monitor conectado: {display_name}")
            
            if self._auto_apply:
                self._log("Aplicando configuración automáticamente...")
                QTimer.singleShot(1000, self._apply_configuration)
        else:
            self._log("Monitor desconectado")
            
            if self._auto_apply:
                self._log("Aplicando configuración interna...")
                self.display_manager.apply_mode(DisplayMode.INTERNAL_ONLY)
        
        self._refresh_display_list()
    
    def _log(self, message: str) -> None:
        """Add message to log"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def closeEvent(self, event) -> None:
        """Handle window close event"""
        self.monitor_detector.stop()
        self.refresh_timer.stop()
        
        # Hide to tray instead of closing if tray is available
        if self.tray_icon and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()


