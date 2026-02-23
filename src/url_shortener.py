"""
In-Memory URL Shortener Service

A tiny URL shortening service that lives entirely in memory. Provides deterministic
short codes for repeated long URLs with O(1) average lookups.

Architecture:
- UrlStore: Storage abstraction with bidirectional mapping
- UrlShortener: Service layer with encoding and collision handling
"""

import hashlib
from abc import ABC, abstractmethod
from typing import Optional


# Base62 alphabet for encoding
BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
CODE_LENGTH = 8


class UrlStore(ABC):
    """Abstract storage interface for URL shortener.
    
    Provides bidirectional mapping between short codes and long URLs.
    """
    
    @abstractmethod
    def get_url(self, code: str) -> Optional[str]:
        """Get long URL for a given short code."""
        pass
    
    @abstractmethod
    def get_code(self, long_url: str) -> Optional[str]:
        """Get short code for a given long URL."""
        pass
    
    @abstractmethod
    def set_mapping(self, code: str, long_url: str) -> None:
        """Store a bidirectional mapping between code and URL."""
        pass


class InMemoryUrlStore(UrlStore):
    """In-memory implementation of UrlStore using Python dicts."""
    
    def __init__(self):
        self._code_to_url: dict[str, str] = {}
        self._url_to_code: dict[str, str] = {}
    
    def get_url(self, code: str) -> Optional[str]:
        return self._code_to_url.get(code)
    
    def get_code(self, long_url: str) -> Optional[str]:
        return self._url_to_code.get(long_url)
    
    def set_mapping(self, code: str, long_url: str) -> None:
        self._code_to_url[code] = long_url
        self._url_to_code[long_url] = code
    
    def __len__(self) -> int:
        return len(self._code_to_url)


def _normalize_url(url: str) -> str:
    """Normalize URL for consistent encoding."""
    return url.strip()


def _sha256_digest(data: str) -> bytes:
    """Generate SHA256 hash of input data."""
    return hashlib.sha256(data.encode('utf-8')).digest()


def _encode_base62(digest: bytes, length: int = CODE_LENGTH) -> str:
    """Encode a hash digest to a Base62 string of specified length."""
    # Convert first few bytes to an integer
    # Use only enough bytes to represent the target length
    num = int.from_bytes(digest[:8], byteorder='big')
    
    result = []
    for _ in range(length):
        num, remainder = divmod(num, 62)
        result.append(BASE62_ALPHABET[remainder])
    
    return ''.join(reversed(result))


def _generate_code(long_url: str, counter: int = 0) -> str:
    """Generate a deterministic short code for a URL.
    
    Args:
        long_url: The URL to encode
        counter: Collision counter (0 for first attempt)
    
    Returns:
        A Base62-encoded short code
    """
    # Include counter in hash for collision resolution
    data_to_hash = f"{long_url}:{counter}" if counter > 0 else long_url
    digest = _sha256_digest(data_to_hash)
    return _encode_base62(digest)


class UrlShortener:
    """URL shortener service with deterministic encoding and collision handling."""
    
    def __init__(self, store: UrlStore, code_length: int = CODE_LENGTH):
        self._store = store
        self._code_length = code_length
    
    def create_short_url(self, long_url: str) -> str:
        """Create a short URL for the given long URL.
        
        If the URL was previously shortened, returns the existing code.
        Handles collisions by incrementing a counter and rehashing.
        
        Args:
            long_url: The URL to shorten
            
        Returns:
            A short code string
            
        Raises:
            ValueError: If the URL is empty or invalid
        """
        # Validate and normalize
        normalized = _normalize_url(long_url)
        if not normalized:
            raise ValueError("URL cannot be empty")
        
        if not normalized.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        
        # Check for existing code (determinism)
        existing_code = self._store.get_code(normalized)
        if existing_code:
            return existing_code
        
        # Generate new code with collision handling
        counter = 0
        while True:
            code = _generate_code(normalized, counter)
            
            # Check if code is unused
            existing_url = self._store.get_url(code)
            if existing_url is None:
                # Free slot - use it
                self._store.set_mapping(code, normalized)
                return code
            elif existing_url == normalized:
                # Same URL already stored with different code - rare but possible
                # Return the existing code for this URL
                return self._store.get_code(normalized)
            else:
                # Collision - different URL already uses this code
                counter += 1
                if counter > 100:
                    raise RuntimeError("Failed to generate unique code after 100 attempts")
    
    def resolve_short_url(self, code: str) -> Optional[str]:
        """Resolve a short code back to its long URL.
        
        Args:
            code: The short code to resolve
            
        Returns:
            The original long URL, or None if code is not found
        """
        if not code:
            return None
        return self._store.get_url(code)


# Convenience function for quick usage
def create_shortener() -> tuple[UrlShortener, UrlStore]:
    """Create a new URL shortener with in-memory storage."""
    store = InMemoryUrlStore()
    return UrlShortener(store), store
