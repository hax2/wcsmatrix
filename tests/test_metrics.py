import numpy as np
import pytest

from wcsmatrix.metrics import coverage, paired_bootstrap, word_groups


def test_nucleus_retains_crossing_token_and_rejects_following():
    probs = np.array([[0.6, 0.25, 0.1, 0.05]] * 4)
    got = coverage(probs, [0, 1, 2, 3], [[0], [1], [2], [3]], p=0.8, mode="strict")
    assert got["wcs"] == 0.5


def test_top100_renormalization_changes_reachability():
    probs = np.array([[0.4, 0.3, 0.1]])  # stored mass=.8; full mass may be below p
    assert coverage(probs, [2], [[0]], p=0.8, mode="strict")["wcs"] == 1
    assert coverage(probs, [2], [[0]], p=0.8, mode="realistic")["wcs"] == 0


def test_missing_top100_is_excluded_but_full_nucleus_can_retain():
    probs = np.array([[0.4, 0.3, 0.1]])
    assert coverage(probs, [-1], [[0]], p=0.99)["wcs"] == 0
    assert coverage(probs, [-1], [[0]], p=0.99, mode="strict_full", mass_before=[0.85])["wcs"] == 1


def test_word_requires_every_subtoken_and_unicode_offsets():
    text = "café storms!"
    groups = word_groups(text, [(0, 2), (2, 4), (4, 8), (8, 10), (10, 11)])
    assert groups == [[0, 1], [2, 3, 4]]
    got = coverage(np.array([[0.9, 0.1]] * 5), [0, -1, 0, 0, 0], groups)
    assert got == {"wcs": 0.5, "covered_words": 1, "total_words": 2}


def test_bootstrap_pairs_prompts_instead_of_independent_samples():
    result = paired_bootstrap([0.1, 0.5, 0.9], [0, 0.4, 0.8], replicates=1000)
    assert result["delta"] == pytest.approx(0.1)
    assert result["ci_low"] == pytest.approx(0.1)
    assert result["ci_high"] == pytest.approx(0.1)
    assert result == paired_bootstrap([0.1, 0.5, 0.9], [0, 0.4, 0.8], replicates=1000)


def test_empty_pairs_and_unmapped_words_are_errors():
    with pytest.raises(ValueError):
        paired_bootstrap([], [])
    with pytest.raises(ValueError):
        word_groups("hello", [])
