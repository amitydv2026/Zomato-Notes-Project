"""
Unit tests for algorithms.py — pure functions, no database needed.
These run instantly and cover the four hand-written search/sort algorithms.
"""

from algorithms import (
    binary_search_iterative,
    binary_search_recursive,
    insertion_sort_by_key,
    linear_search,
)


# ── Insertion sort ────────────────────────────────────────────────────────────

def test_insertion_sort_descending_by_score():
    items = [
        {"title": "low", "score": 1},
        {"title": "high", "score": 9},
        {"title": "mid", "score": 5},
    ]
    result = insertion_sort_by_key(items, "score")
    assert [r["score"] for r in result] == [9, 5, 1]


def test_insertion_sort_empty_list():
    assert insertion_sort_by_key([], "score") == []


def test_insertion_sort_single_element():
    assert insertion_sort_by_key([{"title": "x", "score": 3}], "score") == [
        {"title": "x", "score": 3}
    ]


def test_insertion_sort_does_not_mutate_input():
    items = [{"title": "a", "score": 3}, {"title": "b", "score": 1}]
    original = [d["score"] for d in items]
    insertion_sort_by_key(items, "score")
    assert [d["score"] for d in items] == original


# ── Binary search (iterative) ─────────────────────────────────────────────────

def test_binary_search_iterative_finds_existing():
    titles = ["alpha", "bravo", "charlie", "delta", "echo"]
    assert binary_search_iterative(titles, "charlie") == 2


def test_binary_search_iterative_case_insensitive():
    titles = ["alpha", "bravo", "charlie"]
    assert binary_search_iterative(titles, "CHARLIE") == 2


def test_binary_search_iterative_first_and_last():
    titles = ["alpha", "bravo", "charlie"]
    assert binary_search_iterative(titles, "alpha") == 0
    assert binary_search_iterative(titles, "charlie") == 2


def test_binary_search_iterative_missing_returns_neg1():
    assert binary_search_iterative(["alpha", "bravo"], "zulu") == -1


def test_binary_search_iterative_empty_list():
    assert binary_search_iterative([], "anything") == -1


# ── Binary search (recursive) ─────────────────────────────────────────────────

def test_binary_search_recursive_finds_existing():
    titles = ["alpha", "bravo", "charlie", "delta", "echo"]
    assert binary_search_recursive(titles, "delta", 0, len(titles) - 1) == 3


def test_binary_search_recursive_case_insensitive():
    titles = ["alpha", "bravo", "charlie"]
    assert binary_search_recursive(titles, "BRAVO", 0, len(titles) - 1) == 1


def test_binary_search_recursive_missing_returns_neg1():
    titles = ["alpha", "bravo"]
    assert binary_search_recursive(titles, "zulu", 0, 1) == -1


# ── Linear search ─────────────────────────────────────────────────────────────

def test_linear_search_finds_first_match():
    items = [{"tag": "work"}, {"tag": "health"}, {"tag": "work"}]
    assert linear_search(items, "tag", "work") == items[0]


def test_linear_search_returns_none_when_absent():
    assert linear_search([{"tag": "work"}], "tag", "travel") is None


def test_linear_search_empty_list():
    assert linear_search([], "tag", "work") is None
