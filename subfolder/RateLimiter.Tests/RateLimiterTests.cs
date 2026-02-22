using Microsoft.Extensions.DependencyInjection;
using RateLimiter;
using RateLimiter.Configuration;
using Xunit;

namespace RateLimiter.Tests;

public sealed class RateLimiterTests
{
    [Fact]
    public async Task TokenBucket_AllowsThenRefillsAsync()
    {
        var options = new TokenBucketOptions(capacity: 3, tokensPerInterval: 1, refillInterval: TimeSpan.FromMilliseconds(100));
        var limiter = new TokenBucketRateLimiter(options);
        var hit = false;
        limiter.RateLimitHit += (_, _) => hit = true;

        Assert.True(limiter.TryAcquire());
        Assert.True(limiter.TryAcquire());
        Assert.True(limiter.TryAcquire());
        Assert.False(limiter.TryAcquire());
        Assert.True(hit);

        await Task.Delay(150);
        Assert.True(limiter.TryAcquire());
    }

    [Fact]
    public async Task LeakyBucket_ProcessesQueuedRequests()
    {
        var options = new LeakyBucketOptions(capacity: 2, leakInterval: TimeSpan.FromMilliseconds(50));
        var limiter = new LeakyBucketRateLimiter(options);
        var hit = false;
        limiter.RateLimitHit += (_, _) => hit = true;

        Assert.True(limiter.TryAcquire());
        Assert.True(limiter.TryAcquire());
        Assert.False(limiter.TryAcquire());
        Assert.True(hit);

        await Task.Delay(150);
        Assert.True(limiter.TryAcquire());
    }

    [Fact]
    public async Task FixedWindow_ResetsAfterWindow()
    {
        var options = new FixedWindowOptions(maxRequests: 2, window: TimeSpan.FromMilliseconds(150));
        var limiter = new FixedWindowRateLimiter(options);
        var hit = false;
        limiter.RateLimitHit += (_, _) => hit = true;

        Assert.True(limiter.TryAcquire());
        Assert.True(limiter.TryAcquire());
        Assert.False(limiter.TryAcquire());
        Assert.True(hit);

        await Task.Delay(200);
        Assert.True(limiter.TryAcquire());
    }

    [Fact]
    public async Task SlidingWindow_HonorsWindow()
    {
        var options = new SlidingWindowOptions(maxRequests: 2, window: TimeSpan.FromMilliseconds(120));
        var limiter = new SlidingWindowRateLimiter(options);
        var hit = false;
        limiter.RateLimitHit += (_, _) => hit = true;

        Assert.True(limiter.TryAcquire());
        Assert.True(limiter.TryAcquire());
        Assert.False(limiter.TryAcquire());
        Assert.True(hit);

        await Task.Delay(150);
        Assert.True(limiter.TryAcquire());
    }

    [Fact]
    public void ServiceCollection_CanResolveLimiters()
    {
        var services = new ServiceCollection();
        services.AddTokenBucketLimiter(new TokenBucketOptions(capacity: 2, tokensPerInterval: 1, refillInterval: TimeSpan.FromSeconds(1)), "di-token");
        services.AddFixedWindowLimiter(new FixedWindowOptions(maxRequests: 1, window: TimeSpan.FromSeconds(1)), "di-fixed");

        using var provider = services.BuildServiceProvider();
        var tokenBucket = provider.GetRequiredService<TokenBucketRateLimiter>();
        var fixedWindow = provider.GetRequiredService<FixedWindowRateLimiter>();

        Assert.NotNull(tokenBucket);
        Assert.NotNull(fixedWindow);
        Assert.True(tokenBucket.TryAcquire());
        Assert.True(fixedWindow.TryAcquire());
    }
}
