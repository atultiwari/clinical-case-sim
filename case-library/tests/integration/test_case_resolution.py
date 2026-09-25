"""Every curated case resolves completely on the local database (PLAN L1.3).

A case counts as curated once it has a `curation/` folder. Its replay
(scripts/case_replay.py) must end with no coverage gap, consistency problem,
leak or placeholder, as the skill's step 10 requires before hand-over.
"""

from pathlib import Path

import psycopg
import pytest

from scripts.case_replay import replay

pytestmark = pytest.mark.integration

CASES = Path(__file__).resolve().parents[2] / "cases"
CURATED = sorted(p.parent for p in CASES.glob("*/curation"))


@pytest.mark.parametrize("case_dir", CURATED, ids=lambda p: p.name)
def test_the_case_resolves_with_nothing_open(db: psycopg.Connection, case_dir: Path) -> None:
    [result] = replay(db, [case_dir])
    assert result.problems == []
