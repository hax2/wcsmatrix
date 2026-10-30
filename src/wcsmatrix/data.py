from __future__ import annotations

import json
import random
from pathlib import Path

import httpx

from .io import digest, write_json, write_jsonl


def prepare(config):
    spec = config["dataset"]
    domain = spec.get("domain", "eli5")
    filename = "reddit_eli5" if domain == "eli5" else domain
    raw = Path(f"data/raw/hc3-{domain}-{spec['revision']}.jsonl")
    raw.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://huggingface.co/datasets/Hello-SimpleAI/HC3/resolve/{spec['revision']}/{filename}.jsonl"
    if not raw.exists():
        response = httpx.get(url, follow_redirects=True, timeout=120)
        response.raise_for_status()
        raw.write_bytes(response.content)
    candidates = []
    for row_index, line in enumerate(raw.read_text().splitlines()):
        row = json.loads(line)
        for i, answer in enumerate(row["human_answers"]):
            if spec["min_words"] <= len(answer.split()) <= spec["max_words"]:
                candidates.append(
                    {
                        "id": f"hc3-{domain}-" + str(row.get("id", row_index)),
                        "question": row["question"],
                        "human_text": answer,
                        "answer_index": i,
                        "domain": domain,
                        "dataset": "HC3",
                        "dataset_revision": spec["revision"],
                    }
                )
                break
    if len(candidates) < spec["n"]:
        raise ValueError("Not enough eligible HC3 questions")
    candidates.sort(key=lambda r: r["id"])
    selected = random.Random(spec["seed"]).sample(candidates, spec["n"])
    for row in selected:
        row["prompt"] = config["prompt_template"].format(question=row["question"])
    target = Path(config["prompts"])
    if target.exists() and target.read_text().strip():
        from .io import read_jsonl

        if read_jsonl(target) != selected:
            raise ValueError(f"{target} already has different prompts; choose a new path")
    write_jsonl(target, selected)
    write_json(
        target.with_suffix(".manifest.json"),
        {
            "url": url,
            "raw_sha256": __import__("hashlib").sha256(raw.read_bytes()).hexdigest(),
            "selection": spec,
            "prompts_sha256": digest(selected),
            "eligible_questions": len(candidates),
            "license": "CC-BY-SA-4.0; see HC3 dataset card",
            "selection_note": "first length-eligible human answer per question; not original curated IDs",
        },
    )
    human = [
        {
            "prompt_id": row["id"],
            "source": "human",
            "family": "human",
            "kind": "human",
            "text": row["human_text"],
            "prompt_sha256": digest(row["prompt"]),
            "text_sha256": digest(row["human_text"]),
        }
        for row in selected
    ]
    write_jsonl(config["human_texts"], human)
    print(f"Prepared {len(selected)} paired prompts and human answers")
