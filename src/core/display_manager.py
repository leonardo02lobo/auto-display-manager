"""
Display manager - Core logic for managing displays and modes
"""

from typing import List, Optional, Dict, Callable
from enum import Enum
from .xrandr_wrapper import XRandRWrapper, Display


class DisplayMode(Enum):
    """Display mode options"""
    EXTEND = "extend"
    MIRROR = "mirror"
    EXTERNAL_ONLY = "external-only"
    INTERNAL_ONLY = "internal-only"
    AUTO = "auto"


class DisplayManager:
    """Main class for managing display configurations"""
    
    def __init__(self):
        self.xrandr = XRandRWrapper()
        self._displays: List[Display] = []
        self._primary_display: Optional[str] = None
        self._external_displays: List[str] = []
        self._internal_display: Optional[str] = None
        self._refresh_displays()
    
    def _refresh_displays(self) -> None:
        """Refresh the list of displays from xrandr"""
        self._displays = self.xrandr.get_displays()
        self._primary_display = None
        self._external_displays = []
        self._internal_display = None
        
        for display in self._displays:
            if display.primary:
                self._primary_display = display.name
            
            # Identify internal display (usually eDP, LVDS)
            if any(prefix in display.name for prefix in ['eDP', 'LVDS', 'DSI']):
                self._internal_display = display.name
            elif display.connected:
                self._external_displays.append(display.name)
        
        # If no internal display found, use primary as internal
        if not self._internal_display and self._primary_display:
            self._internal_display = self._primary_display
    
    def get_displays(self) -> List[Display]:
        """Get current list of displays"""
        self._refresh_displays()
        return self._displays
    
    def get_connected_displays(self) -> List[Display]:
        """Get list of connected displays"""
        return [d for d in self._displays if d.connected]
    
    def get_external_displays(self) -> List[Display]:
        """Get list of connected external displays"""
        self._refresh_displays()
        return [d for d in self._displays 
                if d.connected and d.name in self._external_displays]
    
    def get_internal_display(self) -> Optional[Display]:
        """Get the internal display"""
        self._refresh_displays()
        if self._internal_display:
            for display in self._displays:
                if display.name == self._internal_display:
                    return display
        return None
    
    def apply_mode(self, mode: DisplayMode, 
                   external_display: Optional[str] = None) -> bool:
        """
        Apply a display mode configuration
        
        Args:
            mode: DisplayMode to apply
            external_display: Specific external display to use (if multiple)
            
        Returns:
            True if successful, False otherwise
        """
        self._refresh_displays()
        
        if not self._internal_display:
            raise RuntimeError("No internal display found")
        
        # Select external display if not specified
        if not external_display and self._external_displays:
            external_display = self._external_displays[0]
        
        if mode == DisplayMode.EXTEND:
            return self._apply_extend_mode(external_display)
        elif mode == DisplayMode.MIRROR:
            return self._apply_mirror_mode(external_display)
        elif mode == DisplayMode.EXTERNAL_ONLY:
            return self._apply_external_only_mode(external_display)
        elif mode == DisplayMode.INTERNAL_ONLY:
            return self._apply_internal_only_mode()
        elif mode == DisplayMode.AUTO:
            return self._apply_auto_mode(external_display)
        
        return False
    
    def _apply_extend_mode(self, external_display: Optional[str]) -> bool:
        """Extend display to external monitor"""
        if not external_display:
            return False
        
        try:
            # Enable internal display and set as primary
            self.xrandr.enable_display(self._internal_display)
            self.xrandr.set_primary_display(self._internal_display)
            
            # Enable external display and position to the right
            self.xrandr.enable_display(external_display)
            self.xrandr.set_display_position(external_display, 
                                            f"--right-of {self._internal_display}")
            return True
        except Exception:
            return False
    
    def _apply_mirror_mode(self, external_display: Optional[str]) -> bool:
        """Mirror internal display to external"""
        if not external_display:
            return False
        
        try:
            # Get internal display resolution
            internal = self.get_internal_display()
            if not internal or not internal.resolution:
                return False
            
            # Enable both displays with same resolution
            self.xrandr.enable_display(self._internal_display)
            self.xrandr.set_primary_display(self._internal_display)
            
            self.xrandr.enable_display(external_display)
            self.xrandr.set_display_mode(external_display, internal.resolution)
            return True
        except Exception:
            return False
    
    def _apply_external_only_mode(self, external_display: Optional[str]) -> bool:
        """Use only external display"""
        if not external_display:
            return False
        
        try:
            # Disable internal display
            self.xrandr.disable_display(self._internal_display)
            
            # Enable external display and set as primary
            self.xrandr.enable_display(external_display)
            self.xrandr.set_primary_display(external_display)
            return True
        except Exception:
            return False
    
    def _apply_internal_only_mode(self) -> bool:
        """Use only internal display"""
        try:
            # Disable all external displays
            for ext_display in self._external_displays:
                self.xrandr.disable_display(ext_display)
            
            # Enable internal display
            self.xrandr.enable_display(self._internal_display)
            self.xrandr.set_primary_display(self._internal_display)
            return True
        except Exception:
            return False
    
    def _apply_auto_mode(self, external_display: Optional[str]) -> bool:
        """Auto-detect and apply appropriate mode"""
        if external_display:
            # Default to extend mode for external displays
            return self._apply_extend_mode(external_display)
        else:
            # No external display, use internal only
            return self._apply_internal_only_mode()
    
    def has_external_display(self) -> bool:
        """Check if there's at least one external display connected"""
        self._refresh_displays()
        return len(self._external_displays) > 0
