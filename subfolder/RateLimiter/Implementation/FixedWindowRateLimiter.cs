namespace RateLimiter;

using Configuration;
using RateLimiter.Events;

public sealed class FixedWindowRateLimiter : RateLimiterBase
{
    private readonly object _sync = new();
    private readonly FixedWindowOptions _options;
    private DateTimeOffset _windowStart;
    private int _count;

    public FixedWindowRateLimiter(FixedWindowOptions options, string? name = null)
        : base(name ?? "FixedWindowRateLimiter")
    {
        _options = options ?? throw new ArgumentNullException(nameof(options));
        _options.Validate();
        _windowStart = DateTimeOffset.UtcNow;
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
            if (now - _windowStart >= _options.Window)
            {
                _windowStart = now;
                _count = 0;
            }

            if (_count + tokens > _options.MaxRequests)
            {
                RaiseRateLimitHit(tokens);
                return false;
            }

            _count += tokens;
            return true;
        }
    }
}
