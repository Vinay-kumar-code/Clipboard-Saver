Clipboard Saver
This project includes two variations of a Clipboard Saver tool:

Console-Based Clipboard Saver
This version runs in the terminal, monitors the clipboard, and saves copied text to a text file in real time.

GUI-Based Clipboard Saver
This version includes a graphical user interface (GUI) for easy interaction, allowing users to configure settings like save location and enable/disable features.

Features
Current Features:
Clipboard Monitoring: Continuously monitors clipboard content and saves any copied text to a specified text file.
Timestamped Entries: Each copied text is saved with a timestamp for future reference.
Indefinite Operation: Runs indefinitely until manually stopped via the terminal or GUI.
Standalone Variations: Includes both a terminal-based and GUI-based version.
Planned Features:
Single Executable File
Package the application as a standalone executable that runs without requiring Python or terminal windows.
Image Copying
Option to copy images and save them to a designated folder.
Filename and Path Saving
Option to copy filenames and their full paths, storing them in a separate text file.
Enhanced GUI Options
Allow users to configure settings, including enabling/disabling specific features like image copying or file path saving.
Automatic Startup
Add the application as a Windows Task Manager service for automatic startup.
How to Use
Terminal-Based Version
Run the script from the terminal.
Copied text will automatically be saved to the specified text file in the same directory.
To stop the script, close the terminal window or press Ctrl+C.
GUI-Based Version
Launch the GUI version by running the corresponding script.
Use the application to:
Set the save location for text or images.
Enable or disable features via settings.
View clipboard history.
Close the application to stop monitoring the clipboard.
Future Enhancements
To improve usability, these features are planned for future updates:

Convert the application into a single executable file using tools like PyInstaller.
Add support for clipboard images and saving them to folders.
Include an option to copy filenames and paths and save them in separate files.
Enhance the GUI to allow seamless toggling of features.
Automatically start the application at system startup by creating a Windows service.
