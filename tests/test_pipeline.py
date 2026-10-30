import json
from pathlib import Path

import pytest

from wcsmatrix.data import prepare
from wcsmatrix.io import digest, write_jsonl
from wcsmatrix.local import encode_text


def test_selection_pairs_questions_and_refuses_changed_manifest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw = Path("data/raw/hc3-eli5-test.jsonl")
    rows = [
        {"question": str(i), "human_answers": ["too short", " ".join(["word"] * (150 + i))]} for i in range(5)
    ]
    write_jsonl(raw, rows)
    config = {
        "dataset": {"revision": "test", "n": 3, "seed": 42, "min_words": 150, "max_words": 400},
        "prompts": "prompts.jsonl",
        "human_texts": "human.jsonl",
        "prompt_template": "Question: {question}",
    }
    prepare(config)
    prompts = [json.loads(s) for s in Path("prompts.jsonl").read_text().splitlines()]
    human = [json.loads(s) for s in Path("human.jsonl").read_text().splitlines()]
    assert len({r["id"] for r in prompts}) == 3
    assert all(r["answer_index"] == 1 for r in prompts)
    assert [h["prompt_id"] for h in human] == [p["id"] for p in prompts]
    assert all(h["prompt_sha256"] == digest(p["prompt"]) for h, p in zip(human, prompts))
    prepare(config)
    config["dataset"]["seed"] = 1
    with pytest.raises(ValueError, match="different prompts"):
        prepare(config)


class CharTokenizer:
    def __call__(self, text, **kwargs):
        return {
            "input_ids": [ord(c) % 32 for c in text],
            "offset_mapping": [(i, i + 1) for i in range(len(text))],
        }


def test_answer_offsets_and_teacher_forcing_boundary():
    ids, selected, offsets = encode_text(CharTokenizer(), "Q: ", "café")
    assert selected.tolist() == [3, 4, 5, 6]
    assert offsets.tolist() == [[0, 1], [1, 2], [2, 3], [3, 4]]
    assert ids[selected[0]] == ord("c") % 32


def test_offline_rescore_allows_threshold_change_but_rejects_inference_drift(tmp_path, monkeypatch):
    import numpy as np
    from wcsmatrix.io import write_json
    from wcsmatrix.local import rescore

    monkeypatch.chdir(tmp_path)
    spec = {"name": "scorer", "family": "x", "id": "model", "revision": "fixed"}
    scoring = {
        "modes": ["realistic"],
        "top_p": [0.99],
        "word_policy": "whitespace",
        "top_k": 2,
        "context_mode": "chat",
        "chunk_size": 128,
        "max_sequence_tokens": 100,
        "temperature": 1.0,
    }
    cfg = {
        "name": "test",
        "models": [spec],
        "scoring": scoring,
        "prompts": "p.jsonl",
        "human_texts": "h.jsonl",
        "local_texts": "l.jsonl",
        "frontier_texts": "f.jsonl",
    }
    write_jsonl("p.jsonl", [{"id": "q", "prompt": "Q"}])
    write_jsonl("h.jsonl", [{"prompt_id": "q", "source": "human", "text": "a b"}])
    inference = {k: v for k, v in scoring.items() if k not in {"modes", "top_p", "word_policy"}}
    identity = digest({"model": spec, "scoring": inference, "text": "a b", "prompt": "Q"})
    root = Path("results/audits/test/scorer/human")
    root.mkdir(parents=True)
    np.savez_compressed(
        root / "q.npz",
        top_probs=[[0.9, 0.1], [0.9, 0.1]],
        target_top_index=[0, 1],
        mass_before=[0, 0.9],
        offsets=[[0, 1], [1, 3]],
    )
    write_json(
        root / "q.json",
        {
            "audit_sha256": identity,
            "prompt_id": "q",
            "source": "human",
            "text": "a b",
            "scorer": "scorer",
            "family": "human",
            "kind": "human",
            "scorer_family": "x",
        },
    )
    rescore(cfg)
    target = Path("results/scores/test.jsonl")
    assert json.loads(target.read_text())["wcs"] == 1
    scoring["top_p"] = [0.8]
    rescore(cfg)
    assert json.loads(target.read_text())["wcs"] == 0.5
    scoring["context_mode"] = "plain"
    with pytest.raises(ValueError, match="identity changed"):
        rescore(cfg)


def test_additional_source_files_are_combined_without_relabeling(tmp_path, monkeypatch):
    from wcsmatrix.local import source_texts

    monkeypatch.chdir(tmp_path)
    config = {
        "human_texts": "human.jsonl",
        "local_texts": "local.jsonl",
        "frontier_texts": "closed.jsonl",
        "additional_texts": ["open.jsonl"],
    }
    write_jsonl("human.jsonl", [{"prompt_id": "q", "source": "human", "kind": "human"}])
    write_jsonl("closed.jsonl", [{"prompt_id": "q", "source": "closed", "kind": "frontier"}])
    write_jsonl(
        "open.jsonl",
        [
            {
                "prompt_id": "q",
                "source": "open",
                "kind": "frontier",
                "source_metadata": {"weights_access": "open_weights"},
            }
        ],
    )
    rows = source_texts(config)
    assert len(rows) == 3
    assert rows[-1]["kind"] == "frontier"
    assert rows[-1]["source_metadata"]["weights_access"] == "open_weights"
    config["additional_texts"].append("closed.jsonl")
    with pytest.raises(ValueError, match="Duplicate row"):
        source_texts(config)


def test_evaluation_exclusions_are_explicit_and_do_not_change_frozen_data(tmp_path, monkeypatch):
    from wcsmatrix.io import evaluation_prompts

    monkeypatch.chdir(tmp_path)
    path = Path("prompts.jsonl")
    write_jsonl(path, [{"id": "q1"}, {"id": "q2"}, {"id": "q3"}])
    original = path.read_bytes()
    config = {"prompts": str(path), "evaluation_exclusions": {"q2": "provider content filter"}}
    assert [r["id"] for r in evaluation_prompts(config)] == ["q1", "q3"]
    assert path.read_bytes() == original
    config["evaluation_exclusions"]["unknown"] = "typo"
    with pytest.raises(ValueError, match="unknown prompts"):
        evaluation_prompts(config)
