"""Entry point for `python -m deeporra.dashboard`."""

import sys
from pathlib import Path

from streamlit.web import cli as st_cli


def main(port: int | None = None) -> None:
    app_path = Path(__file__).resolve().parent / "app.py"
    argv = ["streamlit", "run", str(app_path)]
    if port is not None:
        argv.extend(["--server.port", str(port)])
    sys.argv = argv
    sys.exit(st_cli.main())


if __name__ == "__main__":
    main()
