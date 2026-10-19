from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

import pandas as pd


def new_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:6]


@dataclass
class RunLog:
    run_id: str = field(default_factory=new_run_id)
    rows: list[dict] = field(default_factory=list)

    @contextmanager
    def step(self, name: str) -> Iterator[dict]:
        record = {
            "run_id": self.run_id,
            "step": name,
            "rows_in": None,
            "rows_out": None,
            "rows_quarantined": 0,
            "status": "running",
            "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        start = perf_counter()
        try:
            yield record
            if record["status"] == "running":
                record["status"] = "success"
        except Exception:
            record["status"] = "failed"
            raise
        finally:
            record["duration_s"] = round(perf_counter() - start, 3)
            self.rows.append(record)

    def frame(self) -> pd.DataFrame:
        frame = pd.DataFrame(self.rows)
        counts = ["rows_in", "rows_out", "rows_quarantined"]
        return frame.astype(dict.fromkeys(counts, "Int64")) if not frame.empty else frame
