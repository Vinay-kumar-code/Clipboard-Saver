

import pyperclip
import time
import os
from datetime import datetime
import threading
from typing import Optional 


DEFAULT_FILENAME: str = "clipboard_log.txt"

FILE_PATH: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_FILENAME)
POLLING_INTERVAL: int = 1

last_content: Optional[str] = None

def save_clipboard_content() -> None:
    """
    Monitors the clipboard and saves new text content to the log file.
    Runs in an infinite loop until the program is terminated.
    """
    global last_content # Use the global variable to track state across checks

    print(f"Monitoring clipboard. Saving changes to: {FILE_PATH}")
    try:
        last_content = pyperclip.paste()
    except pyperclip.PyperclipException as e:
        print(f"Error accessing clipboard on startup: {e}")
  
        last_content = ""
    except Exception as e:
     
        print(f"Unexpected error accessing clipboard on startup: {e}")
        last_content = ""


    while True:
        try:
            current_content: str = pyperclip.paste()

        
            if isinstance(current_content, str) and \
               current_content != last_content and \
               current_content.strip() != "": # Check if not just whitespace

             
                last_content = current_content

          
                current_time: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            
                content_to_save: str = f"[{current_time}] {current_content}\n"

      
                try:
                    with open(FILE_PATH, 'a', encoding='utf-8') as file:
                        file.write(content_to_save)
                  
                    print(f"Saved: [{current_time}] {current_content[:50]}...") # Show preview

                except IOError as e:
                    print(f"Error writing to file {FILE_PATH}: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred during file write: {e}")

        except pyperclip.PyperclipException as e:
      
            print(f"Error accessing clipboard: {e}. Retrying...")
           
            time.sleep(POLLING_INTERVAL * 5) # Wait longer if clipboard access fails
        except Exception as e:
       
             print(f"An unexpected error occurred during clipboard check: {e}. Retrying...")
             time.sleep(POLLING_INTERVAL * 2) 

        time.sleep(POLLING_INTERVAL)

def start_clipboard_monitoring() -> None:
    """
    Starts the clipboard monitoring function in a separate daemon thread.
    """
    print("Starting clipboard monitoring thread...")
   
    clipboard_thread = threading.Thread(target=save_clipboard_content, daemon=True)
    clipboard_thread.start()
    print("Clipboard monitoring started in the background.")


if __name__ == "__main__":
    start_clipboard_monitoring()

  
    print("Press Ctrl+C to stop monitoring.")
    try:
        while True:
         
            time.sleep(60) # Sleep for a longer time, doesn't affect polling interval
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Stopping clipboard monitoring.")
    except Exception as e:
        print(f"\nAn unexpected error occurred in the main loop: {e}")
    finally:
        print("Exiting application.")
