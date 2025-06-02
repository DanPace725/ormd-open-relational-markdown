import webbrowser
import threading
import http.server
import socketserver
import tempfile
import socket
import os
import click
from pathlib import Path
from .utils import SYMBOLS

def _serve_and_open(html_content, port, no_browser, file_path, title):
    """Start local server and optionally open browser"""

    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_html_path = f.name

    # Find available port if not specified
    if port == 0:
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()

    # Custom HTTP handler to serve our temporary file
    class ORMDHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=Path(temp_html_path).parent, **kwargs)

        def log_message(self, format, *args):
            # Suppress HTTP logs for cleaner output
            return

    try:
        # Use a simpler approach with better interrupt handling
        httpd = http.server.HTTPServer(("", port), ORMDHandler)
        httpd.timeout = 0.5  # Short timeout for responsiveness

        url = f"http://localhost:{port}/{Path(temp_html_path).name}"

        click.echo(f"{SYMBOLS['success']} Opening '{title}' in browser")
        click.echo(f"{SYMBOLS['info']} Server running at {url}")
        click.echo(f"{SYMBOLS['info']} Press Ctrl+C to stop")

        if not no_browser:
            # Open browser after short delay to ensure server is ready
            threading.Timer(1.0, lambda: webbrowser.open(url)).start()

        # Simple serving loop that's easier to interrupt
        try:
            while True:
                httpd.handle_request()
        except KeyboardInterrupt:
            click.echo(f"\n{SYMBOLS['info']} Stopping server...")
        finally:
            httpd.server_close()

    except OSError as e:
        if "Address already in use" in str(e):
            click.echo(f"{SYMBOLS['error']} Port {port} is already in use. Try a different port with --port")
        else:
            click.echo(f"{SYMBOLS['error']} Failed to start server: {str(e)}")
        exit(1) # Consider if exit is appropriate here or if exception should bubble up
    finally:
        # Cleanup temporary file
        try:
            os.unlink(temp_html_path)
        except:
            pass
