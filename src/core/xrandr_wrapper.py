"""
Wrapper for xrandr commands to manage displays
"""

import subprocess
import re
import time
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
    
    def generate_modeline(self, resolution: str, refresh_rate: float = 60.0) -> Optional[Tuple[str, str]]:
        """
        Generate a modeline for a given resolution using cvt
        
        Args:
            resolution: Resolution string (e.g., "1920x1080")
            refresh_rate: Desired refresh rate
            
        Returns:
            Tuple of (mode_name, modeline_params) or None if failed
        """
        try:
            width, height = resolution.split('x')
            result = subprocess.run(
                ['cvt', width, height, str(refresh_rate)],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the Modeline output
            # Example: Modeline "1920x1080_60.00"  173.00  1920 2048 2248 2576  1080 1083 1088 1120 -hsync +vsync
            match = re.search(r'Modeline\s+"([^"]+)"\s+(.+)', result.stdout)
            if match:
                mode_name = match.group(1)
                modeline_params = match.group(2).strip()
                return (mode_name, modeline_params)
            return None
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            return None
    
    def add_custom_mode(self, mode_name: str, modeline_params: str) -> bool:
        """
        Add a custom mode to the X server using xrandr --newmode
        
        Args:
            mode_name: Name of the mode (e.g., "1920x1080_60.00")
            modeline_params: Modeline parameters from cvt
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cmd = ['xrandr', '--newmode', mode_name] + modeline_params.split()
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def attach_mode_to_output(self, display_name: str, mode_name: str) -> bool:
        """
        Attach a custom mode to a specific output using xrandr --addmode
        
        Args:
            display_name: Name of the display
            mode_name: Name of the mode to attach
            
        Returns:
            True if successful, False otherwise
        """
        try:
            subprocess.run(
                ['xrandr', '--addmode', display_name, mode_name],
                capture_output=True,
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False
    
    def force_resolution(self, display_name: str, resolution: str) -> bool:
        """
        Force a resolution on a display by creating a custom mode if needed.
        This bypasses EDID limitations reported by the monitor.
        
        Args:
            display_name: Name of the display
            resolution: Desired resolution (e.g., "1920x1080")
            
        Returns:
            True if successful, False otherwise
        """
        # First try setting the mode directly (in case it already exists)
        if self.set_display_mode(display_name, resolution):
            return True
        
        # Generate a custom modeline
        mode_data = self.generate_modeline(resolution)
        if not mode_data:
            print(f"[ERROR] Failed to generate modeline for {resolution}")
            return False
        
        mode_name, modeline_params = mode_data
        print(f"[INFO] Generated custom mode: {mode_name}")
        
        # Add the mode to the X server (ignore error if already exists)
        self.add_custom_mode(mode_name, modeline_params)
        
        # Attach the mode to the output
        if not self.attach_mode_to_output(display_name, mode_name):
            print(f"[WARNING] Failed to attach mode {mode_name} to {display_name} (may already be attached)")
        
        # Try to set the mode
        if self.set_display_mode(display_name, mode_name):
            print(f"[INFO] Successfully forced resolution {resolution} on {display_name}")
            return True
        
        print(f"[ERROR] Failed to set custom mode {mode_name} on {display_name}")
        return False
    
    def cleanup_bspwm_desktops(self) -> bool:
        """
        Remove bspwm monitors/desktops for disconnected displays.
        This fixes the issue where bspwm keeps workspaces for disconnected monitors.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if bspc is available
            subprocess.run(['which', 'bspc'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("[INFO] bspc not found, skipping bspwm cleanup")
            return True
        
        try:
            # Get list of bspwm monitors
            result = subprocess.run(
                ['bspc', 'query', '-M', '--names'],
                capture_output=True,
                text=True,
                check=True
            )
            bspwm_monitors = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # Get list of connected xrandr outputs
            xrandr_result = subprocess.run(['xrandr'], capture_output=True, text=True, check=True)
            connected_outputs = []
            for line in xrandr_result.stdout.split('\n'):
                if 'connected' in line:
                    match = re.match(r'^(\S+)\s+connected', line)
                    if match:
                        connected_outputs.append(match.group(1))
            
            print(f"[INFO] bspwm monitors: {bspwm_monitors}")
            print(f"[INFO] Connected xrandr outputs: {connected_outputs}")
            
            # Remove bspwm monitors that don't have a connected xrandr output
            for bspwm_monitor in bspwm_monitors:
                if bspwm_monitor not in connected_outputs:
                    print(f"[INFO] Removing bspwm monitor: {bspwm_monitor}")
                    subprocess.run(
                        ['bspc', 'monitor', bspwm_monitor, '-r'],
                        capture_output=True
                    )
            
            # Restart polybar to refresh workspaces
            print("[INFO] Restarting polybar...")
            try:
                subprocess.run(['polybar-msg', 'cmd', 'restart'], capture_output=True, timeout=5)
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                # Fallback: kill and restart polybar
                try:
                    subprocess.run(['pkill', 'polybar'], capture_output=True)
                    time.sleep(0.5)
                    subprocess.run(['polybar', 'main'], capture_output=True, start_new_session=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    print("[WARNING] Failed to restart polybar")
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] Failed to cleanup bspwm: {e}")
            return False
