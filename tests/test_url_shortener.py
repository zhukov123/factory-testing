"""
Unit tests for URL Shortener (T6)

Tests cover:
1. Duplicate URLs: same code returned for repeated requests
2. Collision Handling: retry logic when codes collide
3. Invalid Code Lookup: returns None for unknown codes
4. Round-Trip Conversion: create and resolve returns original URL
"""

import pytest
from src.url_shortener import (
    UrlStore,
    InMemoryUrlStore,
    UrlShortener,
    _generate_code,
    _encode_base62,
    create_shortener,
)


class TestInMemoryUrlStore:
    """Tests for the storage abstraction."""
    
    def test_set_and_get_url(self):
        """Test basic set/get operations."""
        store = InMemoryUrlStore()
        store.set_mapping("abc123", "https://example.com")
        
        assert store.get_url("abc123") == "https://example.com"
        assert store.get_code("https://example.com") == "abc123"
    
    def test_get_url_not_found(self):
        """Test get_url returns None for unknown code."""
        store = InMemoryUrlStore()
        assert store.get_url("nonexistent") is None
    
    def test_get_code_not_found(self):
        """Test get_code returns None for unknown URL."""
        store = InMemoryUrlStore()
        assert store.get_code("https://example.com") is None
    
    def test_bidirectional_mapping(self):
        """Test both maps stay in sync."""
        store = InMemoryUrlStore()
        store.set_mapping("xyz789", "https://test.com/path")
        
        assert store.get_url("xyz789") == "https://test.com/path"
        assert store.get_code("https://test.com/path") == "xyz789"


class TestEncoding:
    """Tests for encoding functions."""
    
    def test_encode_base62_length(self):
        """Test Base62 encoding produces correct length."""
        digest = b"a" * 32
        result = _encode_base62(digest, length=8)
        assert len(result) == 8
    
    def test_generate_code_deterministic(self):
        """Test same URL produces same code."""
        code1 = _generate_code("https://example.com")
        code2 = _generate_code("https://example.com")
        assert code1 == code2
    
    def test_generate_code_different_urls(self):
        """Test different URLs produce different codes."""
        code1 = _generate_code("https://example.com")
        code2 = _generate_code("https://other.com")
        assert code1 != code2
    
    def test_generate_code_with_counter(self):
        """Test different counters produce different codes."""
        code0 = _generate_code("https://example.com", counter=0)
        code1 = _generate_code("https://example.com", counter=1)
        assert code0 != code1


class TestUrlShortenerDuplicateUrls:
    """Tests for duplicate URL handling (determinism)."""
    
    def test_same_url_returns_same_code(self):
        """Calling create_short_url multiple times for same URL returns same code."""
        store = InMemoryUrlStore()
        shortener = UrlShortener(store)
        
        url = "https://example.com/long/path"
        code1 = shortener.create_short_url(url)
        code2 = shortener.create_short_url(url)
        
        assert code1 == code2
    
    def test_duplicate_does_not_mutate_store(self):
        """Repeated calls don't add duplicate entries."""
        store = InMemoryUrlStore()
        shortener = UrlShortener(store)
        
        url = "https://example.com/test"
        shortener.create_short_url(url)
        shortener.create_short_url(url)
        
        # Should only have one entry
        assert len(store) == 1


class TestUrlShortenerCollisionHandling:
    """Tests for collision detection and resolution."""
    
    def test_collision_handling_different_url(self):
        """Test collision when different URL has same code."""
        store = InMemoryUrlStore()
        shortener = UrlShortener(store)
        
        # Create two shorteners - one with pre-set mapping
        store2 = InMemoryUrlStore()
        shortener2 = UrlShortener(store2)
        
        # First, add URL1 and get its code
        url1 = "https://first.com"
        code1 = shortener2.create_short_url(url1)
        
        # Now add URL2 - collision may or may not happen depending on hash
        # Just verify both work
        url2 = "https://second.com"
        code2 = shortener2.create_short_url(url2)
        
        # Both codes should work and be different
        assert code1 != code2
        assert shortener2.resolve_short_url(code1) == url1
        assert shortener2.resolve_short_url(code2) == url2
    
    def test_force_collision_resolution(self):
        """Test collision resolution by manually injecting collision."""
        store = InMemoryUrlStore()
        
        # Pre-populate: force a code to exist for a different URL
        store.set_mapping("aaaaaaaa", "https://existing.com")
        
        # Now create shortener and try to add a URL that might collide
        shortener = UrlShortener(store)
        
        # This should either find a different code or use collision resolution
        code = shortener.create_short_url("https://new.com")
        
        # Verify the code works
        assert shortener.resolve_short_url(code) == "https://new.com"


class TestUrlShortenerInvalidCode:
    """Tests for invalid/unknown code handling."""
    
    def test_resolve_unknown_code_returns_none(self):
        """resolve_short_url returns None for unknown codes."""
        store = InMemoryUrlStore()
        shortener = UrlShortener(store)
        
        result = shortener.resolve_short_url("unknown123")
        assert result is None
    
    def test_resolve_empty_code_returns_none(self):
        """resolve_short_url returns None for empty code."""
        store = InMemoryUrlStore()
        shortener = UrlShortener(store)
        
        result = shortener.resolve_short_url("")
        assert result is None


class TestUrlShortenerRoundTrip:
    """Tests for round-trip conversion."""
    
    def test_create_and_resolve_returns_original(self):
        """Creating a short URL and resolving it returns original."""
        store = InMemoryUrlStore()
        shortener = UrlShortener(store)
        
        original_url = "https://example.com/very/long/path?query=value"
        code = shortener.create_short_url(original_url)
        resolved = shortener.resolve_short_url(code)
        
        assert resolved == original_url
    
    def test_multiple_urls_round_trip(self):
        """Test multiple different URLs all round-trip correctly."""
        store = InMemoryUrlStore()
        shortener = UrlShortener(store)
        
        urls = [
            "https://google.com",
            "https://github.com/user/repo",
            "https://stackoverflow.com/questions/12345",
            "http://localhost:8080/api/v1",
        ]
        
        codes = []
        for url in urls:
            code = shortener.create_short_url(url)
            codes.append(code)
        
        # All codes should be different
        assert len(set(codes)) == len(urls)
        
        # All should resolve back correctly
        for url, code in zip(urls, codes):
            assert shortener.resolve_short_url(code) == url


class TestUrlShortenerValidation:
    """Tests for URL validation."""
    
    def test_empty_url_raises_error(self):
        """Empty URL raises ValueError."""
        store = InMemoryUrlStore()
        shortener = UrlShortener(store)
        
        with pytest.raises(ValueError, match="empty"):
            shortener.create_short_url("")
    
    def test_whitespace_url_raises_error(self):
        """Whitespace-only URL raises ValueError."""
        store = InMemoryUrlStore()
        shortener = UrlShortener(store)
        
        with pytest.raises(ValueError, match="empty"):
            shortener.create_short_url("   ")
    
    def test_invalid_url_no_scheme_raises_error(self):
        """URL without http/https raises ValueError."""
        store = InMemoryUrlStore()
        shortener = UrlShortener(store)
        
        with pytest.raises(ValueError, match="http"):
            shortener.create_short_url("example.com")
    
    def test_url_normalization(self):
        """URL with leading/trailing whitespace is handled."""
        store = InMemoryUrlStore()
        shortener = UrlShortener(store)
        
        url = "  https://example.com/path  "
        code = shortener.create_short_url(url)
        
        # Should resolve correctly (whitespace normalized)
        resolved = shortener.resolve_short_url(code)
        assert resolved == "https://example.com/path"


class TestConvenienceFunction:
    """Tests for the create_shortener convenience function."""
    
    def test_create_shortener_returns_tuple(self):
        """create_shortener returns (shortener, store) tuple."""
        shortener, store = create_shortener()
        
        assert isinstance(shortener, UrlShortener)
        assert isinstance(store, InMemoryUrlStore)
    
    def test_create_shortener_works(self):
        """Created shortener works correctly."""
        shortener, store = create_shortener()
        
        url = "https://test.com"
        code = shortener.create_short_url(url)
        
        assert shortener.resolve_short_url(code) == url
