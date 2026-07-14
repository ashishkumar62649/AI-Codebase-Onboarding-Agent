"""DeepOrra dashboard [--port] — start the Streamlit dashboard."""

import typer

from deeporra.dashboard.__main__ import main as run_dashboard


def dashboard_cmd(
    port: int = typer.Option(8501, "--port", help="Dashboard port"),
) -> None:
    """Start Streamlit dashboard on localhost."""
    run_dashboard(port=port)
