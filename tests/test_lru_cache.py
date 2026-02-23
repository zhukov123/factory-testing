"""Unit tests for LRU Cache implementation."""
import pytest
from src.lru_cache import LRUCache


class TestLRUCacheBasicOperations:
    """Test basic get and put operations."""
    
    def test_get_empty_cache_returns_minus_one(self):
        """Test that get on empty cache returns -1."""
        cache = LRUCache(capacity=3)
        assert cache.get(1) == -1
    
    def test_put_and_get_roundtrip(self):
        """Test put and get round-trip works correctly."""
        cache = LRUCache(capacity=3)
        cache.put(1, 100)
        assert cache.get(1) == 100


class TestLRUCacheUpdateExistingKey:
    """Test updating existing key."""
    
    def test_update_existing_key(self):
        """Update value of existing key, verify new value is returned."""
        cache = LRUCache(capacity=3)
        cache.put(1, 100)
        cache.put(1, 200)  # Update existing key
        assert cache.get(1) == 200
    
    def test_update_moves_to_mru(self):
        """Verify key is moved to MRU position after update."""
        cache = LRUCache(capacity=3)
        cache.put(1, 100)
        cache.put(2, 200)
        cache.put(3, 300)
        
        # Update key 1 (making it MRU)
        cache.put(1, 1000)
        
        # Add key 4, which should evict key 2 (LRU), not key 1
        cache.put(4, 400)
        
        # Key 1 should still be accessible
        assert cache.get(1) == 1000
        # Key 2 should be evicted
        assert cache.get(2) == -1


class TestLRUCacheEvictionOrder:
    """Test eviction order."""
    
    def test_eviction_order(self):
        """Fill cache to capacity, add one more, verify LRU is evicted."""
        cache = LRUCache(capacity=3)
        cache.put(1, 100)
        cache.put(2, 200)
        cache.put(3, 300)
        
        # Add one more - should evict key 1 (LRU)
        cache.put(4, 400)
        
        # Key 1 should be evicted
        assert cache.get(1) == -1
        # Others should still be accessible
        assert cache.get(2) == 200
        assert cache.get(3) == 300
        assert cache.get(4) == 400
    
    def test_evicted_item_not_accessible(self):
        """Verify evicted item is no longer accessible."""
        cache = LRUCache(capacity=2)
        cache.put(1, 100)
        cache.put(2, 200)
        
        # Add another to trigger eviction
        cache.put(3, 300)
        
        # Original LRU should be gone
        assert cache.get(1) == -1
        assert cache.get(2) == 200
        assert cache.get(3) == 300


class TestLRUCacheRepeatedReads:
    """Test repeated reads behavior."""
    
    def test_repeated_gets(self):
        """Access same key multiple times via get()."""
        cache = LRUCache(capacity=3)
        cache.put(1, 100)
        cache.put(2, 200)
        cache.put(3, 300)
        
        # Repeatedly access key 1
        cache.get(1)
        cache.get(1)
        cache.get(1)
        
        # Add key 4 - should evict key 2 (LRU), not key 1
        cache.put(4, 400)
        
        # Key 1 should survive (was accessed most recently)
        assert cache.get(1) == 100
        # Key 2 should be evicted
        assert cache.get(2) == -1
        # Others should be intact
        assert cache.get(3) == 300
        assert cache.get(4) == 400


class TestLRUCacheCapacityOne:
    """Test capacity=1 edge case."""
    
    def test_capacity_one(self):
        """Test cache with capacity 1."""
        cache = LRUCache(capacity=1)
        
        cache.put(1, 100)
        assert cache.get(1) == 100
        
        # Add item B - should evict A
        cache.put(2, 200)
        
        # A should be evicted
        assert cache.get(1) == -1
        # B should be present
        assert cache.get(2) == 200
    
    def test_capacity_one_update(self):
        """Test updating the only item in capacity 1 cache."""
        cache = LRUCache(capacity=1)
        
        cache.put(1, 100)
        cache.put(1, 200)  # Update, not add
        
        # Should still have only 1 item, with updated value
        assert cache.get(1) == 200
        assert len(cache) == 1


class TestLRUCacheMoveToMRU:
    """Test move to MRU on various operations."""
    
    def test_get_moves_to_mru(self):
        """Accessing a key via get should move it to MRU."""
        cache = LRUCache(capacity=3)
        cache.put(1, 100)
        cache.put(2, 200)
        cache.put(3, 300)
        
        # Access key 1 via get (moves to MRU)
        assert cache.get(1) == 100
        
        # Add key 4 - should evict key 2 (the new LRU), not key 1
        cache.put(4, 400)
        
        # Key 1 should survive
        assert cache.get(1) == 100
        # Key 2 should be evicted
        assert cache.get(2) == -1
    
    def test_put_with_existing_key_moves_to_mru(self):
        """Put to existing key should move it to MRU."""
        cache = LRUCache(capacity=3)
        cache.put(1, 100)
        cache.put(2, 200)
        
        # Put key 1 again (moves to MRU)
        cache.put(1, 1000)
        
        # Order is now: [1, 2], LRU=2
        
        # Add key 3 - still at capacity (3 items), no eviction yet
        # Order becomes [3, 1, 2], LRU=2
        cache.put(3, 300)
        
        # Don't call get() - that changes order!
        # Instead add key 4 - should evict key 2 (the LRU)
        cache.put(4, 400)
        
        # Key 1 should survive (was MRU after put(1, 1000))
        assert cache.get(1) == 1000
        # Key 2 should be evicted (was LRU)
        assert cache.get(2) == -1
        assert cache.get(3) == 300
        assert cache.get(4) == 400


class TestLRUCacheEdgeCases:
    """Test additional edge cases."""
    
    def test_empty_cache_get(self):
        """Test get on empty cache."""
        cache = LRUCache(capacity=3)
        assert cache.get(999) == -1
    
    def test_len_method(self):
        """Test __len__ method."""
        cache = LRUCache(capacity=5)
        assert len(cache) == 0
        
        cache.put(1, 100)
        assert len(cache) == 1
        
        cache.put(2, 200)
        cache.put(3, 300)
        assert len(cache) == 3
    
    def test_capacity_never_exceeded(self):
        """Verify cache never exceeds capacity."""
        cache = LRUCache(capacity=2)
        
        for i in range(10):
            cache.put(i, i * 10)
        
        # Should only have 2 items
        assert len(cache) == 2
    
    def test_overwrite_lru_after_access(self):
        """After accessing LRU item, it becomes MRU and survives."""
        cache = LRUCache(capacity=3)
        cache.put(1, 100)
        cache.put(2, 200)
        cache.put(3, 300)
        
        # Access the LRU item (key 1)
        cache.get(1)
        
        # Now add key 4 - should evict key 2 (which is now LRU)
        cache.put(4, 400)
        
        # Key 1 should survive
        assert cache.get(1) == 100
        # Key 2 should be evicted
        assert cache.get(2) == -1
