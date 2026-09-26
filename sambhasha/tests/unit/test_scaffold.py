"""P0.1: the package imports and the `sambhasha` CLI runs."""

from typer.testing import CliRunner

import sambhasha
from sambhasha.cli import app

runner = CliRunner()


def test_package_exposes_its_version() -> None:
    assert sambhasha.__version__ == "0.1.0"


def test_cli_version_prints_the_package_version() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == "sambhasha 0.1.0"


def test_cli_help_names_the_tool_and_its_purpose() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Sambhasha" in result.stdout
    assert "not clinical advice" in result.stdout
