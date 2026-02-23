# T6: In-Memory URL Shortener - Architecture Plan

## Overview
Build a tiny URL shortening service that lives entirely in memory. The service exposes two operations — `createShortUrl(long_url)` and `resolveShortUrl(code)` — backed by fast maps, deterministic encoding, and collision-safe guardrails so that repeated requests for the same long URL return the same short code and lookups stay O(1) on average.

## Requirements Recap
- Deterministic short codes for repeated long URLs
- Bi-directional mapping (`createShortUrl` and `resolveShortUrl`)
- Collision-safe: encoded values must never point to the wrong long URL
- Modular storage so we can swap the backing store without touching the core logic
- O(1) average lookups via map/dict semantics

## Architecture

### Storage Abstraction
Define a `UrlStore` contract that keeps two maps:
1. `code_to_url: Dict[str, str]`
2. `url_to_code: Dict[str, str]`

The interface exposes methods such as `get_url(code: str) -> Optional[str]`, `get_code(long_url: str) -> Optional[str]`, and `set_mapping(code: str, long_url: str)`.

The default implementation (`InMemoryUrlStore`) uses Python dicts and provides atomic lookups/assignments. Later we can swap in a Redis or SQLite implementation by replacing this class without touching the encoding/service layer.

### Service Layer
Create a `UrlShortener` class that takes a `UrlStore` instance as a dependency. It will expose:
- `create_short_url(long_url: str) -> str`
- `resolve_short_url(code: str) -> Optional[str]`

`create_short_url` will:
1. Sanitize/validate the incoming URL (strip whitespace, ensure non-empty)
2. Check `url_to_code` map first — if already present, return the existing code (determinism requirement)
3. Otherwise, generate a code via the encoding strategy below
4. If the generated code collides (i.e., `code_to_url` holds a different long URL), iterate with an appended counter/salt until an unused code emerges
5. Persist both forward and reverse mappings

`resolve_short_url` simply forwards to the store map and returns `None` for unknown codes.

### Encoding Strategy
- Canonical deterministic input: feed the normalized long URL into `hashlib.sha256` to get a stable digest
- Convert the digest to a large integer and encode it in Base62 (characters `0-9`, `a-z`, `A-Z`)
- Truncate to a configurable length (e.g., 8 characters) for readability
- For collision resolution, append a small counter (`long_url + counter`) before hashing and re-encode; this keeps codes short while ensuring uniqueness
- Store metadata (counter used) optionally if we need to reproduce the code for debugging

### Collision Handling & Determinism
- After generating a candidate code, check if the store already maps it. If it maps to the same long URL, we’re done.
- If it maps to a different long URL, increment the collision counter (starting at 0) and rehash (`sha + counter`), guaranteeing eventual uniqueness while keeping lookups O(1) because the loop stops as soon as a free slot is found.
- Since `url_to_code` is checked first, repeated calls for the same long URL immediately return the stored code without re-encoding.

### API / Usage
```python
store = InMemoryUrlStore()
shortener = UrlShortener(store)

code = shortener.create_short_url("https://example.com/paths?query=1")
long_url = shortener.resolve_short_url(code)
```

Provide helper functions/commands for potential CLI or HTTP wrappers in a later ticket.

## Test Plan
Add unit tests under `tests/test_url_shortener.py` covering the acceptance criteria:
1. **Duplicate URLs**: calling `create_short_url` multiple times for the same long URL returns the same code and does not mutate the store unexpectedly.
2. **Collision Handling**: inject a fake store entry for a different long URL but the same generated code, then ensure the shortener retries and the final code maps correctly.
3. **Invalid Code Lookup**: `resolve_short_url` returns `None` (or raises a well-defined exception) for unknown codes.
4. **Round-Trip Conversion**: creating a short URL and immediately resolving it returns the original long URL.

Also plan to test the storage abstraction itself (e.g., direct `set/get` round trips and that both dicts stay in sync).

## File Structure
```
factory-testing/
├── app/                          # existing FastAPI app
├── docs/
│   └── T6-plan.md                # this document
├── src/
│   └── url_shortener.py          # new service + storage definitions
├── tests/
│   └── test_url_shortener.py     # unit tests covering acceptance criteria
└── ...
```

## Implementation Notes
- Keep everything pure-Python with type hints so it’s easy to plug into either a CLI script or a FastAPI route later.
- Favor `dict` lookups for O(1) average performance, and isolate all store interactions behind the `UrlStore` interface.
- Document any assumptions (code length, base alphabet) inside the module so downstream users can tune them.
- Consider optional logging to aid in debugging collisions and retries.
