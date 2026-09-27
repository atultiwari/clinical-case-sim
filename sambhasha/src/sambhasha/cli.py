"""The `sambhasha` command line (SPEC §17). Later tasks add `run`, `transcript` and more."""

import json
import re
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import typer

from sambhasha import __version__
from sambhasha.catalogue import Catalogue
from sambhasha.config import database_url
from sambhasha.curation.catalogue_names import CatalogueError, CatalogueNames
from sambhasha.curation.importer import ImportRefusedError, import_bundle
from sambhasha.engine.config import DEFAULT_RUN_CONFIG, RunConfigError, load_run_config
from sambhasha.engine.fake_script import FakeScriptError, load_fake_script
from sambhasha.engine.scheduler import CallRecorder
from sambhasha.engine.tables import generate_tables, write_tables
from sambhasha.evaluation.evaluator import Evaluator
from sambhasha.evaluation.mapper import ScoringMapper
from sambhasha.gatekeeper.coding import Coder, MissingRequestLog
from sambhasha.llm.cache import DEFAULT_CACHE_DIR, CacheMiss, RecordReplayCache
from sambhasha.llm.config import ROLES, ConfigError, load_models_config
from sambhasha.llm.fake import FakeLLM
from sambhasha.llm.gateway import LLMGateway
from sambhasha.llm.ratelimit import WaitLedger
from sambhasha.runner import build_scheduler, fake_models_config
from sambhasha.storage.postgres import open_postgres
from sambhasha.storage.repo import DuplicateError, NotFoundError
from sambhasha.transcript import render_html, render_text

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


def make_gateway(replay_only: bool) -> LLMGateway:
    """The model gateway for commands, with the record-and-replay cache."""
    return LLMGateway(load_models_config(), cache=RecordReplayCache(replay_only=replay_only))


@app.command()
def evaluate(
    run_id: Annotated[UUID, typer.Argument(help="The run to score")],
    replay_only: Annotated[
        bool, typer.Option(help="Use cached model replies only; never call a model")
    ] = False,
) -> None:
    """Score a finished run against its case and store the score (SPEC §13).

    Free text that is not an exact catalogue name is mapped by the matcher model, which may
    cost a little; with --replay-only only cached replies are used.
    """
    catalogue = Catalogue.load()
    try:
        with open_repository(database_url()) as repo:
            run = repo.get_run(run_id)
            bundle = repo.get_bundle(run.bundle_id)
            mapper = ScoringMapper(
                catalogue, Coder(catalogue, missing=MissingRequestLog()), make_gateway(replay_only)
            )
            evaluation = Evaluator(bundle, mapper).evaluate(
                run, repo.events(run_id), repo.orders(run_id)
            )
            repo.add_score(evaluation.score)
    except (NotFoundError, DuplicateError, ValueError, CacheMiss, ConfigError) as error:
        typer.echo(f"Refused: {error}", err=True)
        raise typer.Exit(code=1) from error
    score = evaluation.score
    total_do = len(evaluation.must_do)
    typer.echo(f"Run {run_id} on {run.bundle_id}")
    typer.echo(
        f"Diagnosis score: {score.dx_score}/5 ({'correct' if score.dx_correct else 'not correct'})"
    )
    typer.echo(
        f"Must-do met: {score.must_do_hit}/{total_do}; "
        f"must-not-do violated: {score.must_not_do_hit}"
    )
    for flag in score.safety_flags:
        typer.echo(f"  Safety: {flag}")
    typer.echo(
        f"Cost: INR {score.cost_inr}; simulated hours: {score.sim_hours:.1f}; turns: {score.turns}"
    )
    dependence = (
        "n/a" if score.synthetic_dependence is None else f"{score.synthetic_dependence:.0%}"
    )
    fallback = "yes" if score.used_fallback else "no"
    typer.echo(f"Synthetic dependence: {dependence}; fallback used: {fallback}")


MISSING_DIR = Path(__file__).resolve().parents[2] / "data" / "missing"
RUNS_DIR = Path(__file__).resolve().parents[2] / "data" / "runs"


def cache_dir(tag: str | None) -> Path:
    """The reply cache for a run: shared, or its own folder for a tagged repeat."""
    if tag is None:
        return DEFAULT_CACHE_DIR
    if not re.fullmatch(r"[A-Za-z0-9._-]+", tag):
        raise RunConfigError(f"a cache tag uses letters, digits, '.', '_' or '-' only: {tag!r}")
    return DEFAULT_CACHE_DIR / tag


@app.command("run")
def run_case(
    config: Annotated[Path, typer.Option(help="The run configuration")] = DEFAULT_RUN_CONFIG,
    fake: Annotated[
        bool, typer.Option(help="Play the config's scripted replies: no network, no cost")
    ] = False,
    doctor_profile: Annotated[
        str | None, typer.Option(help="Put every doctor seat on this models.yaml profile")
    ] = None,
    cache_tag: Annotated[
        str | None,
        typer.Option(
            help="Keep this run's model replies in data/llm-cache/<tag>/ (one per repeat)"
        ),
    ] = None,
) -> None:
    """Run one case with the seats in the config (SPEC §10).

    A live run refuses to start without llm_budget_usd in the config, and stops making model
    calls once it has spent that much; cached replays are free.
    """
    try:
        run_config = load_run_config(config)
        recorder = CallRecorder()
        if fake:
            if run_config.fake_script is None:
                raise RunConfigError(f"{config.name} has no fake_script for --fake")
            script = FakeLLM(load_fake_script(run_config.fake_script))
            gateway = LLMGateway(
                fake_models_config(), backend_for=lambda e: script, on_call=recorder
            )
        else:
            if run_config.llm_budget_usd is None:
                raise RunConfigError(
                    f"a live run needs llm_budget_usd in {config.name}; set a cap or use --fake"
                )
            models = load_models_config()
            if doctor_profile:
                models = models.with_doctor_profile(doctor_profile)
            for role in ROLES:
                models.endpoint_for(role)  # a missing key refuses the run before it starts
            gateway = LLMGateway(
                models,
                cache=RecordReplayCache(cache_dir(cache_tag)),
                on_call=recorder,
                spend_cap_usd=run_config.llm_budget_usd,
            )
        missing = MissingRequestLog()
        with open_repository(database_url()) as repo:
            try:
                bundle = repo.get_bundle(run_config.bundle)
            except NotFoundError as error:
                raise RunConfigError(
                    f"{run_config.bundle} is not imported; run `sambhasha case import` first"
                ) from error
            scheduler = build_scheduler(
                config=run_config,
                bundle=bundle,
                repo=repo,
                gateway=gateway,
                recorder=recorder,
                missing=missing,
            )
            result = scheduler.run(uuid4())
    except (RunConfigError, FakeScriptError, ConfigError) as error:
        typer.echo(f"Refused: {error}", err=True)
        raise typer.Exit(code=1) from error
    run = result.run
    typer.echo(f"Run {run.id} on {run.bundle_id}: {run.status}")
    if result.commit is not None:
        typer.echo(f"Committed: {result.commit.final_diagnosis}")
    if result.stopped_reason:
        typer.echo(f"Stopped: {result.stopped_reason}")
    flags = [
        name
        for name, on in (
            ("forced commit", result.forced_commit),
            ("used the synthetic fallback", result.used_fallback),
        )
        if on
    ]
    typer.echo(
        f"{len(result.events)} events; final hash {result.event_hash[:16]}"
        + (f"; {', '.join(flags)}" if flags else "")
    )
    if not fake:
        typer.echo(
            f"Model calls cost USD {gateway.spent_usd} of the USD {run_config.llm_budget_usd} cap."
        )
    if missing.requests:
        MISSING_DIR.mkdir(parents=True, exist_ok=True)
        path = missing.write_csv(MISSING_DIR / f"{run.id}.csv")
        typer.echo(f"Missing requests for the Case Library: {path}")
    _report_waits(run.id, gateway.waits)
    typer.echo(f"Next: sambhasha transcript {run.id}; sambhasha evaluate {run.id}")


def _report_waits(run_id: UUID, waits: WaitLedger) -> None:
    """How long the run waited on rate limits, and what a paid tier would have saved."""
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    stats = {"run_id": str(run_id), **waits.summary()}
    (RUNS_DIR / f"{run_id}.waits.json").write_text(json.dumps(stats, indent=1), encoding="utf-8")
    if waits.pauses:
        typer.echo(
            f"Waited {WaitLedger.describe(waits.total_seconds)} for the free tier's rate limits"
            f" ({waits.pauses} pauses). A paid tier would have saved most of this time."
        )


@app.command()
def transcript(
    run_id: Annotated[UUID, typer.Argument(help="The run to show")],
    html_out: Annotated[
        Path | None, typer.Option("--html", help="Write a self-contained HTML page here")
    ] = None,
) -> None:
    """Show a run's whole Event Log (private: it holds the case's answers)."""
    try:
        with open_repository(database_url()) as repo:
            run = repo.get_run(run_id)
            events, orders = repo.events(run_id), repo.orders(run_id)
    except NotFoundError as error:
        typer.echo(f"Refused: {error}", err=True)
        raise typer.Exit(code=1) from error
    if html_out is None:
        typer.echo(render_text(run, events, orders), nl=False)
        return
    html_out.write_text(render_html(run, events, orders), encoding="utf-8")
    typer.echo(f"Wrote {html_out}")
