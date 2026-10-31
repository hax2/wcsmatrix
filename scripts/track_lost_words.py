#!/usr/bin/env python3
"""
Track which words get lost under the Word Coverage Score (WCS) definition.

In WCS:
A word is segmented by the word policy (whitespace by default).
A word is LOST if any of its constituent subtokens fails to fall within
the top-p nucleus of the scorer (i.e. cumulative mass before > p or target not in top-100).
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from wcsmatrix.metrics import word_groups


def analyze_lost_words(audit_dir: Path, p: float = 0.99, mode: str = "realistic", policy: str = "whitespace"):
    lost_records = []
    word_counters_by_pair = defaultdict(Counter)
    word_counters_by_source = defaultdict(Counter)
    total_words_by_source = Counter()

    npz_paths = sorted(audit_dir.glob("*/*/*.npz"))
    print(f"Analyzing {len(npz_paths)} audits in {audit_dir}...")

    for path in npz_paths:
        meta_path = path.with_suffix(".json")
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text())
        scorer = meta["scorer"]
        source = meta["source"]
        prompt_id = meta["prompt_id"]
        text = meta["text"]

        with np.load(path, allow_pickle=False) as arrays:
            top_probs = arrays["top_probs"]
            target_top_index = arrays["target_top_index"]
            offsets = arrays["offsets"].tolist()
            mass_before = arrays.get("mass_before")

        probs = np.asarray(top_probs, dtype=np.float64)
        indices = np.asarray(target_top_index, dtype=int)

        if mode == "realistic":
            probs = probs / probs.sum(axis=-1, keepdims=True)
            before = probs.cumsum(axis=-1) - probs
            valid = (indices >= 0) & (indices < probs.shape[1])
            survives = valid & (before[np.arange(len(indices)), indices.clip(0, probs.shape[1] - 1)] <= p)
        elif mode == "strict":
            before = probs.cumsum(axis=-1) - probs
            valid = (indices >= 0) & (indices < probs.shape[1])
            survives = valid & (before[np.arange(len(indices)), indices.clip(0, probs.shape[1] - 1)] <= p)
        elif mode == "strict_full":
            survives = np.asarray(mass_before) <= p
        else:
            raise ValueError(mode)

        # Segment text into words
        pattern = r"\S+" if policy == "whitespace" else r"\b\w+(?:['’-]\w+)*\b"
        import re

        matches = list(re.finditer(pattern, text, flags=re.UNICODE))
        groups = word_groups(text, offsets, policy)

        if len(matches) != len(groups):
            continue

        for match, g in zip(matches, groups):
            word_str = match.group()
            total_words_by_source[source] += 1
            word_survives = bool(np.all(survives[g]))

            if not word_survives:
                # Find which token(s) failed
                failing_tokens = [tok_idx for tok_idx in g if not survives[tok_idx]]
                first_fail = failing_tokens[0]
                fail_reason = "outside_top100" if indices[first_fail] < 0 else "outside_nucleus_p"

                lost_records.append(
                    {
                        "scorer": scorer,
                        "source": source,
                        "prompt_id": prompt_id,
                        "word": word_str,
                        "char_start": match.start(),
                        "char_end": match.end(),
                        "failing_token_idx": first_fail,
                        "reason": fail_reason,
                    }
                )
                word_counters_by_pair[(source, scorer)][word_str.lower()] += 1
                word_counters_by_source[source][word_str.lower()] += 1

    return lost_records, word_counters_by_pair, word_counters_by_source, total_words_by_source


def main():
    parser = argparse.ArgumentParser(description="Track lost words in WCS audits")
    parser.add_argument(
        "--suite",
        default="results/audits/hc3-50-expanded-open-frontier-20261030",
        help="Path to audit suite directory",
    )
    parser.add_argument("--p", type=float, default=0.99)
    parser.add_argument("--mode", default="realistic")
    parser.add_argument("--output", default="results/reports/wcs_lost_words.csv")
    args = parser.parse_args()

    audit_dir = Path(args.suite)
    records, by_pair, by_source, totals = analyze_lost_words(audit_dir, p=args.p, mode=args.mode)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "scorer",
                "source",
                "prompt_id",
                "word",
                "char_start",
                "char_end",
                "failing_token_idx",
                "reason",
            ],
        )
        writer.writeheader()
        writer.writerows(records)

    print(f"\nWrote {len(records)} lost word occurrences to {out_path}")
    print("\n=== TOP 10 MOST FREQUENTLY LOST WORDS BY SOURCE (WCS p=0.99) ===")
    for src in sorted(by_source.keys()):
        top_words = by_source[src].most_common(10)
        formatted = ", ".join(f"{w} ({c})" for w, c in top_words)
        print(f"\n{src}:")
        print(f"  {formatted}")


if __name__ == "__main__":
    main()
