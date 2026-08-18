from __future__ import annotations

import os
import threading
import webbrowser

from app import app

HOST = os.getenv("TRADELATIN_HOST", "127.0.0.1")
PORT = int(os.getenv("TRADELATIN_PORT", "8002"))
URL = f"http://{HOST}:{PORT}/prices?lang=en"


def open_browser() -> None:
    webbrowser.open_new(URL)


def main() -> None:
    threading.Timer(1.5, open_browser).start()
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
