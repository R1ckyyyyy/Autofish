import sys
import os
import cv2
from datetime import datetime
from pathlib import Path

from src.vision import vision
from src.config import cfg

def generate_debug_screenshot(show_image=True):
    """
    Captures screen, draws debug overlays, and saves/shows the image.
    """
    print("Capturing screenshot...")
    screenshot = vision.screenshot()
    
    # CRITICAL FIX: Build the config dict with SCALED coordinates from cfg.get_rect()
    debug_config = {}
    for name in cfg.REGIONS.keys():
        try:
            # This gets the correctly scaled rectangle for the current screen resolution
            debug_config[name] = list(cfg.get_rect(name))
        except Exception as e:
            print(f"Error calculating rect for {name}: {e}")

    print("Drawing debug overlay...")
    # Modify the screenshot in-place using the new vision method
    vision.draw_debug_rects(screenshot, debug_config)
    
    # Draw circles for Jiashi buttons
    jiashi_yes_pos = cfg.get_center_anchored_pos(cfg.BTN_JIASHI_YES)
    jiashi_no_pos = cfg.get_center_anchored_pos(cfg.BTN_JIASHI_NO)
    
    cv2.circle(screenshot, jiashi_yes_pos, 10, (0, 255, 0), 2)  # Green circle for YES
    cv2.putText(screenshot, 'YES', (jiashi_yes_pos[0] + 15, jiashi_yes_pos[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    cv2.circle(screenshot, jiashi_no_pos, 10, (0, 0, 255), 2)   # Red circle for NO
    cv2.putText(screenshot, 'NO', (jiashi_no_pos[0] + 15, jiashi_no_pos[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    # Save the debug image
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Use the centralized config to get the correct base path
    save_dir = cfg._get_base_path() / 'debug_screenshots'
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    filename = f"visual_debug_{timestamp}.png"
    filepath = os.path.join(save_dir, filename)
    
    # Use cv2.imencode to handle potential non-ASCII paths gracefully
    is_success, buffer = cv2.imencode(".png", screenshot)
    if is_success:
        with open(filepath, 'wb') as f:
            f.write(buffer)
        print(f"Debug screenshot saved to: {filepath}")
    else:
        print("Failed to save debug screenshot.")
        return None
    
    if show_image:
        try:
             # Use os.startfile for Windows, which uses the default viewer
             os.startfile(filepath)
        except AttributeError:
             # For non-Windows/Fallback
             import subprocess
             try:
                subprocess.call(['xdg-open', filepath]) # Linux
             except:
                try:
                    subprocess.call(['open', filepath]) # MacOS
                except:
                    # Fallback to OpenCV window if system viewer fails
                    print("Could not open default image viewer. Using OpenCV.")
                    cv2.imshow("Debug Overlay", screenshot)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()

    return filepath

def main():
    print("Starting Debug Overlay...")
    print(f"Screen Resolution: {cfg.screen_width}x{cfg.screen_height}")
    generate_debug_screenshot(show_image=True)

if __name__ == "__main__":
    main()
