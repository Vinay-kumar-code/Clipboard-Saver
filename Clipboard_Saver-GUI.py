import sys
import pyperclip
import time
import threading
import os
from datetime import datetime
from PyQt5 import QtWidgets, QtGui
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import ctypes

# Path to save clipboard content
FILE_PATH = r'Your .txt file path'

class ClipboardMonitor:
    def __init__(self):
        self.running = False
        self.last_content = ""
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.monitor_clipboard, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def monitor_clipboard(self):
        while self.running:
            current_content = pyperclip.paste()
            if current_content != self.last_content and current_content != "":
                self.last_content = current_content
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                content_to_save = f"[{current_time}] {current_content}\n"
                with open(FILE_PATH, 'a', encoding='utf-8') as file:
                    file.write(content_to_save)
            time.sleep(1)

class App(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.monitor = ClipboardMonitor()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Clipboard Saver")
        self.setGeometry(100, 100, 300, 150)
        self.setWindowIcon(QtGui.QIcon("icon.ico"))

        self.start_button = QtWidgets.QPushButton("Start Monitoring", self)
        self.start_button.setGeometry(50, 30, 200, 40)
        self.start_button.clicked.connect(self.start_monitoring)

        self.stop_button = QtWidgets.QPushButton("Stop Monitoring", self)
        self.stop_button.setGeometry(50, 90, 200, 40)
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False)

        self.tray_icon = SystemTray(self)
        self.tray_icon.show()

    def start_monitoring(self):
        self.monitor.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_monitoring(self):
        self.monitor.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.show_message("Clipboard Saver is running in the background.")

# Define system tray functionality
class SystemTray:
    def __init__(self, app):
        self.app = app
        self.icon = self.create_icon()
        self.tray = Icon("Clipboard Saver", self.icon, menu=self.create_menu())

    def create_icon(self):
        size = 64
        image = Image.new("RGB", (size, size), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, size, size), fill=(0, 0, 255))
        return image

    def create_menu(self):
        return Menu(
            MenuItem("Show", self.show_app),
            MenuItem("Exit", self.exit_app)
        )

    def show_app(self):
        self.app.show()

    def exit_app(self):
        self.app.monitor.stop()
        self.tray.stop()
        QtWidgets.QApplication.quit()

    def show_message(self, message):
        ctypes.windll.user32.MessageBoxW(0, message, "Clipboard Saver", 1)

    def show(self):
        self.tray.run()

# Main function
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
