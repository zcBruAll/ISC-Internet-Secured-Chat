# Import the custom module that handles the server connection.
import server_interaction
# Import the custom module that creates and manages the application window.
import window
# Import threading module to run the server connection concurrently.
import threading

# The following code block will only be executed when this script is run directly,
# and not when it is imported as a module in another script.
if __name__ == '__main__': 
    try:
        # Inform the user that the connection to the server is starting.
        print("Starting connection to server...")
        # Create a new thread that will run the open_connection function from the server_interaction module.
        # The daemon=True flag ensures the thread will not block the program from exiting.
        s = threading.Thread(target=server_interaction.open_connection, daemon=True)
        # Start the server connection thread.
        s.start()

        # Inform the user that the window (UI) is starting.
        print("Starting window...")
        # The window.load_window() function initializes and starts the GUI.
        # This is executed in the main thread because most GUI frameworks require the UI to run on the main thread.
        window.load_window()

    except Exception as e:
        # In case any exception is raised during startup, it will be caught here.
        # The error is printed to the console for debugging purposes.
        print(f"Error : {e}")
