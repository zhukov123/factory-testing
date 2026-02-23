# T7: LRU Cache Implementation - Architecture Plan

## Overview
Implement a Least Recently Used (LRU) cache using a combination of a hash map (dictionary) and a doubly linked list. This classic data structure problem demonstrates efficient pointer manipulation and maintains O(1) time complexity for both get and put operations.

## Requirements Recap
- Support `get(key)` and `put(key, value)` operations in O(1) time
- Evict the least recently used entry when capacity is exceeded
- Move key to most-recent position on access (get) and update (put)
- Unit tests covering: update existing key, eviction order, repeated reads, and capacity=1 edge case

## Architecture

### Data Structure Design

#### Doubly Linked List
- **Purpose**: Track access order - most recently used (MRU) at one end, least recently used (LRU) at the other
- **Implementation**: Custom `Node` class with `key`, `value`, `prev`, and `next` attributes
- **Head and Tail**: Use sentinel/dummy nodes to simplify edge case handling
  - `head` → points to most recently used node
  - `tail` → points to least recently used node

#### Hash Map (Dictionary)
- **Purpose**: O(1) key lookup
- **Storage**: `cache: Dict[key, Node]` - maps keys to their corresponding Node objects

#### Operation Principles
1. **Most Recently Used (MRU)**: Near the `head` (front of list)
2. **Least Recently Used (LRU)**: Near the `tail` (end of list)
3. On each access (get/put), move the accessed node to the front (MRU position)

### Class Design: LRUCache

```python
class Node:
    """Doubly linked list node."""
    def __init__(self, key: int = 0, value: int = 0):
        self.key = key
        self.value = value
        self.prev: Optional[Node] = None
        self.next: Optional[Node] = None

class LRUCache:
    """LRU Cache implementation using hash map + doubly linked list."""
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache: Dict[int, Node] = {}
        
        # Sentinel nodes for head and tail
        self.head = Node()  # MRU side
        self.tail = Node()  # LRU side
        self.head.next = self.tail
        self.tail.prev = self.head
    
    def get(self, key: int) -> int:
        """Get value by key, moving it to MRU position."""
        # O(1) lookup
        # Move node to front if found
        # Return -1 if not found
    
    def put(self, key: int, value: int):
        """Insert or update key-value pair."""
        # Check if key exists:
        #   - If yes: update value and move to MRU position
        #   - If no: create new node
        #         - If at capacity: remove LRU node (tail.prev)
        #         - Add new node to MRU position
```

### Helper Methods

1. **`_move_to_front(node: Node)`**: Remove node from current position and add to front (MRU)
2. **`_add_to_front(node: Node)`**: Add new node right after head (MRU position)
3. **`_remove_node(node: Node)`**: Remove node from linked list (internal helper)
4. **`_pop_tail()`**: Remove and return the LRU node (tail.prev)

### Time Complexity Analysis
| Operation | Time Complexity |
|-----------|----------------|
| get(key)  | O(1)           |
| put(key, value) | O(1)    |
| Eviction  | O(1)           |

All operations are O(1) because:
- Hash map provides O(1) lookup
- Doubly linked list provides O(1) insertion/removal when node reference is available

### Edge Cases to Handle
1. **Capacity = 1**: Ensure correct eviction when only one slot exists
2. **Repeated gets**: Moving same node to front multiple times should be idempotent
3. **Update existing key**: Should move to MRU, not add duplicate
4. **Access LRU item**: After access, it becomes MRU and should not be evicted next
5. **Empty cache**: get() returns -1, put() works normally

## Test Plan

### Unit Tests (tests/test_lru_cache.py)

1. **Basic Operations**
   - Test get on empty cache returns -1
   - Test put and get round-trip

2. **Update Existing Key**
   - Update value of existing key, verify new value is returned
   - Verify key is moved to MRU position

3. **Eviction Order**
   - Fill cache to capacity
   - Add one more item, verify LRU is evicted
   - Verify evicted item is no longer accessible

4. **Repeated Reads**
   - Access same key multiple times via get()
   - Verify order: repeated-read item should survive longer than untouched items

5. **Capacity = 1 Edge Case**
   - Create cache with capacity 1
   - Add item A, then add item B
   - Verify A is evicted and B remains
   - Verify get(A) returns -1, get(B) returns correct value

6. **Move to MRU on Put**
   - Put key A, then key B, then access A again
   - Add key C (triggering eviction)
   - Verify A survives (was accessed more recently than B)

## File Structure
```
factory-testing/
├── app/                          # existing FastAPI app
├── docs/
│   └── T7-plan.md                # this document
├── src/
│   └── lru_cache.py              # LRUCache and Node classes
├── tests/
│   └── test_lru_cache.py         # unit tests covering acceptance criteria
└── ...
```

## Implementation Notes

- Use Python's built-in `collections.OrderedDict` internally? 
  - **Decision**: Implement custom doubly linked list to demonstrate the classic algorithm (as per interview focus)
  - OrderedDict maintains insertion order but doesn't track access order by default for LRU semantics

- Type hints: Use `int` for keys and values (can generalize to generics later if needed)

- Thread safety: Not in scope for this ticket, but can add locks if needed

- Consider adding `__len__` method for convenience

- The implementation follows the classic LeetCode LRU Cache pattern