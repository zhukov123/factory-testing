using Microsoft.Extensions.DependencyInjection;
using RateLimiter;
using RateLimiter.Configuration;

await RateLimiterDemoAsync();

static async Task RateLimiterDemoAsync()
{
    var tokenBucketOptions = new TokenBucketOptions(capacity: 5, tokensPerInterval: 1, refillInterval: TimeSpan.FromSeconds(1));
    var tokenBucket = new TokenBucketRateLimiter(tokenBucketOptions, "TokenBucketDemo");
    tokenBucket.RateLimitHit += (sender, args) => Console.WriteLine($"[TokenBucket] Rate limit hit requesting {args.RequestedTokens} tokens at {args.Timestamp:u}.");

    Console.WriteLine("Token bucket warm-up:");
    for (var i = 0; i < 7; i++)
    {
        Console.WriteLine($"  Try {i + 1}: {tokenBucket.TryAcquire()}");
        await Task.Delay(200);
    }

    Console.WriteLine("Waiting for refill...");
    await Task.Delay(1100);
    Console.WriteLine($"  After refill: {tokenBucket.TryAcquire()}");

    var services = new ServiceCollection();
    services.AddFixedWindowLimiter(new FixedWindowOptions(maxRequests: 3, window: TimeSpan.FromSeconds(2)), "FixedWindowDemo");
    services.AddSlidingWindowLimiter(new SlidingWindowOptions(maxRequests: 4, window: TimeSpan.FromSeconds(3)), "SlidingWindowDemo");

    using var provider = services.BuildServiceProvider();
    var fixedLimiter = provider.GetRequiredService<FixedWindowRateLimiter>();
    var slidingLimiter = provider.GetRequiredService<SlidingWindowRateLimiter>();

    fixedLimiter.RateLimitHit += (sender, args) => Console.WriteLine($"[FixedWindow] Limit hit requesting {args.RequestedTokens} tokens at {args.Timestamp:u}.");
    slidingLimiter.RateLimitHit += (sender, args) => Console.WriteLine($"[SlidingWindow] Limit hit requesting {args.RequestedTokens} tokens at {args.Timestamp:u}.");

    Console.WriteLine("Fixed window attempts:");
    for (var i = 0; i < 5; i++)
    {
        Console.WriteLine($"  Try {i + 1}: {fixedLimiter.TryAcquire()}");
        await Task.Delay(400);
    }

    Console.WriteLine("Sliding window attempts:");
    for (var i = 0; i < 6; i++)
    {
        var allowed = await slidingLimiter.AcquireAsync();
        Console.WriteLine($"  Try {i + 1}: {allowed}");
        await Task.Delay(500);
    }
}
