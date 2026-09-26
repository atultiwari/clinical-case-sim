"""The `sambhasha` command line (SPEC §17). Later tasks add `case`, `run`, `transcript` and more."""

import typer

from sambhasha import __version__

app = typer.Typer(
    help=(
        "Sambhasha: AI and human doctor seats work up hidden, published case reports. "
        "An educational research tool: its output is not clinical advice."
    ),
    no_args_is_help=True,
)


@app.callback()
def main() -> None:
    """Keep subcommands explicit, even while there is only one."""


@app.command()
def version() -> None:
    """Print the installed Sambhasha version."""
    typer.echo(f"sambhasha {__version__}")
