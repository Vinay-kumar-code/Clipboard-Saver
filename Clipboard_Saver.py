import pyperclip
import time
import os
from datetime import datetime
import threading

# Define the path of the txt file where clipboard content will be save
FILE_PATH = r'Your absolute path for txt file'


def save_clipboard_content():
    # Get the current clipboard content
    last_content = ""
    
    while True:
        current_content = pyperclip.paste()  # Get clipboard content

        
        if current_content != last_content and current_content != "":
            last_content = current_content  # Update the last content
            
          
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            
            content_to_save = f"[{current_time}] {current_content}\n"
            
          
            with open(FILE_PATH, 'a', encoding='utf-8') as file:
                file.write(content_to_save)
                
            print(f"Saved to file: {content_to_save.strip()}")
        
      
        time.sleep(1)

# Function to run it in the background
def start_clipboard_monitoring():
    print("Starting clipboard monitoring...")
    clipboard_thread = threading.Thread(target=save_clipboard_content, daemon=True)
    clipboard_thread.start()

# Main function to start the process
if __name__ == "__main__":
    start_clipboard_monitoring()
    
    # Keep the script running indefinitely in the background
    try:
        while True:
            time.sleep(10)  # Sleep to keep the main thread running
    except KeyboardInterrupt:
        print("Clipboard monitoring stopped.")
