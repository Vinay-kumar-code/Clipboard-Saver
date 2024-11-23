# Clipboard Saver

This project includes two variations of a **Clipboard Saver** tool:

1. **Console-Based Clipboard Saver**  
   This version runs in the terminal, monitors the clipboard, and saves copied text to a text file in real time.

2. **GUI-Based Clipboard Saver**  
   This version includes a graphical user interface (GUI) for easy interaction, allowing users to configure settings like save location and enable/disable features.

---

## Features

### Current Features:
- **Clipboard Monitoring**: Continuously monitors clipboard content and saves any copied text to a specified text file. 
- **Timestamped Entries**: Each copied text is saved with a timestamp for future reference.
- **Indefinite Operation**: Runs indefinitely until manually stopped via the terminal or GUI.
- **Standalone Variations**: Includes both a terminal-based and GUI-based version.

### Planned Features:
1. **Single Executable File**  
   - Package the application as a standalone executable that runs without requiring Python or terminal windows.
2. **Image Copying**  
   - Option to copy images and save them to a designated folder.
3. **Filename and Path Saving**  
   - Option to copy filenames and their full paths, storing them in a separate text file.
4. **Enhanced GUI Options**  
   - Allow users to configure settings, including enabling/disabling specific features like image copying or file path saving.
5. **Automatic Startup**  
   - Add the application as a Windows Task Manager service for automatic startup.

---

## How to Use

### Terminal-Based Version
1. Run the script from the terminal.
2. Copied text will automatically be saved to the specified text file in the same directory.
3. To stop the script, close the terminal window or press `Ctrl+C`.

### GUI-Based Version
1. Launch the GUI version by running the corresponding script.
2. Use the application to:
   - Set the save location for text or images.
   - Enable or disable features via settings.
   - View clipboard history.
3. Close the application to stop monitoring the clipboard.

---

