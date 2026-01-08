import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from qfluentwidgets import setTheme, Theme
from src.gui.main_window import MainWindow
from src.config import cfg

# --- Path Fix ---
# Determine the base path in a way that is robust for both script and bundled app
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # creates a temp folder and stores path in _MEIPASS
    # BUT, we want the path to the executable itself
    application_path = Path(sys.executable).parent
else:
    application_path = Path(__file__).parent

# Set this path in the config object EARLY, before any other part of the app uses it
cfg.set_base_path(application_path)
# --- End Path Fix ---

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        
        # Set theme based on config
        if cfg.theme == "Light":
            setTheme(Theme.LIGHT)
        else:
            setTheme(Theme.DARK)
            
        w = MainWindow()
        w.show()
        
        sys.exit(app.exec())
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
