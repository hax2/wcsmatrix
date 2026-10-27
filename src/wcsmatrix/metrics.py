from __future__ import annotations

import re

import numpy as np


def word_groups(text, offsets, policy="whitespace"):
    pattern = r"\S+" if policy == "whitespace" else r"\b\w+(?:['’-]\w+)*\b"
    groups = []
    for match in re.finditer(pattern, text, flags=re.UNICODE):
        positions = [i for i, (a, b) in enumerate(offsets) if b > a and a < match.end() and b > match.start()]
        if not positions:
            raise ValueError(f"Word has no token offsets: {match.group()!r}")
        groups.append(positions)
    if not groups:
        raise ValueError("No words to score")
    return groups


def coverage(top_probs, target_top_index, groups, p=0.99, mode="realistic", mass_before=None):
    """Retain the token crossing p. A word survives iff all overlapping tokens survive."""
    probs = np.asarray(top_probs, dtype=np.float64)
    indices = np.asarray(target_top_index, dtype=int)
    if not 0 < p <= 1:
        raise ValueError("p must be in (0, 1]")
    if mode == "strict_full":
        if mass_before is None:
            raise ValueError("strict_full needs full-vocabulary mass_before")
        survives = np.asarray(mass_before) <= p
    else:
        if mode not in {"realistic", "strict"}:
            raise ValueError(mode)
        if mode == "realistic":
            probs = probs / probs.sum(axis=-1, keepdims=True)
        before = probs.cumsum(axis=-1) - probs
        valid = (indices >= 0) & (indices < probs.shape[1])
        survives = valid & (before[np.arange(len(indices)), indices.clip(0, probs.shape[1] - 1)] <= p)
    words = [bool(np.all(survives[g])) for g in groups]
    return {"wcs": float(np.mean(words)), "covered_words": sum(words), "total_words": len(words)}


def paired_bootstrap(a, b, seed=42, replicates=10000):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if a.shape != b.shape or a.ndim != 1 or not len(a):
        raise ValueError("Paired bootstrap requires equal non-empty 1D arrays")
    delta = a - b
    rng = np.random.default_rng(seed)
    means = np.concatenate(
        [
            delta[rng.integers(0, len(delta), size=(min(1000, replicates - i), len(delta)))].mean(axis=1)
            for i in range(0, replicates, 1000)
        ]
    )
    return {
        "delta": float(delta.mean()),
        "ci_low": float(np.quantile(means, 0.025)),
        "ci_high": float(np.quantile(means, 0.975)),
        "n": len(delta),
    }
