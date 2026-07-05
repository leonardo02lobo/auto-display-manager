"""
Wrapper for xrandr commands to manage displays
"""

import subprocess
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Display:
    """Represents a display/monitor"""
    name: str
    connected: bool
    primary: bool
    resolution: Optional[str] = None
    current_mode: Optional[str] = None
    available_modes: List[str] = None
    
    def __post_init__(self):
        if self.available_modes is None:
            self.available_modes = []


class XRandRWrapper:
    """Wrapper class for xrandr command line tool"""
    
    def __init__(self):
        self._check_xrandr_available()
    
    def _check_xrandr_available(self) -> None:
        """Check if xrandr is available on the system"""
        try:
            subprocess.run(['xrandr', '--version'], 
                         capture_output=True, 
                         check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("xrandr is not installed or not available in PATH")
    
    def get_displays(self) -> List[Display]:
        """
        Get list of all displays detected by xrandr
        
        Returns:
            List of Display objects with current status
        """
        try:
            result = subprocess.run(['xrandr'], 
                                  capture_output=True, 
                                  text=True, 
                                  check=True)
            return self._parse_xrandr_output(result.stdout)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to execute xrandr: {e.stderr}")
    
    def _parse_xrandr_output(self, output: str) -> List[Display]:
        """
        Parse xrandr output into Display objects
        
        Args:
            output: Raw xrandr output
            
        Returns:
            List of Display objects
        """
        displays = []
        lines = output.split('\n')
        
        for line in lines:
            # Match display line (e.g., "HDMI-1 connected 1920x1080+0+0")
            match = re.match(r'^(\S+)\s+(connected|disconnected)', line)
            if match:
                name = match.group(1)
                connected = match.group(2) == 'connected'
                primary = 'primary' in line
                
                # Extract current resolution if connected
                resolution = None
                current_mode = None
                available_modes = []
                
                if connected:
                    res_match = re.search(r'(\d{3,4}x\d{3,4})', line)
                    if res_match:
                        resolution = res_match.group(1)
                
                displays.append(Display(
                    name=name,
                    connected=connected,
                    primary=primary,
                    resolution=resolution,
                    current_mode=resolution,
                    available_modes=available_modes
                ))
        
        return displays
    
    def get_display_modes(self, display_name: str) -> List[str]:
        """
        Get available resolutions/modes for a specific display
        
        Args:
            display_name: Name of the display (e.g., HDMI-1)
            
        Returns:
            List of available resolution strings
        """
        try:
            result = subprocess.run(['xrandr'], 
                                  capture_output=True, 
                                  text=True, 
                                  check=True)
            return self._parse_display_modes(result.stdout, display_name)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get display modes: {e.stderr}")
    
    def _parse_display_modes(self, output: str, display_name: str) -> List[str]:
        """
        Parse available modes for a specific display from xrandr output
        
        Args:
            output: Raw xrandr output
            display_name: Name of the display
            
        Returns:
            List of available resolution strings
        """
        lines = output.split('\n')
        modes = []
        found_display = False
        
        for line in lines:
            if line.startswith(display_name):
                found_display = True
                continue
            
            if found_display:
                # Stop at next display
                if re.match(r'^\S+\s+(connected|disconnected)', line):
                    break
                
                # Extract resolution (e.g., "1920x1080     60.00*+")
                mode_match = re.match(r'^\s*(\d{3,4}x\d{3,4})', line)
                if mode_match:
                    resolution = mode_match.group(1)
                    if resolution not in modes:
                        modes.append(resolution)
        
        return modes
    
    def set_display_mode(self, display_name: str, mode: str) -> bool:
        """
        Set the resolution/mode for a specific display
        
        Args:
            display_name: Name of the display
            mode: Resolution string (e.g., "1920x1080")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(['xrandr', '--output', display_name, '--mode', mode],
                         capture_output=True,
                         check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def enable_display(self, display_name: str) -> bool:
        """
        Enable a display
        
        Args:
            display_name: Name of the display
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(['xrandr', '--output', display_name, '--auto'],
                         capture_output=True,
                         check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def disable_display(self, display_name: str) -> bool:
        """
        Disable a display
        
        Args:
            display_name: Name of the display
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(['xrandr', '--output', display_name, '--off'],
                         capture_output=True,
                         check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def set_primary_display(self, display_name: str) -> bool:
        """
        Set a display as primary
        
        Args:
            display_name: Name of the display
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(['xrandr', '--output', display_name, '--primary'],
                         capture_output=True,
                         check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def set_display_position(self, display_name: str, position: str) -> bool:
        """
        Set the position of a display relative to another
        
        Args:
            display_name: Name of the display
            position: Position string (e.g., "--left-of eDP-1", "--right-of eDP-1")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = ['xrandr', '--output', display_name] + position.split()
            subprocess.run(cmd,
                         capture_output=True,
                         check=True)
            return True
        except subprocess.CalledProcessError:
            return False
