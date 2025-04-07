import sys
import pyperclip
import time
import threading
import os
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread, QObject  # Import necessary Qt concurrency classes
from pystray import Icon as SysTrayIcon, MenuItem, Menu
from PIL import Image, ImageDraw
import typing 
DEFAULT_FILENAME: str = "clipboard_log.txt"
DEFAULT_SAVE_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_FILENAME)
POLLING_INTERVAL: int = 1  # Seconds

def create_default_icon() -> Image.Image:
    """Creates a simple PIL Image to use as an icon."""
    size = 64
    # Use RGBA for transparency support if needed by the tray backend
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    # Simple blue circle icon
    draw.ellipse((4, 4, size - 4, size - 4), fill=(60, 120, 240, 255), outline =(255, 255, 255, 255), width=3)
    draw.text((size // 2 -10 , size // 2 - 10), "CB", fill=(255, 255, 255, 255), font_size=20) # Basic text
    return image

def load_app_icon() -> QtGui.QIcon:
    """Loads the application icon, falls back to default if file not found."""
    icon_path = "icon.ico" # Or your preferred icon file
    if os.path.exists(icon_path):
         return QtGui.QIcon(icon_path)
    else:
        print(f"Warning: Icon file '{icon_path}' not found. Using default generated icon.")
        # Convert PIL image to QPixmap then to QIcon
        pil_img = create_default_icon()
        # Convert PIL image mode if necessary (e.g., to RGB if saving as JPG/BMP)
        if pil_img.mode != 'RGBA':
            pil_img = pil_img.convert('RGBA')
        img_byte_array = pil_img.tobytes("raw","RGBA")
        qimage = QtGui.QImage(img_byte_array, pil_img.width, pil_img.height, QtGui.QImage.Format_RGBA8888)
        qpixmap = QtGui.QPixmap.fromImage(qimage)
        return QtGui.QIcon(qpixmap)
# --- End Helper Functions ---


class ClipboardMonitor(QObject):
    """
    Runs in a separate thread to monitor clipboard changes
    and emits signals to update the GUI safely.
    """
    content_saved = pyqtSignal(str)  # Signal emitted when content is saved (sends preview)
    error_occurred = pyqtSignal(str) # Signal emitted on error
    status_update = pyqtSignal(str) # Signal for general status updates

    def __init__(self, save_path_func: typing.Callable[[], str], parent=None):
        super().__init__(parent)
        self._running = False
        self.last_content: typing.Optional[str] = None
        self._lock = threading.Lock() # To safely access self._running
        self.get_save_path = save_path_func # Function to get current save path from main App

    def start(self):
        with self._lock:
            if self._running:
                return # Already running
            self._running = True
        print("Clipboard monitor starting...")
        self.status_update.emit("Initializing...")

        # Initialize last_content before starting the loop
        try:
            self.last_content = pyperclip.paste()
        except pyperclip.PyperclipException as e:
            self.error_occurred.emit(f"Initial clipboard access failed: {e}")
            self.last_content = "" # Fallback
        except Exception as e:
            self.error_occurred.emit(f"Unexpected initial clipboard error: {e}")
            self.last_content = "" # Fallback

        self.status_update.emit("Monitoring")


    def stop(self):
        with self._lock:
            if not self._running:
                return # Already stopped
            self._running = False
        print("Clipboard monitor stopping...")
        self.status_update.emit("Stopping...")

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def run(self):
        """The main monitoring loop executed in the QThread."""
        self.start() # Initialize and set state

        while True:
             # Check running flag safely
            if not self.is_running():
                 break # Exit loop if stopped

            try:
                current_content: str = pyperclip.paste()

                # Check if content is new, not empty, and actually different
                if isinstance(current_content, str) and \
                   current_content != self.last_content and \
                   current_content.strip() != "":

                    # Update the last known content
                    self.last_content = current_content

                    # Get current timestamp
                    current_time: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Format the content with timestamp
                    content_to_save: str = f"[{current_time}] {current_content}\n"
                    save_path = self.get_save_path() # Get the path dynamically

                    # Save to file
                    try:
                        with open(save_path, 'a', encoding='utf-8') as file:
                            file.write(content_to_save)
                        # Emit signal with a preview
                        preview = current_content[:50].replace('\n', ' ') + ('...' if len(current_content) > 50 else '')
                        self.content_saved.emit(f"Saved: [{current_time}] {preview}")

                    except IOError as e:
                        self.error_occurred.emit(f"Error writing to file {save_path}: {e}")
                        self.stop() # Stop monitoring on persistent file error
                    except Exception as e:
                        self.error_occurred.emit(f"Unexpected file write error: {e}")
                        # Decide if we should stop or just log and continue

            except pyperclip.PyperclipException as e:
                self.error_occurred.emit(f"Clipboard access error: {e}. Retrying...")
                time.sleep(POLLING_INTERVAL * 3) # Wait longer on clipboard error
            except Exception as e:
                 self.error_occurred.emit(f"Unexpected error in monitor loop: {e}")
                 time.sleep(POLLING_INTERVAL * 2) # Wait a bit

            # Wait before checking again only if running
            if self.is_running():
                time.sleep(POLLING_INTERVAL)

        print("Clipboard monitor loop finished.")
        self.status_update.emit("Idle") # Final status update


class SystemTrayIcon(QObject):
    """ Manages the system tray icon using pystray in a separate thread. """
    exit_signal = pyqtSignal() # Signal to tell the main app to quit

    def __init__(self, app_window: 'App', parent=None):
        super().__init__(parent)
        self.app_window = app_window
        self.icon_image = create_default_icon() # Use the generated PIL image
        self.tray_icon = SysTrayIcon(
            "Clipboard Saver",
            icon=self.icon_image,
            menu=self.create_menu(),
            title="Clipboard Saver"
        )
        self._thread = None

    def create_menu(self) -> Menu:
        return Menu(
            MenuItem("Show Window", self.show_app, default=True),
            MenuItem("Start Monitoring", self.start_monitoring_from_tray, enabled=lambda item: not self.app_window.monitor_thread or not self.app_window.clipboard_monitor.is_running()),
            MenuItem("Stop Monitoring", self.stop_monitoring_from_tray, enabled=lambda item: self.app_window.monitor_thread and self.app_window.clipboard_monitor.is_running()),
            Menu.SEPARATOR,
            MenuItem("Exit", self.exit_app)
        )

    @pyqtSlot()
    def show_app(self):
        self.app_window.showNormal() # Show and bring to front
        self.app_window.activateWindow()

    @pyqtSlot()
    def start_monitoring_from_tray(self):
        # Use QMetaObject.invokeMethod to safely call the slot on the main thread
        QtCore.QMetaObject.invokeMethod(self.app_window, "start_monitoring", QtCore.Qt.QueuedConnection)

    @pyqtSlot()
    def stop_monitoring_from_tray(self):
         # Use QMetaObject.invokeMethod to safely call the slot on the main thread
        QtCore.QMetaObject.invokeMethod(self.app_window, "stop_monitoring", QtCore.Qt.QueuedConnection)

    @pyqtSlot()
    def exit_app(self):
        print("Exit requested from tray icon.")
        self.tray_icon.stop()
        if self._thread:
             self._thread.join(timeout=1) # Wait briefly for tray thread to finish
        self.exit_signal.emit() # Signal the main application to quit

    def run_tray_icon(self):
        """ Runs the pystray icon's event loop. """
        # This function runs in a separate thread
        print("System tray thread started.")
        self.tray_icon.run()
        print("System tray thread finished.") # Should happen after tray_icon.stop()

    def start(self):
        """ Starts the system tray icon in a separate thread. """
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(target=self.run_tray_icon, daemon=True)
            self._thread.start()

    def stop(self):
        """ Stops the system tray icon. """
        if self.tray_icon.visible:
            self.tray_icon.stop()

    def notify(self, message: str, title: str = "Clipboard Saver"):
        """ Shows a tray notification if the icon is running. """
        if self.tray_icon and self.tray_icon.visible:
            self.tray_icon.notify(message, title)

    def update_menu(self):
        """ Updates the tray menu state (e.g., enable/disable start/stop). """
        # Pystray doesn't have a direct 'update menu' function after creation.
        # The enabled lambda functions handle this dynamically when the menu is shown.
        # If more complex updates are needed, recreating the menu might be necessary.
        pass


class App(QtWidgets.QWidget):
    """ Main Application Window """
    def __init__(self):
        super().__init__()
        self.current_save_path: str = DEFAULT_SAVE_PATH
        self.clipboard_monitor = ClipboardMonitor(lambda: self.current_save_path) # Pass function to get path
        self.monitor_thread: typing.Optional[QThread] = None
        self.tray_icon: typing.Optional[SystemTrayIcon] = None
        self.init_ui()
        self.init_monitor()
        self.init_tray_icon()


    def init_ui(self):
        """ Sets up the user interface elements and layout. """
        self.setWindowTitle("Clipboard Saver")
        self.setWindowIcon(load_app_icon())
        # self.setGeometry(100, 100, 400, 250) # Use layouts instead

        # --- Widgets ---
        self.status_label = QtWidgets.QLabel("Status: Idle")
        self.status_label.setStyleSheet("color: gray;")

        self.path_label = QtWidgets.QLabel(f"Saving to:")
        self.path_display = QtWidgets.QLineEdit(self.current_save_path)
        self.path_display.setReadOnly(True) # Display only
        self.browse_button = QtWidgets.QPushButton("Browse...")
        self.browse_button.clicked.connect(self.select_save_path)

        self.start_button = QtWidgets.QPushButton("Start Monitoring")
        self.start_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))
        self.start_button.clicked.connect(self.start_monitoring)

        self.stop_button = QtWidgets.QPushButton("Stop Monitoring")
        self.stop_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaStop))
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.stop_button.setEnabled(False) # Initially disabled

        # --- Layouts ---
        main_layout = QtWidgets.QVBoxLayout(self)

        # Path Selection Layout
        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_display, 1) # Stretch the line edit
        path_layout.addWidget(self.browse_button)

        # Button Layout
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch(1) # Pushes buttons to the left

        # Add widgets and layouts to main layout
        main_layout.addWidget(self.status_label)
        main_layout.addLayout(path_layout)
        main_layout.addLayout(button_layout)
        main_layout.addStretch(1) # Pushes content upwards

        self.setLayout(main_layout)
        self.resize(450, 150) # Set initial size after layout

    def init_monitor(self):
        """ Sets up the signals/slots connection for the monitor. """
        self.clipboard_monitor.content_saved.connect(self.on_content_saved)
        self.clipboard_monitor.error_occurred.connect(self.on_monitor_error)
        self.clipboard_monitor.status_update.connect(self.update_status_label)


    def init_tray_icon(self):
        """ Creates and starts the system tray icon. """
        # Check if systray is supported might be needed for some Linux DEs
        if QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
             self.tray_icon = SystemTrayIcon(self)
             self.tray_icon.exit_signal.connect(self.quit_application)
             self.tray_icon.start() # Run pystray in its thread
             print("System tray icon initiated.")
        else:
            print("Warning: System tray not available on this system.")
            self.tray_icon = None # Ensure it's None if not available


    @pyqtSlot()
    def select_save_path(self):
        """ Opens a dialog to select the save file path. """
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog # Optional: Use Qt's dialog
        new_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Select Save File",
            self.current_save_path, # Start directory
            "Text Files (*.txt);;All Files (*)",
            options=options)

        if new_path:
            self.current_save_path = new_path
            self.path_display.setText(self.current_save_path)
            print(f"Save path set to: {self.current_save_path}")
            # If monitoring, maybe notify the user or restart monitor?
            # For now, it will use the new path on the next save.

    @pyqtSlot()
    def start_monitoring(self):
        """Starts the clipboard monitoring thread."""
        if not self.monitor_thread or not self.monitor_thread.isRunning():
            self.update_status_label("Starting...")
            self.monitor_thread = QThread(self)
            # Move the monitor object to the new thread
            self.clipboard_monitor.moveToThread(self.monitor_thread)
            # Connect the thread's started signal to the monitor's run method
            self.monitor_thread.started.connect(self.clipboard_monitor.run)
            # Clean up thread when finished
            self.monitor_thread.finished.connect(self.monitor_thread.deleteLater)
            # Start the thread's event loop
            self.monitor_thread.start()

            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            if self.tray_icon: self.tray_icon.update_menu()
            print("Monitoring started via GUI.")
        else:
            print("Monitoring already running.")


    @pyqtSlot()
    def stop_monitoring(self):
        """Stops the clipboard monitoring thread."""
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.update_status_label("Stopping...")
            # Signal the monitor object to stop its loop
            # Use invokeMethod for thread-safe call if monitor is in another thread
            QtCore.QMetaObject.invokeMethod(self.clipboard_monitor, "stop", QtCore.Qt.QueuedConnection)

            # Quit the thread's event loop and wait for it to finish
            self.monitor_thread.quit()
            if not self.monitor_thread.wait(2000): # Wait up to 2 seconds
                 print("Warning: Monitor thread did not stop gracefully. Terminating.")
                 self.monitor_thread.terminate() # Force terminate if needed
                 self.monitor_thread.wait() # Wait again after terminate

            self.monitor_thread = None
            self.update_status_label("Idle")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            if self.tray_icon: self.tray_icon.update_menu()
            print("Monitoring stopped via GUI.")

    @pyqtSlot(str)
    def update_status_label(self, status: str):
        """ Updates the status label text and color. """
        self.status_label.setText(f"Status: {status}")
        if "rror" in status.lower():
             self.status_label.setStyleSheet("color: red; font-weight: bold;")
        elif "onitoring" in status.lower() or "aved" in status.lower():
             self.status_label.setStyleSheet("color: green;")
        else:
             self.status_label.setStyleSheet("color: gray;")

    @pyqtSlot(str)
    def on_content_saved(self, message: str):
        """ Slot called when content is saved by the monitor. """
        # For now, just update status. Could show a temporary notification.
        self.update_status_label(message)
        # Example: Show tray notification
        # if self.tray_icon:
        #    self.tray_icon.notify(message)

    @pyqtSlot(str)
    def on_monitor_error(self, error_message: str):
        """ Slot called when the monitor encounters an error. """
        print(f"ERROR: {error_message}")
        self.update_status_label(f"Error: {error_message.split(':')[0]}") # Show concise error
        # Optionally, show a message box for critical errors
        # QtWidgets.QMessageBox.warning(self, "Clipboard Monitor Error", error_message)

    def closeEvent(self, event: QtGui.QCloseEvent):
        """ Overrides the window close event to hide to tray instead. """
        if self.tray_icon and self.tray_icon.tray_icon.visible:
            event.ignore() # Don't close the application
            self.hide()    # Hide the main window
            self.tray_icon.notify("Clipboard Saver is running in the background.")
            print("Window hidden to system tray.")
        else:
            # If no tray icon, perform normal close procedure
            print("No system tray icon running, closing application.")
            self.quit_application()
            event.accept()

    @pyqtSlot()
    def quit_application(self):
        """ Cleans up and quits the entire application. """
        print("Quit application requested.")
        self.stop_monitoring() # Ensure monitor thread is stopped

        if self.tray_icon:
            self.tray_icon.stop() # Stop pystray icon

        print("Exiting application...")
        QtWidgets.QApplication.quit() # Quit the Qt application loop

# --- Main Execution ---
if __name__ == "__main__":
    # Necessary for high-DPI displays
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QtWidgets.QApplication(sys.argv)
    # Important: Prevent Qt from quitting when the last window is hidden (if tray is active)
    app.setQuitOnLastWindowClosed(False)

    window = App()
    window.show()

    sys.exit(app.exec_())
