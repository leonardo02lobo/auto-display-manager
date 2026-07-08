"""
Monitor detector - Automatic detection of display connection/disconnection
"""

import threading
from typing import Optional, Callable
from queue import Queue
import time


class MonitorDetector:
    """
    Detects monitor connection/disconnection events
    Uses polling as fallback if udev is not available
    """
    
    def __init__(self, callback: Callable[[bool, Optional[str]], None],
                 poll_interval: float = 2.0):
        """
        Initialize monitor detector
        
        Args:
            callback: Function to call when display change detected
                     Args: (connected: bool, display_name: Optional[str])
            poll_interval: Seconds between polling checks
        """
        self.callback = callback
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_external_count = 0
        self._display_manager = None
        self._event_queue = Queue()
    
    def set_display_manager(self, display_manager) -> None:
        """Set the display manager instance"""
        self._display_manager = display_manager
    
    def start(self) -> None:
        """Start the monitor detection thread"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the monitor detection thread"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
    
    def _detection_loop(self) -> None:
        """Main detection loop"""
        while self._running:
            try:
                if self._display_manager:
                    self._check_displays()
            except Exception as e:
                print(f"Error in detection loop: {e}")
            
            time.sleep(self.poll_interval)
    
    def _check_displays(self) -> None:
        """Check for display changes"""
        external_displays = self._display_manager.get_external_displays()
        current_count = len(external_displays)
        
        if current_count != self._last_external_count:
            if current_count > self._last_external_count:
                # Display connected
                display_name = external_displays[-1].name if external_displays else None
                self._event_queue.put((True, display_name))
            else:
                # Display disconnected - cleanup bspwm desktops
                print("[INFO] Display disconnected, cleaning up bspwm...")
                self._display_manager.xrandr.cleanup_bspwm_desktops()
                self._event_queue.put((False, None))
            
            self._last_external_count = current_count
            
            # Process events
            self._process_events()
    
    def _process_events(self) -> None:
        """Process queued display events"""
        while not self._event_queue.empty():
            connected, display_name = self._event_queue.get()
            try:
                self.callback(connected, display_name)
            except Exception as e:
                print(f"Error in callback: {e}")
