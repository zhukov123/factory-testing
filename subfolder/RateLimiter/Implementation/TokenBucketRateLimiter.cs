namespace RateLimiter;

using Configuration;
using RateLimiter.Events;

public sealed class TokenBucketRateLimiter : RateLimiterBase
{
    private readonly object _sync = new();
    private readonly TokenBucketOptions _options;
    private double _availableTokens;
    private DateTimeOffset _lastRefill;

    public TokenBucketRateLimiter(TokenBucketOptions options, string? name = null)
        : base(name ?? "TokenBucketRateLimiter")
    {
        _options = options ?? throw new ArgumentNullException(nameof(options));
        _options.Validate();
        _availableTokens = _options.Capacity;
        _lastRefill = DateTimeOffset.UtcNow;
    }

    public override bool TryAcquire(int tokens = 1)
    {
        if (tokens <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(tokens));
        }

        lock (_sync)
        {
            Refill();
            if (_availableTokens >= tokens)
            {
                _availableTokens -= tokens;
                return true;
            }

            RaiseRateLimitHit(tokens);
            return false;
        }
    }

    private void Refill()
    {
        var now = DateTimeOffset.UtcNow;
        var elapsed = now - _lastRefill;
        if (elapsed <= TimeSpan.Zero)
        {
            return;
        }

        var refillIntervals = elapsed.TotalMilliseconds / _options.RefillInterval.TotalMilliseconds;
        if (refillIntervals <= 0)
        {
            return;
        }

        var tokensToAdd = refillIntervals * _options.TokensPerInterval;
        if (tokensToAdd <= 0)
        {
            _lastRefill = now;
            return;
        }

        _availableTokens = Math.Min((double)_options.Capacity, _availableTokens + tokensToAdd);
        _lastRefill = now;
    }
}
