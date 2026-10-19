import json
import re

from qqq_volatility_forecaster.brief.evaluate import run_eval


class EchoLlm:
    model_id = "echo"

    def complete(self, system: str, prompt: str) -> str:
        date = re.search(r"Date: (\S+)", prompt).group(1)
        forecast = re.search(r"forecast of realized .*?: (\S+)", prompt).group(1)
        vxn = re.search(r"VXN, options-implied .*?: (\S+)", prompt).group(1)
        return f"On {date} the forecast was {forecast} and VXN was {vxn}."


def test_eval_scores_every_case(tmp_path):
    case = {"status": "ok", "date": "2020-01-02", "forecast": 15.25, "vxn": 18.5, "premium": 3.25}
    path = tmp_path / "eval.json"
    path.write_text(json.dumps([case, {**case, "date": "2021-01-04"}]))
    report = run_eval(EchoLlm(), path)
    assert report["verified"] == 2
    assert report["passed"]
