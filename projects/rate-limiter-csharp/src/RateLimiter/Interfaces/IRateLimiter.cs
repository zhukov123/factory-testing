using System.Threading;

namespace RateLimiter;

public interface IRateLimiter
{
    string Name { get; }

    event EventHandler<RateLimitHitEventArgs>? RateLimitHit;

    bool TryAcquire(int tokens = 1);
}

public interface IAsyncRateLimiter : IRateLimiter
{
    ValueTask<bool> AcquireAsync(int tokens = 1, CancellationToken cancellationToken = default);
}
