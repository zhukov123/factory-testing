namespace RateLimiter;

using Configuration;
using RateLimiter.Events;

public sealed class LeakyBucketRateLimiter : RateLimiterBase
{
    private readonly object _sync = new();
    private readonly LeakyBucketOptions _options;
    private double _pending;
    private DateTimeOffset _lastLeak;

    public LeakyBucketRateLimiter(LeakyBucketOptions options, string? name = null)
        : base(name ?? "LeakyBucketRateLimiter")
    {
        _options = options ?? throw new ArgumentNullException(nameof(options));
        _options.Validate();
        _lastLeak = DateTimeOffset.UtcNow;
    }

    public override bool TryAcquire(int tokens = 1)
    {
        if (tokens <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(tokens));
        }

        lock (_sync)
        {
            Leak();
            if (_pending + tokens <= _options.Capacity)
            {
                _pending += tokens;
                return true;
            }

            RaiseRateLimitHit(tokens);
            return false;
        }
    }

    private void Leak()
    {
        var now = DateTimeOffset.UtcNow;
        if (_pending <= 0)
        {
            _lastLeak = now;
            return;
        }

        var leakIntervals = (now - _lastLeak).TotalMilliseconds / _options.LeakInterval.TotalMilliseconds;
        if (leakIntervals <= 0)
        {
            return;
        }

        _pending = Math.Max(0.0, _pending - leakIntervals);
        _lastLeak = now;
    }
}
