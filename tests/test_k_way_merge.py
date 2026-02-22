"""
Unit tests for K-Way Merge functionality.

Tests cover:
- k=0 (empty list)
- k=1 (single list)
- Uneven lengths
- Lists with duplicates
- All-empty lists
- Mixed empty and non-empty lists
"""

import pytest
from app.k_way_merge import (
    ListNode,
    merge_k_lists_min_heap,
    merge_k_lists_brute_force,
    list_to_array,
    array_to_list,
)


class TestKWayMergeMinHeap:
    """Test cases for min-heap based k-way merge."""
    
    def test_k_zero_empty_list(self):
        """Test with k=0 (empty list of lists)."""
        result = merge_k_lists_min_heap([])
        assert result is None
    
    def test_all_none_lists(self):
        """Test with all None entries in the lists."""
        result = merge_k_lists_min_heap([None, None, None])
        assert result is None
    
    def test_k_single_list(self):
        """Test with k=1 (single list)."""
        lists = [array_to_list([1, 2, 3, 4, 5])]
        result = merge_k_lists_min_heap(lists)
        assert list_to_array(result) == [1, 2, 3, 4, 5]
    
    def test_two_sorted_lists(self):
        """Test merging two sorted lists."""
        lists = [
            array_to_list([1, 3, 5]),
            array_to_list([2, 4, 6])
        ]
        result = merge_k_lists_min_heap(lists)
        assert list_to_array(result) == [1, 2, 3, 4, 5, 6]
    
    def test_uneven_lengths(self):
        """Test with lists of varying lengths."""
        lists = [
            array_to_list([1]),
            array_to_list([2, 3, 4, 5]),
            array_to_list([6, 7, 8, 9, 10])
        ]
        result = merge_k_lists_min_heap(lists)
        assert list_to_array(result) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    def test_lists_with_duplicates(self):
        """Test merging lists that contain duplicate values."""
        lists = [
            array_to_list([1, 2, 3]),
            array_to_list([2, 3, 4]),
            array_to_list([3, 4, 5])
        ]
        result = merge_k_lists_min_heap(lists)
        assert list_to_array(result) == [1, 2, 2, 3, 3, 3, 4, 4, 5]
    
    def test_mixed_empty_and_non_empty(self):
        """Test with mix of empty and non-empty lists."""
        lists = [
            array_to_list([1, 3, 5]),
            None,
            array_to_list([2, 4, 6]),
            None,
            array_to_list([7, 8, 9])
        ]
        result = merge_k_lists_min_heap(lists)
        assert list_to_array(result) == [1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    def test_single_element_each_list(self):
        """Test with single element in each of k lists."""
        lists = [
            array_to_list([5]),
            array_to_list([2]),
            array_to_list([8]),
            array_to_list([1])
        ]
        result = merge_k_lists_min_heap(lists)
        assert list_to_array(result) == [1, 2, 5, 8]
    
    def test_already_sorted_single_list(self):
        """Test with a single list that's already sorted."""
        lists = [array_to_list([1, 2, 3])]
        result = merge_k_lists_min_heap(lists)
        assert list_to_array(result) == [1, 2, 3]
    
    def test_reverse_sorted_single_list(self):
        """Test with a single list in reverse order."""
        lists = [array_to_list([3, 2, 1])]
        result = merge_k_lists_min_heap(lists)
        # Note: the implementation assumes input lists are sorted
        assert list_to_array(result) == [3, 2, 1]


class TestKWayMergeBruteForce:
    """Test cases for brute-force k-way merge."""
    
    def test_k_zero_empty_list(self):
        """Test with k=0 (empty list of lists)."""
        result = merge_k_lists_brute_force([])
        assert result is None
    
    def test_all_none_lists(self):
        """Test with all None entries."""
        result = merge_k_lists_brute_force([None, None, None])
        assert result is None
    
    def test_k_single_list(self):
        """Test with k=1 (single list)."""
        lists = [array_to_list([1, 2, 3, 4, 5])]
        result = merge_k_lists_brute_force(lists)
        assert list_to_array(result) == [1, 2, 3, 4, 5]
    
    def test_two_sorted_lists(self):
        """Test merging two sorted lists."""
        lists = [
            array_to_list([1, 3, 5]),
            array_to_list([2, 4, 6])
        ]
        result = merge_k_lists_brute_force(lists)
        assert list_to_array(result) == [1, 2, 3, 4, 5, 6]
    
    def test_uneven_lengths(self):
        """Test with lists of varying lengths."""
        lists = [
            array_to_list([1]),
            array_to_list([2, 3, 4, 5]),
            array_to_list([6, 7, 8, 9, 10])
        ]
        result = merge_k_lists_brute_force(lists)
        assert list_to_array(result) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    def test_lists_with_duplicates(self):
        """Test merging lists that contain duplicate values."""
        lists = [
            array_to_list([1, 2, 3]),
            array_to_list([2, 3, 4]),
            array_to_list([3, 4, 5])
        ]
        result = merge_k_lists_brute_force(lists)
        assert list_to_array(result) == [1, 2, 2, 3, 3, 3, 4, 4, 5]
    
    def test_mixed_empty_and_non_empty(self):
        """Test with mix of empty and non-empty lists."""
        lists = [
            array_to_list([1, 3, 5]),
            None,
            array_to_list([2, 4, 6]),
            None,
            array_to_list([7, 8, 9])
        ]
        result = merge_k_lists_brute_force(lists)
        assert list_to_array(result) == [1, 2, 3, 4, 5, 6, 7, 8, 9]


class TestCorrectnessValidation:
    """Test that both approaches produce the same results."""
    
    def test_compare_approaches_k_zero(self):
        """Compare min-heap vs brute-force for k=0."""
        min_heap_result = merge_k_lists_min_heap([])
        brute_result = merge_k_lists_brute_force([])
        assert list_to_array(min_heap_result) == list_to_array(brute_result)
    
    def test_compare_approaches_single_list(self):
        """Compare min-heap vs brute-force for single list."""
        lists = [array_to_list([1, 3, 5, 7, 9])]
        min_heap_result = merge_k_lists_min_heap(lists)
        brute_result = merge_k_lists_brute_force(lists)
        assert list_to_array(min_heap_result) == list_to_array(brute_result)
    
    def test_compare_approaches_multiple_lists(self):
        """Compare min-heap vs brute-force for multiple lists."""
        lists = [
            array_to_list([1, 4, 7]),
            array_to_list([2, 5, 8]),
            array_to_list([3, 6, 9])
        ]
        min_heap_result = merge_k_lists_min_heap(lists)
        brute_result = merge_k_lists_brute_force(lists)
        assert list_to_array(min_heap_result) == list_to_array(brute_result)
    
    def test_compare_approaches_with_duplicates(self):
        """Compare min-heap vs brute-force with duplicates."""
        lists = [
            array_to_list([1, 2, 2]),
            array_to_list([2, 3, 3]),
            array_to_list([3, 4, 4])
        ]
        min_heap_result = merge_k_lists_min_heap(lists)
        brute_result = merge_k_lists_brute_force(lists)
        assert list_to_array(min_heap_result) == list_to_array(brute_result)
    
    def test_compare_approaches_uneven_lengths(self):
        """Compare min-heap vs brute-force for uneven lengths."""
        lists = [
            array_to_list([1]),
            array_to_list([2, 3]),
            array_to_list([4, 5, 6]),
        ]
        min_heap_result = merge_k_lists_min_heap(lists)
        brute_result = merge_k_lists_brute_force(lists)
        assert list_to_array(min_heap_result) == list_to_array(brute_result)


class TestHelperFunctions:
    """Test helper functions for list/array conversion."""
    
    def test_array_to_list_empty(self):
        """Test converting empty array to list."""
        result = array_to_list([])
        assert result is None
    
    def test_list_to_array_empty(self):
        """Test converting empty list to array."""
        result = list_to_array(None)
        assert result == []
    
    def test_array_list_roundtrip(self):
        """Test array -> list -> array conversion."""
        original = [1, 2, 3, 4, 5]
        linked = array_to_list(original)
        result = list_to_array(linked)
        assert result == original
