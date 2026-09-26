"""The record-and-replay cache in `data/llm-cache/` (SPEC §11).

Each response is stored under the SHA-256 of its request, so an identical request is
answered from disk and a rerun is identical. `replay_only` refuses to call a model at all.
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from sambhasha.llm.types import LLMRequest, LLMResponse

DEFAULT_CACHE_DIR: Final = Path(__file__).resolve().parents[3] / "data" / "llm-cache"
log = logging.getLogger(__name__)


class CacheMiss(LookupError):  # noqa: N818 (it is a lookup outcome, raised only in replay-only mode)
    """A replay-only cache has no response for this request."""


class RecordReplayCache:
    def __init__(self, directory: Path = DEFAULT_CACHE_DIR, *, replay_only: bool = False) -> None:
        self._directory = directory
        self.replay_only = replay_only

    def _path(self, key: str) -> Path:
        return self._directory / key[:2] / f"{key}.json"

    def get(self, request: LLMRequest) -> LLMResponse | None:
        key = request.cache_key()
        path = self._path(key)
        try:
            return LLMResponse.model_validate_json(path.read_bytes())
        except FileNotFoundError:
            pass
        except (ValidationError, ValueError) as error:
            log.warning("ignoring unreadable cache entry %s: %s", path, error)
        if self.replay_only:
            raise CacheMiss(f"no cached response for request {key} (replay-only)")
        return None

    def put(self, request: LLMRequest, response: LLMResponse) -> None:
        path = self._path(request.cache_key())
        path.parent.mkdir(parents=True, exist_ok=True)
        body = json.dumps(response.model_dump(mode="json"), sort_keys=True, indent=1)
        # Write to a temporary file first, so a crash never leaves half an entry.
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
        ) as handle:
            handle.write(body)
        os.replace(handle.name, path)
