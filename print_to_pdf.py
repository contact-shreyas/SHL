#!/usr/bin/env python3
"""Serve HTML and print to PDF via browser."""

import http.server
import socketserver
import threading
import time
import subprocess
from pathlib import Path

PORT = 8888
HANDLER = http.server.SimpleHTTPRequestHandler

# Start server in background thread
def run_server():
    try:
        with socketserver.TCPServer(("", PORT), HANDLER) as httpd:
            print(f"Server running at http://localhost:{PORT}")
            httpd.serve_forever()
    except:
        pass

# Start server
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
time.sleep(1)

# Try to open in browser
url = f"http://localhost:{PORT}/approach_document.html"

print(f"Opening {url}")
try:
    # Try common browsers
    for browser in ["chrome", "firefox", "msedge"]:
        try:
            subprocess.Popen([browser, f"--app={url}"])
            print(f"Opened in {browser}")
            break
        except:
            continue
    else:
        import webbrowser
        webbrowser.open(url)
        print("Opened in default browser")
except Exception as e:
    print(f"Error: {e}")

print("\nInstructions:")
print("1. When browser opens, press Ctrl+P")
print("2. Select 'Save as PDF'")
print("3. Save as: approach_document.pdf")
print("4. Close this window after saving")

# Keep server running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nServer stopped.")
