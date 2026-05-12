from __future__ import annotations

import socket
import threading
import time
import webbrowser

from app import app


def find_free_port(start: int = 8050) -> int:
    for port in range(start, start + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError("No free local port found.")


def open_browser_later(url: str) -> None:
    def worker() -> None:
        time.sleep(1.2)
        webbrowser.open(url)

    threading.Thread(target=worker, daemon=True).start()


def main() -> None:
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"
    print(f"SciencePlots Chart Builder is running at {url}")
    open_browser_later(url)
    app.run(debug=False, host="127.0.0.1", port=port)


if __name__ == "__main__":
    main()
