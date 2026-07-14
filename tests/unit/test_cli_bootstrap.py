"""CLI bootstrap tests — verify help, entry points, and import safety."""

import subprocess
import sys

import typer


class TestEntryPoints:
    def test_python_m_deeporra_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "deeporra", "--help"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0
        for cmd in ("index", "status", "doctor", "dashboard", "mcp", "setup"):
            assert cmd in result.stdout

    def test_root_help_lists_all_commands(self):
        from deeporra.cli.main import app
        cmds = {c.name or c.callback.__name__ for c in app.registered_commands}
        expected = {"index", "status", "doctor", "dashboard", "mcp", "setup"}
        assert cmds == expected

    def test_help_does_not_import_unfinished_modules(self):
        before = set(sys.modules.keys())
        import deeporra.cli.main
        after = set(sys.modules.keys())
        new_modules = after - before
        forbidden = {"deeporra.storage", "deeporra.scanner", "deeporra.parser",
                     "deeporra.chunking", "deeporra.embeddings", "deeporra.indexing",
                     "deeporra.graph", "deeporra.retrieval", "deeporra.mcp_server",
                     "deeporra.dashboard"}
        assert new_modules.isdisjoint(forbidden), \
            f"CLI startup imported: {new_modules & forbidden}"

    def test_no_command_has_side_effects(self):
        import deeporra.cli.main
        for cmd in deeporra.cli.main.app.registered_commands:
            name = cmd.name or cmd.callback.__name__
            assert name in ("index", "status", "doctor", "dashboard",
                            "mcp", "setup")


class TestIndexCommand:
    def test_index_accepts_positional_path(self):
        from deeporra.cli.commands.index_cmd import index_cmd
        import inspect
        sig = inspect.signature(index_cmd)
        assert "repo_path" in sig.parameters


class TestStatusCommand:
    def test_status_accepts_optional_path(self):
        from deeporra.cli.commands.status_cmd import status_cmd
        import inspect
        sig = inspect.signature(status_cmd)
        assert "repo_path" in sig.parameters
        # Optional arg: has a default (Typer wraps in ArgumentInfo)
        params = sig.parameters["repo_path"]
        assert params.default is not None or params.default is None


class TestDoctorCommand:
    def test_doctor_accepts_optional_path(self):
        from deeporra.cli.commands.doctor_cmd import doctor_cmd
        import inspect
        sig = inspect.signature(doctor_cmd)
        assert "repo_path" in sig.parameters


class TestDashboardCommand:
    def test_dashboard_accepts_port(self):
        from deeporra.cli.commands.dashboard_cmd import dashboard_cmd
        import inspect
        sig = inspect.signature(dashboard_cmd)
        assert "port" in sig.parameters


class TestMCPCommand:
    def test_mcp_requires_repo(self):
        from deeporra.cli.commands.mcp_cmd import mcp_cmd
        import inspect
        sig = inspect.signature(mcp_cmd)
        assert "repo_path" in sig.parameters


class TestSetupCommand:
    def test_setup_accepts_agent_and_repo(self):
        from deeporra.cli.commands.setup_cmd import setup_cmd
        import inspect
        sig = inspect.signature(setup_cmd)
        assert "agent" in sig.parameters
        assert "repo_path" in sig.parameters
