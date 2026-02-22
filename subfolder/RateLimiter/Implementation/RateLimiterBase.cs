using System.Threading;

namespace RateLimiter;

public abstract class RateLimiterBase : IAsyncRateLimiter
{
    protected RateLimiterBase(string name)
    {
        Name = name;
    }

    public string Name { get; }

    public event EventHandler<RateLimitHitEventArgs>? RateLimitHit;

    public abstract bool TryAcquire(int tokens = 1);

    public virtual ValueTask<bool> AcquireAsync(int tokens = 1, CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return new ValueTask<bool>(TryAcquire(tokens));
    }

    protected void RaiseRateLimitHit(int requestedTokens)
    {
        RateLimitHit?.Invoke(this, new RateLimitHitEventArgs(Name, requestedTokens, DateTimeOffset.UtcNow));
    }
}
