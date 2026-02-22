"""
K-Way Merge for Sorted Linked Lists

This module implements merging k sorted linked lists using a min-heap approach.
"""

import heapq
from typing import List, Optional


class ListNode:
    """Definition for singly-linked list node."""
    
    def __init__(self, val: int = 0, next: 'ListNode' = None):
        self.val = val
        self.next = next


def merge_k_lists_min_heap(lists: List[Optional[ListNode]]) -> Optional[ListNode]:
    """
    Merge k sorted linked lists into one sorted list using a min-heap.
    
    Time Complexity: O(N log k) where N is total number of nodes
    Space Complexity: O(k) for the heap
    
    Args:
        lists: List of sorted linked list heads (can contain None)
        
    Returns:
        Head of merged sorted linked list, or None for empty input
    """
    # Handle empty list case
    if not lists:
        return None
    
    # Initialize min-heap with first node from each non-empty list
    # Store (value, list_index, node) tuples to handle duplicates correctly
    heap = []
    for idx, head in enumerate(lists):
        if head is not None:
            heapq.heappush(heap, (head.val, idx, head))
    
    # Dummy head to simplify the merge process
    dummy = ListNode(0)
    current = dummy
    
    while heap:
        # Extract the minimum element from heap
        val, idx, node = heapq.heappop(heap)
        
        # Append this node to the result list (create a new node to avoid mutating input)
        current.next = ListNode(val)
        current = current.next
        
        # If there's a next node in this list, push it to heap
        # We need to traverse to find it without modifying the original list
        if node.next is not None:
            heapq.heappush(heap, (node.next.val, idx, node.next))
    
    return dummy.next


def merge_k_lists_brute_force(lists: List[Optional[ListNode]]) -> Optional[ListNode]:
    """
    Merge k sorted linked lists using brute-force approach.
    
    Collects all values, sorts them, and rebuilds the linked list.
    
    Time Complexity: O(N log N)
    Space Complexity: O(N)
    
    Args:
        lists: List of sorted linked list heads (can contain None)
        
    Returns:
        Head of merged sorted linked list, or None for empty input
    """
    # Collect all values
    values = []
    
    for head in lists:
        current = head
        while current:
            values.append(current.val)
            current = current.next
    
    # Sort values
    values.sort()
    
    # Rebuild linked list
    if not values:
        return None
    
    dummy = ListNode(0)
    current = dummy
    
    for val in values:
        current.next = ListNode(val)
        current = current.next
    
    return dummy.next


def list_to_array(head: Optional[ListNode]) -> List[int]:
    """Convert linked list to array for easy verification."""
    result = []
    current = head
    while current:
        result.append(current.val)
        current = current.next
    return result


def array_to_list(arr: List[int]) -> Optional[ListNode]:
    """Convert array to linked list."""
    if not arr:
        return None
    
    dummy = ListNode(0)
    current = dummy
    for val in arr:
        current.next = ListNode(val)
        current = current.next
    
    return dummy.next
