import server_interaction
import window
import threading

if __name__ == '__main__': 
    try:
        print("Starting connection to server...")
        s = threading.Thread(target=server_interaction.open_connection, daemon=True)
        s.start()

        print("Starting window...")
        # window_interaction.load_window()  # Execute in the main thread
        window.load_window()

    except Exception as e:
        print(f"Error : {e}")