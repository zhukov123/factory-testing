# RateLimiter (C# / .NET)

A modern, DI-friendly collection of rate limiting primitives for .NET. The library ships with four thread-safe implementations (Token Bucket, Leaky Bucket, Fixed Window, and Sliding Window), optional asynchronous support, eventing, and configuration records that make it easy to plug into ASP.NET, worker queues, or any long-running service.

## Features

- **Token Bucket**: Tokens refill at a fixed cadence and are consumed per request, making it easy to control burst capacity.
- **Leaky Bucket**: Backlogged requests leak out at a steady pace to smooth peaks.
- **Fixed Window**: Counter-based ratelimiting per discrete time window.
- **Sliding Window**: Smooth rate limits over a sliding time window.
- **Events & Notifications**: Subscribe to `RateLimitHit` events when limits are exceeded.
- **Configuration Records**: Each limiter exposes an `Options` record (e.g., `TokenBucketOptions`) with built-in validation.
- **Dependency Injection Helpers**: `ServiceCollectionExtensions` makes it easy to register limiters with ASP.NET Core.

## Getting Started

### Add the library to your solution

```bash
dotnet add <your-project>.csproj reference RateLimiter.csproj
```

### Simple Token Bucket example

```csharp
var tokenBucket = new TokenBucketRateLimiter(
    new TokenBucketOptions(capacity: 10, tokensPerInterval: 2, refillInterval: TimeSpan.FromSeconds(1)));

if (!tokenBucket.TryAcquire())
{
    Console.WriteLine("Rate limit hit");
}
```

### Asynchronous support

All implementations also provide `IAsyncRateLimiter` so you can `await` acquisitions:

```csharp
await tokenBucket.AcquireAsync();
```

### Dependency injection registration

```csharp
services.AddTokenBucketLimiter(new TokenBucketOptions(capacity: 5, tokensPerInterval: 5, refillInterval: TimeSpan.FromSeconds(1)));
```

## Building

```bash
dotnet build RateLimiter.csproj
```

## Testing

The `tests/` directory is reserved for the xUnit suite that verifies the limiter implementations. When tests are present, run them with:

```bash
dotnet test tests/RateLimiter.Tests/RateLimiter.Tests.csproj
```

## Benchmarks & Examples

Benchmarks and sample apps can be added next to the core library. Once you drop in `RateLimiter.Benchmarks` or `RateLimiter.Examples`, run them with the standard `dotnet run --project <project>` workflow (e.g., `dotnet run --project benchmarks/RateLimiter.Benchmarks/RateLimiter.Benchmarks.csproj -c Release`).

## Project Structure

```
projects/rate-limiter-csharp/
├── RateLimiter.csproj        # Class library entry point
├── README.md                # This file
├── tests/README.md          # Testing instructions/helpers
├── src/
│   └── RateLimiter/         # Implementation folders (Configuration, Events, Extensions, Factories, Implementation, Interfaces, Limiters, Options, Time)
└── tests/                   # Reserve for RateLimiter.Tests and related projects
```
