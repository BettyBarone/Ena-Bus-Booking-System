import os
import webbrowser
import threading
import time
import subprocess
import signal
import socket

# Define the URL to open
DJANGO_URL = "http://127.0.0.1:8000/"

def wait_for_server(host="127.0.0.1", port=8000, timeout=10):
    """Wait until the Django server starts accepting connections."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.5)  # Wait a bit before retrying
    return False

def open_browser():
    """Wait for the server to start and open the browser."""
    if wait_for_server():
        webbrowser.open(DJANGO_URL)
    else:
        print("Warning: Django server did not start within the expected time.")

def run_django_server():
    """Run the Django development server as a separate process."""
    process = subprocess.Popen(["python", "manage.py", "runserver"], stdout=None, stderr=None)

    try:
        while process.poll() is None:  # Keep checking if the process is still running
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Django server...")
        process.send_signal(signal.SIGTERM)
        process.wait()

if __name__ == "__main__":
    # Start the browser in a separate thread AFTER ensuring the server is running
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start the Django server
    run_django_server()
