# T9: K-Way Merge for Sorted Linked Lists - Architecture Plan

## Overview
Implement k-way merge for sorted linked lists using a min-heap approach with O(N log k) time complexity.

## Problem Statement
Given k sorted linked lists, merge them into a single sorted linked list.

## Architecture

### Core Algorithm: Min-Heap Based K-Way Merge
- Use a min-heap (priority queue) to always extract the smallest element
- Heap size remains at k (or less if some lists are exhausted)
- Time complexity: O(N log k) where N is total number of nodes
- Space complexity: O(k) for the heap

### Components

1. **ListNode Class**
   - `val`: node value
   - `next`: pointer to next node

2. **Solution Class**
   - `mergeKLists(lists: List[ListNode]) -> ListNode`
     - Handles empty lists and null nodes gracefully
     - Returns None for empty input
   - `mergeKListsBruteForce(lists: List[ListNode]) -> ListNode`
     - Brute-force baseline: collect all values, sort, rebuild list
     - O(N log N) time, O(N) space

3. **Test Cases**
   - k=0 (empty list)
   - k=1 (single list)
   - Uneven lengths
   - Lists with duplicates
   - All-empty lists
   - Mixed empty and non-empty lists

## Complexity Trade-offs

| Approach | Time | Space | Notes |
|----------|------|-------|-------|
| Min-Heap | O(N log k) | O(k) | Optimal for large k |
| Brute Force | O(N log N) | O(N) | Simpler, good baseline |
| Merge pairs | O(N log k) | O(1)* | *without recursion stack |

## File Structure
```
factory-testing/
├── app/
│   └── (existing code)
├── docs/
│   └── T9-plan.md (this file)
├── tests/
│   └── test_k_way_merge.py
└── app/k_way_merge.py (new)
```

## Implementation Notes
- Use heapq module for min-heap in Python
- Store (value, list_index, node) tuples to handle duplicate values correctly
- Implement proper null/empty handling per acceptance criteria
