from __future__ import annotations

import threading
import webbrowser

from app import app


HOST = "127.0.0.1"
PORT = 8039
URL = f"http://{HOST}:{PORT}"


def open_browser() -> None:
    """Abre automáticamente la HMI cuando el servidor esté listo."""
    webbrowser.open_new(URL)


def main() -> None:
    threading.Timer(1.5, open_browser).start()

    app.run(
        host=HOST,
        port=PORT,
        debug=True,
        use_reloader=False,
    )


if __name__ == "__main__":
    main()