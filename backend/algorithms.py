"""
Part 2 — Ranking Engine
All four algorithms implemented from scratch.
No built-in sorted(), list.sort(), or any imported search/sort utility.
"""

from typing import Optional


# ── 1. Insertion Sort ─────────────────────────────────────────────────────────

def insertion_sort_by_key(items: list[dict], key: str) -> list[dict]:
    """
    Sort a list of dicts in DESCENDING order by a numeric key,
    using insertion sort from scratch.

    Outer loop: pick each element starting from index 1.
    Inner backward-swap loop: shift elements right while the current element
    is greater (descending), placing it in the correct position.
    """
    arr = list(items)  # shallow copy — do not mutate the caller's list
    for i in range(1, len(arr)):
        current = arr[i]
        j = i - 1
        # Move elements that are LESS than current one position to the right
        # (descending order means larger values bubble left)
        while j >= 0 and arr[j][key] < current[key]:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = current
    return arr


# ── 2. Iterative Binary Search ────────────────────────────────────────────────

def binary_search_iterative(sorted_titles: list[str], target: str) -> int:
    """
    Return the index of target in a sorted list of title strings, or -1.
    Uses the overflow-safe midpoint formula: start + (end - start) // 2.
    Case-insensitive comparison.
    """
    target_lower = target.lower()
    start = 0
    end = len(sorted_titles) - 1

    while start <= end:
        mid = start + (end - start) // 2
        mid_val = sorted_titles[mid].lower()

        if mid_val == target_lower:
            return mid
        elif mid_val < target_lower:
            start = mid + 1
        else:
            end = mid - 1

    return -1


# ── 3. Recursive Binary Search ────────────────────────────────────────────────

def binary_search_recursive(
    sorted_titles: list[str], target: str, start: int, end: int
) -> int:
    """
    Recursive binary search. Returns index of target or -1.
    Base case: start > end → return -1.
    Case-insensitive comparison.
    """
    if start > end:
        return -1

    mid = start + (end - start) // 2
    mid_val = sorted_titles[mid].lower()
    target_lower = target.lower()

    if mid_val == target_lower:
        return mid
    elif mid_val < target_lower:
        return binary_search_recursive(sorted_titles, target, mid + 1, end)
    else:
        return binary_search_recursive(sorted_titles, target, start, mid - 1)


# ── 4. Linear Search with Found-Flag ─────────────────────────────────────────

def linear_search(items: list[dict], key: str, value) -> Optional[dict]:
    """
    Scan items sequentially using an explicit found-flag pattern.
    Returns the first dict where dict[key] == value, or None if no match.
    """
    found = False
    result = None
    for item in items:
        if item.get(key) == value:
            found = True
            result = item
            break  # stop at the first match

    if found:
        return result
    return None
