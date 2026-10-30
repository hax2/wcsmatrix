import json
from pathlib import Path

import httpx
import pytest

from wcsmatrix.frontier import collect
from wcsmatrix.io import write_jsonl


@pytest.mark.parametrize(
    "metadata", [None, {"weights_access": "open_weights", "reference_weights": {"weights_revision": "fixed"}}]
)
def test_api_provenance_no_secrets_and_resume_identity(tmp_path, monkeypatch, metadata):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-test-value")
    config = {
        "prompts": "p.jsonl",
        "frontier_texts": "texts.jsonl",
        "frontier_max_tokens": 100,
        "frontier_models": [{"name": "frontier", "id": "test/model", "family": "test", "parameters": {}}],
    }
    if metadata:
        config["frontier_models"][0]["metadata"] = metadata
    write_jsonl("p.jsonl", [{"id": "p1", "prompt": "Question"}])
    calls = []

    def handler(request):
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "data": [
                        {
                            "id": "test/model",
                            "pricing": {"prompt": ".000001", "completion": ".000002"},
                            "supported_parameters": [],
                        }
                    ]
                },
            )
        calls.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "r1",
                "model": "test/model-snapshot",
                "provider": "provider",
                "choices": [{"message": {"content": "A usable answer"}, "finish_reason": "stop"}],
                "usage": {"cost": 0.001},
            },
        )

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw)
    )
    collect(config, max_cost=1)
    collect(config, max_cost=1)
    assert len(calls) == 1
    row = json.loads(Path("texts.jsonl").read_text())
    assert row["kind"] == "frontier"
    assert row["model_returned"] == "test/model-snapshot"
    assert row["complete"] is True
    assert "secret-test-value" not in Path("texts.jsonl").read_text()
    assert row["request_sha256"]
    if metadata:
        assert row["source_metadata"] == metadata
        config["frontier_models"][0]["metadata"] = {**metadata, "changed": True}
        with pytest.raises(ValueError, match="different settings"):
            collect(config, max_cost=1)
        config["frontier_models"][0]["metadata"] = metadata
    config["frontier_max_tokens"] = 200
    with pytest.raises(ValueError, match="different settings"):
        collect(config, max_cost=1)


def test_missing_prompt_manifest_is_a_failure(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-value")
    with pytest.raises(ValueError, match="No prompts"):
        collect({"prompts": "absent.jsonl"})


def test_combined_analysis_config_cannot_overwrite_baseline_collection():
    with pytest.raises(ValueError, match="analysis-only"):
        collect({"frontier_collection_enabled": False})
