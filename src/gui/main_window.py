import sys
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentIcon, FluentWindow, NavigationItemPosition, setTheme, Theme

from src.gui.home_interface import HomeInterface
from src.gui.records_interface import RecordsInterface
from src.gui.settings_interface import SettingsInterface
from src.gui.overlay_window import OverlayWindow
from src.workers import FishingWorker, PopupWorker
from src.inputs import InputController


class MainWindow(FluentWindow):

    preset_should_change = Signal(str)

    def nativeEvent(self, event_type, message):
        """
        Override the native event handler to gracefully handle KeyboardInterrupts
        that might be raised by underlying libraries (like pynput) interacting
        with the Qt event loop.
        """
        try:
            # Pass the event to the parent class's handler
            return super().nativeEvent(event_type, message)
        except KeyboardInterrupt:
            # This is a workaround for an issue where pynput's listener can
            # cause a KeyboardInterrupt in the main thread when a hotkey is pressed.
            # We catch it here to prevent it from crashing the application or printing
            # an error to the console, and simply ignore it.
            print("DEBUG: Caught and ignored KeyboardInterrupt in nativeEvent.")
            return True, 0 # Indicate that the event has been handled

    def __init__(self):
        super().__init__()
        print("Initializing MainWindow UI...")
        self.setObjectName("MainWindow")
        self.setWindowTitle("AutoFish")
        self.setWindowIcon(FluentIcon.GAME.icon())
        self.resize(800, 600)

        print("Instantiating interfaces...")
        self.home_interface = HomeInterface(self)
        self.records_interface = RecordsInterface(self)
        self.settings_interface = SettingsInterface(self)
 
        self.overlay = OverlayWindow()

        print("Instantiating worker and input controller...")
        self.worker = FishingWorker()
        self.popup_worker = PopupWorker()
        self.input_controller = InputController()

        print("Setting up navigation...")
        # 添加导航
        self.addSubInterface(self.home_interface, FluentIcon.HOME, "主页")
        self.addSubInterface(self.records_interface, FluentIcon.LIBRARY, "记录")
        self.addSubInterface(self.settings_interface, FluentIcon.SETTING, "设置", NavigationItemPosition.BOTTOM)

        print("Connecting signals...")
        self.worker.log_updated.connect(self.append_log)
        self.worker.status_updated.connect(self.update_status)
        self.worker.record_added.connect(self.records_interface.add_record)
        self.worker.record_added.connect(self.home_interface.update_catch_info)
        self.worker.record_added.connect(self.home_interface.add_record_to_session_table)
        self.popup_worker.log_updated.connect(self.append_log)
        self.input_controller.toggle_script_signal.connect(self.toggle_script)
        self.input_controller.debug_screenshot_signal.connect(self.take_debug_screenshot)
        self.settings_interface.hotkey_changed_signal.connect(self.home_interface.update_hotkey_display)
        self.settings_interface.debug_hotkey_changed_signal.connect(self.home_interface.update_debug_hotkey_display)
        self.settings_interface.hotkey_changed_signal.connect(self.input_controller._update_hotkey_handler)
        self.settings_interface.debug_hotkey_changed_signal.connect(self.input_controller._update_debug_hotkey_handler)
        self.home_interface.preset_changed_signal.connect(self.on_preset_changed)
        self.settings_interface.theme_changed_signal.connect(self._on_theme_changed)
        self.preset_should_change.connect(self.worker.update_preset)
        self.home_interface.toggle_overlay_signal.connect(self.toggle_overlay)
        
        # Overlay signals
        self.worker.status_updated.connect(self.overlay.update_status)
        self.worker.record_added.connect(lambda: self.overlay.update_fish_count(self.home_interface.total_catch))

        # Start the worker thread, but it will be initially paused
        self.worker.start()
        self.popup_worker.start()

        # Start listening for hotkeys
        self.input_controller.start_listening()

    def toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()

    def _on_theme_changed(self, theme: str):
        if theme == "Light":
            setTheme(Theme.LIGHT)
        else:
            setTheme(Theme.DARK)
        
        # 主题切换后刷新记录和主页，以更新颜色
        if hasattr(self.records_interface, 'refresh_table_colors'):
            self.records_interface.refresh_table_colors()
            
        if hasattr(self.home_interface, 'refresh_table_colors'):
            self.home_interface.refresh_table_colors()

    def append_log(self, message):
        """在日志窗口追加日志"""
        self.home_interface.update_log(message)

    def update_status(self, status):
        """更新状态标签"""
        self.home_interface.update_status(status)

    def toggle_script(self):
        """切换脚本的运行/暂停状态"""
        if self.worker.paused:
            self.worker.resume()
        else:
            self.worker.pause()
            
    def take_debug_screenshot(self):
        """Taking debug screenshot and opening it"""
        print("Taking debug screenshot via hotkey...")
        try:
            # Dynamically import the generation function to avoid circular dependencies
            # and to keep GUI code clean from direct tool logic.
            import sys
            import os
            
            # Since this file is in src/gui, we go up two levels for the root.
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            tools_path = os.path.join(project_root, 'tools')
            
            if tools_path not in sys.path:
                sys.path.append(tools_path)
            
            # Now we can import from the tools directory
            from debug_overlay import generate_debug_screenshot
            
            filepath = generate_debug_screenshot(show_image=True)
            self.append_log(f"调试截图已保存: {filepath}")
            self.update_status("调试截图已生成")
            
        except Exception as e:
            print(f"Failed to take debug screenshot: {e}")
            self.append_log(f"截图失败: {e}")

    def on_preset_changed(self, preset_name: str):
        """
        当UI中的预设改变时，通过信号安全地通知工作线程。
        """
        self.append_log(f"UI请求更改预设为: {preset_name}")

        # 发射信号，将预设名称传递给工作线程
        self.preset_should_change.emit(preset_name)

        # 切换预设后，为安全起见，强制暂停脚本
        # 这可以防止在新配置加载期间发生意外行为
        if not self.worker.paused:
            self.worker.pause()
            
        self.update_status(f"预设已切换为 '{preset_name}'，脚本已暂停。")
        self.append_log("请检查配置，然后按快捷键继续。")

    def closeEvent(self, event):
        """关闭窗口事件"""
        print("Closing application, stopping threads...")
        self.worker.stop()
        self.popup_worker.stop()
        
        # Wait for threads to finish with a timeout to avoid freezing
        if not self.worker.wait(2000):
            print("Worker thread did not stop in time, terminating...")
            self.worker.terminate()
            
        if not self.popup_worker.wait(2000):
            print("Popup worker thread did not stop in time, terminating...")
            self.popup_worker.terminate()
        
        self.input_controller.stop_listening()
        print("All threads stopped. Goodbye.")
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
