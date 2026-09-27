"""The `sambhasha` command line (SPEC §17). Later tasks add `run`, `transcript` and more."""

from pathlib import Path
from typing import Annotated

import typer

from sambhasha import __version__
from sambhasha.catalogue import Catalogue
from sambhasha.config import database_url
from sambhasha.curation.catalogue_names import CatalogueError, CatalogueNames
from sambhasha.curation.importer import ImportRefusedError, import_bundle
from sambhasha.engine.tables import generate_tables, write_tables
from sambhasha.storage.postgres import open_postgres

app = typer.Typer(
    help=(
        "Sambhasha: AI and human doctor seats work up hidden, published case reports. "
        "An educational research tool: its output is not clinical advice."
    ),
    no_args_is_help=True,
)
case_app = typer.Typer(help="Import and list Case Library bundles.", no_args_is_help=True)
app.add_typer(case_app, name="case")
tables_app = typer.Typer(
    help="Price and turnaround tables from the catalogue.", no_args_is_help=True
)
app.add_typer(tables_app, name="tables")

# The repository the commands use; tests replace it with an in-memory one.
open_repository = open_postgres


@app.callback()
def main() -> None:
    """Keep subcommands explicit."""


@app.command()
def version() -> None:
    """Print the installed Sambhasha version."""
    typer.echo(f"sambhasha {__version__}")


@case_app.command("import")
def case_import(
    bundle: Annotated[Path, typer.Argument(help="A bundle file from ../case-library/exports/")],
) -> None:
    """Verify, leak-scan and store one bundle in the run database (SUPABASE_DB_URL)."""
    try:
        catalogue = CatalogueNames.load()
        with open_repository(database_url()) as repo:
            report = import_bundle(bundle, repo, catalogue)
    except (ImportRefusedError, CatalogueError) as error:
        typer.echo(f"Refused: {error}", err=True)
        raise typer.Exit(code=1) from error
    counts = ", ".join(f"{n} {name.replace('_', ' ')}" for name, n in report.counts.items())
    typer.echo(f"Imported {report.bundle_id} (SHA-256 {report.sha256[:12]}): {counts}; no leaks.")
    typer.echo(f"Marked not eligible for primary results ({report.eligibility_reason}).")


@case_app.command("list")
def case_list() -> None:
    """List the imported bundles and whether a study may use them for primary results."""
    with open_repository(database_url()) as repo:
        records = repo.list_bundles()
    if not records:
        typer.echo("No bundles imported yet.")
        return
    for record in records:
        eligibility = "primary" if record.primary_eligible else "not primary"
        typer.echo(
            f"{record.bundle_id}  catalogue v{record.catalogue_version}  {eligibility}"
            f"  ({record.eligibility_reason or 'no decision recorded'})"
        )


@tables_app.command("generate")
def tables_generate() -> None:
    """Write configs/prices_inr.yaml and configs/turnaround.yaml from the shared catalogue."""
    try:
        prices, turnaround = write_tables(generate_tables(Catalogue.load()))
    except CatalogueError as error:
        typer.echo(f"Refused: {error}", err=True)
        raise typer.Exit(code=1) from error
    typer.echo(f"Wrote {prices.name} and {turnaround.name}.")
