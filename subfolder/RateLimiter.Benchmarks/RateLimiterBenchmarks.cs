using BenchmarkDotNet.Attributes;
using RateLimiter;
using RateLimiter.Configuration;

[MemoryDiagnoser]
public class RateLimiterBenchmarks
{
    private TokenBucketRateLimiter? _tokenBucket;
    private LeakyBucketRateLimiter? _leakyBucket;
    private FixedWindowRateLimiter? _fixedWindow;
    private SlidingWindowRateLimiter? _slidingWindow;

    [GlobalSetup]
    public void Setup()
    {
        _tokenBucket = new TokenBucketRateLimiter(new TokenBucketOptions(capacity: 100_000, tokensPerInterval: 100_000, refillInterval: TimeSpan.FromMilliseconds(1)));
        _leakyBucket = new LeakyBucketRateLimiter(new LeakyBucketOptions(capacity: 100_000, leakInterval: TimeSpan.FromMilliseconds(1)));
        _fixedWindow = new FixedWindowRateLimiter(new FixedWindowOptions(maxRequests: 100_000, window: TimeSpan.FromSeconds(1)));
        _slidingWindow = new SlidingWindowRateLimiter(new SlidingWindowOptions(maxRequests: 100_000, window: TimeSpan.FromSeconds(1)));
    }

    [Benchmark(Baseline = true)]
    public bool TokenBucket() => _tokenBucket!.TryAcquire();

    [Benchmark]
    public bool LeakyBucket() => _leakyBucket!.TryAcquire();

    [Benchmark]
    public bool FixedWindow() => _fixedWindow!.TryAcquire();

    [Benchmark]
    public bool SlidingWindow() => _slidingWindow!.TryAcquire();
}
