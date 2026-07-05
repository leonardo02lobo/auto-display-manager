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
            print("[ERROR] No external display provided for extend mode")
            return False
        
        try:
            print(f"[INFO] Extending: {self._internal_display} -> {external_display}")
            
            # Enable internal display and set as primary
            if not self.xrandr.enable_display(self._internal_display):
                print(f"[ERROR] Failed to enable internal display {self._internal_display}")
                return False
            
            if not self.xrandr.set_primary_display(self._internal_display):
                print(f"[ERROR] Failed to set {self._internal_display} as primary")
                return False
            
            # Enable external display and position to the right
            if not self.xrandr.enable_display(external_display):
                print(f"[ERROR] Failed to enable external display {external_display}")
                return False
            
            if not self.xrandr.set_display_position(external_display, 
                                            f"--right-of {self._internal_display}"):
                print(f"[ERROR] Failed to position {external_display}")
                return False
            
            print("[INFO] Extend mode applied successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Exception in extend mode: {e}")
            return False
    
    def _apply_mirror_mode(self, external_display: Optional[str]) -> bool:
        """Mirror internal display to external"""
        if not external_display:
            print("[ERROR] No external display provided for mirror mode")
            return False
        
        try:
            # Get internal display resolution
            internal = self.get_internal_display()
            if not internal:
                print(f"[ERROR] Internal display not found: {self._internal_display}")
                return False
            
            if not internal.resolution:
                print("[ERROR] Internal display has no resolution")
                return False
            
            print(f"[INFO] Mirroring: {self._internal_display} ({internal.resolution}) -> {external_display}")
            
            # Enable internal display and set as primary
            if not self.xrandr.enable_display(self._internal_display):
                print(f"[ERROR] Failed to enable internal display {self._internal_display}")
                return False
            
            if not self.xrandr.set_primary_display(self._internal_display):
                print(f"[ERROR] Failed to set {self._internal_display} as primary")
                return False
            
            # Get available modes for external display
            external_modes = self.xrandr.get_display_modes(external_display)
            print(f"[INFO] Available modes for {external_display}: {external_modes}")
            
            # Check if internal resolution is available on external
            if internal.resolution not in external_modes:
                print(f"[WARNING] Resolution {internal.resolution} not available on {external_display}")
                # Use first available mode as fallback
                if external_modes:
                    internal.resolution = external_modes[0]
                    print(f"[INFO] Using fallback resolution: {internal.resolution}")
                else:
                    print("[ERROR] No available modes on external display")
                    return False
            
            # Enable external display with same resolution
            if not self.xrandr.enable_display(external_display):
                print(f"[ERROR] Failed to enable external display {external_display}")
                return False
            
            if not self.xrandr.set_display_mode(external_display, internal.resolution):
                print(f"[ERROR] Failed to set mode {internal.resolution} on {external_display}")
                return False
            
            print("[INFO] Mirror mode applied successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Exception in mirror mode: {e}")
            return False
    
    def _apply_external_only_mode(self, external_display: Optional[str]) -> bool:
        """Use only external display"""
        if not external_display:
            print("[ERROR] No external display provided for external-only mode")
            return False
        
        try:
            print(f"[INFO] External-only mode: {external_display}")
            
            # Disable internal display
            if not self.xrandr.disable_display(self._internal_display):
                print(f"[WARNING] Failed to disable internal display {self._internal_display}")
            
            # Enable external display and set as primary
            if not self.xrandr.enable_display(external_display):
                print(f"[ERROR] Failed to enable external display {external_display}")
                return False
            
            if not self.xrandr.set_primary_display(external_display):
                print(f"[ERROR] Failed to set {external_display} as primary")
                return False
            
            print("[INFO] External-only mode applied successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Exception in external-only mode: {e}")
            return False
    
    def _apply_internal_only_mode(self) -> bool:
        """Use only internal display"""
        try:
            print(f"[INFO] Internal-only mode: {self._internal_display}")
            
            # Disable all external displays
            for ext_display in self._external_displays:
                print(f"[INFO] Disabling external display: {ext_display}")
                if not self.xrandr.disable_display(ext_display):
                    print(f"[WARNING] Failed to disable {ext_display}")
            
            # Enable internal display
            if not self.xrandr.enable_display(self._internal_display):
                print(f"[ERROR] Failed to enable internal display {self._internal_display}")
                return False
            
            if not self.xrandr.set_primary_display(self._internal_display):
                print(f"[ERROR] Failed to set {self._internal_display} as primary")
                return False
            
            print("[INFO] Internal-only mode applied successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Exception in internal-only mode: {e}")
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
