# RateLimiter

A modern, DI-friendly collection of classic and precise rate limiting primitives for .NET. The library ships with four thread-safe implementations (Token Bucket, Leaky Bucket, Fixed Window, and Sliding Window), optional asynchronous support, eventing, and configuration records that make it easy to plug into services, worker queues, and ASP.NET middleware pipelines.

## Features

- **Token Bucket**: Tokens refill at a fixed cadence and are consumed per request.
- **Leaky Bucket**: Backlogged requests leak out at a steady fixed pace.
- **Fixed Window**: Simplest counter per discrete time window.
- **Sliding Window**: Smooth rate limiting with a sliding time window.
- Thread-safe implementations using locks and optional asynchronous access via `IAsyncRateLimiter`.
- Events and notifications (`RateLimitHit`) to react when limits are exceeded.
- Configuration records (`TokenBucketOptions`, etc.) with validation built in.
- DI helpers via `ServiceCollectionExtensions` for easy registration.
- Sample console app, benchmarks, and xUnit tests for complete verification.

## Getting Started

### Installation

Add the project/reference to your solution:

```bash
dotnet add <your-project>.csproj reference RateLimiter.csproj
```

### Simple Token Bucket

```csharp
var tokenBucket = new TokenBucketRateLimiter(
    new TokenBucketOptions(capacity: 10, tokensPerInterval: 2, refillInterval: TimeSpan.FromSeconds(1)));

if (!tokenBucket.TryAcquire())
{
    Console.WriteLine("Rate limit hit");
}
```

### Asynchronous Support

All limiters inherit from `IAsyncRateLimiter`, so you can await acquisitions:

```csharp
await tokenBucket.AcquireAsync();
```

### DI Registration

```csharp
services.AddTokenBucketLimiter(new TokenBucketOptions(capacity: 5, tokensPerInterval: 5, refillInterval: TimeSpan.FromSeconds(1)));
```

The extension registers the concrete limiter as `IRateLimiter`, `IAsyncRateLimiter`, and the concrete type for easy injection.

## Example App

Explore `factory-testing/subfolder/RateLimiter.Examples` for a console demo that wires up multiple rate limiters, subscribes to `RateLimitHit` events, and demonstrates both synchronous and asynchronous flows.

## Testing

Run the xUnit suite:

```bash
dotnet test subfolder/RateLimiter.Tests/RateLimiter.Tests.csproj
```

The suite exercises each limiter, validates resets, and verifies DI registration.

## Benchmarks

Performance comparisons are implemented with BenchmarkDotNet:

```bash
dotnet run --project subfolder/RateLimiter.Benchmarks/RateLimiter.Benchmarks.csproj -c Release
```

## Integration

The solution is arranged for `factory-testing/subfolder` with a shared `RateLimiter` class library, sample console app, tests, and benchmarks. The projects are already wired into the solution file and can be built/tested with `dotnet` tooling.
