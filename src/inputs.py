import ctypes
import time
import random
from pynput import mouse, keyboard
from PySide6.QtCore import QObject, Signal
from src.config import cfg

# Constants for mouse_event
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

class InputController(QObject):
    toggle_script_signal = Signal()
    debug_screenshot_signal = Signal() # Signal for debug screenshot

    def __init__(self):
        super().__init__()
        self.running = False
        self.mouse_listener = None
        self.keyboard_listener = None
        self._hotkey_handler = None
        self._debug_hotkey_handler = None # Handler for F10
        self.is_mouse_down = False
        self._update_hotkey_handler()
        self._update_debug_hotkey_handler()

    def _parse_hotkey_string(self, hotkey_string):
        """Helper function to parse a hotkey string into pynput format."""
        raw = hotkey_string.lower()
        parts = raw.split('+')
        formatted_parts = []
        
        special_keys = {
            'ctrl', 'alt', 'shift', 'win', 'cmd',
            'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
            'space', 'tab', 'enter', 'esc', 'backspace', 'delete', 'insert', 
            'home', 'end', 'pgup', 'pgdn', 'up', 'down', 'left', 'right'
        }
        
        for p in parts:
            p = p.strip()
            if p in special_keys:
                formatted_parts.append(f"<{p}>")
            else:
                formatted_parts.append(p)
        
        return "+".join(formatted_parts)

    def _update_hotkey_handler(self):
        """
        Parses the main hotkey from config and creates a pynput HotKey handler.
        """
        try:
            formatted_hotkey = self._parse_hotkey_string(cfg.hotkey)
            self._hotkey_handler = keyboard.HotKey(
                keyboard.HotKey.parse(formatted_hotkey),
                self.toggle_script_signal.emit
            )
        except Exception as e:
            print(f"Error parsing hotkey '{cfg.hotkey}': {e}")
            self._hotkey_handler = None
            
    def _update_debug_hotkey_handler(self):
        """
        Parses the debug hotkey from config and creates a pynput HotKey handler.
        """
        try:
            formatted_hotkey = self._parse_hotkey_string(cfg.global_settings.get("debug_hotkey", "F10"))
            self._debug_hotkey_handler = keyboard.HotKey(
                keyboard.HotKey.parse(formatted_hotkey),
                self.debug_screenshot_signal.emit
            )
        except Exception as e:
            print(f"Error parsing debug hotkey '{cfg.global_settings.get('debug_hotkey')}': {e}")
            self._debug_hotkey_handler = None

    def add_jitter(self, base_time):
        jitter_range = cfg.jitter_range
        if jitter_range <= 0:
            return base_time
        
        multiplier = random.uniform(1 - jitter_range / 100, 1 + jitter_range / 100)
        jittered_time = round(base_time * multiplier, 3)
        
        return max(0.01, jittered_time)

    @staticmethod
    def press_key(key_name):
        """
        Simulates pressing and releasing a key using virtual key codes.
        """
        key_name = key_name.upper()
        # Common virtual key codes
        vk_map = {
            'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73,
            'E': 0x45, 'R': 0x52, 'SPACE': 0x20
        }
        vk = vk_map.get(key_name)
        if vk:
            ctypes.windll.user32.keybd_event(vk, 0, 0, 0) # Key Down
            time.sleep(random.uniform(0.05, 0.1))
            ctypes.windll.user32.keybd_event(vk, 0, 2, 0) # Key Up
        else:
            print(f"Unknown key for simulation: {key_name}")

    @staticmethod
    def jitter_click(x, y):
        """
        Simulates a more human-like mouse click with random delay.
        """
        ctypes.windll.user32.SetCursorPos(x, y)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(random.uniform(0.05, 0.12))
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def click(self, x, y):
        """
        Simulates a left mouse click at the given coordinates.
        """
        self.jitter_click(x, y)

    def press_mouse_button(self):
        """Simulates pressing the left mouse button down without releasing."""
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        self.is_mouse_down = True

    def release_mouse_button(self):
        """Simulates releasing the left mouse button."""
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        self.is_mouse_down = False

    def hold_mouse(self, duration):
        """
        Simulates holding the left mouse button for a specified duration.
        """
        actual_duration = self.add_jitter(duration)
        self.press_mouse_button()
        time.sleep(actual_duration)
        self.release_mouse_button()

    def left_click(self):
        """
        Simulates a left mouse click.
        """
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        self.is_mouse_down = True
        time.sleep(0.1)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        self.is_mouse_down = False

    def ensure_mouse_up(self):
        """
        Ensures the left mouse button is released if it's currently held down.
        """
        if self.is_mouse_down:
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            self.is_mouse_down = False

    def _on_press(self, key):
        """
        Callback for keyboard press events.
        """
        if self._hotkey_handler:
            try:
                self._hotkey_handler.press(self.keyboard_listener.canonical(key))
            except Exception:
                pass
        
        if self._debug_hotkey_handler:
            try:
                self._debug_hotkey_handler.press(self.keyboard_listener.canonical(key))
            except Exception:
                pass

    def _on_release(self, key):
        """
        Callback for keyboard release events.
        """
        if self._hotkey_handler:
            try:
                self._hotkey_handler.release(self.keyboard_listener.canonical(key))
            except Exception:
                pass
                
        if self._debug_hotkey_handler:
            try:
                self._debug_hotkey_handler.release(self.keyboard_listener.canonical(key))
            except Exception:
                pass

    def _on_click(self, x, y, button, pressed):
        """
        Callback for mouse click events.
        """
        if (button == mouse.Button.x1 or button == mouse.Button.x2) and pressed:
            self.toggle_script_signal.emit()

    def start_listening(self):
        """
        Starts the mouse and keyboard listeners.
        """
        if self.running:
            return
            
        self._update_hotkey_handler() # Ensure latest config
        self._update_debug_hotkey_handler()
        self.running = True
        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def stop_listening(self):
        """
        Stops the mouse and keyboard listeners.
        """
        if not self.running:
            return

        self.running = False
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None
