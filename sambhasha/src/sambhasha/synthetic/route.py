"""One request through the Gatekeeper, and on to the Synthetic Findings Service only when the
catalogue cannot answer it (D-023). A run that used the service is flagged: its results are
kept out of a study's primary results until the missing items are reviewed and added."""

from dataclasses import dataclass

from sambhasha.gatekeeper.resolver import Gatekeeper, GatekeeperRequest, Outcome, OutsideCatalogue
from sambhasha.synthetic.service import SyntheticOutcome, SyntheticService


@dataclass(frozen=True)
class Response:
    result: Outcome | SyntheticOutcome
    used_fallback: bool


def respond(
    gatekeeper: Gatekeeper,
    service: SyntheticService,
    request: GatekeeperRequest,
    released: tuple[str, ...] = (),
) -> Response:
    outcome = gatekeeper.resolve(request)
    if not isinstance(outcome, OutsideCatalogue):
        return Response(result=outcome, used_fallback=False)
    generated = service.answer(outcome, day=request.day, released=released)
    return Response(result=generated, used_fallback=True)
