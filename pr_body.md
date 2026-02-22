## Changes

### 1. Added RateLimiter.Events Import
- Added `using RateLimiter.Events;` to all rate limiter implementations:
  - SlidingWindowRateLimiter.cs
  - LeakyBucketRateLimiter.cs
  - TokenBucketRateLimiter.cs
  - FixedWindowRateLimiter.cs

### 2. Updated Async Method to Use ValueTask
- Changed `IAsyncRateLimiter.AcquireAsync` to return `ValueTask<bool>` instead of `Task<bool>`
- Updated `RateLimiterBase.AcquireAsync` implementation to use `new ValueTask<bool>(TryAcquire(tokens))`
- This provides better async performance for the typically synchronous rate limiting operations

### 3. Fixed Math Operations with Explicit Casting
- Fixed `Math.Max(0, _pending - leakIntervals)` → `Math.Max(0.0, _pending - leakIntervals)` in LeakyBucketRateLimiter
- Fixed `Math.Min(_options.Capacity, _availableTokens + tokensToAdd)` → `Math.Min((double)_options.Capacity, _availableTokens + tokensToAdd)` in TokenBucketRateLimiter
- These changes avoid implicit double-to-int/int-to-double conversion ambiguity

## Testing
1. Unit tests in `RateLimiter.Tests/` already pass (they only use `TryAcquire()`)
2. Build the project with: `dotnet build`
3. Run tests with: `dotnet test`

## Related
Fixes issues reported in rate limiter implementation regarding namespace imports, async pattern consistency, and math operation type safety.
