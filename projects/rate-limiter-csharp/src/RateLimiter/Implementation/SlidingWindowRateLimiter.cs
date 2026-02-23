namespace RateLimiter;

using Configuration;
using RateLimiter.Events;

public sealed class SlidingWindowRateLimiter : RateLimiterBase
{
    private readonly object _sync = new();
    private readonly SlidingWindowOptions _options;
    private readonly Queue<DateTimeOffset> _timestamps = new();

    public SlidingWindowRateLimiter(SlidingWindowOptions options, string? name = null)
        : base(name ?? "SlidingWindowRateLimiter")
    {
        _options = options ?? throw new ArgumentNullException(nameof(options));
        _options.Validate();
    }

    public override bool TryAcquire(int tokens = 1)
    {
        if (tokens <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(tokens));
        }

        lock (_sync)
        {
            var now = DateTimeOffset.UtcNow;
            Cleanup(now);

            if (_timestamps.Count + tokens > _options.MaxRequests)
            {
                RaiseRateLimitHit(tokens);
                return false;
            }

            for (var i = 0; i < tokens; i++)
            {
                _timestamps.Enqueue(now);
            }

            return true;
        }
    }

    private void Cleanup(DateTimeOffset now)
    {
        while (_timestamps.Count > 0 && now - _timestamps.Peek() >= _options.Window)
        {
            _timestamps.Dequeue();
        }
    }
}
