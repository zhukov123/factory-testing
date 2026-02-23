"""LRU Cache implementation using hash map + doubly linked list."""
from typing import Dict, Optional


class Node:
    """Doubly linked list node."""
    
    def __init__(self, key: int = 0, value: int = 0):
        self.key = key
        self.value = value
        self.prev: Optional[Node] = None
        self.next: Optional[Node] = None


class LRUCache:
    """LRU Cache implementation using hash map + doubly linked list.
    
    Supports get(key) and put(key, value) operations in O(1) time.
    Evicts the least recently used entry when capacity is exceeded.
    """
    
    def __init__(self, capacity: int):
        """Initialize LRU cache with given capacity.
        
        Args:
            capacity: Maximum number of entries the cache can hold.
        """
        self.capacity = capacity
        self.cache: Dict[int, Node] = {}
        
        # Sentinel nodes for head and tail
        # head -> points to most recently used node
        # tail -> points to least recently used node
        self.head = Node()  # MRU side (dummy)
        self.tail = Node()  # LRU side (dummy)
        self.head.next = self.tail
        self.tail.prev = self.head
    
    def _remove_node(self, node: Node) -> None:
        """Remove a node from the linked list.
        
        Args:
            node: Node to remove from its current position.
        """
        node.prev.next = node.next
        node.next.prev = node.prev
    
    def _add_to_front(self, node: Node) -> None:
        """Add a new node right after head (MRU position).
        
        Args:
            node: Node to add to the front of the list.
        """
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node
    
    def _move_to_front(self, node: Node) -> None:
        """Move an existing node to the front (MRU position).
        
        Args:
            node: Node to move to the front.
        """
        self._remove_node(node)
        self._add_to_front(node)
    
    def _pop_tail(self) -> Node:
        """Remove and return the LRU node (tail.prev).
        
        Returns:
            The least recently used node.
        """
        lru_node = self.tail.prev
        self._remove_node(lru_node)
        return lru_node
    
    def get(self, key: int) -> int:
        """Get value by key. If key exists, moves it to MRU position.
        
        Args:
            key: The key to look up.
            
        Returns:
            The value associated with the key, or -1 if not found.
        """
        if key not in self.cache:
            return -1
        
        node = self.cache[key]
        self._move_to_front(node)
        return node.value
    
    def put(self, key: int, value: int) -> None:
        """Insert or update a key-value pair.
        
        If the key already exists, update its value and move to MRU position.
        If the cache is at capacity, evict the LRU entry before adding.
        
        Args:
            key: The key to insert or update.
            value: The value to associate with the key.
        """
        if key in self.cache:
            # Update existing node
            node = self.cache[key]
            node.value = value
            self._move_to_front(node)
        else:
            # Create new node
            new_node = Node(key, value)
            self.cache[key] = new_node
            self._add_to_front(new_node)
            
            # Check capacity and evict if necessary
            if len(self.cache) > self.capacity:
                lru_node = self._pop_tail()
                del self.cache[lru_node.key]
    
    def __len__(self) -> int:
        """Return the number of entries in the cache."""
        return len(self.cache)
